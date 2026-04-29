"""Unit tests for ``services.scoring_service.get_base_points``.

The helper is the single source of truth for picking
``base_points_l1`` vs ``base_points_l2`` from an ``AchievementType``. It must
honour ``League.parent_code`` so that subleagues inherit their parent's
points field — the bug this PR fixes is exactly the case where callers were
using ``league.code == '1'`` directly and miscounted future subleagues.
"""

from __future__ import annotations

import unittest

from app import create_app
from models import AchievementType, League, db
from services.scoring_service import get_base_points


class TestGetBasePoints(unittest.TestCase):
    """Verify ``get_base_points`` honours the league hierarchy."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.ach_type = AchievementType(
            code="TOP1",
            name="Top 1",
            base_points_l1=800,
            base_points_l2=300,
        )
        db.session.add(self.ach_type)

        self.league_l1 = League(code="1", name="League 1", is_active=True)
        self.league_l2 = League(code="2", name="League 2", is_active=True)
        db.session.add_all([self.league_l1, self.league_l2])
        db.session.flush()

        # Subleagues 2.1 / 2.2 with parent_code='2'
        self.league_l2_1 = League(code="2.1", name="League 2.1", parent_code="2", is_active=True)
        self.league_l2_2 = League(code="2.2", name="League 2.2", parent_code="2", is_active=True)
        db.session.add_all([self.league_l2_1, self.league_l2_2])
        db.session.commit()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_l1_returns_base_points_l1(self) -> None:
        self.assertEqual(get_base_points(self.ach_type, self.league_l1), 800.0)

    def test_l2_returns_base_points_l2(self) -> None:
        self.assertEqual(get_base_points(self.ach_type, self.league_l2), 300.0)

    def test_subleague_inherits_parent_field(self) -> None:
        """``2.1`` and ``2.2`` must resolve to ``base_points_l2`` via parent_code.

        This is the regression test for the original bug: callers comparing
        ``league.code == '1'`` would route '2.1' to ``base_points_l2`` only
        by accident, and a hypothetical L1 subleague would silently flip to
        ``base_points_l2`` (wrong). Going through ``League.base_points_field``
        is the only league-aware path.
        """
        self.assertEqual(get_base_points(self.ach_type, self.league_l2_1), 300.0)
        self.assertEqual(get_base_points(self.ach_type, self.league_l2_2), 300.0)

    def test_returns_float(self) -> None:
        """Helper must return ``float`` even when DB column stores ``Integer``."""
        result = get_base_points(self.ach_type, self.league_l1)
        self.assertIsInstance(result, float)


if __name__ == "__main__":
    unittest.main()
