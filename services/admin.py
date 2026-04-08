"""Flask-Admin configuration for Shadow Hockey League.

This module sets up the admin interface with authentication and CRUD views
for managing countries, managers, and achievements.
"""

import logging
from flask import redirect, url_for, request, flash
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import Select2Widget
from wtforms import Form, StringField
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import SelectField

from models import (
    db, AdminUser, Country, Manager, Achievement, AuditLog,
    AchievementType, League, Season, ApiKey
)
from services.cache_service import invalidate_leaderboard_cache
from services.audit_service import log_action, set_current_user_for_audit

# Logger for admin operations
admin_logger = logging.getLogger('shleague.admin')


import os
import glob
import secrets
from datetime import datetime, timedelta
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.form.upload import ImageUploadField
from flask import current_app

def get_flag_choices():
    """Dynamically get flag choices from static folder."""
    flags_dir = os.path.join(current_app.root_path, 'static', 'img', 'flags')
    choices = [('', '-- Select Flag --')]
    
    if os.path.exists(flags_dir):
        files = sorted(os.listdir(flags_dir))
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                path = f'/static/img/flags/{f}'
                choices.append((path, f))
    return choices

# List of available flag images (updated to match actual file names)
# Оставляем как фоллбэк, но приоритет у динамической функции
FLAG_CHOICES = get_flag_choices()


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'admin_login.index'
login_manager.login_message = 'Please log in to access the admin panel.'


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
    from flask import redirect, url_for, flash, request
    from services.audit_service import log_action
    import logging
    admin_logger = logging.getLogger('shleague.admin')

    class StatsAdminIndexView(AdminIndexView):
        """Custom admin index view with dashboard statistics."""

        # Use custom master template with login/logout links (BUG-001)
        base_template = 'admin/shl_master.html'

        @expose('/')
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
                recent_logs = db.session.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
            except Exception:
                manager_count = achievement_count = country_count = admin_count = 0
                api_key_count = audit_log_count = 0
                recent_logs = []

            return self.render(
                'admin/index.html',
                manager_count=manager_count,
                achievement_count=achievement_count,
                country_count=country_count,
                admin_count=admin_count,
                # Новые переменные
                api_key_count=api_key_count,
                audit_log_count=audit_log_count,
                recent_logs=recent_logs,
            )

        @expose('/flush-cache', methods=['POST'])
        @login_required
        def flush_cache(self):
            """Manually invalidate leaderboard cache."""
            try:
                # Invalidate cache
                invalidate_leaderboard_cache()

                # Log the action
                log_action(
                    user_id=current_user.id,
                    action='FLUSH_CACHE'
                )
                admin_logger.info(f"FLUSH_CACHE by {current_user.username}")

                flash('Cache flushed successfully', 'success')
            except Exception as e:
                admin_logger.error(f"Failed to flush cache: {e}")
                flash('Failed to flush cache', 'error')

            return redirect(url_for('.index'))

    # Create admin interface
    admin = Admin(
        app,
        name='Shadow Hockey League Admin',
        url='/admin/',
        endpoint='admin',
        index_view=StatsAdminIndexView(
            name='Home',
            template='admin/index.html'
        )
    )

    # Add views with proper menu structure
    admin.add_view(CountryModelView(Country, db.session, name='Countries', category='Data', menu_icon_type='fa', menu_icon_value='fa-flag'))
    admin.add_view(ManagerModelView(Manager, db.session, name='Managers', category='Data', menu_icon_type='fa', menu_icon_value='fa-user'))
    admin.add_view(AchievementModelView(Achievement, db.session, name='Achievements', category='Data', menu_icon_type='fa', menu_icon_value='fa-trophy'))
    admin.add_view(AdminUserModelView(AdminUser, db.session, name='Admin Users', category='Settings', menu_icon_type='fa', menu_icon_value='fa-users'))

    # Reference Data
    admin.add_view(AchievementTypeModelView(AchievementType, db.session, name='Achievement Types', category='Reference', menu_icon_type='fa', menu_icon_value='fa-list'))
    admin.add_view(LeagueModelView(League, db.session, name='Leagues', category='Reference', menu_icon_type='fa', menu_icon_value='fa-shield'))
    admin.add_view(SeasonModelView(Season, db.session, name='Seasons', category='Reference', menu_icon_type='fa', menu_icon_value='fa-calendar'))

    # System
    admin.add_view(ApiKeyModelView(ApiKey, db.session, name='API Keys', category='System', menu_icon_type='fa', menu_icon_value='fa-key'))
    admin.add_view(AuditLogModelView(AuditLog, db.session, name='Audit Log', category='System', menu_icon_type='fa', menu_icon_value='fa-history'))

    # Add Login/Logout as separate menu items
    admin.add_view(LoginView(name='Login', endpoint='admin_login', url='/admin/login'))
    admin.add_view(LogoutView(name='Logout', endpoint='admin_logout', url='/admin/logout'))


