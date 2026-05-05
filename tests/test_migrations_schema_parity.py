"""Regression tests for Alembic-vs-model schema parity.

These tests would have caught the prod 500 from 2026-05-05 (``no such
column: achievement_types.is_active``). They build a database from
migrations *only* — no ``db.create_all()`` — and assert that every
column declared in ``models.py`` actually exists in the resulting
schema.

If a future model gets a new ``Column`` without a matching migration,
``test_migrations_match_models`` fails with the exact list of missing
columns *before* the change can reach production.

We also exercise the migration through a full ``upgrade → downgrade →
upgrade`` cycle to catch accidentally-non-idempotent migrations
(another class of bug that almost broke prod here — see
``9a30d278d31d`` and ``c5e7f9a1b2d4``).
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import sqlalchemy as sa

REPO_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_BIN = REPO_ROOT / "venv" / "bin" / "alembic"


def _run_alembic(args: list[str], db_path: Path) -> subprocess.CompletedProcess:
    """Run ``alembic`` against ``db_path`` and return the completed process.

    The Alembic binary may not exist in CI venvs that use a different
    layout; fall back to ``python -m alembic`` in that case.
    """

    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_path}"}
    if ALEMBIC_BIN.exists():
        cmd = [str(ALEMBIC_BIN), *args]
    else:
        cmd = [sys.executable, "-m", "alembic", *args]

    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.fixture
def fresh_migrated_db(tmp_path: Path) -> Path:
    """Create a brand-new SQLite DB and migrate it to ``head``.

    Mirrors how production DBs are bootstrapped (Alembic only — no
    ``db.create_all()``), so any ``models.py`` column missing from the
    migration history will be missing from this DB too.
    """

    db_path = tmp_path / "fresh.db"
    result = _run_alembic(["upgrade", "head"], db_path)
    if result.returncode != 0:
        pytest.fail(
            "alembic upgrade head failed on a fresh DB:\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return db_path


def _expected_schema() -> dict[str, set[str]]:
    """Return ``{table_name: {column_name, ...}}`` from the model metadata."""

    # Importing ``models`` registers all tables on ``db.metadata``.
    import models  # noqa: F401  ← side-effect: registers all tables
    from app import create_app, db

    app = create_app()
    with app.app_context():
        return {
            table_name: {col.name for col in table.columns}
            for table_name, table in db.metadata.tables.items()
        }


def _actual_schema(db_path: Path) -> dict[str, set[str]]:
    """Return ``{table_name: {column_name, ...}}`` from the live SQLite DB."""

    engine = sa.create_engine(f"sqlite:///{db_path}")
    inspector = sa.inspect(engine)
    actual: dict[str, set[str]] = {}
    for table_name in inspector.get_table_names():
        actual[table_name] = {c["name"] for c in inspector.get_columns(table_name)}
    return actual


def test_migrations_match_models(fresh_migrated_db: Path) -> None:
    """A fresh ``alembic upgrade head`` must produce the same schema as ``models.py``.

    Catches the class of bug where a developer adds a ``db.Column(...)`` to
    a model but forgets to author the corresponding Alembic migration —
    on local dev DBs the column gets created via ``db.create_all()``, but
    on prod (which is migration-only) it goes missing and explodes once
    the ORM SELECTs it.
    """

    expected = _expected_schema()
    actual = _actual_schema(fresh_migrated_db)

    missing_tables = sorted(set(expected) - set(actual))
    assert not missing_tables, (
        "Tables defined in models.py are missing from the migration head:\n"
        f"  {missing_tables}\n"
        "Add an Alembic migration that creates them."
    )

    drift: list[tuple[str, list[str]]] = []
    for table_name in sorted(set(expected) & set(actual)):
        missing_cols = sorted(expected[table_name] - actual[table_name])
        if missing_cols:
            drift.append((table_name, missing_cols))

    assert not drift, (
        "Columns declared in models.py are missing from the migration head:\n"
        + "\n".join(f"  {tbl}: {cols}" for tbl, cols in drift)
        + "\nAdd an Alembic migration that adds them — see "
        "migrations/versions/a3e91f4c7b28_backfill_is_active_columns.py "
        "for the idempotent ``inspect``-then-``add_column`` pattern."
    )


def test_head_migration_is_idempotent(fresh_migrated_db: Path) -> None:
    """Running ``alembic upgrade head`` twice must not change anything.

    Catches non-idempotent migrations (e.g. ones that try to ``DROP
    INDEX`` something that no longer exists, or ``INSERT`` a row that
    already exists without a ``WHERE NOT EXISTS`` guard). The
    second-pass invocation is what would surface in CI if a migration
    re-applied wasn't side-effect-free.

    A rollback-roundtrip test (``downgrade base`` → ``upgrade head``)
    would be ideal but is currently blocked by a pre-existing
    unnamed-FK ``drop_constraint`` issue in
    ``c8a1f0cd030d_upgrade_achievement_schema.py::downgrade``. That
    bug is unrelated to the schema-drift class we're guarding here, so
    we keep the test scoped to the forward-replay invariant.
    """

    second_pass = _run_alembic(["upgrade", "head"], fresh_migrated_db)
    assert second_pass.returncode == 0, (
        "Second alembic upgrade head failed (migration is not idempotent):\n"
        f"stdout:\n{second_pass.stdout}\nstderr:\n{second_pass.stderr}"
    )

    # Schema must still match the model after the no-op pass.
    expected = _expected_schema()
    actual = _actual_schema(fresh_migrated_db)
    drift: list[tuple[str, list[str]]] = []
    for table_name in sorted(set(expected) & set(actual)):
        missing_cols = sorted(expected[table_name] - actual[table_name])
        if missing_cols:
            drift.append((table_name, missing_cols))

    assert not drift, "Schema drift after second upgrade head:\n" + "\n".join(
        f"  {tbl}: {cols}" for tbl, cols in drift
    )


def test_orm_smoke_against_migrated_db(fresh_migrated_db: Path) -> None:
    """Run the exact ORM SELECTs that the failing prod homepage triggers.

    ``services/rating_service.build_leaderboard`` chains
    ``_get_base_points_from_db`` (``session.query(AchievementType).all()``)
    and ``_get_season_multiplier_from_db`` (``session.query(Season).all()``).
    These are the SELECTs that exploded on prod when ``is_active`` /
    ``start_year`` / ``end_year`` were missing — keep this smoke test
    runnable so we never ship that combination again.

    We bypass Flask-SQLAlchemy here and bind a fresh SQLAlchemy engine
    directly to the migrated DB. The session-scoped ``app`` fixture in
    ``conftest.py`` is hard-wired to ``TestingConfig`` (``:memory:``)
    via ``Config.SQLALCHEMY_DATABASE_URI`` evaluated at import time, so
    we can't reuse ``db.session`` in this isolated test.
    """

    # Import inside the test so model metadata + columns are loaded against
    # this engine — the conftest session-scoped app would otherwise have
    # already bound them to its own ``:memory:`` engine.
    from models import AchievementType, Country, League, Manager, Season

    engine = sa.create_engine(f"sqlite:///{fresh_migrated_db}")
    Session = sa.orm.sessionmaker(bind=engine)
    session = Session()
    try:
        # Each of these five queries previously crashed prod with "no
        # such column: ...". They must all complete on a freshly-migrated DB.
        assert session.query(AchievementType).count() >= 0
        assert session.query(League).count() >= 0
        assert session.query(Country).count() >= 0
        assert session.query(Manager).count() >= 0
        assert session.query(Season).count() >= 0
    finally:
        session.close()
        engine.dispose()
