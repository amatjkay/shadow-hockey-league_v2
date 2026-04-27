"""Flask-Admin configuration for Shadow Hockey League.

This module sets up the admin interface with authentication and CRUD views
for managing countries, managers, and achievements.
"""

import json
import logging
import os
import subprocess
from typing import Any, Callable

# Monkey-patch Flask-Admin 2.0.2 BaseView._run_view to not pass 'cls' parameter
# Flask-Admin 2.0.2 passes cls=self to view functions but they don't accept it
import flask_admin.base
from flask import current_app, flash, redirect, request, url_for
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import Select2Widget
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from markupsafe import Markup
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import Form, SelectField, StringField, validators


def patched_run_view(self: Any, f: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Remove cls parameter from _run_view for compatibility."""
    # Call the function with self as positional argument instead of cls keyword
    return f(self, *args, **kwargs)


flask_admin.base.BaseView._run_view = patched_run_view

# Monkey-patch WTForms Field.__init__ to remove allow_blank parameter for Flask-Admin compatibility
# Flask-Admin passes allow_blank to fields, but WTForms 3.x doesn't accept it in base Field
from wtforms.fields.core import Field

original_field_init = Field.__init__


def patched_field_init(self: Any, *args: Any, **kwargs: Any) -> None:
    """Remove allow_blank from field options for WTForms 3.x compatibility."""
    # Remove allow_blank if present (Flask-Admin passes it but WTForms 3.x doesn't accept it)
    if "allow_blank" in kwargs:
        del kwargs["allow_blank"]
    return original_field_init(self, *args, **kwargs)


Field.__init__ = patched_field_init

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
from services.audit_service import log_action, set_current_user_for_audit
from services.cache_service import invalidate_leaderboard_cache
from services.scoring_service import get_base_points

# Logger for admin operations
admin_logger = logging.getLogger("shleague.admin")


import glob
import os
import secrets
from datetime import datetime, timedelta

from flask import current_app
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.form.upload import ImageUploadField


def get_flag_choices() -> list[tuple[str, str]]:
    """Dynamically get flag choices from static folder."""
    flags_dir = os.path.join(current_app.root_path, "static", "img", "flags")
    choices = [("", "-- Select Flag --")]

    if os.path.exists(flags_dir):
        files = sorted(os.listdir(flags_dir))
        for f in files:
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                path = f"/static/img/flags/{f}"
                choices.append((path, f))
    return choices


def get_achievement_icon_choices() -> list[tuple[str, str]]:
    """Dynamically get achievement icon choices from static folder."""
    icons_dir = os.path.join(current_app.root_path, "static", "img", "cups")
    choices = [("", "-- Select Icon --")]

    if os.path.exists(icons_dir):
        files = sorted(os.listdir(icons_dir))
        for f in files:
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".svg")):
                path = f"/static/img/cups/{f}"
                choices.append((path, f))
    return choices


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = "admin_login.index"
login_manager.login_message = "Please log in to access the admin panel."


def init_admin(app) -> None:
    """Initialize Flask-Admin and Flask-Login.

    Args:
        app: Flask application instance
    """
    # Initialize Flask-Login
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login."""
        return db.session.get(AdminUser, int(user_id))

    # Create custom admin index with dashboard stats
    import logging

    from flask import flash, redirect, request, url_for

    from services.audit_service import log_action

    admin_logger = logging.getLogger("shleague.admin")

    class StatsAdminIndexView(AdminIndexView):
        """Custom admin index view with dashboard statistics."""

        # Use custom master template with login/logout links (BUG-001)
        base_template = "admin/shl_master.html"

        @expose("/")
        def index(self):
            """Render dashboard with statistics."""
            try:
                manager_count = db.session.query(Manager).count()
                achievement_count = db.session.query(Achievement).count()
                country_count = db.session.query(Country).count()
                admin_count = db.session.query(AdminUser).count()

                # Новые счетчики
                api_key_count = db.session.query(ApiKey).count()
                audit_log_count = db.session.query(AuditLog).count()

                # Последние действия из AuditLog
                recent_logs = (
                    db.session.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
                )
            except Exception:
                manager_count = achievement_count = country_count = admin_count = 0
                api_key_count = audit_log_count = 0
                recent_logs = []

            return self.render(
                "admin/index.html",
                manager_count=manager_count,
                achievement_count=achievement_count,
                country_count=country_count,
                admin_count=admin_count,
                # Новые переменные
                api_key_count=api_key_count,
                audit_log_count=audit_log_count,
                recent_logs=recent_logs,
            )

        @expose("/flush-cache", methods=["POST"])
        @login_required
        def flush_cache(self):
            """Manually invalidate leaderboard cache."""
            try:
                # Invalidate cache
                invalidate_leaderboard_cache()

                # Log the action
                log_action(user_id=current_user.id, action="FLUSH_CACHE")
                admin_logger.info(f"FLUSH_CACHE by {current_user.username}")

                flash("Cache flushed successfully", "success")
            except Exception as e:
                admin_logger.error(f"Failed to flush cache: {e}")
                flash("Failed to flush cache", "error")

            return redirect(url_for(".index"))

    # Create admin interface
    admin = Admin(
        app,
        name="Shadow Hockey League Admin",
        url="/admin/",
        endpoint="admin",
        index_view=StatsAdminIndexView(name="Home", template="admin/index.html"),
    )

    # Add views with proper menu structure
    admin.add_view(
        ManagerModelView(
            Manager,
            db.session,
            name="Managers",
            category="Data",
            menu_icon_type="fa",
            menu_icon_value="fa-user",
        )
    )

    # Reference Data
    admin.add_view(
        CountryModelView(
            Country,
            db.session,
            name="Countries",
            category="Reference",
            menu_icon_type="fa",
            menu_icon_value="fa-flag",
        )
    )
    # Achievement CRUD moved to Manager edit page — removed from menu
    admin.add_view(AchievementModelView(Achievement, db.session, category="Data"))
    admin.add_view(
        AdminUserModelView(
            AdminUser,
            db.session,
            name="Admin Users",
            category="Settings",
            menu_icon_type="fa",
            menu_icon_value="fa-users",
        )
    )

    # Reference Data
    admin.add_view(
        AchievementTypeModelView(
            AchievementType,
            db.session,
            name="Achievement Types",
            category="Reference",
            menu_icon_type="fa",
            menu_icon_value="fa-list",
        )
    )
    admin.add_view(
        LeagueModelView(
            League,
            db.session,
            name="Leagues",
            category="Reference",
            menu_icon_type="fa",
            menu_icon_value="fa-shield",
        )
    )
    admin.add_view(
        SeasonModelView(
            Season,
            db.session,
            name="Seasons",
            category="Reference",
            menu_icon_type="fa",
            menu_icon_value="fa-calendar",
        )
    )

    # System
    admin.add_view(
        ApiKeyModelView(
            ApiKey,
            db.session,
            name="API Keys",
            category="System",
            menu_icon_type="fa",
            menu_icon_value="fa-key",
        )
    )
    admin.add_view(
        AuditLogModelView(
            AuditLog,
            db.session,
            name="Audit Log",
            category="System",
            menu_icon_type="fa",
            menu_icon_value="fa-history",
        )
    )
    admin.add_view(
        ServerControlView(
            name="Server Control",
            category="System",
            menu_icon_type="fa",
            menu_icon_value="fa-power-off",
        )
    )

    # Add Login/Logout as separate menu items
    admin.add_view(LoginView(name="Login", endpoint="admin_login", url="/admin/login"))
    admin.add_view(LogoutView(name="Logout", endpoint="admin_logout", url="/admin/logout"))


# Helper data for Countries (sorted alphabetically by name for better UX)
_raw_choices = [
    ("RUS", "Russia"),
    ("CAN", "Canada"),
    ("USA", "United States"),
    ("SWE", "Sweden"),
    ("FIN", "Finland"),
    ("CZE", "Czech Republic"),
    ("SUI", "Switzerland"),
    ("GER", "Germany"),
    ("SVK", "Slovakia"),
    ("DEN", "Denmark"),
    ("NOR", "Norway"),
    ("FRA", "France"),
    ("AUT", "Austria"),
    ("BLR", "Belarus"),
    ("KAZ", "Kazakhstan"),
    ("LAT", "Latvia"),
    ("GBR", "Great Britain"),
    ("ITA", "Italy"),
    ("UKR", "Ukraine"),
    ("POL", "Poland"),
    ("SLO", "Slovenia"),
    ("HUN", "Hungary"),
    ("JPN", "Japan"),
    ("KOR", "South Korea"),
    ("CHN", "China"),
    ("AUS", "Australia"),
    ("MEX", "Mexico"),
    ("VNM", "Vietnam"),
]
COUNTRY_CHOICES = [("", "")] + sorted(_raw_choices, key=lambda x: x[1])

# Map codes to actual flag filenames (handling legacy names or differences)
# Assuming standard 3-letter codes match filenames in most cases
COUNTRY_FLAG_MAP = {code: f"/static/img/flags/{code}.png" for code, _ in _raw_choices}
# Add specific overrides if filenames differ from ISO codes
COUNTRY_FLAG_MAP["GBR"] = "/static/img/flags/GBR.png"  # Or UK.png if exists

# JavaScript to auto-fill Name, Flag Path, and show preview
COUNTRY_AUTOFILL_JS = (
    """
<script>
$(document).ready(function() {
    var $code = $('#code');
    var $name = $('#name');
    var $flag = $('#flag_path');
    var $preview = $('#flag-preview-img');
    var flagMap = """
    + json.dumps({k: v for k, v in COUNTRY_FLAG_MAP.items()})
    + """;

    function updateCountryDetails() {
        // Wait a tick for Select2 to update data
        setTimeout(function() {
            var data = $code.select2('data');
            if (data && data.length > 0) {
                var val = data[0];
                // Update Name
                if ($name.val() === '' || $name.val() === 'Unknown') {
                    $name.val(val.text);
                }
                // Update Flag if mapping exists
                var flagUrl = flagMap[val.id];
                if (flagUrl) {
                    $flag.val(flagUrl).trigger('change');
                    $preview.attr('src', flagUrl).show();
                }
            }
        }, 50);
    }

    $code.on('select2:select', updateCountryDetails);

    // Initial check on load
    setTimeout(function() {
        var currentVal = $code.val();
        if (currentVal) {
             // Trigger update manually if value exists
             updateCountryDetails();
        }
    }, 1000);
});
</script>
"""
)

# JavaScript for Achievement Auto-fill
ACHIEVEMENT_AUTOFILL_JS = """
<script>
$(document).ready(function() {
    var $type = $('#type_id');
    var $league = $('#league_id');
    var $season = $('#season_id');
    var $title = $('#title');
    var $icon = $('#icon_path');
    var $base = $('#base_points');
    var $mult = $('#multiplier');
    var $final = $('#final_points');

    function calculate() {
        setTimeout(function() {
            var typeData = $type.select2('data');
            var leagueData = $league.select2('data');
            var seasonData = $season.select2('data');

            if (typeData.length > 0 && leagueData.length > 0 && seasonData.length > 0) {
                // Variant A Logic: Title
                $title.val(typeData[0].text + ' ' + leagueData[0].text + ' ' + seasonData[0].text);
                // Variant A Logic: Icon
                $icon.val('/static/img/achievements/' + typeData[0].id + '.png');
                // Note: Points logic happens on Server
            }
        }, 50);
    }

    $type.on('select2:select', calculate);
    $league.on('select2:select', calculate);
    $season.on('select2:select', calculate);
});
</script>
"""


# Helper function to get (code, name) tuples for reference tables
def _get_ref_data_choices(model: Any) -> list[tuple[str, str]]:
    """Returns list of tuples (code, name) for reference tables."""
    try:
        items = db.session.query(model.code, model.name).order_by(model.code).all()
        return [("", "-- Select --")] + [(code, name) for code, name in items]
    except Exception:
        return [("", "-- Error loading --")]


# Helper function to get (id, name) tuples for FK relationships
def _get_choice_tuples(model: Any) -> list[tuple[str, str]]:
    """Returns list of tuples (id, name) for reference tables."""
    try:
        items = db.session.query(model.id, model.name).order_by(model.code).all()
        return [("", "-- Select --")] + [(str(i.id), n) for i, n in items]
    except Exception:
        return [("", "-- Error loading --")]


class SecureModelView(ModelView):
    """Base model view with authentication and audit logging."""

    def is_accessible(self):
        """Check if user is authenticated and set current user for audit."""
        if current_user.is_authenticated:
            set_current_user_for_audit(current_user.id)
            return True
        return False

    def _has_permission(self, permission: str) -> bool:
        """Check if current user has the required permission."""
        if not current_user.is_authenticated:
            return False
        return current_user.has_permission(permission)

    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login if not accessible."""
        flash("Please log in to access this page.", "warning")
        return redirect(url_for("admin_login.index", next=request.url))

    def create_model(self, form):
        """Create model with permission check and audit logging."""
        if not self._has_permission("create"):
            flash("Insufficient permissions to create.", "error")
            return None
        model = super().create_model(form)
        if model and current_user.is_authenticated:
            try:
                log_action(
                    user_id=current_user.id,
                    action="CREATE",
                    target_model=self.model.__name__,
                    target_id=getattr(model, "id", None),
                )
                admin_logger.info(
                    f"CREATE {self.model.__name__} by {current_user.username}: "
                    f"id={getattr(model, 'id', 'N/A')}"
                )
            except Exception as e:
                admin_logger.error(f"Failed to log CREATE action: {e}")
        return model

    def update_model(self, form, model):
        """Update model with permission check and audit logging."""
        if not self._has_permission("edit"):
            flash("Insufficient permissions to edit.", "error")
            return False
        # Capture changes before update
        old_values = {}
        if hasattr(model, "__table__"):
            for column in model.__table__.columns:
                old_values[column.name] = getattr(model, column.name)

        result = super().update_model(form, model)

        if result and current_user.is_authenticated:
            try:
                # Capture new values after update
                new_values = {}
                changes = {}
                if hasattr(model, "__table__"):
                    for column in model.__table__.columns:
                        new_value = getattr(model, column.name)
                        if old_values[column.name] != new_value:
                            changes[column.name] = {
                                "old": old_values[column.name],
                                "new": new_value,
                            }

                log_action(
                    user_id=current_user.id,
                    action="UPDATE",
                    target_model=self.model.__name__,
                    target_id=getattr(model, "id", None),
                    changes=changes if changes else None,
                )
                admin_logger.info(
                    f"UPDATE {self.model.__name__} by {current_user.username}: "
                    f"id={getattr(model, 'id', 'N/A')}"
                )
            except Exception as e:
                admin_logger.error(f"Failed to log UPDATE action: {e}")

        return result

    def delete_model(self, model):
        """Delete model with permission check and audit logging."""
        if not self._has_permission("delete"):
            flash("Insufficient permissions to delete.", "error")
            return False
        model_id = getattr(model, "id", "N/A")
        model_name = self.model.__name__

        result = super().delete_model(model)

        if result and current_user.is_authenticated:
            try:
                log_action(
                    user_id=current_user.id,
                    action="DELETE",
                    target_model=model_name,
                    target_id=model_id if model_id != "N/A" else None,
                )
                admin_logger.info(f"DELETE {model_name} by {current_user.username}: id={model_id}")
            except Exception as e:
                admin_logger.error(f"Failed to log DELETE action: {e}")

        return result


class CountryModelView(SecureModelView):
    """Admin view for Country CRUD operations."""

    name = "Countries"
    column_list = ("id", "code", "name", "flag_path")
    column_searchable_list = ("code", "name")
    column_filters = ("code", "name")
    # Simplified form_columns — flag_source_type/flag_url disabled until WTForms compatibility is resolved
    form_columns = ("code", "name", "flag_path")
    column_default_sort = ("name", False)

    column_labels = {"code": "Country", "name": "Name (Auto)", "flag_path": "Flag Img"}

    form_overrides = {
        "code": SelectField,
        "flag_path": SelectField,
    }

    form_args = {
        "code": {
            "choices": COUNTRY_CHOICES,
            "validators": [
                validators.DataRequired(message="Country code is required"),
                validators.Regexp(
                    r"^[A-Z]{2,3}$",
                    message="Country code must be 2-3 uppercase letters (e.g., RU, USA)",
                ),
                validators.Length(min=2, max=3, message="Country code must be 2-3 characters"),
            ],
        },
        "flag_path": {"choices": get_flag_choices, "validators": []},
        "name": {"validators": []},
    }

    form_widget_args = {
        "code": {},
        "flag_path": {},
        "name": {"readonly": True, "style": "background-color: #f0f0f0;"},
    }

    # Размер картинки (соответствует стилю главной страницы)
    column_formatters = {
        "flag_path": lambda v, c, m, p: (
            Markup(
                f'<img src="{m.flag_display_url}" width="32" height="24" style="border: 1px solid #ccc;">'
            )
            if m.flag_path or m.flag_url
            else ""
        )
    }

    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)
        form.extra_js = COUNTRY_AUTOFILL_JS
        form.extra_html = Markup(
            '<img id="flag-preview-img" src="" style="display:none; margin-top:10px; border:1px solid #ccc; max-width:64px;">'
        )
        return form

    def edit_form(self, obj, **kwargs):
        form = super().edit_form(obj, **kwargs)
        form.extra_js = COUNTRY_AUTOFILL_JS
        form.extra_html = Markup(
            f'<img id="flag-preview-img" src="{obj.flag_path}" style="margin-top:10px; border:1px solid #ccc; max-width:64px;">'
            if obj.flag_path
            else '<img id="flag-preview-img" src="" style="display:none; margin-top:10px; border:1px solid #ccc; max-width:64px;">'
        )
        return form

    def on_model_change(self, form, model, is_created):
        """Автоматическое заполнение name на основе code."""
        if form.code.data:
            model.name = dict(COUNTRY_CHOICES).get(form.code.data, "Unknown")
        invalidate_leaderboard_cache()

    def delete_model(self, model):
        """Prevent deletion if managers exist."""
        # Check if any managers use this country
        manager_count = db.session.query(Manager).filter_by(country_id=model.id).count()
        if manager_count > 0:
            flash(
                f'Невозможно удалить страну "{model.name}". Она используется у {manager_count} менеджер(ов). Сначала измените их страну.',
                "error",
            )
            return False

        result = super().delete_model(model)
        if result:
            invalidate_leaderboard_cache()
        return result


class ManagerModelView(SecureModelView):
    """Admin view for Manager CRUD operations."""

    name = "Managers"

    create_template = "admin/manager_create.html"
    edit_template = "admin/manager_edit.html"
    list_template = "admin/manager_list.html"

    # Updated column list with flag, stats, and status
    column_list = (
        "id",
        "flag",
        "name",
        "country",
        "achievement_count",
        "total_points",
        "is_active",
        "manage_achievements",
    )
    column_searchable_list = ("name",)
    column_filters = ("country.name", "is_active")
    form_columns = ("name", "country", "is_active")
    column_default_sort = ("name", False)

    # Используем SelectField для country (QuerySelectField не совместим с Select2 ajax)
    form_overrides = {
        "country": SelectField,
    }

    def get_country_choices():
        """Get countries for SelectField choices."""
        from data.static_paths import StaticPaths

        paths = StaticPaths()
        choices = [("", "-- Select Country --")]
        countries = db.session.query(Country).filter_by(is_active=True).order_by(Country.name).all()
        for c in countries:
            # Use code_to_flag to get display name
            display_name = paths.code_to_flag(c.code)
            if display_name:
                display_name = display_name.replace(".png", "")
            else:
                display_name = c.name
            choices.append((str(c.id), f"{display_name} ({c.code})"))
        return choices

    form_args = {
        "name": {
            "validators": [
                validators.DataRequired(message="Manager name is required"),
                validators.Regexp(
                    r"^[a-zA-Z0-9\s,.\'-]+$",
                    message="Name can only contain letters, numbers, spaces, commas, periods, hyphens and apostrophes",
                ),
                validators.Length(
                    min=2, max=100, message="Name must be between 2 and 100 characters"
                ),
            ]
        },
        "country": {
            "choices": get_country_choices,
            "validators": [validators.DataRequired(message="Country is required")],
        },
    }

    form_widget_args = {"country": {"class": "form-control"}}

    # Formatters
    def _get_flag(view, context, model, name):
        if model.country and model.country.flag_display_url:
            return Markup(
                f'<img src="{model.country.flag_display_url}" width="24" alt="{model.country.code}">'
            )
        return "—"

    def _format_name(view, context, model, name):
        return (
            model.display_name if hasattr(model, "display_name") else (model.name or str(model.id))
        )

    def _get_country(view, context, model, name):
        if model.country:
            return f"{model.country.name} ({model.country.code})"
        return "Unknown"

    def _get_achievement_count(view, context, model, name):
        return len(model.achievements)

    def _get_total_points(view, context, model, name):
        return round(sum(a.final_points for a in model.achievements), 2)

    def _get_status(view, context, model, name):
        return Markup("🟢") if model.is_active else Markup("🔴")

    def _manage_achievements(view, context, model, name):
        url = url_for(".edit_view", id=model.id)
        return Markup(f'<a href="{url}">🏆 Manage ({len(model.achievements)})</a>')

    column_formatters = {
        "flag": _get_flag,
        "name": _format_name,
        "country": _get_country,
        "achievement_count": _get_achievement_count,
        "total_points": _get_total_points,
        "is_active": _get_status,
        "manage_achievements": _manage_achievements,
    }

    column_labels = {
        "flag": "",
        "name": "Name",
        "country": "Country",
        "achievement_count": "Ach.",
        "total_points": "Points",
        "is_active": "Status",
        "manage_achievements": "Actions",
    }

    def create_model(self, form):
        """Create manager with proper country handling."""
        try:
            model = Manager()
            # Manually set country from ID
            country_id = form.country.data
            if country_id:
                country = db.session.get(Country, int(country_id))
                if country:
                    model.country = country
            # Set other fields
            model.name = form.name.data
            model.is_active = form.is_active.data if hasattr(form, "is_active") else True

            db.session.add(model)
            db.session.commit()

            # Log and invalidate cache
            if current_user.is_authenticated:
                log_action(
                    user_id=current_user.id,
                    action="CREATE",
                    target_model="Manager",
                    target_id=model.id,
                )
            invalidate_leaderboard_cache()
            return model
        except Exception as e:
            db.session.rollback()
            admin_logger.error(f"Error creating manager: {e}")
            raise

    def update_model(self, form, model):
        """Update manager with proper country handling."""
        try:
            # Manually update country from ID
            country_id = form.country.data
            if country_id:
                country = db.session.get(Country, int(country_id))
                if country:
                    model.country = country
            # Update other fields
            model.name = form.name.data
            model.is_active = form.is_active.data

            db.session.commit()

            # Log and invalidate cache
            if current_user.is_authenticated:
                log_action(
                    user_id=current_user.id,
                    action="UPDATE",
                    target_model="Manager",
                    target_id=model.id,
                )
            invalidate_leaderboard_cache()
            return True
        except Exception as e:
            db.session.rollback()
            admin_logger.error(f"Error updating manager: {e}")
            raise

    def on_model_change(self, form, model, is_created):
        """Invalidate cache and show tandem warning if applicable."""
        # Tandem detection warning (server-side)
        if "," in model.name:
            flash("⚠️ Tandem detected. Ensure both players represent one country", "warning")

        invalidate_leaderboard_cache()

    def on_model_delete(self, model):
        invalidate_leaderboard_cache()


class AchievementModelView(SecureModelView):
    """Admin view for Achievement CRUD operations (FK-based)."""

    name = "Achievements"

    create_template = "admin/achievement_create.html"
    edit_template = "admin/achievement_edit.html"

    column_list = ("id", "type", "league", "season", "manager", "final_points")
    column_searchable_list = ("title",)
    column_filters = ("league.code", "season.code", "type.code", "manager.name")
    form_columns = (
        "manager",
        "type",
        "league",
        "season",
        "title",
        "icon_path",
        "base_points",
        "multiplier",
        "final_points",
    )
    column_default_sort = ("manager.name", False)

    # Убираем form_overrides, чтобы Flask-Admin сам создал правильные поля для связей (QuerySelectField)
    # Используем form_args для настройки отображения
    form_args = {
        "type": {
            "query_factory": lambda: db.session.query(AchievementType).order_by(
                AchievementType.name
            ),
            "get_label": "name",
        },
        "league": {
            "query_factory": lambda: db.session.query(League).order_by(League.name),
            "get_label": "name",
        },
        "season": {
            "query_factory": lambda: db.session.query(Season).order_by(Season.name),
            "get_label": "name",
        },
        "base_points": {
            "label": "Base Points",
            "render_kw": {"readonly": True, "class": "form-control"},
        },
        "multiplier": {
            "label": "Multiplier",
            "render_kw": {"readonly": True, "class": "form-control"},
        },
        "final_points": {
            "label": "Points",
            "render_kw": {"readonly": True, "class": "form-control"},
        },
    }

    form_overrides = {"icon_path": SelectField}

    form_widget_args = {
        "type": {"class": "form-control select2"},
        "league": {"class": "form-control select2"},
        "season": {"class": "form-control select2"},
        "base_points": {"readonly": True},
        "multiplier": {"readonly": True},
        "final_points": {"readonly": True},
    }

    column_labels = {
        "type": "Type",
        "league": "League",
        "season": "Season",
        "manager": "Manager",
        "final_points": "Points",
    }

    # Форматтеры для списка — отображают данные relationships
    column_formatters = {
        "type": lambda v, c, m, p: m.type.name if m.type else "-",
        "league": lambda v, c, m, p: m.league.name if m.league else "-",
        "season": lambda v, c, m, p: m.season.name if m.season else "-",
        "manager": lambda v, c, m, p: m.manager.name if m.manager else "-",
        "icon_path": lambda v, c, m, p: (
            Markup(f'<img src="{m.icon_path}" style="height:32px;">') if m.icon_path else "-"
        ),
    }

    def create_form(self, obj=None):
        form = super().create_form(obj=obj)
        # Подхват менеджера из URL
        manager_id = request.args.get("manager_id")
        if manager_id:
            form.manager.data = db.session.query(Manager).get(int(manager_id))

        # Icon choices
        form.icon_path.choices = get_achievement_icon_choices()

        # Генерируем JS для автозаполнения
        form.extra_js = self._get_achievement_js()
        return form

    def edit_form(self, obj):
        form = super().edit_form(obj)
        # Icon choices
        form.icon_path.choices = get_achievement_icon_choices()
        form.extra_js = self._get_achievement_js()
        return form

    def _get_achievement_js(self, current_type=None, current_league=None, current_season=None):
        """Генерирует JS с данными для автозаполнения."""
        # Собираем полные данные для JS
        types = [
            (t.id, t.name, t.code, t.base_points_l1, t.base_points_l2)
            for t in db.session.query(AchievementType).all()
        ]
        leagues = [(l.id, l.name, l.code) for l in db.session.query(League).all()]
        seasons = [(s.id, s.name, s.code, s.multiplier) for s in db.session.query(Season).all()]

        return f"""
        <script>
        $(document).ready(function() {{
            var TYPES = {json.dumps(types)};
            var LEAGUES = {json.dumps(leagues)};
            var SEASONS = {json.dumps(seasons)};

            var $type = $('#type');
            var $league = $('#league');
            var $season = $('#season');
            var $title = $('#title');
            var $icon = $('#icon_path');
            var $base = $('#base_points');
            var $mult = $('#multiplier');
            var $final = $('#final_points');

            function calculate() {{
                // Ждем инициализации Select2
                setTimeout(function() {{
                    var tId = $type.val();
                    var lId = $league.val();
                    var sId = $season.val();

                    if (tId && lId && sId) {{
                        var t = TYPES.find(x => x[0] == tId);
                        var l = LEAGUES.find(x => x[0] == lId);
                        var s = SEASONS.find(x => x[0] == sId);

                        if (t && l && s) {{
                            // 1. Title
                            $title.val(t[1] + ' ' + l[1] + ' ' + s[1]);
                            // 2. Icon
                            $icon.val('/static/img/achievements/' + t[2] + '.png');
                            // 3. Points
                            var isL1 = (l[2] == '1'); 
                            var base = isL1 ? t[3] : t[4];
                            var mult = s[3];
                            $base.val(base);
                            $mult.val(mult);
                            $final.val((base * mult).toFixed(2));
                        }}
                    }}
                }}, 100);
            }}

            $type.on('select2:select change', calculate);
            $league.on('select2:select change', calculate);
            $season.on('select2:select change', calculate);

            // Запуск при загрузке, если данные уже есть
            calculate();
        }});
        </script>
        """

    def on_model_change(self, form, model, is_created):
        # Автозаполнение на сервере
        # Т.к. используем SelectField, form.type.data - это ID
        if form.type.data and form.league.data and form.season.data:
            type_obj = db.session.get(AchievementType, form.type.data)
            league_obj = db.session.get(League, form.league.data)
            season_obj = db.session.get(Season, form.season.data)

            if type_obj and league_obj and season_obj:
                # Title & Icon (Variant A)
                model.title = f"{type_obj.name} {league_obj.name} {season_obj.name}"
                model.icon_path = f"/static/img/achievements/{type_obj.code}.png"

                # Points Logic (league-aware: honours League.parent_code for subleagues)
                model.base_points = get_base_points(type_obj, league_obj)
                model.multiplier = float(season_obj.multiplier)
                model.final_points = model.base_points * model.multiplier

        invalidate_leaderboard_cache()

    def on_model_delete(self, model):
        """Invalidate cache when achievement is deleted."""
        invalidate_leaderboard_cache()


class AdminUserModelView(SecureModelView):
    """Admin view for managing admin users."""

    # Page title (BUG-002)
    name = "Admin Users"

    column_list = ("username", "role")
    column_searchable_list = ("username",)
    column_filters = ("role",)
    form_columns = ("username", "password_hash", "role")

    form_args = {
        "role": {
            "choices": AdminUser.ROLE_CHOICES,
        }
    }

    # Only super_admin can manage users
    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        set_current_user_for_audit(current_user.id)
        if not current_user.has_permission("manage_users"):
            flash("Access denied. Super Admin role required.", "error")
            return False
        return True

    # Hide password from list
    def _list_password(self, model):
        return "***"

    # Form handling for password
    def on_model_change(self, form, model, is_created):
        """Hash password when creating/updating user."""
        if form.password_hash.data:
            model.set_password(form.password_hash.data)
        elif not is_created:
            # Keep existing password if not changed
            pass

    def on_model_delete(self, model):
        """Prevent deleting last admin user."""
        user_count = db.session.query(AdminUser).count()
        if user_count <= 1:
            flash("Cannot delete the last admin user.", "error")
            return False
        return True


# ==================== NEW VIEWS (Reference & System) ====================


class AchievementTypeModelView(SecureModelView):
    """Admin view for managing achievement types and base points.

    Supports custom icon_path with fallback to /static/img/cups/default.svg.
    V-006: base_points cannot be negative.
    Triggers point recalculation when base_points change.
    """

    name = "Achievement Types"
    category = "Reference"
    create_template = "admin/achievement_type_create.html"
    edit_template = "admin/achievement_type_edit.html"
    column_list = ("code", "name", "base_points_l1", "base_points_l2", "is_active")
    column_searchable_list = ("code", "name")
    column_filters = ("code", "name", "is_active")
    form_columns = ("code", "name", "base_points_l1", "base_points_l2", "icon_path", "is_active")
    column_default_sort = ("code", False)

    column_formatters = {
        "icon_path": lambda v, c, m, p: (
            f'<img src="{m.icon_path}" width="24" alt="">' if m.icon_path else "—"
        ),
    }

    form_widget_args = {
        "base_points_l1": {"style": "width: 80px"},
        "base_points_l2": {"style": "width: 80px"},
    }

    column_labels = {
        "code": "Code",
        "name": "Name",
        "base_points_l1": "Points L1",
        "base_points_l2": "Points L2",
        "icon_path": "Icon",
    }

    form_args = {
        "code": {
            "validators": [
                validators.DataRequired(),
                validators.Regexp(
                    r"^[A-Z0-9_]+$",
                    message="Code must be uppercase letters, numbers, and underscores",
                ),
            ],
        },
        "name": {
            "validators": [validators.DataRequired()],
        },
        "base_points_l1": {
            "validators": [validators.NumberRange(min=0, message="Base points cannot be negative")],
        },
        "base_points_l2": {
            "validators": [validators.NumberRange(min=0, message="Base points cannot be negative")],
        },
        "icon_path": {
            "validators": [
                validators.Optional(),
                validators.Regexp(
                    r"^/static/img/cups/.*\.(svg|png)$",
                    message="Icon must be /static/img/cups/*.svg or *.png",
                ),
            ],
        },
    }

    def on_model_change(self, form, model, is_created):
        """V-006: Validate base_points and auto-set icon_path.

        Also triggers recalculation if base_points change.
        """
        # Auto-uppercase code
        model.code = model.code.upper().strip()

        # Auto-set icon_path if empty
        if not model.icon_path:
            model.icon_path = f"/static/img/cups/{model.code.lower()}.svg"

        # Fallback for missing icon
        from pathlib import Path

        icon_filename = model.icon_path.split("/")[-1]
        icon_full_path = Path(__file__).parent.parent / "static" / "img" / "cups" / icon_filename
        if not icon_full_path.exists():
            model.icon_path = "/static/img/cups/default.svg"

        # Trigger recalculation if points changed
        if not is_created:
            old = AchievementType.query.get(model.id)
            if old and (
                old.base_points_l1 != model.base_points_l1
                or old.base_points_l2 != model.base_points_l2
            ):
                from services.recalc_service import recalc_by_achievement_type

                result = recalc_by_achievement_type(model.id)
                if result["errors"]:
                    flash(f"Error recalculating points: {', '.join(result['errors'])}", "error")
                elif result["affected"] > 0:
                    flash(f"Recalculated points for {result['affected']} achievements.", "info")

    def delete_model(self, model):
        """V-008: Prevent deletion if achievements exist."""
        count = Achievement.query.filter_by(type_id=model.id).count()
        if count > 0:
            flash(
                f'Cannot delete "{model.code}": used in {count} achievements. Deactivate instead.',
                "error",
            )
            return False
        return super().delete_model(model)


class LeagueModelView(SecureModelView):
    """Admin view for managing leagues.

    Supports parent_code for subleagues (e.g. 2.1, 2.2 are subleagues of 2).
    """

    name = "Leagues"
    column_list = ("code", "name", "parent_code", "is_active")
    column_searchable_list = ("code", "name")
    column_filters = ("code", "name", "parent_code", "is_active")
    form_columns = ("code", "name", "parent_code", "is_active")
    column_default_sort = ("code", False)

    form_args = {
        "code": {
            "validators": [
                validators.DataRequired(),
                validators.Regexp(
                    r"^[\w.]+$", message="Code can only contain letters, numbers, and dots"
                ),
            ],
        },
        "name": {
            "validators": [validators.DataRequired()],
        },
    }

    def delete_model(self, model):
        """V-008: Prevent deletion if achievements exist."""
        count = Achievement.query.filter_by(league_id=model.id).count()
        if count > 0:
            flash(
                f'Cannot delete "{model.code}": used in {count} achievements. Deactivate instead.',
                "error",
            )
            return False
        return super().delete_model(model)


class SeasonModelView(SecureModelView):
    """Admin view for managing seasons and multipliers.

    V-009: Cannot deactivate the last active season.
    """

    name = "Seasons"
    column_list = ("code", "name", "multiplier", "start_year", "end_year", "is_active")
    column_searchable_list = ("code", "name")
    column_filters = ("code", "name", "is_active", "multiplier")
    form_columns = ("code", "name", "multiplier", "start_year", "end_year", "is_active")
    column_default_sort = ("start_year", True)

    column_formatters = {
        "is_active": lambda v, c, m, p: "✅" if m.is_active else "❌",
        "multiplier": lambda v, c, m, p: f"×{m.multiplier:.2f}",
    }

    form_widget_args = {
        "is_active": {"class": "form-check-input"},
    }

    form_args = {
        "code": {
            "validators": [
                validators.DataRequired(),
                validators.Regexp(
                    r"^\d{2}/\d{2}$", message="Code must be in YY/YY format (e.g. 24/25)"
                ),
            ],
        },
        "name": {
            "validators": [validators.DataRequired()],
        },
        "multiplier": {
            "validators": [validators.NumberRange(min=0.01, message="Multiplier must be ≥ 0.01")],
        },
    }

    def on_model_change(self, form, model, is_created):
        """V-009: Prevent deactivating the last active season.
        Also triggers recalculation if multiplier changes.
        """
        # V-009 Check
        if not is_created and not model.is_active:
            active_count = Season.query.filter_by(is_active=True).count()
            if active_count <= 1:
                raise ValueError(
                    "Cannot deactivate the last active season. Activate another season first."
                )

        # Trigger recalculation if multiplier changed
        if not is_created:
            old = Season.query.get(model.id)
            if old and old.multiplier != model.multiplier:
                from services.recalc_service import recalc_by_season

                result = recalc_by_season(model.id)
                if result["errors"]:
                    flash(f"Error recalculating points: {', '.join(result['errors'])}", "error")
                elif result["affected"] > 0:
                    flash(f"Recalculated points for {result['affected']} achievements.", "info")

    def delete_model(self, model):
        """V-008: Prevent deletion if achievements exist."""
        count = Achievement.query.filter_by(season_id=model.id).count()
        if count > 0:
            flash(
                f'Cannot delete "{model.code}": used in {count} achievements. Deactivate instead.',
                "error",
            )
            return False
        return super().delete_model(model)


class ApiKeyModelView(SecureModelView):
    """Admin view for managing API keys."""

    name = "API Keys"
    # Используем revoked (колонка БД) вместо is_active (свойство модели)
    column_list = ("name", "scope", "revoked", "created_at", "last_used_at")
    column_searchable_list = ("name",)
    column_filters = ("scope", "revoked")
    form_columns = ("name", "scope", "expires_at", "revoked")
    column_default_sort = ("created_at", True)

    column_formatters = {
        "key_hash": lambda v, c, m, p: "***",
        "revoked": lambda v, c, m, p: "🚫" if m.revoked else "✅",
    }

    form_overrides = {
        "key_hash": StringField,
    }

    form_args = {
        "key_hash": {
            "label": "API Key (Скопируйте сейчас!)",
            "validators": [],
            "render_kw": {"readonly": True},
        }
    }

    form_widget_args = {
        "key_hash": {"readonly": True},
        "expires_at": {"class": "form-control", "placeholder": "YYYY-MM-DD HH:MM:SS"},
    }

    def create_form(self):
        """Clear key_hash field for new key creation."""
        form = super().create_form()
        form.key_hash.data = ""
        return form

    def on_model_change(self, form, model, is_created):
        """Generate and hash new API key on creation."""
        if is_created:
            # Генерируем новый ключ
            new_key = secrets.token_urlsafe(32)
            # Сохраняем ключ во временное поле формы, чтобы показать пользователю
            form.key_hash.data = new_key
            # Хэшируем для хранения в БД
            model.key_hash = generate_password_hash(new_key)
            # Flash с предупреждением
            flash(
                Markup(
                    f"🔑 Новый API ключ создан! <strong>Скопируйте его сейчас:</strong><br>"
                    f'<code style="background:#f0f0f0; padding:8px; display:block; margin:8px 0; '
                    f'font-size:14px; user-select:all;">{new_key}</code>'
                    f'<span style="color:red;">⚠️ Он больше не будет показан!</span>'
                ),
                "warning",
            )
        else:
            # При обновлении не трогаем хэш, если он уже есть
            if not model.key_hash.startswith("pbkdf2:sha256:"):
                model.key_hash = generate_password_hash(model.key_hash)


class AchievementModelView(SecureModelView):
    """Admin view for viewing all achievements with filters.

    Creation is disabled here (use Manager view or Bulk Create).
    """

    name = "All Achievements"
    category = "Data"
    menu_icon_type = "fa"
    menu_icon_value = "fa-trophy"

    column_list = ("manager", "type", "league", "season", "final_points", "created_at")
    column_filters = ("manager_id", "type_id", "league_id", "season_id")
    column_searchable_list = ("manager.name", "type.code", "season.code")
    column_labels = {
        "manager": "Manager",
        "type": "Type",
        "league": "League",
        "season": "Season",
        "final_points": "Points",
    }

    column_formatters = {
        "manager": lambda v, c, m, p: m.manager.name if m.manager else "Unknown",
        "type": lambda v, c, m, p: m.type.code if m.type else "Unknown",
        "league": lambda v, c, m, p: m.league.code if m.league else "Unknown",
        "season": lambda v, c, m, p: m.season.code if m.season else "Unknown",
    }

    # Default sort by points descending
    column_default_sort = ("final_points", True)

    form_args = {
        "manager": {"query_factory": lambda: db.session.query(Manager).order_by(Manager.name)},
        "type": {
            "query_factory": lambda: db.session.query(AchievementType).order_by(
                AchievementType.code
            )
        },
        "league": {"query_factory": lambda: db.session.query(League).order_by(League.code)},
        "season": {"query_factory": lambda: db.session.query(Season).order_by(Season.code.desc())},
    }

    can_create = False
    can_edit = True
    can_delete = True

    def delete_model(self, model):
        """V-008: Confirm before deletion (optional, handled by JS usually)."""
        return super().delete_model(model)


class AuditLogModelView(SecureModelView):
    """Admin view for viewing audit logs (Read-Only + Bulk Delete)."""

    name = "Audit Log"
    can_create = False
    can_edit = False
    can_delete = False  # Only bulk delete is allowed, individual delete is disabled
    can_view_details = True

    column_list = ("timestamp", "user_id", "action", "target_model", "target_id")
    column_filters = ("user_id", "action", "target_model", "timestamp")
    column_default_sort = ("timestamp", True)

    column_formatters = {
        "changes": lambda v, c, m, p: (
            f'<pre style="max-width:300px; white-space:pre-wrap;">{m.changes}</pre>'
            if m.changes
            else ""
        ),
    }

    # Bulk delete action
    @action(
        "delete_selected", "Delete Selected", "Are you sure you want to delete these log entries?"
    )
    def action_delete_selected(self, ids):
        count = 0
        for audit_id in ids:
            model = db.session.get(AuditLog, int(audit_id))
            if model:
                db.session.delete(model)
                count += 1
        db.session.commit()
        flash(f"Удалено записей: {count}", "success")


class ServerControlView(BaseView):
    """View for server administration actions like restart."""

    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        if not current_user.has_permission("server_control"):
            flash("Access denied. Super Admin role required.", "error")
            return False
        set_current_user_for_audit(current_user.id)
        return True

    @expose("/")
    def index(self):
        return self.render("admin/server_control.html")

    @expose("/restart", methods=["POST"])
    def restart(self):
        """Restart the service."""
        # Log the restart action
        user_id = current_user.id if current_user.is_authenticated else None
        platform = "windows" if os.name == "nt" else "linux"
        try:
            log_action(
                user_id=user_id,
                action="SERVER_RESTART",
                target_model="Server",
                changes={"platform": platform},
            )
            admin_logger.info(f"SERVER_RESTART initiated by user_id={user_id} on {platform}")
        except Exception as e:
            admin_logger.error(f"Failed to log SERVER_RESTART action: {e}")

        try:
            if os.name == "nt":
                # Windows (Local Dev): Just stop the process.
                # User needs to restart it manually in console.
                flash(
                    "Server stopped. Please restart it manually in the console (`python app.py`).",
                    "info",
                )
                # Return a page that tells user to restart
                return '<html><body style="font-family:sans-serif; text-align:center; margin-top:50px;"><h1>🛑 Server Stopped</h1><p>Please restart via console: <code>python app.py</code></p></body></html>'
                # Use background thread to kill self after response?
                # No, simple exit is safer for dev.
                import threading

                def suicide():
                    import time

                    time.sleep(1)
                    import os

                    os._exit(0)

                threading.Thread(target=suicide).start()
                return redirect(url_for(".index"))
            else:
                # Linux (Production): Use systemctl
                subprocess.Popen(["sudo", "systemctl", "restart", "shadow-hockey-league"])
                return '<html><body style="font-family:sans-serif; text-align:center; margin-top:50px;"><h1>🔄 Restarting Server...</h1><p>Please wait a moment.</p><script>setTimeout(()=>window.location.href="/admin/", 5000);</script></body></html>'
        except Exception as e:
            flash(f"Failed to restart: {str(e)}", "error")
            return redirect(url_for(".index"))


# ==================== RATE LIMITING FOR LOGIN ====================

_login_attempts = {}  # {ip: [(timestamp, ...)]}


def _check_login_rate_limit(max_attempts: int = 10, window_seconds: int = 60) -> bool:
    """Check if IP has exceeded login attempt limit. Returns True if allowed."""
    import time

    from flask import request

    ip = request.remote_addr or "unknown"
    now = time.time()
    cutoff = now - window_seconds

    # Clean old attempts
    if ip in _login_attempts:
        _login_attempts[ip] = [t for t in _login_attempts[ip] if t > cutoff]
    else:
        _login_attempts[ip] = []

    # Check limit
    if len(_login_attempts[ip]) >= max_attempts:
        return False

    # Record attempt
    _login_attempts[ip].append(now)
    return True


# ==================== LOGIN / LOGOUT ====================


class LoginView(BaseView):
    """Login view for admin panel."""

    @expose("/", methods=["GET", "POST"])
    def index(self):
        """Handle login form."""
        if current_user.is_authenticated:
            return redirect(url_for("admin.index"))

        if request.method == "POST":
            # Rate limiting check (10 attempts per minute per IP)
            if not _check_login_rate_limit():
                flash("Too many login attempts. Please wait 60 seconds.", "error")
                admin_logger.warning("LOGIN rate limit exceeded for IP %s", request.remote_addr)
                return self.render("admin/login.html"), 429

            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            remember = request.form.get("remember", False)

            user = db.session.query(AdminUser).filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user, remember=remember)
                flash("Logged in successfully.", "success")

                # Set current user for audit logging
                set_current_user_for_audit(user.id)

                # Log successful login
                try:
                    log_action(user_id=user.id, action="LOGIN")
                    admin_logger.info(f"LOGIN successful for user {username}")
                except Exception as e:
                    admin_logger.error(f"Failed to log LOGIN action: {e}")

                next_page = request.args.get("next")
                return redirect(next_page or url_for("admin.index"))
            else:
                flash("Invalid username or password.", "error")
                admin_logger.warning(f"LOGIN failed for user {username}")

        return self.render("admin/login.html")


class LogoutView(BaseView):
    """Logout view for admin panel."""

    @expose("/")
    @login_required
    def index(self):
        """Handle logout."""
        logout_user()
        flash("Logged out successfully.", "info")
        return redirect(url_for("admin_login.index"))
