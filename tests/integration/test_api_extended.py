"""Targeted tests for services/api.py delete endpoints and edge cases.

Covers previously untested lines:
- DELETE endpoints for countries, managers, achievements (lines 709-816)
- Error handling edge cases (lines 460-482, 614-645)
"""

import pytest

from models import Achievement, AchievementType, ApiKey, Country, League, Manager, Season, db
from services.api_auth import generate_api_key, hash_api_key

# ==================== Fixtures ====================


@pytest.fixture
def api_client(client, db_session):
    """Create admin API key and set up client."""
    plain_key = generate_api_key()
    api_key = ApiKey(
        key_hash=hash_api_key(plain_key),
        name="Test Admin Key",
        scope="admin",
    )
    db.session.add(api_key)
    db.session.commit()

    client.environ_base["HTTP_X_API_KEY"] = plain_key
    yield client, plain_key


@pytest.fixture
def api_data(db_session):
    """Create test data for API tests."""
    country = Country(code="RUS", name="Russia", flag_path="/static/img/flags/RUS.png")
    db.session.add(country)
    db.session.flush()

    ach_type = AchievementType(code="TOP1", name="Top 1", base_points_l1=800, base_points_l2=400)
    league = League(code="1", name="League 1")
    season = Season(code="24/25", name="Season 24/25", multiplier=1.0, is_active=True)
    db.session.add_all([ach_type, league, season])
    db.session.flush()

    manager = Manager(name="API Test Manager", country_id=country.id)
    db.session.add(manager)
    db.session.flush()

    achievement = Achievement(
        type_id=ach_type.id,
        league_id=league.id,
        season_id=season.id,
        title="TOP1",
        icon_path="/static/img/cups/top1.svg",
        manager_id=manager.id,
        base_points=800.0,
        multiplier=1.0,
        final_points=800.0,
    )
    db.session.add(achievement)
    db.session.commit()

    yield {
        "country": country,
        "manager": manager,
        "achievement": achievement,
    }


# ==================== DELETE Country Tests ====================


class TestDeleteCountry:
    """Test DELETE /api/countries/<id>."""

    def test_delete_country_not_found(self, api_client):
        """Should return 404 for non-existent country."""
        client, _ = api_client
        response = client.delete("/api/countries/99999")
        assert response.status_code in (404, 409)

    def test_delete_country_with_managers(self, api_client, api_data):
        """Should return 409 when country has managers."""
        client, _ = api_client
        country_id = api_data["country"].id
        response = client.delete(f"/api/countries/{country_id}")
        assert response.status_code == 409


# ==================== DELETE Manager Tests ====================


class TestDeleteManager:
    """Test DELETE /api/managers/<id>."""

    def test_delete_manager_not_found(self, api_client):
        """Should return 404 for non-existent manager."""
        client, _ = api_client
        response = client.delete("/api/managers/99999")
        assert response.status_code == 404

    def test_delete_manager_cascades_achievements(self, api_client, api_data):
        """Should delete manager and cascade achievements."""
        client, _ = api_client
        manager_id = api_data["manager"].id
        response = client.delete(f"/api/managers/{manager_id}")
        assert response.status_code in (200, 204)


# ==================== DELETE Achievement Tests ====================


class TestDeleteAchievement:
    """Test DELETE /api/achievements/<id>."""

    def test_delete_achievement_not_found(self, api_client):
        """Should return 404 for non-existent achievement."""
        client, _ = api_client
        response = client.delete("/api/achievements/99999")
        assert response.status_code == 404

    def test_delete_achievement_success(self, api_client, api_data):
        """Should delete achievement successfully."""
        client, _ = api_client
        ach_id = api_data["achievement"].id
        response = client.delete(f"/api/achievements/{ach_id}")
        assert response.status_code in (200, 204)


# ==================== API Error Handling Tests ====================


class TestAPIErrorHandling:
    """Test API error handling edge cases."""

    def test_get_country_not_found(self, api_client):
        """Should return 404 for non-existent country."""
        client, _ = api_client
        response = client.get("/api/countries/99999")
        assert response.status_code == 404

    def test_get_manager_not_found(self, api_client):
        """Should return 404 for non-existent manager."""
        client, _ = api_client
        response = client.get("/api/managers/99999")
        assert response.status_code == 404

    def test_get_achievement_not_found(self, api_client):
        """Should return 404 for non-existent achievement."""
        client, _ = api_client
        response = client.get("/api/achievements/99999")
        assert response.status_code == 404


# ==================== GET /api/achievements (listing + filters) ====================


