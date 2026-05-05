"""backfill_missing_schema_columns

Idempotent schema-fix migration. Brings already-initialised DBs in line
with the SQLAlchemy model definitions on the four reference tables:

- ``achievement_types`` / ``leagues`` / ``countries`` / ``managers``: each
  has an ``is_active`` ``Boolean`` column in ``models.py`` but it was
  never added by any previous Alembic migration.
- ``seasons``: ``start_year`` / ``end_year`` ``Integer`` columns are
  defined on the model but were also missing from the migration history.

Background
----------
The model has had ``is_active`` on these four tables for a long time;
``seasons`` got the column in ``b2c3d4e5f6a7_add_reference_tables.py``
but the other four were never backfilled. DBs that were initialised
through ``db.create_all()`` (most local dev environments) already have
the columns from the SQLAlchemy metadata. DBs initialised exclusively
through Alembic (production) were missing them, which only became a
hard 500 once the leaderboard cache was invalidated and
``services/rating_service._get_base_points_from_db`` issued
``session.query(AchievementType).all()`` — the ORM SELECT references
``is_active`` and SQLite raised
``sqlite3.OperationalError: no such column: achievement_types.is_active``.
``seasons.start_year`` / ``end_year`` are referenced by
``services/rating_service._get_season_multiplier_from_db`` along the
exact same code path, so they need the same treatment.

Approach
--------
Detect the current column set with ``sa.inspect(bind)`` *before* trying
to add anything; if the column is already present we skip. This makes
the migration safe to run on:

- dev.db / local DBs initialised via ``db.create_all()`` (column already
  there → skip);
- prod / staging DBs initialised exclusively via Alembic (column missing
  → add it);
- DBs that have already been hot-fixed manually (column already there
  → skip).

For SQLite we use ``with op.batch_alter_table(...)`` per table — the
column add is rewritten as ``CREATE TABLE new ... INSERT INTO new SELECT
... FROM old`` automatically. For Postgres / other dialects we use the
plain ``op.add_column``.

Defaults
--------
- ``is_active`` columns get ``server_default='1'`` so existing rows are
  treated as active; this matches the application's default = True and
  how every code path before this fix already assumed those rows were
  active. Boolean is stored as 0/1 on SQLite, hence the literal ``'1'``.
- ``start_year`` / ``end_year`` are nullable Integers with no
  ``server_default`` — they're only used for display, and ``NULL`` is
  the existing implicit value for legacy seasons.

Revision ID: a3e91f4c7b28
Revises: f1c8b2e4a9d6
Create Date: 2026-05-05 10:25:00.000000
"""

from dataclasses import dataclass
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3e91f4c7b28"
down_revision: Union[str, None] = "f1c8b2e4a9d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


@dataclass(frozen=True)
class _MissingColumn:
    """A single ``(table, column, type, server_default)`` to backfill."""

    table: str
    column: str
    sa_type: type[sa.types.TypeEngine]  # type: ignore[type-arg]
    nullable: bool
    server_default: str | None


# Columns that drifted out of the migration history. We detect each one
# at runtime with ``sa.inspect()``: the same migration is therefore safe
# to run on dev.db (rows already exist via ``db.create_all()`` → skip)
# and on prod (column missing → add it with the correct default).
TARGET_COLUMNS: tuple[_MissingColumn, ...] = (
    _MissingColumn("achievement_types", "is_active", sa.Boolean, False, "1"),
    _MissingColumn("leagues", "is_active", sa.Boolean, False, "1"),
    _MissingColumn("countries", "is_active", sa.Boolean, False, "1"),
    _MissingColumn("managers", "is_active", sa.Boolean, False, "1"),
    _MissingColumn("seasons", "start_year", sa.Integer, True, None),
    _MissingColumn("seasons", "end_year", sa.Integer, True, None),
)


def _has_column(inspector: sa.Inspector, table: str, column: str) -> bool:
    """Return True if ``table`` already has ``column`` according to ``inspector``."""

    return any(c["name"] == column for c in inspector.get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    dialect = bind.dialect.name

    for spec in TARGET_COLUMNS:
        if _has_column(inspector, spec.table, spec.column):
            # Column is already present (dev.db via db.create_all() or a
            # previously hot-fixed prod). Nothing to do.
            continue

        new_column = sa.Column(
            spec.column,
            spec.sa_type(),
            nullable=spec.nullable,
            server_default=spec.server_default,
        )

        if dialect == "sqlite":
            with op.batch_alter_table(spec.table) as batch_op:
                batch_op.add_column(new_column)
        else:
            op.add_column(spec.table, new_column)


def downgrade() -> None:
    # Defensive: only drop columns we actually have. Symmetrical with
    # upgrade() — a no-op on DBs that already lacked the column.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    dialect = bind.dialect.name

    for spec in reversed(TARGET_COLUMNS):
        if not _has_column(inspector, spec.table, spec.column):
            continue

        if dialect == "sqlite":
            with op.batch_alter_table(spec.table) as batch_op:
                batch_op.drop_column(spec.column)
        else:
            op.drop_column(spec.table, spec.column)
