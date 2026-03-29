"""Tests for Shadow Hockey League application.

Includes unit tests for rating calculation, integration tests for Flask routes,
and data validation tests.
"""

import unittest

from app import create_app
from data.managers_data import Manager, countries, managers
from data.rating import (
    BASE_POINTS,
    SEASON_MULTIPLIER,
    build_leaderboard,
    parse_achievement_html,
)


class TestAppRoutes(unittest.TestCase):
    """Integration tests for Flask routes."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()

    def test_home_page(self) -> None:
        """Test that home page renders successfully."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Рейтинг лиги", html)
        self.assertIn("Кубки", html)

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

    def test_static_files_accessible(self) -> None:
        """Test that static files are accessible."""
        static_files = [
            "/static/img/logo.png",
            "/static/css/style.css",
            "/static/img/cups/top1.svg",
        ]
        for file_path in static_files:
            response = self.client.get(file_path)
            self.assertIn(
                response.status_code, [200, 304], f"Static file {file_path} not accessible"
            )


class TestManagersData(unittest.TestCase):
    """Tests for managers data structure."""

    def test_managers_exist(self) -> None:
        """Test that managers list is not empty."""
        self.assertTrue(len(managers) > 0, "Managers list should not be empty")

    def test_countries_exist(self) -> None:
        """Test that countries list is not empty."""
        self.assertTrue(len(countries) > 0, "Countries list should not be empty")

    def test_manager_structure(self) -> None:
        """Test that each manager has required attributes."""
        for manager in managers:
            self.assertIsInstance(manager, Manager)
            self.assertTrue(hasattr(manager, "name"))
            self.assertTrue(hasattr(manager, "country"))
            self.assertTrue(hasattr(manager, "achievements"))
            self.assertIsInstance(manager.achievements, list)

    def test_manager_names_not_empty(self) -> None:
        """Test that all managers have non-empty names."""
        for manager in managers:
            self.assertTrue(
                len(manager.name.strip()) > 0, f"Manager name should not be empty: {manager}"
            )


class TestRatingCalculation(unittest.TestCase):
    """Tests for rating calculation logic."""

    def test_build_leaderboard_returns_list(self) -> None:
        """Test that build_leaderboard returns a list."""
        result = build_leaderboard()
        self.assertIsInstance(result, list)

    def test_leaderboard_has_required_fields(self) -> None:
        """Test that each leaderboard entry has required fields."""
        result = build_leaderboard()
        required_fields = ["name", "country", "total", "achievements", "rank"]

        for entry in result:
            for field in required_fields:
                self.assertIn(field, entry, f"Missing field: {field}")

    def test_leaderboard_sorted_by_total(self) -> None:
        """Test that leaderboard is sorted by total points descending."""
        result = build_leaderboard()
        totals = [entry["total"] for entry in result]
        self.assertEqual(totals, sorted(totals, reverse=True))

    def test_rank_assignment(self) -> None:
        """Test that ranks are assigned correctly."""
        result = build_leaderboard()

        prev_total = None
        expected_rank = 0

        for i, entry in enumerate(result, start=1):
            if entry["total"] != prev_total:
                expected_rank = i
            self.assertEqual(entry["rank"], expected_rank, f"Rank mismatch for {entry['name']}")
            prev_total = entry["total"]

    def test_parse_achievement_top1_season_23_24(self) -> None:
        """Test parsing TOP1 achievement from season 23/24."""
        html = '<img src="/static/img/cups/top1.svg" title="Shadow 1 league TOP1 s23/24">'
        result = parse_achievement_html(html)

        self.assertIsNotNone(result)
        self.assertEqual(result["base"], 600)
        self.assertEqual(result["mul"], 1.15)
        self.assertEqual(result["points"], 690)  # 600 * 1.15
        self.assertEqual(result["league"], "1")
        self.assertEqual(result["kind"], "TOP1")

    def test_parse_achievement_top2_season_21_22(self) -> None:
        """Test parsing TOP2 achievement from season 21/22."""
        html = '<img src="/static/img/cups/top2.svg" title="Shadow 1 league TOP2 s21/22">'
        result = parse_achievement_html(html)

        self.assertIsNotNone(result)
        self.assertEqual(result["base"], 500)
        self.assertEqual(result["mul"], 0.85)
        self.assertEqual(result["points"], 425)  # 500 * 0.85

    def test_parse_achievement_league_2(self) -> None:
        """Test parsing league 2 achievements."""
        html = '<img src="/static/img/cups/top1.svg" title="Shadow 2 league TOP1 s22/23">'
        result = parse_achievement_html(html)

        self.assertIsNotNone(result)
        self.assertEqual(result["base"], 300)
        self.assertEqual(result["mul"], 1.00)
        self.assertEqual(result["points"], 300)
        self.assertEqual(result["league"], "2")

    def test_parse_best_regular(self) -> None:
        """Test parsing Best Regular achievement."""
        html = (
            '<img src="/static/img/cups/best-reg.svg" '
            'title="Shadow 1 league Best regular player s23/24">'
        )
        result = parse_achievement_html(html)

        self.assertIsNotNone(result)
        self.assertEqual(result["base"], 50)
        self.assertEqual(result["kind"], "BEST")

    def test_parse_round_achievements(self) -> None:
        """Test parsing Round achievements."""
        html_r3 = '<img src="/static/img/cups/clap-b.svg" title="Shadow 1 league Round 3 s23/24">'
        html_r1 = '<img src="/static/img/cups/clap.svg" title="Shadow 1 league Round 1 s23/24">'

        result_r3 = parse_achievement_html(html_r3)
        result_r1 = parse_achievement_html(html_r1)

        self.assertIsNotNone(result_r3)
        self.assertEqual(result_r3["kind"], "R3")
        self.assertEqual(result_r3["base"], 30)

        self.assertIsNotNone(result_r1)
        self.assertEqual(result_r1["kind"], "R1")
        self.assertEqual(result_r1["base"], 10)

    def test_parse_toxic_achievement(self) -> None:
        """Test parsing toxic achievement (zero points)."""
        html = '<img src="/static/img/cups/toxic.png" title="toxic and unpleasant person">'
        result = parse_achievement_html(html)

        self.assertIsNotNone(result)
        self.assertEqual(result["points"], 0)
        self.assertEqual(result["kind"], "toxic")

    def test_parse_invalid_html(self) -> None:
        """Test parsing invalid HTML returns None."""
        html = '<img src="invalid.svg" title="Invalid achievement">'
        result = parse_achievement_html(html)
        self.assertIsNone(result)

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

    def test_season_multipliers(self) -> None:
        """Test that season multipliers are defined."""
        expected_seasons = ["23/24", "22/23", "21/22"]
        for season in expected_seasons:
            self.assertIn(season, SEASON_MULTIPLIER, f"Missing multiplier for season {season}")


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
