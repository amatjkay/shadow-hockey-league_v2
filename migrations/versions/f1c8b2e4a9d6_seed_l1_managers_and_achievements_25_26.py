"""seed_l1_managers_and_achievements_for_season_25_26

Idempotent data-only migration. Companion to ``c5e7f9a1b2d4``,
``d6f8a2b9c1e3``, and ``e7a9b3d5c2f1`` — completes the Season 25/26
backfill on already-initialised production / staging DBs by also
seeding **League 1** (Premier League) playoff results.

Background
----------
TIK-58 brought 25/26 results in waves:

1.  ``c5e7f9a1b2d4`` — subleagues ``2.1``/``2.2`` rows + ``Denis``→
    ``Denys`` rename.
2.  ``d6f8a2b9c1e3`` — 14 new managers + 9 League 2.2 achievements.
3.  ``e7a9b3d5c2f1`` — 4 new managers + 9 League 2.1 achievements.
4.  **This migration** — 3 more new managers + 9 League 1 achievements
    (TOP1 / TOP2 / TOP3 + R3 + BEST + 4 × R1).

``seed_db.py`` is safe-mode by default, so the JSON-only changes
introduced together with this migration never reach an already-running
DB. All inserts use ``INSERT ... SELECT ... WHERE NOT EXISTS`` against
``managers.name`` UNIQUE and ``uq_achievement_manager_league_season_type``
— safe to re-run.

Scoring notes
-------------
- League ``1`` is a top-level league (``parent_code = NULL``), so
  achievements use ``base_points_l1``: TOP1=800, TOP2=400, TOP3=200,
  BEST=200, R3=100, R1=50.
- Season ``25/26`` multiplier = ``1.0`` (active season), so
  ``final_points == base_points`` for every row.
- The SQLAlchemy ``before_insert`` listener in
  ``services/rating_service.py`` does not fire on raw ``op.execute()``,
  so all three computed columns are set explicitly here.

Admin observers
---------------
``whiplash 92`` and ``AleX TiiKii`` each play **solo** in League 1
this season — ``whiplash 92`` won the championship with Ryazan Jerks
(TOP1) and ``AleX TiiKii`` lost the 3rd-place game with Yaroslavl
Thunderstorm (R3). Per the ``data/admin_observers.py`` rule, solo
observer rows are accepted unconditionally — the validator only
rejects ``Tandem: ..., <observer>`` records that are not in the
explicit allowlist. No carve-out is needed in this migration.

Revision ID: f1c8b2e4a9d6
Revises: e7a9b3d5c2f1
Create Date: 2026-05-05 09:55:00.000000
"""

from typing import Sequence, Union

from alembic import op

revision: str = "f1c8b2e4a9d6"
down_revision: Union[str, None] = "e7a9b3d5c2f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# 3 new managers introduced together with the L1 25/26 results.
# All RUS by default; spelling kept verbatim from the league's
# scoreboard / standings screenshots (Cyrillic preserved where shown).
NEW_MANAGERS_RUS: tuple[str, ...] = (
    "Е. Медведев",
    "V. Shamanov",
    "N. Yessengaliev",
)


# 9 achievements for Season 25/26 / League 1.
# Tuple shape: (manager_name, type_code, base_points, title, icon_filename).
# Achievement-type codes are the *normalised* DB codes, not the JSON
# legacy aliases (BEST_REG → BEST, HOCKEY_STICKS_AND_PUCK → R3/R1).
NEW_ACHIEVEMENTS_L1_25_26: tuple[tuple[str, str, int, str, str], ...] = (
    # CHAMPIONSHIP: Ryazan Jerks > Yoze's Burger
    ("whiplash 92", "TOP1", 800, "TOP1", "top1.svg"),
    ("Yoze Marino", "TOP2", 400, "TOP2", "top2.svg"),
    # 3RD PLACE GAME: Sinichki > Yaroslavl Thunderstorm
    ("Е. Медведев", "TOP3", 200, "TOP3", "top3.svg"),
    ("AleX TiiKii", "R3", 100, "Round 3", "hockey-sticks-and-puck.svg"),
    # Best regular season: Sinichki / Е. Медведев (.684, ranked #1 with `*-`).
    ("Е. Медведев", "BEST", 200, "Best regular", "best-reg.svg"),
    # 5TH/7TH PLACE GAMES → 4 × R1 (round-1 playoff losers).
    ("Feel Good", "R1", 50, "Round 1", "hockey-sticks-and-puck.svg"),
    ("V. Shamanov", "R1", 50, "Round 1", "hockey-sticks-and-puck.svg"),
    ("N. Yessengaliev", "R1", 50, "Round 1", "hockey-sticks-and-puck.svg"),
    ("Павел Роевнев", "R1", 50, "Round 1", "hockey-sticks-and-puck.svg"),
)


def _esc(value: str) -> str:
    """Escape a single-quoted SQL literal (SQLite- and Postgres-compatible)."""

    return value.replace("'", "''")


def upgrade() -> None:
    # 1. Insert 3 new managers (idempotent: skip rows already present by name).
    #    ``country_id`` resolved through subquery; the WHERE-EXISTS guard
    #    prevents the NOT NULL FK from triggering on a corrupt DB without
    #    the RUS row.
    for name in NEW_MANAGERS_RUS:
        op.execute(f"""
            INSERT INTO managers (name, country_id, is_active)
            SELECT '{_esc(name)}',
                   (SELECT id FROM countries WHERE code = 'RUS'),
                   1
            WHERE NOT EXISTS (SELECT 1 FROM managers WHERE name = '{_esc(name)}')
              AND EXISTS (SELECT 1 FROM countries WHERE code = 'RUS')
            """)

    # 2. Insert 9 new achievements for Season 25/26 / League 1.
    #    Idempotent via the existing
    #    uq_achievement_manager_league_season_type unique constraint.
    #    base_points / multiplier / final_points pre-computed (see module
    #    docstring); SQLAlchemy event listeners do not fire on raw SQL.
    #    created_at / updated_at fall back to their server_default = now().
    for manager_name, type_code, base_points, title, icon in NEW_ACHIEVEMENTS_L1_25_26:
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
              AND l.code = '1'
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
    # Reverse achievements first (FK ON DELETE CASCADE — explicit delete
    # keeps the audit trail clean and avoids removing managers that still
    # own historical achievements).
    for manager_name, type_code, _base, _title, _icon in NEW_ACHIEVEMENTS_L1_25_26:
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
                  AND l.code = '1'
                  AND s.code = '25/26'
            )
            """)

    # Then the 3 managers, but only if they have no remaining achievements
    # (defensive: production may have manually added rows that reference
    # them — never silently drop those).
    for name in NEW_MANAGERS_RUS:
        op.execute(f"""
            DELETE FROM managers
            WHERE name = '{_esc(name)}'
              AND id NOT IN (SELECT DISTINCT manager_id FROM achievements)
            """)
