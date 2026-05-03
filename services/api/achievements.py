"""Achievement CRUD endpoints registered on the ``services.api`` Blueprint.

Includes the helpers extracted in TIK-44 (``_resolve_fk_by_code``,
``_apply_achievement_patch``, ``_recalculate_achievement_points``) used by
:func:`update_achievement` to keep cyclomatic complexity ≤ B.
"""

from __future__ import annotations

from typing import Any, cast

from flask import jsonify, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from models import Achievement, AchievementType, League, Season, db
from services.api import api
from services.api._helpers import paginate_query
from services.api_auth import authenticate_api_key
from services.cache_service import invalidate_leaderboard_cache
from services.extensions import limiter
from services.scoring_service import get_base_points
from services.validation_service import validate_achievement_data, validate_manager_exists


@api.route("/achievements", methods=["GET"])
@limiter.limit("100 per minute")
@authenticate_api_key("read")
def get_achievements() -> tuple[Any, int]:
    """Get all achievements with optional filtering and pagination."""
    # Eager-load every relationship serialised below to avoid N+1.
    query = db.session.query(Achievement).options(
        joinedload(Achievement.type),
        joinedload(Achievement.league),
        joinedload(Achievement.season),
        joinedload(Achievement.manager),
    )

    manager_id = request.args.get("manager_id", type=int)
    if manager_id:
        query = query.filter(Achievement.manager_id == manager_id)

    league = request.args.get("league", "")
    if league:
        query = query.join(League).filter(League.code == league)

    season = request.args.get("season", "")
    if season:
        query = query.join(Season).filter(Season.code == season)

    achievement_type = request.args.get("achievement_type", "")
    if achievement_type:
        query = query.join(AchievementType).filter(AchievementType.code == achievement_type)

    query = query.order_by(Achievement.season_id.desc())

    def serialize_achievement(a: Achievement) -> dict:
        return {
            "id": a.id,
            "type_id": a.type_id,
            "league_id": a.league_id,
            "season_id": a.season_id,
            "achievement_type": a.type.code if a.type else None,
            "league": a.league.code if a.league else None,
            "season": a.season.code if a.season else None,
            "title": a.title,
            "icon_path": a.icon_path,
            "manager_id": a.manager_id,
            "manager_name": a.manager.name,
            "base_points": a.base_points,
            "multiplier": a.multiplier,
            "final_points": a.final_points,
        }

    return paginate_query(query, serialize_achievement)


