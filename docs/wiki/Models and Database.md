# Models and Database

All models live in a single [`models.py`](../../models.py). SQLAlchemy 2.0
declarative, type-hinted (mypy gate enforced — TIK-53).

## Key entities

- **Country** — flag asset normalised to uppercase code (e.g. `RUS.png`).
- **Manager** — solo or tandem participant; auto-badge on tandems.
- **League** — top-level league + subleagues (League 2 / 2.1 / 2.2).
- **Season** — has a `multiplier` (see [[Business Rules]]).
- **AchievementType** — `code`, `base_points_l1`, `base_points_l2`,
  icon path via `get_icon_url()`.
- **Achievement** — *fact*: `(manager, season, league, achievement_type)`.
  Auto-calculated `points` via `on_model_change` (server-side, never
  client).
- **AuditLog** — captures every admin mutation; see [[Audit Log]].
- **APIKey** — read / write / admin scope; see [[REST API]].
- **User** — Flask-Login admin user.

## Conventions

- **Type hints:** mandatory for every new field / method (TIK-53).
- **`is_active`:** soft-delete flag on `Country`, `League`,
  `Manager`, `AchievementType` (added via inspector-based migration —
  see [[Migrations]]).
- **`__str__`:** every model has a deterministic `__str__` used by
  Flask-Admin; covered by `tests/test_model_str.py`.

## Tooling

- Read-only schema check: `sqlite3 dev.db '.schema <table>'`.
- Schema parity test: `tests/test_migrations_schema_parity.py`
  (ensures `db.create_all()` and `alembic upgrade head` converge).
- Diagrams: see [docs/ARCHITECTURE.md](../ARCHITECTURE.md).

## See also

- [[Migrations]] — Alembic conventions.
- [[Caching]] — what to invalidate after a mutation.
- [[Audit Log]] — what gets logged automatically.
