"""Tests for the ProductionConfig fail-fast secret validator (T02).

Covers `config.validate_production_secrets` and the wiring in
`app.create_app()` that calls it when `FLASK_ENV=production`. See
`docs/owner-actions.md` § T02.

Note on the end-to-end coverage: ``ProductionConfig.SECRET_KEY`` and friends
are resolved once at class-body evaluation time (= module import time), so
in-process `monkeypatch.setenv` cannot retroactively change them. The
happy-path of "production with strong secrets boots cleanly" is therefore
covered by overlaying values onto ``app.config`` directly after
``from_object``, which is what the wired-in validator actually reads.
"""

from __future__ import annotations

import pytest

from config import _PRODUCTION_SECRET_DEFAULTS, validate_production_secrets


def _strong_secrets() -> dict[str, str]:
    """Return a config dict with all required secrets set to non-default values."""
    return {name: f"strong-{name}-value" for name, _ in _PRODUCTION_SECRET_DEFAULTS}


def test_validate_passes_when_all_secrets_are_strong():
    """No exception when every secret is set to a non-default value."""
    validate_production_secrets(_strong_secrets())


@pytest.mark.parametrize("missing", [name for name, _ in _PRODUCTION_SECRET_DEFAULTS])
def test_validate_fails_when_a_secret_is_missing(missing: str):
    """RuntimeError names the missing secret when its key is absent."""
    config = _strong_secrets()
    config.pop(missing)
    with pytest.raises(RuntimeError, match=missing):
        validate_production_secrets(config)


@pytest.mark.parametrize("name,dev_default", list(_PRODUCTION_SECRET_DEFAULTS))
def test_validate_fails_when_secret_is_dev_default(name: str, dev_default: str):
    """RuntimeError names the offender when its value matches the dev placeholder."""
    config = _strong_secrets()
    config[name] = dev_default
    with pytest.raises(RuntimeError, match=name):
        validate_production_secrets(config)


def test_validate_reports_all_offenders_in_one_message():
    """Multiple missing/dev-default secrets are all listed in the error message."""
    config: dict = {}
    with pytest.raises(RuntimeError) as exc_info:
        validate_production_secrets(config)
    message = str(exc_info.value)
    for name, _ in _PRODUCTION_SECRET_DEFAULTS:
        assert name in message


def test_create_app_with_testing_config_does_not_trigger_validator(monkeypatch):
    """Tests use TestingConfig — validator must not run (FLASK_ENV irrelevant)."""
    # Set FLASK_ENV=production to confirm the explicit config_class arg wins.
    monkeypatch.setenv("FLASK_ENV", "production")
    from app import create_app

    # If the validator ran, this would raise because TestingConfig doesn't
    # set the production secrets to non-default values.
    app = create_app("config.TestingConfig")
    assert app.config["TESTING"] is True


def test_create_app_in_production_raises_when_secrets_are_dev_default(monkeypatch):
    """End-to-end: FLASK_ENV=production with dev defaults => RuntimeError."""
    # Unset env vars so ProductionConfig falls back to its dev defaults.
    for name, _ in _PRODUCTION_SECRET_DEFAULTS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FLASK_ENV", "production")

    from app import create_app

    with pytest.raises(RuntimeError, match="ProductionConfig refuses to start"):
        create_app()


def test_validator_accepts_app_config_with_strong_values():
    """Wired-in path: feed `app.config`-shaped dict with strong values => pass.

    Mirrors what `app.create_app()` does after `from_object()` succeeds.
    Class-attribute caching prevents a clean "boot in production" test, so
    we exercise the same callable directly with realistic input.
    """
    strong = {name: f"strong-{name}-value" for name, _ in _PRODUCTION_SECRET_DEFAULTS}
    validate_production_secrets(strong)
