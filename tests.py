"""Tests for Shadow Hockey League application.

Includes unit tests for rating service, integration tests for Flask routes,
and data validation tests.
"""

import unittest

from app import create_app
from models import db, Manager, Achievement, Country
from services.rating_service import (
    BASE_POINTS,
    SEASON_MULTIPLIER,
    build_leaderboard,
    calculate_achievement_points,
    get_achievement_kind,
)


class TestAppRoutes(unittest.TestCase):
    """Integration tests for Flask routes."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()
        
        # Create tables and seed test data
        with self.app.app_context():
            db.create_all()
            self._seed_test_data()

    def tearDown(self) -> None:
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _seed_test_data(self) -> None:
        """Seed database with test data."""
        # Create country
        country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
        db.session.add(country)
        db.session.flush()
        
        # Create manager with achievements
        manager = Manager(name="Test Manager", country_id=country.id)
        db.session.add(manager)
        db.session.flush()
        
        # Create achievements
        achievements = [
            Achievement(
                achievement_type="TOP1",
                league="1",
                season="23/24",
                title="TOP1",
                icon_path="/static/img/cups/top1.svg",
                manager_id=manager.id,
            ),
            Achievement(
                achievement_type="TOP2",
                league="1",
                season="21/22",
                title="TOP2",
                icon_path="/static/img/cups/top2.svg",
                manager_id=manager.id,
            ),
        ]
        for ach in achievements:
            db.session.add(ach)
        
        db.session.commit()

    def test_home_page(self) -> None:
        """Test that home page renders successfully."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Рейтинг лиги", html)

    def test_rating_redirects_to_main(self) -> None:
        """Test that /rating redirects to main page with anchor."""
        response = self.client.get("/rating", follow_redirects=False)
        self.assertIn(response.status_code, (301, 302, 308))
        location = response.headers.get("Location", "")
        self.assertIn("#rating", location)

    def test_health_endpoint(self) -> None:
        """Test health check endpoint."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "healthy")


class TestRatingServiceHelpers(unittest.TestCase):
    """Tests for rating service helper functions."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
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

    def _create_achievement(self, ach_type: str, league: str, season: str, title: str) -> Achievement:
        """Helper to create test achievement."""
        ach = Achievement(
            achievement_type=ach_type,
            league=league,
            season=season,
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

    def test_get_achievement_kind_toxic(self) -> None:
        """Test kind extraction for TOXIC."""
        ach = self._create_achievement("TOXIC", "1", "N/A", "Toxic")
        self.assertEqual(get_achievement_kind(ach), "TOXIC")

    def test_calculate_points_top1_s23_24(self) -> None:
        """Test points calculation for TOP1 s23/24."""
        ach = self._create_achievement("TOP1", "1", "23/24", "TOP1")
        result = calculate_achievement_points(ach)

        self.assertEqual(result["base"], 800)
        self.assertEqual(result["mul"], 0.95)
        self.assertEqual(result["points"], 760)  # 800 * 0.95

    def test_calculate_points_top2_s21_22(self) -> None:
        """Test points calculation for TOP2 s21/22."""
        ach = self._create_achievement("TOP2", "1", "21/22", "TOP2")
        result = calculate_achievement_points(ach)

        self.assertEqual(result["base"], 550)
        self.assertEqual(result["mul"], 0.85)
        self.assertEqual(result["points"], 468)  # 550 * 0.85 = 467.5 → 468

    def test_calculate_points_league2(self) -> None:
        """Test points calculation for league 2."""
        ach = self._create_achievement("TOP1", "2", "22/23", "TOP1")
        result = calculate_achievement_points(ach)

        self.assertEqual(result["base"], 300)
        self.assertEqual(result["mul"], 0.90)
        self.assertEqual(result["points"], 270)  # 300 * 0.90

    def test_calculate_points_toxic(self) -> None:
        """Test points calculation for TOXIC (zero points)."""
        ach = self._create_achievement("TOXIC", "1", "N/A", "Toxic")
        result = calculate_achievement_points(ach)

        self.assertEqual(result["points"], 0)

    def test_calculate_points_s24_25(self) -> None:
        """Test points calculation for season 24/25 (baseline)."""
        ach = self._create_achievement("TOP1", "2", "24/25", "TOP1")
        result = calculate_achievement_points(ach)

        self.assertEqual(result["base"], 300)
        self.assertEqual(result["mul"], 1.00)
        self.assertEqual(result["points"], 300)  # 300 * 1.00

    def test_season_multiplier_s24_25_exists(self) -> None:
        """Test that season 24/25 multiplier is defined as baseline."""
        self.assertIn("24/25", SEASON_MULTIPLIER)
        self.assertEqual(SEASON_MULTIPLIER["24/25"], 1.00)


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
        db.session.add_all([
            Achievement(
                achievement_type="TOP1", league="1", season="23/24",
                title="TOP1", icon_path="/static/img/cups/top1.svg",
                manager_id=self.manager1.id,
            ),
            Achievement(
                achievement_type="TOP2", league="1", season="22/23",
                title="TOP2", icon_path="/static/img/cups/top2.svg",
                manager_id=self.manager1.id,
            ),
        ])
        
        # Create achievements for manager2 (medium score)
        db.session.add(Achievement(
            achievement_type="TOP3", league="1", season="23/24",
            title="TOP3", icon_path="/static/img/cups/top3.svg",
            manager_id=self.manager2.id,
        ))
        
        # Create achievements for manager3 (tandem, low score)
        db.session.add(Achievement(
            achievement_type="R1", league="2", season="21/22",
            title="Round 1", icon_path="/static/img/cups/r1.svg",
            manager_id=self.manager3.id,
        ))
        
        db.session.commit()

    def test_build_leaderboard_returns_list(self) -> None:
        """Test that build_leaderboard returns a list."""
        result = build_leaderboard(db.session)
        self.assertIsInstance(result, list)

    def test_leaderboard_has_required_fields(self) -> None:
        """Test that each leaderboard entry has required fields."""
        result = build_leaderboard(db.session)
        required_fields = ["id", "name", "display_name", "is_tandem", "country", "total", "achievements", "rank"]

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

    def test_base_points_coverage(self) -> None:
        """Test that BASE_POINTS covers all expected combinations."""
        expected_combinations = [
            ("1", "TOP1"), ("1", "TOP2"), ("1", "TOP3"),
            ("2", "TOP1"), ("2", "TOP2"), ("2", "TOP3"),
            ("1", "BEST"), ("2", "BEST"),
            ("1", "R3"), ("2", "R3"),
            ("1", "R1"), ("2", "R1"),
        ]
        for combo in expected_combinations:
            self.assertIn(combo, BASE_POINTS, f"Missing base points for {combo}")

    def test_base_points_values(self) -> None:
        """Test that base points have correct values (updated system)."""
        # League 1 - increased values for TOP achievements
        self.assertEqual(BASE_POINTS[("1", "TOP1")], 800)
        self.assertEqual(BASE_POINTS[("1", "TOP2")], 550)
        self.assertEqual(BASE_POINTS[("1", "TOP3")], 450)
        self.assertEqual(BASE_POINTS[("1", "BEST")], 50)
        self.assertEqual(BASE_POINTS[("1", "R3")], 30)
        self.assertEqual(BASE_POINTS[("1", "R1")], 10)
        
        # League 2
        self.assertEqual(BASE_POINTS[("2", "TOP1")], 300)
        self.assertEqual(BASE_POINTS[("2", "TOP2")], 200)
        self.assertEqual(BASE_POINTS[("2", "TOP3")], 100)
        self.assertEqual(BASE_POINTS[("2", "BEST")], 40)
        self.assertEqual(BASE_POINTS[("2", "R3")], 20)
        self.assertEqual(BASE_POINTS[("2", "R1")], 5)

    def test_season_multipliers(self) -> None:
        """Test that season multipliers are defined with correct values."""
        expected_seasons = ["24/25", "23/24", "22/23", "21/22"]
        for season in expected_seasons:
            self.assertIn(season, SEASON_MULTIPLIER, f"Missing multiplier for season {season}")
        
        # Verify multiplier values (current season = baseline, older = discount)
        self.assertEqual(SEASON_MULTIPLIER["24/25"], 1.00)  # Baseline
        self.assertEqual(SEASON_MULTIPLIER["23/24"], 0.95)  # -5%
        self.assertEqual(SEASON_MULTIPLIER["22/23"], 0.90)  # -10%
        self.assertEqual(SEASON_MULTIPLIER["21/22"], 0.85)  # -15%


class TestSecurityHeaders(unittest.TestCase):
    """Tests for security headers."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()

    def test_x_content_type_options(self) -> None:
        """Test X-Content-Type-Options header."""
        response = self.client.get("/")
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")

    def test_x_frame_options(self) -> None:
        """Test X-Frame-Options header."""
        response = self.client.get("/")
        self.assertEqual(response.headers.get("X-Frame-Options"), "SAMEORIGIN")

    def test_x_xss_protection(self) -> None:
        """Test X-XSS-Protection header."""
        response = self.client.get("/")
        self.assertEqual(response.headers.get("X-XSS-Protection"), "1; mode=block")


if __name__ == "__main__":
    unittest.main(verbosity=2)
