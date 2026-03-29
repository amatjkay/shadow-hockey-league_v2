"""Script to seed the database with initial data from managers_data.py.

This script parses the hardcoded manager data and populates the database
with countries, managers, and achievements.

Usage:
    python seed_db.py
"""

import re
from app import create_app
from models import db, Country, Manager, Achievement
from data.managers_data import managers as initial_managers


def parse_achievement_html(achievement_html: str) -> dict | None:
    """Parse achievement HTML string into structured data.

    Args:
        achievement_html: HTML img tag with title attribute

    Returns:
        Dictionary with achievement data or None if parsing fails
    """
    # Handle toxic achievement
    if 'toxic' in achievement_html.lower():
        return {
            'achievement_type': 'TOXIC',
            'league': '1',
            'season': 'N/A',
            'title': 'Toxic and unpleasant person',
            'icon_path': '/static/img/cups/toxic.png',
        }

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

    return {
        'achievement_type': achievement_type,
        'league': league,
        'season': season,
        'title': title,
        'icon_path': f'/static/img/cups/{cup_type}.{ext}',
    }


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

        # Cache for countries to avoid duplicates
        country_cache: dict[str, Country] = {}

        managers_created = 0
        achievements_created = 0

        for manager_data in initial_managers:
            # Get or create country
            country_path = manager_data.country
            if country_path not in country_cache:
                # Extract country code from flag path (e.g., "/static/img/flags/bel.png" -> "BEL")
                country_code = country_path.split('/')[-1].split('.')[0].upper()
                country = Country(
                    code=country_code,
                    flag_path=country_path
                )
                db.session.add(country)
                db.session.flush()
                country_cache[country_path] = country
                print(f"  Created country: {country_code}")

            # Create manager
            manager = Manager(
                name=manager_data.name,
                country_id=country_cache[country_path].id
            )
            db.session.add(manager)
            db.session.flush()
            managers_created += 1

            # Add achievements
            for achievement_html in manager_data.achievements:
                parsed = parse_achievement_html(achievement_html)
                if parsed is None:
                    print(f"  WARNING: Could not parse achievement: {achievement_html}")
                    continue

                achievement = Achievement(
                    achievement_type=parsed['achievement_type'],
                    league=parsed['league'],
                    season=parsed['season'],
                    title=parsed['title'],
                    icon_path=parsed['icon_path'],
                    manager_id=manager.id
                )
                db.session.add(achievement)
                achievements_created += 1

        db.session.commit()
        print(f"\nDatabase seeded successfully!")
        print(f"  Countries: {len(country_cache)}")
        print(f"  Managers: {managers_created}")
        print(f"  Achievements: {achievements_created}")


if __name__ == "__main__":
    seed_database()
