"""Tests for audit service functionality."""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from models import AuditLog, AdminUser, db
from services.audit_service import log_action, get_audit_logs, get_audit_log_count, cleanup_old_audit_logs


class TestAuditService:
    """Test cases for audit service functions."""

    def test_log_action_create_success(self, app, admin_user):
        """Test successful logging of CREATE action."""
        with app.app_context():
            audit_entry = log_action(
                user_id=admin_user.id,
                action='CREATE',
                target_model='Manager',
                target_id=123,
                changes={'name': 'Test Manager'}
            )
            
            assert audit_entry is not None
            assert audit_entry.user_id == admin_user.id
            assert audit_entry.action == 'CREATE'
            assert audit_entry.target_model == 'Manager'
            assert audit_entry.target_id == 123
            assert audit_entry.changes is not None
            
            # Verify changes are stored as JSON
            changes_data = json.loads(audit_entry.changes)
            assert changes_data['name'] == 'Test Manager'
            
            # Verify timestamp is set
            assert audit_entry.timestamp is not None

    def test_log_action_login_success(self, app, admin_user):
        """Test successful logging of LOGIN action."""
        with app.app_context():
            audit_entry = log_action(
                user_id=admin_user.id,
                action='LOGIN'
            )
            
            assert audit_entry is not None
            assert audit_entry.user_id == admin_user.id
            assert audit_entry.action == 'LOGIN'
            assert audit_entry.target_model is None
            assert audit_entry.target_id is None
            assert audit_entry.changes is None

    def test_log_action_flush_cache_success(self, app, admin_user):
        """Test successful logging of FLUSH_CACHE action."""
        with app.app_context():
            audit_entry = log_action(
                user_id=admin_user.id,
                action='FLUSH_CACHE'
            )
            
            assert audit_entry is not None
            assert audit_entry.action == 'FLUSH_CACHE'
            assert audit_entry.target_model is None
            assert audit_entry.target_id is None

    def test_log_action_with_none_changes(self, app, admin_user):
        """Test logging action with None changes."""
        with app.app_context():
            audit_entry = log_action(
                user_id=admin_user.id,
                action='UPDATE',
                target_model='Country',
                target_id=456,
                changes=None
            )
            
            assert audit_entry is not None
            assert audit_entry.changes is None

    def test_log_action_with_empty_changes(self, app, admin_user):
        """Test logging action with empty changes dict."""
        with app.app_context():
            audit_entry = log_action(
                user_id=admin_user.id,
                action='UPDATE',
                target_model='Country',
                target_id=456,
                changes={}
            )
            
            assert audit_entry is not None
            changes_data = json.loads(audit_entry.changes)
            assert changes_data == {}

    def test_log_action_invalid_user_id(self, app):
        """Test log_action with invalid user_id."""
        with app.app_context():
            with pytest.raises(ValueError, match="user_id is required"):
                log_action(
                    user_id=0,
                    action='CREATE'
                )

    def test_log_action_invalid_action(self, app, admin_user):
        """Test log_action with invalid action."""
        with app.app_context():
            # Empty action
            with pytest.raises(ValueError, match="action is required"):
                log_action(
                    user_id=admin_user.id,
                    action=''
                )
            
            # Too long action
            with pytest.raises(ValueError, match="action is required and must be <= 50 characters"):
                log_action(
                    user_id=admin_user.id,
                    action='A' * 51
                )

    def test_log_action_invalid_target_model(self, app, admin_user):
        """Test log_action with invalid target_model."""
        with app.app_context():
            with pytest.raises(ValueError, match="target_model must be <= 50 characters"):
                log_action(
                    user_id=admin_user.id,
                    action='CREATE',
                    target_model='M' * 51
                )

    def test_log_action_database_error(self, app, admin_user):
        """Test log_action handling of database errors."""
        with app.app_context():
            with patch('services.audit_service.db.session.commit', side_effect=Exception("DB Error")):
                audit_entry = log_action(
                    user_id=admin_user.id,
                    action='CREATE'
                )
                
                # Should return None on database error
                assert audit_entry is None

    def test_log_action_changes_serialization_error(self, app, admin_user):
        """Test log_action handling of JSON serialization errors."""
        with app.app_context():
            # Create an object that can't be serialized to JSON
            class UnserializableObject:
                pass
            
            changes = {'bad_object': UnserializableObject()}
            
            audit_entry = log_action(
                user_id=admin_user.id,
                action='UPDATE',
                target_model='Manager',
                target_id=123,
                changes=changes
            )
            
            # Should still succeed but with error message in changes
            assert audit_entry is not None
            changes_data = json.loads(audit_entry.changes)
            assert 'error' in changes_data

    def test_get_audit_logs_all(self, app, admin_user, sample_audit_logs):
        """Test retrieving all audit logs."""
        with app.app_context():
            logs = get_audit_logs(limit=10)
            
            assert len(logs) == len(sample_audit_logs)
            # Should be ordered by timestamp descending
            assert logs[0].timestamp >= logs[1].timestamp

    def test_get_audit_logs_by_user(self, app, admin_user, sample_audit_logs):
        """Test retrieving audit logs filtered by user."""
        with app.app_context():
            logs = get_audit_logs(user_id=admin_user.id, limit=10)
            
            # All logs should belong to the specified user
            for log in logs:
                assert log.user_id == admin_user.id

    def test_get_audit_logs_by_action(self, app, admin_user, sample_audit_logs):
        """Test retrieving audit logs filtered by action."""
        with app.app_context():
            logs = get_audit_logs(action='CREATE', limit=10)
            
            # All logs should have the specified action
            for log in logs:
                assert log.action == 'CREATE'

    def test_get_audit_logs_by_model(self, app, admin_user, sample_audit_logs):
        """Test retrieving audit logs filtered by target model."""
        with app.app_context():
            logs = get_audit_logs(target_model='Manager', limit=10)
            
            # All logs should have the specified target model
            for log in logs:
                assert log.target_model == 'Manager'

    def test_get_audit_logs_with_pagination(self, app, admin_user, sample_audit_logs):
        """Test retrieving audit logs with pagination."""
        with app.app_context():
            # Get first page
            page1 = get_audit_logs(limit=2, offset=0)
            
            # Get second page
            page2 = get_audit_logs(limit=2, offset=2)
            
            # Should have different entries
            assert len(page1) == 2
            assert len(page2) == 2
            
            # Entries should be different (ordered by timestamp)
            assert page1[0].id != page2[0].id

    def test_get_audit_logs_database_error(self, app):
        """Test get_audit_logs handling of database errors."""
        with app.app_context():
            with patch('services.audit_service.AuditLog.query') as mock_query:
                mock_query.side_effect = Exception("DB Error")
                logs = get_audit_logs()
                
                # Should return empty list on database error
                assert logs == []

    def test_get_audit_log_count_all(self, app, admin_user, sample_audit_logs):
        """Test counting all audit logs."""
        with app.app_context():
            count = get_audit_log_count()
            
            assert count == len(sample_audit_logs)

    def test_get_audit_log_count_filtered(self, app, admin_user, sample_audit_logs):
        """Test counting audit logs with filters."""
        with app.app_context():
            count = get_audit_log_count(action='CREATE')
            
            # Count should match filtered logs
            expected_count = len([log for log in sample_audit_logs if log.action == 'CREATE'])
            assert count == expected_count

    def test_get_audit_log_count_database_error(self, app):
        """Test get_audit_log_count handling of database errors."""
        with app.app_context():
            with patch('services.audit_service.AuditLog.query') as mock_query:
                mock_query.side_effect = Exception("DB Error")
                count = get_audit_log_count()
                
                # Should return 0 on database error
                assert count == 0

    def test_cleanup_old_audit_logs(self, app, admin_user, sample_audit_logs):
        """Test cleanup of old audit logs."""
        with app.app_context():
            # Create an old log entry (91 days ago)
            old_timestamp = datetime.utcnow() - timedelta(days=91)
            old_log = AuditLog(
                user_id=admin_user.id,
                action='CREATE',
                target_model='Manager',
                target_id=999,
                timestamp=old_timestamp
            )
            db.session.add(old_log)
            db.session.commit()
            
            # Run cleanup for 90 days
            deleted_count = cleanup_old_audit_logs(days_to_keep=90)
            
            # Should delete the old log
            assert deleted_count == 1
            
            # Verify old log is gone
            remaining_log = AuditLog.query.filter_by(id=old_log.id).first()
            assert remaining_log is None

    def test_cleanup_old_audit_logs_no_old_entries(self, app, admin_user, sample_audit_logs):
        """Test cleanup when no old entries exist."""
        with app.app_context():
            # Run cleanup for 90 days (all logs are recent)
            deleted_count = cleanup_old_audit_logs(days_to_keep=90)
            
            # Should delete nothing
            assert deleted_count == 0

    def test_cleanup_old_audit_logs_database_error(self, app):
        """Test cleanup handling of database errors."""
        with app.app_context():
            with patch('services.audit_service.db.session.commit', side_effect=Exception("DB Error")):
                deleted_count = cleanup_old_audit_logs()
                
                # Should return 0 on database error
                assert deleted_count == 0

    def test_audit_log_to_dict(self, app, admin_user):
        """Test AuditLog to_dict method."""
        with app.app_context():
            # Create audit entry with timestamp
            from datetime import datetime
            test_timestamp = datetime.utcnow()
            
            audit_entry = AuditLog(
                user_id=admin_user.id,
                action='CREATE',
                target_model='Manager',
                target_id=123,
                changes='{"name": "Test"}',
                timestamp=test_timestamp
            )
            
            result = audit_entry.to_dict()
            
            assert result['user_id'] == admin_user.id
            assert result['action'] == 'CREATE'
            assert result['target_model'] == 'Manager'
            assert result['target_id'] == 123
            assert result['changes'] == '{"name": "Test"}'
            assert result['timestamp'] is not None
            assert 'id' in result


