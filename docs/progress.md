# Progress — Shadow Hockey League v2

> **Purpose:** Tracking long-term project milestones and feature progress.

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

- **B9 [P1]** — admin audit log is not actually written in production.
  `services/audit_service.py:213-220` early-returns unless `g.current_user_id`
  is set, and `set_current_user_for_audit()` is only called from tests — no
  production code path populates it. `audit_logs` table is empty even after
  multiple admin CRUD operations. Directly contradicts AGENTS.md §5 mandate
  "All admin CRUD actions logged via `audit_service.log_action()`". Fix is
  ~10 LoC (Flask-Login `before_request` hook).
- **B10 [P2]** — `/health` blocks ~7s when Redis is unreachable. Caused by
  `redis_client.ping()` in `blueprints/health.py:71-94` lacking a
  `socket_timeout`; only `socket_connect_timeout=2` is set, but cumulative
  retries push wall time well past that. Production unaffected (Redis is
  available there); dev/staging/CI without Redis lose health-probe usefulness.
- **B11 [P3]** — `app.py` startup banner advertises
  `http_requests_total, http_request_duration_seconds` as default metrics,
  but `/metrics` only emits the duration histogram. Either add the counter
  or fix the banner string.

### Carried over

- **PR #15 / #16 / #17 / #18** — earlier integration-fix work (docs sync,
  rate-limiter Redis storage, `base_points` unification, transaction-neutral
  audit), open against `devin/integration-analyst-fixes`. Awaiting user
  review/merge decision. PR #18 also has a known latent bug found by Devin
  Review («flush() without SAVEPOINT after error leaves session in
  needs-rollback state») that needs a follow-up commit before merge.

---

## Audit 2026-04-28 — Analysis Pass (this PR #31)

Analytical-only PR (no application code touched). Artifacts under `docs/audits/`:

- `audit-2026-04-28-analysis.md` — validation of all external audit claims
  against `main` HEAD `ff6bca0`, with file:line evidence; decomposition into
  ≤1h tasks (groups V/A/B/L/C/D); resolved owner Q&A in §5.
- `audit-2026-04-28-plan.md` — sequenced execution plan (Phase 2A → 2B →
  2C → 3 → 4) with locked owner decisions and constraints.
- `linear-actions-2026-04-28.md` — Linear MCP action script.

**Done in this pass:**

- Linear sync (commit `7758bd6`): TIK-12/18/19 → Cancelled, TIK-16 → Done,
  TIK-36 (B9, P1), TIK-37 (B10), TIK-38 (B11) created.
- PR triage (commit `5c47184`): #11, #15, #28 closed without merge per owner
  decision (prod stays on existing `PROXY_FIX_X_FOR=1` default behind nginx).
- Branch cleanup (commit `9e41cdc`): 16 stale merged branches deleted;
  `feature/admin-enhancement`, `release/feature-admin-enhancement-to-main`,
  and active PR branches (#16, #17) preserved.
- Verifications T-V-2 (`League.base_points_field` subleague behavior) and
  T-V-3 (real `/metrics` output vs banner) completed and folded into the
  analysis doc.

**Remaining work (per `audit-2026-04-28-plan.md`):**

- Phase 2B — TIK-37 (`socket_timeout` in `/health`), TIK-38 (metrics banner).
- Phase 2C — cherry-pick PR #16 (rate-limiter) and #17 (subleague scoring)
  into new PRs on `main`; close stale #16/#17.
- Phase 3 — TIK-36 (B9 audit log `before_request` wiring + e2e test +
  AGENTS.md/decisionLog/activeContext sync).
- Phase 4 — linter debt roadmap (T-D-1..D-4: mypy and flake8 inventory +
  Linear epics).

**New blockers:** none.

---

_Last updated: 2026-04-28_
