"""Admin API endpoints for Select2 dropdowns and bulk operations.

Implements API-001 through API-006 from requirements.json.
All endpoints require admin authentication.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable

from flask import Blueprint, jsonify, request
from flask_login import current_user
from sqlalchemy.orm import joinedload

from models import Achievement, AchievementType, Country, League, Manager, Season, db
from services.cache_service import invalidate_leaderboard_cache
from services.scoring_service import get_base_points


def admin_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """Ensure the current user has admin privileges."""
    from functools import wraps

    from flask import jsonify

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        if not getattr(current_user, "is_admin", False):
            return jsonify({"error": "Access denied"}), 403
        return func(*args, **kwargs)

    return wrapper


admin_api_bp = Blueprint("admin_api", __name__, url_prefix="/admin/api")

api_logger = logging.getLogger("shleague.admin_api")


# ==================== Helper ====================


def _paginate_query(query, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    """Helper to paginate query results for Select2."""
    page_size = min(max(page_size, 1), 100)  # Clamp 1-100
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
            "has_more": page * page_size < total,
        },
    }


# ==================== API-001: Countries ====================


@admin_api_bp.route("/countries", methods=["GET"])
@admin_required
def get_countries() -> Any:
    """API-001: Search and list countries for Select2 dropdown.

    Query params:
        q: Search query (country name or code)
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)
    """
    try:
        q = request.args.get("q", "").strip()
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 20, type=int)

        query = db.session.query(Country).filter_by(is_active=True)

        if q:
            query = query.filter(db.or_(Country.name.ilike(f"%{q}%"), Country.code.ilike(f"%{q}%")))

        query = query.order_by(Country.name)
        result = _paginate_query(query, page, page_size)

        return jsonify(
            {
                "items": [
                    {
                        "id": c.id,
                        "code": c.code,
                        "name": c.name,
                        "flag_url": c.flag_display_url,
                        "is_active": c.is_active,
                    }
                    for c in result["items"]
                ],
                "pagination": result["pagination"],
            }
        )
    except Exception as e:
        api_logger.error(f"Error in GET /admin/api/countries: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ==================== API-002: Managers ====================


@admin_api_bp.route("/managers", methods=["GET"])
@admin_required
def get_managers() -> Any:
    """API-002: Search managers for Select2 dropdown.

    Query params:
        q: Search query (manager name)
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)
        ids: Comma-separated list of manager IDs for bulk fetch (optional)
    """
    try:
        q = request.args.get("q", "").strip()
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 20, type=int)
        ids_param = request.args.get("ids", "").strip()

        # Handle bulk fetch by IDs (P0-1: bulk preview with real data)
        if ids_param:
            try:
                ids = [int(x.strip()) for x in ids_param.split(",") if x.strip()]
                if not ids:
                    return jsonify({"items": [], "pagination": {"total": 0}})

                managers = (
                    db.session.query(Manager)
                    .options(joinedload(Manager.country))
                    .filter(Manager.id.in_(ids), Manager.is_active == True)
                    .all()
                )

                # Sort by original order of IDs
                manager_map = {m.id: m for m in managers}
                sorted_managers = [manager_map[mid] for mid in ids if mid in manager_map]

                return jsonify(
                    {
                        "items": [
                            {
                                "id": m.id,
                                "name": m.name,
                                "country_id": m.country_id,
                                "country_name": m.country.name if m.country else "Unknown",
                                "country_code": m.country.code if m.country else "",
                                "country_flag": m.country.flag_path if m.country else "",
                                "country_flag_url": m.country.flag_display_url if m.country else "",
                                "is_tandem": m.is_tandem,
                            }
                            for m in sorted_managers
                        ],
                        "pagination": {"total": len(sorted_managers)},
                    }
                )
            except ValueError:
                return jsonify({"error": "Invalid IDs format"}), 400

        # Standard paginated search
        query = (
            db.session.query(Manager).options(joinedload(Manager.country)).filter_by(is_active=True)
        )

        if q:
            query = query.filter(Manager.name.ilike(f"%{q}%"))

        query = query.order_by(Manager.name)
        result = _paginate_query(query, page, page_size)

        return jsonify(
            {
                "items": [
                    {
                        "id": m.id,
                        "name": m.name,
                        "country_id": m.country_id,
                        "country_name": m.country.name if m.country else "Unknown",
                        "country_code": m.country.code if m.country else "",
                        "country_flag": m.country.flag_path if m.country else "",
                        "is_tandem": m.is_tandem,
                    }
                    for m in result["items"]
                ],
                "pagination": result["pagination"],
            }
        )
    except Exception as e:
        api_logger.error(f"Error in GET /admin/api/managers: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ==================== API-003: Seasons ====================


@admin_api_bp.route("/seasons", methods=["GET"])
@admin_required
def get_seasons() -> Any:
    """API-003: List seasons filtered by league.

    Query params:
        league_id: League ID to filter seasons (required)
        active_only: Only return active seasons (default: true)
    """
    try:
        league_id = request.args.get("league_id", type=int)
        if not league_id:
            return jsonify({"error": "league_id is required"}), 400

        active_only = request.args.get("active_only", "true").lower() == "true"

        # Get league to check code
        league = db.session.get(League, league_id)
        if not league:
            return jsonify({"error": "League not found"}), 404

        query = db.session.query(Season)
        if active_only:
            query = query.filter_by(is_active=True)

        # VR-004: League 2.1/2.2 only available from 2025
        if league.code in ("2.1", "2.2"):
            query = query.filter(Season.start_year >= 2025)

        seasons = query.order_by(Season.code.desc()).all()

        return jsonify(
            {
                "items": [
                    {
                        "id": s.id,
                        "code": s.code,
                        "name": s.name,
                        "multiplier": s.multiplier,
                        "start_year": s.start_year,
                        "end_year": s.end_year,
                        "is_active": s.is_active,
                        "is_available": True,
                    }
                    for s in seasons
                ]
            }
        )
    except Exception as e:
        api_logger.error(f"Error in GET /admin/api/seasons: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ==================== API-004: Achievement Type Points ====================


@admin_api_bp.route("/achievement-types/<int:type_id>/points", methods=["GET"])
@admin_required
def get_achievement_points(type_id: int) -> Any:
    """API-004: Get base points for achievement type based on league.

    Query params:
        league_id: League ID (required)
    """
    try:
        league_id = request.args.get("league_id", type=int)
        if not league_id:
            return jsonify({"error": "league_id is required"}), 400

        ach_type = db.session.get(AchievementType, type_id)
        if not ach_type:
            return jsonify({"error": "Achievement type not found"}), 404

        league = db.session.get(League, league_id)
        if not league:
            return jsonify({"error": "League not found"}), 404

        # Determine base points (league-aware via League.parent_code).
        base_points = get_base_points(ach_type, league)
        points_source = league.base_points_field

        return jsonify(
            {
                "type_id": ach_type.id,
                "type_code": ach_type.code,
                "type_name": ach_type.name,
                "league_id": league.id,
                "league_code": league.code,
                "base_points": base_points,
                "points_source": points_source,
            }
        )
    except Exception as e:
        api_logger.error(f"Error in GET /admin/api/achievement-types/{type_id}/points: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ==================== API-005: Leagues ====================


@admin_api_bp.route("/leagues", methods=["GET"])
@admin_required
def get_leagues() -> Any:
    """API-005: List all active leagues."""
    try:
        leagues = db.session.query(League).filter_by(is_active=True).order_by(League.code).all()

        return jsonify(
            {
                "items": [
                    {"id": l.id, "code": l.code, "name": l.name, "is_active": l.is_active}
                    for l in leagues
                ]
            }
        )
    except Exception as e:
        api_logger.error(f"Error in GET /admin/api/leagues: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ==================== API-Extra: Achievement Calculator ====================


@admin_api_bp.route("/calculate-points", methods=["GET"])
@admin_required
def calculate_points() -> Any:
    """Calculate final points for achievement type based on league and season.

    Query params:
        type_id: Achievement Type ID (required)
        league_id: League ID (required)
        season_id: Season ID (required)
    """
    try:
        type_id = request.args.get("type_id", type=int)
        league_id = request.args.get("league_id", type=int)
        season_id = request.args.get("season_id", type=int)

        if not all([type_id, league_id, season_id]):
            return jsonify({"error": "type_id, league_id, and season_id are required"}), 400

        # Get entities
        ach_type = db.session.get(AchievementType, type_id)
        league = db.session.get(League, league_id)
        season = db.session.get(Season, season_id)

        if not ach_type:
            return jsonify({"error": "Achievement type not found"}), 404
        if not league:
            return jsonify({"error": "League not found"}), 404
        if not season:
            return jsonify({"error": "Season not found"}), 404

        # Calculate base points (league-aware via League.parent_code).
        base_points = get_base_points(ach_type, league)
        points_source = league.base_points_field

        # Calculate final points
        final_points = base_points * season.multiplier

        return jsonify(
            {
                "type_id": ach_type.id,
                "type_code": ach_type.code,
                "type_name": ach_type.name,
                "league_id": league.id,
                "league_code": league.code,
                "league_name": league.name,
                "season_id": season.id,
                "season_code": season.code,
                "season_name": season.name,
                "base_points": base_points,
                "points_source": points_source,
                "multiplier": season.multiplier,
                "final_points": round(final_points, 2),
                "icon_path": ach_type.get_icon_url(),
            }
        )

    except Exception as e:
        api_logger.error(f"Error in GET /admin/api/calculate-points: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ==================== API-Extra: Achievement Types ====================


@admin_api_bp.route("/achievement-types", methods=["GET"])
@admin_required
def get_achievement_types() -> Any:
    """List all active achievement types for Select2 dropdown."""
    try:
        q = request.args.get("q", "").strip()
        types = db.session.query(AchievementType).filter_by(is_active=True)

        if q:
            types = types.filter(
                db.or_(AchievementType.name.ilike(f"%{q}%"), AchievementType.code.ilike(f"%{q}%"))
            )

        types = types.order_by(AchievementType.name).all()

        return jsonify(
            {
                "items": [
                    {
                        "id": t.id,
                        "text": t.name
                        + " (L1: "
                        + str(t.base_points_l1)
                        + ", L2: "
                        + str(t.base_points_l2)
                        + ")",
                    }
                    for t in types
                ]
            }
        )
    except Exception as e:
        api_logger.error(f"Error in GET /admin/api/achievement-types: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ==================== API-006: Bulk Create ====================


def _validate_bulk_create_payload(
    data: dict | None,
) -> tuple[tuple[Any, int] | None, dict]:
    """Extract & validate the bulk-create request body.

    Returns ``(error_response_or_none, parsed_payload)``.
    """
    if not data:
        return (jsonify({"error": "Request body is required"}), 400), {}

    manager_ids = data.get("manager_ids")
    type_id = data.get("type_id")
    league_id = data.get("league_id")
    season_id = data.get("season_id")

    if not manager_ids or not isinstance(manager_ids, list):
        return (jsonify({"error": "manager_ids array is required"}), 400), {}
    if len(manager_ids) > 100:
        return (jsonify({"error": "Maximum 100 managers per bulk operation"}), 400), {}
    if not type_id or not league_id or not season_id:
        return (jsonify({"error": "type_id, league_id, season_id are required"}), 400), {}

    return None, {
        "manager_ids": manager_ids,
        "type_id": type_id,
        "league_id": league_id,
        "season_id": season_id,
    }


def _resolve_bulk_refs(
    type_id: int, league_id: int, season_id: int
) -> tuple[tuple[Any, int] | None, tuple[Any, Any, Any]]:
    """Look up AchievementType / League / Season rows, or build an error response."""
    ach_type = db.session.get(AchievementType, type_id)
    league = db.session.get(League, league_id)
    season = db.session.get(Season, season_id)

    if not ach_type:
        return (jsonify({"error": "Achievement type not found"}), 400), (None, None, None)
    if not league:
        return (jsonify({"error": "League not found"}), 400), (None, None, None)
    if not season:
        return (jsonify({"error": "Season not found"}), 400), (None, None, None)

    if league.code in ("2.1", "2.2") and season.start_year and season.start_year < 2025:
        return (
            jsonify({"error": f"League {league.code} is only available from season 25/26 onwards"}),
            400,
        ), (None, None, None)

    return None, (ach_type, league, season)


def _compute_points(ach_type: Any, league: Any, season: Any) -> tuple[tuple[Any, int] | None, dict]:
    """Compute base/multiplier/final points; returns error response if any is negative."""
    base_points = float(get_base_points(ach_type, league))
    multiplier = float(season.multiplier)
    final_points = round(base_points * multiplier, 2)

    if base_points < 0 or multiplier < 0 or final_points < 0:
        return (
            jsonify(
                {
                    "error": (
                        f"Points calculation error: negative values "
                        f"(base={base_points}, multiplier={multiplier})"
                    )
                }
            ),
            400,
        ), {}

    return None, {"base": base_points, "multiplier": multiplier, "final": final_points}


def _process_bulk_create_manager(
    mid: int,
    manager: Manager | None,
    existing_id: int | None,
    refs: tuple[Any, Any, Any],
    points: dict,
    icon_path: str,
) -> tuple[str, dict | int]:
    """Decide what to do with a single manager in bulk-create. Returns ``(action, payload)``.

    action ∈ {"error", "skip", "create"}.
    """
    if not manager:
        return "error", {
            "manager_id": mid,
            "manager_name": "Unknown",
            "error_code": "MANAGER_NOT_FOUND",
            "error_message": f"Manager ID {mid} not found",
        }
    if not manager.is_active:
        return "skip", {
            "manager_id": mid,
            "manager_name": manager.name,
            "reason": "Manager is not active",
        }
    if existing_id:
        return "skip", {
            "manager_id": mid,
            "manager_name": manager.name,
            "reason": "Achievement already exists for this manager",
            "existing_id": existing_id,
            "existing_url": f"/admin/achievement/edit/?id={existing_id}",
        }

    ach_type, league, season = refs
    achievement = Achievement(
        manager_id=mid,
        type_id=ach_type.id,
        league_id=league.id,
        season_id=season.id,
        title=f"{ach_type.name} {league.name} {season.name}",
        icon_path=icon_path,
        base_points=points["base"],
        multiplier=points["multiplier"],
        final_points=points["final"],
    )
    db.session.add(achievement)
    db.session.flush()
    return "create", achievement.id


@admin_api_bp.route("/achievements/bulk-create", methods=["POST"])
@admin_required
def bulk_create_achievements() -> Any:
    """API-006: Create achievements for multiple managers."""
    try:
        if not current_user.has_permission("create"):
            return jsonify({"error": "Insufficient permissions"}), 403

        err, payload = _validate_bulk_create_payload(request.get_json())
        if err:
            return err

        err, (ach_type, league, season) = _resolve_bulk_refs(
            payload["type_id"], payload["league_id"], payload["season_id"]
        )
        if err:
            return err

        err, points = _compute_points(ach_type, league, season)
        if err:
            return err

        manager_ids = payload["manager_ids"]
        managers = {
            m.id: m for m in db.session.query(Manager).filter(Manager.id.in_(manager_ids)).all()
        }
        existing_manager_map = {
            ea[1]: ea[0]
            for ea in db.session.query(Achievement.id, Achievement.manager_id)
            .filter(
                Achievement.manager_id.in_(manager_ids),
                Achievement.type_id == payload["type_id"],
                Achievement.league_id == payload["league_id"],
                Achievement.season_id == payload["season_id"],
            )
            .all()
        }
        icon_path = f"/static/img/cups/{ach_type.code.lower()}.svg"

        created: list[int] = []
        skipped: list[dict] = []
        errors: list[dict] = []
        for mid in manager_ids:
            action, item = _process_bulk_create_manager(
                mid,
                managers.get(mid),
                existing_manager_map.get(mid),
                (ach_type, league, season),
                points,
                icon_path,
            )
            if action == "create":
                created.append(item)  # type: ignore[arg-type]
            elif action == "skip":
                skipped.append(item)  # type: ignore[arg-type]
            else:
                errors.append(item)  # type: ignore[arg-type]

        db.session.commit()
        invalidate_leaderboard_cache()

        return jsonify(
            {
                "success": True,
                "summary": {
                    "total_requested": len(manager_ids),
                    "created": len(created),
                    "skipped_duplicates": len(skipped),
                    "errors": len(errors),
                },
                "details": {"created_ids": created, "skipped": skipped, "errors": errors},
                "recalculation_triggered": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    except Exception as e:
        db.session.rollback()
        api_logger.error(f"Error in POST /admin/api/achievements/bulk-create: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ==================== API-005 (NEW): Manager Achievements ====================


@admin_api_bp.route("/managers/<int:manager_id>/achievements", methods=["GET"])
@admin_required
def get_manager_achievements(manager_id: int) -> Any:
    """Get all achievements for a manager.

    Uses joinedload to avoid N+1 queries on type/league/season relationships.
    """
    try:
        manager = db.session.get(Manager, manager_id)
        if not manager:
            return jsonify({"error": "Manager not found"}), 404

        achievements = (
            db.session.query(Achievement)
            .options(
                joinedload(Achievement.type),
                joinedload(Achievement.league),
                joinedload(Achievement.season),
            )
            .filter_by(manager_id=manager_id)
            .all()
        )

        result_achievements = []
        total_points = 0.0

        for a in achievements:
            points = a.final_points or 0.0
            total_points += points

            result_achievements.append(
                {
                    "id": a.id,
                    "type": {
                        "id": a.type_id,
                        "code": a.type.code if a.type else "",
                        "name": a.type.name if a.type else "",
                    },
                    "league": {
                        "id": a.league_id,
                        "code": a.league.code if a.league else "",
                        "name": a.league.name if a.league else "",
                    },
                    "season": {
                        "id": a.season_id,
                        "code": a.season.code if a.season else "",
                        "name": a.season.name if a.season else "",
                        "multiplier": a.season.multiplier if a.season else 1.0,
                    },
                    "base_points": a.base_points,
                    "multiplier": a.multiplier,
                    "final_points": a.final_points,
                    "title": a.title,
                    "icon_path": a.icon_path,
                }
            )

        return jsonify(
            {
                "manager_id": manager.id,
                "manager_name": manager.name,
                "total_points": total_points,
                "achievements": result_achievements,
            }
        )

    except Exception as e:
        import traceback

        error_detail = traceback.format_exc()
        api_logger.error(
            f"Error in GET /admin/api/managers/{manager_id}/achievements: {e}\n{error_detail}"
        )
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


def _validate_bulk_add_payload(data: Any) -> tuple[tuple[Any, int] | None, list]:
    """Validate the bulk-add request body and return the achievements list."""
    if not data or "achievements" not in data:
        return (
            jsonify({"error": "Request body with achievements array is required"}),
            400,
        ), []
    achievements = data["achievements"]
    if not isinstance(achievements, list):
        return (jsonify({"error": "achievements must be an array"}), 400), []
    if len(achievements) > 50:
        return (jsonify({"error": "Maximum 50 achievements per request"}), 400), []
    return None, achievements


def _batch_load_bulk_add_refs(
    achievements: list,
) -> tuple[dict[int, Any], dict[int, Any], dict[int, Any]]:
    """Batch-load AchievementType / League / Season rows referenced by the items."""
    type_ids = {a.get("type_id") for a in achievements if a.get("type_id")}
    league_ids = {a.get("league_id") for a in achievements if a.get("league_id")}
    season_ids = {a.get("season_id") for a in achievements if a.get("season_id")}

    types = {
        t.id: t
        for t in db.session.query(AchievementType).filter(AchievementType.id.in_(type_ids)).all()
    }
    leagues = {lg.id: lg for lg in db.session.query(League).filter(League.id.in_(league_ids)).all()}
    seasons = {s.id: s for s in db.session.query(Season).filter(Season.id.in_(season_ids)).all()}
    return types, leagues, seasons


def _validate_bulk_add_item(
    idx: int,
    ach_data: dict,
    types: dict[int, Any],
    leagues: dict[int, Any],
    seasons: dict[int, Any],
) -> tuple[dict | None, tuple[int, int, int, Any, Any, Any] | None]:
    """Validate one bulk-add item. Returns ``(error_dict, resolved)`` — exactly one is truthy."""
    type_id = ach_data.get("type_id")
    league_id = ach_data.get("league_id")
    season_id = ach_data.get("season_id")

    if not type_id or not league_id or not season_id:
        return {"index": idx, "error": "type_id, league_id, season_id are required"}, None

    ach_type = types.get(type_id)
    if not ach_type:
        return {"index": idx, "error": f"Type {type_id} not found"}, None
    league = leagues.get(league_id)
    if not league:
        return {"index": idx, "error": f"League {league_id} not found"}, None
    season = seasons.get(season_id)
    if not season:
        return {"index": idx, "error": f"Season {season_id} not found"}, None

    if league.code in ("2.1", "2.2") and season.start_year and season.start_year < 2025:
        return {
            "index": idx,
            "error": f"League {league.code} only available from season 25/26",
        }, None

    return None, (type_id, league_id, season_id, ach_type, league, season)


def _build_skip_record(
    type_id: int, ach_type: Any, league: Any, season: Any, existing_id: int
) -> dict:
    return {
        "type_id": type_id,
        "type_name": ach_type.name,
        "league_name": league.name,
        "season_name": season.name,
        "reason": "Achievement already exists for this manager",
        "existing_id": existing_id,
        "existing_url": f"/admin/achievement/edit/?id={existing_id}",
    }


def _create_achievement_for_manager(
    manager_id: int,
    type_id: int,
    league_id: int,
    season_id: int,
    ach_type: Any,
    league: Any,
    season: Any,
) -> tuple[dict | None, Achievement | None]:
    """Build and persist an Achievement; returns (error_dict, achievement). Exactly one is truthy."""
    base_points = float(get_base_points(ach_type, league))
    multiplier = float(season.multiplier)
    final_points = round(base_points * multiplier, 2)
    if base_points < 0 or multiplier < 0 or final_points < 0:
        return {
            "error": (
                f"Points calculation error: negative values "
                f"(base={base_points}, multiplier={multiplier})"
            ),
        }, None

    achievement = Achievement(
        manager_id=manager_id,
        type_id=type_id,
        league_id=league_id,
        season_id=season_id,
        title=f"{ach_type.name} {league.name} {season.name}",
        icon_path=f"/static/img/cups/{ach_type.code.lower()}.svg",
        base_points=base_points,
        multiplier=multiplier,
        final_points=final_points,
    )
    db.session.add(achievement)
    db.session.flush()
    return None, achievement


@admin_api_bp.route("/managers/<int:manager_id>/achievements/bulk-add", methods=["POST"])
@admin_required
def bulk_add_achievements(manager_id: int) -> Any:
    """API-005: Add multiple achievements to a single manager."""
    try:
        if not current_user.has_permission("create"):
            return jsonify({"error": "Insufficient permissions"}), 403

        err, achievements = _validate_bulk_add_payload(request.get_json())
        if err:
            return err

        manager = db.session.get(Manager, manager_id)
        if not manager:
            return jsonify({"error": "Manager not found"}), 404

        types, leagues, seasons = _batch_load_bulk_add_refs(achievements)

        # VR-003: Pre-load existing achievements (type, league, season) -> achievement_id
        existing_key_map = {
            (e[1], e[2], e[3]): e[0]
            for e in db.session.query(
                Achievement.id,
                Achievement.type_id,
                Achievement.league_id,
                Achievement.season_id,
            )
            .filter(Achievement.manager_id == manager_id)
            .all()
        }

        created: list[int] = []
        skipped: list[dict] = []
        errors: list[dict] = []

        for idx, ach_data in enumerate(achievements):
            error_dict, resolved = _validate_bulk_add_item(idx, ach_data, types, leagues, seasons)
            if error_dict:
                errors.append(error_dict)
                continue
            assert resolved is not None
            type_id, league_id, season_id, ach_type, league, season = resolved

            key = (type_id, league_id, season_id)
            existing_id = existing_key_map.get(key)
            if existing_id:
                skipped.append(_build_skip_record(type_id, ach_type, league, season, existing_id))
                continue

            err_dict, achievement = _create_achievement_for_manager(
                manager_id, type_id, league_id, season_id, ach_type, league, season
            )
            if err_dict:
                errors.append({"index": idx, **err_dict})
                continue
            assert achievement is not None
            created.append(achievement.id)
            existing_key_map[key] = achievement.id  # Prevent intra-batch duplicates

        db.session.commit()
        invalidate_leaderboard_cache()

        total_points = (
            db.session.query(db.func.sum(Achievement.final_points))
            .filter(Achievement.manager_id == manager_id)
            .scalar()
            or 0.0
        )

        return jsonify(
            {
                "success": True,
                "summary": {
                    "total_requested": len(achievements),
                    "created": len(created),
                    "skipped_duplicates": len(skipped),
                    "errors": len(errors),
                },
                "details": {"created_ids": created, "skipped": skipped, "errors": errors},
                "manager_total_points": total_points,
                "recalculation_triggered": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    except Exception as e:
        db.session.rollback()
        api_logger.error(
            f"Error in POST /admin/api/managers/{manager_id}/achievements/bulk-add: {e}"
        )
        return jsonify({"error": "Internal server error"}), 500


@admin_api_bp.route("/managers/<int:manager_id>/achievements/<int:ach_id>", methods=["DELETE"])
@admin_required
def delete_achievement(manager_id: int, ach_id: int) -> Any:
    """Delete a specific achievement for a manager."""
    try:
        if not current_user.has_permission("delete"):
            return jsonify({"error": "Insufficient permissions"}), 403

        achievement = (
            db.session.query(Achievement).filter_by(id=ach_id, manager_id=manager_id).first()
        )

        if not achievement:
            return jsonify({"error": "Achievement not found"}), 404

        db.session.delete(achievement)
        db.session.commit()

        # Invalidate cache
        invalidate_leaderboard_cache()

        return jsonify({"success": True, "message": "Achievement deleted successfully"})

    except Exception as e:
        db.session.rollback()
        api_logger.error(
            f"Error in DELETE /admin/api/managers/{manager_id}/achievements/{ach_id}: {e}"
        )
        return jsonify({"error": "Internal server error"}), 500
