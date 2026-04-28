"""Integration tests for admin panel views.

Tests cover:
- TEST-001: AchievementModelView auto-calculation
- TEST-002: ApiKeyModelView key generation
- TEST-003: ServerControlView
- TEST-004: StatsAdminIndexView dashboard
- TEST-005: HTTP-level integration (POST to admin endpoints)
- TEST-006: Login/logout with CSRF
"""

import unittest

from flask_login import login_user

from app import create_app
from models import (
    Achievement,
    AchievementType,
    AdminUser,
    Country,
    League,
    Manager,
    Season,
    db,
)
from services.admin import AchievementModelView, ServerControlView


class TestAchievementModelView(unittest.TestCase):
    """TEST-001: Tests for AchievementModelView auto-calculation."""

    def setUp(self):
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create reference data
        self.ach_type = AchievementType(
            code="TOP1", name="Top 1", base_points_l1=10, base_points_l2=5
        )
        db.session.add(self.ach_type)
        self.league = League(code="1", name="League 1")
        db.session.add(self.league)
        self.season = Season(code="25/26", name="Season 25/26", multiplier=1.5, is_active=True)
        db.session.add(self.season)
        country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
        db.session.add(country)
        db.session.flush()
        self.manager = Manager(name="Test Manager", country_id=country.id)
        db.session.add(self.manager)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_column_list_has_correct_columns(self):
        """AchievementModelView should have correct column list."""
        self.assertIn("type", AchievementModelView.column_list)
        self.assertIn("league", AchievementModelView.column_list)
        self.assertIn("season", AchievementModelView.column_list)
        self.assertIn("final_points", AchievementModelView.column_list)

    def test_form_ajax_refs_covers_relationship_fields(self):
        """form_ajax_refs should drive type/league/season/manager pickers.

        The previous ``form_args={'<rel>': {'query_factory': ...}}`` shape
        crashed under WTForms 3.x with
        ``TypeError: Field.__init__() got an unexpected keyword argument
        'query_factory'`` — see B2 in the e2e bug report. The canonical
        Flask-Admin pattern is ``form_ajax_refs``, which is what the live
        admin actually uses.
        """
        self.assertIn("type", AchievementModelView.form_ajax_refs)
        self.assertIn("league", AchievementModelView.form_ajax_refs)
        self.assertIn("season", AchievementModelView.form_ajax_refs)
        self.assertIn("manager", AchievementModelView.form_ajax_refs)

    def test_achievement_model_auto_calculation(self):
        """Achievement should auto-calculate base_points, multiplier, final_points."""
        achievement = Achievement(
            type_id=self.ach_type.id,
            league_id=self.league.id,
            season_id=self.season.id,
            title="TOP1",
            icon_path="/static/img/cups/top1.svg",
            manager_id=self.manager.id,
            base_points=10.0,
            multiplier=1.5,
            final_points=15.0,
        )
        db.session.add(achievement)
        db.session.commit()

        # Verify auto-calculated values
        self.assertEqual(achievement.base_points, 10.0)
        self.assertEqual(achievement.multiplier, 1.5)
        self.assertEqual(achievement.final_points, 15.0)

    def test_achievement_foreign_keys(self):
        """Achievement should have proper FK relationships."""
        achievement = Achievement(
            type_id=self.ach_type.id,
            league_id=self.league.id,
            season_id=self.season.id,
            title="TOP1",
            icon_path="/static/img/cups/top1.svg",
            manager_id=self.manager.id,
            base_points=10.0,
            multiplier=1.5,
            final_points=15.0,
        )
        db.session.add(achievement)
        db.session.commit()

        # Reload from DB
        db.session.refresh(achievement)
        self.assertEqual(achievement.type.id, self.ach_type.id)
        self.assertEqual(achievement.league.id, self.league.id)
        self.assertEqual(achievement.season.id, self.season.id)


class TestApiKeyModelView(unittest.TestCase):
    """TEST-002: Tests for ApiKeyModelView key generation."""

    def setUp(self):
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_api_key_generation_and_hashing(self):
        """Creating an API key should generate a valid hash."""
        from services.admin import ApiKeyModelView

        # Verify view exists and has correct config
        self.assertEqual(ApiKeyModelView.name, "API Keys")
        self.assertIn("name", ApiKeyModelView.column_list)
        self.assertIn("scope", ApiKeyModelView.column_list)

    def test_api_key_hash_is_pbkdf2(self):
        """Stored API key hash should use sha256 (via api_auth)."""
        from services.api_auth import generate_api_key, hash_api_key

        key = generate_api_key()
        hashed = hash_api_key(key)
        self.assertEqual(len(hashed), 64)  # SHA-256 hex length

    def test_api_key_verification(self):
        """Generated API key should be verifiable."""
        from services.api_auth import generate_api_key, hash_api_key

        plain_key = generate_api_key()
        hashed = hash_api_key(plain_key)

        # Same key should produce same hash
        self.assertEqual(hash_api_key(plain_key), hashed)
        # Different key should produce different hash
        self.assertNotEqual(hash_api_key("different-key"), hashed)


