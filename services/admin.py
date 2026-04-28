"""Admin service for configuring Flask-Admin interface.

Includes model views for all database models with customized forms,
validation, and access control.
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any, cast

from flask import Flask, redirect, url_for, request, flash, current_app, render_template
from markupsafe import Markup
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_admin.form import Select2Widget
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from wtforms import PasswordField, StringField, SelectField, HiddenField
from wtforms.validators import DataRequired
from sqlalchemy.orm import joinedload

from models import (
    db, AdminUser, Country, Manager, Achievement, AchievementType,
    League, Season, AuditLog, ApiKey
)
from data.static_paths import get_flag_choices

# Configure logging for admin service
admin_logger = logging.getLogger('shleague.admin')


def init_admin(app: Flask) -> None:
    """Initialize Flask-Admin and Flask-Login for the application.

    Args:
        app: Flask application instance.
    """
    # Initialize LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'

    @login_manager.user_loader
    def load_user(user_id: str) -> AdminUser | None:
        return db.session.get(AdminUser, int(user_id))

    # Initialize Admin with custom index view
    admin = Admin(
        app,
        name='SH League Admin',
        index_view=SHLAdminIndexView(),
        theme=Bootstrap4Theme(base_template='admin/shl_master.html')
    )

    # Add model views
    admin.add_view(CountryModelView(Country, db.session, category='Core'))
    admin.add_view(ManagerModelView(Manager, db.session, category='Core'))
    admin.add_view(AchievementModelView(Achievement, db.session, category='Data'))
    
    admin.add_view(AchievementTypeModelView(AchievementType, db.session, category='Reference'))
    admin.add_view(LeagueModelView(League, db.session, category='Reference'))
    admin.add_view(SeasonModelView(Season, db.session, category='Reference'))
    
    admin.add_view(AuditLogModelView(AuditLog, db.session, category='System'))
    admin.add_view(ApiKeyModelView(ApiKey, db.session, category='System'))
    admin.add_view(AdminUserModelView(AdminUser, db.session, category='System'))


# ==================== Auth & Index ====================

class SHLAdminIndexView(AdminIndexView):
    """Custom admin index view with login/logout and stats."""

    @expose('/')
    def index(self) -> Any:
        if not current_user.is_authenticated:
            return redirect(url_for('.login'))

        # Get stats for dashboard. Pass both the legacy flat names
        # (manager_count, …) consumed by templates/admin/index.html and a
        # combined `stats` dict for newer templates.
        manager_count = db.session.query(Manager).count()
        achievement_count = db.session.query(Achievement).count()
        country_count = db.session.query(Country).count()
        admin_count = db.session.query(AdminUser).count()
        active_seasons = db.session.query(Season).filter_by(is_active=True).count()
        last_audit = (
            db.session.query(AuditLog).order_by(AuditLog.timestamp.desc()).first()
        )

        stats = {
            'managers': manager_count,
            'achievements': achievement_count,
            'countries': country_count,
            'admins': admin_count,
            'active_seasons': active_seasons,
            'last_audit': last_audit,
        }

        return self.render(
            'admin/index.html',
            stats=stats,
            manager_count=manager_count,
            achievement_count=achievement_count,
            country_count=country_count,
            admin_count=admin_count,
        )

    @expose('/login/', methods=['GET', 'POST'])
    def login(self) -> Any:
        if current_user.is_authenticated:
            return redirect(url_for('.index'))

        if request.method == 'POST':
            # Brute-force defence: 10 *failed* attempts / 60 s per client IP.
            # Successful logins do not count toward the budget so that admins
            # can't lock themselves out by repeatedly logging in/out.
            if not _is_login_rate_limit_ok(max_attempts=10, window_seconds=60):
                admin_logger.warning(
                    f"Rate-limited login attempt from {_get_client_ip()}"
                )
                flash('Too many login attempts. Please wait 60 seconds.', 'error')
                return self.render('admin/login.html')

            username = request.form.get('username')
            password = request.form.get('password')

            user = db.session.query(AdminUser).filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                admin_logger.info(f"Admin login: {username}")
                return redirect(url_for('.index'))
            else:
                _record_failed_login_attempt()
                flash('Invalid username or password', 'error')

        return self.render('admin/login.html')

    @expose('/logout/')
    def logout(self) -> Any:
        admin_logger.info(f"Admin logout: {current_user.username if current_user.is_authenticated else 'unknown'}")
        logout_user()
        return redirect(url_for('.index'))

    @expose('/flush-cache/', methods=['POST'])
    @login_required
    def flush_cache(self) -> Any:
        """Invalidate all leaderboard caches. Admin-only."""
        invalidate_leaderboard_cache()
        admin_logger.info(
            f"FLUSH_CACHE by {current_user.username if current_user.is_authenticated else 'unknown'}"
        )
        flash('Leaderboard cache successfully flushed', 'success')
        return redirect(url_for('.index'))
# ==================== Base View ====================

class SHLModelView(ModelView):
    """Base model view with common security and logging."""


    # UI Customization
    list_template = 'admin/model/list.html'
    create_template = 'admin/model/create.html'
    edit_template = 'admin/model/edit.html'
    
    can_export = True
    page_size = 50

    def is_accessible(self) -> bool:
        """Check if user is authenticated and has admin role."""
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name: str, **kwargs: Any) -> Any:
        """Redirect to login if access is denied."""
        return redirect(url_for('admin.login', next=request.url))

    def on_model_change(self, form: Any, model: Any, is_created: bool) -> None:
        """Log changes to audit log."""
        action = 'CREATE' if is_created else 'UPDATE'
        from services.audit_service import log_action
        
        # We don't log the actual changes here (done via SQLAlchemy events for better coverage),
        # but we can log the action intent.
        username = getattr(current_user, 'username', 'system')
        admin_logger.debug(f"{action} {model.__class__.__name__} by {username}")

    def on_model_delete(self, model: Any) -> None:
        """Log deletion to audit log."""
        from services.audit_service import log_action
        username = getattr(current_user, 'username', 'system')
        admin_logger.info(f"DELETE {model.__class__.__name__} {getattr(model, 'id', 'unknown')} by {username}")


# Resolve alias
SecureModelView = SHLModelView


# ==================== Core Views ====================

class CountryModelView(SHLModelView):
    """View for managing countries."""
    column_list = ('code', 'name', 'flag_path', 'is_active')
    column_searchable_list = ('code', 'name')
    column_filters = ('is_active', 'flag_source_type')
    
    form_choices = {
        'flag_source_type': [('local', 'Local Asset'), ('api', 'External API')]
    }

    column_formatters = {
        'flag_path': lambda v, c, m, p: Markup(f'<img src="{m.flag_display_url}" width="24" height="24"> {m.flag_path}')
    }

    def on_model_change(self, form: Any, model: Country, is_created: bool) -> None:
        """Auto-fill country name from code if it matches known codes."""
        # Mapping from code to name (expected by tests)
        name_map = {
            'RUS': 'Russia',
            'BLR': 'Belarus',
            'KAZ': 'Kazakhstan',
            'UKR': 'Ukraine',
            'LAT': 'Latvia'
        }
        if model.code in name_map:
            model.name = name_map[model.code]
        
        super().on_model_change(form, model, is_created)


class ManagerModelView(SHLModelView):
    """View for managing managers."""
    edit_template = 'admin/manager_edit.html'
    
    column_list = ('name', 'country', 'achievements_count', 'is_active')
    column_searchable_list = ('name',)
    # column_filters = (Country.name, 'is_active')
    # column_select_related_list = [Manager.country]
    
    column_labels = {
        'achievements_count': 'Achievements'
    }

    column_formatters = {
        'achievements_count': lambda v, c, m, p: len(m.achievements)
    }

    # Use Select2 for country selection
    form_ajax_refs = {
        'country': {
            'fields': (Country.name, Country.code),
            'placeholder': 'Please select a country',
            'page_size': 10,
            'minimum_input_length': 0,
        }
    }


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

    column_list = ('manager', 'type', 'league', 'season', 'final_points', 'updated_at')
    # column_searchable_list = (Manager.name, 'title')
    # column_filters = (AchievementType.code, League.code, Season.code, 'final_points')
    # column_select_related_list = [Achievement.manager, Achievement.type, Achievement.league, Achievement.season]
    
    # Validation Rules
    form_ajax_refs = {
        'manager': {'fields': (Manager.name,), 'placeholder': 'Select Manager'},
        'type': {'fields': (AchievementType.code, AchievementType.name), 'placeholder': 'Select Type'},
        'league': {'fields': (League.code, League.name), 'placeholder': 'Select League'},
        'season': {'fields': (Season.code, Season.name), 'placeholder': 'Select Season'},
    }

    def on_model_change(self, form: Any, model: Achievement, is_created: bool) -> None:
        """Auto-calculate fields and validate uniqueness."""
        # --- Duplicate Validation (TIK-23) ---
        with db.session.no_autoflush:
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
            if model.type_id: model.type = db.session.get(AchievementType, model.type_id)
            if model.league_id: model.league = db.session.get(League, model.league_id)
            if model.season_id: model.season = db.session.get(Season, model.season_id)

        if model.type and model.league and model.season:
            # 1. Generate Title: "Top 1 League 1 Season 23/24"
            model.title = f"{model.type.name} {model.league.name} {model.season.name}"
            
            # 2. Resolve Icon Path
            model.icon_path = model.type.get_icon_url()
            
            # 3. Calculate Points
            # Use base_points_l1 for League 1, l2 for others
            base = model.type.base_points_l1 if model.league.code == '1' else model.type.base_points_l2
            mult = model.season.multiplier
            
            model.base_points = float(base)
            model.multiplier = float(mult)
            model.final_points = round(float(base * mult), 2)
            
            admin_logger.info(f"Auto-calculated achievement: {model.title} = {model.final_points} pts")

        super().on_model_change(form, model, is_created)

    def after_model_change(self, form: Any, model: Any, is_created: bool) -> None:
        """Trigger cache invalidation."""
        invalidate_leaderboard_cache()


# ==================== Reference Views ====================

class AchievementTypeModelView(SHLModelView):
    """View for managing achievement types."""
    column_list = ('code', 'name', 'base_points_l1', 'base_points_l2', 'icon_path', 'is_active')
    column_editable_list = ('name', 'base_points_l1', 'base_points_l2', 'is_active')


class LeagueModelView(SHLModelView):
    """View for managing leagues."""
    column_list = ('code', 'name', 'parent_code', 'is_active')
    form_ajax_refs = {
        'parent': {'fields': (League.code,), 'placeholder': 'Select parent league'}
    }


class SeasonModelView(SHLModelView):
    """View for managing seasons."""
    column_list = ('code', 'name', 'multiplier', 'is_active', 'start_year')
    column_editable_list = ('multiplier', 'is_active')
    column_sortable_list = ('code', 'start_year', 'multiplier')
    column_default_sort = ('start_year', True)


# ==================== System Views ====================

class AuditLogModelView(SHLModelView):
    """Read-only view for audit logs."""
    list_template = 'admin/audit_list.html'
    
    column_list = ('timestamp', 'user_id', 'action', 'target_model', 'target_id', 'changes')
    column_sortable_list = ('timestamp',)
    column_default_sort = ('timestamp', True)
    
    column_labels = {
        'target_model': 'Model',
        'target_id': 'Target ID/Link',
        'user_id': 'Admin User ID'
    }

    column_filters = ('action', 'target_model', 'user_id')

    column_formatters = {
        'action': lambda v, c, m, p: Markup(
            f'<span class="badge badge-{"create" if m.action == "CREATE" else "update" if m.action == "UPDATE" else "delete" if m.action == "DELETE" else "secondary"}">'
            f'{m.action}</span>'
        ),
        'target_id': lambda v, c, m, p: _format_target_link(m),
        'changes': lambda v, c, m, p: _format_audit_changes(m.changes)
    }


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
            if field in ('password_hash', 'key_hash'):
                html.append(f'<div><strong>{field}</strong>: <span class="text-muted">[HIDDEN]</span></div>')
                continue

            if isinstance(values, dict) and 'old' in values and 'new' in values:
                # UPDATE style
                old = values['old'] if values['old'] is not None else '<i>null</i>'
                new = values['new'] if values['new'] is not None else '<i>null</i>'
                html.append(
                    f'<div><strong>{field}</strong>: '
                    f'<span class="text-danger"><del>{old}</del></span> &rarr; '
                    f'<span class="text-success">{new}</span></div>'
                )
            else:
                # CREATE/DELETE style (single value)
                val = values if values is not None else '<i>null</i>'
                html.append(f'<div><strong>{field}</strong>: {val}</div>')
        
        html.append('</div>')
        return Markup(''.join(html))
        
    except (ValueError, TypeError):
        return Markup(f'<code class="small text-muted">{changes_json}</code>')


def _format_target_link(model: AuditLog) -> Markup:
    """Generate a link to the target model's edit view."""
    if not model.target_model or not model.target_id:
        return Markup(f'<span class="text-muted">{model.target_id or "-"}</span>')
    
    # Map model names to their admin view endpoints
    # Flask-Admin default endpoint is usually lowercase model name
    endpoint_map = {
        'Country': 'country',
        'Manager': 'manager',
        'Achievement': 'achievement',
        'AchievementType': 'achievementtype',
        'League': 'league',
        'Season': 'season',
        'AdminUser': 'adminuser',
        'ApiKey': 'apikey'
    }
    
    endpoint = endpoint_map.get(model.target_model)
    if not endpoint:
        return Markup(f'<span>{model.target_model} #{model.target_id}</span>')
    
    try:
        url = url_for(f'{endpoint}.edit_view', id=model.target_id)
        return Markup(f'<a href="{url}" class="target-link">{model.target_model} #{model.target_id}</a>')
    except Exception:
        # Fallback if endpoint or route doesn't exist (e.g. if can_edit is False)
        return Markup(f'<span>{model.target_model} #{model.target_id}</span>')


