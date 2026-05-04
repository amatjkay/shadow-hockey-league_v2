"""seed_subleagues_2_1_and_2_2_and_rename_denis_to_denys

Idempotent data-only migration. Two purposes:

1. Insert reference rows for subleagues ``2.1`` and ``2.2`` (parent code ``"2"``)
   into the ``leagues`` table.  Migration ``8a3279741758`` only added the
   ``parent_code`` column; the rows themselves were never seeded by Alembic.
   ``data/seed_service.py::_seed_reference_data`` now seeds them on a fresh
   DB, but already-initialised production / staging DBs need this data
   migration to backfill.

2. Rename existing manager ``Denis Sanzharevskyi`` → ``Denys Sanzharevskyi``
   (correct spelling per league owner). FK ``manager_id`` on achievements
   keeps the historical record attached to the renamed row.

Both operations use ``INSERT ... WHERE NOT EXISTS`` / ``UPDATE ... WHERE``
predicates so the migration is safe to re-run.

Revision ID: c5e7f9a1b2d4
Revises: 9a30d278d31d
Create Date: 2026-05-04 21:30:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "c5e7f9a1b2d4"
down_revision: Union[str, None] = "9a30d278d31d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Seed subleagues 2.1 and 2.2 (idempotent — skip rows that already exist).
    op.execute("""
        INSERT INTO leagues (code, name, parent_code, is_active)
        SELECT '2.1', 'League 2.1', '2', 1
        WHERE NOT EXISTS (SELECT 1 FROM leagues WHERE code = '2.1')
        """)
    op.execute("""
        INSERT INTO leagues (code, name, parent_code, is_active)
        SELECT '2.2', 'League 2.2', '2', 1
        WHERE NOT EXISTS (SELECT 1 FROM leagues WHERE code = '2.2')
        """)

    # 2. Rename Denis -> Denys Sanzharevskyi (idempotent — UPDATE-WHERE).
    #    FK on achievements.manager_id keeps historical achievements pointed
    #    at the renamed manager.
    op.execute("""
        UPDATE managers
        SET name = 'Denys Sanzharevskyi'
        WHERE name = 'Denis Sanzharevskyi'
        """)


def downgrade() -> None:
    # Reverse rename first (preserves FK integrity if rows exist).
    op.execute("""
        UPDATE managers
        SET name = 'Denis Sanzharevskyi'
        WHERE name = 'Denys Sanzharevskyi'
        """)

    # Remove subleagues only if no achievements reference them (avoid ON DELETE
    # cascading away production data on a downgrade).
    op.execute("""
        DELETE FROM leagues
        WHERE code IN ('2.1', '2.2')
          AND id NOT IN (SELECT DISTINCT league_id FROM achievements)
        """)
