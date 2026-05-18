"""Health check blueprint for Shadow Hockey League.

Provides /health endpoint with comprehensive system status.

## Contract (TIK-91)

- ``status: healthy`` / HTTP 200 — DB up + Redis up.
- ``status: degraded`` / HTTP 200 — DB up, Redis (or cache round-trip) down,
  request did **not** ask for strict mode. Default for uptime checkers;
  payload shape unchanged from pre-TIK-91.
- ``status: degraded`` / HTTP 503 — same as above but the request passed
  ``?strict=1`` or ``X-Health-Mode: strict``. Used by k8s readinessProbe so
  the pod is rotated out of the load balancer when its Redis-backed cache
  is gone, even though the app itself still serves traffic.
- ``status: down`` / HTTP 503 — database query failed. Always 503 regardless
  of strict mode; the app cannot serve real traffic without the DB.

Latency is observed on the ``health_response_seconds`` Prometheus histogram
labelled by the final ``status`` value, on every call.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from flask import Blueprint, jsonify, request
from prometheus_client import Histogram
from werkzeug.wrappers import Response

from models import Achievement, Country, Manager, db
from services.cache_service import cache

health = Blueprint("health", __name__)


# Module-level singleton so repeated ``create_app()`` calls in tests don't
# try to re-register the same collector with ``prometheus_client.REGISTRY``
# (``services.metrics_service.reset_metrics`` only cleans
# ``prometheus_flask_exporter`` collectors, which is the desired behaviour:
# this histogram lives across app re-creations).
HEALTH_RESPONSE_SECONDS = Histogram(
    "health_response_seconds",
    "Response time of /health endpoint by final status",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
    labelnames=("status",),
)


def _strict_mode_requested() -> bool:
    """Return True if the caller opted into strict-mode via query or header.

    Accepts ``?strict=1`` (any truthy value: ``1`` / ``true`` / ``yes``,
    case-insensitive) **or** ``X-Health-Mode: strict``. Anything else —
    including the absence of both — keeps the pre-TIK-91 behaviour
    (``200 + degraded`` for Redis-down).
    """
    strict_param = (request.args.get("strict") or "").strip().lower()
    if strict_param in {"1", "true", "yes"}:
        return True
    strict_header = (request.headers.get("X-Health-Mode") or "").strip().lower()
    return strict_header == "strict"


@health.route("/health")
def health_check() -> Response:
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

    db_down = False

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
        # TIK-91: DB failure escalates to ``status: down`` (was ``degraded``
        # pre-TIK-91) so k8s readiness + uptime checkers both see 503.
        health_status["status"] = "down"
        health_status["database_status"] = "error"
        health_status["database_error"] = str(e)
        db_down = True

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
            if not db_down:
                health_status["status"] = "degraded"
    except (redis.ConnectionError, redis.TimeoutError, ImportError):
        health_status["redis_status"] = "disconnected"
        health_status["cache_status"] = "fallback"
        health_status["cache_type"] = current_app.config.get("CACHE_TYPE", "unknown")
        if not db_down:
            health_status["status"] = "degraded"

    health_status["response_time_ms"] = round((time.time() - start_time) * 1000)

    final_status = health_status["status"]
    if final_status == "down":
        http_code = 503
    elif final_status == "degraded" and _strict_mode_requested():
        http_code = 503
    else:
        http_code = 200

    HEALTH_RESPONSE_SECONDS.labels(status=final_status).observe(time.time() - start_time)

    response = jsonify(health_status)
    response.status_code = http_code
    return response