# Helper function to get choices from reference tables
def _get_choice_tuples(model):
    """Returns list of tuples (id, name) for reference tables."""
    try:
        items = db.session.query(model.id, model.name).order_by(model.code).all()
        return [('', '-- Select --')] + [(str(i.id), n) for i, n in items]
    except Exception:
        return [('', '-- Error loading --')]


class SecureModelView(ModelView):
    """Base model view with authentication and audit logging."""

    def is_accessible(self):
        """Check if user is authenticated and set current user for audit."""
        if current_user.is_authenticated:
            set_current_user_for_audit(current_user.id)
            return True
        return False

    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login if not accessible."""
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('admin_login.index', next=request.url))

    def create_model(self, form):
        """Create model with audit logging."""
        model = super().create_model(form)
        if model and current_user.is_authenticated:
            try:
                log_action(
                    user_id=current_user.id,
                    action='CREATE',
                    target_model=self.model.__name__,
                    target_id=getattr(model, 'id', None)
                )
                admin_logger.info(
                    f"CREATE {self.model.__name__} by {current_user.username}: "
                    f"id={getattr(model, 'id', 'N/A')}"
                )
            except Exception as e:
                admin_logger.error(f"Failed to log CREATE action: {e}")
        return model

    def update_model(self, form, model):
        """Update model with audit logging."""
        # Capture changes before update
        old_values = {}
        if hasattr(model, '__table__'):
            for column in model.__table__.columns:
                old_values[column.name] = getattr(model, column.name)
        
        result = super().update_model(form, model)
        
        if result and current_user.is_authenticated:
            try:
                # Capture new values after update
                new_values = {}
                changes = {}
                if hasattr(model, '__table__'):
                    for column in model.__table__.columns:
                        new_value = getattr(model, column.name)
                        if old_values[column.name] != new_value:
                            changes[column.name] = {
                                'old': old_values[column.name],
                                'new': new_value
                            }
                
                log_action(
                    user_id=current_user.id,
                    action='UPDATE',
                    target_model=self.model.__name__,
                    target_id=getattr(model, 'id', None),
                    changes=changes if changes else None
                )
                admin_logger.info(
                    f"UPDATE {self.model.__name__} by {current_user.username}: "
                    f"id={getattr(model, 'id', 'N/A')}"
                )
            except Exception as e:
                admin_logger.error(f"Failed to log UPDATE action: {e}")
        
        return result

    def delete_model(self, model):
        """Delete model with audit logging."""
        model_id = getattr(model, 'id', 'N/A')
        model_name = self.model.__name__
        
        result = super().delete_model(model)
        
        if result and current_user.is_authenticated:
            try:
                log_action(
                    user_id=current_user.id,
                    action='DELETE',
                    target_model=model_name,
                    target_id=model_id if model_id != 'N/A' else None
                )
                admin_logger.info(
                    f"DELETE {model_name} by {current_user.username}: id={model_id}"
                )
            except Exception as e:
                admin_logger.error(f"Failed to log DELETE action: {e}")
        
        return result


class CountryModelView(SecureModelView):
    """Admin view for Country CRUD operations."""

    # Page title (BUG-002)
    name = 'Countries'

    # Display settings
    column_list = ('id', 'code', 'name', 'flag_path')
    column_searchable_list = ('code', 'name')
    column_filters = ('code', 'name')
    form_columns = ('code', 'name', 'flag_path')
    column_default_sort = ('id', False)

    # Page titles
    list_template = 'admin/model/list.html'
    edit_template = 'admin/model/edit.html'
    create_template = 'admin/model/create.html'

    # Labels for columns
    column_labels = {
        'code': 'Code',
        'name': 'Country Name',
        'flag_path': 'Flag Image',
    }

    # Labels for form fields
    form_labels = {
        'code': 'Country Code (e.g., RUS)',
        'name': 'Country Name (e.g., Russia)',
        'flag_path': 'Flag Image',
    }

    # Widget configuration for flag_path (dropdown)
    form_widget_args = {
        'flag_path': {
            'class': 'form-control select2',
            'data-placeholder': 'Select a flag...',
            'style': 'width: 100%'
        }
    }

    column_formatters = {
        'flag_path': lambda v, c, m, p: f'<img src="{m.flag_path}" width="24" height="16" style="border: 1px solid #ddd;">' if m.flag_path else ''
    }
    column_formatters_detail = column_formatters

    def create_form(self):
        """Create form with flag choices."""
        form = super().create_form()
        form.flag_path.choices = get_flag_choices()
        return form

    def edit_form(self, obj):
        """Edit form with flag choices."""
        form = super().edit_form(obj)
        form.flag_path.choices = get_flag_choices()
        return form

    def on_model_change(self, form, model, is_created):
        """Auto-fill country name from code and invalidate cache."""
        from models import Country

        if is_created and model.code:
            # Auto-fill name from reference data (only if not manually set)
            resolved_name = Country.resolve_name(model.code)
            if resolved_name != "Unknown" and (not model.name or model.name == "Unknown"):
                model.name = resolved_name

        invalidate_leaderboard_cache()

    def on_model_delete(self, model):
        """Invalidate cache when country is deleted."""
        invalidate_leaderboard_cache()


class ManagerModelView(SecureModelView):
    """Admin view for Manager CRUD operations."""

    # Page title (BUG-002)
    name = 'Managers'

    # Display settings - only use columns, not relationships or properties
    column_list = ('id', 'name', 'country')
    column_searchable_list = ('name',)
    column_filters = ('country_id',)
    form_columns = ('name', 'country_id')
    column_default_sort = ('id', False)

    # Use Select2 for Country
    form_ajax_refs = {
        'country': {
            'fields': ['name', 'code'],
            'page_size': 10
        }
    }

    # Formatter to show Country name instead of ID
    column_formatters = {
        'country': lambda v, c, m, p: m.country.name if m.country else f'ID: {m.country_id}'
    }

    # Labels for columns
    column_labels = {
        'id': 'ID',
        'name': 'Manager Name',
        'country': 'Country',
    }

    # Labels for form fields
    form_labels = {
        'name': 'Manager Name',
        'country_id': 'Country',
    }

    def on_model_change(self, form, model, is_created):
        """Invalidate cache when manager is created/updated."""
        invalidate_leaderboard_cache()

    def on_model_delete(self, model):
        """Invalidate cache when manager is deleted."""
        invalidate_leaderboard_cache()


class AchievementModelView(SecureModelView):
    """Admin view for Achievement CRUD operations."""

    # Page title (BUG-002)
    name = 'Achievements'

    # Display settings
    column_list = ('id', 'achievement_type', 'league', 'season', 'manager', 'title')
    column_searchable_list = ('title', 'achievement_type')
    column_filters = ('league', 'season', 'achievement_type', 'manager_id')
    form_columns = ('achievement_type', 'league', 'season', 'title', 'icon_path', 'manager_id')
    column_default_sort = ('id', False)

    # Use Select2 for Manager
    form_ajax_refs = {
        'manager': {
            'fields': ['name'],
            'page_size': 10
        }
    }

    # Formatter to show Manager name
    column_formatters = {
        'manager': lambda v, c, m, p: m.manager.name if m.manager else f'ID: {m.manager_id}',
        'icon_path': lambda v, c, m, p: f'<img src="{m.icon_path}" width="20">' if m.icon_path else ''
    }

    # Labels for columns
    column_labels = {
        'id': 'ID',
        'achievement_type': 'Type',
        'league': 'League',
        'season': 'Season',
        'manager': 'Manager',
        'title': 'Title',
        'icon_path': 'Icon',
    }

    # Labels for form fields
    form_labels = {
        'achievement_type': 'Achievement Type',
        'league': 'League',
        'season': 'Season',
        'title': 'Title',
        'icon_path': 'Icon Path',
        'manager_id': 'Manager',
    }

    def create_form(self, **kwargs):
        """Add dynamic choices for reference fields stored as strings."""
        form = super().create_form(**kwargs)
        form.achievement_type.choices = _get_choice_tuples(AchievementType)
        form.league.choices = _get_choice_tuples(League)
        form.season.choices = _get_choice_tuples(Season)
        return form

    def edit_form(self, obj, **kwargs):
        """Add dynamic choices for reference fields stored as strings."""
        form = super().edit_form(obj, **kwargs)
        form.achievement_type.choices = _get_choice_tuples(AchievementType)
        form.league.choices = _get_choice_tuples(League)
        form.season.choices = _get_choice_tuples(Season)
        return form

    def on_model_change(self, form, model, is_created):
        """Invalidate cache when achievement is created/updated."""
        invalidate_leaderboard_cache()

    def on_model_delete(self, model):
        """Invalidate cache when achievement is deleted."""
        invalidate_leaderboard_cache()


class AdminUserModelView(SecureModelView):
    """Admin view for managing admin users."""

    # Page title (BUG-002)
    name = 'Admin Users'

    column_list = ('username',)
    column_searchable_list = ('username',)
    form_columns = ('username', 'password_hash')
    
    # Hide password from list
    def _list_password(self, model):
        return '***'
    
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
            flash('Cannot delete the last admin user.', 'error')
            return False
        return True


# ==================== NEW VIEWS (Reference & System) ====================


class AchievementTypeModelView(SecureModelView):
    """Admin view for managing achievement types and base points."""

    name = 'Achievement Types'
    column_list = ('code', 'name', 'base_points_l1', 'base_points_l2')
    column_searchable_list = ('code', 'name')
    column_filters = ('code', 'name')
    form_columns = ('code', 'name', 'base_points_l1', 'base_points_l2')
    column_default_sort = ('code', False)
    
    form_widget_args = {
        'base_points_l1': {'style': 'width: 80px'},
        'base_points_l2': {'style': 'width: 80px'},
    }

    column_labels = {
        'code': 'Code',
        'name': 'Name',
        'base_points_l1': 'Points L1',
        'base_points_l2': 'Points L2',
    }


class LeagueModelView(SecureModelView):
    """Admin view for managing leagues."""

    name = 'Leagues'
    column_list = ('code', 'name')
    column_searchable_list = ('code', 'name')
    column_filters = ('code', 'name')
    form_columns = ('code', 'name')
    column_default_sort = ('code', False)


class SeasonModelView(SecureModelView):
    """Admin view for managing seasons and multipliers."""

    name = 'Seasons'
    column_list = ('code', 'name', 'multiplier', 'is_active')
    column_searchable_list = ('code', 'name')
    column_filters = ('code', 'name', 'is_active')
    form_columns = ('code', 'name', 'multiplier', 'is_active')
    column_default_sort = ('code', False)
    
    column_formatters = {
        'is_active': lambda v, c, m, p: '✅' if m.is_active else '❌'
    }
    
    form_widget_args = {
        'is_active': {'class': 'form-check-input'},
    }


class ApiKeyModelView(SecureModelView):
    """Admin view for managing API keys."""

    name = 'API Keys'
    column_list = ('name', 'scope', 'is_active', 'created_at', 'last_used_at')
    column_searchable_list = ('name',)
    column_filters = ('scope', 'is_active', 'revoked')
    form_columns = ('name', 'scope', 'expires_at', 'revoked')
    column_default_sort = ('created_at', True)
    
    column_formatters = {
        'key_hash': lambda v, c, m, p: '***',
        'is_active': lambda v, c, m, p: '✅' if m.is_active else '❌',
        'revoked': lambda v, c, m, p: '🚫' if m.revoked else '—',
    }
    
    form_overrides = {
        'key_hash': StringField, # Поле для отображения ключа при создании
    }
    
    form_args = {
        'key_hash': {
            'label': 'API Key (Copy this now!)',
            'validators': [],
            'render_kw': {'readonly': True},
        }
    }
    
    form_widget_args = {
        'key_hash': {'readonly': True},
        'expires_at': {'class': 'form-control', 'placeholder': 'YYYY-MM-DD HH:MM:SS'},
    }
    
    def create_form(self):
        """Clear key_hash field for new key creation."""
        form = super().create_form()
        form.key_hash.data = ''
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
        else:
            # При обновлении не трогаем хэш, если он уже есть
            if not model.key_hash.startswith('pbkdf2:sha256:'):
                model.key_hash = generate_password_hash(model.key_hash)


class AuditLogModelView(SecureModelView):
    """Admin view for viewing audit logs (Read-Only + Bulk Delete)."""

    name = 'Audit Log'
    can_create = False
    can_edit = False
    can_view_details = True
    
    column_list = ('timestamp', 'user_id', 'action', 'target_model', 'target_id')
    column_filters = ('user_id', 'action', 'target_model', 'timestamp')
    column_default_sort = ('timestamp', True)
    
    column_formatters = {
        'changes': lambda v, c, m, p: f'<pre style="max-width:300px; white-space:pre-wrap;">{m.changes}</pre>' if m.changes else '',
    }

    def delete_model(self, model):
        """Allow deleting audit logs for cleanup."""
        return super().delete_model(model)

    # Добавляем действие для массовой очисткики
    action_list = (
        ('delete_selected', 'Delete Selected', 'Delete selected log entries'),
    )


# ==================== LOGIN / LOGOUT ====================


class LoginView(BaseView):
    """Login view for admin panel."""
    
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Handle login form."""
        if current_user.is_authenticated:
            return redirect(url_for('admin.index'))
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            remember = request.form.get('remember', False)
            
            user = db.session.query(AdminUser).filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user, remember=remember)
                flash('Logged in successfully.', 'success')
                
                # Set current user for audit logging
                set_current_user_for_audit(user.id)
                
                # Log successful login
                try:
                    log_action(
                        user_id=user.id,
                        action='LOGIN'
                    )
                    admin_logger.info(f"LOGIN successful for user {username}")
                except Exception as e:
                    admin_logger.error(f"Failed to log LOGIN action: {e}")
                
                next_page = request.args.get('next')
                return redirect(next_page or url_for('admin.index'))
            else:
                flash('Invalid username or password.', 'error')
                admin_logger.warning(f"LOGIN failed for user {username}")
        
        return self.render('admin/login.html')


class LogoutView(BaseView):
    """Logout view for admin panel."""
    
    @expose('/')
    @login_required
    def index(self):
        """Handle logout."""
        logout_user()
        flash('Logged out successfully.', 'info')
        return redirect(url_for('admin_login'))
