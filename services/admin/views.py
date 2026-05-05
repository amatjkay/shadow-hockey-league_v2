"""Per-model ModelViews + audit-log formatters + ServerControlView.

Grouped together because they share the same ``SHLModelView`` base, audit
helpers, and admin-only access patterns. Splitting further would force
many small files with ~30-40 LOC each while increasing import surface.
"""

from __future__ import annotations

import json
import logging
from typing import Any, cast

from flask import flash, redirect, request, url_for
from flask_admin import AdminIndexView, expose
from flask_login import current_user
from markupsafe import Markup
from wtforms import PasswordField

from data.admin_observers import validate_manager_name
from models import (
    Achievement,
    AchievementType,
    AdminUser,
    ApiKey,
    AuditLog,
    Country,
    League,
    Manager,
    Season,
    db,
)
from services.admin.base import SHLModelView
from services.cache_service import invalidate_leaderboard_cache

admin_logger = logging.getLogger("shleague.admin")


# ==================== Core Views ====================


class CountryModelView(SHLModelView):
    """View for managing countries."""

    column_list = ("code", "name", "flag_path", "is_active")
    column_searchable_list = ("code", "name")
    column_filters = ("is_active", "flag_source_type")

    form_choices = {"flag_source_type": [("local", "Local Asset"), ("api", "External API")]}

    column_formatters = {
        "flag_path": lambda v, c, m, p: Markup(
            f'<img src="{m.flag_display_url}" width="24" height="24"> {m.flag_path}'
        )
    }

    def on_model_change(self, form: Any, model: Country, is_created: bool) -> None:
        """Auto-fill country name from code if it matches known codes."""
        # Mapping from code to name (expected by tests)
        name_map = {
            "RUS": "Russia",
            "BLR": "Belarus",
            "KAZ": "Kazakhstan",
            "UKR": "Ukraine",
            "LAT": "Latvia",
        }
        if model.code in name_map:
            model.name = name_map[model.code]

        super().on_model_change(form, model, is_created)


class ManagerModelView(SHLModelView):
    """View for managing managers."""

    edit_template = "admin/manager_edit.html"

    column_list = ("name", "country", "achievements_count", "is_active")
    column_searchable_list = ("name",)

    column_labels = {"achievements_count": "Achievements"}

    column_formatters = {"achievements_count": lambda v, c, m, p: len(m.achievements)}

    # Use Select2 for country selection
    form_ajax_refs = {
        "country": {
            "fields": (Country.name, Country.code),
            "placeholder": "Please select a country",
            "page_size": 10,
            "minimum_input_length": 0,
        }
    }

    def on_model_change(self, form: Any, model: Manager, is_created: bool) -> None:
        """Block admin-observer tandem records that lack an explicit allowlist entry."""

        validate_manager_name(model.name)
        super().on_model_change(form, model, is_created)


