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
from werkzeug.middleware.proxy_fix import ProxyFix

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
        loaded_config = config_class
    else:
        env = os.environ.get("FLASK_ENV", "development")
        config_map = {
            "development": "config.DevelopmentConfig",
            "production": "config.ProductionConfig",
            "testing": "config.TestingConfig",
        }
        loaded_config = config_map.get(env, "config.DevelopmentConfig")
        app.config.from_object(loaded_config)

    # Fail-fast on dev-default secrets in production (T02 in
    # docs/owner-actions.md). No-op in development / testing.
    if loaded_config == "config.ProductionConfig":
        from config import validate_production_secrets

        validate_production_secrets(app.config)

    # Configure logging
    configure_logging(app)

    # Trust the reverse proxy in front of Gunicorn (Nginx in production) so
    # that `request.remote_addr` and Flask-Limiter see the real client IP
    # via X-Forwarded-For. Without this, every per-IP feature (login
    # rate-limit, API rate-limit, audit log IP) buckets every client under
    # the proxy IP. See docs/ARCHITECTURE.md § Production deployment.
    proxy_count = int(app.config.get("PROXY_FIX_X_FOR", os.environ.get("PROXY_FIX_X_FOR", "1")))
    if proxy_count > 0:
        app.wsgi_app = ProxyFix(  # type: ignore[method-assign]
            app.wsgi_app,
            x_for=proxy_count,
            x_proto=proxy_count,
            x_host=proxy_count,
            x_prefix=proxy_count,
        )

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


def _is_redis_available(app: Flask) -> bool:
    """Probe Redis once and cache the result on the app for the startup phase.

    Avoids opening multiple throw-away connections when both the rate limiter
    and the cache subsystem need to know whether Redis is reachable.
    """
    sentinel = "_redis_available"
    cached = app.config.get(sentinel)
    if cached is not None:
        return cached  # type: ignore[return-value]

    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        app.config[sentinel] = False
        return False

    try:
        import redis

        client = redis.from_url(redis_url, socket_connect_timeout=2)
        client.ping()
        app.config[sentinel] = True
        return True
    except Exception as exc:  # noqa: BLE001 - logging fallback path
        app.logger.warning("Redis unavailable (%s), falling back to in-process backends", exc)
        app.config[sentinel] = False
        return False


def _configure_rate_limiter(app: Flask) -> None:
    """Set ``RATELIMIT_*`` config values before the limiter is initialised.

    - ``RATELIMIT_STORAGE_URI`` is taken from ``REDIS_URL`` env when reachable
      (so the limit is shared across Gunicorn workers in production); falls
      back to ``memory://``.
    - ``RATELIMIT_ENABLED`` is ``False`` for ``TESTING`` so tests don't trip 429
      responses unrelated to the assertion under test.
    """
    if app.config.get("TESTING"):
        app.config.setdefault("RATELIMIT_STORAGE_URI", "memory://")
        app.config.setdefault("RATELIMIT_ENABLED", False)
        return

    storage_uri = (
        os.environ.get("REDIS_URL", "memory://") if _is_redis_available(app) else "memory://"
    )
    app.config.setdefault("RATELIMIT_STORAGE_URI", storage_uri)
    app.config.setdefault("RATELIMIT_ENABLED", True)


