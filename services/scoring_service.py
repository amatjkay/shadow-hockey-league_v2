"""League-aware helpers for computing achievement points.

The League hierarchy supports subleagues via ``League.parent_code`` (e.g.
``2.1`` and ``2.2`` are children of ``2``). Picking the right
``base_points_l1`` / ``base_points_l2`` column must therefore go through
``League.base_points_field`` — never via a direct ``league.code == '1'``
comparison, which silently miscounts any subleague: ``'2.1' != '1'`` so the
naive check would route subleague-2 achievements to ``base_points_l2``
"by accident" today, and would do the wrong thing the moment a hypothetical
subleague of L1 is added.

Putting this single helper in one place lets every caller —
``services.api``, ``services.rating_service``, ``services.admin``,
``blueprints.admin_api`` — share the same source of truth.
"""

from __future__ import annotations

from models import AchievementType, League


def get_base_points(ach_type: AchievementType, league: League) -> float:
    """Return the league-aware base points for an achievement_type/league pair.

    Reads ``League.base_points_field`` (which honours ``parent_code``) so a
    subleague like ``2.1`` correctly inherits ``base_points_l2`` from its
    parent, and a future subleague of L1 (should one ever be created) would
    inherit ``base_points_l1``.

    Args:
        ach_type: The achievement type carrying ``base_points_l1`` /
            ``base_points_l2`` columns.
        league: The league. Its ``base_points_field`` property is the
            authoritative selector.

    Returns:
        Base points as a ``float`` — callers historically multiply this by
        ``Season.multiplier`` (also a float) to get ``final_points``.
    """
    return float(getattr(ach_type, league.base_points_field))