@pytest.fixture
def sample_audit_logs(app, admin_user):
    """Create sample audit log entries for testing."""
    with app.app_context():
        db.create_all()  # Ensure tables exist
        
        logs = []
        
        # CREATE actions
        for i in range(3):
            log = AuditLog(
                user_id=admin_user.id,
                action='CREATE',
                target_model='Manager',
                target_id=100 + i,
                changes=json.dumps({'name': f'Manager {i}'})
            )
            db.session.add(log)
            logs.append(log)
        
        # UPDATE action
        log = AuditLog(
            user_id=admin_user.id,
            action='UPDATE',
            target_model='Country',
            target_id=456,
            changes=json.dumps({'name': {'old': 'Old Name', 'new': 'New Name'}})
        )
        db.session.add(log)
        logs.append(log)
        
        # DELETE action
        log = AuditLog(
            user_id=admin_user.id,
            action='DELETE',
            target_model='Achievement',
            target_id=789
        )
        db.session.add(log)
        logs.append(log)
        
        # LOGIN action
        log = AuditLog(
            user_id=admin_user.id,
            action='LOGIN'
        )
        db.session.add(log)
        logs.append(log)
        
        db.session.commit()
        
        yield logs
        
        # Cleanup
        try:
            for log in logs:
                db.session.delete(log)
            db.session.commit()
        except Exception:
            # Ignore cleanup errors
            pass
