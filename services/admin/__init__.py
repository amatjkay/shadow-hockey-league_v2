"""Admin service: Flask-Admin + Flask-Login configuration.

The package preserves the public surface previously exposed by
``services/admin.py``. External callers (``app.py``, tests) import
``init_admin`` and the ModelView classes directly from
``services.admin``; the layout below makes that possible without source-
level changes.

Layout:

* ``base.py`` — :class:`SHLModelView` base
* ``views.py`` — concrete ModelViews + audit formatters + ServerControlView
* ``_rate_limit.py`` — module-level rate-limit bucket and helpers used by
  :class:`SHLAdminIndexView` and exposed for tests
"""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, flash, redirect, request, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.theme import Bootstrap4Theme
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

from data.static_paths import get_flag_choices  # noqa: F401  (re-exported for tests)
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
from services.admin._rate_limit import (
    _check_login_rate_limit,
    _get_client_ip,
    _is_login_rate_limit_ok,
    _login_attempts,
    _record_failed_login_attempt,
)
from services.admin.base import SecureModelView, SHLModelView
from services.admin.views import (
    AchievementModelView,
    AchievementTypeModelView,
    AdminUserModelView,
    ApiKeyModelView,
    AuditLogModelView,
    CountryModelView,
    LeagueModelView,
    ManagerModelView,
    SeasonModelView,
    ServerControlView,
)
from services.cache_service import invalidate_leaderboard_cache

admin_logger = logging.getLogger("shleague.admin")


def init_admin(app: Flask) -> None:
    """Initialize Flask-Admin and Flask-Login for the application.

    Args:
        app: Flask application instance.
    """
    # Initialize LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "admin.login"

    @login_manager.user_loader
    def load_user(user_id: str) -> AdminUser | None:
        return db.session.get(AdminUser, int(user_id))

    # Initialize Admin with custom index view
    admin = Admin(
        app,
        name="SH League Admin",
        index_view=SHLAdminIndexView(),
        theme=Bootstrap4Theme(base_template="admin/shl_master.html"),
    )

    # Add model views
    admin.add_view(CountryModelView(Country, db, category="Core"))
    admin.add_view(ManagerModelView(Manager, db, category="Core"))
    admin.add_view(AchievementModelView(Achievement, db, category="Data"))

    admin.add_view(AchievementTypeModelView(AchievementType, db, category="Reference"))
    admin.add_view(LeagueModelView(League, db, category="Reference"))
    admin.add_view(SeasonModelView(Season, db, category="Reference"))

    admin.add_view(AuditLogModelView(AuditLog, db, category="System"))
    admin.add_view(ApiKeyModelView(ApiKey, db, category="System"))
    admin.add_view(AdminUserModelView(AdminUser, db, category="System"))


class SHLAdminIndexView(AdminIndexView):
    """Custom admin index view with login/logout and stats."""

    @expose("/")
    def index(self) -> Any:
        if not current_user.is_authenticated:
            return redirect(url_for(".login"))

        # Get stats for dashboard. Pass both the legacy flat names
        # (manager_count, …) consumed by templates/admin/index.html and a
        # combined `stats` dict for newer templates.
        manager_count = db.session.query(Manager).count()
        achievement_count = db.session.query(Achievement).count()
        country_count = db.session.query(Country).count()
        admin_count = db.session.query(AdminUser).count()
        active_seasons = db.session.query(Season).filter_by(is_active=True).count()
        last_audit = db.session.query(AuditLog).order_by(AuditLog.timestamp.desc()).first()

        stats = {
            "managers": manager_count,
            "achievements": achievement_count,
            "countries": country_count,
            "admins": admin_count,
            "active_seasons": active_seasons,
            "last_audit": last_audit,
        }

        return self.render(
            "admin/index.html",
            stats=stats,
            manager_count=manager_count,
            achievement_count=achievement_count,
            country_count=country_count,
            admin_count=admin_count,
        )

    @expose("/login/", methods=["GET", "POST"])
    def login(self) -> Any:
        if current_user.is_authenticated:
            return redirect(url_for(".index"))

        if request.method == "POST":
            # Brute-force defence: 10 *failed* attempts / 60 s per client IP.
            # Successful logins do not count toward the budget so that admins
            # can't lock themselves out by repeatedly logging in/out.
            if not _is_login_rate_limit_ok(max_attempts=10, window_seconds=60):
                admin_logger.warning(f"Rate-limited login attempt from {_get_client_ip()}")
                flash("Too many login attempts. Please wait 60 seconds.", "error")
                return self.render("admin/login.html")

            username = request.form.get("username")
            password = request.form.get("password")

            user = db.session.query(AdminUser).filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                admin_logger.info(f"Admin login: {username}")
                return redirect(url_for(".index"))
            else:
                _record_failed_login_attempt()
                flash("Invalid username or password", "error")

        return self.render("admin/login.html")

    @expose("/logout/")
    def logout(self) -> Any:
        admin_logger.info(
            f"Admin logout: {current_user.username if current_user.is_authenticated else 'unknown'}"
        )
        logout_user()
        return redirect(url_for(".index"))

    @expose("/flush-cache/", methods=["POST"])
    @login_required
    def flush_cache(self) -> Any:
        """Invalidate all leaderboard caches. Admin-only."""
        invalidate_leaderboard_cache()
        admin_logger.info(
            f"FLUSH_CACHE by {current_user.username if current_user.is_authenticated else 'unknown'}"
        )
        flash("Leaderboard cache successfully flushed", "success")
        return redirect(url_for(".index"))


__all__ = [
    "init_admin",
    "SHLAdminIndexView",
    "SHLModelView",
    "SecureModelView",
    "CountryModelView",
    "ManagerModelView",
    "AchievementModelView",
    "AchievementTypeModelView",
    "LeagueModelView",
    "SeasonModelView",
    "AuditLogModelView",
    "AdminUserModelView",
    "ApiKeyModelView",
    "ServerControlView",
    "invalidate_leaderboard_cache",
    "get_flag_choices",
    "_login_attempts",
    "_check_login_rate_limit",
    "_is_login_rate_limit_ok",
    "_record_failed_login_attempt",
    "_get_client_ip",
    "admin_logger",
]
