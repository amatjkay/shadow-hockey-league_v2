"""Rating service for calculating manager rankings.

This module provides functions to calculate manager ratings based on their
achievements stored in the database. Points are calculated as:
    base_points(league, achievement_type) × season_multiplier

Base points and season multipliers are read from reference tables in the database.
Fallback to hardcoded values if reference tables are empty (backward compatibility).

The rating is used to build the leaderboard displayed on the main page.
"""

from __future__ import annotations

from typing import Any, cast

from sqlalchemy.orm import joinedload

from models import Achievement, AchievementType, League, Manager, Season
from services._types import SessionLike
from services.scoring_service import get_base_points

# ==================== Fallback constants (used if reference tables are empty) ====================

# Base points for each league and achievement type combination (TIK-80).
#
# Compact-10 scale: TOP1 L1 = 10.0 is the cap, all other values are scaled
# down proportionally. The scale stays in single-/low-double digits so the
# leaderboard is easy to read (champion ≈ 20, not 1635).
#
# League 2 = ~60 % of League 1 (was 50 %): hard 2× ratio overstated the gap
# between divisions. Subleagues 2.1 / 2.2 inherit L2 values via
# ``League.parent_code`` — see ``services/scoring_service.get_base_points``.
#
# ``BEST > TOP3`` (was equal): regular-season MVP outranks one playoff bronze
# series.
BASE_POINTS: dict[tuple[str, str], float] = {
    # League 1 - Elite division
    ("1", "TOP1"): 10.0,
    ("1", "TOP2"): 5.0,
    ("1", "TOP3"): 2.5,
    ("1", "BEST"): 3.0,
    ("1", "R3"): 1.5,
    ("1", "R1"): 0.75,
    # League 2 - Second division (~60 % of L1 values)
    ("2", "TOP1"): 6.0,
    ("2", "TOP2"): 3.0,
    ("2", "TOP3"): 1.5,
    ("2", "BEST"): 1.8,
    ("2", "R3"): 0.9,
    ("2", "R1"): 0.45,
}

# Season multipliers — smooth exponential decay ``0.7 ^ years_ago`` (TIK-80).
# Was uneven: −20 %, −38 %, −40 %, −33 % year-on-year. New curve gives a
# constant −30 % per year, no cliffs. Future seasons (26/27, …) just need
# ``is_active=True`` to flip to baseline; older seasons follow the same
# curve via ``years_ago = active_year - season_year``.
SEASON_MULTIPLIER: dict[str, float] = {
    "25/26": 1.000,  # Baseline (years_ago=0)
    "24/25": 0.700,  # 0.7^1
    "23/24": 0.490,  # 0.7^2
    "22/23": 0.343,  # 0.7^3
    "21/22": 0.240,  # 0.7^4
}

# Human-readable labels for achievement kinds
LABEL_RU: dict[str, str] = {
    "TOP1": "TOP1",
    "TOP2": "TOP2",
    "TOP3": "TOP3",
    "BEST": "Best regular",
    "R3": "Round 3",
    "R1": "Round 1",
}


def _get_base_points_from_db(session: SessionLike) -> dict[tuple[str, str], float]:
    """Read base points from AchievementType reference table.

    Falls back to hardcoded BASE_POINTS if table is empty.

    Args:
        session: SQLAlchemy database session

    Returns:
        Dictionary mapping (league_code, type_code) -> base points as float.
        Floats preserve compact-scale fractional values like ``2.5`` (TOP3 L1)
        without rounding to ``2`` and collapsing onto ``BEST``.
    """
    types = session.query(AchievementType).all()
    if not types:
        return BASE_POINTS  # Fallback to hardcoded

    leagues = session.query(League).all()
    if not leagues:
        return BASE_POINTS

    result: dict[tuple[str, str], float] = {}
    for ach_type in types:
        for league in leagues:
            # get_base_points honours League.parent_code so subleagues like 2.1
            # correctly inherit base_points_l2 from their parent.
            result[(league.code, ach_type.code)] = float(get_base_points(ach_type, league))

    return result


