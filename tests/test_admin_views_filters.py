"""Regression tests for admin view filters / search / bulk actions (TIK-80).

These tests pin the contract added in the admin polish round:

* every list view exposes a non-empty ``column_searchable_list`` and
  ``column_filters`` so the user can drill down without scrolling through
  hundreds of rows;
* the achievement view, in particular, must expose every FK relation in
  both the search bar and the sidebar, plus a bulk ``recalculate_points``
  action that re-applies scoring to the selected rows.

The tests live at the unit level — they only inspect class attributes and
the ``@action`` registry, no DB / HTTP round-trips needed. That keeps the
suite fast and the contract explicit: anyone removing a filter / search
column will have to update the corresponding test, which surfaces the
intent in the PR diff.
"""

from __future__ import annotations

from typing import Any

from services.admin.views import (
    AchievementModelView,
    AchievementTypeModelView,
    CountryModelView,
    LeagueModelView,
    ManagerModelView,
    SeasonModelView,
)


def _attr_set(view_cls: type, attr: str) -> set[str]:
    """Return ``getattr(view_cls, attr)`` as a set of strings.

    Flask-Admin accepts column names as either bare strings or relation
    references (``Model.column``); the polish PR uses bare strings so we
    can do a simple set-membership check.
    """

    raw = getattr(view_cls, attr, None) or ()
    return {str(item) for item in raw}


class TestSearchContract:
    """Every list view must expose a non-trivial ``column_searchable_list``."""

    def test_manager_search_includes_country(self) -> None:
        cols = _attr_set(ManagerModelView, "column_searchable_list")
        # Searching by manager name was the original behaviour; TIK-80 adds
        # cross-relation search so typing ``Russia`` finds every Russian
        # manager.
        assert "name" in cols
        assert "country.name" in cols
        assert "country.code" in cols

    def test_achievement_search_covers_all_fk_relations(self) -> None:
        cols = _attr_set(AchievementModelView, "column_searchable_list")
        # The four FK relations + the title column. Without these, the
        # search bar would have nothing to match against, since the
        # achievement table itself only stores numeric FKs.
        assert "manager.name" in cols
        assert "type.name" in cols
        assert "league.name" in cols
        assert "season.name" in cols
        assert "title" in cols

    def test_country_search_covers_code_and_name(self) -> None:
        cols = _attr_set(CountryModelView, "column_searchable_list")
        assert "code" in cols
        assert "name" in cols

    def test_achievement_type_search_covers_code_and_name(self) -> None:
        cols = _attr_set(AchievementTypeModelView, "column_searchable_list")
        assert "code" in cols
        assert "name" in cols

    def test_league_search_covers_code_name_parent(self) -> None:
        cols = _attr_set(LeagueModelView, "column_searchable_list")
        assert "code" in cols
        assert "name" in cols
        assert "parent_code" in cols

    def test_season_search_covers_code_and_name(self) -> None:
        cols = _attr_set(SeasonModelView, "column_searchable_list")
        assert "code" in cols
        assert "name" in cols


class TestFilterContract:
    """Every list view must expose a non-trivial ``column_filters``."""

    def test_manager_filters_include_country_and_active(self) -> None:
        cols = _attr_set(ManagerModelView, "column_filters")
        assert "country.name" in cols
        assert "is_active" in cols

    def test_achievement_filters_cover_fk_relations(self) -> None:
        cols = _attr_set(AchievementModelView, "column_filters")
        # The four FK filters at single-relation depth. We intentionally
        # do not include ``manager.country.name`` (3-level chain) because
        # Flask-Admin's ``tools.is_hybrid_property`` cannot traverse it.
        assert "type.name" in cols
        assert "league.name" in cols
        assert "season.code" in cols
        assert "manager.name" in cols

    def test_achievement_type_filters_include_active(self) -> None:
        cols = _attr_set(AchievementTypeModelView, "column_filters")
        assert "is_active" in cols

    def test_league_filters_include_active_and_parent(self) -> None:
        cols = _attr_set(LeagueModelView, "column_filters")
        assert "is_active" in cols
        assert "parent_code" in cols

    def test_season_filters_include_active_and_year(self) -> None:
        cols = _attr_set(SeasonModelView, "column_filters")
        assert "is_active" in cols
        assert "start_year" in cols


class TestDefaultSort:
    """Default sort order makes the most-recently-touched rows easy to find."""

    def test_manager_default_sort_by_name(self) -> None:
        # Tuple form: ``(column, descending)``.
        assert ManagerModelView.column_default_sort == ("name", False)

    def test_achievement_default_sort_by_updated_desc(self) -> None:
        # Most-recently-edited rows should float to the top of the list.
        assert AchievementModelView.column_default_sort == ("updated_at", True)


class TestBulkRecalculateAction:
    """``AchievementModelView`` exposes a ``recalculate_points`` bulk action."""

    def test_action_is_registered(self) -> None:
        # Flask-Admin's ``@action(name, label, confirmation)`` decorator
        # stores the metadata on the method itself as ``method._action``.
        # The view instance later picks it up in ``init_actions``. We
        # check at the class level so the test is fast and doesn't need
        # a DB session.
        method = getattr(AchievementModelView, "action_recalculate_points", None)
        assert method is not None, "bulk action method must exist on the class"

        action_meta = getattr(method, "_action", None)
        assert action_meta is not None, (
            "method must be decorated with @action so Flask-Admin "
            "registers it in the bulk-action dropdown"
        )
        # ``_action`` is a 2- or 3-tuple ``(name, label[, confirmation])``.
        assert action_meta[0] == "recalculate_points"

    def test_action_method_exists_and_is_callable(self) -> None:
        method = getattr(AchievementModelView, "action_recalculate_points", None)
        assert callable(method), (
            "action_recalculate_points must remain a callable bulk action; "
            "Flask-Admin invokes it as `self.action_recalculate_points(ids)`."
        )

    def test_action_iterates_recalc_helper(self, monkeypatch, app, app_context, db_session) -> None:
        """Smoke-test the bulk action against the canonical recalc helper.

        We monkey-patch ``recalc_single_achievement_id`` so the test does
        not need real achievements in the DB — we only assert that the
        bulk action calls the helper once per selected ID. Behaviour of
        the helper itself is covered by the recalc-service tests.
        """

        called_ids: list[int] = []

        def _fake_recalc(achievement_id: int) -> bool:
            called_ids.append(achievement_id)
            return True

        # The bulk action does a deferred import; patch the source module
        # so the patched symbol is what gets imported.
        monkeypatch.setattr(
            "services.recalc_service.recalc_single_achievement_id",
            _fake_recalc,
        )

        from models import Achievement

        view = AchievementModelView(Achievement, db_session)
        # Suppress the ``flash`` call which needs a request context we
        # don't have in this unit test.
        monkeypatch.setattr("services.admin.views.flash", lambda *_a, **_kw: None)
        # Suppress cache invalidation — it tries to talk to Redis.
        monkeypatch.setattr(
            "services.admin.views.invalidate_leaderboard_cache",
            lambda: None,
        )

        view.action_recalculate_points(["1", "2", "bad", "3"])

        # "bad" is silently skipped — non-int IDs are never passed to the
        # recalc helper. The remaining three are forwarded as ints.
        assert called_ids == [1, 2, 3]
