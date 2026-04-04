"""Audit service for Shadow Hockey League.

Provides logging functionality for admin actions including CRUD operations,
logins, and cache flushes.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from models import AuditLog, db

logger = logging.getLogger(__name__)


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
    
    try:
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            target_model=target_model,
            target_id=target_id,
            changes=changes_json
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
    offset: int = 0
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
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    target_model: Optional[str] = None
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
    from datetime import datetime, timedelta
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        deleted_count = AuditLog.query.filter(
            AuditLog.timestamp < cutoff_date
        ).delete()
        
        db.session.commit()
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old audit log entries")
        
        return deleted_count
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to cleanup old audit logs: {e}")
        return 0
