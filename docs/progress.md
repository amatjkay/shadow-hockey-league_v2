# Progress — Shadow Hockey League v2

> **Purpose:** Tracking long-term project milestones and feature progress.

---

## Completed (Stabilization Phase)

- [x] Create dedicated development branch `fix`.
- [x] Reset primary admin account (`s3ifer`).
- [x] Standardize flag filenames to uppercase (`RUS.png`) for Linux compatibility.
- [x] Synchronize `SeedService` and `RatingService` point calculations.
- [x] Isolate Flask-Admin monkey-patches to `utils/patches.py`.
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

- **Total Tests:** 388 unit/integration (3 pre-existing failures unchanged) +
  42-scenario Playwright e2e smoke (manual run only, not auto-collected by pytest).
- **Code Coverage:** ~94%
- **Linting:** Configured (.flake8, mypy)
- **Architecture:** Modular Python utilities + External static assets

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

## Known Open Issues

- **B5** — jQuery race in `templates/admin/shl_master.html`: inline script
  calls `$.fn.select2.defaults.set(...)` before the parent template's jQuery
  loads. Surfaces as `pageerror: $ is not defined` in the browser console on
  every admin page. Functionality is unaffected; Flask-Admin re-loads its
  own select2 later. Tracked separately, will get a TIK ticket before fix.
- **PR #15 / #16 / #17** — earlier integration-fix work (rate-limiter Redis
  storage, `base_points` unification, MCP-config hygiene), open against
  `devin/integration-analyst-fixes`. Awaiting user review/merge decision.

---

_Last updated: 2026-04-28_
