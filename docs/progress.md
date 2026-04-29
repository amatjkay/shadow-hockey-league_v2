# Progress — Shadow Hockey League v2

> **Purpose:** Living document tracking completed work, in-progress tasks, and blockers.
> All agents MUST update this before ending their turn.

## 2026-04-27: Analyst Audit — Documentation & Security

### Completed
- [x] Full repo audit produced (artifact in Devin session). 20 decomposed tasks
      (T-001..T-020) recorded.
- [x] **T-001** — `.env` removed from git tracking; `.gitignore` cleaned of
      stray markdown fences; `.env.example` updated (documented `GEMINI_API_KEY`,
      removed Windows-only DB path). PR #13 → `devin/integration-analyst-fixes`.
- [x] **T-005, T-006, T-018, T-019** — Documentation sync:
      `README.md` season table corrected to `25/26..21/22`; test count `296 → 383`;
      coverage badge dropped (was static, misleading); env-vars table refreshed.
      `docs/ARCHITECTURE.md` test count `381 → 383`. ADR-005 added to
      `docs/decisionLog.md` recording season baseline decision. PR #14 merged into
      `devin/integration-analyst-fixes`.
- [x] **T-002 + T-011** — Rate limiter unified into a single `services.extensions.limiter`
      Flask-Limiter instance bound via `init_app`. Storage URI is read from
      `REDIS_URL` (production) with `memory://` fallback; `RATELIMIT_ENABLED`
      mirrors `TESTING` so test suite isn't slowed by 50/hour defaults.
      `services/api.py` now uses `@limiter.limit("100 per minute")` for all
      15 REST endpoints (was the dead `@api_limiter` instance). Added
      `tests/test_api.py::TestAPIRateLimiting` proving the 101st request to
      `/api/countries` returns 429 (test count `383 → 384`).

### In Progress
- [ ] **T-003 + T-004 + T-007 + T-020** — unify points calculation through
      `League.base_points_field`; expand validation to support subleagues.
- [ ] **T-009** — make `audit_service.log_action` transactionally neutral.
- [ ] **T-008** — defer `ApiKey.last_used_at` writes off the request hot path.
- [ ] **T-010** — drop `with db.session.begin()` in `blueprints/health.py`.

### Blockers
- [!] `GEMINI_API_KEY` and other publicly-committed secrets still live in git
      history. PR #13 untracks the file but does **not** rewrite history. User
      must rotate the Gemini key and decide on `git filter-repo` against `main`.

---

## Completed (Stabilization Phase)

- [x] Create dedicated development branch `fix`.
- [x] Reset primary admin account (`s3ifer`).
- [x] Standardize flag filenames to uppercase (`RUS.png`) for Linux compatibility.
- [x] Synchronize `SeedService` and `RatingService` point calculations.
- [x] Isolate Flask-Admin monkey-patches to `utils/patches.py` (later removed in TIK-34: Flask-Admin 2.0.2 + WTForms 3.2.x no longer require them).
- [x] Externalize Admin Panel JavaScript to `static/js/admin/autofill.js`.
- [x] Fix cache contamination in E2E tests.
- [x] Verify 100% test pass rate (383+ tests).
- [x] Update documentation in NotebookLM and Linear.
- [x] Final manual verification of Admin Panel and Leaderboard.
- [x] Fix database seeding logic and reference data population.
- [x] Case-insensitive flag image resolution (Linux fix).
- [x] Synchronize point system between database and app logic.
- [x] Stabilize environment (Health checks, SQLite concurrency fixes).
- [x] Fix Audit Logging (before_flush/after_flush pattern).
- [x] Implement **[TIK-23]** Real-time duplicate validation for achievements.

- [x] Fix Admin Achievement Management (UI consolidation + auto-calculation).
- [x] Resolve duplicate class definitions in `services/admin.py`.
- [x] Implement integration tests for achievements.
- [x] Finalize icon path resolution and API synchronization.
- [x] Resolve Admin Template recursion (`shl_master.html` fix).
- [x] Standardize Admin endpoints (`admin.login`, `admin.logout`).
- [x] Implement `flush_cache` admin action.
- [x] Synchronize 800/400 point system across all tests and UI.
- [x] Verify 100% test pass rate for all modules (69+ integration tests).
- [x] Merge `fix` into `feature/admin-enhancement` (Stabilization complete).
- [x] Implement and Optimize **Historical Season View**.
- [x] Resolve Admin critical bugs (CSRF protection, UnboundLocalError).
- [x] Consolidate database (removed redundant `instance/dev.db`).
- [x] Perform comprehensive E2E verification of Leaderboard and Admin Panel.

