"""Audit service for Shadow Hockey League.

Provides logging functionality for admin actions including CRUD operations,
logins, and cache flushes.
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Any, Optional

from flask import g
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from models import AuditLog, db

logger = logging.getLogger(__name__)

# Thread-safe lock for audit operations
_audit_lock = threading.Lock()


def log_action(
    user_id: int,
    action: str,
    target_model: Optional[str] = None,
    target_id: Optional[int] = None,
    changes: Optional[dict[str, Any]] = None,
) -> Optional[AuditLog]:
    """Log an admin action to the audit trail.

    Args:
        user_id: ID of the admin user performing the action
        action: Type of action (CREATE, UPDATE, DELETE, LOGIN, FLUSH_CACHE)
        target_model: Name of the model being acted upon (e.g., 'Manager')
        target_id: Primary key of the target record
        changes: Dictionary of changes for UPDATE actions

    Returns:
        AuditLog entry if successful, None if logging failed

    Raises:
        ValueError: If required parameters are invalid
    """
    if not user_id:
        raise ValueError("user_id is required")

    if not action or len(action) > 50:
        raise ValueError("action is required and must be <= 50 characters")

    if target_model and len(target_model) > 50:
        raise ValueError("target_model must be <= 50 characters")

    # Convert changes dict to JSON string for storage
    changes_json = None
    if changes is not None:
        try:
            changes_json = json.dumps(changes, default=str)
        except (TypeError, ValueError) as e:
            logger.warning(f"Failed to serialize changes to JSON: {e}")
            changes_json = json.dumps({"error": "Failed to serialize changes"})

    # Thread-safe database operation
    with _audit_lock:
        try:
            audit_entry = AuditLog(
                user_id=user_id,
                action=action,
                target_model=target_model,
                target_id=target_id,
                changes=changes_json,
            )

            db.session.add(audit_entry)
            db.session.commit()

            logger.info(f"Audit log entry created: {action} by user {user_id}")
            return audit_entry

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Failed to create audit log entry: {e}")
            # Fallback to regular logging
            logger.info(f"ACTION LOG: {action} by user {user_id} on {target_model}#{target_id}")
            return None

        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error creating audit log entry: {e}")
            return None


def get_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    target_model: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Retrieve audit log entries with optional filtering.

    Args:
        user_id: Filter by specific user ID
        action: Filter by action type
        target_model: Filter by target model
        limit: Maximum number of entries to return
        offset: Number of entries to skip

    Returns:
        List of audit log entries ordered by timestamp (newest first)
    """
    try:
        query = AuditLog.query

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        if action:
            query = query.filter(AuditLog.action == action)

        if target_model:
            query = query.filter(AuditLog.target_model == target_model)

        return query.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset).all()

    except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve audit logs: {e}")
        return []


def get_audit_log_count(
    user_id: Optional[int] = None, action: Optional[str] = None, target_model: Optional[str] = None
) -> int:
    """Get count of audit log entries matching filters.

    Args:
        user_id: Filter by specific user ID
        action: Filter by action type
        target_model: Filter by target model

    Returns:
        Count of matching audit log entries
    """
    try:
        query = AuditLog.query

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        if action:
            query = query.filter(AuditLog.action == action)

        if target_model:
            query = query.filter(AuditLog.target_model == target_model)

        return query.count()

    except SQLAlchemyError as e:
        logger.error(f"Failed to count audit logs: {e}")
        return 0


def cleanup_old_audit_logs(days_to_keep: int = 90) -> int:
    """Remove audit log entries older than specified number of days.

    Args:
        days_to_keep: Number of days to keep logs (default: 90)

    Returns:
        Number of entries deleted
    """
    from datetime import datetime, timedelta, timezone

    try:
        # Use naive UTC datetime to match database (which stores naive datetimes)
        cutoff_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days_to_keep)

        deleted_count = AuditLog.query.filter(AuditLog.timestamp < cutoff_date).delete()

        db.session.commit()

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old audit log entries")

        return deleted_count

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to cleanup old audit logs: {e}")
        return 0


