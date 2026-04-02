"""Flask-Admin configuration for Shadow Hockey League.

This module sets up the admin interface with authentication and CRUD views
for managing countries, managers, and achievements.
"""

from flask import redirect, url_for, request, flash
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import Select2Widget
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import SelectField

from models import db, AdminUser, Country, Manager, Achievement
from services.cache_service import invalidate_leaderboard_cache

# List of available flag images
FLAG_CHOICES = [
    ('/static/img/flags/rus.png', 'Russia'),
    ('/static/img/flags/bel.png', 'Belarus'),
    ('/static/img/flags/kz.png', 'Kazakhstan'),
    ('/static/img/flags/vietnam.png', 'Vietnam'),
    ('/static/img/flags/ua.png', 'Ukraine'),
    ('/static/img/flags/mexico.png', 'Mexico'),
    ('/static/img/flags/pol.png', 'Poland'),
    ('/static/img/flags/china.png', 'China'),
    ('/static/img/flags/usa.png', 'USA'),
    ('/static/img/flags/canada.png', 'Canada'),
    ('/static/img/flags/fin.png', 'Finland'),
    ('/static/img/flags/swe.png', 'Sweden'),
    ('/static/img/flags/cze.png', 'Czech Republic'),
    ('/static/img/flags/svk.png', 'Slovakia'),
    ('/static/img/flags/ger.png', 'Germany'),
    ('/static/img/flags/sui.png', 'Switzerland'),
    ('/static/img/flags/aut.png', 'Austria'),
    ('/static/img/flags/nor.png', 'Norway'),
    ('/static/img/flags/den.png', 'Denmark'),
    ('/static/img/flags/fra.png', 'France'),
    ('/static/img/flags/gbr.png', 'United Kingdom'),
    ('/static/img/flags/lat.png', 'Latvia'),
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

    # Create admin interface
    # Note: AdminIndexView url='/admin/' is the main admin page
    admin = Admin(
        app,
        name='Shadow Hockey League Admin',
        url='/admin/',
        endpoint='admin',
        index_view=AdminIndexView(
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
    """Base model view with authentication."""
    
    def is_accessible(self):
        """Check if user is authenticated."""
        return current_user.is_authenticated
    
    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login if not accessible."""
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('admin_login', next=request.url))


class CountryModelView(SecureModelView):
    """Admin view for Country CRUD operations."""
    
    column_list = ('id', 'code', 'name', 'flag_path')
    column_searchable_list = ('code', 'name')
    column_filters = ('code', 'name')
    form_columns = ('code', 'name', 'flag_path')
    column_default_sort = ('id', False)
    
    # Column labels for better readability
    column_labels = {
        'code': 'Code',
        'name': 'Country Name',
        'flag_path': 'Flag Image',
    }
    
    # Form labels
    form_labels = {
        'code': 'Country Code (e.g., RUS)',
        'name': 'Country Name (e.g., Russia)',
        'flag_path': 'Flag Image',
    }
    
    # Override form_columns to use Select2 for flag_path
    form_widget_args = {
        'flag_path': {
            'class': 'form-control select2',
            'data-placeholder': 'Select a flag...',
        }
    }
    
    def on_form_prefill(self, form, id):
        """Pre-fill flag_path choices."""
        form.flag_path.choices = [('', '-- Select Flag --')] + FLAG_CHOICES
    
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
        """Invalidate cache when country is created/updated."""
        invalidate_leaderboard_cache()
    
    def on_model_delete(self, model):
        """Invalidate cache when country is deleted."""
        invalidate_leaderboard_cache()


class ManagerModelView(SecureModelView):
    """Admin view for Manager CRUD operations."""
    
    column_list = ('id', 'name', 'country', 'is_tandem')
    column_searchable_list = ('name',)
    column_filters = ('country', 'is_tandem')
    form_columns = ('name', 'country_id')
    column_default_sort = ('id', False)
    
    # Column labels
    column_labels = {
        'name': 'Manager Name',
        'country': 'Country',
        'is_tandem': 'Is Tandem',
    }
    
    # Form labels
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
    
    column_list = ('id', 'achievement_type', 'league', 'season', 'manager', 'title')
    column_searchable_list = ('title', 'achievement_type')
    column_filters = ('league', 'season', 'achievement_type')
    form_columns = ('achievement_type', 'league', 'season', 'title', 'icon_path', 'manager_id')
    column_default_sort = ('id', False)
    
    # Column labels
    column_labels = {
        'achievement_type': 'Type',
        'league': 'League',
        'season': 'Season',
        'manager': 'Manager',
        'title': 'Title',
        'icon_path': 'Icon',
    }
    
    # Form labels
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
