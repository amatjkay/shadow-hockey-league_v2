"""Tests for API authentication and pagination.

Tests cover:
1. API key authentication (valid, invalid, expired, revoked, missing)
2. Scope enforcement (read/write/admin)
3. Pagination (page, per_page, max cap, response format)
4. Rate limiting
"""

import unittest
from datetime import datetime, timedelta, timezone

from app import create_app
from models import Achievement, AchievementType, ApiKey, Country, League, Manager, Season, db
from services.api_auth import generate_api_key, hash_api_key


def _seed_reference_data():
    """Seed reference tables. Returns (league_ids, season_ids, type_map)."""
    leagues = {}
    for code in ["1", "2"]:
        lg = League(code=code, name=f"League {code}")
        db.session.add(lg)
        leagues[code] = lg

    seasons = {}
    multipliers = {"25/26": 1.00, "24/25": 0.95, "23/24": 0.90, "22/23": 0.85, "21/22": 0.80}
    for i, code in enumerate(["25/26", "24/25", "23/24", "22/23", "21/22"]):
        s = Season(
            code=code, name=f"Season {code}", multiplier=multipliers[code], is_active=(i == 0)
        )
        db.session.add(s)
        seasons[code] = s

    type_points = {
        "TOP1": (800, 400),
        "TOP2": (400, 200),
        "TOP3": (200, 100),
        "BEST": (50, 40),
        "R3": (30, 20),
        "R1": (10, 5),
    }
    types = {}
    for code, (bp_l1, bp_l2) in type_points.items():
        at = AchievementType(code=code, name=code, base_points_l1=bp_l1, base_points_l2=bp_l2)
        db.session.add(at)
        types[code] = at

    db.session.flush()
    return {c: lg.id for c, lg in leagues.items()}, {c: s.id for c, s in seasons.items()}, types


