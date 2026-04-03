"""Parameterized tests for rating calculation formula.

Tests verify that:
1. Base points are read from DB (AchievementType table)
2. Season multipliers are read from DB (Season table)
3. Fallback to hardcoded values if reference tables are empty
4. All league/achievement_type combinations produce correct points
5. All season multipliers produce correct results
"""

import unittest

from app import create_app
from models import Achievement, Country, Manager, AchievementType, League, Season, db
from services.rating_service import (
    BASE_POINTS,
    SEASON_MULTIPLIER,
    calculate_achievement_points,
    get_achievement_kind,
    _get_base_points_from_db,
    _get_season_multiplier_from_db,
)


class TestAchievementKindDetection(unittest.TestCase):
    """Tests for achievement kind detection logic."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
        db.session.add(self.country)
        db.session.flush()

        self.manager = Manager(name="Test Manager", country_id=self.country.id)
        db.session.add(self.manager)
        db.session.flush()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_achievement(self, ach_type: str, title: str) -> Achievement:
        ach = Achievement(
            achievement_type=ach_type,
            league="1",
            season="25/26",
            title=title,
            icon_path="/static/img/cups/test.svg",
            manager_id=self.manager.id,
        )
        db.session.add(ach)
        db.session.flush()
        return ach

    def test_top1_kind(self) -> None:
        ach = self._create_achievement("TOP1", "TOP1")
        self.assertEqual(get_achievement_kind(ach), "TOP1")

    def test_top2_kind(self) -> None:
        ach = self._create_achievement("TOP2", "TOP2")
        self.assertEqual(get_achievement_kind(ach), "TOP2")

    def test_top3_kind(self) -> None:
        ach = self._create_achievement("TOP3", "TOP3")
        self.assertEqual(get_achievement_kind(ach), "TOP3")

    def test_best_kind_by_title(self) -> None:
        ach = self._create_achievement("BEST", "Best regular player")
        self.assertEqual(get_achievement_kind(ach), "BEST")

    def test_r3_kind_by_title(self) -> None:
        ach = self._create_achievement("R3", "Round 3")
        self.assertEqual(get_achievement_kind(ach), "R3")

    def test_r1_kind_by_title(self) -> None:
        ach = self._create_achievement("R1", "Round 1")
        self.assertEqual(get_achievement_kind(ach), "R1")


class TestBasePointsFromDB(unittest.TestCase):
    """Tests for reading base points from database."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_fallback_to_hardcoded_when_tables_empty(self) -> None:
        """When reference tables are empty, should fallback to hardcoded."""
        result = _get_base_points_from_db(db.session)
        self.assertEqual(result, BASE_POINTS)

    def test_read_from_db_when_tables_populated(self) -> None:
        """When reference tables have data, should read from DB."""
        # Seed reference tables
        db.session.add_all([
            League(code="1", name="League 1"),
            League(code="2", name="League 2"),
            AchievementType(code="TOP1", name="TOP1", base_points_l1=999, base_points_l2=888),
        ])
        db.session.commit()

        result = _get_base_points_from_db(db.session)
        self.assertEqual(result[("1", "TOP1")], 999)
        self.assertEqual(result[("2", "TOP1")], 888)

    def test_base_points_l1_values(self) -> None:
        """Test all League 1 base points from DB."""
        db.session.add(League(code="1", name="League 1"))
        db.session.add_all([
            AchievementType(code="TOP1", name="TOP1", base_points_l1=800, base_points_l2=300),
            AchievementType(code="TOP2", name="TOP2", base_points_l1=550, base_points_l2=200),
            AchievementType(code="TOP3", name="TOP3", base_points_l1=450, base_points_l2=100),
            AchievementType(code="BEST", name="Best regular", base_points_l1=50, base_points_l2=40),
            AchievementType(code="R3", name="Round 3", base_points_l1=30, base_points_l2=20),
            AchievementType(code="R1", name="Round 1", base_points_l1=10, base_points_l2=5),
        ])
        db.session.commit()

        result = _get_base_points_from_db(db.session)
        self.assertEqual(result[("1", "TOP1")], 800)
        self.assertEqual(result[("1", "TOP2")], 550)
        self.assertEqual(result[("1", "TOP3")], 450)
        self.assertEqual(result[("1", "BEST")], 50)
        self.assertEqual(result[("1", "R3")], 30)
        self.assertEqual(result[("1", "R1")], 10)

    def test_base_points_l2_values(self) -> None:
        """Test all League 2 base points from DB."""
        db.session.add(League(code="2", name="League 2"))
        db.session.add_all([
            AchievementType(code="TOP1", name="TOP1", base_points_l1=800, base_points_l2=300),
            AchievementType(code="TOP2", name="TOP2", base_points_l1=550, base_points_l2=200),
            AchievementType(code="TOP3", name="TOP3", base_points_l1=450, base_points_l2=100),
            AchievementType(code="BEST", name="Best regular", base_points_l1=50, base_points_l2=40),
            AchievementType(code="R3", name="Round 3", base_points_l1=30, base_points_l2=20),
            AchievementType(code="R1", name="Round 1", base_points_l1=10, base_points_l2=5),
        ])
        db.session.commit()

        result = _get_base_points_from_db(db.session)
        self.assertEqual(result[("2", "TOP1")], 300)
        self.assertEqual(result[("2", "TOP2")], 200)
        self.assertEqual(result[("2", "TOP3")], 100)
        self.assertEqual(result[("2", "BEST")], 40)
        self.assertEqual(result[("2", "R3")], 20)
        self.assertEqual(result[("2", "R1")], 5)


