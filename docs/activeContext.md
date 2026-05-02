# Active Context — Shadow Hockey League v2

> **Purpose:** This file tracks the current focus of work, recent changes, and immediate
> next steps. All agents MUST read this before starting any task.

---

## Current Focus

**Phase:** No active campaign. Audit-2026-04-28 closed; token-efficiency pass merged.
**Status:** `main` is green. Quality & Tests CI passing (415 unit/integration tests). All
backlog Linear tickets either closed or marked Cancelled in the 2026-05-01 cleanup pass.

Next milestone: owner-driven features. No campaign-level work in flight. New tickets
should land in Linear with their own scope; do not assume Phase A→H exists anymore.

---

## Status

- **Branch:** `main` (HEAD `7170317`, post PR #43 merge).
- **Goal:** Maintenance mode. Awaiting next feature/bug request.
- **Seeding Status:** 58 achievements, 42 managers, 5 seasons, baseline 25/26.
- **Live dev server (when running):** `http://127.0.0.1:5000`.

## Recent Changes (post-2026-04-28)

- **PR #32 (TIK-37 / B10)** ✅ merged — `socket_timeout=1.0` in `blueprints/health.py:81`.
- **PR #33 (TIK-38 / B11)** ✅ merged — startup banner derived from `services/metrics_service` constants.
- **PR #34 (TIK-16 / rate-limiter)** ✅ merged — shared `Limiter` in `services/extensions.py` wired across all 15 API endpoints.
- **PR #35 (TIK-17 / scoring)** ✅ merged — `services/scoring_service.py::get_base_points()` is the single source of truth for league/subleague base points.
- **PR #38 (TIK-36 / B9)** ✅ merged — `register_audit_request_hook(app)` populates `g.current_user_id` so admin CRUD writes to `audit_logs`.
- **PR #41 (Phase D / test cleanup)** ✅ merged.
- **PR #42 (TIK-39 + TIK-40 / linter debt)** ✅ merged — mypy + flake8 zero campaign closed.
- **PR #43 (token-efficiency)** ✅ merged — Flask-Compress, JSON minification, long-cache for `/static`, opt-in `?fields=`, N+1 fixes in `services/api.py`. Plus removed `TESTING` gate on Prometheus init and made `reset_metrics()` clean `prometheus_client.REGISTRY`.
- **PR #44 (repo hygiene)** ✅ merged — untracked `mcp-servers/`, `dev.db`, `.env`. New `make mcp-install` target.
- **PR #45 (sub-agents + skills)** ✅ merged — `.agents/agents/{token-auditor,doc-curator}.md`, three skills, `docs/INDEX.md`.

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
- **Rate limiting**: shared `Limiter` lives in `services/extensions.py`. Both `app.py` (`@app.before_request`-style protection of the admin login form) and `services/api.py` (15 API endpoints) use it. Storage is Redis in production, in-memory in dev/test.
- **Subleague scoring**: always go through `services/scoring_service.py::get_base_points(ach_type, league)` — never compare `league.code == "1"` directly. The helper reads `League.base_points_field`, which respects `parent_code` so subleagues `2.1`/`2.2` inherit `base_points_l2` from parent `2`.
- **Audit log**: `register_audit_request_hook(app)` is wired in `app.py::register_extensions`. It populates `g.current_user_id` from `flask_login.current_user` so the existing `after_flush` listener writes to `audit_logs` for admin CRUD. `audit_service.log_action()` is still the explicit API used by `services/recalc_service.py` for non-CRUD events.
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
