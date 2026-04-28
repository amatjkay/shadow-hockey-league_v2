"""Pytest fixtures for Shadow Hockey League tests.

Provides reusable fixtures for app, client, database session,
and test data seeding.
"""

import os
import tempfile
from unittest.mock import patch

import pytest


# Global mock for Redis to prevent any network activity during tests
class _FakeRedis:
    """Minimal in-memory Redis mock that supports get/set/delete/ping/info."""

    def __init__(self):
        self._store: dict = {}

    def get(self, key=None, name=None):
        k = name if key is None else key
        return self._store.get(k)

    def set(
        self, key=None, value=None, ex=None, px=None, nx=False, xx=False, keepttl=False, name=None
    ):
        k = name if key is None else key
        self._store[k] = value
        return True

    def setex(self, name=None, time=None, value=None, key=None, timeout=None):
        k = name if key is None else key
        self._store[k] = value
        return True

    def getset(self, key, value):
        old = self._store.get(key)
        self._store[key] = value
        return old

    def delete(self, *keys):
        for k in keys:
            self._store.pop(k, None)
        return len(keys)

    def mget(self, *keys):
        return [self._store.get(k) for k in keys]

    def keys(self, pattern="*"):
        return list(self._store.keys())

    def ping(self):
        return True

    def info(self, section=None):
        return {
            "used_memory": 1024 * 1024,
            "used_memory_human": "1M",
            "connected_clients": 1,
            "mem_fragmentation_ratio": 1.5,
        }

    def expire(self, key, time):
        return True

    def ttl(self, key):
        return -1

    def exists(self, *keys):
        return sum(1 for k in keys if k in self._store)

    def flushdb(self):
        self._store.clear()
        return True

    def pipeline(self, transaction=True):
        return self

    def execute(self):
        return []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


@pytest.fixture(scope="session", autouse=True)
def mock_redis():
    fake = _FakeRedis()
    with patch("redis.Redis", return_value=fake), patch("redis.from_url", return_value=fake):
        yield fake


@pytest.fixture(autouse=True)
def _reset_admin_login_rate_limit():
    """Clear in-memory admin login rate-limit state between tests.

    Without this, repeated logins from `auth_client` fixtures across tests
    exhaust the 10-attempts/60s budget and yield false 401s.
    """
    try:
        from services.admin import _login_attempts

        _login_attempts.clear()
    except Exception:
        pass
    yield


from app import create_app

# Explicitly import ALL models so SQLAlchemy metadata knows about all tables
# before db.create_all() is called. Without this, some tables (like
# achievement_types, audit_logs, leagues, seasons) will be missing in CI.
from models import (
    AdminUser,
    db,
)


@pytest.fixture(scope="session")
def app():
    """Create Flask application with testing config.

    This fixture is session-scoped to avoid recreating the app
    for every test.
    """
    app = create_app("config.TestingConfig")
    return app


@pytest.fixture
def client(app):
    """Create test client for Flask application."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Push application context for tests that need it."""
    ctx = app.app_context()
    ctx.push()
    yield ctx
    ctx.pop()


@pytest.fixture
def db_session(app, app_context):
    """Create database tables and provide session.

    Creates tables before each test and drops them after.
    Explicitly imports all models to ensure db.create_all sees them.
    """
    # Explicitly import all models so db.create_all creates their tables

    with app.app_context():
        db.create_all()
        yield db.session
        db.session.remove()
        db.drop_all()


@pytest.fixture
def seeded_db(app, app_context):
    """Create database with test data.

    Seeds country, manager, and achievements.
    """
    # Explicitly import all models so db.create_all creates their tables
    from models import (
        Achievement,
        AchievementType,
        Country,
        League,
        Manager,
        Season,
    )

    with app.app_context():
        db.create_all()

        # Create country
        country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
        db.session.add(country)
        db.session.flush()

        # Create manager
        manager = Manager(name="Test Manager", country_id=country.id)
        db.session.add(manager)
        db.session.flush()

        # Create reference data for achievements
        ach_type_top1 = AchievementType(
            code="TOP1", name="Top 1", base_points_l1=800, base_points_l2=400
        )
        ach_type_top2 = AchievementType(
            code="TOP2", name="Top 2", base_points_l1=400, base_points_l2=200
        )
        db.session.add_all([ach_type_top1, ach_type_top2])
        league = League(code="1", name="League 1")
        db.session.add(league)
        season_2324 = Season(code="23/24", name="Season 23/24", multiplier=0.5, is_active=False)
        season_2122 = Season(code="21/22", name="Season 21/22", multiplier=0.2, is_active=False)
        db.session.add_all([league, season_2324, season_2122])
        db.session.flush()

        # Create achievements with FK fields
        achievements = [
            Achievement(
                type_id=ach_type_top1.id,
                league_id=league.id,
                season_id=season_2324.id,
                title="TOP1",
                icon_path="/static/img/cups/top1.svg",
                manager_id=manager.id,
                base_points=800.0,
                multiplier=0.5,
                final_points=400.0,
            ),
            Achievement(
                type_id=ach_type_top2.id,
                league_id=league.id,
                season_id=season_2122.id,
                title="TOP2",
                icon_path="/static/img/cups/top2.svg",
                manager_id=manager.id,
                base_points=400.0,
                multiplier=0.2,
                final_points=80.0,
            ),
        ]
        for ach in achievements:
            db.session.add(ach)

        db.session.commit()

        yield db.session

        db.session.remove()
        db.drop_all()


@pytest.fixture
def temp_db_app(app):
    """Create app with temporary SQLite database file.

    Useful for integration tests that need file-based SQLite.
    """
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    with app.app_context():
        db.create_all()

    yield app, db_fd, db_path

    with app.app_context():
        db.session.remove()
        db.drop_all()

    os.close(db_fd)
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def admin_user(app, app_context):
    """Create admin user for testing."""
    with app.app_context():
        db.create_all()  # Ensure tables exist

        admin = AdminUser(username="testadmin", role=AdminUser.ROLE_SUPER_ADMIN)
        admin.set_password("testpass123")
        db.session.add(admin)
        db.session.commit()

        yield admin

        # Cleanup
        try:
            db.session.delete(admin)
            db.session.commit()
        except Exception:
            # Ignore cleanup errors (table might not exist)
            pass
