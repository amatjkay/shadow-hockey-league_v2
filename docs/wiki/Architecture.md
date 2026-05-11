# Architecture

Stack at a glance: **Nginx → Gunicorn (4 workers) → Flask 3.1 app
factory → SQLAlchemy 2.0 / SQLite + Redis cache**. Diagrams and full
prose live in [docs/ARCHITECTURE.md](../ARCHITECTURE.md) and
[docs/techContext.md](../techContext.md) — read those for the canonical
picture; this note is just the orientation map.

## Top-level layout

- [`app.py`](../../app.py) — application factory (`create_app()`),
  blueprint registration, extension wiring, audit hook.
- [`wsgi.py`](../../wsgi.py) — Gunicorn entrypoint.
- [`config.py`](../../config.py) — `Development` / `Production` / `Testing`
  configs.
- [`models.py`](../../models.py) — all SQLAlchemy 2.0 models.
- [[Blueprints]] — `blueprints/` (routes + templates).
- [[Services]] — `services/` (business logic; packages: `api/`, `admin/`).
- [[Admin Panel]] — Flask-Admin (`services/admin/`).
- [[Caching]] — `services/cache_service.py` + Redis.
- [[Audit Log]] — `services/audit_service.py` + `after_flush` listener.

## Cross-cutting flows

- **Read flow (leaderboard):** `blueprints/main.py::index` →
  cache hit/miss → `services/rating_service` → DB → template render
  → cache fill. See [[Caching]] for the partitioned key contract.
- **Admin mutation flow:** Flask-Admin form → `SHLModelView` →
  `models.py` save → `services/audit_service` `after_flush` → cache
  invalidation via `invalidate_leaderboard_cache()`.
- **REST API flow:** API key auth (`services/api_auth.py`) → rate
  limiter (`services/extensions.py`) → endpoint in
  `services/api/<resource>.py` → JSON response.

## Important constraints

- App factory is the only public entrypoint — **don't** import
  blueprints at module top of `app.py` (circular imports). Use
  `register_blueprints(app)`.
- All admin CRUD must be captured by the audit hook. Bypassing the
  hook is a guardrail violation (AGENTS.md § 2).
- The leaderboard cache key is partitioned by `?season=N` — see
  [[Caching]].

## See also

- [[Models and Database]] — entity overview.
- [[Operations and CI-CD]] — how this is deployed.
