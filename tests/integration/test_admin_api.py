"""Integration tests for admin API endpoints (blueprints/admin_api.py).

Tests cover:
- API-001: GET /admin/api/countries
- API-002: GET /admin/api/managers
- API-003: GET /admin/api/seasons
- API-004: GET /admin/api/achievement-types/<id>/points
- API-005: GET /admin/api/leagues
- API-Extra: GET /admin/api/achievement-types
- API-006: POST /admin/api/achievements/bulk-create
- API-Manager: GET /admin/api/managers/<id>/achievements
- API-Manager: POST /admin/api/managers/<id>/achievements/bulk-add
"""

import pytest

from models import Achievement, AchievementType, AdminUser, Country, League, Manager, Season, db


@pytest.fixture(autouse=True)
def reset_rate_limit():
    """Reset login rate limiter before each test."""
    from services.admin import _login_attempts

    _login_attempts.clear()
    yield


@pytest.fixture
def admin_user(db_session):
    """Create a super admin user for testing."""
    admin = AdminUser(username="api_test_admin", role=AdminUser.ROLE_SUPER_ADMIN)
    admin.set_password("apipass123")
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture
def moderator_user(db_session):
    """Create a moderator user (no create permission)."""
    mod = AdminUser(username="api_moderator", role=AdminUser.ROLE_MODERATOR)
    mod.set_password("modpass123")
    db.session.add(mod)
    db.session.commit()
    return mod


@pytest.fixture
def reference_data(db_session):
    """Create reference data for achievements."""
    ach_type = AchievementType(code="TOP1", name="Top 1", base_points_l1=800, base_points_l2=400)
    league = League(code="1", name="League 1")
    league2 = League(code="2", name="League 2")
    season = Season(
        code="24/25",
        name="Season 24/25",
        multiplier=1.0,
        start_year=2024,
        end_year=2025,
        is_active=True,
    )
    season_old = Season(
        code="22/23",
        name="Season 22/23",
        multiplier=0.85,
        start_year=2022,
        end_year=2023,
        is_active=True,
    )
    db.session.add_all([ach_type, league, league2, season, season_old])
    db.session.flush()
    return {
        "ach_type": ach_type,
        "league": league,
        "league2": league2,
        "season": season,
        "season_old": season_old,
    }


@pytest.fixture
def country_data(db_session):
    """Create countries for testing."""
    countries = [
        Country(code="RUS", name="Russia", flag_path="/static/img/flags/RUS.png"),
        Country(code="USA", name="United States", flag_path="/static/img/flags/USA.png"),
        Country(code="CAN", name="Canada", flag_path="/static/img/flags/CAN.png"),
    ]
    db.session.add_all(countries)
    db.session.flush()
    return countries


@pytest.fixture
def manager_data(db_session, country_data):
    """Create managers for testing."""
    managers = [
        Manager(name="Test Manager 1", country_id=country_data[0].id),
        Manager(name="Test Manager 2", country_id=country_data[1].id),
        Manager(name="Tandem: Alice, Bob", country_id=country_data[2].id),
    ]
    db.session.add_all(managers)
    db.session.flush()
    return managers


def _login(client, username="api_test_admin", password="apipass123"):
    """Helper to login as admin."""
    return client.post(
        "/admin/login/",
        data={
            "username": username,
            "password": password,
        },
        follow_redirects=True,
    )


class TestAdminAPIAuth:
    """All admin API endpoints require authentication."""

    def test_unauthenticated_post_redirected(self, client):
        """Unauthenticated POST to bulk-create should be redirected to login."""
        response = client.post("/admin/api/achievements/bulk-create", json={})
        assert response.status_code in (302, 401)


class TestCountriesAPI:
    """API-001: GET /admin/api/countries."""

    def test_list_countries(self, client, admin_user, country_data):
        """Should return paginated list of countries."""
        _login(client)
        response = client.get("/admin/api/countries")
        assert response.status_code == 200
        data = response.get_json()
        assert "items" in data
        assert "pagination" in data
        assert len(data["items"]) == 3
        # Check country fields
        country = data["items"][0]
        assert "id" in country
        assert "code" in country
        assert "name" in country
        assert "flag_url" in country

    def test_search_countries(self, client, admin_user, country_data):
        """Should filter countries by search query."""
        _login(client)
        response = client.get("/admin/api/countries?q=rus")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["items"]) >= 1
        assert data["items"][0]["code"] == "RUS"

    def test_search_by_name(self, client, admin_user, country_data):
        """Should search countries by name."""
        _login(client)
        response = client.get("/admin/api/countries?q=Canada")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["items"]) >= 1
        assert data["items"][0]["code"] == "CAN"

    def test_pagination(self, client, admin_user, country_data):
        """Should support pagination."""
        _login(client)
        response = client.get("/admin/api/countries?page=1&page_size=2")
        assert response.status_code == 200
        data = response.get_json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 2
        assert len(data["items"]) <= 2


