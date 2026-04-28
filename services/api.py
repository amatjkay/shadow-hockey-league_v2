"""REST API Blueprint for manager management.

This module provides REST endpoints for CRUD operations on managers,
countries, and achievements.

Этап 5: Добавлена аутентификация API ключами и пагинация.
"""

from __future__ import annotations

import math
from typing import Any

from flask import Blueprint, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Achievement, AchievementType, Country, League, Manager, Season, db
from services.api_auth import authenticate_api_key
from services.cache_service import invalidate_leaderboard_cache
from services.validation_service import (
    validate_achievement_data,
    validate_country_data,
    validate_country_exists,
    validate_country_unique,
    validate_manager_data,
    validate_manager_exists,
    validate_manager_unique,
)

api = Blueprint("api", __name__, url_prefix="/api")

# Rate limiter for API endpoints (100 requests per minute per key)
api_limiter = Limiter(
    key_func=lambda: request.headers.get("X-API-Key", get_remote_address()),
    default_limits=["100 per minute"],
)


def get_session() -> Session:
    """Get database session from current Flask app."""
    return db.session


def paginate_query(query, schema, default_per_page: int = 20, max_per_page: int = 100):
    """Apply offset/limit pagination to a query.

    Args:
        query: SQLAlchemy query object
        schema: Schema function to serialize results
        default_per_page: Default items per page
        max_per_page: Maximum allowed items per page

    Returns:
        Tuple of (response_dict, status_code)
    """
    # Get pagination parameters
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=default_per_page, type=int)

    # Enforce limits
    page = max(1, page)
    per_page = min(max(per_page, 1), max_per_page)

    # Get total count
    total = query.count()
    pages = math.ceil(total / per_page) if total > 0 else 0

    # Apply offset/limit
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()

    return {
        "data": [schema(item) for item in items],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
        },
    }, 200


# ============== Countries ==============


@api.route("/countries", methods=["GET"])
@api_limiter.limit("100 per minute")
def get_countries() -> tuple[Any, int]:
    """Get all countries.

    Returns:
        JSON list of countries
    """
    countries = db.session.query(Country).order_by(Country.code).all()

    return (
        jsonify(
            [
                {
                    "id": c.id,
                    "code": c.code,
                    "flag_path": c.flag_path,
                }
                for c in countries
            ]
        ),
        200,
    )