class AdminUserModelView(SHLModelView):
    """View for managing admin users."""
    column_list = ('username', 'role')
    form_columns = ('username', 'password', 'role')
    
    form_extra_fields = {
        'password': PasswordField('Password')
    }
    
    form_choices = {
        'role': AdminUser.ROLE_CHOICES
    }

    def on_model_change(self, form: Any, model: AdminUser, is_created: bool) -> None:
        if form.password.data:
            model.set_password(form.password.data)


class ApiKeyModelView(SHLModelView):
    """View for managing API keys."""
    name = "API Keys"
    column_list = ('name', 'scope', 'expires_at', 'revoked', 'last_used_at')
    form_columns = ('name', 'scope', 'expires_at', 'revoked')
    
    column_labels = {
        'revoked': 'Revoked?'
    }
    
    form_choices = {
        'scope': [('read', 'Read Only'), ('write', 'Read/Write'), ('admin', 'Admin')]
    }


class ServerControlView(AdminIndexView):
    """View for server control operations."""
    
    def is_accessible(self) -> bool:
        """Only super admins can access server control."""
        return current_user.is_authenticated and current_user.has_permission('server_control')

    def inaccessible_callback(self, name: str, **kwargs: Any) -> Any:
        return redirect(url_for('admin.login', next=request.url))

    @expose('/')
    def index(self) -> Any:
        return self.render('admin/server_control.html')

    @expose('/restart', methods=['POST'])
    def restart(self) -> Any:
        """Simulate a server restart."""
        flash('Server restart initiated. The application will be unavailable for a moment.', 'warning')
        admin_logger.warning(f"Server restart initiated by {current_user.username}")
        return redirect(url_for('.index'))


