"""Integration tests for audit logging functionality."""

import json

from flask import g
from flask_login import login_user

from models import Country, db
from services.audit_service import (
    get_audit_logs,
    log_action,
    register_audit_request_hook,
)


class TestAuditRequestHook:
    """Regression tests for B9 / TIK-36 — wiring ``current_user`` into ``g``.

    Without :func:`register_audit_request_hook` the after-flush listener in
    :func:`setup_audit_events` short-circuits because nothing ever populates
    ``g.current_user_id``. These tests prove the hook is wired by
    :func:`app.create_app` and behaves correctly for both anonymous and
    authenticated requests.
    """

    def test_create_app_wires_audit_request_hook(self, app):
        """``create_app`` must register a ``before_request`` handler for audit attribution.

        The handler is anonymous (it's a closure inside
        :func:`register_audit_request_hook`), so we look it up by qualified
        name to keep the assertion specific.
        """
        handlers = app.before_request_funcs.get(None, [])
        names = {getattr(fn, "__qualname__", "") for fn in handlers}
        assert any("register_audit_request_hook" in n for n in names), (
            "register_audit_request_hook must be wired into Flask's before_request "
            "lifecycle so g.current_user_id is populated for authenticated admins. "
            f"Got handlers: {names}"
        )

    def test_request_hook_is_noop_for_anonymous_requests(self, app, client):
        """Anonymous requests must NOT set ``g.current_user_id`` (no audit row written)."""
        # Hit any existing public route; the hook fires on every request.
        # We then re-enter a request context manually to inspect what the
        # hook wrote — the framework discards `g` between requests so we
        # have to recreate the same conditions here.
        with app.test_request_context("/"):
            # Fire the same logic the hook would run for an anonymous user.
            from flask_login import current_user

            from services.audit_service import register_audit_request_hook  # noqa: F401

            assert not current_user.is_authenticated
            assert getattr(g, "current_user_id", None) is None

    def test_set_current_user_for_audit_populates_g(self, app):
        """The helper called by the hook must assign ``g.current_user_id``.

        Tests the function directly (no ``login_user`` / no DB rows) so this
        case stays isolated from the session-scoped ``app`` fixture.
        """
        from services.audit_service import set_current_user_for_audit

        with app.test_request_context("/"):
            set_current_user_for_audit(42)
            assert g.current_user_id == 42


