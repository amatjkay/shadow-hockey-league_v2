"""Flask-Admin configuration for Shadow Hockey League.

This module sets up the admin interface with authentication and CRUD views
for managing countries, managers, and achievements.
"""

import logging
import os
import subprocess
import json
from flask import redirect, url_for, request, flash, current_app
from markupsafe import Markup
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import Select2Widget
from wtforms import SelectField, Form, StringField, validators
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

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
    admin.add_view(ServerControlView(name='Server Control', category='System', menu_icon_type='fa', menu_icon_value='fa-power-off'))

    # Add Login/Logout as separate menu items
    admin.add_view(LoginView(name='Login', endpoint='admin_login', url='/admin/login'))
    admin.add_view(LogoutView(name='Logout', endpoint='admin_logout', url='/admin/logout'))


# Helper data for Countries (sorted alphabetically by name for better UX)
_raw_choices = [
    ('RUS', 'Russia'), ('CAN', 'Canada'), ('USA', 'United States'),
    ('SWE', 'Sweden'), ('FIN', 'Finland'), ('CZE', 'Czech Republic'),
    ('SUI', 'Switzerland'), ('GER', 'Germany'), ('SVK', 'Slovakia'),
    ('DEN', 'Denmark'), ('NOR', 'Norway'), ('FRA', 'France'),
    ('AUT', 'Austria'), ('BLR', 'Belarus'), ('KAZ', 'Kazakhstan'),
    ('LAT', 'Latvia'), ('GBR', 'Great Britain'), ('ITA', 'Italy'),
    ('UKR', 'Ukraine'), ('POL', 'Poland'), ('SLO', 'Slovenia'),
    ('HUN', 'Hungary'), ('JPN', 'Japan'), ('KOR', 'South Korea'),
    ('CHN', 'China'), ('AUS', 'Australia'), ('MEX', 'Mexico'),
    ('VNM', 'Vietnam')
]
COUNTRY_CHOICES = [('', '')] + sorted(_raw_choices, key=lambda x: x[1])

# Map codes to actual flag filenames (handling legacy names or differences)
# Assuming standard 3-letter codes match filenames in most cases
COUNTRY_FLAG_MAP = {code: f'/static/img/flags/{code}.png' for code, _ in _raw_choices}
# Add specific overrides if filenames differ from ISO codes
COUNTRY_FLAG_MAP['GBR'] = '/static/img/flags/GBR.png' # Or UK.png if exists