@api.route("/countries", methods=["POST"])
@api_limiter.limit("100 per minute")
@authenticate_api_key("write")
def create_country() -> tuple[Any, int]:
    """Create a new country.

    Request JSON:
        {
            "code": "RUS",  # 3 letters, required
            "flag_path": "/static/img/flags/rus.png"  # required
        }

    Returns:
        JSON with created country or error
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Validate data format
    code = data.get("code", "")
    flag_path = data.get("flag_path", "")

    is_valid, error = validate_country_data(code, flag_path)
    if not is_valid:
        return jsonify({"error": error}), 400

    # Check uniqueness
    is_valid, error = validate_country_unique(db.session, code)
    if not is_valid:
        return jsonify({"error": error}), 409

    # Create country
    country = Country(code=code, flag_path=flag_path)
    db.session.add(country)
    db.session.commit()

    # Invalidate leaderboard cache
    invalidate_leaderboard_cache()

    return (
        jsonify(
            {
                "id": country.id,
                "code": country.code,
                "flag_path": country.flag_path,
                "message": "Country created successfully",
            }
        ),
        201,
    )


@api.route("/countries/<int:country_id>", methods=["GET"])
@api_limiter.limit("100 per minute")
def get_country(country_id: int) -> tuple[Any, int]:
    """Get a specific country by ID.

    Args:
        country_id: Country ID

    Returns:
        JSON with country data or error
    """
    country = db.session.query(Country).filter_by(id=country_id).first()

    if not country:
        return jsonify({"error": f"Country with ID {country_id} not found"}), 404

    return (
        jsonify(
            {
                "id": country.id,
                "code": country.code,
                "flag_path": country.flag_path,
            }
        ),
        200,
    )


@api.route("/countries/<int:country_id>", methods=["PUT"])
@api_limiter.limit("100 per minute")
@authenticate_api_key("write")
def update_country(country_id: int) -> tuple[Any, int]:
    """Update a country.

    Args:
        country_id: Country ID

    Request JSON:
        {
            "code": "RUS",  # optional
            "flag_path": "/static/img/flags/rus.png"  # optional
        }

    Returns:
        JSON with updated country or error
    """
    country = db.session.query(Country).filter_by(id=country_id).first()

    if not country:
        return jsonify({"error": f"Country with ID {country_id} not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update fields
    if "code" in data:
        new_code = data["code"]
        # Check uniqueness
        existing = db.session.query(Country).filter_by(code=new_code).first()
        if existing and existing.id != country_id:
            return jsonify({"error": f"Country with code '{new_code}' already exists"}), 409
        country.code = new_code

    if "flag_path" in data:
        country.flag_path = data["flag_path"]

    db.session.commit()

    # Invalidate leaderboard cache
    invalidate_leaderboard_cache()

    return (
        jsonify(
            {
                "id": country.id,
                "code": country.code,
                "flag_path": country.flag_path,
                "message": "Country updated successfully",
            }
        ),
        200,
    )


@api.route("/countries/<int:country_id>", methods=["DELETE"])
@api_limiter.limit("100 per minute")
@authenticate_api_key("admin")
def delete_country(country_id: int) -> tuple[Any, int]:
    """Delete a country.

    Args:
        country_id: Country ID

    Returns:
        JSON with success message or error
    """
    country = db.session.query(Country).filter_by(id=country_id).first()

    if not country:
        return jsonify({"error": f"Country with ID {country_id} not found"}), 404

    # Check if country has managers
    managers_count = db.session.query(Manager).filter_by(country_id=country_id).count()
    if managers_count > 0:
        return jsonify({"error": f"Cannot delete country with {managers_count} manager(s)"}), 409

    db.session.delete(country)
    db.session.commit()

    # Invalidate leaderboard cache
    invalidate_leaderboard_cache()

    return jsonify({"message": "Country deleted successfully"}), 200


# ============== Managers ==============


@api.route("/managers", methods=["GET"])
@api_limiter.limit("100 per minute")
@authenticate_api_key("read")
def get_managers() -> tuple[Any, int]:
    """Get all managers with optional filtering and pagination.

    Query params:
        country_id: Filter by country ID
        search: Search by name (case-insensitive)
        page: Page number (default: 1)
        per_page: Items per page (default: 20, max: 100)

    Returns:
        JSON with paginated list of managers
    """
    query = db.session.query(Manager).join(Country)

    # Apply filters
    country_id = request.args.get("country_id", type=int)
    if country_id:
        query = query.filter(Manager.country_id == country_id)

    search = request.args.get("search", "")
    if search:
        query = query.filter(Manager.name.ilike(f"%{search}%"))

    query = query.order_by(Manager.name)

    def serialize_manager(m: Manager) -> dict:
        return {
            "id": m.id,
            "name": m.name,
            "display_name": m.display_name,
            "is_tandem": m.is_tandem,
            "country_id": m.country_id,
            "country_code": m.country.code,
            "achievements_count": len(m.achievements),
        }

    return paginate_query(query, serialize_manager)


@api.route("/managers", methods=["POST"])
@api_limiter.limit("100 per minute")
@authenticate_api_key("write")
def create_manager() -> tuple[Any, int]:
    """Create a new manager.

    Request JSON:
        {
            "name": "John Doe",  # required, unique
            "country_id": 1  # required, must exist
        }

    Returns:
        JSON with created manager or error
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    name = data.get("name", "")
    country_id = data.get("country_id")

    # Validate data format
    is_valid, error = validate_manager_data(name, country_id)
    if not is_valid:
        return jsonify({"error": error}), 400

    # Check uniqueness
    is_valid, error = validate_manager_unique(db.session, name)
    if not is_valid:
        return jsonify({"error": error}), 409

    # Check country exists
    is_valid, error = validate_country_exists(db.session, country_id)
    if not is_valid:
        return jsonify({"error": error}), 400

    # Create manager
    manager = Manager(name=name, country_id=country_id)
    db.session.add(manager)
    db.session.commit()

    # Invalidate leaderboard cache
    invalidate_leaderboard_cache()

    return (
        jsonify(
            {
                "id": manager.id,
                "name": manager.name,
                "display_name": manager.display_name,
                "is_tandem": manager.is_tandem,
                "country_id": manager.country_id,
                "message": "Manager created successfully",
            }
        ),
        201,
    )


