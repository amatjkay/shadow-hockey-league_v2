"""Pytest fixtures for Shadow Hockey League tests.

Provides reusable fixtures for app, client, database session,
and test data seeding.
"""

import os
import tempfile

import pytest

from app import create_app
from models import Achievement, Country, Manager, AdminUser, db


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
    """
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
        
        admin = AdminUser(username="testadmin")
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
