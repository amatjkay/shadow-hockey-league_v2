# Active Context — Shadow Hockey League v2

> **Purpose:** This file tracks the current focus of work, recent changes, and immediate
> next steps. All agents MUST read this before starting any task.

---

## Current Focus

**Phase:** No active campaign. TIK-42 cleanup epic closed (PR #55 merged 2026-05-03).
**Status:** `main` is green. Quality & Tests CI passing (423 unit/integration tests).
Linear backlog empty (all 41 tickets in Tikispace team are Done or Canceled). 3 split
packages (`services/api`, `blueprints/admin_api`, `services/admin`) smoke-tested live.

Next milestone: owner-driven features. No campaign-level work in flight. New tickets
should land in Linear with their own scope.

---

## Status

- **Branch:** `main` (HEAD `511b152`, post PR #55 merge).
- **Goal:** Maintenance mode. Awaiting next feature/bug request.
- **Seeding Status:** 58 achievements, 42 managers, 5 seasons, baseline 25/26.
- **Live dev server (when running):** `http://127.0.0.1:5000`.

## Recent Changes (post-2026-04-28)

- **PR #32-#42** ✅ merged — see `docs/archive/progress-pre-2026-04-29.md` for the per-ticket history of TIK-16/17/36/37/38/39/40 and Phase D test cleanup.
- **PR #43 (token-efficiency)** ✅ merged — Flask-Compress, JSON minification, long-cache for `/static`, opt-in `?fields=`, N+1 fixes in `services/api.py`. Plus removed `TESTING` gate on Prometheus init and made `reset_metrics()` clean `prometheus_client.REGISTRY`.
- **PR #44 (repo hygiene)** ✅ merged — untracked `mcp-servers/`, `dev.db`, `.env`. New `make mcp-install` target.
- **PR #45 (sub-agents + skills)** ✅ merged — `.agents/agents/{token-auditor,doc-curator}.md`, three skills, `docs/INDEX.md`.
- **PR #46 (docs sync 2026-05-01)** ✅ merged — retired Phase A→H plan; backlog drained.
- **PR #47-#54 (TIK-43..TIK-50)** ✅ merged via **PR #55 (TIK-42 epic)** on 2026-05-03 — dead code purge, CC reduction, 3 monolith→package splits, test dedup, scratch archive, coverage boost. Net: 423 tests / 84% coverage / 0 files > 600 LOC / 0 functions ≥ CC D.

---

## Immediate Next Steps

- [x] All audit-2026-04-28 phases (2A → G) closed.
- [x] All backlog Linear tickets either Done or Cancelled (2026-05-01 cleanup).
- [ ] **Owner action — secret rotation.** `.env` was tracked in git history before PR #44.
  Rotate `GEMINI_API_KEY` at Google AI Studio; regenerate `SECRET_KEY`,
  `WTF_CSRF_SECRET_KEY`, `API_KEY_SECRET` (32+ char random) and replace in local `.env`.
  Decide whether to run `git filter-repo` to scrub history (irreversible, breaks any open
  forks/PRs). Tracked in `docs/progress.md` 2026-05-01 entry as a blocker.

---

## Active Blockers

- **[Owner-action] Secret rotation** — see «Immediate Next Steps» above. Untracking the
  file does not rewrite history.

---

## Notes for Next Agent

- **Flask-Admin compatibility**: Flask-Admin 2.0.2 ships with the `cls=self` fallback in `BaseView._run_view`, and WTForms 3.2.x no longer accepts `allow_blank` on the base `Field`. The previous `utils/patches.py` shim is therefore obsolete and was removed in TIK-34. If a future upgrade re-introduces the incompatibility, restore the patch and call it from `create_app()` before `init_admin(app)`.
- **Admin JS**: Shared logic is in `static/js/admin/autofill.js`.
- **Rate limiting**: shared `Limiter` lives in `services/extensions.py`. Both `app.py` (`@app.before_request`-style protection of the admin login form) and the `services/api/` package (15 API endpoints across `countries.py`, `managers.py`, `achievements.py`) use it. Storage is Redis in production, in-memory in dev/test. Admin-side login throttling lives in `services/admin/_rate_limit.py`.
- **Subleague scoring**: always go through `services/scoring_service.py::get_base_points(ach_type, league)` — never compare `league.code == "1"` directly. The helper reads `League.base_points_field`, which respects `parent_code` so subleagues `2.1`/`2.2` inherit `base_points_l2` from parent `2`.
- **Audit log**: `register_audit_request_hook(app)` is wired in `app.py::register_extensions`. It populates `g.current_user_id` from `flask_login.current_user` so the existing `after_flush` listener writes to `audit_logs` for admin CRUD. `audit_service.log_action()` is still the explicit API used by `services/recalc_service.py` for non-CRUD events.
- **Admin views**: All `ModelView` subclasses live in `services/admin/views.py` (Country, League, Season, Manager, Achievement, AuditLog, SystemControl). Base class `SHLModelView` is in `services/admin/base.py`. `init_admin(app)` lives in `services/admin/__init__.py` and is the single entrypoint called from `app.py`.
- **Public API**: `services/api/` is a package; routes are split per resource (`countries.py`, `managers.py`, `achievements.py`) and registered onto a single `api` Blueprint created in `services/api/__init__.py`. Admin-side lookup endpoints are in `blueprints/admin_api/lookups.py`.
- **Prometheus metrics**: `services/metrics_service.py` is a singleton. `app.py::register_extensions` initialises it unconditionally (even under `TESTING`); `reset_metrics()` cleans `prometheus_client.REGISTRY` so test fixtures can rebind cleanly. Production behaviour is unchanged — `TESTING=False` there.
- **HTTP compression**: Flask-Compress is wired in `app.py::register_extensions` (br + gzip, level 6, `>=500 B`). Disabled in `TESTING` so `test_client` responses stay byte-comparable.
- **`?fields=` projection**: opt-in only, plumbed through `paginate_query` for listing endpoints (`GET /api/managers`, `GET /api/achievements`, ...). Single-record endpoints (`/<id>`) still return the full record.
- **Testing**:
  - Unit/integration: `venv/bin/pytest --ignore=tests/e2e -n auto`. ~70s, expect 415 pass.
  - Smoke e2e: requires a running dev server; see PROJECT_KNOWLEDGE.md §5 for the exact command.
- **Database**: `dev.db` is the primary SQLite database (now untracked); recreate locally via `make init-db`. Schema checks via the `sqlite` MCP server are recommended before any mutation.
- **Cache key**: any new `@cache.cached` decorator that varies by query-string MUST use a callable `key_prefix` (see `blueprints/main.py::index`).
- **mcp-servers/**: untracked since PR #44. Reinstate via `make mcp-install`.

---

_Last updated: 2026-05-01 — post-cleanup sync (PR #43 merged, audit closed, backlog drained)._