# SQLAlchemy Event Listeners for automatic audit logging
def setup_audit_events():
    """Setup SQLAlchemy event listeners for automatic audit logging."""

    # Enable foreign key constraints for SQLite
    @event.listens_for(db.engine, "connect")
    def set_sqlite_pragma(dbapi_connection, _connection_record):
        if "sqlite" in str(db.engine.url):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    @event.listens_for(Session, "after_flush")
    def after_flush(session, _context):
        """Log changes after session flush."""
        try:
            # Get current user from Flask context
            current_user_id = getattr(g, "current_user_id", None)
            if not current_user_id:
                return  # Skip if no authenticated user

            # Process all new, dirty, and deleted objects
            for obj in session.new:
                _log_model_change(session, current_user_id, "CREATE", obj)

            for obj in session.dirty:
                _log_model_change(session, current_user_id, "UPDATE", obj)

            for obj in session.deleted:
                _log_model_change(session, current_user_id, "DELETE", obj)

        except Exception as e:
            logger.error(f"Error in audit event listener: {e}")


def _log_model_change(session: Session, user_id: int, action: str, obj: Any) -> None:
    """Log a model change to audit trail."""
    try:
        # Skip audit log entries themselves to avoid infinite loops
        if obj.__class__.__name__ == "AuditLog":
            return

        # Get model name and ID
        model_name = obj.__class__.__name__
        model_id = getattr(obj, "id", None)

        changes = None
        if action == "UPDATE":
            # Capture changes for UPDATE operations
            changes = {}
            state = db.inspect(obj)

            # Get all attributes that have changed
            for attr in state.mapper.column_attrs:
                if attr.key in state.unloaded:
                    continue

                history = state.get_history(attr.key, passive=True)
                if history.has_changes():
                    old_value = history.deleted[0] if history.deleted else None
                    new_value = history.added[0] if history.added else None

                    if old_value != new_value:
                        changes[attr.key] = {"old": old_value, "new": new_value}

        elif action == "DELETE":
            # Capture full snapshot for DELETE operations
            changes = {}
            state = db.inspect(obj)
            for attr in state.mapper.column_attrs:
                # Capture all column values as they currently stand
                changes[attr.key] = getattr(obj, attr.key)

        # Create audit log entry
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            target_model=model_name,
            target_id=model_id,
            changes=json.dumps(changes) if changes else None,
        )

        # Add to session (but don't flush to avoid recursion)
        session.add(audit_entry)

    except Exception as e:
        logger.error(f"Error logging model change: {e}")


def set_current_user_for_audit(user_id: Optional[int]) -> None:
    """Set current user ID for audit logging in Flask context."""
    g.current_user_id = user_id


def register_audit_request_hook(app: Any) -> None:
    """Wire ``set_current_user_for_audit`` into Flask's request lifecycle.

    Without this hook ``g.current_user_id`` is only ever populated from the
    test suite, so the ``after_flush`` listener in :func:`setup_audit_events`
    short-circuits in production and ``audit_logs`` stays empty for every
    admin CRUD action — see audit-2026-04-28 finding **B9 / TIK-36**.

    The hook reads ``flask_login.current_user`` (already populated by
    Flask-Login's own ``before_request`` handler) and forwards the
    authenticated user's id into ``flask.g``. Anonymous requests are a no-op
    so public read endpoints don't pay the cost of writing audit rows.

    Args:
        app: Flask application instance. Must have Flask-Login initialised
            already (i.e. call this after ``init_admin``).
    """
    from flask_login import current_user

    @app.before_request
    def _populate_audit_user() -> None:
        try:
            if current_user.is_authenticated:
                set_current_user_for_audit(int(current_user.get_id()))
        except Exception as exc:
            # Never let audit plumbing break a real request: log and move on.
            logger.warning("Could not set audit user from current_user: %s", exc)