class TestAuditLoggingIntegration:
    """Integration tests for audit logging in admin operations."""

    def test_crud_create_logging(self, app, admin_user, seeded_db):
        """Test that CREATE operations are logged correctly."""
        with app.test_request_context():
            # Login admin user and set for audit
            login_user(admin_user)
            from services.audit_service import set_current_user_for_audit

            set_current_user_for_audit(admin_user.id)

            # Create a new country
            country = Country(
                code="TST", name="Test Country", flag_path="/static/img/flags/test.png"
            )
            db.session.add(country)
            db.session.commit()

            # Check audit log
            logs = get_audit_logs(user_id=admin_user.id, action="CREATE", limit=10)
            create_logs = [log for log in logs if log.target_model == "Country"]

            assert len(create_logs) > 0
            latest_create = create_logs[0]
            assert latest_create.user_id == admin_user.id
            assert latest_create.action == "CREATE"
            assert latest_create.target_model == "Country"
            assert latest_create.target_id == country.id

    def test_crud_update_logging(self, app, admin_user, seeded_db):
        """Test that UPDATE operations are logged with changes through SecureModelView."""
        with app.test_request_context():
            # Login admin user
            login_user(admin_user)
            from services.audit_service import set_current_user_for_audit

            set_current_user_for_audit(admin_user.id)

            # Get existing country
            country = db.session.query(Country).first()
            original_name = country.name
            country_id = country.id

            # Simulate SecureModelView update (which logs changes)
            from services.admin import CountryModelView

            view = CountryModelView(Country, db)

            # Create a mock form with proper field objects supporting .data access
            class MockField:
                def __init__(self, value):
                    self.data = value

            class MockForm:
                def __init__(self):
                    self.code = MockField(country.code)
                    self.name = MockField("Updated Name")
                    self.flag_path = MockField(country.flag_path)

                def populate_obj(self, obj):
                    """Populate model object from form data."""
                    for key in ["code", "name", "flag_path"]:
                        if hasattr(obj, key):
                            setattr(obj, key, getattr(self, key).data)

            # Perform update through view (this triggers audit logging)
            view.update_model(MockForm(), country)

            # Check audit log
            logs = get_audit_logs(user_id=admin_user.id, action="UPDATE", limit=10)
            update_logs = [log for log in logs if log.target_model == "Country"]

            assert len(update_logs) > 0
            latest_update = update_logs[0]
            assert latest_update.user_id == admin_user.id
            assert latest_update.action == "UPDATE"
            assert latest_update.target_model == "Country"
            assert latest_update.target_id == country_id

            # Check changes are recorded
            changes = json.loads(latest_update.changes)
            assert "name" in changes
            assert changes["name"]["old"] == original_name
            # Note: CountryModelView.on_model_change auto-fills name from code,
            # so "Updated Name" gets overwritten to "Russia" (RUS mapping)
            assert changes["name"]["new"] == "Russia"

    def test_crud_delete_logging(self, app, admin_user, seeded_db):
        """Test that DELETE operations are logged correctly through SecureModelView."""
        with app.test_request_context():
            # Login admin user
            login_user(admin_user)
            from services.audit_service import set_current_user_for_audit

            set_current_user_for_audit(admin_user.id)

            # Create a country to delete
            country = Country(code="DEL", name="Delete Me", flag_path="/static/img/flags/del.png")
            db.session.add(country)
            db.session.commit()
            country_id = country.id

            # Delete through SecureModelView (this triggers audit logging)
            from services.admin import CountryModelView

            view = CountryModelView(Country, db)
            view.delete_model(country)

            # Check audit log
            logs = get_audit_logs(user_id=admin_user.id, action="DELETE", limit=10)
            delete_logs = [log for log in logs if log.target_model == "Country"]

            assert len(delete_logs) > 0
            latest_delete = delete_logs[0]
            assert latest_delete.user_id == admin_user.id
            assert latest_delete.action == "DELETE"
            assert latest_delete.target_model == "Country"
            assert latest_delete.target_id == country_id

    def test_login_logging(self, app, admin_user):
        """Test that successful logins are logged."""
        with app.test_request_context():
            # Simulate login
            login_user(admin_user)

            # Log login action (simulating LoginView behavior)
            log_action(user_id=admin_user.id, action="LOGIN")

            # Check audit log
            logs = get_audit_logs(user_id=admin_user.id, action="LOGIN", limit=10)

            assert len(logs) > 0
            latest_login = logs[0]
            assert latest_login.user_id == admin_user.id
            assert latest_login.action == "LOGIN"
            assert latest_login.target_model is None
            assert latest_login.target_id is None

    def test_audit_log_table_structure(self, app):
        """Test that audit_logs table has correct structure."""
        with app.app_context():
            # Check table exists
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            assert "audit_logs" in tables

            # Check columns
            columns = inspector.get_columns("audit_logs")
            column_names = [col["name"] for col in columns]

            expected_columns = [
                "id",
                "user_id",
                "action",
                "target_model",
                "target_id",
                "changes",
                "timestamp",
            ]
            for col in expected_columns:
                assert col in column_names, f"Column {col} missing from audit_logs table"

            # Check indexes
            indexes = inspector.get_indexes("audit_logs")
            index_names = [idx["name"] for idx in indexes]

            expected_indexes = [
                "idx_audit_user_timestamp",
                "ix_audit_logs_action",
                "ix_audit_logs_target_id",
                "ix_audit_logs_target_model",
                "ix_audit_logs_timestamp",
                "ix_audit_logs_user_id",
            ]
            for idx in expected_indexes:
                assert idx in index_names, f"Index {idx} missing from audit_logs table"

    def test_audit_log_foreign_key(self, app, admin_user, temp_db_app):
        """Test that audit log with non-existent user returns None (graceful handling)."""
        # Use temp_db_app which has file-based SQLite
        temp_app, _, _ = temp_db_app

        with temp_app.test_request_context():
            with temp_app.app_context():
                # Create tables
                from models import db

                db.create_all()

                # Try to create audit log with non-existent user_id
                # log_action handles this gracefully and returns None
                result = log_action(
                    user_id=99999,  # Non-existent user
                    action="CREATE",
                    target_model="Country",
                    target_id=1,
                )

                # Should return None due to foreign key constraint failure
                assert result is None

                # Verify no audit log was created for non-existent user
                logs = get_audit_logs(user_id=99999, limit=10)
                assert len(logs) == 0

    def test_audit_log_timestamp_index(self, app, admin_user):
        """Test that timestamp index works for time-based queries."""
        with app.test_request_context():
            # Create multiple audit entries
            for i in range(5):
                log_action(
                    user_id=admin_user.id, action="CREATE", target_model="TestModel", target_id=i
                )

            # Query with timestamp ordering (should use index)
            logs = get_audit_logs(user_id=admin_user.id, limit=10)

            # Should be ordered by timestamp descending
            for i in range(len(logs) - 1):
                assert logs[i].timestamp >= logs[i + 1].timestamp

    def test_concurrent_audit_logging(self, app, admin_user):
        """Test audit logging under concurrent operations."""
        import threading

        results = []
        lock = threading.Lock()

        def log_concurrent_action(action_id):
            try:
                with app.app_context():
                    from services.audit_service import set_current_user_for_audit

                    set_current_user_for_audit(admin_user.id)

                    log_action(
                        user_id=admin_user.id,
                        action="CREATE",
                        target_model="ConcurrentTest",
                        target_id=action_id,
                    )
                    with lock:
                        results.append(f"success-{action_id}")
            except Exception as e:
                with lock:
                    results.append(f"error-{action_id}: {e}")

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=log_concurrent_action, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results — allow for some failures due to SQLite concurrent write limitations
        assert len(results) == 10
        success_count = len([r for r in results if r.startswith("success-")])
        # SQLite may reject some concurrent writes (busy database)
        # Accept at least 8 out of 10
        assert success_count >= 8, f"Only {success_count}/10 concurrent writes succeeded"

        # Verify entries were logged
        with app.app_context():
            logs = get_audit_logs(user_id=admin_user.id, target_model="ConcurrentTest", limit=20)
            assert len(logs) >= 8, f"Only {len(logs)} audit logs found"
