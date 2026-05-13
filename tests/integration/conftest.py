"""Integration-test conftest: optional Postgres override (TIK-95).

Default (``Quality & Tests`` job + local ``make test``):
``config.TestingConfig`` returns ``sqlite:///:memory:``; nothing in
this conftest fires and all tests run as before.

Postgres CI job: the ``integration-postgres`` workflow sets
``DATABASE_URL=postgresql+psycopg2://...`` and
``RUN_INTEGRATION_POSTGRES=1``.  We then monkey-patch
``config.TestingConfig`` so every call to
``create_app("config.TestingConfig")`` points at the Postgres URL,
and replace ``db.create_all`` / ``db.drop_all`` with Postgres-aware
shims so the alembic-owned schema survives between tests.

We do NOT touch ``config.py`` or ``models.py`` (AGENTS.md § 2
forbids it without owner approval) — every patch here is test-only.
"""

from __future__ import annotations

import os

import pytest

_RUN_PG = os.environ.get("RUN_INTEGRATION_POSTGRES") == "1"
_DB_URL = os.environ.get("DATABASE_URL", "")


def _is_postgres_url(url: str) -> bool:
    return url.startswith("postgresql://") or url.startswith("postgresql+")


if _RUN_PG and _is_postgres_url(_DB_URL):
    from sqlalchemy import text

    from config import TestingConfig
    from models import db

    TestingConfig.SQLALCHEMY_DATABASE_URI = _DB_URL  # type: ignore[assignment]

    @classmethod  # type: ignore[misc]
    def _pg_get_database_url(cls: type) -> str:  # noqa: ARG001
        return _DB_URL

    TestingConfig.get_database_url = _pg_get_database_url  # type: ignore[assignment]

    # The schema is owned by ``alembic upgrade head`` (the CI step
    # before pytest). Many integration tests call ``db.drop_all()``
    # in tearDown and ``db.create_all()`` in setUp for isolation —
    # the standard pattern on SQLite. On Postgres those calls would
    # destroy the alembic schema and then fail to recreate it,
    # because ``models.py`` declares ``unique=True`` columns as a
    # separate UNIQUE INDEX (not an inline ``UniqueConstraint``).
    # Postgres rejects ``FOREIGN KEY(parent_code) REFERENCES
    # leagues(code)`` during ``CREATE TABLE`` when the referent's
    # uniqueness only arrives via a later ``CREATE UNIQUE INDEX``;
    # SQLite is lenient about this.
    #
    # TODO(TIK-95-followup): teach ``models.py`` to use inline
    # ``UniqueConstraint`` for self-referential FKs so plain
    # ``db.create_all`` works on Postgres without this shim.
    #
    # In the meantime we keep alembic's schema between tests and
    # provide isolation via ``TRUNCATE ... RESTART IDENTITY
    # CASCADE``.

    def _pg_drop_all(*_args: object, **_kwargs: object) -> None:
        """Reset all tables in dependency order — schema stays."""
        tables = ", ".join(f'"{t.name}"' for t in db.metadata.sorted_tables)
        if not tables:
            return
        with db.engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))

    def _pg_create_all(*_args: object, **_kwargs: object) -> None:
        """Alembic owns the schema; we truncate to start each test clean.

        Mirrors SQLite's ``db.create_all`` on an in-memory DB —
        which always starts empty. Without this, alembic-seeded
        reference data (e.g. ``achievement_types.TOP1`` in
        ``b2c3d4e5f6a7_add_reference_tables.py``) would collide with
        rows the first test inserts in setUp.
        """
        _pg_drop_all()

    db.drop_all = _pg_drop_all  # type: ignore[method-assign]
    db.create_all = _pg_create_all  # type: ignore[method-assign]


def pytest_collection_modifyitems(
    config: pytest.Config,  # noqa: ARG001
    items: list[pytest.Item],
) -> None:
    """Skip SQLite-only integration suites when the Postgres CI job is active.

    ``tests/integration/test_routes.py`` hard-codes
    ``self.app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{...}"``
    in every ``setUp``, bypassing any conftest-level override.  Until a
    follow-up PR teaches it to honour ``DATABASE_URL``, we skip the
    entire module in the Postgres leg.

    TODO(TIK-95-followup): make test_routes.py honour DATABASE_URL so
    it can validate route behaviour on Postgres as well.
    """
    if not (_RUN_PG and _is_postgres_url(_DB_URL)):
        return

    skip_marker = pytest.mark.skip(
        reason="SQLite-only test setup (hard-coded sqlite:/// path); "
        "see TODO in tests/integration/conftest.py.",
    )
    for item in items:
        fspath = str(item.fspath).replace("\\", "/")
        if "tests/integration/test_routes.py" in fspath:
            item.add_marker(skip_marker)
