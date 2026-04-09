"""Shadow Hockey League Flask Application.

Application Factory pattern implementation with proper extension initialization,
logging configuration, security headers, caching and metrics.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from flask import Flask
from flask.logging import default_handler

from models import db
from services.admin import init_admin


def create_app(config_class: str | None = None) -> Flask:
    """Application factory for creating Flask app instance.

    Args:
        config_class: Optional import path to config class
                      (e.g., 'config.DevelopmentConfig').
                      If not provided, uses FLASK_ENV or defaults to Development.

    Returns:
        Configured Flask application instance.
    """
    # IMPORTANT: Disable instance_relative_config to prevent SQLite from using instance/ folder
    app = Flask(__name__, instance_relative_config=False)

    # Store app start time for uptime calculation
    app.config["APP_START_TIME"] = time.time()

    # Load configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        env = os.environ.get("FLASK_ENV", "development")
        config_map = {
            "development": "config.DevelopmentConfig",
            "production": "config.ProductionConfig",
            "testing": "config.TestingConfig",
        }
        app.config.from_object(config_map.get(env, "config.DevelopmentConfig"))

    # Configure logging
    configure_logging(app)

    # Register extensions
    register_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Add security headers
    @app.after_request
    def add_security_headers(response: Any) -> Any:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # Error handlers
    register_error_handlers(app)

    return app


def configure_logging(app: Flask) -> None:
    """Configure application logging."""
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO"))

    # Remove default handler
    app.logger.removeHandler(default_handler)

    # Create formatter
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

    # File handler (production only)
    if app.config.get("LOG_TO_FILE"):
        try:
            from logging.handlers import RotatingFileHandler

            # Create logs directory
            log_dir = app.config.get("LOG_DIR")
            if log_dir:
                log_dir.mkdir(exist_ok=True)

            # Rotating file handler
            file_handler = RotatingFileHandler(
                app.config.get("LOG_FILE", "logs/app.log"),
                maxBytes=app.config.get("LOG_MAX_BYTES", 10 * 1024 * 1024),
                backupCount=app.config.get("LOG_BACKUP_COUNT", 5),
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            app.logger.addHandler(file_handler)
            app.logger.info("File logging enabled")
        except Exception as e:
            app.logger.warning(f"Could not enable file logging: {e}")

    app.logger.setLevel(log_level)


def register_extensions(app: Flask) -> None:
    """Initialize Flask extensions."""
    # Initialize SQLAlchemy with app
    db.init_app(app)

    # Initialize CSRF protection (Этап 3.1)
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect()
    csrf.init_app(app)
    app.logger.info("CSRF protection initialized")

    # Initialize Rate Limiting (Этап 5)
    # Disable rate limiting in testing mode to speed up CI/CD and tests
    if not app.config.get("TESTING"):
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        limiter = Limiter(
            key_func=get_remote_address,
            app=app,
            default_limits=["200 per day", "50 per hour"],
            storage_uri="memory://",
        )
        app.logger.info("Rate limiting initialized")
    else:
        app.logger.info("Rate limiting disabled (TESTING mode)")

    # Initialize caching with Redis (or fallback to simple cache)
    cache_config = {
        "CACHE_TYPE": "RedisCache",
        "CACHE_REDIS_HOST": os.environ.get("REDIS_HOST", "localhost"),
        "CACHE_REDIS_PORT": int(os.environ.get("REDIS_PORT", 6379)),
        "CACHE_REDIS_DB": int(os.environ.get("REDIS_DB", 0)),
        "CACHE_REDIS_PASSWORD": os.environ.get("REDIS_PASSWORD", None),
        "CACHE_DEFAULT_TIMEOUT": 300,  # 5 minutes
    }

    # Fallback to simple cache if Redis is not available
    try:
        import redis

        redis_client = redis.Redis(
            host=cache_config["CACHE_REDIS_HOST"],
            port=cache_config["CACHE_REDIS_PORT"],
            db=cache_config["CACHE_REDIS_DB"],
            password=cache_config["CACHE_REDIS_PASSWORD"],
            socket_connect_timeout=2,
        )
        redis_client.ping()
        app.logger.info(f"Redis connection established: {cache_config['CACHE_REDIS_HOST']}:{cache_config['CACHE_REDIS_PORT']}")
    except (redis.ConnectionError, redis.TimeoutError, ImportError) as e:
        app.logger.warning(f"Redis not available, falling back to simple cache: {e}")
        cache_config["CACHE_TYPE"] = "SimpleCache"

    app.config.update(cache_config)

    from services.cache_service import cache
    cache.init_app(app)

    # Initialize Flask-Admin and Flask-Login within application context
    with app.app_context():
        try:
            init_admin(app)
            app.logger.info("Flask-Admin and Flask-Login initialized")

            # Initialize audit events after admin is set up
            from services.audit_service import setup_audit_events
            setup_audit_events()
            app.logger.info("Audit event listeners initialized")

        except Exception as e:
            app.logger.warning(f"Could not initialize Flask-Admin/Login: {e}")

    # Initialize Prometheus metrics (only in non-testing environments)
    if app.config.get("TESTING") is not True:
        try:
            from services.metrics_service import get_metrics

            metrics = get_metrics(app)
            if metrics is not None:
                app.logger.info("Prometheus metrics enabled at /metrics")
                app.logger.info("Default metrics: http_requests_total, http_request_duration_seconds")
        except Exception as e:
            app.logger.warning(f"Could not initialize Prometheus metrics: {e}")


def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints."""
    # Main blueprint (leaderboard page)
    from blueprints.main import main
    app.register_blueprint(main)

    # Health check blueprint
    from blueprints.health import health
    app.register_blueprint(health)

    # Admin API blueprint (for Select2 dropdowns and bulk operations)
    from blueprints.admin_api import admin_api_bp
    app.register_blueprint(admin_api_bp)
    # Exempt admin API from CSRF (uses Flask-Login auth)
    if 'csrf' in app.extensions:
        app.extensions['csrf'].exempt(admin_api_bp)

    # API blueprint (if enabled)
    if app.config.get("ENABLE_API"):
        from services.api import api
        app.register_blueprint(api)
        # Exempt API from CSRF (uses API Key auth instead)
        if 'csrf' in app.extensions:
            app.extensions['csrf'].exempt(api)
    else:
        app.logger.info("REST API is disabled in this environment (ENABLE_API=False)")

    # Exempt Flask-Admin from CSRF (has its own auth)
    try:
        # The admin blueprint is usually named 'admin'
        admin_bp = app.blueprints.get('admin')
        if admin_bp and 'csrf' in app.extensions:
            app.extensions['csrf'].exempt(admin_bp)
        
        # Also exempt login/logout endpoints if they are separate
        for bp_name in ['admin_login', 'admin_logout']:
            bp = app.blueprints.get(bp_name)
            if bp and 'csrf' in app.extensions:
                app.extensions['csrf'].exempt(bp)
    except Exception as e:
        app.logger.warning(f"Could not exempt admin from CSRF: {e}")


def register_error_handlers(app: Flask) -> None:
    """Register error handlers."""
    from flask import render_template, request

    @app.errorhandler(404)
    def not_found_error(error: Any) -> tuple[str, int]:
        app.logger.warning(f"404 error: {request.url}")
        return (
            render_template(
                "error.html",
                message="Страница не найдена.",
                error_code=404,
            ),
            404,
        )

    @app.errorhandler(500)
    def internal_error(error: Any) -> tuple[str, int]:
        db.session.rollback()
        app.logger.error(f"500 error: {str(error)}", exc_info=True)
        return (
            render_template(
                "error.html",
                message="Внутренняя ошибка сервера. Пожалуйста, попробуйте позже.",
                error_code=500,
            ),
            500,
        )


# ==================== Entry point ====================

if __name__ == "__main__":
    app = create_app()
    app.run(
        host=os.environ.get("FLASK_RUN_HOST", "127.0.0.1"),
        port=int(os.environ.get("FLASK_RUN_PORT", "5000")),
        debug=app.config.get("DEBUG", False),
    )
