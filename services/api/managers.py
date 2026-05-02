"""Manager CRUD endpoints registered on the ``services.api`` Blueprint."""

from __future__ import annotations

from typing import Any

from flask import jsonify, request
from sqlalchemy.orm import joinedload, selectinload

from models import Achievement, Country, Manager, db
from services.api import api
from services.api._helpers import paginate_query
from services.api_auth import authenticate_api_key
from services.cache_service import invalidate_leaderboard_cache
from services.extensions import limiter
from services.validation_service import (
    validate_country_exists,
    validate_manager_data,
    validate_manager_unique,
)


@api.route("/managers", methods=["GET"])
@limiter.limit("100 per minute")
@authenticate_api_key("read")
def get_managers() -> tuple[Any, int]:
    """Get all managers with optional filtering and pagination."""
    # Eager-load country and achievements to avoid N+1.
    query = (
        db.session.query(Manager)
        .options(joinedload(Manager.country), selectinload(Manager.achievements))
        .join(Country)
    )

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
@limiter.limit("100 per minute")
@authenticate_api_key("write")
def create_manager() -> tuple[Any, int]:
    """Create a new manager."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    name = data.get("name", "")
    country_id = data.get("country_id")

    is_valid, error = validate_manager_data(name, country_id)
    if not is_valid:
        return jsonify({"error": error}), 400

    is_valid, error = validate_manager_unique(db.session, name)
    if not is_valid:
        return jsonify({"error": error}), 409

    is_valid, error = validate_country_exists(db.session, country_id)
    if not is_valid:
        return jsonify({"error": error}), 400

    manager = Manager(name=name, country_id=country_id)
    db.session.add(manager)
    db.session.commit()
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
@limiter.limit("100 per minute")
@authenticate_api_key("read")
def get_manager(manager_id: int) -> tuple[Any, int]:
    """Get a specific manager by ID with achievements."""
    # Eager-load country + the relationship chain used by serialisation so the
    # endpoint runs in O(1) queries instead of O(achievements*3) + 1.
    manager = (
        db.session.query(Manager)
        .options(
            joinedload(Manager.country),
            selectinload(Manager.achievements).joinedload(Achievement.type),
            selectinload(Manager.achievements).joinedload(Achievement.league),
            selectinload(Manager.achievements).joinedload(Achievement.season),
        )
        .filter_by(id=manager_id)
        .first()
    )

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
@limiter.limit("100 per minute")
@authenticate_api_key("write")
def update_manager(manager_id: int) -> tuple[Any, int]:
    """Update a manager."""
    manager = db.session.query(Manager).filter_by(id=manager_id).first()

    if not manager:
        return jsonify({"error": f"Manager with ID {manager_id} not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "name" in data:
        new_name = data["name"]
        existing = db.session.query(Manager).filter_by(name=new_name).first()
        if existing and existing.id != manager_id:
            return jsonify({"error": f"Manager with name '{new_name}' already exists"}), 409
        manager.name = new_name

    if "country_id" in data:
        new_country_id = data["country_id"]
        is_valid, error = validate_country_exists(db.session, new_country_id)
        if not is_valid:
            return jsonify({"error": error}), 400
        manager.country_id = new_country_id

    db.session.commit()
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
@limiter.limit("100 per minute")
@authenticate_api_key("admin")
def delete_manager(manager_id: int) -> tuple[Any, int]:
    """Delete a manager (achievements removed via CASCADE)."""
    manager = db.session.query(Manager).filter_by(id=manager_id).first()

    if not manager:
        return jsonify({"error": f"Manager with ID {manager_id} not found"}), 404

    db.session.delete(manager)
    db.session.commit()
    invalidate_leaderboard_cache()

    return jsonify({"message": "Manager deleted successfully"}), 200
