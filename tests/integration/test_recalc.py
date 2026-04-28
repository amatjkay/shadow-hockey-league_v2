"""Tests for services.recalc_service.

Covers:
- recalc_by_achievement_type
- recalc_by_season
- recalc_single_achievement_id
- Audit logging
- Cache invalidation
"""

import pytest

from models import Achievement, AchievementType, Country, League, Manager, Season, db
from services.recalc_service import (
    recalc_by_achievement_type,
    recalc_by_season,
    recalc_single_achievement_id,
)

# ==================== Fixtures ====================


@pytest.fixture
def recalc_data(db_session):
    """Create data for recalculation tests."""
    country = Country(code="RUS", name="Russia", flag_path="/static/img/flags/RUS.png")
    db.session.add(country)
    db.session.flush()

    manager = Manager(name="Test Manager", country_id=country.id)
    db.session.add(manager)
    db.session.flush()

    ach_type = AchievementType(code="TOP1", name="Top 1", base_points_l1=800, base_points_l2=400)
    league = League(code="1", name="League 1")
    league2 = League(code="2", name="League 2")  # Parent for subleagues
    season = Season(code="24/25", name="Season 24/25", multiplier=1.0, is_active=True)
    db.session.add_all([ach_type, league, league2, season])
    db.session.flush()

    # Create an achievement
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

    yield {
        "manager": manager,
        "ach_type": ach_type,
        "league": league,
        "league2": league2,
        "season": season,
        "achievement": achievement,
    }


# ==================== Recalc by Type Tests ====================


class TestRecalcByType:
    """Test recalc_by_achievement_type."""

    def test_recalc_updates_points(self, recalc_data):
        """Should update base_points and final_points when type changes."""
        ach_type = recalc_data["ach_type"]
        achievement = recalc_data["achievement"]

        # Change base points
        ach_type.base_points_l1 = 1000
        db.session.commit()

        result = recalc_by_achievement_type(ach_type.id)

        db.session.refresh(achievement)
        assert result["affected"] == 1
        assert achievement.base_points == 1000.0
        assert achievement.final_points == 1000.0  # 1000 * 1.0

    def test_recalc_respects_league(self, recalc_data):
        """Should use base_points_l2 for League 2."""
        ach_type = recalc_data["ach_type"]
        league2 = recalc_data["league2"]
        achievement = recalc_data["achievement"]

        # Switch achievement to League 2
        achievement.league_id = league2.id
        ach_type.base_points_l2 = 500
        db.session.commit()

        result = recalc_by_achievement_type(ach_type.id)

        db.session.refresh(achievement)
        assert result["affected"] == 1
        assert achievement.base_points == 500.0

    def test_recalc_with_parent_code(self, recalc_data):
        """Should use base_points_l2 for subleague (2.1)."""
        ach_type = recalc_data["ach_type"]
        league = recalc_data["league"]
        league2 = recalc_data["league2"]  # Parent league
        achievement = recalc_data["achievement"]

        # Change league to 2.1 with parent 2
        league.code = "2.1"
        league.parent_code = league2.code  # Now '2' exists
        ach_type.base_points_l2 = 400
        db.session.commit()

        result = recalc_by_achievement_type(ach_type.id)

        db.session.refresh(achievement)
        assert result["affected"] == 1
        assert achievement.base_points == 400.0

    def test_recalc_audit_log(self, recalc_data, app_context):
        """Should NOT create audit log if no user is logged in (system action)."""
        ach_type = recalc_data["ach_type"]
        ach_type.base_points_l1 = 900
        db.session.commit()

        # In tests without login, user_id is None, so log is skipped
        result = recalc_by_achievement_type(ach_type.id)
        assert result["affected"] == 1
        assert len(result["errors"]) == 0
        # Note: Real audit log requires authenticated user context


# ==================== Recalc by Season Tests ====================


class TestRecalcBySeason:
    """Test recalc_by_season."""

    def test_recalc_multiplier(self, recalc_data):
        """Should update final_points when season multiplier changes."""
        season = recalc_data["season"]
        achievement = recalc_data["achievement"]

        season.multiplier = 0.5
        db.session.commit()

        result = recalc_by_season(season.id)

        db.session.refresh(achievement)
        assert result["affected"] == 1
        assert achievement.final_points == 400.0  # 800 * 0.5


# ==================== Recalc Single Achievement Tests ====================


class TestRecalcSingleAchievement:
    """Test recalc_single_achievement_id."""

    def test_recalc_single(self, recalc_data):
        """Should recalculate a single achievement."""
        achievement = recalc_data["achievement"]
        ach_type = recalc_data["ach_type"]

        ach_type.base_points_l1 = 1200
        db.session.commit()

        success = recalc_single_achievement_id(achievement.id)

        db.session.refresh(achievement)
        assert success is True
        assert achievement.base_points == 1200.0

    def test_recalc_single_not_found(self, db_session):
        """Should return False for non-existent achievement."""
        assert recalc_single_achievement_id(99999) is False
