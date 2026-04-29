"""Prometheus metrics service with singleton pattern.

This module provides a singleton PrometheusMetrics instance to prevent
duplicate endpoint registration when create_app() is called multiple times.
"""

from typing import Optional

from prometheus_flask_exporter import PrometheusMetrics

# Single source of truth for the metrics prefix. Imported by app.py to
# build the startup banner so the two never drift (see TIK-38 / B11).
METRICS_PREFIX = "shadow_hockey_league"

# Suffixes that prometheus_flask_exporter emits when configured with
# defaults_prefix=METRICS_PREFIX. Kept here so the banner stays a thin
# formatter over this list rather than duplicating literals.
DEFAULT_METRIC_SUFFIXES = (
    "http_request_total",
    "http_request_duration_seconds",
    "http_request_exceptions_total",
    "exporter_info",
)

# Singleton instance
_metrics_instance: Optional[PrometheusMetrics] = None


def get_metrics(app=None) -> Optional[PrometheusMetrics]:
    """Get or create PrometheusMetrics singleton instance.

    Args:
        app: Flask app instance (required for first initialization)

    Returns:
        PrometheusMetrics instance or None if not initialized
    """
    global _metrics_instance

    if _metrics_instance is not None:
        return _metrics_instance

    if app is None:
        return None

    try:
        _metrics_instance = PrometheusMetrics(
            app,
            defaults_prefix=METRICS_PREFIX,
            excluded_endpoints=["/static", "/metrics", "/health"],
        )
        return _metrics_instance
    except Exception:
        # If initialization fails, return None
        # This prevents duplicate registration attempts
        return None


def reset_metrics() -> None:
    """Reset metrics singleton (useful for testing).

    WARNING: Only use this in test environments!
    """
    global _metrics_instance
    _metrics_instance = None
