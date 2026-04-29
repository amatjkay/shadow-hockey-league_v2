# Technical Context — Shadow Hockey League v2

## Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                        Nginx (SSL)                           │
│                    shadow-hockey-league.ru                    │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                   Gunicorn (4 workers)                        │
│                     wsgi.py → app.py                          │
├──────────────────────────────────────────────────────────────┤
│  Flask 3.1+ Application (Application Factory Pattern)        │
│                                                              │
│  ┌─────────────┐  ┌──────────────────┐  ┌──────────────┐    │
│  │ Blueprints  │  │     Services     │  │    Models    │    │
│  │  main.py    │  │ rating_svc       │  │   models.py  │    │
│  │  health.py  │  │ cache_svc        │  │ (SA 2.0)     │    │
│  │  admin_api  │  │ audit_svc        │  │              │    │
│  └─────────────┘  │ api_auth         │  └──────┬───────┘    │
│                   │ admin.py         │         │            │
│                   │ recalc_svc       │         │            │
│                   │ scoring_svc ★    │         │            │
│                   │ extensions ★     │         │            │
│                   │ metrics_svc      │         │            │
│                   └──────────────────┘         │            │
│           ★ = added/refactored in audit-2026-04-28          │
├──────────────────────────────────────────────┼──────────────┤
│                                              ▼              │
│  ┌──────────────┐                   ┌────────────────┐      │
│  │ Redis Cache  │                   │  SQLite (dev.db)│      │
│  │ (fallback:   │                   │  + Alembic      │      │
│  │  SimpleCache)│                   │    migrations   │      │
│  └──────────────┘                   └────────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology | Version |
| :--- | :--- | :--- |
| Language | Python | 3.10+ |
| Framework | Flask | 3.1+ |
| ORM | SQLAlchemy | 2.0+ |
| Database | SQLite | — |
| Migrations | Alembic | 1.14+ |
| Caching | Redis (Flask-Caching) | 5.0+ |
| Admin Panel | Flask-Admin | 2.0.2 |
| Auth | Flask-Login | 0.6+ |
| Forms/CSRF | Flask-WTF / WTForms | 3.0+ |
| Rate Limiting | Flask-Limiter | 3.5+ |
| Metrics | prometheus-flask-exporter | 0.23+ |
| WSGI Server | Gunicorn | 23.0+ |
| Web Server | Nginx | — |
| OS | Ubuntu 22.04 LTS | — |
| CI/CD | GitHub Actions | — |
| Testing | pytest + pytest-cov + xdist | 9.0+ |
| Frontend | Jinja2 + Vanilla CSS/JS | — |

---

## MCP Servers (8 Connected)

| Server | Purpose | Constraint |
| :--- | :--- | :--- |
| `filesystem` | Read/write files in project root | Scoped to `/home/tiki/dev/shadow-hockey-league_v2` |
| `github` | Repository operations, PRs, issues | Token-authenticated |
| `sqlite` | Direct query access to `dev.db` | **Read-only by default** (see AGENTS.md) |
| `context7` | Fresh library/framework documentation | API-key authenticated |
| `duckduckgo` | Web search | No auth required |
| `sequential-thinking` | Structured problem decomposition | Stateless |
| `notebooklm` | Research notebooks, source management | Cookie-authenticated |
| `linear` | Task/issue management (TIK- prefix) | API-key authenticated |

---

## Database Schema (Key Models)

| Model | Table | Key Relationships |
| :--- | :--- | :--- |
| `AdminUser` | `admin_users` | Roles: super_admin, admin, moderator, viewer |
| `ApiKey` | `api_keys` | Scopes: read, write, admin |
| `Country` | `countries` | → managers (1:N) |
| `Manager` | `managers` | → country (N:1), → achievements (1:N) |
| `Achievement` | `achievements` | → manager, type, league, season (all N:1) |
| `AchievementType` | `achievement_types` | Base points for L1 and L2 |
| `League` | `leagues` | Self-referential parent (subleagues) |
| `Season` | `seasons` | Multiplier for point decay |
| `AuditLog` | `audit_logs` | → user_id; tracks all admin actions |

### Critical Constraints

