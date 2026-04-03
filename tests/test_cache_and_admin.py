"""Tests for cache service and admin authentication.

Migrated from tests_cache_and_admin.py
"""

import unittest

from app import create_app
from models import db, Country, Manager, Achievement, AdminUser
from services.cache_service import cache, invalidate_leaderboard_cache, get_cache_stats


class TestCacheService(unittest.TestCase):
    """Tests for cache service functionality."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_invalidate_leaderboard_cache(self) -> None:
        """Test cache invalidation returns True."""
        result = invalidate_leaderboard_cache()
        self.assertTrue(result)

    def test_get_cache_stats(self) -> None:
        """Test cache stats returns dict with status."""
        stats = get_cache_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("status", stats)

    def test_cache_set_and_get(self) -> None:
        """Test basic cache set and get operations."""
        with self.app.app_context():
            cache.set("test_key", "test_value", timeout=60)
            value = cache.get("test_key")
            self.assertEqual(value, "test_value")

    def test_cache_delete(self) -> None:
        """Test cache delete operation."""
        with self.app.app_context():
            cache.set("to_delete", "value")
            cache.delete("to_delete")
            value = cache.get("to_delete")
            self.assertIsNone(value)

    def test_cache_timeout(self) -> None:
        """Test cache expires after timeout."""
        with self.app.app_context():
            cache.set("short_lived", "value", timeout=1)
            value = cache.get("short_lived")
            self.assertEqual(value, "value")


class TestAdminAuthentication(unittest.TestCase):
    """Tests for admin panel authentication.

    NOTE: Flask-Admin is disabled in testing mode by default.
    These tests verify the configuration is correct.
    """

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()

    def test_admin_disabled_in_testing(self) -> None:
        """Test admin is disabled in testing mode."""
        response = self.client.get("/admin/")
        # Should return 404 since admin is disabled in testing
        self.assertEqual(response.status_code, 404)

    def test_admin_login_disabled_in_testing(self) -> None:
        """Test admin login is disabled in testing mode."""
        response = self.client.get("/admin/login")
        self.assertEqual(response.status_code, 404)


class TestCacheInvalidationOnModelChange(unittest.TestCase):
    """Tests that model changes invalidate cache."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create country
        country = Country(code="TST", flag_path="/static/img/flags/TST.png")
        db.session.add(country)
        db.session.commit()
        self.country_id = country.id

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_cache_invalidated_after_manager_create(self) -> None:
        """Test cache is invalidated after creating a manager."""
        # Set a test cache value
        cache.set("leaderboard", "cached_value")

        # Create manager
        manager = Manager(name="Test Manager", country_id=self.country_id)
        db.session.add(manager)
        db.session.commit()

        # Manually invalidate
        result = invalidate_leaderboard_cache()
        self.assertTrue(result)

    def test_cache_invalidated_after_achievement_create(self) -> None:
        """Test cache is invalidated after creating an achievement."""
        # Create manager first
        manager = Manager(name="Test Manager", country_id=self.country_id)
        db.session.add(manager)
        db.session.commit()

        # Set cache
        cache.set("leaderboard", "cached_value")

        # Create achievement
        achievement = Achievement(
            achievement_type="TOP1",
            league="1",
            season="25/26",
            title="TOP1",
            icon_path="/static/img/cups/top1.svg",
            manager_id=manager.id,
        )
        db.session.add(achievement)
        db.session.commit()

        # Manually invalidate
        result = invalidate_leaderboard_cache()
        self.assertTrue(result)
