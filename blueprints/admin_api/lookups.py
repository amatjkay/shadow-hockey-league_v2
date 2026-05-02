"""Lookup endpoints for Select2 dropdowns and the points calculator.

Includes simple GET endpoints for countries, managers, seasons, leagues,
achievement types, and the league-aware points calculator.
"""

from __future__ import annotations

from typing import Any

from flask import jsonify, request
from sqlalchemy.orm import joinedload

from blueprints.admin_api import admin_api_bp, admin_required, api_logger
from blueprints.admin_api._helpers import paginate_query
from models import AchievementType, Country, League, Manager, Season, db
from services.scoring_service import get_base_points


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
        result = paginate_query(query, page, page_size)

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
                    .filter(Manager.id.in_(ids), Manager.is_active == True)  # noqa: E712
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
        result = paginate_query(query, page, page_size)

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


@admin_api_bp.route("/leagues", methods=["GET"])
@admin_required
def get_leagues() -> Any:
    """API-005: List all active leagues."""
    try:
        leagues = db.session.query(League).filter_by(is_active=True).order_by(League.code).all()

        return jsonify(
            {
                "items": [
                    {"id": lg.id, "code": lg.code, "name": lg.name, "is_active": lg.is_active}
                    for lg in leagues
                ]
            }
        )
    except Exception as e:
        api_logger.error(f"Error in GET /admin/api/leagues: {e}")
        return jsonify({"error": "Internal server error"}), 500


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
