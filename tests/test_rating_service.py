"""Unit tests for rating service helpers and calculation logic.

Migrated from tests.py and trimmed in TIK-48: route/security/validation/API
tests previously co-located here are now covered exclusively by
tests/test_blueprints.py, tests/test_validation.py, tests/test_api.py, and
tests/integration/test_api_extended.py.
"""

import unittest
from typing import Any

from app import create_app
from models import Achievement, AchievementType, Country, League, Manager, Season, db
from services.rating_service import (
    BASE_POINTS,
    SEASON_MULTIPLIER,
    build_leaderboard,
    calculate_achievement_points,
    get_achievement_kind,
)


def _seed_reference_data():
    """Seed reference tables. Returns (league_ids, season_ids, type_map)."""
    leagues = {}
    for code in ["1", "2"]:
        lg = League(code=code, name=f"League {code}")
        db.session.add(lg)
        leagues[code] = lg

    seasons = {}
    multipliers = {"25/26": 1.0, "24/25": 0.8, "23/24": 0.5, "22/23": 0.3, "21/22": 0.2}
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


class TestRatingServiceHelpers(unittest.TestCase):
    """Tests for rating service helper functions."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        league_ids, season_ids, type_map = _seed_reference_data()
        self.league_ids = league_ids
        self.season_ids = season_ids
        self.type_map = type_map

        # Create test country and manager
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
        """Helper to create test achievement."""
        ach = Achievement(
            type_id=self.type_map[ach_type].id,
            league_id=self.league_ids[league],
            season_id=self.season_ids[season],
            title=title,
            icon_path=f"/static/img/cups/{ach_type.lower()}.svg",
            manager_id=self.manager.id,
        )
        db.session.add(ach)
        db.session.flush()
        return ach

    def test_get_achievement_kind_top(self) -> None:
        """Test kind extraction for TOP achievements."""
        for top_type in ["TOP1", "TOP2", "TOP3"]:
            ach = self._create_achievement(top_type, "1", "23/24", top_type)
            self.assertEqual(get_achievement_kind(ach), top_type)

    def test_get_achievement_kind_best(self) -> None:
        """Test kind extraction for Best regular."""
        ach = self._create_achievement("BEST", "1", "23/24", "Best regular player")
        self.assertEqual(get_achievement_kind(ach), "BEST")

    def test_get_achievement_kind_round3(self) -> None:
        """Test kind extraction for Round 3."""
        ach = self._create_achievement("R3", "1", "23/24", "Round 3")
        self.assertEqual(get_achievement_kind(ach), "R3")

    def test_get_achievement_kind_round1(self) -> None:
        """Test kind extraction for Round 1."""
        ach = self._create_achievement("R1", "1", "23/24", "Round 1")
        self.assertEqual(get_achievement_kind(ach), "R1")

    def test_calculate_points_top1_s23_24(self) -> None:
        """Test points calculation for TOP1 s23/24."""
        ach = self._create_achievement("TOP1", "1", "23/24", "TOP1")
        result = calculate_achievement_points(ach)

        self.assertEqual(result["base"], 800)
        self.assertEqual(result["mul"], 0.5)
        self.assertEqual(result["points"], 400)  # 800 * 0.5

    def test_calculate_points_top2_s21_22(self) -> None:
        """Test points calculation for TOP2 s21/22."""
        ach = self._create_achievement("TOP2", "1", "21/22", "TOP2")
        result = calculate_achievement_points(ach)

        self.assertEqual(result["base"], 400)
        self.assertEqual(result["mul"], 0.2)
        self.assertEqual(result["points"], 80)  # 400 * 0.2

    def test_calculate_points_league2(self) -> None:
        """Test points calculation for league 2."""
        ach = self._create_achievement("TOP1", "2", "22/23", "TOP1")
        result = calculate_achievement_points(ach)

        self.assertEqual(result["base"], 400)
        self.assertEqual(result["mul"], 0.3)
        self.assertEqual(result["points"], 120)  # 400 * 0.3

    def test_calculate_points_s25_26(self) -> None:
        """Test points calculation for season 25/26 (baseline)."""
        ach = self._create_achievement("TOP1", "2", "25/26", "TOP1")
        result = calculate_achievement_points(ach)

        self.assertEqual(result["base"], 400)
        self.assertEqual(result["mul"], 1.00)
        self.assertEqual(result["points"], 400)  # 400 * 1.00

    def test_season_multiplier_s25_26_exists(self) -> None:
        """Test that season 25/26 multiplier is defined as baseline."""
        self.assertIn("25/26", SEASON_MULTIPLIER)
        self.assertEqual(SEASON_MULTIPLIER["25/26"], 1.00)


class TestRatingCalculation(unittest.TestCase):
    """Tests for rating calculation logic with database."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self._seed_test_data()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _seed_test_data(self) -> None:
        """Seed database with test data."""
        league_ids, season_ids, type_map = _seed_reference_data()
        self.season_ids = season_ids

        # Create countries
        self.country_rus = Country(code="RUS", flag_path="/static/img/flags/rus.png")
        self.country_bel = Country(code="BEL", flag_path="/static/img/flags/bel.png")
        db.session.add_all([self.country_rus, self.country_bel])
        db.session.flush()

        # Create managers
        self.manager1 = Manager(name="Manager One", country_id=self.country_rus.id)
        self.manager2 = Manager(name="Manager Two", country_id=self.country_bel.id)
        self.manager3 = Manager(name="Tandem: A, B", country_id=self.country_rus.id)
        db.session.add_all([self.manager1, self.manager2, self.manager3])
        db.session.flush()

        # Create achievements for manager1 (high score)
        db.session.add_all(
            [
                Achievement(
                    type_id=type_map["TOP1"].id,
                    league_id=league_ids["1"],
                    season_id=season_ids["23/24"],
                    title="TOP1",
                    icon_path="/static/img/cups/top1.svg",
                    manager_id=self.manager1.id,
                ),
                Achievement(
                    type_id=type_map["TOP2"].id,
                    league_id=league_ids["1"],
                    season_id=season_ids["22/23"],
                    title="TOP2",
                    icon_path="/static/img/cups/top2.svg",
                    manager_id=self.manager1.id,
                ),
            ]
        )

        # Create achievements for manager2 (medium score)
        db.session.add(
            Achievement(
                type_id=type_map["TOP3"].id,
                league_id=league_ids["1"],
                season_id=season_ids["23/24"],
                title="TOP3",
                icon_path="/static/img/cups/top3.svg",
                manager_id=self.manager2.id,
            )
        )

        # Create achievements for manager3 (tandem, low score)
        db.session.add(
            Achievement(
                type_id=type_map["R1"].id,
                league_id=league_ids["2"],
                season_id=season_ids["21/22"],
                title="Round 1",
                icon_path="/static/img/cups/r1.svg",
                manager_id=self.manager3.id,
            )
        )

        db.session.commit()

    def test_build_leaderboard_returns_list(self) -> None:
        """Test that build_leaderboard returns a list."""
        result = build_leaderboard(db.session)
        self.assertIsInstance(result, list)

    def test_leaderboard_has_required_fields(self) -> None:
        """Test that each leaderboard entry has required fields."""
        result = build_leaderboard(db.session)
        required_fields = [
            "id",
            "name",
            "display_name",
            "is_tandem",
            "country",
            "total",
            "achievements",
            "rank",
        ]

        for entry in result:
            for field in required_fields:
                self.assertIn(field, entry, f"Missing field: {field}")

    def test_leaderboard_sorted_by_total(self) -> None:
        """Test that leaderboard is sorted by total points descending."""
        result = build_leaderboard(db.session)
        totals = [entry["total"] for entry in result]
        self.assertEqual(totals, sorted(totals, reverse=True))

    def test_rank_assignment(self) -> None:
        """Test that ranks are assigned correctly."""
        result = build_leaderboard(db.session)

        prev_total = None
        expected_rank = 0

        for i, entry in enumerate(result, start=1):
            if entry["total"] != prev_total:
                expected_rank = i
            self.assertEqual(entry["rank"], expected_rank, f"Rank mismatch for {entry['name']}")
            prev_total = entry["total"]

    def test_tandem_detection(self) -> None:
        """Test that tandem managers are detected correctly."""
        result = build_leaderboard(db.session)

        tandem_entry = next(e for e in result if e["name"] == "Tandem: A, B")
        self.assertTrue(tandem_entry["is_tandem"])
        self.assertEqual(tandem_entry["display_name"], "A, B")

        non_tandem_entry = next(e for e in result if e["name"] == "Manager One")
        self.assertFalse(non_tandem_entry["is_tandem"])
        self.assertEqual(non_tandem_entry["display_name"], "Manager One")

    # ---- season filter (B6) ----------------------------------------
    #
    # Seed reminder:
    #   manager1: TOP1 / L1 / 23-24  +  TOP2 / L1 / 22-23
    #   manager2: TOP3 / L1 / 23-24
    #   manager3: R1   / L2 / 21-22
    #
    # build_leaderboard(season_id=N) must return all three managers but
    # only count achievements tied to season N. Managers with no
    # qualifying achievement keep total=0 so the dropdown does not
    # silently hide active rows.

    def test_season_filter_keeps_managers_with_zero_total(self) -> None:
        """Selecting a season returns every manager — those without a
        matching achievement get total=0 and an empty achievements
        list, instead of vanishing from the page."""
        season_2425 = self.season_ids["24/25"]  # nobody has achievements here
        result = build_leaderboard(db.session, season_id=season_2425)

        names = {row["name"] for row in result}
        self.assertEqual(names, {"Manager One", "Manager Two", "Tandem: A, B"})

        for row in result:
            self.assertEqual(
                row["total"],
                0,
                f"{row['name']!r} should have total=0 for an empty season",
            )
            self.assertEqual(
                row["achievements"],
                [],
                f"{row['name']!r} should have no achievements for an empty season",
            )

    def test_season_filter_isolates_single_season(self) -> None:
        """?season=23/24 — only manager1 (TOP1) and manager2 (TOP3)
        contribute; manager1's TOP2 (22/23) is filtered out, manager3
        is present but with total=0."""
        season_2324 = self.season_ids["23/24"]
        result = build_leaderboard(db.session, season_id=season_2324)

        m1 = next(r for r in result if r["name"] == "Manager One")
        m2 = next(r for r in result if r["name"] == "Manager Two")
        m3 = next(r for r in result if r["name"] == "Tandem: A, B")

        # manager1: only TOP1/L1/23-24 contributes — TOP2/22-23 is
        # filtered out.
        self.assertEqual(len(m1["achievements"]), 1)
        self.assertEqual(m1["achievements"][0]["kind"], "TOP1")

        # manager2: TOP3/L1/23-24 is the only achievement and it does
        # belong to 23/24, so it stays.
        self.assertEqual(len(m2["achievements"]), 1)
        self.assertEqual(m2["achievements"][0]["kind"], "TOP3")

        # manager3 has nothing in 23/24.
        self.assertEqual(m3["total"], 0)
        self.assertEqual(m3["achievements"], [])

    def test_season_filter_changes_totals_vs_lifetime(self) -> None:
        """Lifetime total for manager1 ≠ single-season totals — proves
        the filter is doing real work, not a no-op."""
        lifetime = build_leaderboard(db.session)
        s23 = build_leaderboard(db.session, season_id=self.season_ids["23/24"])
        s22 = build_leaderboard(db.session, season_id=self.season_ids["22/23"])

        m1_lifetime = next(r for r in lifetime if r["name"] == "Manager One")["total"]
        m1_s23 = next(r for r in s23 if r["name"] == "Manager One")["total"]
        m1_s22 = next(r for r in s22 if r["name"] == "Manager One")["total"]

        # Lifetime is the sum of the per-season slices for this manager
        # because every achievement belongs to exactly one season.
        self.assertEqual(m1_lifetime, m1_s23 + m1_s22)
        # And each per-season slice is strictly less than lifetime
        # (manager1 has multi-season achievements).
        self.assertLess(m1_s23, m1_lifetime)
        self.assertLess(m1_s22, m1_lifetime)

    def test_season_filter_none_equals_lifetime(self) -> None:
        """season_id=None must be identical to omitting the argument."""
        a = build_leaderboard(db.session)
        b = build_leaderboard(db.session, season_id=None)
        self.assertEqual(
            [(r["name"], r["total"]) for r in a],
            [(r["name"], r["total"]) for r in b],
        )

    def test_base_points_coverage(self) -> None:
        """Test that BASE_POINTS covers all expected combinations."""
        expected_combinations = [
            ("1", "TOP1"),
            ("1", "TOP2"),
            ("1", "TOP3"),
            ("2", "TOP1"),
            ("2", "TOP2"),
            ("2", "TOP3"),
            ("1", "BEST"),
            ("2", "BEST"),
            ("1", "R3"),
            ("2", "R3"),
            ("1", "R1"),
            ("2", "R1"),
        ]
        for combo in expected_combinations:
            self.assertIn(combo, BASE_POINTS, f"Missing base points for {combo}")

    def test_base_points_values(self) -> None:
        """Test that base points have correct values (updated system)."""
        # League 1 - increased values for TOP achievements
        self.assertEqual(BASE_POINTS[("1", "TOP1")], 800)
        self.assertEqual(BASE_POINTS[("1", "TOP2")], 400)
        self.assertEqual(BASE_POINTS[("1", "TOP3")], 200)
        self.assertEqual(BASE_POINTS[("1", "BEST")], 200)
        self.assertEqual(BASE_POINTS[("1", "R3")], 100)
        self.assertEqual(BASE_POINTS[("1", "R1")], 50)

        # League 2
        self.assertEqual(BASE_POINTS[("2", "TOP1")], 400)
        self.assertEqual(BASE_POINTS[("2", "TOP2")], 200)
        self.assertEqual(BASE_POINTS[("2", "TOP3")], 100)
        self.assertEqual(BASE_POINTS[("2", "BEST")], 100)
        self.assertEqual(BASE_POINTS[("2", "R3")], 50)
        self.assertEqual(BASE_POINTS[("2", "R1")], 25)

    def test_season_multipliers(self) -> None:
        """Test that season multipliers are defined with correct values."""
        expected_seasons = ["25/26", "24/25", "23/24", "22/23", "21/22"]
        for season in expected_seasons:
            self.assertIn(season, SEASON_MULTIPLIER, f"Missing multiplier for season {season}")

        # Verify multiplier values (current season = baseline, older = discount)
        self.assertEqual(SEASON_MULTIPLIER["25/26"], 1.0)  # Baseline
        self.assertEqual(SEASON_MULTIPLIER["24/25"], 0.8)  # -20%
        self.assertEqual(SEASON_MULTIPLIER["23/24"], 0.5)  # -50%
        self.assertEqual(SEASON_MULTIPLIER["22/23"], 0.3)  # -70%
        self.assertEqual(SEASON_MULTIPLIER["21/22"], 0.2)  # -80%
