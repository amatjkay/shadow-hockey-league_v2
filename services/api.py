"""REST API Blueprint for manager management.

This module provides REST endpoints for CRUD operations on managers,
countries, and achievements.
"""

from __future__ import annotations

from typing import Any

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.orm import Session

from models import Achievement, Country, Manager, db
from services.validation_service import (
    DataValidator,
    validate_achievement_data,
    validate_country_data,
    validate_country_exists,
    validate_country_unique,
    validate_manager_data,
    validate_manager_exists,
    validate_manager_unique,
)

api = Blueprint("api", __name__, url_prefix="/api")


def get_session() -> Session:
    """Get database session from current Flask app."""
    return db.session


# ============== Countries ==============

@api.route("/countries", methods=["GET"])
def get_countries() -> tuple[Any, int]:
    """Get all countries.

    Returns:
        JSON list of countries
    """
    countries = db.session.query(Country).order_by(Country.code).all()

    return jsonify([
        {
            "id": c.id,
            "code": c.code,
            "flag_path": c.flag_path,
        }
        for c in countries
    ]), 200


@api.route("/countries", methods=["POST"])
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

    return jsonify({
        "id": country.id,
        "code": country.code,
        "flag_path": country.flag_path,
        "message": "Country created successfully"
    }), 201


@api.route("/countries/<int:country_id>", methods=["GET"])
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

    return jsonify({
        "id": country.id,
        "code": country.code,
        "flag_path": country.flag_path,
    }), 200


@api.route("/countries/<int:country_id>", methods=["PUT"])
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

    return jsonify({
        "id": country.id,
        "code": country.code,
        "flag_path": country.flag_path,
        "message": "Country updated successfully"
    }), 200


@api.route("/countries/<int:country_id>", methods=["DELETE"])
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
        return jsonify({
            "error": f"Cannot delete country with {managers_count} manager(s)"
        }), 409

    db.session.delete(country)
    db.session.commit()

    return jsonify({"message": "Country deleted successfully"}), 200


# ============== Managers ==============

@api.route("/managers", methods=["GET"])
def get_managers() -> tuple[Any, int]:
    """Get all managers with optional filtering.

    Query params:
        country_id: Filter by country ID
        search: Search by name (case-insensitive)

    Returns:
        JSON list of managers
    """
    query = db.session.query(Manager).join(Country)

    # Apply filters
    country_id = request.args.get("country_id", type=int)
    if country_id:
        query = query.filter(Manager.country_id == country_id)

    search = request.args.get("search", "")
    if search:
        query = query.filter(Manager.name.ilike(f"%{search}%"))

    managers = query.order_by(Manager.name).all()

    return jsonify([
        {
            "id": m.id,
            "name": m.name,
            "display_name": m.display_name,
            "is_tandem": m.is_tandem,
            "country_id": m.country_id,
            "country_code": m.country.code,
            "achievements_count": len(m.achievements),
        }
        for m in managers
    ]), 200


@api.route("/managers", methods=["POST"])
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

    return jsonify({
        "id": manager.id,
        "name": manager.name,
        "display_name": manager.display_name,
        "is_tandem": manager.is_tandem,
        "country_id": manager.country_id,
        "message": "Manager created successfully"
    }), 201


@api.route("/managers/<int:manager_id>", methods=["GET"])
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

    return jsonify({
        "id": manager.id,
        "name": manager.name,
        "display_name": manager.display_name,
        "is_tandem": manager.is_tandem,
        "country_id": manager.country_id,
        "country_code": manager.country.code,
        "achievements": [
            {
                "id": a.id,
                "achievement_type": a.achievement_type,
                "league": a.league,
                "season": a.season,
                "title": a.title,
                "icon_path": a.icon_path,
            }
            for a in manager.achievements
        ],
    }), 200


@api.route("/managers/<int:manager_id>", methods=["PUT"])
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

    return jsonify({
        "id": manager.id,
        "name": manager.name,
        "display_name": manager.display_name,
        "is_tandem": manager.is_tandem,
        "country_id": manager.country_id,
        "message": "Manager updated successfully"
    }), 200


@api.route("/managers/<int:manager_id>", methods=["DELETE"])
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

    return jsonify({"message": "Manager deleted successfully"}), 200


