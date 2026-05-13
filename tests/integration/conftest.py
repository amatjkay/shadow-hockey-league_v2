"""Integration-test conftest: optional Postgres override (TIK-95).

Default (``Quality & Tests`` job + local ``make test``):
``config.TestingConfig`` returns ``sqlite:///:memory:``; nothing in
this conftest fires and all tests run as before.

Postgres CI job: the ``integration-postgres`` workflow sets
``DATABASE_URL=postgresql+psycopg2://...`` and
``RUN_INTEGRATION_POSTGRES=1``.  We then monkey-patch
``config.TestingConfig`` so every call to
``create_app("config.TestingConfig")`` points at the Postgres URL.

``db.create_all`` / ``db.drop_all`` now work on Postgres natively
because ``models.py::League.code`` uses an inline ``UNIQUE`` constraint
(TIK-98) — the previous monkey-patch shim is no longer needed.
"""

from __future__ import annotations

import os

import pytest

_RUN_PG = os.environ.get("RUN_INTEGRATION_POSTGRES") == "1"
_DB_URL = os.environ.get("DATABASE_URL", "")


def _is_postgres_url(url: str) -> bool:
    return url.startswith("postgresql://") or url.startswith("postgresql+")


if _RUN_PG and _is_postgres_url(_DB_URL):
    from config import TestingConfig

    TestingConfig.SQLALCHEMY_DATABASE_URI = _DB_URL  # type: ignore[assignment]

    @classmethod  # type: ignore[misc]
    def _pg_get_database_url(cls: type) -> str:  # noqa: ARG001
        return _DB_URL

    TestingConfig.get_database_url = _pg_get_database_url  # type: ignore[assignment]

    # ``alembic upgrade head`` (the CI step before pytest) seeds reference
    # data into ``achievement_types`` / ``leagues`` / ``seasons``. The
    # unittest-style integration tests assume the SQLite-shaped contract
    # where ``setUp`` starts on empty tables, so we drop the alembic
    # schema once at conftest import time and let each test's ``setUp``
    # call ``db.create_all()`` to recreate fresh tables. Real
    # ``db.drop_all()`` / ``db.create_all()`` cycles between tests are now
    # safe on Postgres because ``models.py::League.code`` uses an inline
    # ``UNIQUE`` constraint (TIK-98), so the self-referential FK
    # ``leagues.parent_code -> leagues.code`` no longer hits the
    # referent-uniqueness check that previously required a shim.
    from app import create_app  # noqa: E402
    from models import db  # noqa: E402

    _bootstrap_app = create_app("config.TestingConfig")
    with _bootstrap_app.app_context():
        db.drop_all()


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
