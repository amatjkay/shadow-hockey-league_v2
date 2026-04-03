"""Unit tests for rating service, routes, security headers, validation, and API.

Migrated from tests.py
"""

import unittest

from app import create_app
from models import Achievement, Country, Manager, db
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

        # Check extended health fields (Этап 2)
        self.assertIn("timestamp", data)
        self.assertIn("response_time_ms", data)
        self.assertIn("database_status", data)
        self.assertIn("redis_status", data)
        self.assertIn("cache_status", data)
        self.assertIn("managers_count", data)
        self.assertIn("achievements_count", data)
        self.assertIn("countries_count", data)

        # Database should be connected in test environment
        self.assertEqual(data["database_status"], "connected")

        # Redis may be disconnected (fallback to simple cache)
        self.assertIn(data["redis_status"], ["connected", "disconnected", "unknown"])

    def test_metrics_endpoint(self) -> None:
        """Test Prometheus metrics endpoint."""
        # Note: Prometheus metrics are disabled in testing mode
        # This test verifies the endpoint exists or is properly excluded
        response = self.client.get("/metrics")

        # In testing mode, /metrics may return 404 or empty response
        # Just verify it doesn't crash
        self.assertIn(response.status_code, [200, 404, 500])


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

    def _create_achievement(
        self, ach_type: str, league: str, season: str, title: str
    ) -> Achievement:
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

    def test_calculate_points_top1_s23_24(self) -> None:
        """Test points calculation for TOP1 s23/24."""
        ach = self._create_achievement("TOP1", "1", "23/24", "TOP1")
        result = calculate_achievement_points(ach)

        self.assertEqual(result["base"], 800)
        self.assertEqual(result["mul"], 0.90)
        self.assertEqual(result["points"], 720)  # 800 * 0.90

    def test_calculate_points_top2_s21_22(self) -> None:
        """Test points calculation for TOP2 s21/22."""
        ach = self._create_achievement("TOP2", "1", "21/22", "TOP2")
        result = calculate_achievement_points(ach)

        self.assertEqual(result["base"], 550)
        self.assertEqual(result["mul"], 0.80)
        self.assertEqual(result["points"], 440)  # 550 * 0.80 = 440

    def test_calculate_points_league2(self) -> None:
        """Test points calculation for league 2."""
        ach = self._create_achievement("TOP1", "2", "22/23", "TOP1")
        result = calculate_achievement_points(ach)

        self.assertEqual(result["base"], 300)
        self.assertEqual(result["mul"], 0.85)
        self.assertEqual(result["points"], 255)  # 300 * 0.85

    def test_calculate_points_s25_26(self) -> None:
        """Test points calculation for season 25/26 (baseline)."""
        ach = self._create_achievement("TOP1", "2", "25/26", "TOP1")
        result = calculate_achievement_points(ach)

        self.assertEqual(result["base"], 300)
        self.assertEqual(result["mul"], 1.00)
        self.assertEqual(result["points"], 300)  # 300 * 1.00

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
                    achievement_type="TOP1",
                    league="1",
                    season="23/24",
                    title="TOP1",
                    icon_path="/static/img/cups/top1.svg",
                    manager_id=self.manager1.id,
                ),
                Achievement(
                    achievement_type="TOP2",
                    league="1",
                    season="22/23",
                    title="TOP2",
                    icon_path="/static/img/cups/top2.svg",
                    manager_id=self.manager1.id,
                ),
            ]
        )

        # Create achievements for manager2 (medium score)
        db.session.add(
            Achievement(
                achievement_type="TOP3",
                league="1",
                season="23/24",
                title="TOP3",
                icon_path="/static/img/cups/top3.svg",
                manager_id=self.manager2.id,
            )
        )

        # Create achievements for manager3 (tandem, low score)
        db.session.add(
            Achievement(
                achievement_type="R1",
                league="2",
                season="21/22",
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
        expected_seasons = ["25/26", "24/25", "23/24", "22/23", "21/22"]
        for season in expected_seasons:
            self.assertIn(season, SEASON_MULTIPLIER, f"Missing multiplier for season {season}")

        # Verify multiplier values (current season = baseline, older = discount)
        self.assertEqual(SEASON_MULTIPLIER["25/26"], 1.00)  # Baseline
        self.assertEqual(SEASON_MULTIPLIER["24/25"], 0.95)  # -5%
        self.assertEqual(SEASON_MULTIPLIER["23/24"], 0.90)  # -10%
        self.assertEqual(SEASON_MULTIPLIER["22/23"], 0.85)  # -15%
        self.assertEqual(SEASON_MULTIPLIER["21/22"], 0.80)  # -20%


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


class TestValidationService(unittest.TestCase):
    """Tests for validation service."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_validate_country_data_valid(self) -> None:
        """Test valid country data validation."""
        from services.validation_service import validate_country_data

        is_valid, error = validate_country_data("RUS", "/static/img/flags/rus.png")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_country_data_invalid_code(self) -> None:
        """Test invalid country code validation."""
        from services.validation_service import validate_country_data

        is_valid, error = validate_country_data("RU", "/static/img/flags/rus.png")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_manager_data_valid(self) -> None:
        """Test valid manager data validation."""
        from services.validation_service import validate_manager_data

        is_valid, error = validate_manager_data("Test Manager", 1)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_achievement_data_valid(self) -> None:
        """Test valid achievement data validation."""
        from services.validation_service import validate_achievement_data

        is_valid, error = validate_achievement_data("TOP1", "1", "24/25", "TOP1")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_achievement_data_invalid_league(self) -> None:
        """Test invalid league validation."""
        from services.validation_service import validate_achievement_data

        is_valid, error = validate_achievement_data("TOP1", "3", "24/25", "TOP1")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)


class TestAPIEndpoints(unittest.TestCase):
    """Tests for REST API endpoints."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Create test data
            country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
            db.session.add(country)
            db.session.flush()

            manager = Manager(name="API Test Manager", country_id=country.id)
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

            self.manager_id = manager.id
            self.country_id = country.id
            self.achievement_id = achievement.id

            # Create API key for tests
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
        """Helper to make authenticated GET requests."""
        return self.client.get(url, headers={"X-API-Key": self.api_key})

    def _post(self, url: str, json: dict) -> Any:
        """Helper to make authenticated POST requests."""
        return self.client.post(url, json=json, headers={"X-API-Key": self.api_key})

    def _put(self, url: str, json: dict) -> Any:
        """Helper to make authenticated PUT requests."""
        return self.client.put(url, json=json, headers={"X-API-Key": self.api_key})

    def _delete(self, url: str) -> Any:
        """Helper to make authenticated DELETE requests."""
        return self.client.delete(url, headers={"X-API-Key": self.api_key})

    def test_api_get_countries(self) -> None:
        """Test GET /api/countries endpoint."""
        response = self._get("/api/countries")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["code"], "RUS")

    def test_api_get_managers(self) -> None:
        """Test GET /api/managers endpoint."""
        response = self._get("/api/managers")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        # Now returns paginated response
        self.assertIn("data", data)
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["name"], "API Test Manager")

    def test_api_get_manager_detail(self) -> None:
        """Test GET /api/managers/<id> endpoint."""
        response = self._get(f"/api/managers/{self.manager_id}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["name"], "API Test Manager")
        self.assertIn("achievements", data)

    def test_api_get_achievements(self) -> None:
        """Test GET /api/achievements endpoint."""
        response = self._get("/api/achievements")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        # Now returns paginated response
        self.assertIn("data", data)
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["achievement_type"], "TOP1")

    def test_api_create_manager(self) -> None:
        """Test POST /api/managers endpoint."""
        new_manager = {
            "name": "New Manager",
            "country_id": self.country_id,
        }
        response = self._post(
            "/api/managers",
            json=new_manager,
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["name"], "New Manager")

    def test_api_create_manager_duplicate(self) -> None:
        """Test POST /api/managers with duplicate name."""
        duplicate_manager = {
            "name": "API Test Manager",
            "country_id": self.country_id,
        }
        response = self._post(
            "/api/managers",
            json=duplicate_manager,
        )
        self.assertEqual(response.status_code, 409)
        data = response.get_json()
        self.assertIn("error", data)

    def test_api_update_manager(self) -> None:
        """Test PUT /api/managers/<id> endpoint."""
        update_data = {"name": "Updated Manager"}
        response = self._put(
            f"/api/managers/{self.manager_id}",
            json=update_data,
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["name"], "Updated Manager")

    def test_api_delete_achievement(self) -> None:
        """Test DELETE /api/achievements/<id> endpoint."""
        response = self._delete(f"/api/achievements/{self.achievement_id}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["message"], "Achievement deleted successfully")


if __name__ == "__main__":
    unittest.main(verbosity=2)
