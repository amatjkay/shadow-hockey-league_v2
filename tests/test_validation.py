"""Tests for validation service.

Tests cover all validation functions including:
- Country uniqueness validation
- Manager uniqueness validation
- Data format validation
- Country/Manager existence validation
- DataValidator class
"""

import unittest

from app import create_app
from models import Country, Manager, db
from services.validation_service import (
    ValidationError,
    validate_achievement_data,
    validate_country_data,
    validate_country_exists,
    validate_country_unique,
    validate_manager_data,
    validate_manager_exists,
    validate_manager_unique,
)


class TestCountryValidation(unittest.TestCase):
    """Tests for country validation functions."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_validate_country_data_valid(self) -> None:
        """Valid country data should pass validation."""
        is_valid, error = validate_country_data("RUS", "/static/img/flags/rus.png")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_country_data_short_code(self) -> None:
        """Country code less than 3 letters should fail."""
        is_valid, error = validate_country_data("RU", "/static/img/flags/ru.png")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_country_data_long_code(self) -> None:
        """Country code more than 3 letters should fail."""
        is_valid, error = validate_country_data("RUSS", "/static/img/flags/russ.png")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_country_data_empty_flag(self) -> None:
        """Empty flag path should fail."""
        is_valid, error = validate_country_data("RUS", "")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_country_unique_new(self) -> None:
        """New country code should be unique."""
        is_valid, error = validate_country_unique(db.session, "USA")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_country_unique_duplicate(self) -> None:
        """Existing country code should not be unique."""
        country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
        db.session.add(country)
        db.session.commit()

        is_valid, error = validate_country_unique(db.session, "RUS")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_country_exists_valid(self) -> None:
        """Existing country should pass existence check."""
        country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
        db.session.add(country)
        db.session.commit()

        is_valid, error = validate_country_exists(db.session, country.id)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_country_exists_invalid(self) -> None:
        """Non-existent country should fail existence check."""
        is_valid, error = validate_country_exists(db.session, 9999)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)


class TestManagerValidation(unittest.TestCase):
    """Tests for manager validation functions."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
        db.session.add(self.country)
        db.session.commit()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_validate_manager_data_valid(self) -> None:
        """Valid manager data should pass validation."""
        is_valid, error = validate_manager_data("Test Manager", self.country.id)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_manager_data_empty_name(self) -> None:
        """Empty manager name should fail."""
        is_valid, error = validate_manager_data("", self.country.id)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_manager_data_no_country(self) -> None:
        """Missing country_id should fail."""
        is_valid, error = validate_manager_data("Test Manager", None)  # type: ignore[arg-type]
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_manager_unique_new(self) -> None:
        """New manager name should be unique."""
        is_valid, error = validate_manager_unique(db.session, "New Manager")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_manager_unique_duplicate(self) -> None:
        """Existing manager name should not be unique."""
        manager = Manager(name="Test Manager", country_id=self.country.id)
        db.session.add(manager)
        db.session.commit()

        is_valid, error = validate_manager_unique(db.session, "Test Manager")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_manager_exists_valid(self) -> None:
        """Existing manager should pass existence check."""
        manager = Manager(name="Test Manager", country_id=self.country.id)
        db.session.add(manager)
        db.session.commit()

        is_valid, error = validate_manager_exists(db.session, manager.id)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_manager_exists_invalid(self) -> None:
        """Non-existent manager should fail existence check."""
        is_valid, error = validate_manager_exists(db.session, 9999)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)


class TestAchievementValidation(unittest.TestCase):
    """Tests for achievement validation functions."""

    def test_validate_achievement_data_valid(self) -> None:
        """Valid achievement data should pass validation."""
        is_valid, error = validate_achievement_data("TOP1", "1", "24/25", "TOP1")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_achievement_data_empty_type(self) -> None:
        """Empty achievement type should fail."""
        is_valid, error = validate_achievement_data("", "1", "24/25", "TOP1")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_achievement_data_malformed_league_rejected(self) -> None:
        """Malformed league code (non-numeric / leading zero / trailing dot) is rejected."""
        for bad in ("abc", "01", "0", "2.", "2.1.1", ""):
            is_valid, error = validate_achievement_data("TOP1", bad, "24/25", "TOP1")
            self.assertFalse(is_valid, f"Expected '{bad}' to fail format validation")
            self.assertIsNotNone(error)

    def test_validate_achievement_data_l1_subleague_rejected(self) -> None:
        """L1 has no subleagues per business rules — '1.1' must be rejected."""
        is_valid, error = validate_achievement_data("TOP1", "1.1", "24/25", "TOP1")
        self.assertFalse(is_valid)
        assert error is not None
        self.assertIn("League 1 has no subleagues", error)

    def test_validate_achievement_data_subleague_accepted(self) -> None:
        """Subleagues for L2+ pass format validation (DB existence checked elsewhere)."""
        for code in ("2", "2.1", "2.2", "3", "3.1", "10", "10.5"):
            is_valid, error = validate_achievement_data("TOP1", code, "24/25", "TOP1")
            self.assertTrue(is_valid, f"Expected '{code}' to pass format validation: {error}")

    def test_validate_achievement_data_invalid_season(self) -> None:
        """Invalid season format - currently passes validation (no season format check)."""
        # Note: validation_service doesn't check season format
        is_valid, error = validate_achievement_data("TOP1", "1", "2024", "TOP1")
        self.assertTrue(is_valid)

    def test_validate_achievement_data_empty_title(self) -> None:
        """Empty title should fail."""
        is_valid, error = validate_achievement_data("TOP1", "1", "24/25", "")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)


