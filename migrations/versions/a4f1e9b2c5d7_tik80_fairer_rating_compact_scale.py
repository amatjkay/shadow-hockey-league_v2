"""tik80_fairer_rating_compact_scale

TIK-80: Recalibrate the rating system to a compact, fair scale.

Three coupled changes, applied as a single migration so the leaderboard
is never observed in a half-converted state:

1. **Column type widening.** ``achievement_types.base_points_l1`` and
   ``base_points_l2`` switch from ``Integer`` to ``Float``. The compact-10
   scale uses fractional values (``TOP3 L1 = 2.5``, ``BEST L2 = 1.8``,
   ``R1 L1 = 0.75``); rounding them to integers would collapse
   ``TOP3 == BEST`` and zero out ``R1 L2``.

2. **Base points UPDATE.** Six achievement-type rows are rewritten to the
   compact-10 scale:

   ===== ======= ======= =================================================
   code  L1      L2      rationale
   ===== ======= ======= =================================================
   TOP1  10.0    6.0     champion is the cap; L2 ≈ 60 % of L1
   TOP2  5.0     3.0
   TOP3  2.5     1.5     bronze ranks below regular-season MVP now
   BEST  3.0     1.8     full-season MVP > one bronze series
   R3    1.5     0.9
   R1    0.75    0.45    no longer "all or nothing" vs TOP1 (was 1/16)
   ===== ======= ======= =================================================

3. **Season multiplier UPDATE.** Five seasons are rewritten to a smooth
   exponential ``0.7 ^ years_ago`` curve (was hand-rolled with uneven
   −20 / −38 / −40 / −33 % year-on-year cliffs):

   ======= =============== ================================================
   code    multiplier      formula
   ======= =============== ================================================
   25/26   1.000           baseline (years_ago=0)
   24/25   0.700           0.7 ^ 1
   23/24   0.490           0.7 ^ 2
   22/23   0.343           0.7 ^ 3
   21/22   0.240           0.7 ^ 4
   ======= =============== ================================================

After the reference rows are rewritten, every existing
``achievements`` row is re-derived (``base_points``, ``multiplier``,
``final_points``) so the leaderboard reflects the new scale immediately.
The recalc honours ``League.parent_code`` so subleagues like ``2.1`` /
``2.2`` correctly inherit ``base_points_l2`` from their parent
(matches ``services.scoring_service.get_base_points``).

The downgrade restores the legacy hundreds scale and uneven decay,
again followed by a per-row recalc, so a roll-back is observable in the
same single atomic step.

Revision ID: a4f1e9b2c5d7
Revises: d8e4f3a2b9c0
Create Date: 2026-05-07 16:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a4f1e9b2c5d7"
down_revision: Union[str, None] = "d8e4f3a2b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---- Compact-10 scale (TIK-80) ----------------------------------------------
_NEW_BASE_POINTS: dict[str, tuple[float, float]] = {
    "TOP1": (10.0, 6.0),
    "TOP2": (5.0, 3.0),
    "TOP3": (2.5, 1.5),
    "BEST": (3.0, 1.8),
    "R3": (1.5, 0.9),
    "R1": (0.75, 0.45),
}

# 0.7 ^ years_ago, rounded to 3 decimals so the DB row matches the seed
# constants verbatim (no floating-point drift between fresh installs and
# upgraded ones).
_NEW_SEASON_MULTIPLIERS: dict[str, float] = {
    "25/26": 1.000,
    "24/25": 0.700,
    "23/24": 0.490,
    "22/23": 0.343,
    "21/22": 0.240,
}

# ---- Legacy values (used by downgrade) --------------------------------------
_OLD_BASE_POINTS: dict[str, tuple[int, int]] = {
    "TOP1": (800, 400),
    "TOP2": (400, 200),
    "TOP3": (200, 100),
    "BEST": (200, 100),
    "R3": (100, 50),
    "R1": (50, 25),
}

_OLD_SEASON_MULTIPLIERS: dict[str, float] = {
    "25/26": 1.00,
    "24/25": 0.80,
    "23/24": 0.50,
    "22/23": 0.30,
    "21/22": 0.20,
}


def _resolve_root_code(parent_code: Union[str, None], code: str) -> str:
    """Mirror of :py:meth:`models.League.base_points_field` selection.

    Subleagues (``2.1`` / ``2.2``) carry ``parent_code='2'`` so they must
    pick ``base_points_l2``. The previous implementation compared
    ``league.code == '1'`` directly and silently misrouted subleagues.
    """

    return parent_code or code


def _recalc_all_achievements(bind: sa.engine.Connection) -> None:
    """Re-derive ``base_points``, ``multiplier``, ``final_points`` for every row.

    Reads the freshly-written reference tables and walks every
    ``achievements`` row in chunks. We avoid loading the ORM (the model
    metadata is migration-time, not runtime) and stick to raw SQL so the
    upgrade is independent of model evolution.
    """

    # 1. Build (type_id -> (l1, l2)) and (league_id -> root_code) maps.
    types_map: dict[int, tuple[float, float]] = {}
    for row in bind.execute(
        sa.text("SELECT id, base_points_l1, base_points_l2 FROM achievement_types")
    ).fetchall():
        type_id, l1, l2 = row
        types_map[type_id] = (float(l1 or 0.0), float(l2 or 0.0))

    leagues_map: dict[int, str] = {}
    for row in bind.execute(sa.text("SELECT id, code, parent_code FROM leagues")).fetchall():
        league_id, code, parent_code = row
        leagues_map[league_id] = _resolve_root_code(parent_code, code)

    seasons_map: dict[int, float] = {}
    for row in bind.execute(sa.text("SELECT id, multiplier FROM seasons")).fetchall():
        season_id, multiplier = row
        seasons_map[season_id] = float(multiplier or 0.0)

    # 2. Walk every achievement and rewrite the three derived columns.
    achievements = bind.execute(
        sa.text("SELECT id, type_id, league_id, season_id FROM achievements")
    ).fetchall()

    for ach_id, type_id, league_id, season_id in achievements:
        l1_l2 = types_map.get(type_id)
        root_code = leagues_map.get(league_id)
        multiplier = seasons_map.get(season_id)

        if l1_l2 is None or root_code is None or multiplier is None:
            # Orphaned achievement (FK to a deleted reference row). Leave
            # the existing values alone — admin tooling will surface it
            # via the audit log.
            continue

        l1, l2 = l1_l2
        base_points = l1 if root_code == "1" else l2
        final_points = round(base_points * multiplier, 2)

        bind.execute(
            sa.text(
                "UPDATE achievements SET base_points = :base, "
                "multiplier = :mul, final_points = :final WHERE id = :id"
            ),
            {
                "base": base_points,
                "mul": multiplier,
                "final": final_points,
                "id": ach_id,
            },
        )


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Widen ``base_points_l1`` / ``_l2`` to ``Float`` so 2.5 / 1.8 / 0.75
    #    round-trip without truncation. Wrapped in ``batch_alter_table`` for
    #    SQLite (matches the pattern used by 8a3279741758 and friends).
    with op.batch_alter_table("achievement_types", schema=None) as batch_op:
        batch_op.alter_column(
            "base_points_l1",
            existing_type=sa.Integer(),
            type_=sa.Float(),
            existing_nullable=False,
            existing_server_default=sa.text("0"),
        )
        batch_op.alter_column(
            "base_points_l2",
            existing_type=sa.Integer(),
            type_=sa.Float(),
            existing_nullable=False,
            existing_server_default=sa.text("0"),
        )

    # 2. UPDATE achievement_types with compact-10 base points.
    for code, (l1, l2) in _NEW_BASE_POINTS.items():
        bind.execute(
            sa.text(
                "UPDATE achievement_types SET base_points_l1 = :l1, "
                "base_points_l2 = :l2 WHERE code = :code"
            ),
            {"l1": l1, "l2": l2, "code": code},
        )

    # 3. UPDATE seasons with 0.7^years_ago multipliers.
    for code, mult in _NEW_SEASON_MULTIPLIERS.items():
        bind.execute(
            sa.text("UPDATE seasons SET multiplier = :mult WHERE code = :code"),
            {"mult": mult, "code": code},
        )

    # 4. Re-derive every achievement so the leaderboard never shows the
    #    half-converted state where reference data is new but stored
    #    points are stale.
    _recalc_all_achievements(bind)


def downgrade() -> None:
    bind = op.get_bind()

    # Restore legacy hundreds-scale base points.
    for code, (l1, l2) in _OLD_BASE_POINTS.items():
        bind.execute(
            sa.text(
                "UPDATE achievement_types SET base_points_l1 = :l1, "
                "base_points_l2 = :l2 WHERE code = :code"
            ),
            {"l1": float(l1), "l2": float(l2), "code": code},
        )

    # Restore the legacy hand-rolled multiplier curve.
    for code, mult in _OLD_SEASON_MULTIPLIERS.items():
        bind.execute(
            sa.text("UPDATE seasons SET multiplier = :mult WHERE code = :code"),
            {"mult": mult, "code": code},
        )

    # Recalc against the legacy reference values before narrowing the
    # column type so we don't lose decimals on the reverse path.
    _recalc_all_achievements(bind)

    # Narrow the column type back to Integer. Existing rows are now
    # whole numbers (800 / 400 / …) and survive the cast losslessly.
    with op.batch_alter_table("achievement_types", schema=None) as batch_op:
        batch_op.alter_column(
            "base_points_l2",
            existing_type=sa.Float(),
            type_=sa.Integer(),
            existing_nullable=False,
            existing_server_default=sa.text("0"),
        )
        batch_op.alter_column(
            "base_points_l1",
            existing_type=sa.Float(),
            type_=sa.Integer(),
            existing_nullable=False,
            existing_server_default=sa.text("0"),
        )
