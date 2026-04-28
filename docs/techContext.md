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
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ Blueprints  │  │   Services   │  │     Models       │    │
│  │  main.py    │  │ rating_svc   │  │   models.py      │    │
│  │  health.py  │  │ cache_svc    │  │ (SQLAlchemy 2.0) │    │
│  │  admin_api  │  │ audit_svc    │  │                  │    │
│  └─────────────┘  │ api_auth     │  └────────┬─────────┘    │
│                   │ admin.py     │           │              │
│                   │ recalc_svc   │           │              │
│                   └──────────────┘           │              │
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
| `PROXY_FIX_X_FOR` | No | `0` |
| `FLASK_RUN_HOST` | No | `127.0.0.1` |

---

## Test Layout

| Path | What | How to run |
| :--- | :--- | :--- |
| `tests/` (root) | Unit tests | `pytest --ignore=tests/e2e -q` |
| `tests/integration/` | Integration tests against in-memory app | same |
| `tests/e2e/test_smoke.py` | Playwright smoke (42 scenarios) | requires a live dev server, see `PROJECT_KNOWLEDGE.md` §5 |

`tests/e2e/conftest.py` sets `collect_ignore_glob = ["*.py"]` so the smoke suite never runs under `pytest` auto-collection.

---

Last updated: 28 апреля 2026 г.
