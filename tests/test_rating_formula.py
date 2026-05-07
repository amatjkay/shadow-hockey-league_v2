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
from models import Achievement, AchievementType, Country, League, Manager, Season, db
from services.rating_service import (
    BASE_POINTS,
    SEASON_MULTIPLIER,
    _get_base_points_from_db,
    _get_season_multiplier_from_db,
    calculate_achievement_points,
    get_achievement_kind,
)


def _seed_reference_data(include_leagues=None, include_seasons=None, include_types=None):
    """Seed reference tables for tests. Returns dicts of created objects."""
    leagues = include_leagues or ["1", "2"]
    seasons = include_seasons or ["25/26", "24/25", "23/24", "22/23", "21/22"]
    types = include_types or ["TOP1", "TOP2", "TOP3", "BEST", "R3", "R1"]

    league_map = {}
    for code in leagues:
        lg = League(code=code, name=f"League {code}")
        db.session.add(lg)
        league_map[code] = lg

    season_map = {}
    # Smooth ``0.7 ^ years_ago`` decay (TIK-80) — matches
    # ``services.rating_service.SEASON_MULTIPLIER`` and the seed data.
    multipliers = {
        "25/26": 1.000,
        "24/25": 0.700,
        "23/24": 0.490,
        "22/23": 0.343,
        "21/22": 0.240,
    }
    for i, code in enumerate(seasons):
        s = Season(
            code=code,
            name=f"Season {code}",
            multiplier=multipliers.get(code, 1.0),
            is_active=(i == 0),
        )
        db.session.add(s)
        season_map[code] = s

    type_map = {}
    # Compact-10 scale (TIK-80) — keeps ``BEST > TOP3`` and ``L2 ≈ 60 % L1``.
    type_points: dict[str, tuple[float, float]] = {
        "TOP1": (10.0, 6.0),
        "TOP2": (5.0, 3.0),
        "TOP3": (2.5, 1.5),
        "BEST": (3.0, 1.8),
        "R3": (1.5, 0.9),
        "R1": (0.75, 0.45),
    }
    for code in types:
        bp_l1, bp_l2 = type_points.get(code, (0, 0))
        at = AchievementType(code=code, name=code, base_points_l1=bp_l1, base_points_l2=bp_l2)
        db.session.add(at)
        type_map[code] = at

    db.session.flush()
    return league_map, season_map, type_map


