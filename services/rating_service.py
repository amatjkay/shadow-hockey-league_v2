"""Rating service for calculating manager rankings.

This module provides functions to calculate manager ratings based on their
achievements stored in the database. Points are calculated as:
    base_points(league, achievement_type) × season_multiplier

The rating is used to build the leaderboard displayed on the main page.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, joinedload

from models import Achievement, Manager

# Base points for each league and achievement type combination
# Updated: increased gap between TOP1 and other achievements to make L1 victories more meaningful
BASE_POINTS: dict[tuple[str, str], int] = {
    # League 1 - Elite division
    ("1", "TOP1"): 800,
    ("1", "TOP2"): 550,
    ("1", "TOP3"): 450,
    ("1", "BEST"): 50,
    ("1", "R3"): 30,
    ("1", "R1"): 10,
    # League 2 - Second division (50% of L1 values for TOP, similar for others)
    ("2", "TOP1"): 300,
    ("2", "TOP2"): 200,
    ("2", "TOP3"): 100,
    ("2", "BEST"): 40,
    ("2", "R3"): 20,
    ("2", "R1"): 5,
}

# Season multipliers - current season is baseline (1.00), older seasons have discount
# Logic: recent achievements are more valuable than old ones
SEASON_MULTIPLIER: dict[str, float] = {
    "24/25": 1.00,  # Current/latest season - baseline
    "23/24": 0.95,  # Previous season - 5% discount
    "22/23": 0.90,  # Older season - 10% discount
    "21/22": 0.85,  # Oldest season - 15% discount
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


def get_achievement_kind(achievement: Achievement) -> str:
    """Get normalized kind for points calculation.

    Args:
        achievement: Achievement model instance

    Returns:
        Normalized kind string (TOP1, TOP2, BEST, R3, R1)
    """
    if achievement.achievement_type.startswith("TOP"):
        return achievement.achievement_type
    if "Best regular" in achievement.title:
        return "BEST"
    if "Round 3" in achievement.title:
        return "R3"
    if "Round 1" in achievement.title:
        return "R1"
    return achievement.achievement_type


def calculate_achievement_points(achievement: Achievement) -> dict[str, Any]:
    """Calculate points for a single achievement.

    Args:
        achievement: Achievement model instance

    Returns:
        Dictionary with points calculation details
    """
    kind = get_achievement_kind(achievement)

    # Calculate points: base × multiplier
    base = BASE_POINTS.get((achievement.league, kind), 0)
    mul = SEASON_MULTIPLIER.get(achievement.season, 1.0)
    points = round(base * mul)
    label = LABEL_RU.get(kind, kind)
    mul_display = f"{mul:.2f}".replace(".", ",")

    return {
        "points": points,
        "base": base,
        "mul": mul,
        "mul_display": mul_display,
        "season": achievement.season,
        "league": achievement.league,
        "kind": kind,
        "label": f"Л{achievement.league} · {label} · s{achievement.season}",
        "html": achievement.to_html(),
    }


def build_leaderboard(session: Session) -> list[dict[str, Any]]:
    """Build the leaderboard with all managers and their ratings.

    Uses eager loading (joinedload) to prevent N+1 query problem:
    - Loads all managers with their achievements in a single query
    - Loads country data for each manager in the same query

    Args:
        session: SQLAlchemy database session

    Returns:
        List of manager rating dictionaries, sorted by total points descending
    """
    # Query all managers with their achievements and country using eager loading
    # This generates a single SQL query with JOINs instead of N+1 queries
    managers = (
        session.query(Manager)
        .options(joinedload(Manager.achievements), joinedload(Manager.country))
        .order_by(Manager.name)
        .all()
    )

    rows: list[dict[str, Any]] = []

    for manager in managers:
        achievements_data: list[dict[str, Any]] = []
        total_points = 0

        for achievement in manager.achievements:
            parsed = calculate_achievement_points(achievement)
            achievements_data.append(parsed)
            total_points += parsed["points"]

        rows.append(
            {
                "id": manager.id,
                "name": manager.name,
                "display_name": manager.display_name,
                "is_tandem": manager.is_tandem,
                "country": manager.country.flag_path,
                "country_code": manager.country.code,
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
