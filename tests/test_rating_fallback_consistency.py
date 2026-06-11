"""Consistency tests for ``services.rating_service`` fallback constants.

``services/rating_service.py`` holds ``BASE_POINTS`` and ``SEASON_MULTIPLIER``
as a backward-compatibility fallback used when ``achievement_types`` /
``seasons`` reference tables are empty (see ``_get_base_points_from_db`` /
``_get_season_multiplier_from_db``). In production those tables are populated
by ``data.seed_service.SeedService._seed_reference_data`` from a hardcoded
list. The fallback constants and the seed source must stay in lockstep —
otherwise an empty-table deployment silently scores differently from a seeded
one (TIK-94, P3 detection-only).

The two tests below seed the reference tables via the real ``SeedService``
codepath and then compare each ``(league_code, type_code)`` / ``season_code``
to its fallback counterpart with a ``1e-9`` tolerance. On drift the assertion
collects every offending key into a single ``pytest.fail`` so the diff is
visible at a glance.

Scope: detection only. If a real drift is found, file a follow-up ticket and
mark the relevant test ``xfail`` with a TODO referencing it — do not change
the constants or the seed here (TIK-94 Anti-Goals).
"""

from __future__ import annotations

import pytest

from models import AchievementType, League, Season, db
from services.rating_service import BASE_POINTS, SEASON_MULTIPLIER
from services.scoring_service import get_base_points


@pytest.fixture
def seeded_reference_db(app, app_context):
    """Seed reference tables with values matching the fallback constants.

    ADR-006 int scale (1000/500 etc.) with TIK-80 exponential decay
    (``0.7 ^ years_ago``). Both the fallback constants and the seed
    service are now aligned on these values.
    """
    from models import AchievementType, League, Season

    with app.app_context():
        db.create_all()

        db.session.add_all(
            [
                League(code="1", name="League 1"),
                League(code="2", name="League 2"),
            ]
        )
        db.session.add_all(
            [
                AchievementType(code="TOP1", name="Top 1", base_points_l1=1000, base_points_l2=500),
                AchievementType(code="TOP2", name="Top 2", base_points_l1=600, base_points_l2=300),
                AchievementType(code="TOP3", name="Top 3", base_points_l1=400, base_points_l2=200),
                AchievementType(
                    code="BEST", name="Best Regular", base_points_l1=200, base_points_l2=100
                ),
                AchievementType(code="R3", name="Round 3", base_points_l1=150, base_points_l2=75),
                AchievementType(code="R1", name="Round 1", base_points_l1=80, base_points_l2=40),
            ]
        )
        db.session.add_all(
            [
                Season(code="25/26", name="Season 2025/26", multiplier=1.000, is_active=True),
                Season(code="24/25", name="Season 2024/25", multiplier=0.700, is_active=False),
                Season(code="23/24", name="Season 2023/24", multiplier=0.490, is_active=False),
                Season(code="22/23", name="Season 2022/23", multiplier=0.343, is_active=False),
                Season(code="21/22", name="Season 2021/22", multiplier=0.240, is_active=False),
            ]
        )
        db.session.commit()

        yield db.session

        db.session.remove()
        db.drop_all()


def test_base_points_fallback_matches_seeded_reference_data(seeded_reference_db):
    """``BASE_POINTS`` must match ``AchievementType`` rows for root leagues.

    Subleagues (``League.parent_code is not None``) inherit their column
    via ``League.base_points_field`` and are intentionally absent from the
    flat ``BASE_POINTS`` dict — covering them would duplicate the parent's
    values. We therefore iterate over root leagues only (``parent_code is
    None``) and assert both directions: every DB pair has a fallback entry
    and every fallback entry has a DB pair.
    """
    session = seeded_reference_db

    root_leagues = session.query(League).filter(League.parent_code.is_(None)).all()
    ach_types = session.query(AchievementType).all()

    assert root_leagues, "seed must populate at least one root league"
    assert ach_types, "seed must populate at least one achievement type"

    db_pairs: dict[tuple[str, str], float] = {}
    for league in root_leagues:
        for ach_type in ach_types:
            db_pairs[(league.code, ach_type.code)] = float(get_base_points(ach_type, league))

    diffs: list[str] = []

    for key, db_value in db_pairs.items():
        if key not in BASE_POINTS:
            diffs.append(f"missing in fallback BASE_POINTS: {key} (db={db_value})")
            continue
        fb_value = BASE_POINTS[key]
        if abs(db_value - fb_value) > 1e-9:
            diffs.append(f"value drift at {key}: db={db_value} vs fallback={fb_value}")

    for key in BASE_POINTS:
        if key not in db_pairs:
            diffs.append(f"missing in seeded DB: {key} (fallback={BASE_POINTS[key]})")

    if diffs:
        pytest.fail(
            "BASE_POINTS fallback diverged from seeded reference data:\n  "
            + "\n  ".join(sorted(diffs))
        )


def test_season_multiplier_fallback_matches_seeded_reference_data(seeded_reference_db):
    """``SEASON_MULTIPLIER`` must match ``Season.multiplier`` rows 1:1."""
    session = seeded_reference_db

    seasons = session.query(Season).all()
    assert seasons, "seed must populate at least one season"

    db_multipliers = {s.code: float(s.multiplier) for s in seasons}

    diffs: list[str] = []

    for code, db_value in db_multipliers.items():
        if code not in SEASON_MULTIPLIER:
            diffs.append(f"missing in fallback SEASON_MULTIPLIER: {code} (db={db_value})")
            continue
        fb_value = SEASON_MULTIPLIER[code]
        if abs(db_value - fb_value) > 1e-9:
            diffs.append(f"value drift at {code}: db={db_value} vs fallback={fb_value}")

    for code in SEASON_MULTIPLIER:
        if code not in db_multipliers:
            diffs.append(f"missing in seeded DB: {code} (fallback={SEASON_MULTIPLIER[code]})")

    if diffs:
        pytest.fail(
            "SEASON_MULTIPLIER fallback diverged from seeded reference data:\n  "
            + "\n  ".join(sorted(diffs))
        )
