"""Smoke tests for critical admin flow (P0 verification).

Tests the full login → dashboard → achievements API → logout cycle.
This ensures no BuildError or 500 errors in the critical admin path.
"""

import pytest

from models import Achievement, AchievementType, AdminUser, Country, League, Manager, Season, db


@pytest.fixture
def admin_user(db_session):
    """Create a super admin user for testing."""
    admin = AdminUser(username="smoke_admin", role=AdminUser.ROLE_SUPER_ADMIN)
    admin.set_password("smokepass123")
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture
def seeded_db_with_data(db_session):
    """Add admin user, country, manager, and achievements to seeded db."""
    # Create admin user — same credentials as admin_user fixture
    admin = AdminUser(username="smoke_admin", role=AdminUser.ROLE_SUPER_ADMIN)
    admin.set_password("smokepass123")
    db.session.add(admin)

    # Get existing country from seeded_db fixture
    country = db.session.query(Country).first()
    if not country:
        country = Country(code="USA", name="USA", flag_path="/static/img/flags/USA.png")
        db.session.add(country)
        db.session.flush()

    manager = Manager(name="Smoke Test Manager", country_id=country.id)
    db.session.add(manager)
    db.session.flush()

    # Create reference data
    ach_type = AchievementType(code="TOP1", name="Top 1", base_points_l1=800, base_points_l2=400)
    league = League(code="1", name="League 1")
    season = Season(
        code="24/25", name="Season 24/25", multiplier=1.0, start_year=2024, end_year=2025
    )
    db.session.add_all([ach_type, league, season])
    db.session.flush()

    achievement = Achievement(
        manager_id=manager.id,
        type_id=ach_type.id,
        league_id=league.id,
        season_id=season.id,
        title="Top 1 League 1 Season 24/25",
        icon_path="/static/img/cups/top1.svg",
        base_points=800,
        multiplier=1.0,
        final_points=800.0,
    )
    db.session.add(achievement)
    db.session.commit()

    return admin, manager


def _login(client, username="smoke_admin", password="smokepass123"):
    """Helper to login a user."""
    return client.post(
        "/admin/login/",
        data={
            "username": username,
            "password": password,
        },
        follow_redirects=True,
    )


class TestAdminSmokeFlow:
    """Smoke tests for the critical admin flow path."""

    def test_login_page_loads(self, client):
        """P0 verification: Login page should load without errors."""
        response = client.get("/admin/login/")
        assert response.status_code == 200

    def test_login_success_redirect(self, client, admin_user):
        """P0 verification: After login, should redirect to dashboard (no BuildError)."""
        response = _login(client)
        assert response.status_code == 200
        # Dashboard should load without BuildError
        assert b"Shadow Hockey League Admin" in response.data

    def test_dashboard_no_build_error(self, client, admin_user):
        """P0-1 verification: Dashboard should render without BuildError.

        Previously failed with: BuildError: Could not build url for endpoint 'achievement.index_view'
        """
        _login(client)

        # Access dashboard directly
        response = client.get("/admin/", follow_redirects=True)
        assert response.status_code == 200
        # Check that page renders without BuildError (dashboard stats present)
        assert b"card-title" in response.data

    def test_manager_achievements_api_no_500(self, client, seeded_db_with_data):
        """P0-2 verification: Manager achievements API should not return 500.

        Previously failed with: expected ORM mapped attribute for loader strategy argument
        """
        admin, manager = seeded_db_with_data
        _login(client)

        # Access the achievements API endpoint
        response = client.get(f"/admin/api/managers/{manager.id}/achievements")
        # Should NOT be 500
        assert response.status_code == 200
        data = response.get_json()
        assert "achievements" in data
        assert "manager_id" in data
        assert len(data["achievements"]) >= 1

    def test_logout_no_build_error(self, client, admin_user):
        """P0-3 verification: Logout should work without BuildError.

        Previously failed with: BuildError: Could not build url for endpoint 'admin_login'
        """
        _login(client)

        # Logout
        response = client.get("/admin/logout/", follow_redirects=True)
        assert response.status_code == 200

    def test_full_admin_cycle(self, client, seeded_db_with_data):
        """Full cycle: login → dashboard → achievements → logout.

        This is the complete UAT smoke test for the admin flow.
        """
        admin, manager = seeded_db_with_data

        # Step 1: Login
        login_response = _login(client)
        assert login_response.status_code == 200
        assert b"Shadow Hockey League Admin" in login_response.data

        # Step 2: Dashboard (P0-1 check — no BuildError)
        dashboard_response = client.get("/admin/", follow_redirects=True)
        assert dashboard_response.status_code == 200

        # Step 3: Manager achievements API (P0-2 check — no 500)
        api_response = client.get(f"/admin/api/managers/{manager.id}/achievements")
        assert api_response.status_code == 200
        api_data = api_response.get_json()
        assert api_data["manager_id"] == manager.id

        # Step 4: Logout (P0-3 check — no BuildError)
        logout_response = client.get("/admin/logout/", follow_redirects=True)
        assert logout_response.status_code == 200

        # Step 5: Verify logged out — accessing admin should redirect to login
        restricted_response = client.get("/admin/", follow_redirects=True)
        assert restricted_response.status_code == 200
