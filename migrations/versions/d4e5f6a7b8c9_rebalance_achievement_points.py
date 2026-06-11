"""Rebalance achievement points — ADR-006: consistent 2:1 L1:L2.

Overrides the TIK-80 compact-10 scale with a principled int-based system:
  - L1:L2 = 2:1 for ALL achievement types (was: inconsistent ratios)
  - TOP1 = 1000/500 (was TIK-80 10.0/6.0)
  - TOP2 = 600/300  (was TIK-80 5.0/3.0)
  - TOP3 = 400/200  (was TIK-80 2.5/1.5)
  - BEST = 200/100  (was TIK-80 3.0/1.8)
  - R3   = 150/75   (was TIK-80 1.5/0.9)
  - R1   = 80/40    (was TIK-80 0.75/0.45)

Season multipliers are unchanged from TIK-80 (0.7 ^ years_ago).
Existing achievements are recalculated automatically.

Revision ID: d4e5f6a7b8c9
Revises: 3f6f9ed6c154
Create Date: 2026-06-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "3f6f9ed6c154"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ADR-006 values (int-based, consistent 2:1 L1:L2)
_NEW_BASE_POINTS: dict[str, tuple[int, int]] = {
    "TOP1": (1000, 500),
    "TOP2": (600, 300),
    "TOP3": (400, 200),
    "BEST": (200, 100),
    "R3": (150, 75),
    "R1": (80, 40),
}

# TIK-80 compact-10 values (for downgrade)
_TIK80_BASE_POINTS: dict[str, tuple[float, float]] = {
    "TOP1": (10.0, 6.0),
    "TOP2": (5.0, 3.0),
    "TOP3": (2.5, 1.5),
    "BEST": (3.0, 1.8),
    "R3": (1.5, 0.9),
    "R1": (0.75, 0.45),
}


def _recalc_all_achievements(bind: sa.engine.Connection) -> None:
    """Re-derive base_points, multiplier, final_points for every row."""
    types_map: dict[int, tuple[float, float]] = {}
    for row in bind.execute(
        sa.text("SELECT id, base_points_l1, base_points_l2 FROM achievement_types")
    ).fetchall():
        type_id, l1, l2 = row
        types_map[type_id] = (float(l1 or 0.0), float(l2 or 0.0))

    leagues_map: dict[int, str] = {}
    for row in bind.execute(sa.text("SELECT id, code, parent_code FROM leagues")).fetchall():
        league_id, code, parent_code = row
        leagues_map[league_id] = parent_code or code

    seasons_map: dict[int, float] = {}
    for row in bind.execute(sa.text("SELECT id, multiplier FROM seasons")).fetchall():
        season_id, multiplier = row
        seasons_map[season_id] = float(multiplier or 0.0)

    for ach_id, type_id, league_id, season_id in bind.execute(
        sa.text("SELECT id, type_id, league_id, season_id FROM achievements")
    ).fetchall():
        l1_l2 = types_map.get(type_id)
        root_code = leagues_map.get(league_id)
        multiplier = seasons_map.get(season_id)

        if l1_l2 is None or root_code is None or multiplier is None:
            continue

        l1, l2 = l1_l2
        base_points = l1 if root_code == "1" else l2
        final_points = round(base_points * multiplier, 2)

        bind.execute(
            sa.text(
                "UPDATE achievements SET base_points = :base, "
                "multiplier = :mul, final_points = :final WHERE id = :id"
            ),
            {"base": base_points, "mul": multiplier, "final": final_points, "id": ach_id},
        )


def upgrade() -> None:
    bind = op.get_bind()

    for code, (l1, l2) in _NEW_BASE_POINTS.items():
        bind.execute(
            sa.text(
                "UPDATE achievement_types SET base_points_l1 = :l1, "
                "base_points_l2 = :l2 WHERE code = :code"
            ),
            {"l1": float(l1), "l2": float(l2), "code": code},
        )

    _recalc_all_achievements(bind)


def downgrade() -> None:
    bind = op.get_bind()

    # Restore TIK-80 compact-10 values (what was in place before this migration)
    for code, (l1, l2) in _TIK80_BASE_POINTS.items():
        bind.execute(
            sa.text(
                "UPDATE achievement_types SET base_points_l1 = :l1, "
                "base_points_l2 = :l2 WHERE code = :code"
            ),
            {"l1": l1, "l2": l2, "code": code},
        )

    _recalc_all_achievements(bind)
