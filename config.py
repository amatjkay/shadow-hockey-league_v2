"""Application configuration with environment variable support.

Uses python-dotenv to load environment variables from .env file.
All configuration values can be overridden via environment variables.
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

    # Database path - uses absolute path for production compatibility
    # Environment variable can override (use absolute path on PythonAnywhere!)
    DATABASE_URL = os.environ.get("DATABASE_URL") or f"sqlite:///{BASE_DIR}/dev.db"
    ENABLE_API = True

    # Logging
    LOG_DIR = Path(__file__).parent / "logs"
    LOG_FILE = LOG_DIR / "app.log"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT = 5

    # Ensure DATABASE_URL is set
    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL with fallback to default."""
        return cls.DATABASE_URL or "sqlite:///dev.db"


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
