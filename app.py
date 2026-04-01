"""Shadow Hockey League Flask Application.

Application Factory pattern implementation with proper extension initialization,
logging configuration, security headers, caching and metrics.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from flask import Flask, redirect, render_template, request, url_for
from flask.logging import default_handler
from prometheus_flask_exporter import PrometheusMetrics

from models import Achievement, Country, Manager, db
from services.rating_service import build_leaderboard
from services.cache_service import cache


def create_app(config_class: str | None = None) -> Flask:
    """Application factory for creating Flask app instance.

    Args:
        config_class: Optional import path to config class
                      (e.g., 'config.DevelopmentConfig').
                      If not provided, uses FLASK_ENV or defaults to Development.

    Returns:
        Configured Flask application instance.
    """
    import time
    
    app = Flask(__name__)
    
    # Store app start time for uptime calculation
    app.config['APP_START_TIME'] = time.time()

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

    # Register blueprints (if any in future)
    register_blueprints(app)

    # Register routes
    register_routes(app)

    # Add security headers
    @app.after_request
    def add_security_headers(response: Any) -> Any:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

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
    
    # Initialize caching with Redis (or fallback to simple cache)
    cache_config = {
        'CACHE_TYPE': 'RedisCache',
        'CACHE_REDIS_HOST': os.environ.get('REDIS_HOST', 'localhost'),
        'CACHE_REDIS_PORT': int(os.environ.get('REDIS_PORT', 6379)),
        'CACHE_REDIS_DB': int(os.environ.get('REDIS_DB', 0)),
        'CACHE_REDIS_PASSWORD': os.environ.get('REDIS_PASSWORD', None),
        'CACHE_DEFAULT_TIMEOUT': 300,  # 5 minutes
    }
    
    # Fallback to simple cache if Redis is not available
    try:
        import redis
        redis_client = redis.Redis(
            host=cache_config['CACHE_REDIS_HOST'],
            port=cache_config['CACHE_REDIS_PORT'],
            db=cache_config['CACHE_REDIS_DB'],
            password=cache_config['CACHE_REDIS_PASSWORD'],
            socket_connect_timeout=2,
        )
        redis_client.ping()
        app.logger.info(f"Redis connection established: {cache_config['CACHE_REDIS_HOST']}:{cache_config['CACHE_REDIS_PORT']}")
    except (redis.ConnectionError, redis.TimeoutError, ImportError) as e:
        app.logger.warning(f"Redis not available, falling back to simple cache: {e}")
        cache_config['CACHE_TYPE'] = 'SimpleCache'
    
    app.config.update(cache_config)
    cache.init_app(app)
    
    # Initialize Prometheus metrics (only in non-testing environments)
    if app.config.get('TESTING') is not True:
        try:
            # Initialize Prometheus with default metrics (HTTP requests, latency)
            metrics = PrometheusMetrics(
                app, 
                defaults_prefix='shadow_hockey_league',
                excluded_endpoints=['/static', '/metrics']  # Exclude static and metrics itself
            )
            metrics.register_endpoint('/health')
            
            # Add custom metrics info
            app.logger.info("Prometheus metrics enabled at /metrics")
            app.logger.info("Default metrics: http_requests_total, http_request_duration_seconds")
        except Exception as e:
            app.logger.warning(f"Could not initialize Prometheus metrics: {e}")


def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints."""
    if app.config.get("ENABLE_API"):
        from services.api import api

        # Register API blueprint
        app.register_blueprint(api)
    else:
        app.logger.info("REST API is disabled in this environment (ENABLE_API=False)")