# JavaScript to auto-fill Name, Flag Path, and show preview
COUNTRY_AUTOFILL_JS = """
<script>
$(document).ready(function() {
    var $code = $('#code');
    var $name = $('#name');
    var $flag = $('#flag_path');
    var $preview = $('#flag-preview-img');
    var flagMap = """ + json.dumps({k: v for k, v in COUNTRY_FLAG_MAP.items()}) + """;

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
def _get_ref_data_choices(model):
    """Returns list of tuples (code, name) for reference tables."""
    try:
        items = db.session.query(model.code, model.name).order_by(model.code).all()
        return [('', '-- Select --')] + [(code, name) for code, name in items]
    except Exception:
        return [('', '-- Error loading --')]

# Helper function to get (id, name) tuples for FK relationships
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

    name = 'Countries'
    column_list = ('id', 'code', 'name', 'flag_path')
    column_searchable_list = ('code', 'name')
    column_filters = ('code', 'name')
    form_columns = ('code', 'name', 'flag_path')
    column_default_sort = ('name', False)
    
    column_labels = {
        'code': 'Country',
        'name': 'Name (Auto)',
        'flag_path': 'Flag Img'
    }

    # Переопределяем поля на SelectField с виджетом Select2
    form_overrides = {
        'code': SelectField,
        'flag_path': SelectField
    }
    
    # Убираем DataRequired чтобы не было красной рамки и можно было сохранить без флага
    form_args = {
        'code': {'validators': []},
        'flag_path': {'validators': []},
    }
    
    form_widget_args = {
        'code': {},  # Будет установлен в create_form/edit_form
        'flag_path': {}, # Будет установлен в create_form/edit_form
        'name': {'readonly': True, 'style': 'background-color: #f0f0f0;'}
    }

    # Размер картинки (соответствует стилю главной страницы)
    column_formatters = {
        'flag_path': lambda v, c, m, p: Markup(f'<img src="{m.flag_path}" width="32" height="24" style="border: 1px solid #ccc;">') if m.flag_path else ''
    }

    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)
        form.code.widget = Select2Widget()
        form.code.choices = COUNTRY_CHOICES
        form.flag_path.widget = Select2Widget()
        form.flag_path.choices = get_flag_choices()
        form.extra_js = COUNTRY_AUTOFILL_JS
        form.extra_html = Markup('<img id="flag-preview-img" src="" style="display:none; margin-top:10px; border:1px solid #ccc; max-width:64px;">')
        return form

    def edit_form(self, obj, **kwargs):
        form = super().edit_form(obj, **kwargs)
        form.code.widget = Select2Widget()
        form.code.choices = COUNTRY_CHOICES
        form.flag_path.widget = Select2Widget()
        form.flag_path.choices = get_flag_choices()
        form.extra_js = COUNTRY_AUTOFILL_JS
        form.extra_html = Markup(f'<img id="flag-preview-img" src="{obj.flag_path}" style="margin-top:10px; border:1px solid #ccc; max-width:64px;">' if obj.flag_path else '<img id="flag-preview-img" src="" style="display:none; margin-top:10px; border:1px solid #ccc; max-width:64px;">')
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
            flash(f'Невозможно удалить страну "{model.name}". Она используется у {manager_count} менеджер(ов). Сначала измените их страну.', 'error')
            return False
        
        result = super().delete_model(model)
        if result:
            invalidate_leaderboard_cache()
        return result


class ManagerModelView(SecureModelView):
    """Admin view for Manager CRUD operations."""

    name = 'Managers'

    # Добавляем ссылку на создание достижения для менеджера
    column_list = ('id', 'name', 'country', 'manage_achievements')
    column_searchable_list = ('name',)
    column_filters = ('country.name',)
    form_columns = ('name', 'country')
    column_default_sort = ('name', False)

    # Используем form_args для надежной загрузки списка стран
    form_args = {
        'country': {
            'query_factory': lambda: db.session.query(Country).order_by(Country.name),
            'allow_blank': False,
            'get_label': 'name'
        }
    }

    form_widget_args = {
        'country': {
            'class': 'form-control select2'
        }
    }

    # Форматтер для ссылки на достижения
    def _manage_achievements(view, context, model, name):
        # Ссылка на создание достижения с предвыбранным менеджером
        url = url_for('achievement.create_view', manager_id=model.id)
        return Markup(f'<a href="{url}">Управление наградами ({len(model.achievements)})</a>')

    column_formatters = {
        'country': lambda v, c, m, p: m.country.name if m.country else 'Unknown',
        'manage_achievements': _manage_achievements
    }

    column_labels = {
        'country': 'Country',
        'manage_achievements': 'Achievements'
    }

    def on_model_change(self, form, model, is_created):
        invalidate_leaderboard_cache()

    def on_model_delete(self, model):
        invalidate_leaderboard_cache()


class AchievementModelView(SecureModelView):
    """Admin view for Achievement CRUD operations (FK-based)."""

    name = 'Achievements'

    column_list = ('id', 'type', 'league', 'season', 'manager', 'final_points')
    column_searchable_list = ('title',)
    column_filters = ('league.code', 'season.code', 'type.code', 'manager.name')
    form_columns = ('manager', 'type', 'league', 'season', 'title', 'icon_path', 'base_points', 'multiplier', 'final_points')
    column_default_sort = ('manager.name', False)

    # 1. Select2 для Менеджера (Ajax), для остальных - SelectField (чтобы легко получать code и points в JS)
    form_ajax_refs = {
        'manager': {'fields': ['name'], 'page_size': 10},
    }

    # Переопределяем поля на обычные SelectField
    form_overrides = {
        'type': SelectField,
        'league': SelectField,
        'season': SelectField,
    }
    
    form_widget_args = {
        'type': {'class': 'form-control select2'},
        'league': {'class': 'form-control select2'},
        'season': {'class': 'form-control select2'},
    }

    column_labels = {
        'type_id': 'Type',
        'league_id': 'League',
        'season_id': 'Season',
        'final_points': 'Points'
    }

    # Форматтеры для списка
    column_formatters = {
        'type': lambda v, c, m, p: m.type.name if m.type else '-',
        'league': lambda v, c, m, p: m.league.name if m.league else '-',
        'season': lambda v, c, m, p: m.season.name if m.season else '-',
        'manager': lambda v, c, m, p: m.manager.name if m.manager else '-',
    }

    def create_form(self):
        form = super().create_form()
        # Подхват менеджера из URL
        manager_id = request.args.get('manager_id')
        if manager_id:
            form.manager.data = db.session.query(Manager).get(int(manager_id))
        
        # Заполняем списки для SelectField (id, name)
        form.type.choices = [(t.id, t.name) for t in db.session.query(AchievementType).order_by(AchievementType.name).all()]
        form.league.choices = [(l.id, l.name) for l in db.session.query(League).order_by(League.name).all()]
        form.season.choices = [(s.id, s.name) for s in db.session.query(Season).order_by(Season.name).all()]

        # Генерируем JS для автозаполнения
        form.extra_js = self._get_achievement_js(form.type.data, form.league.data, form.season.data)
        return form

    def edit_form(self, obj):
        form = super().edit_form(obj)
        
        form.type.choices = [(t.id, t.name) for t in db.session.query(AchievementType).order_by(AchievementType.name).all()]
        form.league.choices = [(l.id, l.name) for l in db.session.query(League).order_by(League.name).all()]
        form.season.choices = [(s.id, s.name) for s in db.session.query(Season).order_by(Season.name).all()]
        
        # Если это редактирование, ставим текущие значения
        if obj:
            if obj.type: form.type.data = obj.type.id
            if obj.league: form.league.data = obj.league.id
            if obj.season: form.season.data = obj.season.id

        form.extra_js = self._get_achievement_js(form.type.data, form.league.data, form.season.data)
        return form

    def _get_achievement_js(self, current_type, current_league, current_season):
        """Генерирует JS с данными для автозаполнения."""
        # Собираем полные данные для JS
        types = [(t.id, t.name, t.code, t.base_points_l1, t.base_points_l2) for t in db.session.query(AchievementType).all()]
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
                
                # Points Logic
                is_l1 = (league_obj.code == '1')
                model.base_points = float(type_obj.base_points_l1 if is_l1 else type_obj.base_points_l2)
                model.multiplier = float(season_obj.multiplier)
                model.final_points = model.base_points * model.multiplier
        
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
    # Используем revoked (колонка БД) вместо is_active (свойство модели)
    column_list = ('name', 'scope', 'revoked', 'created_at', 'last_used_at')
    column_searchable_list = ('name',)
    column_filters = ('scope', 'revoked')
    form_columns = ('name', 'scope', 'expires_at', 'revoked')
    column_default_sort = ('created_at', True)
    
    column_formatters = {
        'key_hash': lambda v, c, m, p: '***',
        'revoked': lambda v, c, m, p: '🚫' if m.revoked else '✅',
    }
    
    form_overrides = {
        'key_hash': StringField,
    }
    
    form_args = {
        'key_hash': {
            'label': 'API Key (Скопируйте сейчас!)',
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

    # Bulk delete action
    @action('delete_selected', 'Delete Selected', 'Are you sure you want to delete these log entries?')
    def action_delete_selected(self, ids):
        count = 0
        for audit_id in ids:
            model = db.session.get(AuditLog, int(audit_id))
            if model:
                db.session.delete(model)
                count += 1
        db.session.commit()
        flash(f'Удалено записей: {count}', 'success')


class ServerControlView(BaseView):
    """View for server administration actions like restart."""

    def is_accessible(self):
        return current_user.is_authenticated

    @expose('/')
    def index(self):
        return self.render('admin/server_control.html')

    @expose('/restart', methods=['POST'])
    def restart(self):
        """Restart the service."""
        try:
            if os.name == 'nt':
                # Windows (Local Dev): Just stop the process.
                # User needs to restart it manually in console.
                flash('Server stopped. Please restart it manually in the console (`python app.py`).', 'info')
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
                return redirect(url_for('.index'))
            else:
                # Linux (Production): Use systemctl
                subprocess.Popen(['sudo', 'systemctl', 'restart', 'shadow-hockey-league'])
                return '<html><body style="font-family:sans-serif; text-align:center; margin-top:50px;"><h1>🔄 Restarting Server...</h1><p>Please wait a moment.</p><script>setTimeout(()=>window.location.href="/admin/", 5000);</script></body></html>'
        except Exception as e:
            flash(f'Failed to restart: {str(e)}', 'error')
            return redirect(url_for('.index'))


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
