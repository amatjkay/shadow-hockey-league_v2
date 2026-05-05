"""Tests for the admin-observer guardrail (``data.admin_observers``).

Covers four surfaces:

1. Pure helpers — ``normalize`` / ``is_admin_observer`` /
   ``parse_tandem_members`` / ``tandem_observer_members``.
2. Allowlist loading from the JSON file (``load_explicit_tandems`` /
   ``is_explicit_tandem``).
3. The ``validate_manager_name`` decision matrix.
4. Integration via :class:`data.seed_service.SeedService` and
   :class:`services.admin.views.ManagerModelView` /
   :class:`services.admin.views.AchievementModelView`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from data.admin_observers import (
    ADMIN_OBSERVERS,
    is_admin_observer,
    is_explicit_tandem,
    load_explicit_tandems,
    normalize,
    parse_tandem_members,
    tandem_observer_members,
    validate_manager_name,
)

# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


class TestNormalize:
    def test_lowercases_and_trims(self) -> None:
        assert normalize("  AleX TiiKii  ") == "alex tiikii"

    def test_collapses_internal_whitespace(self) -> None:
        assert normalize("AleX   TiiKii") == "alex tiikii"

    def test_handles_already_normalized(self) -> None:
        assert normalize("whiplash 92") == "whiplash 92"


class TestIsAdminObserver:
    @pytest.mark.parametrize(
        "name",
        [
            "AleX TiiKii",
            "alex tiikii",
            "ALEX TIIKII",
            "  AleX  TiiKii ",
            "whiplash 92",
            "Whiplash 92",
            "WHIPLASH 92",
        ],
    )
    def test_observers_match_case_insensitive(self, name: str) -> None:
        assert is_admin_observer(name) is True

    @pytest.mark.parametrize(
        "name",
        [
            "Юрий Shestakov",
            "Tandem: Vlad, whiplash 92",  # tandem name itself is not observer
            "Vlad V",
            "",
            "alex",
        ],
    )
    def test_non_observers_do_not_match(self, name: str) -> None:
        assert is_admin_observer(name) is False

    def test_canonical_set_size(self) -> None:
        # If the set ever changes, every test below must be revisited.
        assert ADMIN_OBSERVERS == frozenset({"whiplash 92", "AleX TiiKii"})


class TestParseTandemMembers:
    @pytest.mark.parametrize(
        "name,expected",
        [
            ("Tandem: Vlad, whiplash 92", ["Vlad", "whiplash 92"]),
            ("Tandem:Vlad,whiplash 92", ["Vlad", "whiplash 92"]),
            ("  tandem  : a , b ", ["a", "b"]),
            ("Tandem: A, B, C", ["A", "B", "C"]),
            ("TANDEM: Foo, Bar", ["Foo", "Bar"]),
        ],
    )
    def test_splits_known_formats(self, name: str, expected: list[str]) -> None:
        assert parse_tandem_members(name) == expected

    @pytest.mark.parametrize(
        "name",
        ["Юрий Shestakov", "whiplash 92", "Tandem", "TandemFoo", ""],
    )
    def test_returns_none_for_non_tandem(self, name: str) -> None:
        assert parse_tandem_members(name) is None

    def test_drops_empty_members(self) -> None:
        assert parse_tandem_members("Tandem: A, ,B") == ["A", "B"]


class TestTandemObserverMembers:
    def test_returns_observer_in_pair(self) -> None:
        assert tandem_observer_members("Tandem: Vlad, whiplash 92") == ("whiplash 92",)

    def test_returns_lowercased_observer(self) -> None:
        # We preserve the original spelling from the input string.
        assert tandem_observer_members("Tandem: Vlad, alex tiikii") == ("alex tiikii",)

    def test_empty_for_clean_tandem(self) -> None:
        assert tandem_observer_members("Tandem: Sergey D., Maxim S.") == ()

    def test_empty_for_solo_observer(self) -> None:
        assert tandem_observer_members("whiplash 92") == ()


# ---------------------------------------------------------------------------
# Allowlist loading
# ---------------------------------------------------------------------------


class TestLoadExplicitTandems:
    def test_real_allowlist_contains_vlad_pair(self) -> None:
        allowlist = load_explicit_tandems()
        # data/seed/explicit_tandems.json is committed to the repo.
        assert frozenset({"vlad", "whiplash 92"}) in allowlist

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        target = tmp_path / "missing.json"
        assert load_explicit_tandems(target) == frozenset()

    def test_ignores_non_tandem_entries(self, tmp_path: Path) -> None:
        path = tmp_path / "allow.json"
        path.write_text(json.dumps(["Tandem: a, b", "not-a-tandem"]), encoding="utf-8")
        allowlist = load_explicit_tandems(path)
        assert allowlist == frozenset({frozenset({"a", "b"})})

    def test_normalizes_member_order(self, tmp_path: Path) -> None:
        path = tmp_path / "allow.json"
        path.write_text(json.dumps(["Tandem: B, A"]), encoding="utf-8")
        allowlist = load_explicit_tandems(path)
        # Same members regardless of order.
        assert is_explicit_tandem("Tandem: A, B", allowlist) is True
        assert is_explicit_tandem("Tandem: B, A", allowlist) is True


# ---------------------------------------------------------------------------
# validate_manager_name
# ---------------------------------------------------------------------------


class TestValidateManagerName:
    @pytest.fixture
    def empty_allowlist(self) -> frozenset[frozenset[str]]:
        return frozenset()

    @pytest.fixture
    def vlad_allowlist(self) -> frozenset[frozenset[str]]:
        return frozenset({frozenset({"vlad", "whiplash 92"})})

    @pytest.mark.parametrize(
        "name",
        [
            "whiplash 92",
            "AleX TiiKii",
            "Юрий Shestakov",
            "Tandem: Sergey D., Maxim S.",
            "",
        ],
    )
    def test_passes_for_unrelated_names(
        self, name: str, empty_allowlist: frozenset[frozenset[str]]
    ) -> None:
        # Should not raise.
        validate_manager_name(name, empty_allowlist)

    @pytest.mark.parametrize(
        "name",
        [
            "Tandem: Foo, whiplash 92",
            "Tandem: Foo, Whiplash 92",
            "Tandem: Foo, AleX TiiKii",
            "Tandem: Foo, alex tiikii",
            "Tandem: whiplash 92, Foo",
        ],
    )
    def test_rejects_unsanctioned_observer_tandem(
        self, name: str, empty_allowlist: frozenset[frozenset[str]]
    ) -> None:
        with pytest.raises(ValueError, match="admin observer"):
            validate_manager_name(name, empty_allowlist)

    def test_passes_for_explicit_tandem_in_allowlist(
        self, vlad_allowlist: frozenset[frozenset[str]]
    ) -> None:
        # Both spellings of the canonical pair should resolve.
        validate_manager_name("Tandem: Vlad, whiplash 92", vlad_allowlist)
        validate_manager_name("Tandem: whiplash 92, Vlad", vlad_allowlist)

    def test_uses_default_allowlist_when_omitted(self) -> None:
        # data/seed/explicit_tandems.json is committed; this entry is in it.
        validate_manager_name("Tandem: Vlad, whiplash 92")

    def test_error_message_mentions_observer_name(
        self, empty_allowlist: frozenset[frozenset[str]]
    ) -> None:
        with pytest.raises(ValueError) as excinfo:
            validate_manager_name("Tandem: Foo, AleX TiiKii", empty_allowlist)
        message = str(excinfo.value)
        assert "AleX TiiKii" in message
        assert "explicit_tandems.json" in message


# ---------------------------------------------------------------------------
# Integration: SeedService._seed_managers
# ---------------------------------------------------------------------------


class TestSeedServiceIntegration:
    """``_seed_managers`` should reject unsanctioned observer tandems."""

    @pytest.fixture
    def country_in_db(self, db_session: Any) -> Any:
        """Insert a single RUS country so ``_seed_managers`` resolves FKs."""

        from models import Country

        country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
        db_session.add(country)
        db_session.commit()
        return country

    def _service(self, db_session: Any, tmp_path: Path) -> Any:
        """Build a SeedService that reads from a throwaway seed dir."""

        from data.seed_service import SeedService

        return SeedService(db_session, seed_dir=str(tmp_path))

    def test_rejects_unsanctioned_observer_tandem(
        self,
        db_session: Any,
        country_in_db: Any,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Force an empty allowlist for this test (the real one would
        # otherwise let "Tandem: Vlad, whiplash 92" through).
        from data import seed_service as seed_service_module

        monkeypatch.setattr(seed_service_module, "load_explicit_tandems", lambda: frozenset())

        from data.seed_service import SeedResult

        managers = [
            {"name": "Юрий Shestakov", "country_code": "RUS"},
            {"name": "Tandem: Foo, whiplash 92", "country_code": "RUS"},
        ]

        result = SeedResult()
        self._service(db_session, tmp_path)._seed_managers(managers, result)
        db_session.commit()

        assert result.managers_created == 1
        assert any("admin observer" in err for err in result.errors)

        from models import Manager

        names = {m.name for m in db_session.query(Manager).all()}
        assert "Юрий Shestakov" in names
        assert "Tandem: Foo, whiplash 92" not in names

    def test_accepts_allowlisted_observer_tandem(
        self, db_session: Any, country_in_db: Any, tmp_path: Path
    ) -> None:
        from data.seed_service import SeedResult

        managers = [
            {"name": "Tandem: Vlad, whiplash 92", "country_code": "RUS"},
        ]

        result = SeedResult()
        self._service(db_session, tmp_path)._seed_managers(managers, result)
        db_session.commit()

        assert result.managers_created == 1
        assert result.errors == []

        from models import Manager

        names = {m.name for m in db_session.query(Manager).all()}
        assert "Tandem: Vlad, whiplash 92" in names


# ---------------------------------------------------------------------------
# Integration: Flask-Admin views
# ---------------------------------------------------------------------------


class TestManagerModelViewGuardrail:
    """``ManagerModelView.on_model_change`` should block unsanctioned tandems."""

    def test_blocks_unsanctioned_tandem(self, db_session: Any) -> None:
        from models import Country, Manager
        from services.admin.views import ManagerModelView

        country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
        db_session.add(country)
        db_session.commit()

        manager = Manager(name="Tandem: Foo, whiplash 92", country_id=country.id)
        view = ManagerModelView(Manager, db_session)
        with pytest.raises(ValueError, match="admin observer"):
            view.on_model_change(form=None, model=manager, is_created=True)

    def test_allows_clean_manager(self, db_session: Any) -> None:
        from models import Country, Manager
        from services.admin.views import ManagerModelView

        country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
        db_session.add(country)
        db_session.commit()

        manager = Manager(name="Юрий Shestakov", country_id=country.id)
        view = ManagerModelView(Manager, db_session)
        # Should not raise.
        view.on_model_change(form=None, model=manager, is_created=True)


class TestAchievementModelViewGuardrail:
    """``AchievementModelView`` blocks achievements pointing at observer tandems."""

    def test_blocks_achievement_for_unsanctioned_tandem(self, db_session: Any) -> None:
        from models import (
            Achievement,
            AchievementType,
            Country,
            League,
            Manager,
            Season,
        )
        from services.admin.views import AchievementModelView

        country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
        db_session.add(country)
        db_session.commit()

        # Bypass the ManagerModelView guardrail by creating the manager directly,
        # simulating a legacy / out-of-band insertion path.
        bad_manager = Manager(name="Tandem: Foo, whiplash 92", country_id=country.id)
        db_session.add(bad_manager)

        ach_type = AchievementType(
            code="TOP1", name="Top 1", base_points_l1=800, base_points_l2=400
        )
        league = League(code="1", name="League 1")
        season = Season(code="25/26", name="Season 25/26", multiplier=1.0, is_active=True)
        db_session.add_all([ach_type, league, season])
        db_session.commit()

        achievement = Achievement(
            manager_id=bad_manager.id,
            type_id=ach_type.id,
            league_id=league.id,
            season_id=season.id,
            title="TOP1",
            icon_path="/static/img/cups/top1.svg",
        )

        view = AchievementModelView(Achievement, db_session)
        with pytest.raises(ValueError, match="admin observer"):
            view.on_model_change(form=None, model=achievement, is_created=True)