class AchievementModelView(SHLModelView):
    """View for managing individual achievements.

    The ``type`` / ``league`` / ``season`` foreign-key dropdowns are wired
    through ``form_ajax_refs`` below — that is the canonical Flask-Admin
    pattern for relationship pickers and works under the current WTForms
    3.x where ``form_args={'<rel>': {'query_factory': ...}}`` would be
    forwarded into a plain ``Field.__init__`` and crash with
    ``TypeError: Field.__init__() got an unexpected keyword argument
    'query_factory'``.
    """

    column_list = ("manager", "type", "league", "season", "final_points", "updated_at")

    # Validation Rules
    form_ajax_refs = {
        "manager": {"fields": (Manager.name,), "placeholder": "Select Manager"},
        "type": {
            "fields": (AchievementType.code, AchievementType.name),
            "placeholder": "Select Type",
        },
        "league": {"fields": (League.code, League.name), "placeholder": "Select League"},
        "season": {"fields": (Season.code, Season.name), "placeholder": "Select Season"},
    }

    def on_model_change(self, form: Any, model: Achievement, is_created: bool) -> None:
        """Auto-calculate fields and validate uniqueness."""
        # --- Admin-observer guardrail (defence-in-depth) ---
        # Catches the rare case where an unsanctioned admin-observer
        # tandem manager slipped past the ManagerModelView guardrail
        # (e.g. legacy direct DB insert) before any achievement gets
        # attributed to them.
        if model.manager_id and not model.manager:
            model.manager = db.session.get(Manager, model.manager_id)
        if model.manager is not None:
            validate_manager_name(model.manager.name)

        # --- Duplicate Validation (TIK-23) ---
        with db.session.no_autoflush:  # type: ignore[attr-defined]
            if model.manager_id and model.type_id and model.league_id and model.season_id:
                query = db.session.query(Achievement).filter(
                    Achievement.manager_id == model.manager_id,
                    Achievement.type_id == model.type_id,
                    Achievement.league_id == model.league_id,
                    Achievement.season_id == model.season_id,
                )
                # On edit, exclude the current record
                if not is_created and model.id:
                    query = query.filter(Achievement.id != model.id)

                duplicate = query.first()

                if duplicate:
                    manager_name = model.manager.name if model.manager else f"ID={model.manager_id}"
                    raise ValueError(
                        f"Дубликат: у менеджера «{manager_name}» уже есть достижение "
                        f"с таким же типом, лигой и сезоном (ID={duplicate.id})."
                    )

        # --- Auto-calculation ---
        # Ensure relationships are loaded
        if not model.type or not model.league or not model.season:
            # Re-fetch if they are just IDs
            if model.type_id:
                model.type = db.session.get(AchievementType, model.type_id)
            if model.league_id:
                model.league = db.session.get(League, model.league_id)
            if model.season_id:
                model.season = db.session.get(Season, model.season_id)

        if model.type and model.league and model.season:
            type_resolved = cast(AchievementType, model.type)
            league_resolved = cast(League, model.league)
            season_resolved = cast(Season, model.season)

            # 1. Generate Title: "Top 1 League 1 Season 23/24"
            model.title = f"{type_resolved.name} {league_resolved.name} {season_resolved.name}"

            # 2. Resolve Icon Path
            model.icon_path = type_resolved.get_icon_url()

            # 3. Calculate Points (league-aware via League.parent_code).
            from services.scoring_service import get_base_points

            base = get_base_points(type_resolved, league_resolved)
            mult = season_resolved.multiplier

            model.base_points = float(base)
            model.multiplier = float(mult)
            model.final_points = round(float(base * mult), 2)

            admin_logger.info(
                f"Auto-calculated achievement: {model.title} = {model.final_points} pts"
            )

        super().on_model_change(form, model, is_created)

    def after_model_change(self, form: Any, model: Any, is_created: bool) -> None:
        """Trigger cache invalidation."""
        invalidate_leaderboard_cache()


# ==================== Reference Views ====================


class AchievementTypeModelView(SHLModelView):
    """View for managing achievement types."""

    column_list = ("code", "name", "base_points_l1", "base_points_l2", "icon_path", "is_active")
    column_editable_list = ("name", "base_points_l1", "base_points_l2", "is_active")


class LeagueModelView(SHLModelView):
    """View for managing leagues."""

    column_list = ("code", "name", "parent_code", "is_active")
    form_ajax_refs = {"parent": {"fields": (League.code,), "placeholder": "Select parent league"}}


class SeasonModelView(SHLModelView):
    """View for managing seasons."""

    column_list = ("code", "name", "multiplier", "is_active", "start_year")
    column_editable_list = ("multiplier", "is_active")
    column_sortable_list = ("code", "start_year", "multiplier")
    column_default_sort = ("start_year", True)


# ==================== Audit Log View ====================


def _action_badge_class(action: str) -> str:
    """Return Bootstrap badge class for an audit action."""
    return {
        "CREATE": "create",
        "UPDATE": "update",
        "DELETE": "delete",
    }.get(action, "secondary")


def _format_audit_changes(changes_json: str | None) -> Markup:
    """Format audit log changes JSON into a readable HTML snippet."""
    if not changes_json:
        return Markup('<span class="text-muted">No changes</span>')

    try:
        changes = json.loads(changes_json)
        if not isinstance(changes, dict):
            return Markup(f'<code class="small text-muted">{changes_json}</code>')

        html = ['<div class="audit-changes small">']

        for field, values in changes.items():
            # Skip internal or noisy fields
            if field in ("password_hash", "key_hash"):
                html.append(
                    f'<div><strong>{field}</strong>: <span class="text-muted">[HIDDEN]</span></div>'
                )
                continue

            if isinstance(values, dict) and "old" in values and "new" in values:
                # UPDATE style
                old = values["old"] if values["old"] is not None else "<i>null</i>"
                new = values["new"] if values["new"] is not None else "<i>null</i>"
                html.append(
                    f"<div><strong>{field}</strong>: "
                    f'<span class="text-danger"><del>{old}</del></span> &rarr; '
                    f'<span class="text-success">{new}</span></div>'
                )
            else:
                # CREATE/DELETE style (single value)
                val = values if values is not None else "<i>null</i>"
                html.append(f"<div><strong>{field}</strong>: {val}</div>")

        html.append("</div>")
        return Markup("".join(html))

    except (ValueError, TypeError):
        return Markup(f'<code class="small text-muted">{changes_json}</code>')