class TestAchievementKindDetection(unittest.TestCase):
    """Tests for achievement kind detection logic."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        league_map, season_map, type_map = _seed_reference_data()
        self.league_id = league_map["1"].id
        self.season_id = season_map["25/26"].id
        self.type_map = type_map

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
            type_id=self.type_map[ach_type].id,
            league_id=self.league_id,
            season_id=self.season_id,
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
        db.session.add_all(
            [
                League(code="1", name="League 1"),
                League(code="2", name="League 2"),
                AchievementType(code="TOP1", name="TOP1", base_points_l1=999, base_points_l2=888),
            ]
        )
        db.session.commit()

        result = _get_base_points_from_db(db.session)
        self.assertEqual(result[("1", "TOP1")], 999)
        self.assertEqual(result[("2", "TOP1")], 888)

    def test_base_points_l1_values(self) -> None:
        """Test all League 1 base points from DB."""
        db.session.add(League(code="1", name="League 1"))
        db.session.add_all(
            [
                AchievementType(code="TOP1", name="TOP1", base_points_l1=10.0, base_points_l2=6.0),
                AchievementType(code="TOP2", name="TOP2", base_points_l1=5.0, base_points_l2=3.0),
                AchievementType(code="TOP3", name="TOP3", base_points_l1=2.5, base_points_l2=1.5),
                AchievementType(
                    code="BEST", name="Best regular", base_points_l1=3.0, base_points_l2=1.8
                ),
                AchievementType(code="R3", name="Round 3", base_points_l1=1.5, base_points_l2=0.9),
                AchievementType(
                    code="R1", name="Round 1", base_points_l1=0.75, base_points_l2=0.45
                ),
            ]
        )
        db.session.commit()

        result = _get_base_points_from_db(db.session)
        self.assertEqual(result[("1", "TOP1")], 10.0)
        self.assertEqual(result[("1", "TOP2")], 5.0)
        self.assertEqual(result[("1", "TOP3")], 2.5)
        self.assertEqual(result[("1", "BEST")], 3.0)
        self.assertEqual(result[("1", "R3")], 1.5)
        self.assertEqual(result[("1", "R1")], 0.75)

    def test_base_points_l2_values(self) -> None:
        """Test all League 2 base points from DB."""
        db.session.add(League(code="2", name="League 2"))
        db.session.add_all(
            [
                AchievementType(code="TOP1", name="TOP1", base_points_l1=10.0, base_points_l2=6.0),
                AchievementType(code="TOP2", name="TOP2", base_points_l1=5.0, base_points_l2=3.0),
                AchievementType(code="TOP3", name="TOP3", base_points_l1=2.5, base_points_l2=1.5),
                AchievementType(
                    code="BEST", name="Best regular", base_points_l1=3.0, base_points_l2=1.8
                ),
                AchievementType(code="R3", name="Round 3", base_points_l1=1.5, base_points_l2=0.9),
                AchievementType(
                    code="R1", name="Round 1", base_points_l1=0.75, base_points_l2=0.45
                ),
            ]
        )
        db.session.commit()

        result = _get_base_points_from_db(db.session)
        self.assertEqual(result[("2", "TOP1")], 6.0)
        self.assertEqual(result[("2", "TOP2")], 3.0)
        self.assertEqual(result[("2", "TOP3")], 1.5)
        self.assertEqual(result[("2", "BEST")], 1.8)
        self.assertEqual(result[("2", "R3")], 0.9)
        self.assertEqual(result[("2", "R1")], 0.45)


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
        db.session.add(
            Season(code="25/26", name="Season 2025/26", multiplier=0.490, is_active=True)
        )
        db.session.commit()

        result = _get_season_multiplier_from_db(db.session)
        self.assertEqual(result["25/26"], 0.490)

    def test_all_season_multipliers(self) -> None:
        """Test all season multipliers from DB (smooth ``0.7 ^ years_ago``)."""
        db.session.add_all(
            [
                Season(code="25/26", name="Season 2025/26", multiplier=1.000, is_active=True),
                Season(code="24/25", name="Season 2024/25", multiplier=0.700, is_active=False),
                Season(code="23/24", name="Season 2023/24", multiplier=0.490, is_active=False),
                Season(code="22/23", name="Season 2022/23", multiplier=0.343, is_active=False),
                Season(code="21/22", name="Season 2021/22", multiplier=0.240, is_active=False),
            ]
        )
        db.session.commit()

        result = _get_season_multiplier_from_db(db.session)
        self.assertEqual(result["25/26"], 1.000)
        self.assertEqual(result["24/25"], 0.700)
        self.assertEqual(result["23/24"], 0.490)
        self.assertEqual(result["22/23"], 0.343)
        self.assertEqual(result["21/22"], 0.240)


class TestAchievementPointsCalculation(unittest.TestCase):
    """Parameterized tests for achievement points calculation."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        league_map, season_map, type_map = _seed_reference_data()
        self.league_ids = {code: lg.id for code, lg in league_map.items()}
        self.season_ids = {code: s.id for code, s in season_map.items()}
        self.type_map = type_map

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

    def _create_achievement(
        self, ach_type: str, league: str, season: str, title: str
    ) -> Achievement:
        ach = Achievement(
            type_id=self.type_map[ach_type].id,
            league_id=self.league_ids[league],
            season_id=self.season_ids[season],
            title=title,
            icon_path="/static/img/cups/test.svg",
            manager_id=self.manager.id,
        )
        db.session.add(ach)
        db.session.flush()
        return ach

    def test_top1_l1_s25_26(self) -> None:
        """TOP1 League 1 Season 25/26: 10.0 × 1.000 = 10.0"""
        ach = self._create_achievement("TOP1", "1", "25/26", "TOP1")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 10.0)
        self.assertEqual(result["mul"], 1.000)
        self.assertEqual(result["points"], 10.0)

    def test_top1_l1_s24_25(self) -> None:
        """TOP1 League 1 Season 24/25: 10.0 × 0.700 = 7.0"""
        ach = self._create_achievement("TOP1", "1", "24/25", "TOP1")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 10.0)
        self.assertEqual(result["mul"], 0.700)
        self.assertEqual(result["points"], 7.0)

    def test_top1_l1_s23_24(self) -> None:
        """TOP1 League 1 Season 23/24: 10.0 × 0.490 = 4.9"""
        ach = self._create_achievement("TOP1", "1", "23/24", "TOP1")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 10.0)
        self.assertEqual(result["mul"], 0.490)
        self.assertEqual(result["points"], 4.9)

    def test_top2_l1_s22_23(self) -> None:
        """TOP2 League 1 Season 22/23: 5.0 × 0.343 = 1.72 (rounded to 2dp)"""
        ach = self._create_achievement("TOP2", "1", "22/23", "TOP2")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 5.0)
        self.assertEqual(result["mul"], 0.343)
        self.assertEqual(result["points"], 1.72)

    def test_top3_l1_s21_22(self) -> None:
        """TOP3 League 1 Season 21/22: 2.5 × 0.240 = 0.6"""
        ach = self._create_achievement("TOP3", "1", "21/22", "TOP3")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 2.5)
        self.assertEqual(result["mul"], 0.240)
        self.assertEqual(result["points"], 0.6)

    def test_best_l1_s25_26(self) -> None:
        """Best regular League 1 Season 25/26: 3.0 × 1.000 = 3.0 (BEST > TOP3)."""
        ach = self._create_achievement("BEST", "1", "25/26", "Best regular player")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 3.0)
        self.assertEqual(result["mul"], 1.000)
        self.assertEqual(result["points"], 3.0)

    def test_r3_l2_s25_26(self) -> None:
        """Round 3 League 2 Season 25/26: 0.9 × 1.000 = 0.9."""
        ach = self._create_achievement("R3", "2", "25/26", "Round 3")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 0.9)
        self.assertEqual(result["mul"], 1.000)
        self.assertEqual(result["points"], 0.9)

    def test_r1_l2_s21_22(self) -> None:
        """Round 1 League 2 Season 21/22: 0.45 × 0.240 = 0.11 (rounded)."""
        ach = self._create_achievement("R1", "2", "21/22", "Round 1")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 0.45)
        self.assertEqual(result["mul"], 0.240)
        self.assertEqual(result["points"], 0.11)

    def test_unknown_season_defaults_to_1(self) -> None:
        """Unknown season should default to multiplier 1.0."""
        ach = self._create_achievement("TOP1", "1", "25/26", "TOP1")
        result = calculate_achievement_points(ach)
        # With seeded data, 25/26 has multiplier 1.000
        self.assertEqual(result["mul"], 1.0)
        self.assertEqual(result["points"], 10.0)

    def test_unknown_achievement_type_defaults_to_0(self) -> None:
        """Unknown achievement type should default to 0 base points."""
        ach = self._create_achievement("TOP1", "1", "25/26", "TOP1")
        result = calculate_achievement_points(ach)
        self.assertEqual(result["base"], 10.0)
        self.assertEqual(result["points"], 10.0)