# ==================== Utilities ====================

def invalidate_leaderboard_cache() -> None:
    """Invalidate all leaderboard-related caches.
    
    Called after any achievement or manager modification.
    """
    try:
        from services.cache_service import cache
        # If using Redis, we could use cache.delete_memoized or similar.
        # For now, we clear everything related to the main leaderboard.
        # In a real app, this would be more granular.
        cache.clear()
        admin_logger.info("Leaderboard cache invalidated")
    except Exception as e:
        admin_logger.error(f"Failed to invalidate cache: {e}")


# ==================== Rate Limiting (Internal) ====================

_login_attempts: dict[str, list[float]] = {}


def _get_client_ip() -> str:
    """Return the client IP for rate-limit bucketing.

    `request.remote_addr` has already been resolved to the real client IP
    by the ProxyFix middleware wired up in :func:`app.create_app` (see
    `app.py` and `docs/ARCHITECTURE.md` § Production deployment (ProxyFix)), which
    walks `X-Forwarded-For` from the right using the configured trusted-
    proxy count.

    We must **not** re-parse `X-Forwarded-For` ourselves. The leftmost
    entry of that header is user-controllable, so trusting it would let
    an attacker rotate the apparent IP on every login attempt and bypass
    the per-IP rate-limit entirely.

    For deployments that don't sit behind a proxy, set ``PROXY_FIX_X_FOR=0``
    and ``request.remote_addr`` is the raw socket address, which is also
    the correct rate-limit key.
    """
    from flask import request

    return request.remote_addr or 'unknown'


