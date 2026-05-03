"""Unit tests for ``services/api/_helpers.py``.

Covers the ``?fields=`` query-parameter projection branch and the
field-projection helper itself, which were previously only exercised via
the full-payload happy path in integration tests.
"""

from __future__ import annotations

from services.api._helpers import _parse_fields_param, _project


class TestParseFieldsParam:
    """``_parse_fields_param`` reads ``request.args['fields']``."""

    def test_returns_none_when_param_absent(self, app) -> None:
        with app.test_request_context("/api/managers"):
            assert _parse_fields_param() is None

    def test_returns_none_when_param_empty(self, app) -> None:
        with app.test_request_context("/api/managers?fields="):
            assert _parse_fields_param() is None

    def test_returns_none_when_param_only_whitespace(self, app) -> None:
        with app.test_request_context("/api/managers?fields=%20%20"):
            assert _parse_fields_param() is None

    def test_returns_none_when_only_commas(self, app) -> None:
        """Commas with no field names yield an empty parts set → None."""
        with app.test_request_context("/api/managers?fields=,,,"):
            assert _parse_fields_param() is None

    def test_parses_single_field_and_injects_id(self, app) -> None:
        with app.test_request_context("/api/managers?fields=name"):
            result = _parse_fields_param()
        assert result == {"id", "name"}

    def test_parses_multiple_fields_with_whitespace(self, app) -> None:
        with app.test_request_context("/api/managers?fields=name, country_code , flag"):
            result = _parse_fields_param()
        assert result == {"id", "name", "country_code", "flag"}

    def test_id_already_present_does_not_duplicate(self, app) -> None:
        with app.test_request_context("/api/managers?fields=id,name"):
            result = _parse_fields_param()
        assert result == {"id", "name"}


class TestProject:
    """``_project`` filters a record dict onto an allow-list."""

    def test_returns_record_unchanged_when_fields_is_none(self) -> None:
        record = {"id": 1, "name": "x", "country_code": "RUS"}
        assert _project(record, None) == record

    def test_keeps_only_requested_fields(self) -> None:
        record = {"id": 1, "name": "x", "country_code": "RUS", "is_active": True}
        result = _project(record, {"id", "name"})
        assert result == {"id": 1, "name": "x"}

    def test_drops_unknown_keys_silently(self) -> None:
        record = {"id": 1, "name": "x"}
        result = _project(record, {"id", "name", "missing"})
        assert result == {"id": 1, "name": "x"}

    def test_returns_empty_dict_when_no_intersection(self) -> None:
        record = {"a": 1, "b": 2}
        result = _project(record, {"c", "d"})
        assert result == {}