def _get_season_multiplier_from_db(session: SessionLike) -> dict[str, float]:
    """Read season multipliers from Season reference table.

    Falls back to hardcoded SEASON_MULTIPLIER if table is empty.

    Args:
        session: SQLAlchemy database session

    Returns:
        Dictionary mapping season_code -> multiplier
    """
    seasons = session.query(Season).all()
    if not seasons:
        return SEASON_MULTIPLIER  # Fallback to hardcoded

    return {s.code: s.multiplier for s in seasons}


def get_achievement_kind(achievement: Achievement) -> str:
    """Get normalized kind for points calculation.

    Args:
        achievement: Achievement model instance

    Returns:
        Normalized kind string (TOP1, TOP2, BEST, R3, R1)
    """
    # Use the relationship to get the type code
    type_code = achievement.type.code if achievement.type else achievement.title.split()[0]

    if type_code.startswith("TOP"):
        return type_code
    if "Best regular" in achievement.title:
        return "BEST"
    if "Round 3" in achievement.title:
        return "R3"
    if "Round 1" in achievement.title:
        return "R1"
    return type_code


def calculate_achievement_points(
    achievement: Achievement,
    base_points: dict[tuple[str, str], float] | None = None,
    season_multiplier: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Calculate points for a single achievement.

    Args:
        achievement: Achievement model instance
        base_points: Optional pre-loaded base points dict (for batch operations)
        season_multiplier: Optional pre-loaded season multiplier dict (for batch operations)

    Returns:
        Dictionary with points calculation details. ``points`` is rounded to
        2 decimals so the compact scale (``TOP1 L1 = 10.0``) keeps meaningful
        precision (e.g. ``10.0 × 0.49 = 4.9`` instead of being truncated to
        ``5``).
    """
    kind = get_achievement_kind(achievement)

    # Use provided dicts or fall back to module-level constants
    bp = base_points if base_points is not None else BASE_POINTS
    sm = season_multiplier if season_multiplier is not None else SEASON_MULTIPLIER

    # Get codes from relationships
    league_code = (
        achievement.league.code
        if achievement.league
        else achievement.title.split()[1] if len(achievement.title.split()) > 1 else "1"
    )
    season_code = achievement.season.code if achievement.season else "24/25"

    # Calculate points: base × multiplier
    base = bp.get((league_code, kind), 0.0)
    mul = sm.get(season_code, 1.0)
    points = round(base * mul, 2)
    label = LABEL_RU.get(kind, kind)
    mul_display = f"{mul:.2f}".replace(".", ",")

    return {
        "points": points,
        "base": base,
        "mul": mul,
        "mul_display": mul_display,
        "season": season_code,
        "league": league_code,
        "kind": kind,
        "label": f"Л{league_code} · {label} · s{season_code}",
        "html": achievement.to_html(),
    }


def build_leaderboard(session: SessionLike, season_id: int | None = None) -> list[dict[str, Any]]:
    """Build the leaderboard with all managers and their ratings.

    Uses eager loading (joinedload) to prevent N+1 query problem:
    - Loads all managers with their achievements in a single query
    - Loads country data for each manager in the same query
    - Loads base points and season multipliers from reference tables (1 query each)

    Args:
        session: SQLAlchemy database session.
        season_id: Optional ``Season.id``. When provided, only achievements
            tied to that season contribute to the leaderboard rows — totals,
            ranks, and the per-manager achievement list are all computed as
            if no other seasons existed. Managers without any achievement
            in the requested season are still returned (with ``total=0``)
            so the dropdown does not silently hide active managers.
            ``None`` means lifetime aggregate (all seasons).

    Returns:
        List of manager rating dictionaries, sorted by total points descending
    """
    # Load reference data from DB (with fallback to hardcoded)
    base_points = _get_base_points_from_db(session)
    season_mult = _get_season_multiplier_from_db(session)

    # Query all managers with their achievements and country using eager loading.
    # Also eager load the achievement relationships (type, league, season) to avoid N+1.
    managers = (
        session.query(Manager)
        .options(
            joinedload(Manager.achievements).joinedload(Achievement.type),
            joinedload(Manager.achievements).joinedload(Achievement.league),
            joinedload(Manager.achievements).joinedload(Achievement.season),
            joinedload(Manager.country),
        )
        .order_by(Manager.name)
        .all()
    )

    rows: list[dict[str, Any]] = []

    for manager in managers:
        achievements_data: list[dict[str, Any]] = []
        total_points = 0

        # Safely handle country (BUG FIX: manager.country might be None in some tests)
        country_flag = manager.country.flag_display_url if manager.country else ""
        country_code = manager.country.code if manager.country else "???"

        for achievement in cast(list[Achievement], manager.achievements):
            # Season filter: when the caller asked for one specific season,
            # skip every achievement that does not belong to it. Passing
            # season_id=None preserves the lifetime aggregate behaviour.
            if season_id is not None and achievement.season_id != season_id:
                continue

            parsed = calculate_achievement_points(achievement, base_points, season_mult)
            achievements_data.append(parsed)

            # total_points should always be cumulative (Lifetime) to match production
            total_points += parsed["points"]

        rows.append(
            {
                "id": manager.id,
                "name": manager.name,
                "display_name": manager.display_name,
                "is_tandem": manager.is_tandem,
                "country": country_flag,
                "country_code": country_code,
                "total": total_points,
                "achievements": achievements_data,
            }
        )

    # Sort by total points descending, then by name ascending
    rows.sort(key=lambda r: (-r["total"], r["name"]))

    # Assign ranks (same points = same rank)
    result: list[dict[str, Any]] = []
    rank = 0
    prev_total: int | None = None

    for i, row in enumerate(rows, start=1):
        if row["total"] != prev_total:
            rank = i
            prev_total = row["total"]

        result.append(
            {
                **row,
                "rank": rank,
            }
        )

    return result


# ==================== Auto-Recalculation Triggers (FR-005) ====================


def setup_rating_triggers() -> None:
    """Setup SQLAlchemy event listeners for automatic rating recalculation.

    Triggers:
    - Achievement created → auto-calculate points
    - Achievement updated (type_id, league_id, season_id changed) → auto-calculate points
    - Achievement deleted → invalidate cache
    - Season multiplier changed → recalculate all achievements in that season
    - AchievementType points changed → recalculate all achievements of that type
    """
    from sqlalchemy import event
    from sqlalchemy.orm import object_session

    def _recalculate_points(target: Achievement) -> None:
        """Helper to recalculate points on an achievement."""
        # Try to use relationships first
        ach_type = target.type
        league = target.league
        season = target.season

        # If relationships not loaded, look them up by ID using session.get()
        if ach_type is None and target.type_id is not None:
            session = object_session(target)
            if session:
                ach_type = session.get(AchievementType, target.type_id)

        if league is None and target.league_id is not None:
            session = object_session(target)
            if session:
                league = session.get(League, target.league_id)

        if season is None and target.season_id is not None:
            session = object_session(target)
            if session:
                season = session.get(Season, target.season_id)

        if ach_type and league and season:
            ach_type_resolved = cast(AchievementType, ach_type)
            league_resolved = cast(League, league)
            season_resolved = cast(Season, season)
            target.base_points = get_base_points(ach_type_resolved, league_resolved)
            target.multiplier = float(season_resolved.multiplier)
            target.final_points = round(target.base_points * target.multiplier, 2)

    @event.listens_for(Achievement, "before_insert")
    def achievement_before_insert(_mapper: Any, _connection: Any, target: Achievement) -> None:
        """Auto-calculate points before insert."""
        _recalculate_points(target)

    @event.listens_for(Achievement, "before_update")
    def achievement_before_update(_mapper: Any, _connection: Any, target: Achievement) -> None:
        """Auto-calculate points before update if relevant fields changed."""
        _recalculate_points(target)

    @event.listens_for(Achievement, "after_delete")
    def achievement_after_delete(_mapper: Any, _connection: Any, target: Achievement) -> None:
        """Invalidate leaderboard cache after achievement deletion."""
        from services.cache_service import invalidate_leaderboard_cache

        invalidate_leaderboard_cache()