class TestAPIAuthentication(unittest.TestCase):
    """Tests for API key authentication."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            league_ids, season_ids, type_map = _seed_reference_data()

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

            # Create test achievements
            achievement = Achievement(
                type_id=type_map["TOP1"].id,
                league_id=league_ids["1"],
                season_id=season_ids["24/25"],
                title="TOP1",
                icon_path="/static/img/cups/top1.svg",
                manager_id=self.manager_id,
            )
            db.session.add(achievement)
            db.session.flush()
            self.achievement_id = achievement.id

            # Create API keys with different scopes
            self.admin_key = generate_api_key()
            db.session.add(
                ApiKey(
                    key_hash=hash_api_key(self.admin_key),
                    name="Admin Test Key",
                    scope="admin",
                )
            )

            self.write_key = generate_api_key()
            db.session.add(
                ApiKey(
                    key_hash=hash_api_key(self.write_key),
                    name="Write Test Key",
                    scope="write",
                )
            )

            self.read_key = generate_api_key()
            db.session.add(
                ApiKey(
                    key_hash=hash_api_key(self.read_key),
                    name="Read Test Key",
                    scope="read",
                )
            )

            # Create expired key
            self.expired_key = generate_api_key()
            db.session.add(
                ApiKey(
                    key_hash=hash_api_key(self.expired_key),
                    name="Expired Key",
                    scope="read",
                    expires_at=datetime.now(timezone.utc) - timedelta(days=1),
                )
            )

            # Create revoked key
            self.revoked_key = generate_api_key()
            db.session.add(
                ApiKey(
                    key_hash=hash_api_key(self.revoked_key),
                    name="Revoked Key",
                    scope="read",
                    revoked=True,
                )
            )

            db.session.commit()

    def tearDown(self) -> None:
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_missing_api_key(self) -> None:
        """Request without API key should return 401."""
        response = self.client.get("/api/managers")
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn("error", data)

    def test_invalid_api_key(self) -> None:
        """Request with invalid API key should return 401."""
        response = self.client.get(
            "/api/managers",
            headers={"X-API-Key": "invalid_key"},
        )
        self.assertEqual(response.status_code, 401)

    def test_expired_api_key(self) -> None:
        """Request with expired API key should return 401."""
        response = self.client.get(
            "/api/managers",
            headers={"X-API-Key": self.expired_key},
        )
        self.assertEqual(response.status_code, 401)

    def test_revoked_api_key(self) -> None:
        """Request with revoked API key should return 401."""
        response = self.client.get(
            "/api/managers",
            headers={"X-API-Key": self.revoked_key},
        )
        self.assertEqual(response.status_code, 401)

    def test_read_key_can_access_get_endpoints(self) -> None:
        """Read key should access GET endpoints."""
        response = self.client.get(
            "/api/managers",
            headers={"X-API-Key": self.read_key},
        )
        self.assertEqual(response.status_code, 200)

    def test_read_key_cannot_access_post_endpoints(self) -> None:
        """Read key should NOT access POST endpoints."""
        response = self.client.post(
            "/api/managers",
            json={"name": "New Manager", "country_id": self.country_id},
            headers={"X-API-Key": self.read_key},
        )
        self.assertEqual(response.status_code, 403)

    def test_write_key_can_access_post_endpoints(self) -> None:
        """Write key should access POST/PUT endpoints."""
        response = self.client.post(
            "/api/managers",
            json={"name": "New Manager", "country_id": self.country_id},
            headers={"X-API-Key": self.write_key},
        )
        self.assertEqual(response.status_code, 201)

    def test_write_key_cannot_access_delete_endpoints(self) -> None:
        """Write key should NOT access DELETE endpoints."""
        response = self.client.delete(
            f"/api/managers/{self.manager_id}",
            headers={"X-API-Key": self.write_key},
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_key_can_access_all_endpoints(self) -> None:
        """Admin key should access all endpoints."""
        response = self.client.delete(
            f"/api/managers/{self.manager_id}",
            headers={"X-API-Key": self.admin_key},
        )
        self.assertEqual(response.status_code, 200)


class TestAPIPagination(unittest.TestCase):
    """Tests for API pagination."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            # Create country
            country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
            db.session.add(country)
            db.session.flush()
            self.country_id = country.id

            # Create 25 managers
            for i in range(25):
                manager = Manager(name=f"Manager {i:03d}", country_id=self.country_id)
                db.session.add(manager)
            db.session.commit()

            # Create API key
            self.api_key = generate_api_key()
            db.session.add(
                ApiKey(
                    key_hash=hash_api_key(self.api_key),
                    name="Pagination Test Key",
                    scope="admin",
                )
            )
            db.session.commit()

    def tearDown(self) -> None:
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_default_pagination(self) -> None:
        """Default pagination should return 20 items."""
        response = self.client.get(
            "/api/managers",
            headers={"X-API-Key": self.api_key},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("data", data)
        self.assertIn("pagination", data)
        self.assertEqual(len(data["data"]), 20)
        self.assertEqual(data["pagination"]["page"], 1)
        self.assertEqual(data["pagination"]["per_page"], 20)
        self.assertEqual(data["pagination"]["total"], 25)
        self.assertEqual(data["pagination"]["pages"], 2)
        self.assertTrue(data["pagination"]["has_next"])
        self.assertFalse(data["pagination"]["has_prev"])

    def test_custom_per_page(self) -> None:
        """Custom per_page should work."""
        response = self.client.get(
            "/api/managers?per_page=10",
            headers={"X-API-Key": self.api_key},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data["data"]), 10)
        self.assertEqual(data["pagination"]["per_page"], 10)

    def test_page_2(self) -> None:
        """Page 2 should return remaining items."""
        response = self.client.get(
            "/api/managers?page=2",
            headers={"X-API-Key": self.api_key},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data["data"]), 5)  # 25 - 20 = 5
        self.assertEqual(data["pagination"]["page"], 2)
        self.assertFalse(data["pagination"]["has_next"])
        self.assertTrue(data["pagination"]["has_prev"])

    def test_max_per_page_cap(self) -> None:
        """per_page should be capped at 100."""
        response = self.client.get(
            "/api/managers?per_page=200",
            headers={"X-API-Key": self.api_key},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["pagination"]["per_page"], 100)

    def test_countries_no_pagination(self) -> None:
        """Countries endpoint should NOT have pagination."""
        response = self.client.get(
            "/api/countries",
            headers={"X-API-Key": self.api_key},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        # Should be a list, not a dict with pagination
        self.assertIsInstance(data, list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
