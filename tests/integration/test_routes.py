"""Integration tests for Shadow Hockey League application.

These tests verify the interaction between components:
- Flask application <-> Database
- API endpoints <-> Data validation
- Services <-> Data models

Unlike unit tests, these use a real SQLite database file.

Migrated from tests_integration.py
"""

import re
import threading
import time

from models import Achievement, AchievementType, Country, League, Manager, Season, db
from services.rating_service import build_leaderboard
from tests.integration._postgres_utils import IntegrationTestCase


def enable_sqlite_fk(session):
    """Enable foreign key constraints for SQLite (no-op on Postgres)."""
    if db.engine.dialect.name == "sqlite":
        session.execute(db.text("PRAGMA foreign_keys=ON"))


def _seed_reference_data():
    """Seed reference tables. Returns (league_ids, season_ids, type_map)."""
    leagues = {}
    for code in ["1", "2"]:
        lg = League(code=code, name=f"League {code}")
        db.session.add(lg)
        leagues[code] = lg

    seasons = {}
    # Smooth ``0.7 ^ years_ago`` decay (TIK-80).
    multipliers = {
        "25/26": 1.000,
        "24/25": 0.700,
        "23/24": 0.490,
        "22/23": 0.343,
        "21/22": 0.240,
    }
    for i, code in enumerate(["25/26", "24/25", "23/24", "22/23", "21/22"]):
        s = Season(
            code=code, name=f"Season {code}", multiplier=multipliers[code], is_active=(i == 0)
        )
        db.session.add(s)
        seasons[code] = s

    # Compact-10 scale (TIK-80): single-/low-double-digit values, BEST > TOP3.
    type_points = {
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


class TestEmptyDatabase(IntegrationTestCase):
    """Tests for empty database scenarios."""

    def test_empty_database_homepage(self) -> None:
        """Home page loads successfully with empty database."""
        with self.app.app_context():
            manager_count = db.session.query(Manager).count()
            self.assertEqual(manager_count, 0)

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Shadow Hockey League", html)


class TestBulkLoadPerformance(IntegrationTestCase):
    """Tests for bulk data load performance."""

    def test_bulk_load_100_managers(self) -> None:
        """Performance test: Load 100 managers with achievements."""
        with self.app.app_context():
            start = time.time()

            # Create reference data
            league_ids, season_ids, type_map = _seed_reference_data()
            db.session.commit()

            # Pre-load reference objects for efficient relationship assignment
            type_objs = {
                code: db.session.get(AchievementType, at.id) for code, at in type_map.items()
            }
            league_obj = db.session.get(League, league_ids["1"])
            season_obj = db.session.get(Season, season_ids["25/26"])

            # Create countries
            for i in range(10):
                country = Country(code=f"C{i:02d}", flag_path="/static/img/flags/test.png")
                db.session.add(country)
            db.session.commit()

            # Create managers
            for i in range(100):
                manager = Manager(name=f"Manager {i:03d}", country_id=(i % 10) + 1)
                db.session.add(manager)
            db.session.commit()

            # Create achievements (5 per manager) - assign relationships directly
            type_list = ["TOP1", "TOP2", "TOP3", "BEST", "R3"]
            title_list = ["TOP1", "TOP2", "TOP3", "Best regular", "Round 3"]
            icon_list = ["top1", "top2", "top3", "best", "r3"]
            for manager_id in range(1, 101):
                for j in range(5):
                    achievement = Achievement(
                        type_id=type_map[type_list[j]].id,
                        league_id=league_ids["1"],
                        season_id=season_ids["25/26"],
                        title=title_list[j],
                        icon_path=f"/static/img/cups/{icon_list[j]}.svg",
                        manager_id=manager_id,
                    )
                    # Assign relationships directly so event listener skips lookups
                    achievement.type = type_objs[type_list[j]]
                    achievement.league = league_obj
                    achievement.season = season_obj
                    db.session.add(achievement)
            db.session.commit()

            elapsed = time.time() - start

        self.assertLess(elapsed, 5.0, f"Bulk load took {elapsed:.2f}s (expected < 5s)")

        with self.app.app_context():
            manager_count = db.session.query(Manager).count()
            achievement_count = db.session.query(Achievement).count()
            self.assertEqual(manager_count, 100)
            self.assertEqual(achievement_count, 500)

    def test_leaderboard_load_performance(self) -> None:
        """Performance test: Leaderboard load with 100 managers."""
        with self.app.app_context():
            league_ids, season_ids, type_map = _seed_reference_data()
            db.session.commit()

            # Create countries
            for i in range(10):
                country = Country(code=f"C{i:02d}", flag_path="/static/img/flags/test.png")
                db.session.add(country)
            db.session.commit()

            # Create managers
            for i in range(100):
                manager = Manager(name=f"Manager {i:03d}", country_id=(i % 10) + 1)
                db.session.add(manager)
            db.session.commit()

            # Create achievements
            for manager_id in range(1, 101):
                achievement = Achievement(
                    type_id=type_map["TOP1"].id,
                    league_id=league_ids["1"],
                    season_id=season_ids["25/26"],
                    title="TOP1",
                    icon_path="/static/img/cups/top1.svg",
                    manager_id=manager_id,
                )
                db.session.add(achievement)
            db.session.commit()

        with self.app.app_context():
            start = time.time()
            response = self.client.get("/")
            elapsed = time.time() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 2.0, f"Page load took {elapsed:.2f}s (expected < 2s)")