@api.route("/achievements", methods=["POST"])
@limiter.limit("100 per minute")
@authenticate_api_key("write")
def create_achievement() -> tuple[Any, int]:
    """Create a new achievement."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Support both new FK-style and legacy string fields
    type_code = data.get("type_code") or data.get("achievement_type", "")
    league_code = data.get("league_code") or data.get("league", "")
    season_code = data.get("season_code") or data.get("season", "")
    title = data.get("title", "")
    icon_path = data.get("icon_path", "")
    manager_id = data.get("manager_id")

    is_valid, error = validate_achievement_data(type_code, league_code, season_code, title)
    if not is_valid:
        return jsonify({"error": error}), 400

    is_valid, error = validate_manager_exists(db.session, manager_id)
    if not is_valid:
        return jsonify({"error": error}), 400

    ach_type = db.session.query(AchievementType).filter_by(code=type_code).first()
    if not ach_type:
        return jsonify({"error": f"Achievement type '{type_code}' not found"}), 400

    league = db.session.query(League).filter_by(code=league_code).first()
    if not league:
        return jsonify({"error": f"League '{league_code}' not found"}), 400

    season = db.session.query(Season).filter_by(code=season_code).first()
    if not season:
        return jsonify({"error": f"Season '{season_code}' not found"}), 400

    base_points = get_base_points(ach_type, league)
    multiplier = season.multiplier
    final_points = base_points * multiplier

    try:
        achievement = Achievement(
            type_id=ach_type.id,
            league_id=league.id,
            season_id=season.id,
            title=title,
            icon_path=icon_path,
            manager_id=manager_id,
            base_points=float(base_points),
            multiplier=float(multiplier),
            final_points=float(final_points),
        )
        db.session.add(achievement)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return (
            jsonify(
                {"error": "Achievement already exists for this manager, league, season, and type"}
            ),
            409,
        )

    invalidate_leaderboard_cache()

    return (
        jsonify(
            {
                "id": achievement.id,
                "type_id": achievement.type_id,
                "league_id": achievement.league_id,
                "season_id": achievement.season_id,
                "achievement_type": type_code,
                "league": league_code,
                "season": season_code,
                "title": achievement.title,
                "icon_path": achievement.icon_path,
                "manager_id": achievement.manager_id,
                "base_points": achievement.base_points,
                "multiplier": achievement.multiplier,
                "final_points": achievement.final_points,
                "message": "Achievement created successfully",
            }
        ),
        201,
    )


@api.route("/achievements/<int:achievement_id>", methods=["GET"])
@limiter.limit("100 per minute")
@authenticate_api_key("read")
def get_achievement(achievement_id: int) -> tuple[Any, int]:
    """Get a specific achievement by ID."""
    achievement = db.session.query(Achievement).filter_by(id=achievement_id).first()

    if not achievement:
        return jsonify({"error": f"Achievement with ID {achievement_id} not found"}), 404

    return (
        jsonify(
            {
                "id": achievement.id,
                "type_id": achievement.type_id,
                "league_id": achievement.league_id,
                "season_id": achievement.season_id,
                "achievement_type": achievement.type.code if achievement.type else None,
                "league": achievement.league.code if achievement.league else None,
                "season": achievement.season.code if achievement.season else None,
                "title": achievement.title,
                "icon_path": achievement.icon_path,
                "manager_id": achievement.manager_id,
                "manager_name": achievement.manager.name,
                "base_points": achievement.base_points,
                "multiplier": achievement.multiplier,
                "final_points": achievement.final_points,
            }
        ),
        200,
    )


def _resolve_fk_by_code(
    model: Any, code: str | None, label: str
) -> tuple[Any, tuple[Any, int] | None]:
    """Look up a model row by its ``code`` column.

    Returns ``(row, None)`` on success, ``(None, error_response)`` on failure.
    When ``code`` is falsy returns ``(None, None)`` — caller should skip update.
    """
    if not code:
        return None, None
    row = db.session.query(model).filter_by(code=code).first()
    if not row:
        return None, (jsonify({"error": f"{label} '{code}' not found"}), 400)
    return row, None


def _apply_achievement_patch(
    achievement: Achievement, data: dict
) -> tuple[tuple[Any, int] | None, bool]:
    """Apply PUT-payload to an Achievement row.

    Returns ``(error_response_or_none, fk_changed_flag)``.
    """
    fk_changed = False

    type_code = data.get("type_code") or data.get("achievement_type")
    ach_type, err = _resolve_fk_by_code(AchievementType, type_code, "Achievement type")
    if err:
        return err, fk_changed
    if ach_type:
        achievement.type_id = ach_type.id
        fk_changed = True

    league_code = data.get("league_code") or data.get("league")
    league, err = _resolve_fk_by_code(League, league_code, "League")
    if err:
        return err, fk_changed
    if league:
        achievement.league_id = league.id
        fk_changed = True

    season_code = data.get("season_code") or data.get("season")
    season, err = _resolve_fk_by_code(Season, season_code, "Season")
    if err:
        return err, fk_changed
    if season:
        achievement.season_id = season.id
        fk_changed = True

    if "title" in data:
        achievement.title = data["title"]
    if "icon_path" in data:
        achievement.icon_path = data["icon_path"]

    if "manager_id" in data:
        new_manager_id = data["manager_id"]
        is_valid, error = validate_manager_exists(db.session, new_manager_id)
        if not is_valid:
            return (jsonify({"error": error}), 400), fk_changed
        achievement.manager_id = new_manager_id

    return None, fk_changed


def _recalculate_achievement_points(achievement: Achievement) -> None:
    """Refresh FK relationships and recompute base/multiplier/final points."""
    db.session.refresh(achievement, attribute_names=["type", "league", "season"])
    if achievement.type and achievement.league and achievement.season:
        ach_type = cast(AchievementType, achievement.type)
        league = cast(League, achievement.league)
        season = cast(Season, achievement.season)
        achievement.base_points = get_base_points(ach_type, league)
        achievement.multiplier = float(season.multiplier)
        achievement.final_points = float(achievement.base_points * achievement.multiplier)


@api.route("/achievements/<int:achievement_id>", methods=["PUT"])
@limiter.limit("100 per minute")
@authenticate_api_key("write")
def update_achievement(achievement_id: int) -> tuple[Any, int]:
    """Update an achievement."""
    achievement = db.session.query(Achievement).filter_by(id=achievement_id).first()
    if not achievement:
        return jsonify({"error": f"Achievement with ID {achievement_id} not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    error_response, fk_changed = _apply_achievement_patch(achievement, data)
    if error_response:
        return error_response

    if fk_changed:
        _recalculate_achievement_points(achievement)

    db.session.commit()
    invalidate_leaderboard_cache()

    return (
        jsonify(
            {
                "id": achievement.id,
                "type_id": achievement.type_id,
                "league_id": achievement.league_id,
                "season_id": achievement.season_id,
                "achievement_type": achievement.type.code if achievement.type else None,
                "league": achievement.league.code if achievement.league else None,
                "season": achievement.season.code if achievement.season else None,
                "title": achievement.title,
                "icon_path": achievement.icon_path,
                "manager_id": achievement.manager_id,
                "message": "Achievement updated successfully",
            }
        ),
        200,
    )


@api.route("/achievements/<int:achievement_id>", methods=["DELETE"])
@limiter.limit("100 per minute")
@authenticate_api_key("admin")
def delete_achievement(achievement_id: int) -> tuple[Any, int]:
    """Delete an achievement."""
    achievement = db.session.query(Achievement).filter_by(id=achievement_id).first()

    if not achievement:
        return jsonify({"error": f"Achievement with ID {achievement_id} not found"}), 404

    db.session.delete(achievement)
    db.session.commit()
    invalidate_leaderboard_cache()

    return jsonify({"message": "Achievement deleted successfully"}), 200
