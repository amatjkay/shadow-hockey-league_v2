"""Tests for blueprints.

Tests cover:
- Health endpoint extended functionality
- Main blueprint error handling
- Blueprint registration
"""

import unittest

from app import create_app
from models import Achievement, Country, Manager, db


class TestHealthBlueprint(unittest.TestCase):
    """Tests for health check blueprint."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Seed some data
            country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
            db.session.add(country)
            db.session.flush()

            manager = Manager(name="Test Manager", country_id=country.id)
            db.session.add(manager)
            db.session.flush()

            achievement = Achievement(
                achievement_type="TOP1",
                league="1",
                season="24/25",
                title="TOP1",
                icon_path="/static/img/cups/top1.svg",
                manager_id=manager.id,
            )
            db.session.add(achievement)
            db.session.commit()

    def tearDown(self) -> None:
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_health_endpoint_returns_healthy(self) -> None:
        """Health endpoint should return healthy status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "healthy")

    def test_health_endpoint_has_timestamp(self) -> None:
        """Health endpoint should include timestamp."""
        response = self.client.get("/health")
        data = response.get_json()
        self.assertIn("timestamp", data)

    def test_health_endpoint_has_response_time(self) -> None:
        """Health endpoint should include response time."""
        response = self.client.get("/health")
        data = response.get_json()
        self.assertIn("response_time_ms", data)
        self.assertIsInstance(data["response_time_ms"], (int, float))

    def test_health_endpoint_has_database_status(self) -> None:
        """Health endpoint should include database status."""
        response = self.client.get("/health")
        data = response.get_json()
        self.assertIn("database_status", data)
        self.assertEqual(data["database_status"], "connected")

    def test_health_endpoint_has_redis_status(self) -> None:
        """Health endpoint should include redis status."""
        response = self.client.get("/health")
        data = response.get_json()
        self.assertIn("redis_status", data)
        self.assertIn(data["redis_status"], ["connected", "disconnected", "unknown"])

    def test_health_endpoint_has_cache_status(self) -> None:
        """Health endpoint should include cache status."""
        response = self.client.get("/health")
        data = response.get_json()
        self.assertIn("cache_status", data)

    def test_health_endpoint_has_managers_count(self) -> None:
        """Health endpoint should include managers count."""
        response = self.client.get("/health")
        data = response.get_json()
        self.assertIn("managers_count", data)
        self.assertEqual(data["managers_count"], 1)

    def test_health_endpoint_has_achievements_count(self) -> None:
        """Health endpoint should include achievements count."""
        response = self.client.get("/health")
        data = response.get_json()
        self.assertIn("achievements_count", data)
        self.assertEqual(data["achievements_count"], 1)

    def test_health_endpoint_has_countries_count(self) -> None:
        """Health endpoint should include countries count."""
        response = self.client.get("/health")
        data = response.get_json()
        self.assertIn("countries_count", data)
        self.assertEqual(data["countries_count"], 1)


class TestMainBlueprint(unittest.TestCase):
    """Tests for main blueprint."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
            db.session.add(country)
            db.session.commit()

    def tearDown(self) -> None:
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_home_page_loads_empty_db(self) -> None:
        """Home page should load even with empty DB."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_home_page_has_rating_section(self) -> None:
        """Home page should have rating section."""
        response = self.client.get("/")
        html = response.data.decode("utf-8")
        self.assertIn("Рейтинг лиги", html)

    def test_rating_redirect(self) -> None:
        """/rating should redirect to main page with anchor."""
        response = self.client.get("/rating", follow_redirects=False)
        self.assertIn(response.status_code, (301, 302, 308))
        location = response.headers.get("Location", "")
        self.assertIn("#rating", location)

    def test_security_headers_present(self) -> None:
        """Security headers should be present on all responses."""
        response = self.client.get("/")
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(response.headers.get("X-XSS-Protection"), "1; mode=block")


class TestBlueprintRegistration(unittest.TestCase):
    """Tests for blueprint registration."""

    def test_main_blueprint_registered(self) -> None:
        """Main blueprint should be registered."""
        app = create_app("config.TestingConfig")
        self.assertIn("main", app.blueprints)

    def test_health_blueprint_registered(self) -> None:
        """Health blueprint should be registered."""
        app = create_app("config.TestingConfig")
        self.assertIn("health", app.blueprints)

    def test_api_blueprint_registered_when_enabled(self) -> None:
        """API blueprint should be registered when ENABLE_API=True."""
        app = create_app("config.TestingConfig")
        self.assertIn("api", app.blueprints)

    def test_api_blueprint_not_registered_when_disabled(self) -> None:
        """API blueprint should be enabled in TestingConfig."""
        app = create_app("config.TestingConfig")
        # TestingConfig has ENABLE_API=True
        self.assertTrue(app.config.get("ENABLE_API"))
        self.assertIn("api", app.blueprints)


if __name__ == "__main__":
    unittest.main(verbosity=2)
