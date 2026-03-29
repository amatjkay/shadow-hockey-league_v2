"""Shadow Hockey League Flask Application.

Application Factory pattern implementation with proper extension initialization,
logging configuration, and security headers.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from flask import Flask, redirect, render_template, url_for
from flask.logging import default_handler

from data.rating import build_leaderboard


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

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

    app.logger.setLevel(log_level)


def register_extensions(app: Flask) -> None:
    """Initialize Flask extensions."""
    # Placeholder for future extensions (SQLAlchemy, LoginManager, etc.)
    pass


def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints."""
    # Placeholder for future blueprints
    pass


def register_routes(app: Flask) -> None:
    """Register application routes."""

    @app.route("/")
    def index() -> str | tuple[str, int]:
        try:
            leaderboard_data = build_leaderboard()
            app.logger.info(f"Built leaderboard with {len(leaderboard_data)} managers")
            return render_template(
                "index.html",
                rating_rows=leaderboard_data,
            )
        except Exception as e:
            app.logger.error(f"Error building leaderboard: {str(e)}", exc_info=True)
            return render_template("error.html"), 500

    @app.route("/rating")
    def rating() -> Any:
        """Redirect old /rating URL to main page with anchor."""
        return redirect(url_for("index") + "#rating", code=308)

    @app.route("/health")
    def health_check() -> dict[str, str]:
        """Health check endpoint for monitoring."""
        return {"status": "healthy"}


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
