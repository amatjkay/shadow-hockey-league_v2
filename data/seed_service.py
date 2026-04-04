"""Seed service for populating database from JSON files.

Reads seed data from data/seed/*.json files, validates it,
and inserts into the database (skipping existing records).

Usage:
    from data.seed_service import SeedService

    service = SeedService(db.session)
    result = service.seed_all()
    print(result)  # {'countries': {'created': 8, 'skipped': 0}, ...}
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from data.schemas import validate_all
from data.static_paths import StaticPaths
from models import Achievement, Country, Manager

logger = logging.getLogger(__name__)


class SeedResult:
    """Result report from seeding operation."""

    def __init__(self) -> None:
        self.countries_created = 0
        self.countries_skipped = 0
        self.managers_created = 0
        self.managers_skipped = 0
        self.achievements_created = 0
        self.achievements_skipped = 0
        self.errors: list[str] = []

    def to_dict(self) -> dict[str, dict[str, int]]:
        return {
            "countries": {"created": self.countries_created, "skipped": self.countries_skipped},
            "managers": {"created": self.managers_created, "skipped": self.managers_skipped},
            "achievements": {
                "created": self.achievements_created,
                "skipped": self.achievements_skipped,
            },
            "errors": len(self.errors),
        }

    def __str__(self) -> str:
        lines = [
            "=" * 50,
            "[SUCCESS] Database seeding completed!",
            f"  Countries: {self.countries_created} created, {self.countries_skipped} skipped",
            f"  Managers: {self.managers_created} created, {self.managers_skipped} skipped",
            f"  Achievements: {self.achievements_created} created, "
            f"{self.achievements_skipped} skipped",
        ]
        if self.errors:
            lines.append(f"  Errors: {len(self.errors)}")
            for err in self.errors[:5]:
                lines.append(f"    - {err}")
        lines.append("=" * 50)
        return "\n".join(lines)


class SeedService:
    """Service for seeding database from JSON files.

    Args:
        session: SQLAlchemy database session.
        seed_dir: Path to directory containing seed JSON files.
    """

    def __init__(self, session: Any, seed_dir: str | Path | None = None) -> None:
        self.session = session
        self.paths = StaticPaths()
        self.seed_dir = Path(seed_dir) if seed_dir else Path(__file__).parent / "seed"

    def _load_json(self, filename: str) -> Any:
        """Load and parse a JSON file."""
        filepath = self.seed_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Seed file not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def check_db_state(self) -> dict[str, int]:
        """Check current database state.

        Returns:
            Dictionary with counts of existing records.
        """
        return {
            "countries": self.session.query(Country).count(),
            "managers": self.session.query(Manager).count(),
            "achievements": self.session.query(Achievement).count(),
        }

    def seed_all(self, force: bool = False) -> SeedResult:
        """Seed all data from JSON files.

        Args:
            force: If True, clears all data before seeding.

        Returns:
            SeedResult with counts of created/skipped records.
        """
        result = SeedResult()

        # Check DB state
        existing = self.check_db_state()
        logger.info(f"Current DB state: {existing}")

        # Handle force mode
        if force:
            if existing["countries"] > 0 or existing["managers"] > 0:
                logger.warning("Force mode: clearing all data")
                try:
                    self.session.query(Achievement).delete()
                    self.session.query(Manager).delete()
                    self.session.query(Country).delete()
                    self.session.commit()
                except Exception as e:
                    self.session.rollback()
                    result.errors.append(f"Failed to clear data: {e}")
                    return result
        else:
            # Safe mode: skip if data exists
            if existing["managers"] > 0:
                logger.info("Database already has data. Skipping seed (use --force to reseed).")
                return result

        # Load seed data
        try:
            countries_data = self._load_json("countries.json")
            managers_data = self._load_json("managers.json")
            achievements_data = self._load_json("achievements.json")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            result.errors.append(f"Failed to load seed data: {e}")
            return result

        # Validate
        validation_errors = validate_all(countries_data, managers_data, achievements_data)
        for section, errors in validation_errors.items():
            for error in errors:
                result.errors.append(f"Validation error in {section}: {error}")

        if result.errors:
            return result

        # Seed countries
        self._seed_countries(countries_data, result)
        self.session.flush()

        # Seed managers
        self._seed_managers(managers_data, result)
        self.session.flush()

        # Seed achievements
        self._seed_achievements(achievements_data, result)

        self.session.commit()
        return result

    def _seed_countries(self, data: list[dict], result: SeedResult) -> None:
        """Seed countries from JSON data."""
        for item in data:
            code = item["code"]
            existing = self.session.query(Country).filter_by(code=code).first()
            if existing:
                logger.debug(f"Skipping existing country: {code}")
                result.countries_skipped += 1
                continue

            country = Country(
                code=code,
                name=item["name"],
                flag_path=self.paths.resolve_flag(item["flag_filename"]),
            )
            self.session.add(country)
            result.countries_created += 1
            logger.info(f"Created country: {code}")

    def _seed_managers(self, data: list[dict], result: SeedResult) -> None:
        """Seed managers from JSON data."""
        for item in data:
            name = item["name"]
            country_code = item["country_code"]

            existing = self.session.query(Manager).filter_by(name=name).first()
            if existing:
                logger.debug(f"Skipping existing manager: {name}")
                result.managers_skipped += 1
                continue

            country = self.session.query(Country).filter_by(code=country_code).first()
            if not country:
                result.errors.append(f"Country not found: {country_code} (for manager {name})")
                continue

            manager = Manager(name=name, country_id=country.id)
            self.session.add(manager)
            result.managers_created += 1
            logger.info(f"Created manager: {name}")

    def _seed_achievements(self, data: list[dict], result: SeedResult) -> None:
        """Seed achievements from JSON data."""
        for item in data:
            manager_name = item["manager_name"]
            manager = self.session.query(Manager).filter_by(name=manager_name).first()
            if not manager:
                result.errors.append(f"Manager not found: {manager_name}")
                continue

            # Check unique constraint
            existing = self.session.query(Achievement).filter_by(
                manager_id=manager.id,
                league=item["league"],
                season=item["season"],
                achievement_type=item["type"],
            ).first()
            if existing:
                result.achievements_skipped += 1
                continue

            achievement = Achievement(
                achievement_type=item["type"],
                league=item["league"],
                season=item["season"],
                title=item["title"],
                icon_path=self.paths.resolve_cup(item["icon_filename"]),
                manager_id=manager.id,
            )
            self.session.add(achievement)
            result.achievements_created += 1