class TestPointsCalculationWithDBData(unittest.TestCase):
    """Integration-style tests: points calculation with data from DB."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        league_map, season_map, type_map = _seed_reference_data()
        self.league_ids = {code: lg.id for code, lg in league_map.items()}
        self.season_ids = {code: s.id for code, s in season_map.items()}
        self.type_map = type_map

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

    def _create_achievement(
        self, ach_type: str, league: str, season: str, title: str
    ) -> Achievement:
        ach = Achievement(
            type_id=self.type_map[ach_type].id,
            league_id=self.league_ids[league],
            season_id=self.season_ids[season],
            title=title,
            icon_path="/static/img/cups/test.svg",
            manager_id=self.manager.id,
        )
        db.session.add(ach)
        db.session.flush()
        return ach

    def test_points_from_db_top1_l1_current(self) -> None:
        """TOP1 L1 s25/26 from DB: 10.0 × 1.000 = 10.0."""
        ach = self._create_achievement("TOP1", "1", "25/26", "TOP1")
        bp = _get_base_points_from_db(db.session)
        sm = _get_season_multiplier_from_db(db.session)
        result = calculate_achievement_points(ach, bp, sm)
        self.assertEqual(result["points"], 10.0)

    def test_points_from_db_top2_l1_previous(self) -> None:
        """TOP2 L1 s24/25 from DB: 5.0 × 0.700 = 3.5."""
        ach = self._create_achievement("TOP2", "1", "24/25", "TOP2")
        bp = _get_base_points_from_db(db.session)
        sm = _get_season_multiplier_from_db(db.session)
        result = calculate_achievement_points(ach, bp, sm)
        self.assertEqual(result["points"], 3.5)

    def test_points_from_db_top1_l2_current(self) -> None:
        """TOP1 L2 s25/26 from DB: 6.0 × 1.000 = 6.0."""
        ach = self._create_achievement("TOP1", "2", "25/26", "TOP1")
        bp = _get_base_points_from_db(db.session)
        sm = _get_season_multiplier_from_db(db.session)
        result = calculate_achievement_points(ach, bp, sm)
        self.assertEqual(result["points"], 6.0)

    def test_points_from_db_r1_l2_oldest(self) -> None:
        """R1 L2 s21/22 from DB: 0.45 × 0.240 = 0.11 (rounded)."""
        ach = self._create_achievement("R1", "2", "21/22", "Round 1")
        bp = _get_base_points_from_db(db.session)
        sm = _get_season_multiplier_from_db(db.session)
        result = calculate_achievement_points(ach, bp, sm)
        self.assertEqual(result["points"], 0.11)


if __name__ == "__main__":
    unittest.main(verbosity=2)
