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

## Known Compatibility Patches

Flask-Admin 2.0.2 has two known incompatibilities that are monkey-patched in `services/admin.py`:

1. **`BaseView._run_view`** — Passes `cls=self` to view functions, but they don't accept it.
   Patched to call `f(self, *args, **kwargs)` without the `cls` keyword.
2. **`Field.__init__`** — Flask-Admin passes `allow_blank` to WTForms 3.x fields, which reject it.
   Patched to strip `allow_blank` from kwargs before calling the original `__init__`.

> ⚠️ These patches are critical for admin panel stability. Do not remove without testing.

---

## Development Commands

```bash
make setup      # Install deps + init DB
make run        # Dev server (port 5000)
make test       # Run 383+ tests
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

Last updated: 23 апреля 2026 г. (Post-Optimization Build)
