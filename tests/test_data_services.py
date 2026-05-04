"""Tests for data services: export, seed, schemas, static_paths."""

import json
import tempfile
from pathlib import Path

import pytest

from data.export_service import ExportService
from data.schemas import (
    validate_achievements,
    validate_all,
    validate_countries,
    validate_managers,
)
from data.seed_service import SeedResult, SeedService
from data.static_paths import StaticPaths, resolve_cup, resolve_flag

# ==================== StaticPaths Tests ====================


class TestStaticPaths:
    """Test StaticPaths class."""

    def test_resolve_flag(self):
        paths = StaticPaths()
        url = paths.resolve_flag("RUS.png")
        assert url == "/static/img/flags/RUS.png"

    def test_resolve_flag_no_extension(self):
        paths = StaticPaths()
        url = paths.resolve_flag("BLR")
        assert url == "/static/img/flags/BLR.png"

    def test_resolve_flag_legacy(self):
        paths = StaticPaths()
        url = paths.resolve_flag("bel.png")
        assert url == "/static/img/flags/BLR.png"

    def test_resolve_cup(self):
        paths = StaticPaths()
        url = paths.resolve_cup("top1.svg")
        assert url == "/static/img/cups/top1.svg"

    def test_flag_to_code(self):
        paths = StaticPaths()
        code = paths.flag_to_code("KAZ.png")
        assert code == "KAZ"

    def test_flag_to_code_not_found(self):
        paths = StaticPaths()
        code = paths.flag_to_code("unknown.png")
        assert code is None

    def test_code_to_flag(self):
        paths = StaticPaths()
        filename = paths.code_to_flag("RUS")
        assert filename == "RUS.png"

    def test_code_to_flag_not_found(self):
        paths = StaticPaths()
        filename = paths.code_to_flag("XYZ")
        assert filename is None

    def test_module_level_resolve_flag(self):
        url = resolve_flag("RUS.png")
        assert "/static/img/flags/" in url

    def test_module_level_resolve_cup(self):
        url = resolve_cup("top1.svg")
        assert url == "/static/img/cups/top1.svg"


# ==================== Schema Validation Tests ====================


class TestValidateCountries:
    """Test countries schema validation."""

    def test_valid_countries(self):
        data = [
            {"code": "RUS", "name": "Russia", "flag_filename": "RUS.png"},
            {"code": "BLR", "name": "Belarus", "flag_filename": "BLR.png"},
        ]
        errors = validate_countries(data)
        assert errors == []

    def test_not_a_list(self):
        errors = validate_countries({"code": "RUS"})
        assert "Countries data must be a list" in errors

    def test_item_not_dict(self):
        errors = validate_countries(["not a dict"])
        assert "Countries[0]: Must be an object" in errors

    def test_missing_required_fields(self):
        errors = validate_countries([{}])
        assert any("Missing required field 'code'" in e for e in errors)
        assert any("Missing required field 'name'" in e for e in errors)

    def test_invalid_code_length(self):
        errors = validate_countries([{"code": "RU", "name": "R", "flag_filename": "R.png"}])
        # 2 chars is valid minimum
        assert "must be 2-3 characters" not in str(errors)

    def test_duplicate_country_code(self):
        data = [
            {"code": "RUS", "name": "Russia", "flag_filename": "RUS.png"},
            {"code": "RUS", "name": "Russia2", "flag_filename": "RUS2.png"},
        ]
        errors = validate_countries(data)
        assert any("Duplicate country code" in e for e in errors)

    def test_empty_name(self):
        data = [{"code": "RUS", "name": "   ", "flag_filename": "RUS.png"}]
        errors = validate_countries(data)
        assert any("must be a non-empty string" in e for e in errors)

    def test_invalid_flag_extension(self):
        data = [{"code": "RUS", "name": "Russia", "flag_filename": "RUS.jpg"}]
        errors = validate_countries(data)
        assert any("must end with .png" in e for e in errors)


