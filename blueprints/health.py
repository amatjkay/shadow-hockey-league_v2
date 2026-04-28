"""Health check blueprint for Shadow Hockey League.

Provides /health endpoint with comprehensive system status.
"""

from __future__ import annotations

import os
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

    # Check Redis connection
    try:
        import redis

        redis_client = redis.Redis(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", 6379)),
            socket_connect_timeout=2,
        )
        redis_client.ping()
        health_status["redis_status"] = "connected"

        # Get Redis info
        redis_info = redis_client.info("memory")
        health_status["redis_used_memory_bytes"] = redis_info.get("used_memory", 0)
        health_status["redis_used_memory_mb"] = round(
            redis_info.get("used_memory", 0) / 1024 / 1024, 2
        )

        # Check cache functionality
        cache.set("_health_check", "ok", timeout=5)
        if cache.get("_health_check") == "ok":
            health_status["cache_status"] = "working"
        else:
            health_status["cache_status"] = "error"
            health_status["status"] = "degraded"
    except (redis.ConnectionError, redis.TimeoutError, ImportError) as e:
        health_status["redis_status"] = "disconnected"
        health_status["cache_status"] = "fallback"
        health_status["cache_type"] = current_app.config.get("CACHE_TYPE", "unknown")
        # Not critical - fallback to simple cache

    health_status["response_time_ms"] = round((time.time() - start_time) * 1000)

    return health_status