class TestSeasonMultiplierFromDB(unittest.TestCase):
    """Tests for reading season multipliers from database."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_fallback_to_hardcoded_when_table_empty(self) -> None:
        """When Season table is empty, should fallback to hardcoded."""
        result = _get_season_multiplier_from_db(db.session)
        self.assertEqual(result, SEASON_MULTIPLIER)

    def test_read_from_db_when_table_populated(self) -> None:
        """When Season table has data, should read from DB."""
        db.session.add(Season(code="25/26", name="Season 2025/26", multiplier=0.50, is_active=True))
        db.session.commit()

        result = _get_season_multiplier_from_db(db.session)
        self.assertEqual(result["25/26"], 0.50)

    def test_all_season_multipliers(self) -> None:
        """Test all season multipliers from DB."""
        db.session.add_all([
            Season(code="25/26", name="Season 2025/26", multiplier=1.00, is_active=True),
            Season(code="24/25", name="Season 2024/25", multiplier=0.95, is_active=False),
            Season(code="23/24", name="Season 2023/24", multiplier=0.90, is_active=False),
            Season(code="22/23", name="Season 2022/23", multiplier=0.85, is_active=False),
            Season(code="21/22", name="Season 2021/22", multiplier=0.80, is_active=False),
        ])
        db.session.commit()

        result = _get_season_multiplier_from_db(db.session)
        self.assertEqual(result["25/26"], 1.00)
        self.assertEqual(result["24/25"], 0.95)
        self.assertEqual(result["23/24"], 0.90)
        self.assertEqual(result["22/23"], 0.85)
        self.assertEqual(result["21/22"], 0.80)


class TestAchievementPointsCalculation(unittest.TestCase):
    """Parameterized tests for achievement points calculation."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
        db.session.add(self.country)
        db.session.flush()

        self.manager = Manager(name="Test Manager", country_id=self.country.id)
        db.session.add(self.manager)
        db.session.flush()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_achievement(self, ach_type: str, league: str, season: str, title: str) -> Achievement:
        ach = Achievement(
            achievement_type=ach_type,
            league=league,
            season=season,
            title=title,
            icon_path="/static/img/cups/test.svg",
            manager_id=self.manager.id,
        )
        db.session.add(ach)
        db.session.flush()
        return ach

    def test_top1_l1_s25_26(self) -> None:
        """TOP1 League 1 Season 25/26: 800 × 1.00 = 800"""
        ach = self._create_achievement("TOP1", "1", "25/26", "TOP1")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 800)
        self.assertEqual(result["mul"], 1.00)
        self.assertEqual(result["points"], 800)

    def test_top1_l1_s24_25(self) -> None:
        """TOP1 League 1 Season 24/25: 800 × 0.95 = 760"""
        ach = self._create_achievement("TOP1", "1", "24/25", "TOP1")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 800)
        self.assertEqual(result["mul"], 0.95)
        self.assertEqual(result["points"], 760)

    def test_top1_l1_s23_24(self) -> None:
        """TOP1 League 1 Season 23/24: 800 × 0.90 = 720"""
        ach = self._create_achievement("TOP1", "1", "23/24", "TOP1")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 800)
        self.assertEqual(result["mul"], 0.90)
        self.assertEqual(result["points"], 720)

    def test_top2_l1_s22_23(self) -> None:
        """TOP2 League 1 Season 22/23: 550 × 0.85 = 467.5 → 468 (banker's rounding)"""
        ach = self._create_achievement("TOP2", "1", "22/23", "TOP2")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 550)
        self.assertEqual(result["mul"], 0.85)
        self.assertEqual(result["points"], 468)

    def test_top3_l1_s21_22(self) -> None:
        """TOP3 League 1 Season 21/22: 450 × 0.80 = 360"""
        ach = self._create_achievement("TOP3", "1", "21/22", "TOP3")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 450)
        self.assertEqual(result["mul"], 0.80)
        self.assertEqual(result["points"], 360)

    def test_best_l1_s25_26(self) -> None:
        """Best regular League 1 Season 25/26: 50 × 1.00 = 50"""
        ach = self._create_achievement("BEST", "1", "25/26", "Best regular player")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 50)
        self.assertEqual(result["mul"], 1.00)
        self.assertEqual(result["points"], 50)

    def test_r3_l2_s25_26(self) -> None:
        """Round 3 League 2 Season 25/26: 20 × 1.00 = 20"""
        ach = self._create_achievement("R3", "2", "25/26", "Round 3")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 20)
        self.assertEqual(result["mul"], 1.00)
        self.assertEqual(result["points"], 20)

    def test_r1_l2_s21_22(self) -> None:
        """Round 1 League 2 Season 21/22: 5 × 0.80 = 4"""
        ach = self._create_achievement("R1", "2", "21/22", "Round 1")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 5)
        self.assertEqual(result["mul"], 0.80)
        self.assertEqual(result["points"], 4)

    def test_unknown_season_defaults_to_1(self) -> None:
        """Unknown season should default to multiplier 1.0."""
        ach = self._create_achievement("TOP1", "1", "99/00", "TOP1")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["mul"], 1.0)
        self.assertEqual(result["points"], 800)

    def test_unknown_achievement_type_defaults_to_0(self) -> None:
        """Unknown achievement type should default to 0 base points."""
        ach = self._create_achievement("UNKNOWN", "1", "25/26", "Unknown")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 0)
        self.assertEqual(result["points"], 0)