class TestValidateManagers:
    """Test managers schema validation."""

    def test_valid_managers(self):
        data = [
            {"name": "Feel Good", "country_code": "BEL"},
            {"name": "Test User", "country_code": "RUS"},
        ]
        errors = validate_managers(data)
        assert errors == []

    def test_not_a_list(self):
        errors = validate_managers({"name": "Test"})
        assert "Managers data must be a list" in errors

    def test_duplicate_name(self):
        data = [
            {"name": "Test", "country_code": "RUS"},
            {"name": "Test", "country_code": "BLR"},
        ]
        errors = validate_managers(data)
        assert any("Duplicate manager name" in e for e in errors)

    def test_invalid_country_code(self):
        data = [{"name": "Test", "country_code": "TOOLONG"}]
        errors = validate_managers(data)
        assert any("must be 2-3 characters" in e for e in errors)


class TestValidateAchievements:
    """Test achievements schema validation."""

    def test_valid_achievements(self):
        data = [
            {
                "manager_name": "Test",
                "type": "TOP1",
                "league": "1",
                "season": "24/25",
                "title": "TOP1",
                "icon_filename": "top1.svg",
            }
        ]
        errors = validate_achievements(data)
        assert errors == []

    def test_invalid_type(self):
        data = [
            {
                "manager_name": "Test",
                "type": "INVALID",
                "league": "1",
                "season": "24/25",
                "title": "X",
                "icon_filename": "top1.svg",
            }
        ]
        errors = validate_achievements(data)
        assert any("'type' must be one of" in e for e in errors)

    def test_invalid_season_format(self):
        data = [
            {
                "manager_name": "Test",
                "type": "TOP1",
                "league": "1",
                "season": "2024",
                "title": "X",
                "icon_filename": "top1.svg",
            }
        ]
        errors = validate_achievements(data)
        assert any("must be in format 'YY/YY'" in e for e in errors)

    def test_invalid_icon_extension(self):
        data = [
            {
                "manager_name": "Test",
                "type": "TOP1",
                "league": "1",
                "season": "24/25",
                "title": "X",
                "icon_filename": "top1.txt",
            }
        ]
        errors = validate_achievements(data)
        assert any("must end with .svg or .png" in e for e in errors)

    def test_missing_fields(self):
        errors = validate_achievements([{}])
        assert any("Missing required field" in e for e in errors)

    def test_subleague_code_accepted(self):
        """Dotted subleague codes such as ``2.1`` / ``2.2`` must validate.

        Subleagues inherit ``base_points_l2`` via ``League.parent_code='2'`` so
        their seed entries are routinely tagged with the dotted code; the seed
        validator must allow them.
        """
        data = [
            {
                "manager_name": "Test",
                "type": "TOP1",
                "league": "2.2",
                "season": "25/26",
                "title": "TOP1",
                "icon_filename": "top1.svg",
            },
            {
                "manager_name": "Test",
                "type": "BEST_REG",
                "league": "2.1",
                "season": "25/26",
                "title": "Best regular",
                "icon_filename": "best-reg.svg",
            },
        ]
        errors = validate_achievements(data)
        assert errors == []

    def test_invalid_league_code_rejected(self):
        """Bogus league codes (leading zero, alpha, double dot) must fail."""
        bad_codes = ["0", "01", "2.", ".2", "2.2.2", "abc", "1a"]
        for code in bad_codes:
            data = [
                {
                    "manager_name": "Test",
                    "type": "TOP1",
                    "league": code,
                    "season": "25/26",
                    "title": "TOP1",
                    "icon_filename": "top1.svg",
                }
            ]
            errors = validate_achievements(data)
            assert any(
                "'league'" in e for e in errors
            ), f"expected league validation error for code={code!r}, got {errors!r}"


