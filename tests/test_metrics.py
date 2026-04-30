"""Test metrics service singleton behaviour.

Refactored from a module-level `print()` script into proper pytest tests.
The original file executed `create_app()` three times at import time, which
ran during pytest collection and polluted the test session. See PR #41
(Phase D) for the cleanup context.
"""

from __future__ import annotations

import pytest

from app import create_app
from services.metrics_service import get_metrics, reset_metrics


@pytest.fixture(autouse=True)
def _reset_metrics_singleton():
    """Ensure each test starts with a fresh metrics singleton."""
    reset_metrics()
    yield
    reset_metrics()


class TestMetricsSingleton:
    """Verify `get_metrics()` returns a singleton across `create_app()` calls."""

    def test_first_app_initializes_metrics(self) -> None:
        """First `create_app()` must initialize the metrics singleton."""
        create_app("config.TestingConfig")
        metrics = get_metrics()
        assert metrics is not None, "Metrics singleton not initialized after first create_app()"

    def test_second_app_reuses_singleton(self) -> None:
        """Second `create_app()` must reuse the same metrics instance."""
        create_app("config.TestingConfig")
        metrics1 = get_metrics()
        create_app("config.TestingConfig")
        metrics2 = get_metrics()
        assert metrics2 is metrics1, "Second create_app() created a new metrics instance"

    def test_third_app_reuses_singleton(self) -> None:
        """Third `create_app()` must still reuse the original metrics instance.

        Regression guard against the duplicate-endpoint warnings that motivated
        the singleton pattern in `services/metrics_service.py`.
        """
        create_app("config.TestingConfig")
        metrics1 = get_metrics()
        create_app("config.TestingConfig")
        create_app("config.TestingConfig")
        metrics3 = get_metrics()
        assert metrics3 is metrics1, "Third create_app() did not reuse the singleton"