def register_extensions(app: Flask) -> None:
    """Initialize Flask extensions."""
    # Initialize SQLAlchemy with app
    db.init_app(app)

    # Response compression (gzip/brotli) — reduces JSON/HTML payload bytes.
    # Disabled in TESTING so test_client responses stay byte-comparable.
    if not app.config.get("TESTING"):
        try:
            from flask_compress import Compress

            Compress(app)
            app.logger.info(
                "Flask-Compress initialized (algorithms=%s)",
                app.config.get("COMPRESS_ALGORITHM", ["br", "gzip"]),
            )
        except ImportError:
            app.logger.warning(
                "Flask-Compress not installed; HTTP responses will not be compressed"
            )

    # Initialize CSRF protection (Этап 3.1)
    if not app.config.get("TESTING"):
        from flask_wtf.csrf import CSRFProtect

        csrf = CSRFProtect()
        csrf.init_app(app)
        app.logger.info("CSRF protection initialized")
    else:
        app.logger.info("CSRF protection skipped (TESTING mode)")

        # Add dummy csrf_token for Jinja templates to prevent UndefinedError
        @app.context_processor
        def dummy_csrf_token() -> dict[str, Any]:
            return dict(csrf_token=lambda: "dummy-token-for-tests")

    # Initialize Rate Limiting (Этап 5)
    # Single Limiter instance shared with services/api.py via services.extensions.
    # Storage is Redis when REDIS_URL is reachable, memory:// otherwise. In TESTING
    # mode the limiter is still bound (so decorators do not raise) but disabled
    # via RATELIMIT_ENABLED=False so tests run at full speed.
    _configure_rate_limiter(app)
    from services.extensions import limiter

    limiter.init_app(app)
    if app.config.get("RATELIMIT_ENABLED", True):
        app.logger.info(
            "Rate limiting initialized (storage=%s)",
            app.config.get("RATELIMIT_STORAGE_URI", "memory://"),
        )
    else:
        app.logger.info("Rate limiting disabled (RATELIMIT_ENABLED=False)")

    # Initialize caching with Redis (or fallback to simple cache).
    # Reuses the cached _is_redis_available() probe so we don't open a
    # second throw-away connection (the rate limiter already checked).
    cache_config: dict[str, Any] = {
        "CACHE_DEFAULT_TIMEOUT": 300,  # 5 minutes
    }

    if _is_redis_available(app):
        cache_config.update(
            {
                "CACHE_TYPE": "RedisCache",
                "CACHE_REDIS_HOST": os.environ.get("REDIS_HOST", "localhost"),
                "CACHE_REDIS_PORT": int(os.environ.get("REDIS_PORT", 6379)),
                "CACHE_REDIS_DB": int(os.environ.get("REDIS_DB", 0)),
                "CACHE_REDIS_PASSWORD": os.environ.get("REDIS_PASSWORD", None),
            }
        )
        app.logger.info(
            "Redis cache: %s:%s",
            cache_config["CACHE_REDIS_HOST"],
            cache_config["CACHE_REDIS_PORT"],
        )
    else:
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
            from services.audit_service import (
                register_audit_request_hook,
                setup_audit_events,
            )

            setup_audit_events()
            # Wire flask_login.current_user → g.current_user_id so the
            # after_flush listener actually writes audit rows for admin
            # CRUD in production (B9 / TIK-36).
            register_audit_request_hook(app)
            app.logger.info("Audit event listeners initialized")

            # Initialize rating recalculation triggers
            from services.rating_service import setup_rating_triggers

            setup_rating_triggers()
            app.logger.info("Rating recalculation triggers initialized")

        except Exception as e:
            app.logger.warning(f"Could not initialize Flask-Admin/Login: {e}")

    # Initialize Prometheus metrics. Singleton in services.metrics_service
    # prevents duplicate endpoint registration across repeated create_app()
    # calls (e.g. in pytest), so this is safe in TESTING too.
    try:
        from services.metrics_service import (
            DEFAULT_METRIC_SUFFIXES,
            METRICS_PREFIX,
            get_metrics,
        )

        metrics = get_metrics(app)
        if metrics is not None:
            app.logger.info("Prometheus metrics enabled at /metrics")
            # Build the banner from the same constants used to configure
            # prometheus_flask_exporter so the two cannot drift (TIK-38).
            metric_names = ", ".join(
                f"{METRICS_PREFIX}_{suffix}" for suffix in DEFAULT_METRIC_SUFFIXES
            )
            app.logger.info(
                f"App metrics: {metric_names} "
                "(plus prometheus_client defaults: process_*, python_*)"
            )
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
    if "csrf" in app.extensions:
        app.extensions["csrf"].exempt(admin_api_bp)

    # API blueprint (if enabled)
    if app.config.get("ENABLE_API"):
        from services.api import api

        app.register_blueprint(api)
        # Exempt API from CSRF (uses API Key auth instead)
        if "csrf" in app.extensions:
            app.extensions["csrf"].exempt(api)
    else:
        app.logger.info("REST API is disabled in this environment (ENABLE_API=False)")

    # Exempt Flask-Admin from CSRF (has its own auth)
    try:
        # The admin blueprint is usually named 'admin'
        admin_bp = app.blueprints.get("admin")
        if admin_bp and "csrf" in app.extensions:
            app.extensions["csrf"].exempt(admin_bp)

        # Also exempt login/logout endpoints if they are separate
        for bp_name in ["admin_login", "admin_logout"]:
            bp = app.blueprints.get(bp_name)
            if bp and "csrf" in app.extensions:
                app.extensions["csrf"].exempt(bp)
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
        use_reloader=False,
    )