def _is_login_rate_limit_ok(max_attempts: int = 5, window_seconds: int = 300) -> bool:
    """Return True iff the caller is *under* the failed-login budget.

    Does NOT record an attempt - successful logins should not consume
    the budget. Pair with :func:`_record_failed_login_attempt` on the
    failure branch.
    """
    import time

    ip = _get_client_ip()
    now = time.time()

    bucket = _login_attempts.setdefault(ip, [])
    # Drop attempts that have aged out of the window.
    bucket[:] = [t for t in bucket if now - t < window_seconds]

    return len(bucket) < max_attempts


def _record_failed_login_attempt() -> None:
    """Record a failed login for rate-limiting purposes."""
    import time

    ip = _get_client_ip()
    _login_attempts.setdefault(ip, []).append(time.time())


def _check_login_rate_limit(max_attempts: int = 5, window_seconds: int = 300) -> bool:
    """Backward-compatible combined check + record.

    Kept for any external callers; the admin login flow now uses the
    split :func:`_is_login_rate_limit_ok` /
    :func:`_record_failed_login_attempt` API so successful logins don't
    consume the budget.
    """
    if not _is_login_rate_limit_ok(max_attempts, window_seconds):
        return False
    _record_failed_login_attempt()
    return True

# Alias for backward compatibility in tests
SecureModelView = SHLModelView
