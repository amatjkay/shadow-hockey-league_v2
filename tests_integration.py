"""Integration tests for Shadow Hockey League application.

These tests verify the interaction between components:
- Flask application ↔ Database
- API endpoints ↔ Data validation
- Services ↔ Data models

Unlike unit tests, these use a real SQLite database file.
"""

import os
import tempfile
import threading
import time
import unittest

from app import create_app
from models import Achievement, Country, Manager, db
from services.rating_service import build_leaderboard


def enable_sqlite_fk(session):
    """Enable foreign key constraints for SQLite."""
    session.execute(db.text("PRAGMA foreign_keys=ON"))


class TestEmptyDatabase(unittest.TestCase):
    """Tests for empty database scenarios."""

    def setUp(self) -> None:
        """Set up test fixtures with empty database."""
        # Create temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        
        self.app = create_app("config.TestingConfig")
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self) -> None:
        """Clean up after tests."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
        # Close and remove temporary file
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_empty_database_homepage(self) -> None:
        """Home page loads successfully with empty database."""
        # Arrange: Database is empty (no managers, no countries)
        with self.app.app_context():
            manager_count = db.session.query(Manager).count()
            self.assertEqual(manager_count, 0)
        
        # Act
        response = self.client.get('/')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        # Page should load, even if empty
        self.assertIn("Shadow Hockey League", html)


class TestBulkLoadPerformance(unittest.TestCase):
    """Tests for bulk data load performance."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        
        self.app = create_app("config.TestingConfig")
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self) -> None:
        """Clean up after tests."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_bulk_load_100_managers(self) -> None:
        """Performance test: Load 100 managers with achievements."""
        # Arrange & Act: Create 100 managers with 5 achievements each
        with self.app.app_context():
            start = time.time()
            
            # Create countries
            for i in range(10):
                country = Country(
                    code=f"COD{i:03d}",
                    flag_path="/static/img/flags/test.png"
                )
                db.session.add(country)
            db.session.commit()
            
            # Create managers
            for i in range(100):
                manager = Manager(
                    name=f"Manager {i:03d}",
                    country_id=(i % 10) + 1
                )
                db.session.add(manager)
            db.session.commit()
            
            # Create achievements (5 per manager)
            for manager_id in range(1, 101):
                for j in range(5):
                    achievement = Achievement(
                        achievement_type="TOP1",
                        league="1",
                        season="24/25",
                        title="TOP1",
                        icon_path="/static/img/cups/top1.svg",
                        manager_id=manager_id
                    )
                    db.session.add(achievement)
            db.session.commit()
            
            elapsed = time.time() - start
        
        # Assert: Bulk load should complete in reasonable time
        self.assertLess(elapsed, 5.0, f"Bulk load took {elapsed:.2f}s (expected < 5s)")
        
        # Verify counts
        with self.app.app_context():
            manager_count = db.session.query(Manager).count()
            achievement_count = db.session.query(Achievement).count()
            self.assertEqual(manager_count, 100)
            self.assertEqual(achievement_count, 500)

    def test_leaderboard_load_performance(self) -> None:
        """Performance test: Leaderboard load with 100 managers."""
        # Arrange: 100 managers with achievements already created
        with self.app.app_context():
            # Create countries
            for i in range(10):
                country = Country(
                    code=f"COD{i:03d}",
                    flag_path="/static/img/flags/test.png"
                )
                db.session.add(country)
            db.session.commit()
            
            # Create managers
            for i in range(100):
                manager = Manager(
                    name=f"Manager {i:03d}",
                    country_id=(i % 10) + 1
                )
                db.session.add(manager)
            db.session.commit()
            
            # Create achievements
            for manager_id in range(1, 101):
                achievement = Achievement(
                    achievement_type="TOP1",
                    league="1",
                    season="24/25",
                    title="TOP1",
                    icon_path="/static/img/cups/top1.svg",
                    manager_id=manager_id
                )
                db.session.add(achievement)
            db.session.commit()
        
        # Act: Measure leaderboard load time
        with self.app.app_context():
            start = time.time()
            response = self.client.get('/')
            elapsed = time.time() - start
        
        # Assert: Page load should be fast
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 2.0, f"Page load took {elapsed:.2f}s (expected < 2s)")


class TestTransactionRollback(unittest.TestCase):
    """Tests for transaction rollback on errors."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        
        self.app = create_app("config.TestingConfig")
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            
            # Create initial country
            country = Country(code="TST", flag_path="/static/img/flags/test.png")
            db.session.add(country)
            db.session.commit()

    def tearDown(self) -> None:
        """Clean up after tests."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_unique_constraint_rollback(self) -> None:
        """Transaction rolls back on unique constraint violation."""
        # Arrange
        with self.app.app_context():
            initial_count = db.session.query(Manager).count()
            
            # Act: Attempt to create managers with duplicate names
            try:
                with db.session.begin():
                    db.session.add(Manager(name="Duplicate Name", country_id=1))
                    db.session.add(Manager(name="Duplicate Name", country_id=1))  # Will fail
            except Exception:
                pass  # Expected exception
            
            # Assert: Count should be unchanged
            final_count = db.session.query(Manager).count()
            self.assertEqual(initial_count, final_count)


class TestConcurrentRequests(unittest.TestCase):
    """Tests for concurrent request handling."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        
        self.app = create_app("config.TestingConfig")
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            
            # Create test data
            country = Country(code="CON", flag_path="/static/img/flags/test.png")
            db.session.add(country)
            db.session.commit()
            
            for i in range(10):
                manager = Manager(name=f"Manager {i}", country_id=1)
                db.session.add(manager)
            db.session.commit()

    def tearDown(self) -> None:
        """Clean up after tests."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_concurrent_homepage_requests(self) -> None:
        """Handle 10 concurrent homepage requests."""
        results = []
        lock = threading.Lock()
        
        def make_request() -> None:
            response = self.client.get('/')
            with lock:
                results.append(response.status_code)
        
        # Act: 10 concurrent requests
        threads = [threading.Thread(target=make_request) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Assert: All requests successful
        self.assertEqual(len(results), 10)
        self.assertTrue(all(code == 200 for code in results))


class TestAPICRUDOperations(unittest.TestCase):
    """Tests for API CRUD operations."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        
        self.app = create_app("config.TestingConfig")
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            
            # Create country for tests
            country = Country(code="API", flag_path="/static/img/flags/test.png")
            db.session.add(country)
            db.session.commit()

    def tearDown(self) -> None:
        """Clean up after tests."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_api_crud_cycle(self) -> None:
        """Complete CRUD cycle through API."""
        # Create
        response = self.client.post(
            '/api/managers',
            json={"name": "CRUD Test Manager", "country_id": 1}
        )
        self.assertEqual(response.status_code, 201)
        manager_id = response.get_json()['id']
        
        # Read
        response = self.client.get(f'/api/managers/{manager_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['name'], "CRUD Test Manager")
        
        # Update
        response = self.client.put(
            f'/api/managers/{manager_id}',
            json={"name": "Updated Manager"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['name'], "Updated Manager")
        
        # Delete
        response = self.client.delete(f'/api/managers/{manager_id}')
        self.assertEqual(response.status_code, 200)
        
        # Verify deletion
        response = self.client.get(f'/api/managers/{manager_id}')
        self.assertEqual(response.status_code, 404)

    def test_api_validation_errors(self) -> None:
        """API rejects invalid data."""
        # Empty name
        response = self.client.post(
            '/api/managers',
            json={"name": "", "country_id": 1}
        )
        self.assertEqual(response.status_code, 400)
        
        # Missing country_id
        response = self.client.post(
            '/api/managers',
            json={"name": "Test"}
        )
        self.assertEqual(response.status_code, 400)
        
        # Non-existent country
        response = self.client.post(
            '/api/managers',
            json={"name": "Test", "country_id": 9999}
        )
        self.assertEqual(response.status_code, 400)
        
        # Duplicate name
        self.client.post(
            '/api/managers',
            json={"name": "Duplicate", "country_id": 1}
        )
        response = self.client.post(
            '/api/managers',
            json={"name": "Duplicate", "country_id": 1}
        )
        self.assertEqual(response.status_code, 409)


class TestRatingCalculationIntegration(unittest.TestCase):
    """Tests for rating service integration with real database."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        
        self.app = create_app("config.TestingConfig")
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self) -> None:
        """Clean up after tests."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_rating_calculation_with_real_db(self) -> None:
        """Rating calculation with real database data."""
        # Arrange: Create manager with known achievements
        with self.app.app_context():
            country = Country(code="RAT", flag_path="/static/img/flags/test.png")
            db.session.add(country)
            db.session.commit()
            
            manager = Manager(name="Rating Test", country_id=country.id)
            db.session.add(manager)
            db.session.commit()
            
            manager_id = manager.id

            # TOP1 s25/26: 800 × 1.00 = 800
            db.session.add(Achievement(
                achievement_type="TOP1",
                league="1",
                season="25/26",
                title="TOP1",
                icon_path="/static/img/cups/top1.svg",
                manager_id=manager_id
            ))

            # TOP2 s24/25: 550 × 0.95 = 522.5 → 522 (banker's rounding)
            db.session.add(Achievement(
                achievement_type="TOP2",
                league="1",
                season="24/25",
                title="TOP2",
                icon_path="/static/img/cups/top2.svg",
                manager_id=manager_id
            ))
            
            db.session.commit()
        
        # Act
        with self.app.app_context():
            leaderboard = build_leaderboard(db.session)

        # Assert: 800 + 522 = 1322 (TOP1 s25/26: 800×1.00=800, TOP2 s24/25: 550×0.95=522.5→522 banker's rounding)
        test_entry = next(e for e in leaderboard if e['name'] == 'Rating Test')
        self.assertEqual(test_entry['total'], 1322)


class TestCascadeDelete(unittest.TestCase):
    """Tests for cascade delete behavior."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        
        self.app = create_app("config.TestingConfig")
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            
            country = Country(code="DEL", flag_path="/static/img/flags/test.png")
            db.session.add(country)
            db.session.commit()

    def tearDown(self) -> None:
        """Clean up after tests."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_manager_delete_cascades_to_achievements(self) -> None:
        """Deleting manager also deletes achievements (CASCADE)."""
        # Arrange: Create manager with achievements
        with self.app.app_context():
            manager = Manager(name="Delete Test", country_id=1)
            db.session.add(manager)
            db.session.commit()
            
            manager_id = manager.id
            
            for i in range(3):
                db.session.add(Achievement(
                    achievement_type="TOP1",
                    league="1",
                    season="24/25",
                    title="TOP1",
                    icon_path="/static/img/cups/top1.svg",
                    manager_id=manager_id
                ))
            db.session.commit()
            
            # Count before delete
            before_count = db.session.query(Achievement).filter_by(
                manager_id=manager_id
            ).count()
            self.assertEqual(before_count, 3)
        
        # Act: Delete manager via API
        response = self.client.delete(f'/api/managers/{manager_id}')
        self.assertEqual(response.status_code, 200)
        
        # Assert: Achievements deleted via CASCADE
        with self.app.app_context():
            after_count = db.session.query(Achievement).filter_by(
                manager_id=manager_id
            ).count()
            self.assertEqual(after_count, 0)


class TestDatabaseConstraints(unittest.TestCase):
    """Tests for database constraint enforcement."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        
        self.app = create_app("config.TestingConfig")
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            enable_sqlite_fk(db.session)

    def tearDown(self) -> None:
        """Clean up after tests."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_country_code_unique(self) -> None:
        """Country code must be unique."""
        with self.app.app_context():
            country1 = Country(code="UNI", flag_path="/static/img/flags/test1.png")
            db.session.add(country1)
            db.session.commit()
            
            # Attempt duplicate
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
            
            # Attempt duplicate
            manager2 = Manager(name="Unique Name", country_id=country.id)
            db.session.add(manager2)
            
            with self.assertRaises(Exception):
                db.session.commit()

    def test_achievement_requires_manager(self) -> None:
        """Achievement must reference existing manager."""
        with self.app.app_context():
            # Attempt to create achievement with non-existent manager
            achievement = Achievement(
                achievement_type="TOP1",
                league="1",
                season="24/25",
                title="TOP1",
                icon_path="/static/img/cups/top1.svg",
                manager_id=9999  # Non-existent
            )
            db.session.add(achievement)
            
            with self.assertRaises(Exception):
                db.session.commit()


if __name__ == '__main__':
    unittest.main(verbosity=2)