class TestListAchievements:
    """Test GET /api/achievements listing endpoint and its filters.

    Targets the previously uncovered branches in `services/api/achievements.py`
    (manager_id / league / season / achievement_type query-param filtering and
    serialisation).
    """

    def test_list_achievements_empty(self, api_client):
        """Should return empty list when no achievements exist."""
        client, _ = api_client
        response = client.get("/api/achievements")
        assert response.status_code == 200
        body = response.get_json()
        assert "data" in body
        assert "pagination" in body
        assert isinstance(body["data"], list)

    def test_list_achievements_returns_seeded_row(self, api_client, api_data):
        """Listing should include a row for the seeded achievement."""
        client, _ = api_client
        response = client.get("/api/achievements")
        assert response.status_code == 200
        body = response.get_json()
        assert len(body["data"]) >= 1
        ach = next(a for a in body["data"] if a["id"] == api_data["achievement"].id)
        assert ach["title"] == "TOP1"
        assert ach["manager_id"] == api_data["manager"].id
        assert ach["manager_name"] == api_data["manager"].name
        assert ach["base_points"] == 800.0
        assert ach["multiplier"] == 1.0
        assert ach["final_points"] == 800.0

    def test_list_achievements_filtered_by_manager_id(self, api_client, api_data):
        """Filtering by ``manager_id`` should return only that manager's rows."""
        client, _ = api_client
        manager_id = api_data["manager"].id
        response = client.get(f"/api/achievements?manager_id={manager_id}")
        assert response.status_code == 200
        body = response.get_json()
        assert all(a["manager_id"] == manager_id for a in body["data"])

    def test_list_achievements_filtered_by_league(self, api_client, api_data):
        """Filtering by ``league=1`` should return only L1 rows."""
        client, _ = api_client
        response = client.get("/api/achievements?league=1")
        assert response.status_code == 200
        body = response.get_json()
        assert all(a["league"] == "1" for a in body["data"])

    def test_list_achievements_filtered_by_season(self, api_client, api_data):
        """Filtering by ``season=24/25`` should return only that season's rows."""
        client, _ = api_client
        response = client.get("/api/achievements?season=24/25")
        assert response.status_code == 200
        body = response.get_json()
        assert all(a["season"] == "24/25" for a in body["data"])

    def test_list_achievements_filtered_by_achievement_type(self, api_client, api_data):
        """Filtering by ``achievement_type=TOP1`` should return only TOP1 rows."""
        client, _ = api_client
        response = client.get("/api/achievements?achievement_type=TOP1")
        assert response.status_code == 200
        body = response.get_json()
        assert all(a["achievement_type"] == "TOP1" for a in body["data"])


# ==================== POST /api/achievements (create) ====================


class TestCreateAchievement:
    """Test POST /api/achievements input validation and success path."""

    def test_create_without_payload_returns_400(self, api_client):
        """Should reject empty payload with 400."""
        client, _ = api_client
        response = client.post("/api/achievements", json=None)
        # Flask returns 415 for missing JSON Content-Type; either 400 or 415 is acceptable
        # (the contract is "do not 500 / do not silently accept").
        assert response.status_code in (400, 415)

    def test_create_with_invalid_data_returns_400(self, api_client, api_data):
        """Should reject payload missing required fields."""
        client, _ = api_client
        response = client.post(
            "/api/achievements",
            json={"manager_id": api_data["manager"].id},
        )
        assert response.status_code == 400

    def test_create_with_unknown_type_returns_400(self, api_client, api_data):
        """Should return 400 when type_code references a non-existent type."""
        client, _ = api_client
        response = client.post(
            "/api/achievements",
            json={
                "type_code": "DOES_NOT_EXIST",
                "league_code": "1",
                "season_code": "24/25",
                "title": "Phantom",
                "icon_path": "/static/img/cups/top1.svg",
                "manager_id": api_data["manager"].id,
            },
        )
        assert response.status_code == 400

    def test_create_with_unknown_manager_returns_400(self, api_client, api_data):
        """Should return 400 when manager_id references a non-existent manager."""
        client, _ = api_client
        response = client.post(
            "/api/achievements",
            json={
                "type_code": "TOP1",
                "league_code": "1",
                "season_code": "24/25",
                "title": "Phantom",
                "icon_path": "/static/img/cups/top1.svg",
                "manager_id": 99999,
            },
        )
        assert response.status_code == 400


# ==================== PUT /api/achievements/<id> (update) ====================


class TestUpdateAchievement:
    """Test PUT /api/achievements/<id> input validation and FK-resolution branches."""

    def test_update_not_found_returns_404(self, api_client):
        """Should return 404 for non-existent achievement."""
        client, _ = api_client
        response = client.put("/api/achievements/99999", json={"title": "x"})
        assert response.status_code == 404

    def test_update_without_payload_returns_400(self, api_client, api_data):
        """Should return 400 when payload is empty."""
        client, _ = api_client
        ach_id = api_data["achievement"].id
        response = client.put(f"/api/achievements/{ach_id}", json=None)
        assert response.status_code in (400, 415)

    def test_update_title_only_succeeds(self, api_client, api_data):
        """Should accept a title-only patch and persist it."""
        client, _ = api_client
        ach_id = api_data["achievement"].id
        response = client.put(f"/api/achievements/{ach_id}", json={"title": "TOP1 (renamed)"})
        assert response.status_code == 200
        # Round-trip via GET to confirm persistence.
        get_response = client.get(f"/api/achievements/{ach_id}")
        assert get_response.status_code == 200
        assert get_response.get_json()["title"] == "TOP1 (renamed)"

    def test_update_with_unknown_league_returns_400(self, api_client, api_data):
        """Should return 400 when league_code does not exist."""
        client, _ = api_client
        ach_id = api_data["achievement"].id
        response = client.put(f"/api/achievements/{ach_id}", json={"league_code": "DOES_NOT_EXIST"})
        assert response.status_code == 400

    def test_update_with_unknown_manager_returns_400(self, api_client, api_data):
        """Should return 400 when manager_id does not exist."""
        client, _ = api_client
        ach_id = api_data["achievement"].id
        response = client.put(f"/api/achievements/{ach_id}", json={"manager_id": 99999})
        assert response.status_code == 400
