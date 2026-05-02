"""Coverage-focused tests for ``services.metrics_service`` (TIK-50).

These tests exercise the error-handling and boundary paths that
``test_metrics.py`` skips:

* ``get_metrics(None)`` when no instance exists yet → returns ``None``.
* ``PrometheusMetrics`` initialization raises → ``get_metrics`` swallows
  and returns ``None`` (so create_app() never crashes on a duplicate-
  registration error).
* ``reset_metrics`` when an instance exists but ``REGISTRY.unregister``
  raises → exception swallowed.
* ``reset_metrics`` is idempotent when no instance exists.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from services import metrics_service
from services.metrics_service import (
    DEFAULT_METRIC_SUFFIXES,
    METRICS_PREFIX,
    get_metrics,
    reset_metrics,
)


@pytest.fixture(autouse=True)
def _reset_metrics_singleton():
    reset_metrics()
    yield
    reset_metrics()


class TestGetMetricsBoundaries:
    """Exercises the early-return branches in ``get_metrics``."""

    def test_returns_none_when_no_instance_and_no_app(self) -> None:
        # Singleton is reset by the autouse fixture; with no app passed,
        # the function should return None and *not* raise.
        assert get_metrics() is None
        assert get_metrics(None) is None

    def test_swallows_init_exception(self) -> None:
        """A failure inside ``PrometheusMetrics(app, ...)`` must not propagate."""
        from app import create_app

        app = create_app("config.TestingConfig")
        # Wipe the singleton that create_app installed so get_metrics() will
        # try to construct a fresh one for our patched PrometheusMetrics.
        reset_metrics()
        with patch.object(
            metrics_service,
            "PrometheusMetrics",
            side_effect=RuntimeError("registration collision"),
        ):
            # Must not raise; must return None to indicate "no metrics".
            assert get_metrics(app) is None


class TestResetMetrics:
    """Exercises the idempotency and error-tolerance of ``reset_metrics``."""

    def test_reset_with_no_instance_is_noop(self) -> None:
        # Already reset by autouse fixture; calling again must not raise.
        reset_metrics()
        assert get_metrics() is None

    def test_reset_swallows_unregister_failure(self) -> None:
        """If ``REGISTRY.unregister`` raises mid-iteration, ``reset_metrics``
        must still null out the singleton."""
        from app import create_app

        create_app("config.TestingConfig")
        assert get_metrics() is not None  # sanity

        with patch("prometheus_client.REGISTRY.unregister", side_effect=RuntimeError("boom")):
            # Should not raise.
            reset_metrics()
        assert get_metrics() is None


class TestModuleConstants:
    """Lock down the public constants other modules rely on."""

    def test_metrics_prefix_is_namespaced(self) -> None:
        # ``app.py`` builds the startup banner from this prefix; making it
        # blank or generic would silently break the banner.
        assert METRICS_PREFIX == "shadow_hockey_league"

    def test_default_metric_suffixes_are_complete(self) -> None:
        # If a suffix is removed from prometheus_flask_exporter without
        # updating the banner, the user-visible log line drifts. Pin it.
        assert "http_request_total" in DEFAULT_METRIC_SUFFIXES
        assert "http_request_duration_seconds" in DEFAULT_METRIC_SUFFIXES
        assert "http_request_exceptions_total" in DEFAULT_METRIC_SUFFIXES
        assert "exporter_info" in DEFAULT_METRIC_SUFFIXES
