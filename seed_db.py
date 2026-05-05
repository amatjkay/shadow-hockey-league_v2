"""Script to seed the database with initial data from JSON files.

This script uses data/seed/*.json files to populate the database.
It is IDEMPOTENT by default - skips existing records.

Usage:
    python seed_db.py           # Safe mode (skip existing)
    python seed_db.py --force   # Force mode (clear and reseed)
    python seed_db.py --check   # Check database state
    python seed_db.py --export  # Export current DB to data/export/
"""

import argparse
import logging
import sys

from app import create_app
from data.export_service import ExportService
from data.seed_service import SeedService
from models import db
from services.cache_service import invalidate_leaderboard_cache

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="Seed or export the database.")
    parser.add_argument(
        "--force", action="store_true", help="Clear all existing data before seeding (DESTRUCTIVE)"
    )
    parser.add_argument(
        "--check", action="store_true", help="Only check database state, do not seed"
    )
    parser.add_argument(
        "--export", action="store_true", help="Export current database to data/export/ directory"
    )
    parser.add_argument(
        "--seed-dir", type=str, default=None, help="Custom seed directory (default: data/seed/)"
    )

    args = parser.parse_args()
    app = create_app()

    with app.app_context():
        # Check mode
        if args.check:
            service = SeedService(db.session)
            state = service.check_db_state()
            print(f"\n[INFO] Database state:")
            print(f"  Countries: {state['countries']}")
            print(f"  Managers: {state['managers']}")
            print(f"  Achievements: {state['achievements']}")

            if state["managers"] > 0:
                print("[INFO] Database has data. Skip seeding (use --force to reseed).")
            else:
                print("[INFO] Database is empty. Run without --check to seed.")
            return

        # Export mode
        if args.export:
            print("\n[INFO] Exporting database to data/export/ ...")
            service = ExportService(db.session)
            result = service.export_all()
            print(f"\n[SUCCESS] Export complete!")
            print(f"  Countries: {result['countries']}")
            print(f"  Managers: {result['managers']}")
            print(f"  Achievements: {result['achievements']}")
            print(f"  Files: data/export/countries.json, managers.json, achievements.json")
            return

        # Seed mode
        print(f"\n[INFO] Seeding database (force={args.force})...")
        service = SeedService(db.session, seed_dir=args.seed_dir)
        result = service.seed_all(force=args.force)

        if result.errors:
            print(f"\n[ERROR] Seeding completed with {len(result.errors)} error(s):")
            for err in result.errors[:5]:
                print(f"  - {err}")
            sys.exit(1)

        print(f"\n{result}")

        # SeedService bypasses the SQLAlchemy ``after_flush`` listener that
        # normally calls ``invalidate_leaderboard_cache`` (it commits raw
        # INSERTs in batches). Without this call the next page load would
        # still see the pre-seed (often empty) cached leaderboard until the
        # default TTL expires. Failures are non-fatal — a redis hiccup
        # mustn't break a successful seed.
        if invalidate_leaderboard_cache():
            print("[INFO] Leaderboard cache invalidated.")
        else:
            print("[WARN] Could not invalidate leaderboard cache (Redis unreachable?).")


if __name__ == "__main__":
    main()
