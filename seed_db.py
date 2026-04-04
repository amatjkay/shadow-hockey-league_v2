"""Script to seed the database with initial data from managers_data.py.

This script parses the hardcoded manager data and populates the database
with countries, managers, and achievements. Includes validation to prevent
duplicates and ensure data integrity.

IMPORTANT: This script is IDEMPOTENT by default.
- It will NOT delete existing data.
- It will SKIP countries/managers/achievements that already exist.
- Use --force flag to clear all data and reseed from scratch.

Usage:
    python seed_db.py           # Safe mode (skip existing)
    python seed_db.py --force   # Force mode (clear and reseed)
"""

import argparse
import re
import sys
from typing import List, Optional, TypedDict

from app import create_app
from data.managers_data import managers as initial_managers
from models import Achievement, Country, Manager, db
from services.validation_service import validate_country_data


class ParsedAchievement(TypedDict):
    """Typed dictionary for parsed achievement data."""

    achievement_type: str
    league: str
    season: str
    title: str
    icon_path: str


class ManagerEntry(TypedDict):
    """Typed dictionary for manager entry data."""

    name: str
    country_code: str
    achievements: List[str]


def parse_achievement_html(achievement_html: str) -> Optional[ParsedAchievement]:
    """Parse achievement HTML string into structured data.

    Args:
        achievement_html: HTML img tag with title attribute

    Returns:
        Dictionary with achievement data or None if parsing fails
    """
    # Parse standard achievement HTML
    # Example: <img src="/static/img/cups/top1.svg"
    # title="Shadow 1 league TOP1 s22/23">
    pattern = (
        r'src="/static/img/cups/([\w-]+)\.(svg|png)"'
        r'.*?title="Shadow (\d) league (.+?) s(\d{2}/\d{2})"'
    )
    match = re.search(pattern, achievement_html)
    if not match:
        return None

    cup_type, ext, league, title, season = match.groups()

    # Normalize achievement type
    achievement_type = cup_type.upper().replace("-", "_")

    return ParsedAchievement(
        achievement_type=achievement_type,
        league=league,
        season=season,
        title=title,
        icon_path=f"/static/img/cups/{cup_type}.{ext}",
    )


def check_existing_data() -> dict[str, int]:
    """Check if database already has data.

    Returns:
        Dictionary with counts of existing records.
    """
    country_count = db.session.query(Country).count()
    manager_count = db.session.query(Manager).count()
    achievement_count = db.session.query(Achievement).count()

    return {
        "countries": country_count,
        "managers": manager_count,
        "achievements": achievement_count,
    }


def clear_database() -> None:
    """Clear all data from the database.

    WARNING: This is destructive and should only be used with --force flag.
    """
    print("[WARN] Clearing all existing data...")
    try:
        db.session.query(Achievement).delete()
        db.session.query(Manager).delete()
        db.session.query(Country).delete()
        db.session.commit()
        print("[OK] All data cleared successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Failed to clear data: {e}")
        raise


