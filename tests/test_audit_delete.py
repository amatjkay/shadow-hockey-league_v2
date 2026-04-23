import pytest
import json
from flask import g
from models import db, Country, AuditLog
from services.audit_service import set_current_user_for_audit

def test_audit_log_snapshot_on_delete(app, db_session, admin_user):
    """
    Test that deleting a record captures a full snapshot of its data in AuditLog.
    Linked to TIK-5.
    """
    # 1. Setup: Use the admin_user fixture
    set_current_user_for_audit(admin_user.id)
    
    country = Country(code="TST", name="TestCountry", flag_path="/static/TST.png")
    db_session.add(country)
    db_session.commit()
    
    country_id = country.id
    
    # 2. Action: Delete the country
    db_session.delete(country)
    db_session.commit()
    
    # 3. Verification: Check AuditLog
    audit_entry = AuditLog.query.filter_by(
        action='DELETE', 
        target_model='Country', 
        target_id=country_id
    ).first()
    
    assert audit_entry is not None, "Audit log entry for DELETE was not created"
    assert audit_entry.user_id == admin_user.id
    
    # Parse changes JSON
    changes = json.loads(audit_entry.changes)
    assert isinstance(changes, dict)
    assert changes['code'] == "TST"
    assert changes['name'] == "TestCountry"
    assert 'id' in changes
    
    print(f"\n[TIK-5] Verified snapshot for DELETE: {changes}")

def test_audit_log_no_user_no_log(app, db_session):
    """Test that no audit log is created if no user is set in context."""
    set_current_user_for_audit(None)
    
    country = Country(code="EMP", name="EmptyUserCountry", flag_path="/static/EMP.png")
    db_session.add(country)
    db_session.commit()
    
    # Check no AuditLog was created for this action
    audit_count = AuditLog.query.filter_by(target_model='Country', target_id=country.id).count()
    assert audit_count == 0
