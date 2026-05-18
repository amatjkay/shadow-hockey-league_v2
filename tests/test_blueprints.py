"""Tests for blueprints.

Tests cover:
- Health endpoint extended functionality
- Main blueprint error handling
- Blueprint registration
"""

import unittest
from unittest.mock import MagicMock, patch

from app import create_app
from models import Achievement, AchievementType, Country, League, Manager, Season, db


def _seed_reference_data():
    """Seed reference tables. Returns (league_ids, season_ids, type_map)."""
    leagues = {}
    for code in ["1", "2"]:
        lg = League(code=code, name=f"League {code}")
        db.session.add(lg)
        leagues[code] = lg

    seasons = {}
    # Smooth ``0.7 ^ years_ago`` decay (TIK-80) — matches the seed data and
    # ``services.rating_service.SEASON_MULTIPLIER``.
    multipliers = {"25/26": 1.000, "24/25": 0.700, "23/24": 0.490, "22/23": 0.343, "21/22": 0.240}
    for i, code in enumerate(["25/26", "24/25", "23/24", "22/23", "21/22"]):
        s = Season(
            code=code, name=f"Season {code}", multiplier=multipliers[code], is_active=(i == 0)
        )
        db.session.add(s)
        seasons[code] = s

    # Compact-10 scale (TIK-80) — keeps ``BEST > TOP3`` and ``L2 ≈ 60 % L1``.
    type_points: dict[str, tuple[float, float]] = {
        "TOP1": (10.0, 6.0),
        "TOP2": (5.0, 3.0),
        "TOP3": (2.5, 1.5),
        "BEST": (3.0, 1.8),
        "R3": (1.5, 0.9),
        "R1": (0.75, 0.45),
    }
    types = {}
    for code, (bp_l1, bp_l2) in type_points.items():
        at = AchievementType(code=code, name=code, base_points_l1=bp_l1, base_points_l2=bp_l2)
        db.session.add(at)
        types[code] = at

    db.session.flush()
    return {c: lg.id for c, lg in leagues.items()}, {c: s.id for c, s in seasons.items()}, types


