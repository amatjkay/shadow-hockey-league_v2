"""Prometheus metrics service with singleton pattern.

This module provides a singleton PrometheusMetrics instance to prevent
duplicate endpoint registration when create_app() is called multiple times.
"""

from typing import Optional
from prometheus_flask_exporter import PrometheusMetrics

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
            defaults_prefix='shadow_hockey_league',
            excluded_endpoints=['/static', '/metrics', '/health']
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