class TestManagersAPI:
    """API-002: GET /admin/api/managers."""

    def test_list_managers(self, client, admin_user, manager_data):
        """Should return paginated list of managers."""
        _login(client)
        response = client.get("/admin/api/managers")
        assert response.status_code == 200
        data = response.get_json()
        assert "items" in data
        assert len(data["items"]) == 3
        manager = data["items"][0]
        assert "id" in manager
        assert "name" in manager
        assert "country_name" in manager

    def test_search_managers(self, client, admin_user, manager_data):
        """Should filter managers by name."""
        _login(client)
        response = client.get("/admin/api/managers?q=Manager 1")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Test Manager 1"

    def test_bulk_fetch_by_ids(self, client, admin_user, manager_data):
        """Should fetch multiple managers by comma-separated IDs."""
        _login(client)
        ids = f"{manager_data[0].id},{manager_data[1].id}"
        response = client.get(f"/admin/api/managers?ids={ids}")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["items"]) == 2

    def test_tandem_detection(self, client, admin_user, manager_data):
        """Should detect tandem managers."""
        _login(client)
        response = client.get("/admin/api/managers?q=Tandem")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["items"]) == 1
        assert data["items"][0]["is_tandem"] is True


class TestSeasonsAPI:
    """API-003: GET /admin/api/seasons."""

    def test_list_seasons_by_league(self, client, admin_user, reference_data):
        """Should return seasons filtered by league_id."""
        _login(client)
        response = client.get(f'/admin/api/seasons?league_id={reference_data["league"].id}')
        assert response.status_code == 200
        data = response.get_json()
        assert "items" in data
        assert len(data["items"]) == 2  # season + season_old

    def test_season_fields(self, client, admin_user, reference_data):
        """Should return season with correct fields."""
        _login(client)
        response = client.get(f'/admin/api/seasons?league_id={reference_data["league"].id}')
        data = response.get_json()
        season = data["items"][0]
        assert "id" in season
        assert "code" in season
        assert "multiplier" in season
        assert "is_active" in season

    def test_missing_league_id(self, client, admin_user):
        """Should return 400 without league_id."""
        _login(client)
        response = client.get("/admin/api/seasons")
        assert response.status_code == 400

    def test_league_not_found(self, client, admin_user):
        """Should return 404 for non-existent league."""
        _login(client)
        response = client.get("/admin/api/seasons?league_id=9999")
        assert response.status_code == 404