class TestTransactionRollback(IntegrationTestCase):
    """Tests for transaction rollback on errors."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        super().setUp()
        with self.app.app_context():
            country = Country(code="TST", flag_path="/static/img/flags/test.png")
            db.session.add(country)
            db.session.commit()

    def test_unique_constraint_rollback(self) -> None:
        """Transaction rolls back on unique constraint violation."""
        with self.app.app_context():
            initial_count = db.session.query(Manager).count()

            try:
                with db.session.begin():
                    db.session.add(Manager(name="Duplicate Name", country_id=1))
                    db.session.add(Manager(name="Duplicate Name", country_id=1))
            except Exception:
                pass

            final_count = db.session.query(Manager).count()
            self.assertEqual(initial_count, final_count)


class TestConcurrentRequests(IntegrationTestCase):
    """Tests for concurrent request handling."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        super().setUp()
        with self.app.app_context():
            country = Country(code="CON", flag_path="/static/img/flags/test.png")
            db.session.add(country)
            db.session.commit()

            for i in range(10):
                manager = Manager(name=f"Manager {i}", country_id=country.id)
                db.session.add(manager)
            db.session.commit()

    def test_concurrent_homepage_requests(self) -> None:
        """Handle 10 concurrent homepage requests."""
        results = []
        lock = threading.Lock()

        def make_request() -> None:
            response = self.client.get("/")
            with lock:
                results.append(response.status_code)

        threads = [threading.Thread(target=make_request) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 10)
        self.assertTrue(all(code == 200 for code in results))

    def test_concurrent_homepage_requests_stress(self) -> None:
        """TIK-86 regression: repeated concurrent homepage requests stay 200.

        Without the ``_LEADERBOARD_LOCK`` guard in ``rating_service``, a
        joinedload race in SQLAlchemy 2.0 surfaces as ``IndexError: tuple
        index out of range`` or ``None`` manager rows once every ~50 calls
        of ``build_leaderboard()`` on a 10-thread fan-out. 20 iterations
        amplify that to >99 % chance of catching the regression locally.
        """
        for _ in range(20):
            results: list[int] = []
            lock = threading.Lock()

            def make_request() -> None:
                response = self.client.get("/")
                with lock:
                    results.append(response.status_code)

            threads = [threading.Thread(target=make_request) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            self.assertEqual(len(results), 10)
            self.assertTrue(
                all(code == 200 for code in results),
                f"Non-200 leaderboard responses under concurrency: {results}",
            )


class TestAPICRUDOperations(IntegrationTestCase):
    """Tests for API CRUD operations."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        super().setUp()
        with self.app.app_context():
            country = Country(code="API", flag_path="/static/img/flags/test.png")
            db.session.add(country)
            db.session.commit()
            self.country_id = country.id

            from models import ApiKey
            from services.api_auth import generate_api_key, hash_api_key

            self.api_key = generate_api_key()
            db.session.add(
                ApiKey(
                    key_hash=hash_api_key(self.api_key),
                    name="Test API Key",
                    scope="admin",
                )
            )
            db.session.commit()

    def _post(self, url: str, json: dict):
        return self.client.post(url, json=json, headers={"X-API-Key": self.api_key})

    def _get(self, url: str):
        return self.client.get(url, headers={"X-API-Key": self.api_key})

    def _put(self, url: str, json: dict):
        return self.client.put(url, json=json, headers={"X-API-Key": self.api_key})

    def _delete(self, url: str):
        return self.client.delete(url, headers={"X-API-Key": self.api_key})

    def test_api_crud_cycle(self) -> None:
        """Complete CRUD cycle through API."""
        response = self._post("/api/managers", json={"name": "CRUD Test Manager", "country_id": 1})
        self.assertEqual(response.status_code, 201)
        manager_id = response.get_json()["id"]

        response = self._get(f"/api/managers/{manager_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "CRUD Test Manager")

        response = self._put(f"/api/managers/{manager_id}", json={"name": "Updated Manager"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "Updated Manager")

        response = self._delete(f"/api/managers/{manager_id}")
        self.assertEqual(response.status_code, 200)

        response = self._get(f"/api/managers/{manager_id}")
        self.assertEqual(response.status_code, 404)

    def test_api_validation_errors(self) -> None:
        """API rejects invalid data."""
        response = self._post("/api/managers", json={"name": "", "country_id": 1})
        self.assertEqual(response.status_code, 400)

        response = self._post("/api/managers", json={"name": "Test"})
        self.assertEqual(response.status_code, 400)

        response = self._post("/api/managers", json={"name": "Test", "country_id": 9999})
        self.assertEqual(response.status_code, 400)

        self._post("/api/managers", json={"name": "Duplicate", "country_id": 1})
        response = self._post("/api/managers", json={"name": "Duplicate", "country_id": 1})
        self.assertEqual(response.status_code, 409)


class TestRatingCalculationIntegration(IntegrationTestCase):
    """Tests for rating service integration with real database."""

    def test_rating_calculation_with_real_db(self) -> None:
        """Rating calculation with real database data."""
        with self.app.app_context():
            league_ids, season_ids, type_map = _seed_reference_data()

            country = Country(code="RAT", flag_path="/static/img/flags/test.png")
            db.session.add(country)
            db.session.commit()

            manager = Manager(name="Rating Test", country_id=country.id)
            db.session.add(manager)
            db.session.commit()

            manager_id = manager.id

            # Compact-10 scale (TIK-80): TOP1 L1 s25/26 -> 10.0 x 1.000 = 10.0.
            db.session.add(
                Achievement(
                    type_id=type_map["TOP1"].id,
                    league_id=league_ids["1"],
                    season_id=season_ids["25/26"],
                    title="TOP1",
                    icon_path="/static/img/cups/top1.svg",
                    manager_id=manager_id,
                )
            )

            # Compact-10 scale (TIK-80): TOP2 L1 s24/25 -> 5.0 x 0.700 = 3.5.
            db.session.add(
                Achievement(
                    type_id=type_map["TOP2"].id,
                    league_id=league_ids["1"],
                    season_id=season_ids["24/25"],
                    title="TOP2",
                    icon_path="/static/img/cups/top2.svg",
                    manager_id=manager_id,
                )
            )

            db.session.commit()

        with self.app.app_context():
            leaderboard = build_leaderboard(db.session)

        test_entry = next(e for e in leaderboard if e["name"] == "Rating Test")
        # Total = 10.0 (TOP1 L1 s25/26 @ 1.000) + 3.5 (TOP2 L1 s24/25 @ 0.700) = 13.5.
        self.assertEqual(test_entry["total"], 13.5)


class TestCascadeDelete(IntegrationTestCase):
    """Tests for cascade delete behavior."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        super().setUp()
        with self.app.app_context():
            country = Country(code="DEL", flag_path="/static/img/flags/test.png")
            db.session.add(country)
            db.session.commit()
            self.country_id = country.id

            from models import ApiKey
            from services.api_auth import generate_api_key, hash_api_key

            self.api_key = generate_api_key()
            db.session.add(
                ApiKey(
                    key_hash=hash_api_key(self.api_key),
                    name="Test API Key",
                    scope="admin",
                )
            )
            db.session.commit()

    def _delete(self, url: str):
        return self.client.delete(url, headers={"X-API-Key": self.api_key})

    def test_manager_delete_cascades_to_achievements(self) -> None:
        """Deleting manager also deletes achievements (CASCADE)."""
        with self.app.app_context():
            league_ids, season_ids, type_map = _seed_reference_data()
            db.session.commit()

            manager = Manager(name="Delete Test", country_id=1)
            db.session.add(manager)
            db.session.commit()

            manager_id = manager.id

            type_list = ["TOP1", "TOP2", "TOP3"]
            icon_list = ["top1", "top2", "top3"]
            for i in range(3):
                db.session.add(
                    Achievement(
                        type_id=type_map[type_list[i]].id,
                        league_id=league_ids["1"],
                        season_id=season_ids["25/26"],
                        title=type_list[i],
                        icon_path=f"/static/img/cups/{icon_list[i]}.svg",
                        manager_id=manager_id,
                    )
                )
            db.session.commit()

            before_count = db.session.query(Achievement).filter_by(manager_id=manager_id).count()
            self.assertEqual(before_count, 3)

        response = self._delete(f"/api/managers/{manager_id}")
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            after_count = db.session.query(Achievement).filter_by(manager_id=manager_id).count()
            self.assertEqual(after_count, 0)


class TestDatabaseConstraints(IntegrationTestCase):
    """Tests for database constraint enforcement."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        super().setUp()
        with self.app.app_context():
            enable_sqlite_fk(db.session)

    def test_country_code_unique(self) -> None:
        """Country code must be unique."""
        with self.app.app_context():
            country1 = Country(code="UNI", flag_path="/static/img/flags/test1.png")
            db.session.add(country1)
            db.session.commit()

            country2 = Country(code="UNI", flag_path="/static/img/flags/test2.png")
            db.session.add(country2)

            with self.assertRaises(Exception):
                db.session.commit()

    def test_manager_name_unique(self) -> None:
        """Manager name must be unique."""
        with self.app.app_context():
            country = Country(code="MNG", flag_path="/static/img/flags/test.png")
            db.session.add(country)
            db.session.commit()

            manager1 = Manager(name="Unique Name", country_id=country.id)
            db.session.add(manager1)
            db.session.commit()

            manager2 = Manager(name="Unique Name", country_id=country.id)
            db.session.add(manager2)

            with self.assertRaises(Exception):
                db.session.commit()

    def test_achievement_requires_manager(self) -> None:
        """Achievement must reference existing manager."""
        with self.app.app_context():
            league_ids, season_ids, type_map = _seed_reference_data()
            db.session.commit()

            # Attempt to create achievement with non-existent manager
            achievement = Achievement(
                type_id=type_map["TOP1"].id,
                league_id=league_ids["1"],
                season_id=season_ids["24/25"],
                title="TOP1",
                icon_path="/static/img/cups/top1.svg",
                manager_id=9999,
            )
            db.session.add(achievement)

            with self.assertRaises(Exception):
                db.session.commit()


class TestLeaderboardTotalFormatting(IntegrationTestCase):
    """TIK-81: leaderboard total must render as ``XX.XX`` (no float-noise).

    Without explicit ``"%.2f"|format`` in ``templates/index.html``, sums of
    round-2 floats can render as e.g. ``20.380000000000003`` (TIK-80 T6).
    """

    def test_score_cell_formatted_to_two_decimals(self) -> None:
        """Score-cell renders as ``\\d+\\.\\d{2}`` without float-noise tail."""
        with self.app.app_context():
            league_ids, season_ids, type_map = _seed_reference_data()
            db.session.commit()

            country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
            db.session.add(country)
            db.session.commit()

            manager = Manager(name="Format Test", country_id=country.id)
            db.session.add(manager)
            db.session.commit()

            for season_code in ["25/26", "24/25", "23/24", "22/23", "21/22"]:
                achievement = Achievement(
                    type_id=type_map["TOP1"].id,
                    league_id=league_ids["1"],
                    season_id=season_ids[season_code],
                    title="TOP1",
                    icon_path="/static/img/cups/top1.svg",
                    manager_id=manager.id,
                )
                db.session.add(achievement)
            db.session.commit()

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        score_cells = re.findall(
            r'<td class="table-items score-cell">([^<]+)</td>',
            html,
        )
        self.assertTrue(score_cells, "expected at least one score-cell row")
        for cell in score_cells:
            value = cell.strip()
            self.assertNotRegex(
                value,
                r"^\d+\.\d{4,}$",
                f"score-cell {value!r} has float-noise (>=4 decimals)",
            )
            self.assertRegex(
                value,
                r"^\d+\.\d{2}$",
                f"score-cell {value!r} not formatted to two decimals",
            )


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)