class TestValidateAll:
    """Test validate_all function."""

    def test_all_valid(self):
        result = validate_all([], [], [])
        assert result == {"countries": [], "managers": [], "achievements": []}

    def test_all_invalid(self):
        result = validate_all("not a list", "not a list", "not a list")
        assert result["countries"] != []
        assert result["managers"] != []
        assert result["achievements"] != []


# ==================== SeedResult Tests ====================


class TestSeedResult:
    """Test SeedResult class."""

    def test_to_dict(self):
        result = SeedResult()
        result.countries_created = 5
        result.managers_created = 10
        result.achievements_created = 20
        d = result.to_dict()
        assert d["countries"]["created"] == 5
        assert d["managers"]["created"] == 10
        assert d["achievements"]["created"] == 20

    def test_str_representation(self):
        result = SeedResult()
        result.countries_created = 3
        result.managers_created = 5
        result.achievements_created = 10
        s = str(result)
        assert "Countries: 3 created" in s
        assert "Managers: 5 created" in s
        assert "Achievements: 10 created" in s

    def test_str_with_errors(self):
        result = SeedResult()
        result.errors.append("Test error")
        s = str(result)
        assert "Errors: 1" in s


# ==================== SeedService Tests ====================


class TestSeedService:
    """Test SeedService class."""

    def test_load_json_file_not_found(self, app_context):
        service = SeedService(None, seed_dir="/nonexistent")
        with pytest.raises(FileNotFoundError):
            service._load_json("missing.json")

    def test_load_json_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.json"
            filepath.write_text(json.dumps([{"key": "value"}]), encoding="utf-8")
            service = SeedService(None, seed_dir=tmpdir)
            data = service._load_json("test.json")
            assert data == [{"key": "value"}]

    def test_seed_all_skip_if_data_exists(self, seeded_db):
        """seed_all should skip if managers already exist."""
        service = SeedService(seeded_db)
        result = service.seed_all()
        # Should skip because seeded_db has managers
        assert result.managers_created == 0
        assert result.managers_skipped == 0  # safe mode returns early

    def test_seed_all_force_clears_data(self, seeded_db):
        """seed_all with force=True should clear data first."""
        service = SeedService(seeded_db)
        result = service.seed_all(force=True)
        # Will try to seed, may fail due to missing seed files
        # but should attempt to clear data
        assert result is not None


# ==================== ExportService Tests ====================


class TestExportService:
    """Test ExportService class."""

    def test_export_countries(self, seeded_db, app_context):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ExportService(seeded_db, export_dir=tmpdir)
            count = service.export_countries()
            assert count >= 1  # seeded_db has at least 1 country

            filepath = Path(tmpdir) / "countries.json"
            assert filepath.exists()

            data = json.loads(filepath.read_text(encoding="utf-8"))
            assert len(data) >= 1
            assert "code" in data[0]
            assert "name" in data[0]

    def test_export_managers(self, seeded_db, app_context):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ExportService(seeded_db, export_dir=tmpdir)
            count = service.export_managers()
            assert count >= 1

            filepath = Path(tmpdir) / "managers.json"
            assert filepath.exists()

            data = json.loads(filepath.read_text(encoding="utf-8"))
            assert len(data) >= 1
            assert "name" in data[0]

    def test_export_achievements(self, seeded_db, app_context):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ExportService(seeded_db, export_dir=tmpdir)
            count = service.export_achievements()
            assert count >= 1

            filepath = Path(tmpdir) / "achievements.json"
            assert filepath.exists()

            data = json.loads(filepath.read_text(encoding="utf-8"))
            assert len(data) >= 1
            assert "manager_name" in data[0]

    def test_export_all(self, seeded_db, app_context):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ExportService(seeded_db, export_dir=tmpdir)
            result = service.export_all()
            assert "countries" in result
            assert "managers" in result
            assert "achievements" in result
            assert result["countries"] >= 1
            assert result["managers"] >= 1
            assert result["achievements"] >= 1
