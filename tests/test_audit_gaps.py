"""Gap-fill regression tests surfaced by Phase E of the post-audit testing campaign.

These tests cover invariants that the post-audit-2026-04-28 modules introduced but
were not previously exercised directly:

* **F-6** — `services/extensions.limiter` is supposed to bind through ``init_app``
  with a Redis storage URI when ``REDIS_URL`` is reachable, falling back to
  ``memory://`` otherwise. Existing API-level tests only exercise the limiter
  indirectly via 429 responses; this file pins the configuration plumbing so a
  silent regression cannot revert the storage choice.
* **F-7** — ``services.scoring_service.get_base_points`` must route every league
  through ``League.base_points_field``. The pre-PR-#35 code branched on
  ``league.code == '1'`` directly. Ensuring the helper resolves correctly for
  ``1``, ``2``, ``2.1``, ``2.2``, ``3``, ``3.1`` (and a hypothetical L1 subleague
  ``1.1``) locks the parent_code-based contract.
"""

from __future__ import annotations

import pytest

from app import create_app
from models import AchievementType, League, db
from services.scoring_service import get_base_points


# ---------------------------------------------------------------------------
# F-6 — extensions.limiter wiring
# ---------------------------------------------------------------------------


class TestLimiterInitApp:
    """Verify the shared `Limiter` is wired through `init_app` correctly."""

    def test_limiter_attached_to_app_extensions(self) -> None:
        """`init_app` must register the limiter under `app.extensions['limiter']` when enabled.

        Flask-Limiter 4.x's ``init_app`` returns early when ``RATELIMIT_ENABLED``
        is False, so we must opt in explicitly via a config override.
        """
        app = create_app("config.TestingConfig")
        # Opt in to limiter registration for this assertion.
        app.config["RATELIMIT_ENABLED"] = True
        from services.extensions import limiter as shared_limiter

        shared_limiter.init_app(app)
        assert "limiter" in app.extensions, (
            "Flask-Limiter not registered on app.extensions — init_app "
            "likely failed or was overridden by a second instance."
        )

    def test_testing_config_uses_memory_storage(self) -> None:
        """Under `TESTING=True`, storage must be `memory://` to keep tests fast."""
        app = create_app("config.TestingConfig")
        assert app.config["RATELIMIT_STORAGE_URI"] == "memory://"

    def test_testing_config_disables_rate_limiting(self) -> None:
        """Under `TESTING=True`, `RATELIMIT_ENABLED` defaults to `False`.

        Tests that explicitly opt in (e.g. ``TestAPIRateLimiting``) override
        this via a config subclass; the default must keep the suite fast and
        avoid spurious 429s."""
        app = create_app("config.TestingConfig")
        assert app.config["RATELIMIT_ENABLED"] is False


# ---------------------------------------------------------------------------
# F-7 — get_base_points must always go through League.base_points_field
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def scoring_app():
    """Provide a TestingConfig app with reference data seeded for scoring."""
    app = create_app("config.TestingConfig")
    ctx = app.app_context()
    ctx.push()
    db.create_all()

    ach_type = AchievementType(
        code="TOP1",
        name="Top 1",
        base_points_l1=800,
        base_points_l2=300,
    )
    db.session.add(ach_type)

    leagues = [
        League(code="1", name="L1", is_active=True),
        League(code="2", name="L2", is_active=True),
        League(code="3", name="L3", is_active=True),
        League(code="1.1", name="L1.1", parent_code="1", is_active=True),
        League(code="2.1", name="L2.1", parent_code="2", is_active=True),
        League(code="2.2", name="L2.2", parent_code="2", is_active=True),
        League(code="3.1", name="L3.1", parent_code="3", is_active=True),
    ]
    db.session.add_all(leagues)
    db.session.commit()

    yield app, ach_type, {league.code: league for league in leagues}

    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.mark.parametrize(
    "league_code, expected_points",
    [
        # League "1" routes to base_points_l1 (the only L1 root).
        ("1", 800.0),
        # Hypothetical subleague "1.1" — must inherit parent's L1 column.
        ("1.1", 800.0),
        # League "2" and its subleagues — base_points_l2.
        ("2", 300.0),
        ("2.1", 300.0),
        ("2.2", 300.0),
        # League "3" — non-L1, so base_points_l2 (the current behaviour
        # documented in `audit-2026-04-28-analysis.md` §1.3).
        ("3", 300.0),
        ("3.1", 300.0),
    ],
)
def test_get_base_points_routes_via_league_base_points_field(
    scoring_app, league_code, expected_points
) -> None:
    """`get_base_points` must use `League.base_points_field` for every league.

    This is the regression test for the bug fixed in PR #35: callers comparing
    ``league.code == '1'`` would route ``1.1`` (a hypothetical L1 subleague)
    to ``base_points_l2``. Any future code that re-introduces a ``code == '1'``
    branch will fail this test on the ``1.1`` row.
    """
    _, ach_type, leagues = scoring_app
    league = leagues[league_code]
    assert get_base_points(ach_type, league) == expected_points
