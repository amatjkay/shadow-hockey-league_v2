"""Shadow Hockey League Flask Application.

Application Factory pattern implementation with proper extension initialization,
logging configuration, and security headers.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from flask import Flask, redirect, render_template, request, url_for
from flask.logging import default_handler

from models import db
from services.rating_service import build_leaderboard


def create_app(config_class: str | None = None) -> Flask:
    """Application factory for creating Flask app instance.

    Args:
        config_class: Optional import path to config class
                      (e.g., 'config.DevelopmentConfig').
                      If not provided, uses FLASK_ENV or defaults to Development.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

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
    def index() -> str | tuple[str, int]:
        from sqlalchemy.exc import OperationalError

        try:
            with db.session.begin():
                leaderboard_data = build_leaderboard(db.session)
            
            # Handle empty database case
            if len(leaderboard_data) == 0:
                app.logger.info("Built leaderboard with 0 managers (empty database)")
            else:
                app.logger.info(f"Built leaderboard with {len(leaderboard_data)} managers")
            
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
    def health_check() -> dict[str, str]:
        """Health check endpoint for monitoring."""
        return {"status": "healthy"}

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