class TestPointsCalculationWithDBData(unittest.TestCase):
    """Integration-style tests: points calculation with data from DB."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed reference tables
        db.session.add_all([
            League(code="1", name="League 1"),
            League(code="2", name="League 2"),
            AchievementType(code="TOP1", name="TOP1", base_points_l1=800, base_points_l2=300),
            AchievementType(code="TOP2", name="TOP2", base_points_l1=550, base_points_l2=200),
            AchievementType(code="TOP3", name="TOP3", base_points_l1=450, base_points_l2=100),
            AchievementType(code="BEST", name="Best regular", base_points_l1=50, base_points_l2=40),
            AchievementType(code="R3", name="Round 3", base_points_l1=30, base_points_l2=20),
            AchievementType(code="R1", name="Round 1", base_points_l1=10, base_points_l2=5),
            Season(code="25/26", name="Season 2025/26", multiplier=1.00, is_active=True),
            Season(code="24/25", name="Season 2024/25", multiplier=0.95, is_active=False),
            Season(code="23/24", name="Season 2023/24", multiplier=0.90, is_active=False),
            Season(code="22/23", name="Season 2022/23", multiplier=0.85, is_active=False),
            Season(code="21/22", name="Season 2021/22", multiplier=0.80, is_active=False),
        ])
        db.session.commit()

        self.country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
        db.session.add(self.country)
        db.session.flush()

        self.manager = Manager(name="Test Manager", country_id=self.country.id)
        db.session.add(self.manager)
        db.session.flush()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_achievement(self, ach_type: str, league: str, season: str, title: str) -> Achievement:
        ach = Achievement(
            achievement_type=ach_type,
            league=league,
            season=season,
            title=title,
            icon_path="/static/img/cups/test.svg",
            manager_id=self.manager.id,
        )
        db.session.add(ach)
        db.session.flush()
        return ach

    def test_points_from_db_top1_l1_current(self) -> None:
        """TOP1 L1 s25/26 from DB: 800 × 1.00 = 800"""
        ach = self._create_achievement("TOP1", "1", "25/26", "TOP1")
        bp = _get_base_points_from_db(db.session)
        sm = _get_season_multiplier_from_db(db.session)
        result = calculate_achievement_points(ach, bp, sm)
        self.assertEqual(result["points"], 800)

    def test_points_from_db_top2_l1_previous(self) -> None:
        """TOP2 L1 s24/25 from DB: 550 × 0.95 = 522.5 → 522"""
        ach = self._create_achievement("TOP2", "1", "24/25", "TOP2")
        bp = _get_base_points_from_db(db.session)
        sm = _get_season_multiplier_from_db(db.session)
        result = calculate_achievement_points(ach, bp, sm)
        self.assertEqual(result["points"], 522)

    def test_points_from_db_top1_l2_current(self) -> None:
        """TOP1 L2 s25/26 from DB: 300 × 1.00 = 300"""
        ach = self._create_achievement("TOP1", "2", "25/26", "TOP1")
        bp = _get_base_points_from_db(db.session)
        sm = _get_season_multiplier_from_db(db.session)
        result = calculate_achievement_points(ach, bp, sm)
        self.assertEqual(result["points"], 300)

    def test_points_from_db_r1_l2_oldest(self) -> None:
        """R1 L2 s21/22 from DB: 5 × 0.80 = 4"""
        ach = self._create_achievement("R1", "2", "21/22", "Round 1")
        bp = _get_base_points_from_db(db.session)
        sm = _get_season_multiplier_from_db(db.session)
        result = calculate_achievement_points(ach, bp, sm)
        self.assertEqual(result["points"], 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
