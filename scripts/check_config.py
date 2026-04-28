#!/usr/bin/env python
"""Configuration check script for Shadow Hockey League.

This script validates the application configuration before deployment.
It checks for common issues that could cause problems in production.

Usage:
    python scripts/check_config.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_env_file() -> bool:
    """Check if .env file exists and has required variables."""
    env_file = PROJECT_ROOT / ".env"

    if not env_file.exists():
        print("WARN - .env file not found")
        print("       Copy .env.example to .env and configure it")
        return False

    print("OK   - .env file exists")

    # Check required variables
    with open(env_file) as f:
        content = f.read()

    required_vars = ["FLASK_ENV", "DATABASE_URL", "SECRET_KEY"]
    all_ok = True

    for var in required_vars:
        if var in content:
            print(f"OK   - {var} is set")
        else:
            print(f"WARN - {var} is not set")
            all_ok = False

    # Check for relative database path
    if "DATABASE_URL=sqlite:///dev.db" in content:
        print("WARN - DATABASE_URL uses relative path")
        print("       Use absolute path to prevent instance/ folder issues")
        all_ok = False
    elif "DATABASE_URL=sqlite:///" in content:
        print("OK   - DATABASE_URL uses absolute path")

    return all_ok


def check_database_path() -> bool:
    """Check if database path is accessible."""
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:
        pass

    db_url = os.environ.get("DATABASE_URL", "")

    if not db_url:
        print("WARN - DATABASE_URL not set")
        return False

    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        if db_path.startswith("/"):
            db_file = Path(db_path)
            if db_file.exists():
                print(f"OK   - Database exists: {db_file}")
                return True
            else:
                print(f"WARN - Database not found: {db_file}")
                print("       Run 'python seed_db.py' to create it")
                return False

    return True


def check_redis_connection() -> bool:
    """Check if Redis is accessible."""
    try:
        import redis

        redis_host = os.environ.get("REDIS_HOST", "localhost")
        redis_port = int(os.environ.get("REDIS_PORT", 6379))

        r = redis.Redis(host=redis_host, port=redis_port, socket_timeout=2)
        r.ping()
        print(f"OK   - Redis connected: {redis_host}:{redis_port}")
        return True
    except ImportError:
        print("WARN - redis package not installed")
        print("       Install with: pip install redis")
        return False
    except redis.ConnectionError:
        print(f"WARN - Redis not available: {redis_host}:{redis_port}")
        print("       Application will fallback to SimpleCache")
        return False


def check_secret_key() -> bool:
    """Check if SECRET_KEY is secure."""
    secret_key = os.environ.get("SECRET_KEY", "")

    if not secret_key:
        print("WARN - SECRET_KEY is not set")
        return False

    if secret_key in ["dev-secret-key-change-in-production", "CHANGE_THIS_TO_A_LONG_RANDOM_STRING"]:
        print("WARN - SECRET_KEY uses default value")
        print('       Generate a new key: python -c "import secrets; print(secrets.token_hex(32))"')
        return False

    if len(secret_key) < 32:
        print("WARN - SECRET_KEY is too short (min 32 chars)")
        return False

    print("OK   - SECRET_KEY is set and looks secure")
    return True


def main() -> int:
    """Run all configuration checks."""
    print("=" * 60)
    print("Shadow Hockey League - Configuration Check")
    print("=" * 60)
    print()

    checks = [
        ("Environment File", check_env_file),
        ("Database Path", check_database_path),
        ("Redis Connection", check_redis_connection),
        ("Secret Key", check_secret_key),
    ]

    all_passed = True

    for name, check_func in checks:
        print(f"\n[{name}]")
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"ERROR - {e}")
            all_passed = False

    print()
    print("=" * 60)

    if all_passed:
        print("OK   - All checks passed!")
        print("=" * 60)
        return 0
    else:
        print("WARN - Some checks failed. Review warnings above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
