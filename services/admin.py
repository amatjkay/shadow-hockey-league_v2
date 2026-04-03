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

from models import db, AdminUser, Country, Manager, Achievement
from services.cache_service import invalidate_leaderboard_cache

# Logger for admin operations
admin_logger = logging.getLogger('shleague.admin')


class AchievementInlineForm(Form):
    """Form for inline achievement editing."""
    achievement_type = StringField('Type')
    league = StringField('League')
    season = StringField('Season')
    title = StringField('Title')
    icon_path = StringField('Icon')

# List of available flag images (updated to match actual file names)
FLAG_CHOICES = [
    ('/static/img/flags/BLR.png', 'Belarus'),
    ('/static/img/flags/RUS.png', 'Russia'),
    ('/static/img/flags/KAZ.png', 'Kazakhstan'),
    ('/static/img/flags/CHN.png', 'China'),
    ('/static/img/flags/VNM.png', 'Vietnam'),
    ('/static/img/flags/UKR.png', 'Ukraine'),
    ('/static/img/flags/MEX.png', 'Mexico'),
    ('/static/img/flags/POL.png', 'Poland'),
    ('/static/img/flags/USA.png', 'USA'),
    ('/static/img/flags/CAN.png', 'Canada'),
    ('/static/img/flags/FIN.png', 'Finland'),
    ('/static/img/flags/SWE.png', 'Sweden'),
    ('/static/img/flags/CZE.png', 'Czech Republic'),
    ('/static/img/flags/SVK.png', 'Slovakia'),
    ('/static/img/flags/GER.png', 'Germany'),
    ('/static/img/flags/SUI.png', 'Switzerland'),
    ('/static/img/flags/AUT.png', 'Austria'),
    ('/static/img/flags/NOR.png', 'Norway'),
    ('/static/img/flags/DEN.png', 'Denmark'),
    ('/static/img/flags/FRA.png', 'France'),
    ('/static/img/flags/GBR.png', 'United Kingdom'),
    ('/static/img/flags/LAT.png', 'Latvia'),
]


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'admin_login'
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
            except Exception:
                manager_count = achievement_count = country_count = admin_count = 0

            return self.render(
                'admin/index.html',
                manager_count=manager_count,
                achievement_count=achievement_count,
                country_count=country_count,
                admin_count=admin_count,
            )

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
    
    # Add Login/Logout as separate menu items (use menu_class_name to force display)
    login_view = LoginView(name='Login', endpoint='admin_login', url='/login')
    logout_view = LogoutView(name='Logout', endpoint='admin_logout', url='/logout')
    admin.add_view(login_view)
    admin.add_view(logout_view)


class SecureModelView(ModelView):
    """Base model view with authentication and audit logging."""

    def is_accessible(self):
        """Check if user is authenticated."""
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login if not accessible."""
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('admin_login', next=request.url))

    def create_model(self, form):
        """Log model creation."""
        model = super().create_model(form)
        if model:
            admin_logger.info(
                f"CREATE {self.model.__name__} by {current_user.username}: "
                f"id={getattr(model, 'id', 'N/A')}"
            )
        return model

    def update_model(self, form, model):
        """Log model update."""
        result = super().update_model(form, model)
        if result:
            admin_logger.info(
                f"UPDATE {self.model.__name__} by {current_user.username}: "
                f"id={getattr(model, 'id', 'N/A')}"
            )
        return result

    def delete_model(self, model):
        """Log model deletion."""
        model_id = getattr(model, 'id', 'N/A')
        model_name = self.model.__name__
        result = super().delete_model(model)
        if result:
            admin_logger.info(
                f"DELETE {model_name} by {current_user.username}: id={model_id}"
            )
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
        }
    }

    def create_form(self):
        """Create form with flag choices."""
        form = super().create_form()
        form.flag_path.choices = [('', '-- Select Flag --')] + FLAG_CHOICES
        return form

    def edit_form(self, obj):
        """Edit form with flag choices."""
        form = super().edit_form(obj)
        form.flag_path.choices = [('', '-- Select Flag --')] + FLAG_CHOICES
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
    column_list = ('id', 'name', 'country_id')
    column_searchable_list = ('name',)
    column_filters = ('country_id',)
    form_columns = ('name', 'country_id')
    column_default_sort = ('id', False)

    # Inline achievements
    form_subdocuments = {
        'achievements': {
            'form_class': AchievementInlineForm,
        }
    }

    # Labels for columns
    column_labels = {
        'id': 'ID',
        'name': 'Manager Name',
        'country_id': 'Country',
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

    # Display settings - only use columns, not relationships
    column_list = ('id', 'achievement_type', 'league', 'season', 'manager_id', 'title')
    column_searchable_list = ('title', 'achievement_type')
    column_filters = ('league', 'season', 'achievement_type', 'manager_id')
    form_columns = ('achievement_type', 'league', 'season', 'title', 'icon_path', 'manager_id')
    column_default_sort = ('id', False)

    # Labels for columns
    column_labels = {
        'id': 'ID',
        'achievement_type': 'Type',
        'league': 'League',
        'season': 'Season',
        'manager_id': 'Manager ID',
        'title': 'Title',
        'icon_path': 'Icon',
    }

    # Labels for form fields
    form_labels = {
        'achievement_type': 'Achievement Type',
        'league': 'League (1 or 2)',
        'season': 'Season (e.g., 24/25)',
        'title': 'Title',
        'icon_path': 'Icon Path',
        'manager_id': 'Manager',
    }

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
                next_page = request.args.get('next')
                return redirect(next_page or url_for('admin.index'))
            else:
                flash('Invalid username or password.', 'error')
        
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
