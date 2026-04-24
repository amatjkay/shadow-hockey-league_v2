"""Seed service for populating database with initial and reference data."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from flask import current_app
from sqlalchemy import text
from models import db, Country, Manager, Achievement, AchievementType, League, Season, AdminUser

logger = logging.getLogger('shleague.seed')


class SeedService:
    """Service to handle database seeding and resets."""

    @staticmethod
    def seed_all(force: bool = False) -> Dict[str, Any]:
        """Seed all database tables.

        Args:
            force: If True, truncate tables before seeding.

        Returns:
            Dictionary with seeding results.
        """
        results = {}
        try:
            if force:
                SeedService.clear_database()
                results['cleared'] = True

            results['reference_data'] = SeedService._seed_reference_data()
            results['countries'] = SeedService._seed_countries()
            results['managers'] = SeedService._seed_managers()
            results['achievements'] = SeedService._seed_achievements()
            results['admin'] = SeedService._seed_default_admin()

            db.session.commit()
            logger.info("Database seeding completed successfully")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database seeding failed: {e}")
            raise

        return results

    @staticmethod
    def clear_database() -> None:
        """Truncate all tables in correct order."""
        # Order matters for foreign keys
        tables = [
            'audit_logs', 'achievements', 'managers', 'countries',
            'seasons', 'leagues', 'achievement_types', 'api_keys', 'admin_users'
        ]
        
        # In SQLite, we can just delete all rows
        for table in tables:
            db.session.execute(text(f"DELETE FROM {table}"))
        
        # Reset auto-increment counters
        db.session.execute(text("DELETE FROM sqlite_sequence"))
        db.session.commit()
        logger.info("Database tables cleared")

    @staticmethod
    def _seed_reference_data() -> Dict[str, int]:
        """Seed reference tables (AchievementType, League, Season)."""
        counts = {'types': 0, 'leagues': 0, 'seasons': 0}

        # 1. Achievement Types
        # Aligning with Season 25/26 baseline: TOP1 = 800
        types_data = [
            {'code': 'TOP1', 'name': 'Top 1', 'base_points_l1': 800, 'base_points_l2': 400},
            {'code': 'TOP2', 'name': 'Top 2', 'base_points_l1': 400, 'base_points_l2': 200},
            {'code': 'BEST', 'name': 'Best Regular', 'base_points_l1': 200, 'base_points_l2': 100},
            {'code': 'R3', 'name': 'Round 3', 'base_points_l1': 100, 'base_points_l2': 50},
            {'code': 'R1', 'name': 'Round 1', 'base_points_l1': 50, 'base_points_l2': 25},
        ]
        for data in types_data:
            if not db.session.query(AchievementType).filter_by(code=data['code']).first():
                db.session.add(AchievementType(**data))
                counts['types'] += 1

        # 2. Leagues
        leagues_data = [
            {'code': '1', 'name': 'League 1'},
            {'code': '2', 'name': 'League 2'},
            {'code': '2.1', 'name': 'League 2.1', 'parent_code': '2'},
            {'code': '2.2', 'name': 'League 2.2', 'parent_code': '2'},
        ]
        for data in leagues_data:
            if not db.session.query(League).filter_by(code=data['code']).first():
                db.session.add(League(**data))
                counts['leagues'] += 1

        # 3. Seasons
        # Multiplier 1.0 for s25/26, historical seasons get lower multipliers
        seasons_data = [
            {'code': '23/24', 'name': 'Season 23/24', 'multiplier': 0.5, 'start_year': 2023, 'end_year': 2024},
            {'code': '24/25', 'name': 'Season 24/25', 'multiplier': 0.75, 'start_year': 2024, 'end_year': 2025},
            {'code': '25/26', 'name': 'Season 25/26', 'multiplier': 1.0, 'start_year': 2025, 'end_year': 2026, 'is_active': True},
        ]
        for data in seasons_data:
            if not db.session.query(Season).filter_by(code=data['code']).first():
                db.session.add(Season(**data))
                counts['seasons'] += 1

        db.session.flush()
        return counts

    @staticmethod
    def _seed_countries() -> int:
        """Seed countries from JSON file."""
        count = 0
        path = os.path.join(current_app.root_path, 'data', 'seed', 'countries.json')
        if not os.path.exists(path):
            logger.warning(f"Countries seed file not found: {path}")
            return 0

        with open(path, 'r', encoding='utf-8') as f:
            countries = json.load(f)

        for c_data in countries:
            if not db.session.query(Country).filter_by(code=c_data['code']).first():
                # Case-insensitive flag filenames (standardizing to uppercase)
                flag_path = f"/static/img/flags/{c_data['code'].upper()}.png"
                country = Country(
                    code=c_data['code'],
                    name=c_data['name'],
                    flag_path=flag_path
                )
                db.session.add(country)
                count += 1

        db.session.flush()
        return count

    @staticmethod
    def _seed_managers() -> int:
        """Seed initial managers."""
        # Implementation depends on business logic for initial managers
        # This is a placeholder for basic set
        count = 0
        initial_managers = [
            {'name': 's3ifer', 'country_code': 'RUS'},
            {'name': 'tiki', 'country_code': 'POL'},
            {'name': 'Tandem: Admin, Moderator', 'country_code': 'CAN'}
        ]
        
        for m_data in initial_managers:
            if not db.session.query(Manager).filter_by(name=m_data['name']).first():
                country = db.session.query(Country).filter_by(code=m_data['country_code']).first()
                if country:
                    manager = Manager(name=m_data['name'], country_id=country.id)
                    db.session.add(manager)
                    count += 1
        
        db.session.flush()
        return count

    @staticmethod
    def _seed_achievements() -> int:
        """Seed initial achievements (demo data)."""
        # Usually we wouldn't seed many achievements, but for demo:
        count = 0
        # Only seed if managers exist
        manager = db.session.query(Manager).first()
        if not manager:
            return 0
            
        # Example achievement
        ach_type = db.session.query(AchievementType).filter_by(code='TOP1').first()
        league = db.session.query(League).filter_by(code='1').first()
        season = db.session.query(Season).filter_by(is_active=True).first()
        
        if ach_type and league and season:
            if not db.session.query(Achievement).filter_by(
                manager_id=manager.id, type_id=ach_type.id, 
                league_id=league.id, season_id=season.id
            ).first():
                # Note: fields will be auto-calculated if we use AchievementModelView logic,
                # but here we set them manually for simplicity in seed
                base = ach_type.base_points_l1
                mult = season.multiplier
                
                ach = Achievement(
                    manager_id=manager.id,
                    type_id=ach_type.id,
                    league_id=league.id,
                    season_id=season.id,
                    title=f"{ach_type.name} {league.name} {season.name}",
                    icon_path=ach_type.get_icon_url(),
                    base_points=base,
                    multiplier=mult,
                    final_points=base * mult
                )
                db.session.add(ach)
                count += 1
        
        db.session.flush()
        return count

    @staticmethod
    def _seed_default_admin() -> bool:
        """Seed default admin user if none exists."""
        if not db.session.query(AdminUser).filter_by(username='admin').first():
            admin = AdminUser(username='admin', role='super_admin')
            admin.set_password('admin123')
            db.session.add(admin)
            
            # User's specific admin
            s3ifer = AdminUser(username='s3ifer', role='super_admin')
            s3ifer.set_password('s3ifer_pass')
            db.session.add(s3ifer)
            
            return True
        return False