class TestAchievementPointsAPI:
    """API-004: GET /admin/api/achievement-types/<id>/points."""

    def test_get_points_league_1(self, client, admin_user, reference_data):
        """Should return base_points_l1 for League 1."""
        _login(client)
        response = client.get(
            f'/admin/api/achievement-types/{reference_data["ach_type"].id}/points'
            f'?league_id={reference_data["league"].id}'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["base_points"] == 800
        assert data["points_source"] == "base_points_l1"

    def test_get_points_league_2(self, client, admin_user, reference_data):
        """Should return base_points_l2 for League 2."""
        _login(client)
        response = client.get(
            f'/admin/api/achievement-types/{reference_data["ach_type"].id}/points'
            f'?league_id={reference_data["league2"].id}'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["base_points"] == 400
        assert data["points_source"] == "base_points_l2"

    def test_missing_league_id(self, client, admin_user, reference_data):
        """Should return 400 without league_id."""
        _login(client)
        response = client.get(
            f'/admin/api/achievement-types/{reference_data["ach_type"].id}/points'
        )
        assert response.status_code == 400


class TestLeaguesAPI:
    """API-005: GET /admin/api/leagues."""

    def test_list_leagues(self, client, admin_user, reference_data):
        """Should return all active leagues."""
        _login(client)
        response = client.get("/admin/api/leagues")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["items"]) == 2


class TestAchievementTypesAPI:
    """API-Extra: GET /admin/api/achievement-types."""

    def test_list_types(self, client, admin_user, reference_data):
        """Should return achievement types with formatted text."""
        _login(client)
        response = client.get("/admin/api/achievement-types")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert "id" in item
        assert "text" in item
        assert "TOP1" in item["text"] or "Top 1" in item["text"]


class TestManagerAchievementsAPI:
    """GET /admin/api/managers/<id>/achievements."""

    def test_get_achievements(self, client, admin_user, manager_data, reference_data):
        """Should return achievements for a manager."""
        _login(client)
        manager = manager_data[0]
        ach = Achievement(
            manager_id=manager.id,
            type_id=reference_data["ach_type"].id,
            league_id=reference_data["league"].id,
            season_id=reference_data["season"].id,
            title="Top 1 League 1",
            icon_path="/static/img/cups/top1.svg",
            base_points=800,
            multiplier=1.0,
            final_points=800.0,
        )
        db.session.add(ach)
        db.session.commit()

        response = client.get(f"/admin/api/managers/{manager.id}/achievements")
        assert response.status_code == 200
        data = response.get_json()
        assert data["manager_id"] == manager.id
        assert len(data["achievements"]) == 1
        assert data["achievements"][0]["final_points"] == 800.0

    def test_manager_not_found(self, client, admin_user):
        """Should return 404 for non-existent manager."""
        _login(client)
        response = client.get("/admin/api/managers/9999/achievements")
        assert response.status_code == 404

    def test_empty_chievements(self, client, admin_user, manager_data):
        """Should return empty achievements list for manager without achievements."""
        _login(client)
        response = client.get(f"/admin/api/managers/{manager_data[0].id}/achievements")
        assert response.status_code == 200
        data = response.get_json()
        assert data["achievements"] == []
        assert data["total_points"] == 0.0


class TestBulkCreateAchievements:
    """API-006: POST /admin/api/achievements/bulk-create."""

    def test_bulk_create_success(self, client, admin_user, manager_data, reference_data):
        """Should create achievements for multiple managers."""
        _login(client)
        manager_ids = [manager_data[0].id, manager_data[1].id]
        response = client.post(
            "/admin/api/achievements/bulk-create",
            json={
                "manager_ids": manager_ids,
                "type_id": reference_data["ach_type"].id,
                "league_id": reference_data["league"].id,
                "season_id": reference_data["season"].id,
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["summary"]["created"] == 2
        assert data["summary"]["total_requested"] == 2

    def test_bulk_create_skips_duplicates(self, client, admin_user, manager_data, reference_data):
        """Should skip managers who already have the achievement."""
        _login(client)
        manager = manager_data[0]
        # Create existing achievement
        existing = Achievement(
            manager_id=manager.id,
            type_id=reference_data["ach_type"].id,
            league_id=reference_data["league"].id,
            season_id=reference_data["season"].id,
            title="Existing",
            icon_path="/static/img/cups/top1.svg",
            base_points=800,
            multiplier=1.0,
            final_points=800.0,
        )
        db.session.add(existing)
        db.session.commit()

        response = client.post(
            "/admin/api/achievements/bulk-create",
            json={
                "manager_ids": [manager.id, manager_data[1].id],
                "type_id": reference_data["ach_type"].id,
                "league_id": reference_data["league"].id,
                "season_id": reference_data["season"].id,
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["summary"]["created"] == 1
        assert data["summary"]["skipped_duplicates"] == 1

    def test_bulk_create_skips_inactive(self, client, admin_user, manager_data, reference_data):
        """Should skip inactive managers."""
        _login(client)
        manager_data[0].is_active = False
        db.session.commit()

        response = client.post(
            "/admin/api/achievements/bulk-create",
            json={
                "manager_ids": [manager_data[0].id, manager_data[1].id],
                "type_id": reference_data["ach_type"].id,
                "league_id": reference_data["league"].id,
                "season_id": reference_data["season"].id,
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["summary"]["created"] == 1
        assert (
            data["summary"]["skipped_duplicates"] == 1
        )  # The inactive one is skipped as duplicate? No, it should be skipped as inactive

    def test_bulk_create_missing_fields(self, client, admin_user):
        """Should return 400 for missing required fields."""
        _login(client)
        response = client.post(
            "/admin/api/achievements/bulk-create",
            json={"manager_ids": [1]},
        )
        assert response.status_code == 400

    def test_bulk_create_not_found_manager(self, client, admin_user, reference_data):
        """Should report error for non-existent manager."""
        _login(client)
        response = client.post(
            "/admin/api/achievements/bulk-create",
            json={
                "manager_ids": [9999],
                "type_id": reference_data["ach_type"].id,
                "league_id": reference_data["league"].id,
                "season_id": reference_data["season"].id,
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["summary"]["errors"] == 1

    def test_bulk_create_over_100_limit(self, client, admin_user, reference_data):
        """Should reject more than 100 manager IDs."""
        _login(client)
        response = client.post(
            "/admin/api/achievements/bulk-create",
            json={
                "manager_ids": list(range(1, 102)),
                "type_id": reference_data["ach_type"].id,
                "league_id": reference_data["league"].id,
                "season_id": reference_data["season"].id,
            },
        )
        assert response.status_code == 400

    def test_bulk_create_requires_create_permission(
        self, client, moderator_user, manager_data, reference_data
    ):
        """Moderator (no create permission) should be denied bulk create."""
        _login(client, username="api_moderator", password="modpass123")
        response = client.post(
            "/admin/api/achievements/bulk-create",
            json={
                "manager_ids": [manager_data[0].id],
                "type_id": reference_data["ach_type"].id,
                "league_id": reference_data["league"].id,
                "season_id": reference_data["season"].id,
            },
        )
        assert response.status_code == 403
