#!/usr/bin/env python3
"""Database validation and initialization script.

This script validates the database setup and provides helpful error messages
if something is misconfigured.

Usage:
    python scripts/validate_db.py [--init] [--seed]
    
Options:
    --init   Create database tables if they don't exist
    --seed   Seed database with initial data after initialization
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app
from models import db, Country, Manager, Achievement


def check_database_exists(app) -> bool:
    """Check if database file exists."""
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '')
        # Handle relative paths
        if not db_path.startswith('/'):
            db_path = project_root / db_path
        else:
            db_path = Path(db_path)
        
        exists = db_path.exists()
        print(f"  Database file: {db_path}")
        print(f"  Exists: {'✓ Yes' if exists else '✗ No'}")
        return exists
    
    # For non-SQLite databases, assume they exist
    print(f"  Database URI: {db_uri}")
    print(f"  Type: Non-SQLite (assumed OK)")
    return True


def check_tables_exist(app) -> bool:
    """Check if required tables exist."""
    with app.app_context():
        try:
            # Try to query each table
            Country.query.first()
            Manager.query.first()
            Achievement.query.first()
            print("  Tables: ✓ All tables exist")
            return True
        except Exception as e:
            print(f"  Tables: ✗ Error - {str(e)}")
            return False


def check_data_exists(app) -> bool:
    """Check if database has data."""
    with app.app_context():
        countries = Country.query.count()
        managers = Manager.query.count()
        achievements = Achievement.query.count()
        
        print(f"  Countries: {countries}")
        print(f"  Managers: {managers}")
        print(f"  Achievements: {achievements}")
        
        has_data = countries > 0 and managers > 0
        print(f"  Has data: {'✓ Yes' if has_data else '✗ No'}")
        return has_data


def init_database(app) -> bool:
    """Initialize database tables."""
    print("\nInitializing database tables...")
    with app.app_context():
        try:
            db.create_all()
            print("  ✓ Tables created successfully")
            return True
        except Exception as e:
            print(f"  ✗ Error creating tables: {str(e)}")
            return False


def seed_database(app) -> bool:
    """Seed database with initial data."""
    print("\nSeeding database...")
    try:
        # Import and run seed script
        import subprocess
        result = subprocess.run(
            [sys.executable, str(project_root / 'seed_db.py')],
            capture_output=True,
            text=True,
            cwd=str(project_root)
        )
        
        if result.returncode == 0:
            print("  ✓ Database seeded successfully")
            return True
        else:
            print(f"  ✗ Error seeding database: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ✗ Error running seed script: {str(e)}")
        return False


def main():
    """Main validation function."""
    print("=" * 60)
    print("Shadow Hockey League - Database Validation")
    print("=" * 60)
    
    # Create app
    app = create_app()
    
    # Parse arguments
    should_init = '--init' in sys.argv
    should_seed = '--seed' in sys.argv
    
    # Run checks
    print("\n[1/3] Checking database file...")
    db_exists = check_database_exists(app)
    
    print("\n[2/3] Checking tables...")
    if db_exists:
        tables_exist = check_tables_exist(app)
    else:
        tables_exist = False
        print("  ⊘ Skipped (database doesn't exist)")
    
    print("\n[3/3] Checking data...")
    if tables_exist:
        has_data = check_data_exists(app)
    else:
        has_data = False
        print("  ⊘ Skipped (tables don't exist)")
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_ok = db_exists and tables_exist and has_data
    
    if all_ok:
        print("\n✓ All checks passed! Database is ready.")
        print("\nTo start the server:")
        print("  python app.py")
        return 0
    
    # Offer to fix
    print("\n✗ Some checks failed.")
    
    if not db_exists or not tables_exist:
        if should_init:
            if init_database(app):
                tables_exist = True
        else:
            print("\nTo initialize database, run:")
            print("  python scripts/validate_db.py --init")
    
    if tables_exist and not has_data:
        if should_seed:
            seed_database(app)
        else:
            print("\nTo seed database with initial data, run:")
            print("  python scripts/validate_db.py --init --seed")
            print("  # or")
            print("  python seed_db.py")
    
    if not all_ok:
        print("\n" + "=" * 60)
        print("QUICK START (initialize everything):")
        print("=" * 60)
        print("  python scripts/validate_db.py --init --seed")
        print("\nOr use Makefile:")
        print("  make init-db")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
