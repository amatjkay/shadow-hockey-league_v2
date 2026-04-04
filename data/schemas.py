"""JSON schema validation for seed and export data.

Validates the structure and content of JSON files used for seeding
and exporting database data.

Usage:
    from data.schemas import validate_countries, validate_managers

    errors = validate_countries(data)
    if errors:
        for error in errors:
            print(f"Validation error: {error}")
"""

from __future__ import annotations

from typing import Any


def validate_countries(data: Any) -> list[str]:
    """Validate countries JSON data structure.

    Expected format:
    [
        {"code": "RUS", "name": "Russia", "flag_filename": "rus.png"},
        ...
    ]

    Args:
        data: Parsed JSON data (should be a list of dicts).

    Returns:
        List of validation error messages. Empty if valid.
    """
    errors: list[str] = []

    if not isinstance(data, list):
        errors.append("Countries data must be a list")
        return errors

    codes_seen: set[str] = set()

    for i, item in enumerate(data):
        prefix = f"Countries[{i}]"

        if not isinstance(item, dict):
            errors.append(f"{prefix}: Must be an object")
            continue

        # Required fields
        for field in ("code", "name", "flag_filename"):
            if field not in item:
                errors.append(f"{prefix}: Missing required field '{field}'")

        # Validate code
        code = item.get("code")
        if code is not None:
            if not isinstance(code, str) or len(code) < 2 or len(code) > 3:
                errors.append(f"{prefix}: 'code' must be 2-3 characters")
            elif code in codes_seen:
                errors.append(f"{prefix}: Duplicate country code '{code}'")
            else:
                codes_seen.add(code)

        # Validate name
        name = item.get("name")
        if name is not None:
            if not isinstance(name, str) or len(name.strip()) == 0:
                errors.append(f"{prefix}: 'name' must be a non-empty string")

        # Validate flag_filename
        flag = item.get("flag_filename")
        if flag is not None:
            if not isinstance(flag, str) or not flag.endswith(".png"):
                errors.append(f"{prefix}: 'flag_filename' must end with .png")

    return errors


def validate_managers(data: Any) -> list[str]:
    """Validate managers JSON data structure.

    Expected format:
    [
        {"name": "Feel Good", "country_code": "BEL"},
        ...
    ]

    Args:
        data: Parsed JSON data (should be a list of dicts).

    Returns:
        List of validation error messages. Empty if valid.
    """
    errors: list[str] = []

    if not isinstance(data, list):
        errors.append("Managers data must be a list")
        return errors

    names_seen: set[str] = set()

    for i, item in enumerate(data):
        prefix = f"Managers[{i}]"

        if not isinstance(item, dict):
            errors.append(f"{prefix}: Must be an object")
            continue

        # Required fields
        for field in ("name", "country_code"):
            if field not in item:
                errors.append(f"{prefix}: Missing required field '{field}'")

        # Validate name
        name = item.get("name")
        if name is not None:
            if not isinstance(name, str) or len(name.strip()) == 0:
                errors.append(f"{prefix}: 'name' must be a non-empty string")
            elif name in names_seen:
                errors.append(f"{prefix}: Duplicate manager name '{name}'")
            else:
                names_seen.add(name)

        # Validate country_code
        code = item.get("country_code")
        if code is not None:
            if not isinstance(code, str) or len(code) < 2 or len(code) > 3:
                errors.append(f"{prefix}: 'country_code' must be 2-3 characters")

    return errors


def validate_achievements(data: Any) -> list[str]:
    """Validate achievements JSON data structure.

    Expected format:
    [
        {
            "manager_name": "Feel Good",
            "type": "TOP1",
            "league": "1",
            "season": "22/23",
            "title": "TOP1",
            "icon_filename": "top1.svg"
        },
        ...
    ]

    Args:
        data: Parsed JSON data (should be a list of dicts).

    Returns:
        List of validation error messages. Empty if valid.
    """
    errors: list[str] = []

    if not isinstance(data, list):
        errors.append("Achievements data must be a list")
        return errors

    valid_types = {"TOP1", "TOP2", "TOP3", "BEST", "R3", "R1"}

    for i, item in enumerate(data):
        prefix = f"Achievements[{i}]"

        if not isinstance(item, dict):
            errors.append(f"{prefix}: Must be an object")
            continue

        # Required fields
        required_fields = ("manager_name", "type", "league", "season", "title", "icon_filename")
        for field in required_fields:
            if field not in item:
                errors.append(f"{prefix}: Missing required field '{field}'")

        # Validate manager_name
        manager_name = item.get("manager_name")
        if manager_name is not None:
            if not isinstance(manager_name, str) or len(manager_name.strip()) == 0:
                errors.append(f"{prefix}: 'manager_name' must be a non-empty string")

        # Validate type
        ach_type = item.get("type")
        if ach_type is not None:
            if ach_type not in valid_types:
                errors.append(f"{prefix}: 'type' must be one of {valid_types}")

        # Validate league
        league = item.get("league")
        if league is not None:
            if not isinstance(league, str) or not league.isdigit() or int(league) < 1:
                errors.append(f"{prefix}: 'league' must be a positive number string")

        # Validate season
        season = item.get("season")
        if season is not None:
            if not isinstance(season, str) or "/" not in season:
                errors.append(f"{prefix}: 'season' must be in format 'YY/YY' (e.g. '22/23')")

        # Validate icon_filename
        icon = item.get("icon_filename")
        if icon is not None:
            if not isinstance(icon, str) or not icon.endswith((".svg", ".png")):
                errors.append(f"{prefix}: 'icon_filename' must end with .svg or .png")

    return errors


def validate_all(countries: Any, managers: Any, achievements: Any) -> dict[str, list[str]]:
    """Validate all data structures at once.

    Args:
        countries: Countries JSON data.
        managers: Managers JSON data.
        achievements: Achievements JSON data.

    Returns:
        Dictionary with validation errors per section.
    """
    return {
        "countries": validate_countries(countries),
        "managers": validate_managers(managers),
        "achievements": validate_achievements(achievements),
    }
