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
from flask_login import LoginManager, current_user, login_user, logout_user
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
    admin.add_view(AdminUserModelView(AdminUser, db.session, category='System'))


# ==================== Auth & Index ====================

class SHLAdminIndexView(AdminIndexView):
    """Custom admin index view with login/logout and stats."""

    @expose('/')
    def index(self) -> Any:
        if not current_user.is_authenticated:
            return redirect(url_for('.login'))
        
        # Get stats for dashboard
        stats = {
            'managers': db.session.query(Manager).count(),
            'achievements': db.session.query(Achievement).count(),
            'active_seasons': db.session.query(Season).filter_by(is_active=True).count(),
            'last_audit': db.session.query(AuditLog).order_by(AuditLog.timestamp.desc()).first()
        }
        
        return self.render('admin/index.html', stats=stats)

    @expose('/login/', methods=['GET', 'POST'])
    def login(self) -> Any:
        if current_user.is_authenticated:
            return redirect(url_for('.index'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = db.session.query(AdminUser).filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                admin_logger.info(f"Admin login: {username}")
                return redirect(url_for('.index'))
            else:
                flash('Invalid username or password', 'error')
                
        return self.render('admin/login.html')

    @expose('/logout/')
    def logout(self) -> Any:
        admin_logger.info(f"Admin logout: {current_user.username if current_user.is_authenticated else 'unknown'}")
        logout_user()
        return redirect(url_for('.index'))

    @expose('/flush-cache/', methods=['POST'])
    def flush_cache(self) -> Any:
        """Invalidate all leaderboard caches."""
        from services.rating_service import invalidate_leaderboard_cache
        invalidate_leaderboard_cache()
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
    """View for managing individual achievements."""
    
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
        """Auto-calculate fields based on reference data."""
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
    can_create = False
    can_edit = False
    can_delete = False
    
    column_list = ('timestamp', 'user_id', 'action', 'target_model', 'target_id', 'changes')
    column_sortable_list = ('timestamp',)
    column_default_sort = ('timestamp', True)
    
    column_filters = ('action', 'target_model', 'user_id')


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


def _check_login_rate_limit(max_attempts: int = 5, window_seconds: int = 300) -> bool:
    """Basic in-memory rate limiting for login attempts."""
    import time
    from flask import request
    
    ip = request.remote_addr or 'unknown'
    now = time.time()
    
    if ip not in _login_attempts:
        _login_attempts[ip] = []
        
    # Remove old attempts
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < window_seconds]
    
    if len(_login_attempts[ip]) >= max_attempts:
        return False
        
    _login_attempts[ip].append(now)
    return True

# Alias for backward compatibility in tests
SecureModelView = SHLModelView