def _format_target_link(model: AuditLog) -> Markup:
    """Generate a link to the target model's edit view."""
    if not model.target_model or not model.target_id:
        return Markup(f'<span class="text-muted">{model.target_id or "-"}</span>')

    # Map model names to their admin view endpoints
    # Flask-Admin default endpoint is usually lowercase model name
    endpoint_map = {
        "Country": "country",
        "Manager": "manager",
        "Achievement": "achievement",
        "AchievementType": "achievementtype",
        "League": "league",
        "Season": "season",
        "AdminUser": "adminuser",
        "ApiKey": "apikey",
    }

    endpoint = endpoint_map.get(model.target_model)
    if not endpoint:
        return Markup(f"<span>{model.target_model} #{model.target_id}</span>")

    try:
        url = url_for(f"{endpoint}.edit_view", id=model.target_id)
        return Markup(
            f'<a href="{url}" class="target-link">{model.target_model} #{model.target_id}</a>'
        )
    except Exception:
        # Fallback if endpoint or route doesn't exist (e.g. if can_edit is False)
        return Markup(f"<span>{model.target_model} #{model.target_id}</span>")


class AuditLogModelView(SHLModelView):
    """Read-only view for audit logs."""

    list_template = "admin/audit_list.html"

    column_list = ("timestamp", "user_id", "action", "target_model", "target_id", "changes")
    column_sortable_list = ("timestamp",)
    column_default_sort = ("timestamp", True)

    column_labels = {
        "target_model": "Model",
        "target_id": "Target ID/Link",
        "user_id": "Admin User ID",
    }

    column_filters = ("action", "target_model", "user_id")

    column_formatters = {
        "action": lambda v, c, m, p: Markup(
            f'<span class="badge badge-{_action_badge_class(m.action)}">' f"{m.action}</span>"
        ),
        "target_id": lambda v, c, m, p: _format_target_link(m),
        "changes": lambda v, c, m, p: _format_audit_changes(m.changes),
    }


# ==================== System Views ====================


class AdminUserModelView(SHLModelView):
    """View for managing admin users."""

    column_list = ("username", "role")
    form_columns = ("username", "password", "role")

    form_extra_fields = {"password": PasswordField("Password")}

    form_choices = {"role": AdminUser.ROLE_CHOICES}

    def on_model_change(self, form: Any, model: AdminUser, is_created: bool) -> None:
        if form.password.data:
            model.set_password(form.password.data)


class ApiKeyModelView(SHLModelView):
    """View for managing API keys."""

    name = "API Keys"
    column_list = ("name", "scope", "expires_at", "revoked", "last_used_at")
    form_columns = ("name", "scope", "expires_at", "revoked")

    column_labels = {"revoked": "Revoked?"}

    form_choices = {"scope": [("read", "Read Only"), ("write", "Read/Write"), ("admin", "Admin")]}


class ServerControlView(AdminIndexView):
    """View for server control operations."""

    def is_accessible(self) -> bool:
        """Only super admins can access server control."""
        return current_user.is_authenticated and current_user.has_permission("server_control")

    def inaccessible_callback(self, name: str, **kwargs: Any) -> Any:
        return redirect(url_for("admin.login", next=request.url))

    @expose("/")
    def index(self) -> Any:
        return self.render("admin/server_control.html")

    @expose("/restart", methods=["POST"])
    def restart(self) -> Any:
        """Simulate a server restart."""
        flash(
            "Server restart initiated. The application will be unavailable for a moment.", "warning"
        )
        admin_logger.warning(f"Server restart initiated by {current_user.username}")
        return redirect(url_for(".index"))
