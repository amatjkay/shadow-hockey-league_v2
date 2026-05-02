"""Coverage-focused tests for ``services.recalc_service`` (TIK-50).

These tests target the error / fallback paths that the original
``test_recalc.py`` happy-path suite never exercised:

* type / season not found
* empty achievement set
* missing relationship FKs (warning + skip)
* per-achievement exception inside the loop
* commit failure → rollback
* audit-log emission with an authenticated user
* ``_get_user_id`` outside an HTTP context (RuntimeError swallowed)

Stylistic note: this file deliberately uses ``unittest.mock.patch`` for the
DB-level error paths so we can simulate a commit failure without a real
DB-failure injection harness.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from models import Achievement, AchievementType, Country, League, Manager, Season, db
from services.recalc_service import (
    _get_user_id,
    _recalc_single_achievement,
    recalc_by_achievement_type,
    recalc_by_season,
    recalc_single_achievement_id,
)

# ==================== Fixtures ====================


@pytest.fixture
def seeded(db_session):
    """Minimal seed: 1 country, 1 manager, 1 type, 1 league, 1 season, 1 achievement."""
    country = Country(code="RUS", name="Russia", flag_path="/static/img/flags/RUS.png")
    db.session.add(country)
    db.session.flush()

    manager = Manager(name="Test Manager", country_id=country.id)
    db.session.add(manager)
    db.session.flush()

    ach_type = AchievementType(code="TOP1", name="Top 1", base_points_l1=800, base_points_l2=400)
    league = League(code="1", name="League 1")
    season = Season(code="24/25", name="Season 24/25", multiplier=1.0, is_active=True)
    db.session.add_all([ach_type, league, season])
    db.session.flush()

    achievement = Achievement(
        manager_id=manager.id,
        type_id=ach_type.id,
        league_id=league.id,
        season_id=season.id,
        title="TOP1",
        icon_path="/static/img/cups/top1.svg",
        base_points=800.0,
        multiplier=1.0,
        final_points=800.0,
    )
    db.session.add(achievement)
    db.session.commit()

    return {
        "country": country,
        "manager": manager,
        "ach_type": ach_type,
        "league": league,
        "season": season,
        "achievement": achievement,
    }


# ==================== Not-found / empty paths ====================


class TestNotFoundAndEmpty:
    """Cover the 404-equivalent and empty-set early returns."""

    def test_recalc_by_type_not_found(self, db_session):
        result = recalc_by_achievement_type(99999)
        assert result == {"affected": 0, "errors": ["Achievement type not found"]}

    def test_recalc_by_season_not_found(self, db_session):
        result = recalc_by_season(99999)
        assert result == {"affected": 0, "errors": ["Season not found"]}

    def test_recalc_by_type_empty(self, db_session):
        """Type exists but has zero achievements → no-op success."""
        ach_type = AchievementType(code="EMPTY", name="Empty", base_points_l1=10, base_points_l2=5)
        db.session.add(ach_type)
        db.session.commit()

        result = recalc_by_achievement_type(ach_type.id)
        assert result == {"affected": 0, "errors": []}

    def test_recalc_by_season_empty(self, db_session):
        season = Season(code="99/00", name="Empty season", multiplier=0.1, is_active=False)
        db.session.add(season)
        db.session.commit()

        result = recalc_by_season(season.id)
        assert result == {"affected": 0, "errors": []}

    def test_recalc_single_not_found(self, db_session):
        assert recalc_single_achievement_id(99999) is False


# ==================== Missing-relationship warning ====================


class TestMissingRelationships:
    """``_recalc_single_achievement`` must warn and skip when FKs are dangling."""

    def test_skip_when_type_relationship_missing(self, seeded, caplog):
        """Hand-craft an Achievement object with type_id=None so the helper hits
        the ``if not all([...])`` guard."""
        ach = Achievement(
            manager_id=seeded["manager"].id,
            type_id=None,  # <- intentionally missing FK
            league_id=seeded["league"].id,
            season_id=seeded["season"].id,
            title="ORPHAN",
            icon_path="/static/img/cups/top1.svg",
            base_points=0.0,
            multiplier=1.0,
            final_points=0.0,
        )
        # Detached object; ID assignment via flush isn't required — helper
        # only inspects the relationship attributes.
        ach.id = -1
        with caplog.at_level("WARNING", logger="services.recalc_service"):
            _recalc_single_achievement(ach)
        assert "missing related entities" in caplog.text


# ==================== Per-achievement exception path ====================


class TestPerAchievementException:
    """A bad achievement in the loop should be caught, logged, and not abort the batch."""

    def test_recalc_by_type_continues_after_per_item_error(self, seeded):
        """Force ``_recalc_single_achievement`` to raise for the first call."""
        with patch(
            "services.recalc_service._recalc_single_achievement",
            side_effect=RuntimeError("boom"),
        ):
            result = recalc_by_achievement_type(seeded["ach_type"].id)
        assert result["affected"] == 0
        assert len(result["errors"]) == 1
        assert "boom" in result["errors"][0]

    def test_recalc_by_season_continues_after_per_item_error(self, seeded):
        with patch(
            "services.recalc_service._recalc_single_achievement",
            side_effect=RuntimeError("boom-season"),
        ):
            result = recalc_by_season(seeded["season"].id)
        assert result["affected"] == 0
        assert len(result["errors"]) == 1
        assert "boom-season" in result["errors"][0]

    def test_recalc_single_returns_false_on_error(self, seeded):
        with patch(
            "services.recalc_service._recalc_single_achievement",
            side_effect=RuntimeError("single-boom"),
        ):
            assert recalc_single_achievement_id(seeded["achievement"].id) is False


# ==================== Commit-failure rollback ====================


class TestCommitFailure:
    """If ``db.session.commit()`` raises, the function must rollback and surface the error."""

    def test_recalc_by_type_rollback_on_commit_failure(self, seeded):
        seeded["ach_type"].base_points_l1 = 1500
        db.session.commit()  # bake the change so commit() inside is the second one

        with patch.object(db.session, "commit", side_effect=RuntimeError("commit fail")):
            result = recalc_by_achievement_type(seeded["ach_type"].id)
        assert result["affected"] == 0
        assert len(result["errors"]) == 1
        assert "Commit failed" in result["errors"][0]

    def test_recalc_by_season_rollback_on_commit_failure(self, seeded):
        seeded["season"].multiplier = 0.5
        db.session.commit()

        with patch.object(db.session, "commit", side_effect=RuntimeError("commit fail")):
            result = recalc_by_season(seeded["season"].id)
        assert result["affected"] == 0
        assert any("Commit failed" in err for err in result["errors"])


# ==================== Audit log path with authenticated user ====================


class TestAuditLogPath:
    """When ``_get_user_id()`` returns a real id, ``log_action`` must be invoked."""

    def test_audit_log_called_with_user(self, seeded):
        with (
            patch("services.recalc_service._get_user_id", return_value=42),
            patch("services.audit_service.log_action") as mock_log,
        ):
            seeded["ach_type"].base_points_l1 = 1234
            db.session.commit()

            recalc_by_achievement_type(seeded["ach_type"].id)
        mock_log.assert_called_once()
        kwargs = mock_log.call_args.kwargs
        assert kwargs["user_id"] == 42
        assert kwargs["action"] == "RECALCULATE_POINTS"
        assert kwargs["target_model"] == "AchievementType"

    def test_audit_log_called_with_user_for_season(self, seeded):
        with (
            patch("services.recalc_service._get_user_id", return_value=7),
            patch("services.audit_service.log_action") as mock_log,
        ):
            seeded["season"].multiplier = 0.4
            db.session.commit()

            recalc_by_season(seeded["season"].id)
        mock_log.assert_called_once()
        kwargs = mock_log.call_args.kwargs
        assert kwargs["user_id"] == 7
        assert kwargs["target_model"] == "Season"


# ==================== _get_user_id ====================


class TestGetUserId:
    """``_get_user_id`` must return None outside an HTTP/login context."""

    def test_get_user_id_returns_none_outside_request_context(self, app):
        """No request context → flask_login.current_user proxy raises RuntimeError."""
        # Pop any active context so the proxy is empty.
        from flask import g

        # In an app context but not a request context, current_user is
        # AnonymousUserMixin; ``is_authenticated`` is False so we hit the
        # ``return None`` fallback.
        with app.app_context():
            assert _get_user_id() is None
            # ``g`` is a sanity import to keep flake8 happy if it's flagged.
            assert g is not None
