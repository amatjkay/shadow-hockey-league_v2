"""Test-only helpers for the Postgres CI matrix (TIK-99).

When the integration suite runs under ``DATABASE_URL`` pointing at a
PostgreSQL URL, ``test_routes.py`` re-uses the alembic-built schema and
isolates tests via ``TRUNCATE ... RESTART IDENTITY CASCADE`` instead of
the SQLite ``tempfile + db.create_all`` flow.

Lives here so the same setUp/tearDown branch is not copy-pasted across
the 9 ``unittest.TestCase`` subclasses in ``test_routes.py``.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from typing import Any

from sqlalchemy import text

from app import create_app
from models import db


def _is_postgres_url(url: str) -> bool:
    """True iff ``url`` is a SQLAlchemy PostgreSQL URL."""
    return url.startswith("postgresql://") or url.startswith("postgresql+")


def _env_database_url() -> str:
    return os.environ.get("DATABASE_URL", "")


def using_postgres() -> bool:
    """True iff ``$DATABASE_URL`` targets PostgreSQL."""
    return _is_postgres_url(_env_database_url())


def truncate_all_tables() -> None:
    """``TRUNCATE ... RESTART IDENTITY CASCADE`` over every model table.

    Mirrors the global ``db.drop_all`` shim in
    ``tests/integration/conftest.py``. Must be called inside an active
    application context.
    """
    tables = ", ".join(f'"{t.name}"' for t in db.metadata.sorted_tables)
    if not tables:
        return
    with db.engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))


class IntegrationTestCase(unittest.TestCase):
    """Base TestCase that honours ``DATABASE_URL`` for the Postgres CI matrix.

    Subclasses get a wired ``self.app`` / ``self.client`` pair and a clean
    database before each test:

    * On Postgres (``DATABASE_URL=postgresql://...``): re-uses the
      alembic-built schema and TRUNCATEs all tables between tests.
    * On SQLite (default): creates a tempfile DB and uses
      ``db.create_all`` / ``db.drop_all`` between tests.

    Subclasses with extra fixture data should override ``setUp`` and
    call ``super().setUp()`` first.
    """

    app: Any
    client: Any
    db_fd: Any
    db_path: Any

    def setUp(self) -> None:
        url = _env_database_url()
        if _is_postgres_url(url):
            self.db_fd = None
            self.db_path = None
            self.app = create_app("config.TestingConfig")
            self.app.config["SQLALCHEMY_DATABASE_URI"] = url
            self.client = self.app.test_client()
            with self.app.app_context():
                truncate_all_tables()
        else:
            self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
            self.app = create_app("config.TestingConfig")
            self.app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{self.db_path}"
            self.client = self.app.test_client()
            with self.app.app_context():
                db.create_all()

    def tearDown(self) -> None:
        if self.db_path is None:
            with self.app.app_context():
                db.session.remove()
                truncate_all_tables()
        else:
            with self.app.app_context():
                db.session.remove()
                db.drop_all()
            os.close(self.db_fd)
            try:
                os.unlink(self.db_path)
            except OSError:
                pass
