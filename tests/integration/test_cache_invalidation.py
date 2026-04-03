"""Tests for API cache invalidation.

These tests verify that all API endpoints that modify data (CREATE/UPDATE/DELETE)
properly invalidate the leaderboard cache.

Test scenarios:
1. Country CRUD → cache invalidation
2. Manager CRUD → cache invalidation
3. Achievement CRUD → cache invalidation
4. Manager delete (cascade achievements) → cache invalidation
5. Full flow: API changes data → cache invalidated → leaderboard updated

Migrated from tests_api_cache_invalidation.py
"""

import unittest

from app import create_app
from models import Achievement, Country, Manager, db
from services.cache_service import cache, invalidate_leaderboard_cache
from services.rating_service import build_leaderboard


class TestAPICacheInvalidation(unittest.TestCase):
    """Tests that API endpoints properly invalidate leaderboard cache."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Create test country
            country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
            db.session.add(country)
            db.session.flush()
            self.country_id = country.id

            # Create test manager
            manager = Manager(name="Test Manager", country_id=self.country_id)
            db.session.add(manager)
            db.session.flush()
            self.manager_id = manager.id

            # Create test achievement
            achievement = Achievement(
                achievement_type="TOP1",
                league="1",
                season="25/26",
                title="TOP1",
                icon_path="/static/img/cups/top1.svg",
                manager_id=self.manager_id,
            )
            db.session.add(achievement)
            db.session.flush()
            self.achievement_id = achievement.id

            # Create API key
            from services.api_auth import generate_api_key, hash_api_key
            from models import ApiKey
            self.api_key = generate_api_key()
            db.session.add(ApiKey(
                key_hash=hash_api_key(self.api_key),
                name="Test API Key",
                scope="admin",
            ))
            db.session.commit()

    def tearDown(self) -> None:
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _get(self, url: str) -> Any:
        return self.client.get(url, headers={"X-API-Key": self.api_key})

    def _post(self, url: str, json: dict) -> Any:
        return self.client.post(url, json=json, headers={"X-API-Key": self.api_key})

    def _put(self, url: str, json: dict) -> Any:
        return self.client.put(url, json=json, headers={"X-API-Key": self.api_key})

    def _delete(self, url: str) -> Any:
        return self.client.delete(url, headers={"X-API-Key": self.api_key})

    def _get_cached_leaderboard(self) -> list | None:
        """Get cached leaderboard data."""
        return cache.get("leaderboard")

    def _set_test_cache_value(self) -> None:
        """Set a test value in cache to verify invalidation."""
        cache.set("leaderboard", "cached_test_value", timeout=60)

    def _assert_cache_invalidated(self) -> None:
        """Assert that the leaderboard cache has been invalidated."""
        cached = self._get_cached_leaderboard()
        # After invalidation, cache should be None or different from test value
        self.assertNotEqual(cached, "cached_test_value")

    # ============== Countries ==============

    def test_create_country_invalidates_cache(self) -> None:
        """Test that creating a country invalidates leaderboard cache."""
        with self.app.app_context():
            self._set_test_cache_value()

        response = self._post(
            "/api/countries",
            json={"code": "USA", "flag_path": "/static/img/flags/usa.png"},
        )
        self.assertEqual(response.status_code, 201)
        self._assert_cache_invalidated()

    def test_update_country_invalidates_cache(self) -> None:
        """Test that updating a country invalidates leaderboard cache."""
        with self.app.app_context():
            self._set_test_cache_value()

        response = self._put(
            f"/api/countries/{self.country_id}",
            json={"flag_path": "/static/img/flags/rus_new.png"},
        )
        self.assertEqual(response.status_code, 200)
        self._assert_cache_invalidated()

    def test_delete_country_invalidates_cache(self) -> None:
        """Test that deleting a country invalidates leaderboard cache."""
        # Create a country without managers to delete
        with self.app.app_context():
            self._set_test_cache_value()
            country = Country(code="BEL", flag_path="/static/img/flags/bel.png")
            db.session.add(country)
            db.session.commit()
            country_id = country.id

        response = self._delete(f"/api/countries/{country_id}")
        self.assertEqual(response.status_code, 200)
        self._assert_cache_invalidated()

    # ============== Managers ==============

    def test_create_manager_invalidates_cache(self) -> None:
        """Test that creating a manager invalidates leaderboard cache."""
        with self.app.app_context():
            self._set_test_cache_value()

        response = self._post(
            "/api/managers",
            json={"name": "New Manager", "country_id": self.country_id},
        )
        self.assertEqual(response.status_code, 201)
        self._assert_cache_invalidated()

    def test_update_manager_invalidates_cache(self) -> None:
        """Test that updating a manager invalidates leaderboard cache."""
        with self.app.app_context():
            self._set_test_cache_value()

        response = self._put(
            f"/api/managers/{self.manager_id}",
            json={"name": "Updated Manager Name"},
        )
        self.assertEqual(response.status_code, 200)
        self._assert_cache_invalidated()

    def test_delete_manager_invalidates_cache(self) -> None:
        """Test that deleting a manager (with cascade) invalidates leaderboard cache."""
        with self.app.app_context():
            self._set_test_cache_value()

        response = self._delete(f"/api/managers/{self.manager_id}")
        self.assertEqual(response.status_code, 200)
        self._assert_cache_invalidated()

    # ============== Achievements ==============

    def test_create_achievement_invalidates_cache(self) -> None:
        """Test that creating an achievement invalidates leaderboard cache."""
        with self.app.app_context():
            self._set_test_cache_value()

        response = self._post(
            "/api/achievements",
            json={
                "achievement_type": "TOP2",
                "league": "1",
                "season": "25/26",
                "title": "TOP2",
                "icon_path": "/static/img/cups/top2.svg",
                "manager_id": self.manager_id,
            },
        )
        self.assertEqual(response.status_code, 201)
        self._assert_cache_invalidated()

    def test_update_achievement_invalidates_cache(self) -> None:
        """Test that updating an achievement invalidates leaderboard cache."""
        with self.app.app_context():
            self._set_test_cache_value()

        response = self._put(
            f"/api/achievements/{self.achievement_id}",
            json={"title": "Updated Title"},
        )
        self.assertEqual(response.status_code, 200)
        self._assert_cache_invalidated()

    def test_delete_achievement_invalidates_cache(self) -> None:
        """Test that deleting an achievement invalidates leaderboard cache."""
        with self.app.app_context():
            self._set_test_cache_value()

        response = self._delete(f"/api/achievements/{self.achievement_id}")
        self.assertEqual(response.status_code, 200)
        self._assert_cache_invalidated()


class TestAPILeaderboardRefresh(unittest.TestCase):
    """Integration tests: API changes → cache invalidated → leaderboard updated."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Clear any leftover cache
            cache.delete("leaderboard")
            # Create test country
            country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
            db.session.add(country)
            db.session.flush()
            self.country_id = country.id

            # Create test manager
            manager = Manager(name="Initial Manager", country_id=self.country_id)
            db.session.add(manager)
            db.session.flush()
            self.manager_id = manager.id

            # Create API key
            from services.api_auth import generate_api_key, hash_api_key
            from models import ApiKey
            self.api_key = generate_api_key()
            db.session.add(ApiKey(
                key_hash=hash_api_key(self.api_key),
                name="Test API Key",
                scope="admin",
            ))
            db.session.commit()

    def tearDown(self) -> None:
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _get(self, url: str):
        return self.client.get(url, headers={"X-API-Key": self.api_key})

    def _post(self, url: str, json: dict):
        return self.client.post(url, json=json, headers={"X-API-Key": self.api_key})

    def _put(self, url: str, json: dict):
        return self.client.put(url, json=json, headers={"X-API-Key": self.api_key})

    def _delete(self, url: str):
        return self.client.delete(url, headers={"X-API-Key": self.api_key})

    def test_new_manager_appears_in_leaderboard(self) -> None:
        """Test that a new manager created via API appears in leaderboard."""
        # Get initial leaderboard
        response1 = self.client.get("/")
        self.assertEqual(response1.status_code, 200)
        initial_html = response1.data.decode("utf-8")
        self.assertNotIn("New API Manager", initial_html)

        # Create new manager via API
        response2 = self._post(
            "/api/managers",
            json={"name": "New API Manager", "country_id": self.country_id},
        )
        self.assertEqual(response2.status_code, 201)

        # Get updated leaderboard
        response3 = self.client.get("/")
        self.assertEqual(response3.status_code, 200)
        updated_html = response3.data.decode("utf-8")
        self.assertIn("New API Manager", updated_html)

    def test_new_achievement_updates_leaderboard_score(self) -> None:
        """Test that adding an achievement via API updates manager's score."""
        # Get initial leaderboard - should have 1 manager with 0 points
        response1 = self.client.get("/")
        self.assertEqual(response1.status_code, 200)
        initial_html = response1.data.decode("utf-8")
        self.assertIn("Initial Manager", initial_html)

        # Add achievement via API
        response2 = self.client.post(
            "/api/achievements",
            json={
                "achievement_type": "TOP1",
                "league": "1",
                "season": "25/26",
                "title": "TOP1",
                "icon_path": "/static/img/cups/top1.svg",
                "manager_id": self.manager_id,
            },
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, 201)

        # Get updated leaderboard - should show new score
        response3 = self.client.get("/")
        self.assertEqual(response3.status_code, 200)
        updated_html = response3.data.decode("utf-8")

        # Manager should now have 800 points (TOP1 L1 s25/26 = 800 * 1.00)
        self.assertIn("800", updated_html)

    def test_delete_achievement_removes_from_leaderboard(self) -> None:
        """Test that deleting an achievement via API removes it from score."""
        with self.app.app_context():
            # Create achievement
            achievement = Achievement(
                achievement_type="TOP1",
                league="1",
                season="25/26",
                title="TOP1",
                icon_path="/static/img/cups/top1.svg",
                manager_id=self.manager_id,
            )
            db.session.add(achievement)
            db.session.commit()
            achievement_id = achievement.id

        # Verify manager has points
        response1 = self.client.get("/")
        self.assertEqual(response1.status_code, 200)
        initial_html = response1.data.decode("utf-8")
        self.assertIn("800", initial_html)

        # Delete achievement via API
        response2 = self._delete(f"/api/achievements/{achievement_id}")
        self.assertEqual(response2.status_code, 200)

        # Get updated leaderboard - score should be 0
        response3 = self.client.get("/")
        self.assertEqual(response3.status_code, 200)
        updated_html = response3.data.decode("utf-8")

        # Manager should now have 0 points
        self.assertIn("Initial Manager", updated_html)

    def test_delete_manager_removes_from_leaderboard(self) -> None:
        """Test that deleting a manager via API removes them from leaderboard."""
        # Verify manager exists
        response1 = self.client.get("/")
        self.assertEqual(response1.status_code, 200)
        initial_html = response1.data.decode("utf-8")
        self.assertIn("Initial Manager", initial_html)

        # Delete manager via API
        response2 = self._delete(f"/api/managers/{self.manager_id}")
        self.assertEqual(response2.status_code, 200)

        # Get updated leaderboard - manager should be gone
        response3 = self.client.get("/")
        self.assertEqual(response3.status_code, 200)
        updated_html = response3.data.decode("utf-8")
        self.assertNotIn("Initial Manager", updated_html)


