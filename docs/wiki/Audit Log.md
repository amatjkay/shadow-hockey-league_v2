# Audit Log

[`services/audit_service.py`](../../services/audit_service.py) is the
single source of truth for "who changed what, when".

## Wiring

- `register_audit_request_hook(app)` is called from
  `app.py::register_extensions` — sets `g.current_user_id` from
  `flask_login.current_user` so production admin CRUD is captured.
- An `after_flush` SQLAlchemy listener emits one `AuditLog` row per
  ORM mutation (insert / update / delete). Deletes also snapshot the
  full row before removal.
- Explicit admin operations (recalc, seed) call
  `audit_service.log_action(action, target, payload)` directly.

## Schema

`AuditLog(id, user_id, action, target_type, target_id, payload_json,
created_at)`. See [`models.py`](../../models.py).

## Querying

- Admin panel: `/admin/auditlog/` (read-only ModelView).
- Tests: `tests/test_audit_service.py`, `tests/test_audit_delete.py`,
  `tests/integration/test_audit_logging.py`.

## Forbidden

- Bypassing the hook in custom views — AGENTS.md § 5 rule.
- Reading the audit table from non-admin code paths.

## See also

- [[Admin Panel]] — every Flask-Admin view inherits the hook.
- [[Caching]] — the hook also drives leaderboard invalidation.
