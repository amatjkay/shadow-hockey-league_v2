"""Validation service for data integrity checks.

This module provides functions to validate data before inserting into database.
"""

from __future__ import annotations

import re
from typing import Any

from models import Country, Manager
from services._types import SessionLike

# Format-only regex for league codes. Matches ``1``, ``2``, ``2.1``, ``3.5``, ``42``,
# but rejects ``0``, ``01``, ``2.``, ``2.1.1``, etc. Existence of the league in the
# database is checked separately (e.g. via ``League.query.filter_by(code=...)``).
_LEAGUE_CODE_RE = re.compile(r"^[1-9]\d*(\.\d+)?$")


class ValidationError(Exception):
    """Custom exception for validation errors."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


def validate_country_unique(session: SessionLike, code: str) -> tuple[bool, str | None]:
    """Check if country code is unique.

    Args:
        session: SQLAlchemy database session
        code: Country code (3 letters)

    Returns:
        Tuple of (is_valid, error_message)
    """
    existing = session.query(Country).filter_by(code=code).first()
    if existing:
        return False, f"Country with code '{code}' already exists"
    return True, None


def validate_manager_unique(session: SessionLike, name: str) -> tuple[bool, str | None]:
    """Check if manager name is unique.

    Args:
        session: SQLAlchemy database session
        name: Manager name

    Returns:
        Tuple of (is_valid, error_message)
    """
    existing = session.query(Manager).filter_by(name=name).first()
    if existing:
        return False, f"Manager with name '{name}' already exists"
    return True, None


def validate_country_exists(session: SessionLike, country_id: int) -> tuple[bool, str | None]:
    """Check if country exists.

    Args:
        session: SQLAlchemy database session
        country_id: Country ID

    Returns:
        Tuple of (is_valid, error_message)
    """
    existing = session.query(Country).filter_by(id=country_id).first()
    if not existing:
        return False, f"Country with ID {country_id} does not exist"
    return True, None


def validate_manager_exists(session: SessionLike, manager_id: int) -> tuple[bool, str | None]:
    """Check if manager exists.

    Args:
        session: SQLAlchemy database session
        manager_id: Manager ID

    Returns:
        Tuple of (is_valid, error_message)
    """
    existing = session.query(Manager).filter_by(id=manager_id).first()
    if not existing:
        return False, f"Manager with ID {manager_id} does not exist"
    return True, None


def validate_achievement_data(
    achievement_type: str, league: str, season: str, title: str
) -> tuple[bool, str | None]:
    """Validate achievement data format.

    Args:
        achievement_type: Type of achievement (TOP1, TOP2, etc.)
        league: League number (1 or 2)
        season: Season string (e.g., "24/25")
        title: Achievement title

    Returns:
        Tuple of (is_valid, error_message)
    """
    errors: list[str] = []

    if not achievement_type:
        errors.append("Achievement type is required")

    if not _LEAGUE_CODE_RE.match(league or ""):
        errors.append(
            f"League must match format 'N' or 'N.M' (digits, no leading zeros), got '{league}'"
        )
    elif league.startswith("1."):
        # L1 is a flat division — subleagues are reserved for L2+ per project rules.
        errors.append(f"League 1 has no subleagues, got '{league}'")

    if not season:
        errors.append("Season is required")

    if not title:
        errors.append("Title is required")

    if errors:
        return False, "; ".join(errors)

    return True, None


def validate_manager_data(name: str, country_id: int) -> tuple[bool, str | None]:
    """Validate manager data format.

    Args:
        name: Manager name
        country_id: Country ID

    Returns:
        Tuple of (is_valid, error_message)
    """
    errors: list[str] = []

    if not name or len(name.strip()) == 0:
        errors.append("Manager name is required")

    if not country_id or country_id <= 0:
        errors.append("Valid country ID is required")

    if errors:
        return False, "; ".join(errors)

    return True, None


def validate_country_data(code: str, flag_path: str) -> tuple[bool, str | None]:
    """Validate country data format.

    Args:
        code: Country code (3 letters)
        flag_path: Path to flag image

    Returns:
        Tuple of (is_valid, error_message)
    """
    errors: list[str] = []

    if not code or len(code.strip()) == 0:
        errors.append("Country code is required")
    elif len(code) != 3:
        errors.append(f"Country code must be 3 characters, got '{code}'")

    if not flag_path or len(flag_path.strip()) == 0:
        errors.append("Flag path is required")

    if errors:
        return False, "; ".join(errors)

    return True, None


class DataValidator:
    """Comprehensive data validator for seed operations."""

    def __init__(self, session: SessionLike):
        self.session = session
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_countries(self, countries_data: list[dict[str, Any]]) -> bool:
        """Validate countries before insertion.

        Args:
            countries_data: List of country data dictionaries

        Returns:
            True if all validations pass
        """
        codes_seen: set[str] = set()

        for country in countries_data:
            code = country.get("code", "")

            # Check for duplicates in input data
            if code in codes_seen:
                self.errors.append(f"Duplicate country code in input: '{code}'")
            codes_seen.add(code)

            # Check database for existing
            is_valid, error = validate_country_unique(self.session, code)
            if not is_valid:
                assert error is not None  # validator contract: error set when is_valid=False
                self.errors.append(error)

        return len(self.errors) == 0

    def validate_managers(self, managers_data: list[dict[str, Any]]) -> bool:
        """Validate managers before insertion.

        Args:
            managers_data: List of manager data dictionaries

        Returns:
            True if all validations pass
        """
        names_seen: set[str] = set()

        for manager in managers_data:
            name = manager.get("name", "")
            country_id = manager.get("country_id")

            # Check for duplicates in input data
            if name in names_seen:
                self.errors.append(f"Duplicate manager name in input: '{name}'")
            names_seen.add(name)

            # Validate format
            is_valid, error = validate_manager_data(name, country_id)  # type: ignore[arg-type]
            if not is_valid:
                self.errors.append(f"Manager '{name}': {error}")

            # Check database for existing
            is_valid, error = validate_manager_unique(self.session, name)
            if not is_valid:
                assert error is not None  # validator contract: error set when is_valid=False
                self.errors.append(error)

            # Check country exists
            is_valid, error = validate_country_exists(
                self.session, country_id  # type: ignore[arg-type]
            )
            if not is_valid:
                self.errors.append(f"Manager '{name}': {error}")

        return len(self.errors) == 0

    def validate_achievements(
        self, achievements_data: list[dict[str, Any]], valid_manager_ids: set[int]
    ) -> bool:
        """Validate achievements before insertion.

        Args:
            achievements_data: List of achievement data dictionaries
            valid_manager_ids: Set of valid manager IDs

        Returns:
            True if all validations pass
        """
        for achievement in achievements_data:
            manager_id = achievement.get("manager_id")
            achievement_type = achievement.get("achievement_type", "")
            league = achievement.get("league", "")
            season = achievement.get("season", "")
            title = achievement.get("title", "")

            # Validate format
            is_valid, error = validate_achievement_data(achievement_type, league, season, title)
            if not is_valid:
                self.errors.append(f"Achievement for manager {manager_id}: {error}")

            # Check manager exists
            if manager_id not in valid_manager_ids:
                self.errors.append(f"Achievement references non-existent manager ID: {manager_id}")

        return len(self.errors) == 0

    def get_report(self) -> str:
        """Generate validation report."""
        lines = ["=== Validation Report ===", ""]

        if self.errors:
            lines.append(f"❌ Errors: {len(self.errors)}")
            for error in self.errors:
                lines.append(f"  - {error}")
        else:
            lines.append("✅ No errors found")

        if self.warnings:
            lines.append(f"\n⚠️ Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        return "\n".join(lines)
