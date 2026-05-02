"""Country CRUD endpoints registered on the ``services.api`` Blueprint."""

from __future__ import annotations

from typing import Any

from flask import jsonify, request

from models import Country, Manager, db
from services.api import api
from services.api_auth import authenticate_api_key
from services.cache_service import invalidate_leaderboard_cache
from services.extensions import limiter
from services.validation_service import validate_country_data, validate_country_unique


@api.route("/countries", methods=["GET"])
@limiter.limit("100 per minute")
def get_countries() -> tuple[Any, int]:
    """Get all countries.

    Returns:
        JSON list of countries.
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
@limiter.limit("100 per minute")
@authenticate_api_key("write")
def create_country() -> tuple[Any, int]:
    """Create a new country."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    code = data.get("code", "")
    flag_path = data.get("flag_path", "")

    is_valid, error = validate_country_data(code, flag_path)
    if not is_valid:
        return jsonify({"error": error}), 400

    is_valid, error = validate_country_unique(db.session, code)
    if not is_valid:
        return jsonify({"error": error}), 409

    country = Country(code=code, flag_path=flag_path)
    db.session.add(country)
    db.session.commit()

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
@limiter.limit("100 per minute")
def get_country(country_id: int) -> tuple[Any, int]:
    """Get a specific country by ID."""
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
@limiter.limit("100 per minute")
@authenticate_api_key("write")
def update_country(country_id: int) -> tuple[Any, int]:
    """Update a country."""
    country = db.session.query(Country).filter_by(id=country_id).first()

    if not country:
        return jsonify({"error": f"Country with ID {country_id} not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "code" in data:
        new_code = data["code"]
        existing = db.session.query(Country).filter_by(code=new_code).first()
        if existing and existing.id != country_id:
            return jsonify({"error": f"Country with code '{new_code}' already exists"}), 409
        country.code = new_code

    if "flag_path" in data:
        country.flag_path = data["flag_path"]

    db.session.commit()
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
@limiter.limit("100 per minute")
@authenticate_api_key("admin")
def delete_country(country_id: int) -> tuple[Any, int]:
    """Delete a country."""
    country = db.session.query(Country).filter_by(id=country_id).first()

    if not country:
        return jsonify({"error": f"Country with ID {country_id} not found"}), 404

    managers_count = db.session.query(Manager).filter_by(country_id=country_id).count()
    if managers_count > 0:
        return jsonify({"error": f"Cannot delete country with {managers_count} manager(s)"}), 409

    db.session.delete(country)
    db.session.commit()
    invalidate_leaderboard_cache()

    return jsonify({"message": "Country deleted successfully"}), 200