- `Achievement` has a unique constraint on `(manager_id, type_id, league_id, season_id)`
- `Country` deletion restricted if managers exist (`ondelete='RESTRICT'`)
- `Manager` deletion cascades to achievements (`ondelete='CASCADE'`)
- At least one season must remain active

---

## Library Compatibility (Historical)

Earlier revisions carried a `utils/patches.py` shim that monkey-patched two
Flask-Admin / WTForms quirks. **The shim was removed in TIK-34** because both
upstream issues are now handled natively by the pinned versions:

1. **`BaseView._run_view`** — Flask-Admin **2.0.2** ships with the `cls=self`
   compatibility fallback in `flask_admin/base.py`. The custom patch was a
   no-op against the current pin.
2. **`Field.__init__`** — Flask-Admin no longer forwards `allow_blank` to
   WTForms **3.2.x** base fields, so stripping the kwarg is unnecessary.

If a future bump re-introduces either incompatibility, restore a small
`utils/patches.py` and call `apply_patches()` from `create_app()` **before**
`init_admin(app)`. The 42/42 Playwright smoke suite (`tests/e2e/test_smoke.py`)
plus the 388 unit/integration tests are the regression net for this area.

---

## Development Commands

```bash
make setup      # Install deps + init DB
make run        # Dev server (port 5000)
make test       # Run 388 unit/integration tests (excludes tests/e2e)
make lint       # Flake8
make format     # Black + isort
make clean      # Remove temp files
make audit      # Data integrity verification
make benchmark  # Performance latency check
```

---

## Environment Variables

| Variable | Required | Default |
| :--- | :--- | :--- |
| `FLASK_ENV` | No | `development` |
| `DATABASE_URL` | No | `sqlite:///dev.db` |
| `SECRET_KEY` | Yes | Auto-generated |
| `REDIS_URL` | No | `redis://localhost` |
| `ENABLE_API` | No | `True` |
| `API_KEY_SECRET` | Yes | — |
| `WTF_CSRF_SECRET_KEY` | Yes | — |

---

## Test Layout

| Path | What | How to run |
| :--- | :--- | :--- |
| `tests/` (root) | Unit tests | `pytest --ignore=tests/e2e -q` |
| `tests/integration/` | Integration tests against in-memory app | same |
| `tests/e2e/test_smoke.py` | Playwright smoke (42 scenarios) | requires a live dev server, see `PROJECT_KNOWLEDGE.md` §5 |

`tests/e2e/conftest.py` sets `collect_ignore_glob = ["*.py"]` so the smoke suite never runs under `pytest` auto-collection.

A full categorical inventory (unit / integration / regression / UI / e2e) is planned at `docs/audits/test-inventory-2026-04-29.md` (post-audit testing campaign Phase C — not yet created; tracked by TIK-41).

---

## Audit-2026-04-28 — affected modules

The following modules were touched (or added) during the audit remediation. Future agents should keep the contracts below stable; changes require a new audit entry.

| Module | Why it matters | Owner of contract |
| :--- | :--- | :--- |
| `services/extensions.py` | Single shared `Limiter` instance. Both `app.py` and `services/api.py` import the same object — do **not** create another `Limiter()`. | PR #34 |
| `services/scoring_service.py` | `get_base_points(ach_type, league)` is the only correct way to look up base points. It reads `League.base_points_field`, which honours `parent_code` so subleagues inherit from parent. **Never** compare `league.code == "1"`. | PR #35 |
| `services/audit_service.py` | `register_audit_request_hook(app)` MUST be called from `app.py::register_extensions` after `init_admin`. Without it the `after_flush` listener silently drops audit rows. | PR #38 |
| `services/metrics_service.py` | `METRICS_PREFIX` + `DEFAULT_METRIC_SUFFIXES` are the single source of truth for `/metrics` names. The startup banner derives from them — never hard-code metric names elsewhere. | PR #33 |
| `blueprints/health.py` | `redis.Redis(...)` MUST pass both `socket_connect_timeout` and `socket_timeout`. Otherwise `/health` blocks for ~5–7s when Redis is degraded. | PR #32 |
| `services/validation_service.py` | League-code validator: format regex `^[1-9]\d*(\.\d+)?$` plus business rule that L1 is flat (no `1.x`). | PR #35 |

---

Last updated: 29 апреля 2026 г.
