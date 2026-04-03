"""Application configuration with environment variable support.

Uses python-dotenv to load environment variables from .env file.
All configuration values can be overridden via environment variables.

Database path is ALWAYS absolute to prevent 'instance/' folder issues.
"""

import os
from pathlib import Path

# Optional dotenv support - gracefully degrades if not installed
try:
    from dotenv import load_dotenv

    # Load environment variables from .env file (project root)
    BASE_DIR = Path(__file__).parent
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    # python-dotenv not installed, use environment variables only
    pass


class Config:
    """Base configuration class."""

    BASE_DIR = Path(__file__).parent

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STATIC_FOLDER = "static"
    TEMPLATES_FOLDER = "templates"
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # CSRF Protection (Этап 3.1)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get("WTF_CSRF_SECRET_KEY") or "csrf-dev-key-change-in-production"
    WTF_CSRF_TIME_LIMIT = None  # No expiration for CSRF tokens

    # Logging
    LOG_DIR = Path(__file__).parent / "logs"
    LOG_FILE = LOG_DIR / "app.log"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT = 5

    # Database path - ALWAYS use absolute path to prevent 'instance/' folder issues
    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL with absolute path.
        
        Returns:
            Absolute SQLite path (e.g., sqlite:///C:/project/dev.db)
        """
        # Check environment variable first
        env_db_url = os.environ.get("DATABASE_URL")
        if env_db_url:
            # If it's a relative SQLite path, convert to absolute
            if env_db_url.startswith("sqlite:///") and not env_db_url.startswith("sqlite:////"):
                # Relative path - convert to absolute
                db_filename = env_db_url.replace("sqlite:///", "")
                absolute_path = cls.BASE_DIR / db_filename
                return f"sqlite:///{absolute_path}"
            return env_db_url
        
        # Default: absolute path to dev.db in project root
        default_db_path = cls.BASE_DIR / "dev.db"
        return f"sqlite:///{default_db_path}"

    # Set DATABASE_URL for consistency
    DATABASE_URL = property(get_database_url)


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = Config.get_database_url()


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = Config.get_database_url()
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    LOG_TO_FILE = True
    ENABLE_API = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    ENABLE_API = True  # Enable API for tests