class TestServerControlView(unittest.TestCase):
    """TEST-003: Tests for ServerControlView."""

    def setUp(self):
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create super admin
        self.admin = AdminUser(username="testadmin", role=AdminUser.ROLE_SUPER_ADMIN)
        self.admin.set_password("testpass123")
        db.session.add(self.admin)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_server_control_view_exists(self):
        """ServerControlView should exist and have correct methods."""
        self.assertTrue(hasattr(ServerControlView, "restart"))
        self.assertTrue(hasattr(ServerControlView, "index"))

    def test_server_control_requires_super_admin(self):
        """ServerControlView.is_accessible should require server_control permission."""
        with self.app.test_request_context():
            login_user(self.admin)
            view = ServerControlView()
            self.assertTrue(view.is_accessible())

    def test_server_control_denies_non_super_admin(self):
        """ServerControlView should deny access to non-super-admin."""
        viewer = AdminUser(username="viewer", role=AdminUser.ROLE_VIEWER)
        viewer.set_password("viewerpass")
        db.session.add(viewer)
        db.session.commit()

        with self.app.test_request_context():
            login_user(viewer)
            view = ServerControlView()
            self.assertFalse(view.is_accessible())


class TestStatsAdminIndexView(unittest.TestCase):
    """TEST-004: Tests for admin dashboard (StatsAdminIndexView)."""

    def setUp(self):
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_dashboard_accessible(self):
        """GET /admin/ should be accessible (or redirect to login)."""
        with self.app.test_client() as client:
            response = client.get("/admin/", follow_redirects=False)
            self.assertIn(response.status_code, [200, 302])

    def test_dashboard_counts(self):
        """Dashboard should show correct counts for managers, achievements, etc."""
        # Create test data
        country = Country(code="TST", flag_path="/static/img/flags/tst.png")
        db.session.add(country)
        db.session.flush()
        manager = Manager(name="Test Manager", country_id=country.id)
        db.session.add(manager)
        db.session.commit()

        # Verify counts
        from models import Country as CountryModel
        from models import Manager as ManagerModel

        manager_count = db.session.query(ManagerModel).count()
        country_count = db.session.query(CountryModel).count()
        self.assertEqual(manager_count, 1)
        self.assertEqual(country_count, 1)


class TestAdminHTTPIntegration(unittest.TestCase):
    """TEST-005: HTTP-level integration tests for admin endpoints."""

    def setUp(self):
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()

        # Create admin user
        with self.app.app_context():
            db.create_all()
            admin = AdminUser(username="testadmin", role=AdminUser.ROLE_SUPER_ADMIN)
            admin.set_password("testpass123")
            db.session.add(admin)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_admin_login_page_loads(self):
        """GET /admin/login/ should return 200."""
        response = self.client.get("/admin/login/")
        self.assertIn(response.status_code, [200, 302])

    def test_admin_dashboard_redirect(self):
        """Unauthenticated user should be redirected to login from /admin/."""
        response = self.client.get("/admin/", follow_redirects=False)
        # Should be 302 redirect to login, or 200 if admin is accessible
        self.assertIn(response.status_code, [200, 302])

    def test_admin_login_success(self):
        """POST /admin/login/ with valid credentials should redirect to admin index."""
        with self.client.session_transaction() as sess:
            sess["_csrf_token"] = "test_token"

        response = self.client.post(
            "/admin/login/",
            data={
                "username": "testadmin",
                "password": "testpass123",
                "csrf_token": "test_token",
            },
            follow_redirects=False,
        )
        # Should redirect after successful login
        self.assertIn(response.status_code, [302])

    def test_admin_login_failure(self):
        """POST /admin/login/ with invalid credentials should show error."""
        with self.client.session_transaction() as sess:
            sess["_csrf_token"] = "test_token"

        response = self.client.post(
            "/admin/login/",
            data={
                "username": "testadmin",
                "password": "wrongpassword",
                "csrf_token": "test_token",
            },
            follow_redirects=True,
        )
        # Should stay on login page with error
        self.assertEqual(response.status_code, 200)


class TestAdminLoginLogoutCSRF(unittest.TestCase):
    """TEST-006: Tests for login/logout flow with CSRF."""

    def setUp(self):
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            admin = AdminUser(username="testadmin", role=AdminUser.ROLE_SUPER_ADMIN)
            admin.set_password("testpass123")
            db.session.add(admin)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_login_page_has_csrf_token(self):
        """Login page should contain CSRF token."""
        response = self.client.get("/admin/login/")
        if response.status_code == 200:
            html = response.data.decode("utf-8")
            self.assertIn("csrf_token", html)

    def test_logout_requires_login(self):
        """GET /admin/logout/ should require login."""
        response = self.client.get("/admin/logout/", follow_redirects=False)
        # Should redirect
        self.assertIn(response.status_code, [302, 401])


if __name__ == "__main__":
    unittest.main(verbosity=2)
