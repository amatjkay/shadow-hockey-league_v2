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


_VALID_ACHIEVEMENT_TYPES = frozenset(
    {"TOP1", "TOP2", "TOP3", "BEST", "R3", "R1", "BEST_REG", "HOCKEY_STICKS_AND_PUCK"}
)
_REQUIRED_ACHIEVEMENT_FIELDS = (
    "manager_name",
    "type",
    "league",
    "season",
    "title",
    "icon_filename",
)


def _check_required_fields(item: dict, prefix: str) -> list[str]:
    return [
        f"{prefix}: Missing required field '{field}'"
        for field in _REQUIRED_ACHIEVEMENT_FIELDS
        if field not in item
    ]


def _check_manager_name(value: Any, prefix: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, str) or len(value.strip()) == 0:
        return [f"{prefix}: 'manager_name' must be a non-empty string"]
    return []


def _check_achievement_type(value: Any, prefix: str) -> list[str]:
    if value is None or value in _VALID_ACHIEVEMENT_TYPES:
        return []
    return [f"{prefix}: 'type' must be one of {_VALID_ACHIEVEMENT_TYPES}"]


def _check_league_code(value: Any, prefix: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, str) or not value.isdigit() or int(value) < 1:
        return [f"{prefix}: 'league' must be a positive number string"]
    return []


def _check_season_code(value: Any, prefix: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, str) or "/" not in value:
        return [f"{prefix}: 'season' must be in format 'YY/YY' (e.g. '22/23')"]
    return []


def _check_icon_filename(value: Any, prefix: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, str) or not value.endswith((".svg", ".png")):
        return [f"{prefix}: 'icon_filename' must end with .svg or .png"]
    return []


def _validate_achievement_item(item: Any, prefix: str) -> list[str]:
    if not isinstance(item, dict):
        return [f"{prefix}: Must be an object"]
    errors: list[str] = []
    errors.extend(_check_required_fields(item, prefix))
    errors.extend(_check_manager_name(item.get("manager_name"), prefix))
    errors.extend(_check_achievement_type(item.get("type"), prefix))
    errors.extend(_check_league_code(item.get("league"), prefix))
    errors.extend(_check_season_code(item.get("season"), prefix))
    errors.extend(_check_icon_filename(item.get("icon_filename"), prefix))
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
    if not isinstance(data, list):
        return ["Achievements data must be a list"]

    errors: list[str] = []
    for i, item in enumerate(data):
        errors.extend(_validate_achievement_item(item, f"Achievements[{i}]"))
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