@api.route("/managers/<int:manager_id>", methods=["GET"])
@api_limiter.limit("100 per minute")
@authenticate_api_key("read")
def get_manager(manager_id: int) -> tuple[Any, int]:
    """Get a specific manager by ID with achievements.

    Args:
        manager_id: Manager ID

    Returns:
        JSON with manager data and achievements
    """
    manager = db.session.query(Manager).filter_by(id=manager_id).first()

    if not manager:
        return jsonify({"error": f"Manager with ID {manager_id} not found"}), 404

    return (
        jsonify(
            {
                "id": manager.id,
                "name": manager.name,
                "display_name": manager.display_name,
                "is_tandem": manager.is_tandem,
                "country_id": manager.country_id,
                "country_code": manager.country.code,
                "achievements": [
                    {
                        "id": a.id,
                        "type_id": a.type_id,
                        "league_id": a.league_id,
                        "season_id": a.season_id,
                        "achievement_type": a.type.code if a.type else None,
                        "league": a.league.code if a.league else None,
                        "season": a.season.code if a.season else None,
                        "title": a.title,
                        "icon_path": a.icon_path,
                    }
                    for a in manager.achievements
                ],
            }
        ),
        200,
    )


@api.route("/managers/<int:manager_id>", methods=["PUT"])
@api_limiter.limit("100 per minute")
@authenticate_api_key("write")
def update_manager(manager_id: int) -> tuple[Any, int]:
    """Update a manager.

    Args:
        manager_id: Manager ID

    Request JSON:
        {
            "name": "John Doe",  # optional, must be unique
            "country_id": 1  # optional, must exist
        }

    Returns:
        JSON with updated manager or error
    """
    manager = db.session.query(Manager).filter_by(id=manager_id).first()

    if not manager:
        return jsonify({"error": f"Manager with ID {manager_id} not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update name
    if "name" in data:
        new_name = data["name"]
        # Check uniqueness
        existing = db.session.query(Manager).filter_by(name=new_name).first()
        if existing and existing.id != manager_id:
            return jsonify({"error": f"Manager with name '{new_name}' already exists"}), 409
        manager.name = new_name

    # Update country
    if "country_id" in data:
        new_country_id = data["country_id"]
        # Check country exists
        is_valid, error = validate_country_exists(db.session, new_country_id)
        if not is_valid:
            return jsonify({"error": error}), 400
        manager.country_id = new_country_id

    db.session.commit()

    # Invalidate leaderboard cache
    invalidate_leaderboard_cache()

    return (
        jsonify(
            {
                "id": manager.id,
                "name": manager.name,
                "display_name": manager.display_name,
                "is_tandem": manager.is_tandem,
                "country_id": manager.country_id,
                "message": "Manager updated successfully",
            }
        ),
        200,
    )


@api.route("/managers/<int:manager_id>", methods=["DELETE"])
@api_limiter.limit("100 per minute")
@authenticate_api_key("admin")
def delete_manager(manager_id: int) -> tuple[Any, int]:
    """Delete a manager (and all achievements via CASCADE).

    Args:
        manager_id: Manager ID

    Returns:
        JSON with success message or error
    """
    manager = db.session.query(Manager).filter_by(id=manager_id).first()

    if not manager:
        return jsonify({"error": f"Manager with ID {manager_id} not found"}), 404

    db.session.delete(manager)
    db.session.commit()

    # Invalidate leaderboard cache (achievements deleted via CASCADE)
    invalidate_leaderboard_cache()

    return jsonify({"message": "Manager deleted successfully"}), 200


# ============== Achievements ==============


@api.route("/achievements", methods=["GET"])
@api_limiter.limit("100 per minute")
@authenticate_api_key("read")
def get_achievements() -> tuple[Any, int]:
    """Get all achievements with optional filtering and pagination.

    Query params:
        manager_id: Filter by manager ID
        league: Filter by league (1 or 2)
        season: Filter by season (e.g., "24/25")
        achievement_type: Filter by type (e.g., "TOP1")
        page: Page number (default: 1)
        per_page: Items per page (default: 20, max: 100)

    Returns:
        JSON with paginated list of achievements
    """
    query = db.session.query(Achievement)

    # Apply filters
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
@api_limiter.limit("100 per minute")
@authenticate_api_key("write")
def create_achievement() -> tuple[Any, int]:
    """Create a new achievement.

    Request JSON:
        {
            "type_code": "TOP1",  # required (or legacy "achievement_type")
            "league_code": "1",   # required (or legacy "league")
            "season_code": "24/25",  # required (or legacy "season")
            "title": "Shadow 1 league TOP1",  # required
            "icon_path": "/static/img/cups/top1.svg",  # required
            "manager_id": 1  # required, must exist
        }

    Returns:
        JSON with created achievement or error
    """
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

    # Validate data format
    is_valid, error = validate_achievement_data(type_code, league_code, season_code, title)
    if not is_valid:
        return jsonify({"error": error}), 400

    # Check manager exists
    is_valid, error = validate_manager_exists(db.session, manager_id)
    if not is_valid:
        return jsonify({"error": error}), 400

    # Look up reference data
    ach_type = db.session.query(AchievementType).filter_by(code=type_code).first()
    if not ach_type:
        return jsonify({"error": f"Achievement type '{type_code}' not found"}), 400

    league = db.session.query(League).filter_by(code=league_code).first()
    if not league:
        return jsonify({"error": f"League '{league_code}' not found"}), 400

    season = db.session.query(Season).filter_by(code=season_code).first()
    if not season:
        return jsonify({"error": f"Season '{season_code}' not found"}), 400

    # Calculate points
    base_points = ach_type.base_points_l1 if league.code == "1" else ach_type.base_points_l2
    multiplier = season.multiplier
    final_points = base_points * multiplier

    # Create achievement
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

    # Invalidate leaderboard cache
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
@api_limiter.limit("100 per minute")
@authenticate_api_key("read")
def get_achievement(achievement_id: int) -> tuple[Any, int]:
    """Get a specific achievement by ID.

    Args:
        achievement_id: Achievement ID

    Returns:
        JSON with achievement data or error
    """
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


@api.route("/achievements/<int:achievement_id>", methods=["PUT"])
@api_limiter.limit("100 per minute")
@authenticate_api_key("write")
def update_achievement(achievement_id: int) -> tuple[Any, int]:
    """Update an achievement.

    Args:
        achievement_id: Achievement ID

    Request JSON:
        {
            "type_code": "TOP1",  # optional (or legacy "achievement_type")
            "league_code": "1",   # optional (or legacy "league")
            "season_code": "24/25",  # optional (or legacy "season")
            "title": "Shadow 1 league TOP1",  # optional
            "icon_path": "/static/img/cups/top1.svg",  # optional
            "manager_id": 1  # optional, must exist
        }

    Returns:
        JSON with updated achievement or error
    """
    achievement = db.session.query(Achievement).filter_by(id=achievement_id).first()

    if not achievement:
        return jsonify({"error": f"Achievement with ID {achievement_id} not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update type
    type_code = data.get("type_code") or data.get("achievement_type")
    if type_code:
        ach_type = db.session.query(AchievementType).filter_by(code=type_code).first()
        if not ach_type:
            return jsonify({"error": f"Achievement type '{type_code}' not found"}), 400
        achievement.type_id = ach_type.id

    # Update league
    league_code = data.get("league_code") or data.get("league")
    if league_code:
        league = db.session.query(League).filter_by(code=league_code).first()
        if not league:
            return jsonify({"error": f"League '{league_code}' not found"}), 400
        achievement.league_id = league.id

    # Update season
    season_code = data.get("season_code") or data.get("season")
    if season_code:
        season = db.session.query(Season).filter_by(code=season_code).first()
        if not season:
            return jsonify({"error": f"Season '{season_code}' not found"}), 400
        achievement.season_id = season.id

    if "title" in data:
        achievement.title = data["title"]

    if "icon_path" in data:
        achievement.icon_path = data["icon_path"]

    if "manager_id" in data:
        new_manager_id = data["manager_id"]
        # Check manager exists
        is_valid, error = validate_manager_exists(db.session, new_manager_id)
        if not is_valid:
            return jsonify({"error": error}), 400
        achievement.manager_id = new_manager_id

    # Recalculate points if any FK field changed
    if type_code or league_code or season_code:
        # Refresh relationships to get updated values
        db.session.refresh(achievement, attribute_names=["type", "league", "season"])
        if achievement.type and achievement.league and achievement.season:
            achievement.base_points = float(
                achievement.type.base_points_l1
                if achievement.league.code == "1"
                else achievement.type.base_points_l2
            )
            achievement.multiplier = float(achievement.season.multiplier)
            achievement.final_points = float(achievement.base_points * achievement.multiplier)

    db.session.commit()

    # Invalidate leaderboard cache
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
@api_limiter.limit("100 per minute")
@authenticate_api_key("admin")
def delete_achievement(achievement_id: int) -> tuple[Any, int]:
    """Delete an achievement.

    Args:
        achievement_id: Achievement ID

    Returns:
        JSON with success message or error
    """
    achievement = db.session.query(Achievement).filter_by(id=achievement_id).first()

    if not achievement:
        return jsonify({"error": f"Achievement with ID {achievement_id} not found"}), 404

    db.session.delete(achievement)
    db.session.commit()

    # Invalidate leaderboard cache
    invalidate_leaderboard_cache()

    return jsonify({"message": "Achievement deleted successfully"}), 200