---

## Feature Roadmap

### Priority 1 — Admin Integrity
- [x] Add historical season view.
- [x] **[TIK-23]** Real-time duplicate validation for achievements (prevent same manager+type+season+league).

### Priority 2 — Leaderboard UX
- [x] **[TIK-24]** Player search on leaderboard (client-side, real-time).
- [x] **[TIK-25]** Advanced filtering: by country and achievement type.

### Priority 3 — Admin Tools
- [x] **[TIK-26]** Enhanced audit log visualization.

---

## Project Metrics (as of 2026-04-28)

- **Total Tests:** 388 unit/integration passing (3 pre-existing failures unchanged) +
  42-scenario Playwright e2e smoke + 23/27 deep-probe checks (2 real bugs found,
  see Known Open Issues below).
- **Code Coverage:** ~87% (target threshold).
- **Linting:** Configured (`.flake8`, `mypy` via `pyproject.toml`).
- **Architecture:** Application Factory + blueprints + services. External static assets.

---

## Recent Bugfixes (Diagnostic Pass on `feature/admin-enhancement`)

Driven by manual user verification of `/?season=N` failing on the live dev server.
All bundled in **PR #19** (`devin/1777326827-e2e-bugfixes`):

- **[TIK-27]** B1 — `blueprints/main.py` missing `request` import → homepage 500.
- **[TIK-27]** B2 — `services/admin.py` form_args used unsupported `query_factory`
  on FK fields → Achievement create/edit form 500.
- **[TIK-27]** B3 — `dev.db` `icon_path` referenced `/static/img/icons/...`,
  files lived under `/static/img/cups/...` → trophy 404s on leaderboard.
- **[TIK-27]** B4 — `@cache.cached(key_prefix='leaderboard')` was a static
  string, so `?season=` variants shared a cache bucket. Switched to a callable
  key + `cache.clear()` on invalidation.
- **[TIK-28]** B6 — `RatingService.build_leaderboard()` accepted `season_id`
  but never filtered on it; the dropdown looked broken even after B1/B4.
- **[TIK-29]** B7 — `templates/index.html` season dropdown was hard-coded to
  three seasons; replaced with dynamic rendering from the `Season` table.
- **[TIK-29]** B8 — `dev.db` shipped with only 18 of 49 achievements (no
  BEST_REG, no HOCKEY_STICKS_AND_PUCK). Re-seeded from the canonical
  `data/seed/achievements.json`.

Follow-up data-only PR **#20**:

- **[TIK-30]** Add 9 Shadow 1 league (Elite) 24/25 awards. Prod was missing the
  same data; user dictated the winners (TOP1 Vyacheslav Shamanov, TOP2/BEST
  whiplash 92, TOP3 Сергей Стрельченко, R3 Павел Роевнев, R1 Nurzhan
  Yessengaliev / AleX TiiKii / Igor Kadzayev / Oleg Karandashov).

Tooling PR **#21**:

- **[TIK-31]** Playwright e2e smoke suite (`tests/e2e/test_smoke.py`). Manual
  run against a live dev server: 42-scenario walk through public pages, REST
  API auth contract, every Flask-Admin model view (list / new / first-row
  edit), admin extras, and a console-error budget. `tests/e2e/conftest.py`
  excludes the script from `pytest` auto-collection so CI is unaffected.

Tooling rollup PR **#22**:

