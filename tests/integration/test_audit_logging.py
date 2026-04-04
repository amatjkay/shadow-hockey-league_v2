"""Integration tests for audit logging functionality."""

import pytest
from flask import Flask
from models import db, AdminUser, Country, Manager, AuditLog
from services.audit_service import log_action, get_audit_logs
from services.admin import SecureModelView, CountryModelView
from flask_login import login_user


class TestAuditLoggingIntegration:
    """Integration tests for audit logging in admin operations."""

    def test_crud_create_logging(self, app, admin_user, seeded_db):
        """Test that CREATE operations are logged correctly."""
        with app.test_request_context():
            # Create tables first
            db.create_all()
            
            # Login admin user and set for audit
            login_user(admin_user)
            from services.audit_service import set_current_user_for_audit
            set_current_user_for_audit(admin_user.id)
            
            # Create a new country
            country = Country(code="TST", name="Test Country", flag_path="/static/img/flags/test.png")
            db.session.add(country)
            db.session.commit()
            
            # Check audit log
            logs = get_audit_logs(user_id=admin_user.id, action='CREATE', limit=10)
            create_logs = [log for log in logs if log.target_model == 'Country']
            
            assert len(create_logs) > 0
            latest_create = create_logs[0]
            assert latest_create.user_id == admin_user.id
            assert latest_create.action == 'CREATE'
            assert latest_create.target_model == 'Country'
            assert latest_create.target_id == country.id

    def test_crud_update_logging(self, app, admin_user, seeded_db):
        """Test that UPDATE operations are logged with changes."""
        with app.test_request_context():
            # Login admin user
            login_user(admin_user)
            
            # Get existing country and update it
            country = db.session.query(Country).first()
            original_name = country.name
            country.name = "Updated Name"
            db.session.commit()
            
            # Check audit log
            logs = get_audit_logs(user_id=admin_user.id, action='UPDATE', limit=10)
            update_logs = [log for log in logs if log.target_model == 'Country']
            
            assert len(update_logs) > 0
            latest_update = update_logs[0]
            assert latest_update.user_id == admin_user.id
            assert latest_update.action == 'UPDATE'
            assert latest_update.target_model == 'Country'
            assert latest_update.target_id == country.id
            
            # Check changes are recorded
            import json
            changes = json.loads(latest_update.changes)
            assert 'name' in changes
            assert changes['name']['old'] == original_name
            assert changes['name']['new'] == "Updated Name"

    def test_crud_delete_logging(self, app, admin_user, seeded_db):
        """Test that DELETE operations are logged correctly."""
        with app.test_request_context():
            # Login admin user
            login_user(admin_user)
            
            # Create a country to delete
            country = Country(code="DEL", name="Delete Me", flag_path="/static/img/flags/del.png")
            db.session.add(country)
            db.session.commit()
            country_id = country.id
            
            # Delete the country
            db.session.delete(country)
            db.session.commit()
            
            # Check audit log
            logs = get_audit_logs(user_id=admin_user.id, action='DELETE', limit=10)
            delete_logs = [log for log in logs if log.target_model == 'Country']
            
            assert len(delete_logs) > 0
            latest_delete = delete_logs[0]
            assert latest_delete.user_id == admin_user.id
            assert latest_delete.action == 'DELETE'
            assert latest_delete.target_model == 'Country'
            assert latest_delete.target_id == country_id

    def test_login_logging(self, app, admin_user):
        """Test that successful logins are logged."""
        with app.test_request_context():
            # Simulate login
            login_user(admin_user)
            
            # Log login action (simulating LoginView behavior)
            log_action(user_id=admin_user.id, action='LOGIN')
            
            # Check audit log
            logs = get_audit_logs(user_id=admin_user.id, action='LOGIN', limit=10)
            
            assert len(logs) > 0
            latest_login = logs[0]
            assert latest_login.user_id == admin_user.id
            assert latest_login.action == 'LOGIN'
            assert latest_login.target_model is None
            assert latest_login.target_id is None

    def test_audit_log_table_structure(self, app):
        """Test that audit_logs table has correct structure."""
        with app.app_context():
            # Check table exists
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            assert 'audit_logs' in tables
            
            # Check columns
            columns = inspector.get_columns('audit_logs')
            column_names = [col['name'] for col in columns]
            
            expected_columns = ['id', 'user_id', 'action', 'target_model', 'target_id', 'changes', 'timestamp']
            for col in expected_columns:
                assert col in column_names, f"Column {col} missing from audit_logs table"
            
            # Check indexes
            indexes = inspector.get_indexes('audit_logs')
            index_names = [idx['name'] for idx in indexes]
            
            expected_indexes = ['idx_audit_user_timestamp', 'ix_audit_logs_action', 
                               'ix_audit_logs_target_id', 'ix_audit_logs_target_model',
                               'ix_audit_logs_timestamp', 'ix_audit_logs_user_id']
            for idx in expected_indexes:
                assert idx in index_names, f"Index {idx} missing from audit_logs table"

    def test_audit_log_foreign_key(self, app, admin_user, temp_db_app):
        """Test that foreign key constraint works correctly."""
        # Use temp_db_app which has file-based SQLite
        temp_app, _, _ = temp_db_app
        
        with temp_app.test_request_context():
            with temp_app.app_context():
                # Create tables
                from models import db
                db.create_all()
                
                # Try to create audit log with non-existent user_id
                with pytest.raises(Exception):  # Should raise integrity error
                    log_action(
                        user_id=99999,  # Non-existent user
                        action='CREATE',
                        target_model='Country',
                        target_id=1
                    )

    def test_audit_log_timestamp_index(self, app, admin_user):
        """Test that timestamp index works for time-based queries."""
        with app.test_request_context():
            # Create multiple audit entries
            for i in range(5):
                log_action(
                    user_id=admin_user.id,
                    action='CREATE',
                    target_model='TestModel',
                    target_id=i
                )
            
            # Query with timestamp ordering (should use index)
            logs = get_audit_logs(user_id=admin_user.id, limit=10)
            
            # Should be ordered by timestamp descending
            for i in range(len(logs) - 1):
                assert logs[i].timestamp >= logs[i + 1].timestamp

    def test_concurrent_audit_logging(self, app, admin_user):
        """Test audit logging under concurrent operations."""
        import threading
        import time
        
        results = []

        def log_concurrent_action(action_id):
            try:
                with app.app_context():
                    from services.audit_service import set_current_user_for_audit
                    set_current_user_for_audit(admin_user.id)
                    
                    log_action(
                        user_id=admin_user.id,
                        action='CREATE',
                        target_model='ConcurrentTest',
                        target_id=action_id
                    )
                    results.append(f"success-{action_id}")
            except Exception as e:
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

        # Check results
        assert len(results) == 10
        success_count = len([r for r in results if r.startswith('success-')])
        assert success_count == 10  # All should succeed
        
        # Verify all entries were logged
        with app.app_context():
            logs = get_audit_logs(user_id=admin_user.id, target_model='ConcurrentTest', limit=20)
            assert len(logs) == 10
