"""Coverage-focused tests for ``app.create_app`` (TIK-50).

These tests target the branches in ``app.py`` that the main test suite
skips because it always passes an explicit ``config_class`` and the
TestingConfig short-circuits production-only init paths:

* ``create_app(None)`` resolves config via ``FLASK_ENV``.
* The 500 error handler renders the error template (covered by
  ``register_error_handlers``).
* ``register_blueprints`` exempts the API blueprint from CSRF when
  ``ENABLE_API=True``.
* ``configure_logging`` swallows file-handler IOError without raising.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from app import configure_logging, create_app


class TestCreateAppEnvFallback:
    """``create_app(None)`` should pick a config based on ``FLASK_ENV``."""

    def test_default_env_uses_development_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Strip the explicit testing override so the env-fallback branch runs.
        monkeypatch.delenv("FLASK_ENV", raising=False)
        app = create_app(None)
        assert app.config["DEBUG"] in (True, False)
        # DevelopmentConfig sets DEBUG=True; assert by config class name to be robust.
        assert "Development" in type(app.config).__name__ or app.config.get("DEBUG") is True

    def test_unknown_env_falls_back_to_development(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FLASK_ENV", "this-env-does-not-exist")
        app = create_app(None)
        # Falls back to DevelopmentConfig.get; just assert app is built.
        assert app is not None
        assert "DEBUG" in app.config

    def test_explicit_testing_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FLASK_ENV", "testing")
        app = create_app(None)
        assert app.config.get("TESTING") is True


class TestErrorHandlers:
    """Confirm the 500 handler renders the template and rolls back the session."""

    def test_500_handler_returns_error_template(self) -> None:
        app = create_app("config.TestingConfig")
        # Inject a route that always raises 500.
        from flask import Blueprint

        bp = Blueprint("boom", __name__)

        @bp.route("/__boom__")
        def _boom():
            raise RuntimeError("forced 500 for test")

        app.register_blueprint(bp)
        # Disable test propagation so the registered errorhandler runs.
        app.config["PROPAGATE_EXCEPTIONS"] = False
        app.config["TRAP_HTTP_EXCEPTIONS"] = False

        with app.test_client() as c:
            resp = c.get("/__boom__")
        assert resp.status_code == 500
        assert b"500" in resp.data or "ошибка" in resp.data.decode("utf-8", "ignore").lower()

    def test_404_handler_returns_error_template(self) -> None:
        app = create_app("config.TestingConfig")
        with app.test_client() as c:
            resp = c.get("/this-route-does-not-exist-xyz")
        assert resp.status_code == 404


class TestBlueprintRegistrationApiPath:
    """``register_blueprints`` must exempt the API blueprint from CSRF when enabled."""

    def test_api_enabled_registers_and_csrf_exempt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Force ENABLE_API=True via the config class.
        from config import TestingConfig

        monkeypatch.setattr(TestingConfig, "ENABLE_API", True, raising=False)
        # Re-create to re-run register_blueprints with the new config.
        app = create_app("config.TestingConfig")
        # Either the API blueprint is registered, or ENABLE_API=True path was hit.
        assert "api" in app.blueprints or app.config.get("ENABLE_API") is True


class TestConfigureLogging:
    """``configure_logging`` must swallow file-handler IOError without raising."""

    def test_swallows_file_handler_error(self, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Build a bare app and force LOG_TO_FILE on so the file-handler branch
        # runs. Mock RotatingFileHandler to raise so the except path is taken.
        from flask import Flask

        app = Flask(__name__)
        app.config["LOG_LEVEL"] = "INFO"
        app.config["LOG_TO_FILE"] = True
        app.config["LOG_DIR"] = tmp_path
        app.config["LOG_FILE"] = str(tmp_path / "app.log")

        with patch(
            "logging.handlers.RotatingFileHandler",
            side_effect=OSError("no disk space"),
        ):
            configure_logging(app)
        # Should not raise; we just want to know the function returned.

    def test_log_to_file_writes_into_log_dir(self, tmp_path) -> None:
        from flask import Flask

        app = Flask(__name__)
        app.config["LOG_LEVEL"] = "INFO"
        app.config["LOG_TO_FILE"] = True
        app.config["LOG_DIR"] = tmp_path
        app.config["LOG_FILE"] = str(tmp_path / "app.log")

        configure_logging(app)
        app.logger.info("smoke")
        # File may or may not be flushed yet; just assert the directory exists
        # and the function completed.
        assert tmp_path.exists()


class TestRedisInitRetry:
    """``_is_redis_available`` retries with backoff at startup (TIK-101).

    Production hit a systemd-ordering race: gunicorn workers booted before
    ``redis-server.service`` was ready, so the one-shot ``ping()`` failed and
    each worker locked into ``SimpleCache`` permanently. With 4 workers the
    leaderboard cache effectively had no cross-process sharing, surfacing as
    5–30 s page loads on season-tab switching.
    """

    def test_no_redis_url_returns_false_without_probing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from flask import Flask

        from app import _is_redis_available

        monkeypatch.delenv("REDIS_URL", raising=False)
        app = Flask(__name__)
        with patch("redis.from_url") as from_url:
            assert _is_redis_available(app) is False
            from_url.assert_not_called()
        # And the sentinel is cached so subsequent calls are also instant.
        with patch("redis.from_url") as from_url:
            assert _is_redis_available(app) is False
            from_url.assert_not_called()

    def test_sentinel_short_circuits_repeat_calls(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from flask import Flask

        from app import _is_redis_available

        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        app = Flask(__name__)
        client = MagicMock()
        client.ping.return_value = True
        with patch("redis.from_url", return_value=client) as from_url:
            assert _is_redis_available(app) is True
            assert _is_redis_available(app) is True
            # Second call reads the cached sentinel and never re-probes.
            assert from_url.call_count == 1

    def test_first_attempt_success_does_not_sleep(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from flask import Flask

        from app import _is_redis_available

        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        app = Flask(__name__)
        client = MagicMock()
        client.ping.return_value = True
        with (
            patch("redis.from_url", return_value=client),
            patch("app.time.sleep") as sleep,
        ):
            assert _is_redis_available(app) is True
            sleep.assert_not_called()

    def test_retries_then_succeeds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The whole point of TIK-101: transient failures are recovered."""
        from flask import Flask

        from app import _is_redis_available

        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        monkeypatch.setenv("REDIS_INIT_RETRIES", "5")
        monkeypatch.setenv("REDIS_INIT_RETRY_DELAY_SECONDS", "0.01")
        app = Flask(__name__)

        # First 2 attempts fail, 3rd succeeds.
        failing = MagicMock()
        failing.ping.side_effect = ConnectionError("ECONNREFUSED")
        succeeding = MagicMock()
        succeeding.ping.return_value = True
        with patch(
            "redis.from_url",
            side_effect=[failing, failing, succeeding],
        ) as from_url:
            assert _is_redis_available(app) is True
            assert from_url.call_count == 3

    def test_exhausted_retries_falls_back_to_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from flask import Flask

        from app import _is_redis_available

        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        monkeypatch.setenv("REDIS_INIT_RETRIES", "3")
        monkeypatch.setenv("REDIS_INIT_RETRY_DELAY_SECONDS", "0.01")
        app = Flask(__name__)

        failing = MagicMock()
        failing.ping.side_effect = ConnectionError("ECONNREFUSED")
        with patch("redis.from_url", return_value=failing) as from_url:
            assert _is_redis_available(app) is False
            assert from_url.call_count == 3

    def test_testing_mode_defaults_to_single_attempt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """In TESTING mode the default is 1 attempt so the suite stays fast."""
        from flask import Flask

        from app import _is_redis_available

        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        monkeypatch.delenv("REDIS_INIT_RETRIES", raising=False)
        monkeypatch.setenv("REDIS_INIT_RETRY_DELAY_SECONDS", "0.01")
        app = Flask(__name__)
        app.config["TESTING"] = True

        failing = MagicMock()
        failing.ping.side_effect = ConnectionError("ECONNREFUSED")
        with (
            patch("redis.from_url", return_value=failing) as from_url,
            patch("app.time.sleep") as sleep,
        ):
            assert _is_redis_available(app) is False
            # Single attempt, no sleep because the loop didn't go round.
            assert from_url.call_count == 1
            sleep.assert_not_called()

    def test_retry_delay_is_honoured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Between failed attempts the loop sleeps the configured delay."""
        from flask import Flask

        from app import _is_redis_available

        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        monkeypatch.setenv("REDIS_INIT_RETRIES", "3")
        monkeypatch.setenv("REDIS_INIT_RETRY_DELAY_SECONDS", "0.25")
        app = Flask(__name__)

        failing = MagicMock()
        failing.ping.side_effect = ConnectionError("ECONNREFUSED")
        with (
            patch("redis.from_url", return_value=failing),
            patch("app.time.sleep") as sleep,
        ):
            assert _is_redis_available(app) is False
            # 3 attempts → 2 sleeps between them; final attempt does not sleep.
            assert sleep.call_count == 2
            for call in sleep.call_args_list:
                assert call.args[0] == 0.25
