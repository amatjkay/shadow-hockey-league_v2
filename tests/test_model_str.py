"""Regression tests for ORM ``__str__`` representations (TIK-79).

Flask-Admin renders relationship columns and FK select dropdowns by calling
``str(obj)`` on the related row. Without an explicit ``__str__`` method the
default ``__repr__`` (``<Manager Felix>``, ``<Achievement 1/1/2>``, …) leaks
into the admin UI and the human reading the audit log sees the technical
debug form instead of a clean human-readable label.

These tests pin the human-readable contract for every ORM model that can
appear in an admin list, dropdown, or audit log target field.
"""

from __future__ import annotations

import pytest

from models import (
    Achievement,
    AchievementType,
    Country,
    League,
    Manager,
    Season,
    db,
)


@pytest.fixture
def reference_rows(app, db_session):
    """Persisted reference rows used across the str-rendering assertions."""

    country = Country(code="RUS", name="Россия", flag_path="/static/img/flags/rus.png")
    db.session.add(country)
    db.session.flush()

    manager = Manager(name="Феликс", country_id=country.id)
    tandem = Manager(name="Tandem: Иванов, Петров", country_id=country.id)
    db.session.add_all([manager, tandem])
    db.session.flush()

    ach_type = AchievementType(
        code="TOP1",
        name="Top 1",
        base_points_l1=800,
        base_points_l2=400,
        icon_path="/static/img/cups/top1.svg",
    )
    league_root = League(code="2", name="League 2")
    db.session.add_all([ach_type, league_root])
    db.session.flush()

    sub_league = League(code="2.1", name="League 2.1", parent_code="2")
    season = Season(code="25/26", name="Season 25/26", multiplier=1.0, is_active=True)
    db.session.add_all([sub_league, season])
    db.session.commit()

    return {
        "country": country,
        "manager": manager,
        "tandem": tandem,
        "type": ach_type,
        "league_root": league_root,
        "sub_league": sub_league,
        "season": season,
    }


def test_country_str_returns_name(reference_rows):
    assert str(reference_rows["country"]) == "Россия"


def test_manager_str_returns_display_name(reference_rows):
    assert str(reference_rows["manager"]) == "Феликс"


def test_manager_str_strips_tandem_prefix(reference_rows):
    """``__str__`` mirrors ``display_name`` so tandem rows lose the prefix."""

    assert str(reference_rows["tandem"]) == "Иванов, Петров"


def test_achievement_type_str_returns_name(reference_rows):
    assert str(reference_rows["type"]) == "Top 1"


def test_league_str_root_returns_name(reference_rows):
    """Root leagues (no parent_code) just return the human name."""

    assert str(reference_rows["league_root"]) == "League 2"


def test_league_str_subleague_includes_code(reference_rows):
    """Subleagues append their canonical code so ``2.1`` and ``2.2`` are
    distinguishable in admin dropdowns."""

    assert str(reference_rows["sub_league"]) == "League 2.1 (2.1)"


def test_season_str_returns_name(reference_rows):
    assert str(reference_rows["season"]) == "Season 25/26"


def test_achievement_str_full_relationships(reference_rows):
    """When all relationships are loaded, the string is a self-contained
    description that reads naturally in audit logs and admin lists."""

    achievement = Achievement(
        manager_id=reference_rows["manager"].id,
        type_id=reference_rows["type"].id,
        league_id=reference_rows["sub_league"].id,
        season_id=reference_rows["season"].id,
        title="Top 1",
        icon_path="/static/img/cups/top1.svg",
        base_points=800.0,
        multiplier=1.0,
        final_points=800.0,
    )
    db.session.add(achievement)
    db.session.commit()

    rendered = str(achievement)
    assert rendered == "Феликс — Top 1 (League 2.1, Season 25/26)"
    assert "<Achievement" not in rendered
    assert "/" not in rendered.split("Season")[0]  # no raw id triplets like 1/1/2


def test_achievement_str_no_repr_leakage_in_unsaved_state():
    """Unsaved achievements never leak ``<Achievement …/…/…>`` into the UI."""

    bare = Achievement(
        manager_id=None,
        type_id=None,
        league_id=None,
        season_id=None,
        title="",
        icon_path="",
        base_points=0.0,
        multiplier=0.0,
        final_points=0.0,
    )
    rendered = str(bare)
    assert rendered.startswith("Achievement")
    assert "<" not in rendered  # plain text, not an HTML-ish repr