class TestHealthBlueprint(unittest.TestCase):
    """Tests for health check blueprint."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            league_ids, season_ids, type_map = _seed_reference_data()

            # Seed some data
            country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
            db.session.add(country)
            db.session.flush()

            manager = Manager(name="Test Manager", country_id=country.id)
            db.session.add(manager)
            db.session.flush()

            achievement = Achievement(
                type_id=type_map["TOP1"].id,
                league_id=league_ids["1"],
                season_id=season_ids["24/25"],
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

    def test_health_endpoint_redis_client_uses_socket_timeout(self) -> None:
        """Regression for B10/TIK-37: redis.Redis() must receive socket_timeout.

        Without socket_timeout the read on .ping()/.info() can block on a
        hung Redis until the system default (~5-7s), making /health unable
        to fail-fast under degraded conditions.
        """
        fake_client = MagicMock()
        fake_client.ping.return_value = True
        fake_client.info.return_value = {"used_memory": 0}
        fake_client.set.return_value = True
        fake_client.get.return_value = "ok"

        with patch("redis.Redis", return_value=fake_client) as mock_redis:
            response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_redis.called)
        kwargs = mock_redis.call_args.kwargs
        self.assertIn(
            "socket_timeout",
            kwargs,
            "redis.Redis(...) must pass socket_timeout to bound read operations",
        )
        self.assertIsNotNone(kwargs["socket_timeout"])
        self.assertLessEqual(
            kwargs["socket_timeout"],
            2.0,
            "socket_timeout should be small (≤2s) so /health fails fast",
        )
        self.assertIn("socket_connect_timeout", kwargs)

    def test_health_endpoint_redis_disconnected_falls_back(self) -> None:
        """When `redis.Redis(...)` raises `ConnectionError`, /health must report
        ``redis_status=disconnected`` and ``cache_status=fallback`` instead of 5xx.

        Targets the previously uncovered Redis-error branch in
        ``blueprints/health.py:100-103``.
        """
        import redis as _redis

        fake_client = MagicMock()
        fake_client.ping.side_effect = _redis.ConnectionError("simulated outage")

        with patch("redis.Redis", return_value=fake_client):
            response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["redis_status"], "disconnected")
        self.assertEqual(data["cache_status"], "fallback")
        self.assertIn("cache_type", data)

    def test_health_endpoint_cache_roundtrip_mismatch_marks_degraded(self) -> None:
        """When `cache.set/get` returns the wrong value, status must degrade.

        Targets the previously uncovered cache-error branch in
        ``blueprints/health.py:97-99``.
        """
        fake_client = MagicMock()
        fake_client.ping.return_value = True
        fake_client.info.return_value = {"used_memory": 0}

        # Force `cache.get("_health_check")` to return None instead of "ok".
        with (
            patch("redis.Redis", return_value=fake_client),
            patch("blueprints.health.cache") as fake_cache,
        ):
            fake_cache.set.return_value = True
            fake_cache.get.return_value = None
            response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["cache_status"], "error")
        self.assertEqual(data["status"], "degraded")

    def test_health_endpoint_has_cache_backend_fields(self) -> None:
        """TIK-100: /health exposes cache backend identity on both code paths.

        ``cache_backend_type``, ``cache_type_config`` and ``cache_key_prefix``
        must be present and JSON-serializable strings regardless of whether
        the Redis probe succeeds (healthy path) or raises (fallback path).
        Concrete values are env-dependent and intentionally not asserted.
        """
        # Healthy path — Redis probe succeeds.
        fake_client = MagicMock()
        fake_client.ping.return_value = True
        fake_client.info.return_value = {"used_memory": 0}
        fake_client.set.return_value = True
        fake_client.get.return_value = "ok"
        with patch("redis.Redis", return_value=fake_client):
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        for field in ("cache_backend_type", "cache_type_config", "cache_key_prefix"):
            self.assertIn(field, data)
            self.assertIsInstance(data[field], str)

        # Fallback path — Redis probe raises.
        import redis as _redis

        bad_client = MagicMock()
        bad_client.ping.side_effect = _redis.ConnectionError("simulated outage")
        with patch("redis.Redis", return_value=bad_client):
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        for field in ("cache_backend_type", "cache_type_config", "cache_key_prefix"):
            self.assertIn(field, data)
            self.assertIsInstance(data[field], str)

    def test_health_endpoint_database_error_marks_down(self) -> None:
        """When the DB session raises, /health reports ``status=down`` and 503.

        TIK-91: DB failure escalates to ``status: down`` + HTTP 503 so k8s
        readiness + uptime checkers both rotate the pod out. Pre-TIK-91 this
        was ``status: degraded`` + HTTP 200.
        """
        with patch.object(db, "session") as fake_session:
            fake_session.begin.side_effect = RuntimeError("simulated db outage")
            response = self.client.get("/health")

        self.assertEqual(response.status_code, 503)
        data = response.get_json()
        self.assertEqual(data["database_status"], "error")
        self.assertEqual(data["status"], "down")
        self.assertIn("database_error", data)


class TestHealthSLAContract(unittest.TestCase):
    """TIK-91: /health strict-mode contract + Prometheus histogram.

    Covers the four canonical scenarios from the DoD:

    - DB up + Redis up                          → 200 healthy
    - DB up + Redis down (strict=0, default)    → 200 degraded
    - DB up + Redis down (strict=1)             → 503 degraded
    - DB down (any strict)                      → 503 down

    Plus: ``health_response_seconds`` histogram observes one sample
    (labelled with the final status) after every call.
    """

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self) -> None:
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    @staticmethod
    def _histogram_sample_count(status: str) -> float:
        """Read the cumulative observation count for ``status`` on the
        ``health_response_seconds`` histogram from the global Prometheus
        registry.

        Returns 0.0 when the label has never been observed.
        """
        from prometheus_client import REGISTRY

        value = REGISTRY.get_sample_value("health_response_seconds_count", {"status": status})
        return float(value) if value is not None else 0.0

    def test_db_up_redis_up_returns_200_healthy(self) -> None:
        """Scenario 1: DB up + Redis up → 200 + status=healthy."""
        fake_client = MagicMock()
        fake_client.ping.return_value = True
        fake_client.info.return_value = {"used_memory": 0}
        fake_client.set.return_value = True
        fake_client.get.return_value = "ok"

        before = self._histogram_sample_count("healthy")
        with patch("redis.Redis", return_value=fake_client):
            response = self.client.get("/health")
        after = self._histogram_sample_count("healthy")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["redis_status"], "connected")
        self.assertEqual(data["database_status"], "connected")
        self.assertAlmostEqual(after - before, 1.0)

    def test_db_up_redis_down_default_returns_200_degraded(self) -> None:
        """Scenario 2: DB up + Redis down (no strict) → 200 + status=degraded."""
        import redis as _redis

        fake_client = MagicMock()
        fake_client.ping.side_effect = _redis.ConnectionError("simulated outage")

        before = self._histogram_sample_count("degraded")
        with patch("redis.Redis", return_value=fake_client):
            response = self.client.get("/health")
        after = self._histogram_sample_count("degraded")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "degraded")
        self.assertEqual(data["redis_status"], "disconnected")
        self.assertEqual(data["database_status"], "connected")
        self.assertAlmostEqual(after - before, 1.0)

    def test_db_up_redis_down_strict_query_returns_503(self) -> None:
        """Scenario 3a: DB up + Redis down + ``?strict=1`` → 503 + degraded."""
        import redis as _redis

        fake_client = MagicMock()
        fake_client.ping.side_effect = _redis.ConnectionError("simulated outage")

        before = self._histogram_sample_count("degraded")
        with patch("redis.Redis", return_value=fake_client):
            response = self.client.get("/health?strict=1")
        after = self._histogram_sample_count("degraded")

        self.assertEqual(response.status_code, 503)
        data = response.get_json()
        self.assertEqual(data["status"], "degraded")
        self.assertEqual(data["redis_status"], "disconnected")
        self.assertAlmostEqual(after - before, 1.0)

    def test_db_up_redis_down_strict_header_returns_503(self) -> None:
        """Scenario 3b: DB up + Redis down + ``X-Health-Mode: strict`` → 503."""
        import redis as _redis

        fake_client = MagicMock()
        fake_client.ping.side_effect = _redis.ConnectionError("simulated outage")

        with patch("redis.Redis", return_value=fake_client):
            response = self.client.get("/health", headers={"X-Health-Mode": "strict"})

        self.assertEqual(response.status_code, 503)
        data = response.get_json()
        self.assertEqual(data["status"], "degraded")

    def test_db_down_returns_503_down_regardless_of_strict(self) -> None:
        """Scenario 4: DB down → 503 + status=down for any strict value."""
        before_down = self._histogram_sample_count("down")

        for strict_path in ("/health", "/health?strict=1"):
            with patch.object(db, "session") as fake_session:
                fake_session.begin.side_effect = RuntimeError("simulated db outage")
                response = self.client.get(strict_path)
            self.assertEqual(response.status_code, 503, f"{strict_path} should return 503")
            data = response.get_json()
            self.assertEqual(data["status"], "down")
            self.assertEqual(data["database_status"], "error")

        after_down = self._histogram_sample_count("down")
        # Two calls in this test, both labelled ``down``.
        self.assertAlmostEqual(after_down - before_down, 2.0)

    def test_histogram_uses_required_buckets(self) -> None:
        """Histogram is configured with the buckets pinned in TIK-91 DoD."""
        from blueprints.health import HEALTH_RESPONSE_SECONDS

        # ``_upper_bounds`` is the public-but-undocumented attribute
        # ``prometheus_client`` uses to remember the configured buckets
        # (``+Inf`` is appended automatically). Tested here so a future
        # refactor that drops a bucket fails fast.
        configured = tuple(HEALTH_RESPONSE_SECONDS._upper_bounds)
        expected = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, float("inf"))
        self.assertEqual(configured, expected)


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
