"""Test-only helpers for the Postgres CI matrix (TIK-99).

``tests/integration/test_routes.py`` runs unchanged under SQLite via
the existing ``tempfile + db.create_all / db.drop_all`` flow.  When
the integration suite is launched with
``DATABASE_URL=postgresql+psycopg2://...`` (the
``integration-postgres`` CI leg or a local docker smoke run), each
test instead points Flask-SQLAlchemy at that URL and lets
``db.create_all`` / ``db.drop_all`` cycle the schema per test.

The native ``create_all`` / ``drop_all`` cycle is safe on Postgres
because ``models.py::League.code`` uses an inline ``UNIQUE``
constraint (TIK-98), so the self-referential FK
``leagues.parent_code -> leagues.code`` no longer hits the
referent-uniqueness check that previously required the conftest
TRUNCATE shim.

Lives here so the same setUp/tearDown branch is not copy-pasted
across the 9 ``unittest.TestCase`` subclasses in ``test_routes.py``.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from typing import Any

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


class IntegrationTestCase(unittest.TestCase):
    """Base TestCase that honours ``DATABASE_URL`` for the Postgres CI matrix.

    Subclasses get a wired ``self.app`` / ``self.client`` pair and a clean
    database before each test:

    * On Postgres (``DATABASE_URL=postgresql://...``): re-uses that URL
      and ``db.create_all`` / ``db.drop_all`` between tests (works
      natively post-TIK-98).
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
        else:
            self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
            self.app = create_app("config.TestingConfig")
            self.app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{self.db_path}"
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self) -> None:
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        if self.db_path is not None:
            os.close(self.db_fd)
            try:
                os.unlink(self.db_path)
            except OSError:
                pass
