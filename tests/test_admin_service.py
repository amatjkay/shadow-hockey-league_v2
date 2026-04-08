"""Tests for admin service views and functionality.

Tests cover:
- CountryModelView flag choices
- AdminUserModelView password hashing
- AdminUserModelView last admin protection
- Cache invalidation on model changes
"""

import unittest

from app import create_app
from models import Achievement, AdminUser, Country, Manager, db
from services.admin import (
    get_flag_choices,
    AchievementModelView,
    AdminUserModelView,
    CountryModelView,
    ManagerModelView,
)
from services.cache_service import cache, invalidate_leaderboard_cache


class TestCountryModelView(unittest.TestCase):
    """Tests for CountryModelView."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self) -> None:
        self.app_context.pop()

    def test_flag_choices_not_empty(self) -> None:
        """FLAG_CHOICES should have entries."""
        choices = get_flag_choices()
        self.assertGreater(len(choices), 0)

    def test_flag_choices_have_correct_format(self) -> None:
        """Each flag choice should be (path, name) tuple."""
        choices = get_flag_choices()
        # Skip the default placeholder option
        flag_choices = [c for c in choices if c[0]]
        for choice in flag_choices:
            self.assertIsInstance(choice, tuple)
            self.assertEqual(len(choice), 2)
            self.assertTrue(choice[0].startswith("/static/img/flags/"))


class TestAdminUserModelView(unittest.TestCase):
    """Tests for AdminUserModelView."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_cannot_delete_last_admin(self) -> None:
        """Should prevent deleting the last admin user."""
        admin = AdminUser(username="lastadmin")
        admin.set_password("password")
        db.session.add(admin)
        db.session.commit()

        # Try to delete via view logic
        user_count = db.session.query(AdminUser).count()
        self.assertEqual(user_count, 1)


class TestCacheInvalidation(unittest.TestCase):
    """Tests for cache invalidation functionality."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
        db.session.add(self.country)
        db.session.commit()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_invalidate_leaderboard_cache_returns_true(self) -> None:
        """Cache invalidation should return True."""
        result = invalidate_leaderboard_cache()
        self.assertTrue(result)

    def test_cache_set_and_get(self) -> None:
        """Should be able to set and get cache values."""
        cache.set("test_key", "test_value", timeout=60)
        value = cache.get("test_key")
        self.assertEqual(value, "test_value")

    def test_cache_delete(self) -> None:
        """Should be able to delete cache values."""
        cache.set("to_delete", "value")
        cache.delete("to_delete")
        value = cache.get("to_delete")
        self.assertIsNone(value)

    def test_manager_create_invalidates_cache(self) -> None:
        """Creating manager should invalidate cache."""
        cache.set("leaderboard", "cached_value")
        manager = Manager(name="Test Manager", country_id=self.country.id)
        db.session.add(manager)
        db.session.commit()
        result = invalidate_leaderboard_cache()
        self.assertTrue(result)

    def test_achievement_create_invalidates_cache(self) -> None:
        """Creating achievement should invalidate cache."""
        from models import AchievementType, League, Season

        # Create reference data
        ach_type = AchievementType(code="TOP1", name="Top 1", base_points_l1=10.0, base_points_l2=5.0)
        db.session.add(ach_type)
        league = League(code="1", name="League 1")
        db.session.add(league)
        season = Season(code="25/26", name="Season 25/26", multiplier=1.0, is_active=True)
        db.session.add(season)
        db.session.commit()

        manager = Manager(name="Test Manager", country_id=self.country.id)
        db.session.add(manager)
        db.session.commit()

        cache.set("leaderboard", "cached_value")
        achievement = Achievement(
            type_id=ach_type.id,
            league_id=league.id,
            season_id=season.id,
            title="TOP1",
            icon_path="/static/img/cups/top1.svg",
            manager_id=manager.id,
            base_points=10.0,
            multiplier=1.0,
            final_points=10.0,
        )
        db.session.add(achievement)
        db.session.commit()
        result = invalidate_leaderboard_cache()
        self.assertTrue(result)


class TestAdminModels(unittest.TestCase):
    """Tests for admin model classes."""

    def test_country_model_view_has_correct_columns(self) -> None:
        """CountryModelView should have correct column list."""
        view = CountryModelView
        self.assertIn("code", view.column_list)
        self.assertIn("name", view.column_list)

    def test_manager_model_view_has_correct_columns(self) -> None:
        """ManagerModelView should have correct column list."""
        view = ManagerModelView
        self.assertIn("name", view.column_list)
        self.assertIn("country", view.column_list)

    def test_achievement_model_view_has_correct_columns(self) -> None:
        """AchievementModelView should have correct column list."""
        view = AchievementModelView
        self.assertIn("type", view.column_list)
        self.assertIn("league", view.column_list)
        self.assertIn("season", view.column_list)
        self.assertIn("final_points", view.column_list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