- **[TIK-32]** B5 — jQuery race in `templates/admin/shl_master.html`: removed
  the dead Select2 locale-init script from `head_meta` (it ran before parent
  template's jQuery, throwing `$ is not defined` in console). Functionality
  was unaffected; this is purely cleanup. Console errors on admin pages
  dropped from 2 to 0.

Rollup PR **#23**:

- Cherry-pick of TIK-30/31/32 onto `feature/admin-enhancement` (the original
  PR stack #20/#21/#22 each merged into PR #19's staging branch instead of
  `feature/admin-enhancement`, leaving the contents stranded). PR #23 is the
  single merge commit that brings them in.

## Known Open Issues

### From deep-probe e2e (2026-04-28, /tmp/e2e_artifacts/deep/BUGS.md)

- **B9 [P1]** ✅ FIXED (TIK-36 / Phase 3 audit-2026-04-28) — added
  `register_audit_request_hook(app)` in `services/audit_service.py` and
  wired it from `app.py::register_extensions` right after `init_admin`.
  The hook is a `@app.before_request` handler that reads
  `flask_login.current_user` and forwards the authenticated admin's id
  into `g.current_user_id`, so the existing `after_flush` listener now
  actually writes to `audit_logs` for admin CRUD. Regression tests in
  `tests/integration/test_audit_logging.py::TestAuditRequestHook` cover
  (1) the hook is registered by `create_app`, (2) anonymous requests
  leave `g.current_user_id` unset, and (3) `set_current_user_for_audit`
  populates `g` correctly inside a request context.
- **B10 [P2]** ✅ FIXED (TIK-37 / Phase 2B audit-2026-04-28) — added
  `socket_timeout=1.0` to `redis.Redis(...)` in `blueprints/health.py:81`
  with regression test
  `tests/test_blueprints.py::test_health_endpoint_redis_client_uses_socket_timeout`
  asserting both `socket_timeout` and `socket_connect_timeout` are passed
  with sensible bounds (≤2s).
- **B11 [P3]** ✅ FIXED (TIK-38 / Phase 2B audit-2026-04-28) — banner in
  `app.py:233-245` now lists the four `shadow_hockey_league_*` metrics
  that `prometheus_flask_exporter` actually emits (verified locally via
  `curl /metrics`) plus a note about `prometheus_client` defaults.

### Carried over

- **PR #15** closed (dev-cleanup, not needed).
- **PR #16** closed → replaced by **PR #34** (rate-limiter, merged).
- **PR #17** closed → replaced by **PR #35** (subleague scoring, merged).
- **PR #18** (transactional audit) — still open against
  `devin/integration-analyst-fixes`. Has a known latent bug found by
  Devin Review («flush() without SAVEPOINT after error leaves session
  in needs-rollback state») that needs a follow-up commit before merge.
  Not blocking the audit-2026-04-28 closure.

---

## Repo Audit & Triage (2026-04-28)

### What was done
- Created audit analysis document summarising repo state (branches, PRs, Linear tickets).
- **Linear tickets created:** TIK-36, TIK-37, TIK-38.
- **Linear tickets cancelled:** TIK-12, TIK-18, TIK-19 (obsolete / superseded).
- **Linear ticket completed:** TIK-16 marked done.
- **PRs closed:** #11, #15, #28 (stale or superseded).
- **Branch cleanup:** 16 stale branches deleted.

### What's left
- **Phase 2B** ✅ landed (TIK-37 / TIK-38 via PR #32, #33).
- **Phase 2C** ✅ landed (rate-limiter via PR #34, subleague scoring via PR #35).
- **Phase 3** ✅ landed (TIK-36 audit-log wiring via PR #38). All B-bugs from
  the deep-probe e2e triage are now resolved.
- **Phase 4** ⏳ linter debt (mypy/flake8) — documentation + Linear epics, no code.
  Tracked in `docs/audits/audit-2026-04-28-plan.md` Phase 4. This is the only
  remaining audit work.

### Post-audit testing campaign (started 2026-04-29)
Owner-requested follow-up to validate the post-fix state:
- **Phase A** docs sync (this update + audit-2026-04-28-plan.md update).
- **Phase B** Linear sync — close TIK-36/37/38, create epic for the audit.
- **Phase C** Test inventory — categorize every test by type
  (`docs/audits/test-inventory-2026-04-28.md`).
- **Phase D** Test optimization — dedupe fixtures, refactor slow tests,
  fix flakies (touches only `tests/`).
- **Phase E** Gap analysis — compare coverage vs B1–B11 + new sub-systems
  (rate-limiter, scoring helper, audit hook); add missing regression tests.
- **Phase F** Mass run — `pytest tests/` + `pytest tests/e2e` (Playwright)
  on local Flask + Redis.
- **Phase G** Linter debt (= audit Phase 4).
- **Phase H** Issue capture — every problem found in C–G filed as Linear ticket.

### New blockers
- None identified.

---

_Last updated: 2026-04-29 — Phase A docs sync._