def register_routes(app: Flask) -> None:
    """Register application routes."""

    @app.route("/")
    @cache.cached(timeout=300, key_prefix='leaderboard')  # Cache for 5 minutes
    def index() -> str | tuple[str, int]:
        from sqlalchemy.exc import OperationalError

        try:
            start_time = time.time()

            with db.session.begin():
                leaderboard_data = build_leaderboard(db.session)

            elapsed_ms = round((time.time() - start_time) * 1000)

            # Handle empty database case
            if len(leaderboard_data) == 0:
                app.logger.info(f"Built leaderboard with 0 managers (empty database) in {elapsed_ms}ms")
            else:
                app.logger.info(f"Built leaderboard with {len(leaderboard_data)} managers in {elapsed_ms}ms")

            return render_template(
                "index.html",
                rating_rows=leaderboard_data,
            )
        except OperationalError as e:
            # Database connection error or table not found
            app.logger.error(f"Database operational error: {str(e)}", exc_info=True)
            return (
                render_template(
                    "error.html",
                    message="Ошибка базы данных. Попробуйте обновить страницу или обратитесь к администратору.",
                    error_code=500,
                    error_type="DatabaseError",
                    traceback=str(e) if app.debug else None,
                    show_details=app.debug,
                ),
                500,
            )
        except Exception as e:
            import traceback as tb

            error_traceback = tb.format_exc()
            app.logger.error(f"Error building leaderboard: {str(e)}", exc_info=True)
            return (
                render_template(
                    "error.html",
                    message="Не удалось загрузить рейтинг лиги. Попробуйте обновить страницу.",
                    error_code=500,
                    error_type=type(e).__name__,
                    traceback=error_traceback if app.debug else None,
                    show_details=app.debug,
                ),
                500,
            )

    @app.route("/rating")
    def rating() -> Any:
        """Redirect old /rating URL to main page with anchor."""
        return redirect(url_for("index") + "#rating", code=308)

    @app.route("/health")
    def health_check() -> dict[str, Any]:
        """Health check endpoint for monitoring with metrics.
        
        Returns comprehensive status including:
        - Database status (connection, size, record counts)
        - Redis status (connection, memory)
        - Cache status (type, functionality)
        - Application info (uptime, version)
        """
        import time
        from pathlib import Path
        
        start_time = time.time()

        health_status: dict[str, Any] = {
            "status": "healthy",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "uptime_seconds": round(time.time() - app.config.get('APP_START_TIME', time.time())),
            "managers_count": 0,
            "achievements_count": 0,
            "countries_count": 0,
            "response_time_ms": 0,
            "redis_status": "unknown",
            "cache_status": "unknown",
            "database_status": "unknown",
        }

        # Check database
        try:
            with db.session.begin():
                health_status["managers_count"] = db.session.query(Manager).count()
                health_status["achievements_count"] = db.session.query(Achievement).count()
                health_status["countries_count"] = db.session.query(Country).count()
            health_status["database_status"] = "connected"
            
            # Get database file size
            db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
            if db_path and db_path != ':memory:':
                try:
                    db_size = Path(db_path).stat().st_size
                    health_status["database_size_bytes"] = db_size
                    health_status["database_size_mb"] = round(db_size / 1024 / 1024, 2)
                except Exception:
                    pass
        except Exception as e:
            app.logger.error(f"Database health check failed: {str(e)}")
            health_status["status"] = "degraded"
            health_status["database_status"] = "error"
            health_status["database_error"] = str(e)

        # Check Redis connection
        try:
            import redis
            redis_client = redis.Redis(
                host=os.environ.get('REDIS_HOST', 'localhost'),
                port=int(os.environ.get('REDIS_PORT', 6379)),
                socket_connect_timeout=2,
            )
            redis_client.ping()
            health_status["redis_status"] = "connected"
            
            # Get Redis info
            redis_info = redis_client.info('memory')
            health_status["redis_used_memory_bytes"] = redis_info.get('used_memory', 0)
            health_status["redis_used_memory_mb"] = round(redis_info.get('used_memory', 0) / 1024 / 1024, 2)
            
            # Check cache functionality
            cache.set('_health_check', 'ok', timeout=5)
            if cache.get('_health_check') == 'ok':
                health_status["cache_status"] = "working"
            else:
                health_status["cache_status"] = "error"
                health_status["status"] = "degraded"
        except (redis.ConnectionError, redis.TimeoutError, ImportError) as e:
            health_status["redis_status"] = "disconnected"
            health_status["cache_status"] = "fallback"
            health_status["cache_type"] = app.config.get('CACHE_TYPE', 'unknown')
            # Not critical - fallback to simple cache

        health_status["response_time_ms"] = round((time.time() - start_time) * 1000)

        return health_status

    # Error handlers
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


# Create app instance for manage.py and direct execution
app = create_app()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Shadow Hockey League Server")
    parser.add_argument("--port", type=int, default=5000, help="Server port")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Server host")
    args = parser.parse_args()

    app.logger.info(f"Starting development server on {args.host}:{args.port}")
    app.run(debug=True, port=args.port, host=args.host)
