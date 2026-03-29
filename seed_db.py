"""Script to seed the database with initial data from managers_data.py.

This script parses the hardcoded manager data and populates the database
with countries, managers, and achievements. Includes validation to prevent
duplicates and ensure data integrity.

Usage:
    python seed_db.py
"""

import re
from typing import Any, Dict, List, Optional, TypedDict

from app import create_app
from models import db, Country, Manager, Achievement
from data.managers_data import managers as initial_managers
from services.validation_service import DataValidator, validate_country_data


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
    # Example: <img src="/static/img/cups/top1.svg" title="Shadow 1 league TOP1 s22/23">
    match = re.search(
        r'src="/static/img/cups/([\w-]+)\.(svg|png)".*?title="Shadow (\d) league (.+?) s(\d{2}/\d{2})"',
        achievement_html
    )
    if not match:
        return None

    cup_type, ext, league, title, season = match.groups()

    # Normalize achievement type
    achievement_type = cup_type.upper().replace('-', '_')

    return ParsedAchievement(
        achievement_type=achievement_type,
        league=league,
        season=season,
        title=title,
        icon_path=f'/static/img/cups/{cup_type}.{ext}',
    )


def seed_database() -> None:
    """Seed the database with initial manager data."""
    app = create_app()
    with app.app_context():
        # Clear existing data (order matters due to FK constraints)
        # Use delete() with error handling for empty/new database
        try:
            db.session.query(Achievement).delete()
            db.session.query(Manager).delete()
            db.session.query(Country).delete()
            db.session.commit()
        except Exception:
            # If tables don't exist yet, just continue (fresh database)
            db.session.rollback()

        # First pass: collect and validate all data
        countries_to_create: dict[str, Country] = {}
        managers_to_create: list[dict] = []
        achievements_to_create: list[dict] = []

        for manager_data in initial_managers:
            # Extract country info
            country_path = manager_data.country
            filename = country_path.split('/')[-1].split('.')[0].upper()
            
            # Map filename to 3-letter country code
            FLAG_TO_CODE = {
                'RUS': 'RUS',
                'BEL': 'BEL',
                'KZ': 'KAZ',
                'KAZ': 'KAZ',
                'VIETNAM': 'VNM',
                'UA': 'UKR',
                'UKR': 'UKR',
                'MEXICO': 'MEX',
                'MEX': 'MEX',
                'POL': 'POL',
                'CHINA': 'CHN',
                'CHN': 'CHN',
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
                    flag_path=country_path
                )

            # Track manager (avoid duplicates within input)
            existing_manager = next(
                (m for m in managers_to_create if m['name'] == manager_data.name),
                None
            )
            if existing_manager:
                print(f"  [WARN] Skipping duplicate manager in input: {manager_data.name}")
                continue

            manager_entry = {
                'name': manager_data.name,
                'country_code': country_code,
                'achievements': manager_data.achievements
            }
            managers_to_create.append(manager_entry)

            # Track achievements
            for achievement_html in manager_data.achievements:
                parsed = parse_achievement_html(achievement_html)
                if parsed is None:
                    print(f"  [WARN] Could not parse achievement: {achievement_html}")
                    continue
                achievements_to_create.append({
                    'manager_name': manager_data.name,
                    **parsed
                })

        # Validate managers for duplicates in database
        validator = DataValidator(db.session)

        # Create countries
        print("\n[INFO] Creating countries...")
        for country_code, country in countries_to_create.items():
            db.session.add(country)
            print(f"  [OK] Created country: {country_code}")
        db.session.flush()

        # Create managers
        print("\n[INFO] Creating managers...")
        manager_id_map: dict[str, int] = {}  # name -> id
        managers_created = 0

        for manager_entry in managers_to_create:
            name = manager_entry['name']
            country = countries_to_create[manager_entry['country_code']]

            # Check for existing in DB
            existing = db.session.query(Manager).filter_by(name=name).first()
            if existing:
                print(f"  [SKIP] Skipping existing manager: {name}")
                manager_id_map[name] = existing.id
                continue

            manager = Manager(
                name=name,
                country_id=country.id
            )
            db.session.add(manager)
            db.session.flush()
            manager_id_map[name] = manager.id
            managers_created += 1
            print(f"  [OK] Created manager: {name}")

        # Create achievements
        print("\n[INFO] Creating achievements...")
        achievements_created = 0

        for achievement_data in achievements_to_create:
            manager_name = achievement_data['manager_name']
            manager_id = manager_id_map.get(manager_name)

            if not manager_id:
                print(f"  [SKIP] Skipping achievement for unknown manager: {manager_name}")
                continue

            achievement = Achievement(
                achievement_type=achievement_data['achievement_type'],
                league=achievement_data['league'],
                season=achievement_data['season'],
                title=achievement_data['title'],
                icon_path=achievement_data['icon_path'],
                manager_id=manager_id
            )
            db.session.add(achievement)
            achievements_created += 1

        db.session.commit()

        print("\n[SUCCESS] Database seeded successfully!")
        print(f"  Countries: {len(countries_to_create)}")
        print(f"  Managers created: {managers_created}")
        print(f"  Achievements created: {achievements_created}")


if __name__ == "__main__":
    seed_database()
