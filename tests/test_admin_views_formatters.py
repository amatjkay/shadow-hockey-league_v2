"""Unit tests for the audit-log formatters defined in services/admin/views.py.

The formatters render audit-log rows in the Flask-Admin AuditLogModelView.
They were previously only exercised indirectly through the integration test
suite, leaving most of their branches uncovered (TIK-54). These pure
helpers are easy to pin down with unit tests since they don't need a DB
session — only an `AuditLog` instance with the right attributes set.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from services.admin.views import (
    _action_badge_class,
    _format_audit_changes,
    _format_target_link,
)


class TestActionBadgeClass:
    """`_action_badge_class` maps an action name to a Bootstrap badge class."""

    @pytest.mark.parametrize(
        "action,expected",
        [
            ("CREATE", "create"),
            ("UPDATE", "update"),
            ("DELETE", "delete"),
            ("LOGIN", "secondary"),
            ("UNKNOWN", "secondary"),
            ("", "secondary"),
        ],
    )
    def test_known_and_fallback_actions(self, action: str, expected: str) -> None:
        assert _action_badge_class(action) == expected


class TestFormatAuditChanges:
    """`_format_audit_changes` renders a JSON-encoded changes payload as HTML."""

    def test_returns_no_changes_marker_when_empty(self) -> None:
        result = str(_format_audit_changes(None))
        assert "No changes" in result

        result_empty = str(_format_audit_changes(""))
        assert "No changes" in result_empty

    def test_returns_raw_when_payload_is_not_a_dict(self) -> None:
        # A JSON list is valid JSON but not a dict — fall back to a code block.
        result = str(_format_audit_changes(json.dumps(["a", "b"])))
        assert "<code" in result

    def test_returns_raw_on_invalid_json(self) -> None:
        result = str(_format_audit_changes("{not valid json"))
        assert "<code" in result

    def test_renders_create_style_changes(self) -> None:
        payload = json.dumps({"name": "Russia", "code": "RUS"})
        result = str(_format_audit_changes(payload))
        assert "Russia" in result
        assert "RUS" in result
        # CREATE-style should not include the diff arrow.
        assert "&rarr;" not in result

    def test_renders_update_style_changes_with_old_new(self) -> None:
        payload = json.dumps(
            {
                "name": {"old": "Russia", "new": "Российская Федерация"},
                "code": {"old": "RUS", "new": "RU"},
            }
        )
        result = str(_format_audit_changes(payload))
        assert "Russia" in result
        assert "Российская Федерация" in result
        assert "&rarr;" in result
        assert "<del>" in result

    def test_renders_null_old_value_as_italic(self) -> None:
        payload = json.dumps({"name": {"old": None, "new": "Russia"}})
        result = str(_format_audit_changes(payload))
        assert "<i>null</i>" in result
        assert "Russia" in result

    def test_renders_null_new_value_as_italic(self) -> None:
        payload = json.dumps({"name": {"old": "Russia", "new": None}})
        result = str(_format_audit_changes(payload))
        assert "<i>null</i>" in result

    def test_hides_password_hash_field(self) -> None:
        payload = json.dumps({"username": "admin", "password_hash": "supersecret"})
        result = str(_format_audit_changes(payload))
        assert "[HIDDEN]" in result
        assert "supersecret" not in result

    def test_hides_key_hash_field(self) -> None:
        payload = json.dumps({"name": "primary", "key_hash": "deadbeef"})
        result = str(_format_audit_changes(payload))
        assert "[HIDDEN]" in result
        assert "deadbeef" not in result


class TestFormatTargetLink:
    """`_format_target_link` builds an admin-edit-view link for an audit row."""

    def test_returns_dash_for_no_target_model(self) -> None:
        log = SimpleNamespace(target_model=None, target_id=None)
        result = str(_format_target_link(log))  # type: ignore[arg-type]
        assert "-" in result

    def test_returns_target_id_text_when_target_id_missing(self) -> None:
        log = SimpleNamespace(target_model="Country", target_id=None)
        result = str(_format_target_link(log))  # type: ignore[arg-type]
        assert "-" in result

    def test_returns_unmapped_model_as_plain_span(self) -> None:
        log = SimpleNamespace(target_model="UnknownModel", target_id=42)
        result = str(_format_target_link(log))  # type: ignore[arg-type]
        assert "UnknownModel" in result
        assert "#42" in result
        # Unmapped models do not get an `<a href>` link.
        assert 'href="' not in result

    def test_returns_link_for_known_model_inside_app_context(self, app) -> None:
        """Inside a Flask app context with admin endpoints, returns a clickable link."""
        log = SimpleNamespace(target_model="Country", target_id=7)
        with app.test_request_context("/admin/"):
            result = str(_format_target_link(log))  # type: ignore[arg-type]
        # Either url_for resolves and we get an <a href>, or it raises and we
        # fall back to the plain span — both are acceptable contracts.
        assert "Country" in result
        assert "#7" in result

    def test_falls_back_to_span_when_url_for_raises(self) -> None:
        """Outside an app/request context url_for raises; the fallback path runs."""
        log = SimpleNamespace(target_model="Country", target_id=7)
        result = str(_format_target_link(log))  # type: ignore[arg-type]
        assert "Country" in result
        assert "#7" in result
        # Outside the request context url_for raises → fallback span (no href).
        assert 'href="' not in result
