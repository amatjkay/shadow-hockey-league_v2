"""Flask-Admin configuration for Shadow Hockey League.

This module sets up the admin interface with authentication and CRUD views
for managing countries, managers, and achievements.
"""

from flask import redirect, url_for, request, flash
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, AdminUser, Country, Manager, Achievement
from services.cache_service import invalidate_leaderboard_cache


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
    
    # Create admin interface with custom index view
    admin = Admin(
        app,
        name='Shadow Hockey League Admin',
        index_view=AdminIndexView(
            name='Home',
            url='/admin/home',
            template='admin/index.html'
        ),
        url='/admin/'
    )
    
    # Add views
    admin.add_view(CountryModelView(Country, db.session, name='Countries', category='Data'))
    admin.add_view(ManagerModelView(Manager, db.session, name='Managers', category='Data'))
    admin.add_view(AchievementModelView(Achievement, db.session, name='Achievements', category='Data'))
    admin.add_view(AdminUserModelView(AdminUser, db.session, name='Admin Users', category='Settings'))
    admin.add_view(LoginView(name='Login', url='/admin/login'))
    admin.add_view(LogoutView(name='Logout', url='/admin/logout'))


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
    
    column_list = ('code', 'flag_path')
    column_searchable_list = ('code',)
    column_filters = ('code',)
    form_columns = ('code', 'flag_path')
    
    def on_model_change(self, form, model, is_created):
        """Invalidate cache when country is created/updated."""
        invalidate_leaderboard_cache()
    
    def on_model_delete(self, model):
        """Invalidate cache when country is deleted."""
        invalidate_leaderboard_cache()


class ManagerModelView(SecureModelView):
    """Admin view for Manager CRUD operations."""
    
    column_list = ('name', 'country_code')
    column_searchable_list = ('name',)
    column_filters = ('country',)
    form_columns = ('name', 'country_id')
    
    def on_model_change(self, form, model, is_created):
        """Invalidate cache when manager is created/updated."""
        invalidate_leaderboard_cache()
    
    def on_model_delete(self, model):
        """Invalidate cache when manager is deleted."""
        invalidate_leaderboard_cache()


class AchievementModelView(SecureModelView):
    """Admin view for Achievement CRUD operations."""
    
    column_list = ('achievement_type', 'league', 'season', 'title')
    column_searchable_list = ('title', 'achievement_type')
    column_filters = ('league', 'season', 'achievement_type')
    form_columns = ('achievement_type', 'league', 'season', 'title', 'icon_path', 'manager_id')
    
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
