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
from models import Achievement, AchievementType, AuditLog, Country, League, Manager, Season

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
                    self.session.query(AchievementType).delete()
                    self.session.query(League).delete()
                    self.session.query(Season).delete()
                    self.session.query(AuditLog).delete()
                    self.session.commit()
                    # Drop identity-map entries left behind by `query.delete()`
                    # so the next add() doesn't collide on stale primary keys
                    # (otherwise SAWarning: "Identity map already had …").
                    self.session.expunge_all()
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

        # Seed reference data (types, leagues, seasons)
        self._seed_reference_data()
        self.session.flush()

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

    def _seed_reference_data(self) -> None:
        """Seed reference tables (AchievementType, League, Season) if they are empty."""
        # 1. Achievement Types
        # Aligning with Season 25/26 baseline: TOP1 = 800
        if self.session.query(AchievementType).count() == 0:
            logger.info("Seeding default AchievementTypes...")
            types_data = [
                {"code": "TOP1", "name": "Top 1", "base_points_l1": 800, "base_points_l2": 400},
                {"code": "TOP2", "name": "Top 2", "base_points_l1": 400, "base_points_l2": 200},
                {"code": "TOP3", "name": "Top 3", "base_points_l1": 200, "base_points_l2": 100},
                {
                    "code": "BEST",
                    "name": "Best Regular",
                    "base_points_l1": 200,
                    "base_points_l2": 100,
                },
                {"code": "R3", "name": "Round 3", "base_points_l1": 100, "base_points_l2": 50},
                {"code": "R1", "name": "Round 1", "base_points_l1": 50, "base_points_l2": 25},
            ]
            for data in types_data:
                self.session.add(AchievementType(**data))

        # 2. Leagues
        if self.session.query(League).count() == 0:
            logger.info("Seeding default Leagues...")
            leagues = [
                ("1", "Elite League", None),
                ("2", "Second League", None),
            ]
            for code, name, parent in leagues:
                self.session.add(League(code=code, name=name, parent_code=parent))

        # 3. Seasons
        if self.session.query(Season).count() == 0:
            logger.info("Seeding default Seasons...")
            # Updated multipliers: current is 1.0, older are significantly less
            seasons = [
                ("21/22", "Season 2021/22", 0.20),
                ("22/23", "Season 2022/23", 0.30),
                ("23/24", "Season 2023/24", 0.50),
                ("24/25", "Season 2024/25", 0.80),
                ("25/26", "Season 2025/26", 1.00),
            ]
            for code, name, mult in seasons:
                self.session.add(
                    Season(code=code, name=name, multiplier=mult, is_active=(code == "25/26"))
                )

    def _seed_achievements(self, data: list[dict], result: SeedResult) -> None:
        """Seed achievements from JSON data."""
        # Cache for performance
        types = {t.code: t for t in self.session.query(AchievementType).all()}
        leagues = {l.code: l for l in self.session.query(League).all()}
        seasons = {s.code: s for s in self.session.query(Season).all()}

        for item in data:
            manager_name = item["manager_name"]
            manager = self.session.query(Manager).filter_by(name=manager_name).first()
            if not manager:
                result.errors.append(f"Manager not found: {manager_name}")
                continue

            # Map legacy types
            ach_type_code = item["type"]
            if ach_type_code == "BEST_REG":
                ach_type_code = "BEST"
            elif ach_type_code == "HOCKEY_STICKS_AND_PUCK":
                ach_type_code = "R3" if "Round 3" in item["title"] else "R1"

            # Resolve objects
            ach_type = types.get(ach_type_code)
            league = leagues.get(item["league"])
            season = seasons.get(item["season"])

            if not all([ach_type, league, season]):
                missing = []
                if not ach_type:
                    missing.append(f"type:{ach_type_code}")
                if not league:
                    missing.append(f"league:{item['league']}")
                if not season:
                    missing.append(f"season:{item['season']}")
                result.errors.append(
                    f"Missing reference data for {manager_name}: {', '.join(missing)}"
                )
                continue

            # Check unique constraint
            existing = (
                self.session.query(Achievement)
                .filter_by(
                    manager_id=manager.id,
                    league_id=league.id,
                    season_id=season.id,
                    type_id=ach_type.id,
                )
                .first()
            )
            if existing:
                result.achievements_skipped += 1
                continue

            achievement = Achievement(
                type=ach_type,
                league=league,
                season=season,
                title=item["title"],
                icon_path=self.paths.resolve_cup(item["icon_filename"]),
                manager_id=manager.id,
            )
            self.session.add(achievement)
            result.achievements_created += 1
