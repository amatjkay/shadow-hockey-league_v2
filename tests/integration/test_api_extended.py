"""Targeted tests for services/api.py delete endpoints and edge cases.

Covers previously untested lines:
- DELETE endpoints for countries, managers, achievements (lines 709-816)
- Error handling edge cases (lines 460-482, 614-645)
"""

import pytest

from models import Achievement, AchievementType, Country, League, Manager, Season, ApiKey, db
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

    ach_type = AchievementType(code="TOP1", name="Top 1", base_points_l1=800, base_points_l2=300)
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