def seed_database(force: bool = False) -> bool:
    """Seed the database with initial manager data.

    This function is IDEMPOTENT by default:
    - Countries: skipped if code already exists
    - Managers: skipped if name already exists
    - Achievements: skipped if (manager, league, season, type) already exists

    Args:
        force: If True, clear all data before seeding.

    Returns:
        True if seeding was successful, False otherwise.
    """
    app = create_app()
    with app.app_context():
        # Check existing data
        existing = check_existing_data()
        print(f"\n[INFO] Current database state:")
        print(f"  Countries: {existing['countries']}")
        print(f"  Managers: {existing['managers']}")
        print(f"  Achievements: {existing['achievements']}")

        # Handle force mode
        if force:
            if existing['countries'] == 0 and existing['managers'] == 0:
                print("[INFO] Database is empty, no need to clear.")
            else:
                clear_database()
        else:
            # Safe mode: check if data already exists
            if existing['managers'] > 0:
                print("\n[INFO] Database already has manager data.")
                print("[INFO] Skipping seed (use --force to reseed from scratch).")
                return True

        # Parse and validate all data
        countries_to_create: dict[str, Country] = {}
        managers_to_create: list[dict] = []
        achievements_to_create: list[dict] = []

        for manager_data in initial_managers:
            # Extract country info
            country_path = manager_data.country
            filename = country_path.split("/")[-1].split(".")[0].upper()

            # Map filename to 3-letter country code
            FLAG_TO_CODE = {
                "RUS": "RUS",
                "BEL": "BEL",
                "KZ": "KAZ",
                "KAZ": "KAZ",
                "VIETNAM": "VNM",
                "UA": "UKR",
                "UKR": "UKR",
                "MEXICO": "MEX",
                "MEX": "MEX",
                "POL": "POL",
                "CHINA": "CHN",
                "CHN": "CHN",
            }
            country_code = FLAG_TO_CODE.get(filename, filename[:3])

            # Validate country data
            is_valid, error = validate_country_data(country_code, country_path)
            if not is_valid:
                print(f"  [ERROR] Validation error for country: {error}")
                continue

            # Track country (avoid duplicates)
            if country_code not in countries_to_create:
                countries_to_create[country_code] = Country(
                    code=country_code,
                    name=Country.resolve_name(country_code),
                    flag_path=country_path,
                )

            # Track manager (avoid duplicates within input)
            existing_manager = next(
                (m for m in managers_to_create if m["name"] == manager_data.name), None
            )
            if existing_manager:
                print(f"  [WARN] Skipping duplicate manager in input: {manager_data.name}")
                continue

            manager_entry = {
                "name": manager_data.name,
                "country_code": country_code,
                "achievements": manager_data.achievements,
            }
            managers_to_create.append(manager_entry)

            # Track achievements
            for achievement_html in manager_data.achievements:
                parsed = parse_achievement_html(achievement_html)
                if parsed is None:
                    print(f"  [WARN] Could not parse achievement: {achievement_html}")
                    continue
                achievements_to_create.append({"manager_name": manager_data.name, **parsed})

        # Create countries (skip existing)
        print("\n[INFO] Processing countries...")
        countries_created = 0
        countries_skipped = 0

        for country_code, country in countries_to_create.items():
            # Check if country already exists
            existing_country = db.session.query(Country).filter_by(code=country_code).first()
            if existing_country:
                print(f"  [SKIP] Country already exists: {country_code}")
                countries_skipped += 1
                continue

            db.session.add(country)
            countries_created += 1
            print(f"  [OK] Created country: {country_code}")

        db.session.flush()

        # Create managers (skip existing)
        print("\n[INFO] Processing managers...")
        manager_id_map: dict[str, int] = {}  # name -> id
        managers_created = 0
        managers_skipped = 0

        for manager_entry in managers_to_create:
            name = manager_entry["name"]
            country = countries_to_create[manager_entry["country_code"]]

            # Check for existing in DB
            existing = db.session.query(Manager).filter_by(name=name).first()
            if existing:
                print(f"  [SKIP] Manager already exists: {name}")
                manager_id_map[name] = existing.id
                managers_skipped += 1
                continue

            manager = Manager(name=name, country_id=country.id)
            db.session.add(manager)
            db.session.flush()
            manager_id_map[name] = manager.id
            managers_created += 1
            print(f"  [OK] Created manager: {name}")

        # Create achievements (skip existing)
        print("\n[INFO] Processing achievements...")
        achievements_created = 0
        achievements_skipped = 0

        for achievement_data in achievements_to_create:
            manager_name = achievement_data["manager_name"]
            manager_id = manager_id_map.get(manager_name)

            if not manager_id:
                print(f"  [SKIP] Skipping achievement for unknown manager: {manager_name}")
                continue

            # Check if achievement already exists (unique constraint)
            existing_achievement = db.session.query(Achievement).filter_by(
                manager_id=manager_id,
                league=achievement_data["league"],
                season=achievement_data["season"],
                achievement_type=achievement_data["achievement_type"],
            ).first()

            if existing_achievement:
                achievements_skipped += 1
                continue

            achievement = Achievement(
                achievement_type=achievement_data["achievement_type"],
                league=achievement_data["league"],
                season=achievement_data["season"],
                title=achievement_data["title"],
                icon_path=achievement_data["icon_path"],
                manager_id=manager_id,
            )
            db.session.add(achievement)
            achievements_created += 1

        db.session.commit()

        print("\n" + "=" * 50)
        print("[SUCCESS] Database seeding completed!")
        print(f"  Countries: {countries_created} created, {countries_skipped} skipped")
        print(f"  Managers: {managers_created} created, {managers_skipped} skipped")
        print(f"  Achievements: {achievements_created} created, {achievements_skipped} skipped")
        print("=" * 50)

        return True


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Seed the database with initial manager data."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Clear all existing data before seeding (DESTRUCTIVE)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check database state, do not seed"
    )

    args = parser.parse_args()

    # Check mode only
    if args.check:
        app = create_app()
        with app.app_context():
            existing = check_existing_data()
            print(f"\n[INFO] Database state:")
            print(f"  Countries: {existing['countries']}")
            print(f"  Managers: {existing['managers']}")
            print(f"  Achievements: {existing['achievements']}")

            if existing['managers'] > 0:
                print("[INFO] Database has data. Skip seeding (use --force to reseed).")
            else:
                print("[INFO] Database is empty. Run without --check to seed.")
        return

    # Seed with optional force
    try:
        success = seed_database(force=args.force)
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
