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

    # Response payload optimisation (token-efficiency).
    # Flask-Compress: gzip/brotli for HTML+JSON. Skip already-compressed types.
    COMPRESS_MIMETYPES = [
        "text/html",
        "text/css",
        "text/xml",
        "text/plain",
        "application/json",
        "application/javascript",
        "application/xml",
        "image/svg+xml",
    ]
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500  # don't bother compressing tiny responses
    COMPRESS_ALGORITHM = ["br", "gzip"]

    # CSRF Protection (Этап 3.1)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = (
        os.environ.get("WTF_CSRF_SECRET_KEY") or "csrf-dev-key-change-in-production"
    )
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
    ENABLE_API = True  # API включено для локальной разработки
    API_KEY_SECRET = os.environ.get("API_KEY_SECRET") or "dev-api-key-secret"


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = Config.get_database_url()
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    LOG_TO_FILE = True
    ENABLE_API = True  # Этап 5: API включено с аутентификацией
    API_KEY_SECRET = os.environ.get("API_KEY_SECRET") or "api-key-secret-change-in-production"

    # Response-byte optimisation.
    # 1. Strip pretty-print + spaces from JSON (default in dev for readability).
    JSONIFY_PRETTYPRINT_REGULAR = False
    JSON_SORT_KEYS = False
    # 2. Allow Flask-Compress to produce smaller bodies (br > gzip).
    COMPRESS_LEVEL = 6
    # 3. Long-lived cache for /static (icons, CSS, JS): 1 year. Bust via
    #    versioned/hashed URLs (or by editing the static file path).
    SEND_FILE_MAX_AGE_DEFAULT = 31_536_000  # 1 year


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    ENABLE_API = True  # Enable API for tests
    SESSION_TYPE = "filesystem"

    # Faster caching for tests
    CACHE_TYPE = "SimpleCache"

    # Enable foreign key constraints in SQLite for testing
    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL with foreign key constraints enabled."""
        base_url = super().get_database_url()
        if base_url.startswith("sqlite:///"):
            # Add foreign key pragma for SQLite
            return base_url + "?foreign_keys=on"
        return base_url


# Pairs of (env-var name, dev-default literal) that ProductionConfig must
# not start with. Kept in sync with the class bodies above so the validator
# stays a single source of truth for the placeholders.
_PRODUCTION_SECRET_DEFAULTS: tuple[tuple[str, str], ...] = (
    ("SECRET_KEY", "dev-secret-key-change-in-production"),
    ("WTF_CSRF_SECRET_KEY", "csrf-dev-key-change-in-production"),
    ("API_KEY_SECRET", "api-key-secret-change-in-production"),
)


def validate_production_secrets(config: dict) -> None:
    """Fail-fast guard for ProductionConfig (T02 in docs/owner-actions.md).

    Raises ``RuntimeError`` if any required production secret is missing or
    still set to the dev placeholder shipped in this file. Called from
    ``app.create_app()`` after ``app.config.from_object(...)`` when
    ``FLASK_ENV=production``. No-op in development / testing.
    """
    missing: list[str] = []
    for name, dev_default in _PRODUCTION_SECRET_DEFAULTS:
        value = config.get(name)
        if not value or value == dev_default:
            missing.append(name)
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            f"ProductionConfig refuses to start: {joined} is unset or still "
            "uses the dev placeholder. Generate a strong value with "
            '`python -c "import secrets; print(secrets.token_hex(32))"` and '
            "set it in the production .env / systemd unit."
        )
