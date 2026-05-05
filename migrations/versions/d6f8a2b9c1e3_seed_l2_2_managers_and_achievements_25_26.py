"""seed_l2_2_managers_and_achievements_for_season_25_26

Idempotent data-only migration. Companion to ``c5e7f9a1b2d4``.

Background
----------
PR #65 / TIK-58 added the Season 25/26 League 2.2 results in two places:

1.  Subleagues ``2.1``/``2.2`` rows + ``Denis``→``Denys`` rename — backfilled
    by ``c5e7f9a1b2d4`` for already-initialised production / staging DBs.
2.  14 new managers + 9 new achievements (TIK-58 commit ``d470f13``)
    appended to ``data/seed/managers.json`` and ``data/seed/achievements.json``.

``seed_db.py`` is **safe-mode by default** — it skips seeding once any
manager exists, so the JSON-only changes never reach an already-running
prod DB. This migration backfills the same rows so prod matches the seed
JSON without a destructive ``--force`` reseed.

All inserts use ``INSERT ... SELECT ... WHERE NOT EXISTS`` against the
existing unique constraints (``managers.name`` UNIQUE,
``uq_achievement_manager_league_season_type``), so the migration is safe
to re-run.

The achievements rows have to set ``base_points`` / ``multiplier`` /
``final_points`` explicitly: SQLAlchemy's ``before_insert`` listener in
``services/rating_service.py`` only fires for ORM-level inserts, not for
Alembic raw-SQL ``op.execute()``. All 9 rows are League 2.2 (parent ``2``
→ ``base_points_l2``) × Season 25/26 (multiplier 1.0), so the computed
columns are known statically and match what ``recalc_service`` /
``rating_service`` would produce.

Revision ID: d6f8a2b9c1e3
Revises: c5e7f9a1b2d4
Create Date: 2026-05-05 08:10:00.000000
"""

from typing import Sequence, Union

from alembic import op

revision: str = "d6f8a2b9c1e3"
down_revision: Union[str, None] = "c5e7f9a1b2d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# 14 new managers added in TIK-58 (commit d470f13). All RUS-flagged.
NEW_MANAGERS_RUS: tuple[str, ...] = (
    "Aliaksandr Naidzionau",
    "Ruslan Ivanov",
    "Konstantin Rumyantsev",
    "Mike B",
    "Igor Deryabin",
    "Max Domchev",
    "Filipp M.",
    "Andrey Rumiantsev",
    "Maksim V",
    "Sergey Aksentyev",
    "Alexey Garnov",
    "Sergey Bulgakov",
    "Dmitry Koblev",
    "Alex Polishchuk",
)


# 9 new achievements added in TIK-58 (commit d470f13).
# League 2.2 (parent_code='2' → base_points_l2) × Season 25/26 (multiplier 1.0)
# so final_points == base_points for every row.
#
# Tuple shape: (manager_name, type_code, base_points, title, icon_filename)
NEW_ACHIEVEMENTS_L2_2_25_26: tuple[tuple[str, str, int, str, str], ...] = (
    ("Aliaksandr Naidzionau", "TOP1", 400, "TOP1", "top1.svg"),
    ("Aliaksandr Naidzionau", "BEST", 100, "Best regular", "best-reg.svg"),
    ("Denys Sanzharevskyi", "TOP2", 200, "TOP2", "top2.svg"),
    ("Ruslan Ivanov", "TOP3", 100, "TOP3", "top3.svg"),
    ("Konstantin Rumyantsev", "R3", 50, "Round 3", "hockey-sticks-and-puck.svg"),
    ("Mike B", "R1", 25, "Round 1", "hockey-sticks-and-puck.svg"),
    ("Igor Deryabin", "R1", 25, "Round 1", "hockey-sticks-and-puck.svg"),
    ("Max Domchev", "R1", 25, "Round 1", "hockey-sticks-and-puck.svg"),
    ("Sousse Sousse", "R1", 25, "Round 1", "hockey-sticks-and-puck.svg"),
)


def _esc(value: str) -> str:
    """Escape a single-quoted SQL literal (SQLite-compatible)."""

    return value.replace("'", "''")


def upgrade() -> None:
    # 1. Insert 14 new managers (idempotent: skip rows already present by name).
    #    country_id resolved through subquery; if RUS is missing the INSERT
    #    becomes a no-op rather than crashing (managers.country_id is NOT NULL,
    #    but the WHERE-EXISTS guard prevents reaching that path on a corrupt
    #    DB).
    for name in NEW_MANAGERS_RUS:
        op.execute(f"""
            INSERT INTO managers (name, country_id, is_active)
            SELECT '{_esc(name)}',
                   (SELECT id FROM countries WHERE code = 'RUS'),
                   1
            WHERE NOT EXISTS (SELECT 1 FROM managers WHERE name = '{_esc(name)}')
              AND EXISTS (SELECT 1 FROM countries WHERE code = 'RUS')
            """)

    # 2. Insert 9 new achievements for Season 25/26 / League 2.2.
    #    Idempotent via the existing
    #    uq_achievement_manager_league_season_type unique constraint.
    #    base_points / multiplier / final_points pre-computed (see module
    #    docstring); SQLAlchemy event listeners do not fire on raw SQL.
    #    created_at / updated_at fall back to their server_default = now().
    for manager_name, type_code, base_points, title, icon in NEW_ACHIEVEMENTS_L2_2_25_26:
        icon_path = f"/static/img/cups/{icon}"
        op.execute(f"""
            INSERT INTO achievements (
                manager_id, type_id, league_id, season_id,
                base_points, multiplier, final_points,
                title, icon_path
            )
            SELECT
                m.id, t.id, l.id, s.id,
                {base_points}, 1.0, {base_points},
                '{_esc(title)}', '{_esc(icon_path)}'
            FROM managers m, achievement_types t, leagues l, seasons s
            WHERE m.name = '{_esc(manager_name)}'
              AND t.code = '{type_code}'
              AND l.code = '2.2'
              AND s.code = '25/26'
              AND NOT EXISTS (
                  SELECT 1 FROM achievements a
                  WHERE a.manager_id = m.id
                    AND a.type_id    = t.id
                    AND a.league_id  = l.id
                    AND a.season_id  = s.id
              )
            """)


def downgrade() -> None:
    # Reverse achievements first (FK manager_id ON DELETE CASCADE — explicit
    # delete keeps the audit trail clean and avoids removing managers that
    # still own historical achievements).
    for manager_name, type_code, _base, _title, _icon in NEW_ACHIEVEMENTS_L2_2_25_26:
        op.execute(f"""
            DELETE FROM achievements
            WHERE id IN (
                SELECT a.id FROM achievements a
                JOIN managers m         ON a.manager_id = m.id
                JOIN achievement_types t ON a.type_id   = t.id
                JOIN leagues l           ON a.league_id = l.id
                JOIN seasons s           ON a.season_id = s.id
                WHERE m.name = '{_esc(manager_name)}'
                  AND t.code = '{type_code}'
                  AND l.code = '2.2'
                  AND s.code = '25/26'
            )
            """)

    # Then the 14 managers, but only if they have no remaining achievements
    # (defensive: production may have manually added rows that reference
    # them — never silently drop those).
    for name in NEW_MANAGERS_RUS:
        op.execute(f"""
            DELETE FROM managers
            WHERE name = '{_esc(name)}'
              AND id NOT IN (SELECT DISTINCT manager_id FROM achievements)
            """)
