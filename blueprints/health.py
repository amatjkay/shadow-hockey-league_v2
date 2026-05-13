"""Health check blueprint for Shadow Hockey League.

Provides /health endpoint with comprehensive system status.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from flask import Blueprint

from models import Achievement, Country, Manager, db
from services.cache_service import cache

health = Blueprint("health", __name__)


@health.route("/health")
def health_check() -> dict[str, Any]:
    """Health check endpoint for monitoring with metrics.

    Returns comprehensive status including:
    - Database status (connection, size, record counts)
    - Redis status (connection, memory)
    - Cache status (type, functionality)
    - Application info (uptime, version)
    """
    from flask import current_app

    start_time = time.time()

    cache_backend = getattr(cache, "cache", None)
    cache_backend_type = (
        type(cache_backend).__name__ if cache_backend is not None else "uninitialised"
    )

    health_status: dict[str, Any] = {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "uptime_seconds": round(
            time.time() - current_app.config.get("APP_START_TIME", time.time())
        ),
        "managers_count": 0,
        "achievements_count": 0,
        "countries_count": 0,
        "response_time_ms": 0,
        "redis_status": "unknown",
        "cache_status": "unknown",
        "database_status": "unknown",
        # TIK-100: surface the actual backend per worker so a partial Redis
        # fallback (only some Gunicorn workers running SimpleCache) is
        # visible without grepping journald. ``cache_type_config`` is what
        # the worker *asked* for; ``cache_backend_type`` is what
        # ``flask_caching`` actually wired up.
        "cache_backend_type": cache_backend_type,
        "cache_type_config": str(current_app.config.get("CACHE_TYPE", "unknown")),
        "cache_key_prefix": str(current_app.config.get("CACHE_KEY_PREFIX", "")),
    }

    # Check database
    try:
        with db.session.begin():
            health_status["managers_count"] = db.session.query(Manager).count()
            health_status["achievements_count"] = db.session.query(Achievement).count()
            health_status["countries_count"] = db.session.query(Country).count()
        health_status["database_status"] = "connected"

        # Get database file size
        db_path = current_app.config.get("SQLALCHEMY_DATABASE_URI", "").replace("sqlite:///", "")
        if db_path and db_path != ":memory:":
            try:
                db_size = Path(db_path).stat().st_size
                health_status["database_size_bytes"] = db_size
                health_status["database_size_mb"] = round(db_size / 1024 / 1024, 2)
            except Exception:
                pass
    except Exception as e:
        current_app.logger.error(f"Database health check failed: {str(e)}")
        health_status["status"] = "degraded"
        health_status["database_status"] = "error"
        health_status["database_error"] = str(e)

    # Check Redis connection using the already-resolved config values
    # instead of re-reading env vars.
    try:
        import redis

        redis_client = redis.Redis(
            host=current_app.config.get("CACHE_REDIS_HOST", "localhost"),
            port=current_app.config.get("CACHE_REDIS_PORT", 6379),
            socket_connect_timeout=2,
            socket_timeout=1.0,
        )
        redis_client.ping()
        health_status["redis_status"] = "connected"

        redis_info = redis_client.info("memory")
        health_status["redis_used_memory_bytes"] = redis_info.get("used_memory", 0)
        health_status["redis_used_memory_mb"] = round(
            redis_info.get("used_memory", 0) / 1024 / 1024, 2
        )

        cache.set("_health_check", "ok", timeout=5)
        if cache.get("_health_check") == "ok":
            health_status["cache_status"] = "working"
        else:
            health_status["cache_status"] = "error"
            health_status["status"] = "degraded"
    except (redis.ConnectionError, redis.TimeoutError, ImportError):
        health_status["redis_status"] = "disconnected"
        health_status["cache_status"] = "fallback"
        health_status["cache_type"] = current_app.config.get("CACHE_TYPE", "unknown")

    health_status["response_time_ms"] = round((time.time() - start_time) * 1000)

    return health_status