# ============== Achievements ==============

@api.route("/achievements", methods=["GET"])
def get_achievements() -> tuple[Any, int]:
    """Get all achievements with optional filtering.

    Query params:
        manager_id: Filter by manager ID
        league: Filter by league (1 or 2)
        season: Filter by season (e.g., "24/25")
        achievement_type: Filter by type (e.g., "TOP1")

    Returns:
        JSON list of achievements
    """
    query = db.session.query(Achievement)

    # Apply filters
    manager_id = request.args.get("manager_id", type=int)
    if manager_id:
        query = query.filter(Achievement.manager_id == manager_id)

    league = request.args.get("league", "")
    if league:
        query = query.filter(Achievement.league == league)

    season = request.args.get("season", "")
    if season:
        query = query.filter(Achievement.season == season)

    achievement_type = request.args.get("achievement_type", "")
    if achievement_type:
        query = query.filter(Achievement.achievement_type == achievement_type)

    achievements = query.order_by(Achievement.season.desc()).all()

    return jsonify([
        {
            "id": a.id,
            "achievement_type": a.achievement_type,
            "league": a.league,
            "season": a.season,
            "title": a.title,
            "icon_path": a.icon_path,
            "manager_id": a.manager_id,
            "manager_name": a.manager.name,
        }
        for a in achievements
    ]), 200


@api.route("/achievements", methods=["POST"])
def create_achievement() -> tuple[Any, int]:
    """Create a new achievement.

    Request JSON:
        {
            "achievement_type": "TOP1",  # required
            "league": "1",  # required (1 or 2)
            "season": "24/25",  # required
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

    achievement_type = data.get("achievement_type", "")
    league = data.get("league", "")
    season = data.get("season", "")
    title = data.get("title", "")
    icon_path = data.get("icon_path", "")
    manager_id = data.get("manager_id", type=int)

    # Validate data format
    is_valid, error = validate_achievement_data(
        achievement_type, league, season, title
    )
    if not is_valid:
        return jsonify({"error": error}), 400

    # Check manager exists
    is_valid, error = validate_manager_exists(db.session, manager_id)
    if not is_valid:
        return jsonify({"error": error}), 400

    # Create achievement
    achievement = Achievement(
        achievement_type=achievement_type,
        league=league,
        season=season,
        title=title,
        icon_path=icon_path,
        manager_id=manager_id,
    )
    db.session.add(achievement)
    db.session.commit()

    return jsonify({
        "id": achievement.id,
        "achievement_type": achievement.achievement_type,
        "league": achievement.league,
        "season": achievement.season,
        "title": achievement.title,
        "icon_path": achievement.icon_path,
        "manager_id": achievement.manager_id,
        "message": "Achievement created successfully"
    }), 201


@api.route("/achievements/<int:achievement_id>", methods=["GET"])
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

    return jsonify({
        "id": achievement.id,
        "achievement_type": achievement.achievement_type,
        "league": achievement.league,
        "season": achievement.season,
        "title": achievement.title,
        "icon_path": achievement.icon_path,
        "manager_id": achievement.manager_id,
        "manager_name": achievement.manager.name,
    }), 200


@api.route("/achievements/<int:achievement_id>", methods=["PUT"])
def update_achievement(achievement_id: int) -> tuple[Any, int]:
    """Update an achievement.

    Args:
        achievement_id: Achievement ID

    Request JSON:
        {
            "achievement_type": "TOP1",  # optional
            "league": "1",  # optional
            "season": "24/25",  # optional
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

    # Update fields
    if "achievement_type" in data:
        achievement.achievement_type = data["achievement_type"]

    if "league" in data:
        achievement.league = data["league"]

    if "season" in data:
        achievement.season = data["season"]

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

    db.session.commit()

    return jsonify({
        "id": achievement.id,
        "achievement_type": achievement.achievement_type,
        "league": achievement.league,
        "season": achievement.season,
        "title": achievement.title,
        "icon_path": achievement.icon_path,
        "manager_id": achievement.manager_id,
        "message": "Achievement updated successfully"
    }), 200


@api.route("/achievements/<int:achievement_id>", methods=["DELETE"])
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

    return jsonify({"message": "Achievement deleted successfully"}), 200