class TestValidationError(unittest.TestCase):
    """Tests for ValidationError exception."""

    def test_validation_error_with_message(self) -> None:
        """ValidationError should store message."""
        error = ValidationError("Test error")
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.errors, [])

    def test_validation_error_with_errors(self) -> None:
        """ValidationError should store errors list."""
        error = ValidationError("Test error", errors=["Error 1", "Error 2"])
        self.assertEqual(error.errors, ["Error 1", "Error 2"])


class TestDataValidator(unittest.TestCase):
    """Tests for DataValidator class."""

    def setUp(self) -> None:
        self.app = create_app("config.TestingConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.country = Country(code="RUS", flag_path="/static/img/flags/rus.png")
        db.session.add(self.country)
        db.session.commit()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_validate_countries_valid(self) -> None:
        """Valid countries should pass validation."""
        from services.validation_service import DataValidator

        validator = DataValidator(db.session)
        result = validator.validate_countries(
            [
                {"code": "USA", "flag_path": "/static/img/flags/usa.png"},
                {"code": "GBR", "flag_path": "/static/img/flags/gbr.png"},
            ]
        )
        self.assertTrue(result)
        self.assertEqual(len(validator.errors), 0)

    def test_validate_countries_duplicate(self) -> None:
        """Duplicate country codes should fail."""
        from services.validation_service import DataValidator

        validator = DataValidator(db.session)
        result = validator.validate_countries(
            [
                {"code": "RUS", "flag_path": "/static/img/flags/rus.png"},
            ]
        )
        self.assertFalse(result)

    def test_validate_managers_valid(self) -> None:
        """Valid managers should pass validation."""
        from services.validation_service import DataValidator

        validator = DataValidator(db.session)
        result = validator.validate_managers(
            [
                {"name": "Manager 1", "country_id": self.country.id},
                {"name": "Manager 2", "country_id": self.country.id},
            ]
        )
        self.assertTrue(result)

    def test_validate_managers_duplicate_name(self) -> None:
        """Duplicate manager names should fail."""
        from services.validation_service import DataValidator

        validator = DataValidator(db.session)
        result = validator.validate_managers(
            [
                {"name": "Duplicate", "country_id": self.country.id},
                {"name": "Duplicate", "country_id": self.country.id},
            ]
        )
        self.assertFalse(result)

    def test_validate_achievements_valid(self) -> None:
        """Valid achievements should pass validation."""
        manager = Manager(name="Test Manager", country_id=self.country.id)
        db.session.add(manager)
        db.session.commit()

        from services.validation_service import DataValidator

        validator = DataValidator(db.session)
        result = validator.validate_achievements(
            [
                {
                    "manager_id": manager.id,
                    "achievement_type": "TOP1",
                    "league": "1",
                    "season": "25/26",
                    "title": "TOP1",
                },
            ],
            {manager.id},
        )
        self.assertTrue(result)

    def test_validate_achievements_invalid_manager(self) -> None:
        """Achievements with invalid manager should fail."""
        from services.validation_service import DataValidator

        validator = DataValidator(db.session)
        result = validator.validate_achievements(
            [
                {
                    "manager_id": 9999,
                    "achievement_type": "TOP1",
                    "league": "1",
                    "season": "25/26",
                    "title": "TOP1",
                },
            ],
            {1},
        )
        self.assertFalse(result)

    def test_get_report_with_errors(self) -> None:
        """Report should show errors."""
        from services.validation_service import DataValidator

        validator = DataValidator(db.session)
        validator.errors.append("Test error 1")
        validator.errors.append("Test error 2")
        report = validator.get_report()
        self.assertIn("Errors: 2", report)
        self.assertIn("Test error 1", report)

    def test_get_report_no_errors(self) -> None:
        """Report should show success when no errors."""
        from services.validation_service import DataValidator

        validator = DataValidator(db.session)
        report = validator.get_report()
        self.assertIn("No errors found", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
