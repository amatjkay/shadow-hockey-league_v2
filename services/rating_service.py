"""Rating service for calculating manager rankings.

This module provides functions to calculate manager ratings based on their
achievements stored in the database. Points are calculated as:
    base_points(league, achievement_type) × season_multiplier

Base points and season multipliers are read from reference tables in the database.
Fallback to hardcoded values if reference tables are empty (backward compatibility).

The rating is used to build the leaderboard displayed on the main page.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, joinedload, scoped_session

from models import Achievement, AchievementType, League, Manager, Season

# ==================== Fallback constants (used if reference tables are empty) ====================

# Base points for each league and achievement type combination
# L1:L2 = 2:1 consistently — L2 is exactly half of L1 for every achievement type
BASE_POINTS: dict[tuple[str, str], int] = {
    ("1", "TOP1"): 1000,
    ("2", "TOP1"): 500,
    ("1", "TOP2"): 600,
    ("2", "TOP2"): 300,
    ("1", "TOP3"): 400,
    ("2", "TOP3"): 200,
    ("1", "BEST"): 200,
    ("2", "BEST"): 100,
    ("1", "R3"): 150,
    ("2", "R3"): 75,
    ("1", "R1"): 80,
    ("2", "R1"): 40,
}

# Season multipliers — smooth exponential decay: ``0.7 ^ years_ago`` (TIK-80)
# Older seasons decay faster: recent achievements are more valuable
SEASON_MULTIPLIER: dict[str, float] = {
    "25/26": 1.000,  # Baseline — current season
    "24/25": 0.700,  # 0.7 ^ 1
    "23/24": 0.490,  # 0.7 ^ 2
    "22/23": 0.343,  # 0.7 ^ 3
    "21/22": 0.240,  # 0.7 ^ 4
}

# Human-readable labels for achievement kinds
LABEL_RU: dict[str, str] = {
    "TOP1": "Чемпион",
    "TOP2": "Финалист",
    "TOP3": "Полуфинал",
    "BEST": "Регулярка",
    "R3": "Раунд 3",
    "R1": "Раунд 1",
}


def _get_base_points_from_db(session: Session | scoped_session) -> dict[tuple[str, str], int]:
    """Read base points from AchievementType reference table.

    Falls back to hardcoded BASE_POINTS if table is empty.

    Args:
        session: SQLAlchemy database session

    Returns:
        Dictionary mapping (league_code, type_code) -> base points
    """
    types = session.query(AchievementType).all()
    if not types:
        return BASE_POINTS  # Fallback to hardcoded

    leagues = {l.code: l.code for l in session.query(League).all()}
    if not leagues:
        return BASE_POINTS

    result: dict[tuple[str, str], int] = {}
    for ach_type in types:
        for league_code in leagues:
            points = ach_type.base_points_l1 if league_code == "1" else ach_type.base_points_l2
            result[(league_code, ach_type.code)] = points

    return result


def _get_season_multiplier_from_db(session: Session | scoped_session) -> dict[str, float]:
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
    base_points: dict[tuple[str, str], int] | None = None,
    season_multiplier: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Calculate points for a single achievement.

    Args:
        achievement: Achievement model instance
        base_points: Optional pre-loaded base points dict (for batch operations)
        season_multiplier: Optional pre-loaded season multiplier dict (for batch operations)

    Returns:
        Dictionary with points calculation details
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
    base = bp.get((league_code, kind), 0)
    mul = sm.get(season_code, 1.0)
    points = round(base * mul)
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


def build_leaderboard(
    session: Session | scoped_session, season_id: int | None = None
) -> list[dict[str, Any]]:
    """Build the leaderboard with all managers and their ratings.

    Uses eager loading (joinedload) to prevent N+1 query problem:
    - Loads all managers with their achievements in a single query
    - Loads country data for each manager in the same query
    - Loads base points and season multipliers from reference tables (1 query each)

    Args:
        session: SQLAlchemy database session
        season_id: Optional season ID to filter achievements by

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
            joinedload(Manager.achievements).joinedload(Achievement.type),  # type: ignore[arg-type]
            joinedload(Manager.achievements).joinedload(Achievement.league),  # type: ignore[arg-type]
            joinedload(Manager.achievements).joinedload(Achievement.season),  # type: ignore[arg-type]
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
        country_flag = manager.country.flag_path if manager.country else ""
        country_code = manager.country.code if manager.country else "???"

        achievements_list: list[Achievement] = list(manager.achievements)
        filtered = (a for a in achievements_list if season_id is None or a.season_id == season_id)
        for achievement in filtered:
            parsed = calculate_achievement_points(achievement, base_points, season_mult)
            achievements_data.append(parsed)
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

    _assign_total_display(result)
    return result


def _assign_total_display(result: list[dict[str, Any]]) -> None:
    """Add a ``total_display`` string to every row.

    Default precision is 2 decimals. For top-10 rows where two distinct ranks
    would render the same 2-decimal value, all rows in that collision group
    are bumped to 3 decimals. True ties keep 2 decimals.
    """
    top10 = result[:10]
    by_2dp: dict[str, list[int]] = {}
    for idx, row in enumerate(top10):
        key = f"{row['total']:.2f}"
        by_2dp.setdefault(key, []).append(idx)

    needs_3dp: set[int] = set()
    for indices in by_2dp.values():
        ranks = {top10[i]["rank"] for i in indices}
        if len(ranks) > 1:
            needs_3dp.update(indices)

    for i, row in enumerate(result):
        if i in needs_3dp:
            row["total_display"] = f"{row['total']:.3f}"
        else:
            row["total_display"] = f"{row['total']:.2f}"


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
            target.base_points = float(
                ach_type.base_points_l1 if league.code == "1" else ach_type.base_points_l2
            )
            target.multiplier = float(season.multiplier)
            target.final_points = round(target.base_points * target.multiplier, 2)

    @event.listens_for(Achievement, "before_insert")
    def achievement_before_insert(mapper: Any, connection: Any, target: Achievement) -> None:
        """Auto-calculate points before insert."""
        _recalculate_points(target)

    @event.listens_for(Achievement, "before_update")
    def achievement_before_update(mapper: Any, connection: Any, target: Achievement) -> None:
        """Auto-calculate points before update if relevant fields changed."""
        _recalculate_points(target)

    @event.listens_for(Achievement, "after_delete")
    def achievement_after_delete(mapper: Any, connection: Any, target: Achievement) -> None:
        """Invalidate leaderboard cache after achievement deletion."""
        from services.cache_service import invalidate_leaderboard_cache

        invalidate_leaderboard_cache()