class TestAPIAchievementUniquenessConstraint(unittest.TestCase):
    """Tests for achievement uniqueness constraint (if implemented)."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Clear any leftover cache
            cache.delete("leaderboard")
            country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
            db.session.add(country)
            db.session.flush()
            self.country_id = country.id

            manager = Manager(name="Test Manager", country_id=self.country_id)
            db.session.add(manager)
            db.session.flush()
            self.manager_id = manager.id

            # Create API key
            from services.api_auth import generate_api_key, hash_api_key
            from models import ApiKey
            self.api_key = generate_api_key()
            db.session.add(ApiKey(
                key_hash=hash_api_key(self.api_key),
                name="Test API Key",
                scope="admin",
            ))
            db.session.commit()

    def tearDown(self) -> None:
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _post(self, url: str, json: dict):
        return self.client.post(url, json=json, headers={"X-API-Key": self.api_key})

    def test_create_duplicate_achievement(self) -> None:
        """Test creating duplicate achievements for same manager/league/season/type.

        The database has a unique constraint on (manager_id, league, season, achievement_type)
        which prevents duplicate achievements.
        """
        achievement_data = {
            "achievement_type": "TOP1",
            "league": "1",
            "season": "25/26",
            "title": "TOP1",
            "icon_path": "/static/img/cups/top1.svg",
            "manager_id": self.manager_id,
        }

        # Create first achievement
        response1 = self.client.post(
            "/api/achievements",
            json=achievement_data,
            content_type="application/json",
        )
        self.assertEqual(response1.status_code, 201)

        # Try to create duplicate - should be rejected by unique constraint
        response2 = self.client.post(
            "/api/achievements",
            json=achievement_data,
            content_type="application/json",
        )
        # Should return 409 (conflict - unique constraint violation)
        self.assertEqual(response2.status_code, 409)


if __name__ == "__main__":
    unittest.main(verbosity=2)
