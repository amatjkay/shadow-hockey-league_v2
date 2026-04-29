# Decision Log

## 2026-04-24: Achievement Management Stabilization

**Context**: The manager achievement management was broken due to duplicate UI sections, JS errors, and mandatory model fields missing from the form.

**Decision**:
1.  **Consolidate UI**: Removed redundant achievement sections in `manager_edit.html`, moving to a single AJAX modal workflow.
2.  **Auto-calculation**: Shifted field population (title, icon_path, base_points, multiplier, final_points) from client-side JS to server-side `on_model_change` hook in `services/admin.py`.
3.  **Code Cleanup**: Deleted a duplicate `AchievementModelView` class that was causing conflicting configurations.

**Rationale**:
- Reduces form complexity and potential for user error.
- Ensures data consistency (points always match reference tables).
- Eliminates "dead code" and shadowed class definitions.

---

## 2026-04-23: Removal of mcp-servers from Git

- **Decision**: Remove `mcp-servers/` directory from version control.
- **Rationale**: The directory contains thousands of node modules and dependencies that bloat the repository, leading to extremely slow git operations and deployment times.
- **Alternative**: MCP servers should be managed as global tools or external dependencies.
- **Status**: Implemented.

## 2026-04-24: Database Point Alignment and Season 25/26 Baseline

- **Decision**: Synchronize `SeedService` base points with `RatingService` (e.g., TOP1 = 800) and establish Season 25/26 as the 1.0 multiplier baseline.
- **Rationale**: Previously, the database was seeded with legacy point values (e.g., TOP1 = 10), which contradicted the calculations shown in the UI and rating reports. This caused confusion and incorrect leaderboard ordering.
- **Implementation**: Updated `SeedService._seed_reference_data` and ensured `--force` mode clears all reference tables to allow point updates.
- **Status**: Implemented and verified via E2E testing.

---

## 2026-04-24: Achievement Icon Resolution Stabilization

**Context**: Inconsistent icon pathing between standard Admin forms and custom Manager Edit modals caused broken images.

**Decision**:
1. Centralized icon resolution in `AchievementType.get_icon_url()`.
2. Removed hardcoded defaults from `models.py` to allow dynamic `{code}.svg` resolution.
3. Updated all API responses (`calculate-points`, `get-manager-achievements`) and client-side scripts (`autofill.js`, `manager_edit.html`) to use the centralized logic or the server-provided `icon_path`.

**Rationale**: 
- Reduces logic duplication across Python and JavaScript.
- Simplifies adding new achievement types (no manual icon pathing required if standard naming is used).
- Fixes regression where custom icons were ignored in the Manager Edit modal.

**Status**: Implemented and verified via integration tests.

---

## 2026-04-28: Cache key partitioning and Season filter contract

**Context**: While diagnosing a homepage 500 reported by the user, three latent issues
in the `?season=N` filter pipeline were uncovered:

1. `blueprints/main.py` accepted `?season=N` from the dropdown but never read it
   (`request` was not imported).
2. `@cache.cached(key_prefix='leaderboard')` used a static prefix, so the cache
   bucket was shared across `?season=` variants — even after fixing (1) the page
   would always render the first cached variant.
3. `RatingService.build_leaderboard(season_id=...)` accepted the parameter but
   never filtered on it inside the loop.

**Decision**:

1. Read `season_id` from `request.args.get("season")` in `blueprints/main.py::index`.
2. Replace the static `key_prefix` with a callable that includes the season id (e.g.
   `key_prefix=lambda: f"leaderboard:{request.args.get('season') or 'lifetime'}"`).
   `invalidate_leaderboard_cache()` now calls `cache.clear()` to flush all variants.
3. In `build_leaderboard`, when `season_id is not None`, filter the achievements loop
   so managers without a matching achievement still appear with `total=0` (consistent
   with the lifetime view). Verified by 4 new regression tests in
   `tests/test_rating_service.py`.

**Rationale**:
- Correctness — three-step fix was needed because each layer relied on a different
  silent assumption.
- Caching contract — any future `@cache.cached` decorator that varies by query string
  must use a callable `key_prefix`. This rule is now in `PROJECT_KNOWLEDGE.md §5`.

**Status**: Implemented in PR #19, verified on dev server and by 4 regression tests.

---

## 2026-04-28: Playwright e2e smoke suite

**Context**: Manual user-driven smoke testing was the only safety net for this app.
Subtle regressions (e.g. an admin form 500 or a leaderboard 404 spree) were only being
caught after the fact.

**Decision**: Add `tests/e2e/test_smoke.py` — a Playwright-based smoke walking 42 scenarios
(public pages + REST API auth + every Flask-Admin model view + admin extras + console
error budget). Excluded from `pytest` auto-collection via `tests/e2e/conftest.py` so CI
remains unchanged. Suite is intentionally tolerant of business-data drift — it asserts
on status codes and the absence of console errors, not on row counts.

**Rationale**:
- A live, exercising probe catches things that unit tests miss (template breakage,
  missing static assets, FK form regressions).
- Manual run only — adopting it as a CI gate would require a hosted dev server and
  is left as a follow-up.

**Status**: Implemented in PR #21, currently 42/42 passing.

---

## 2026-04-28: Audit log gap — known issue, no fix yet

**Context**: Deep e2e probe revealed `audit_logs` table is empty after admin CRUD
operations. Investigation found the SQLAlchemy `after_flush` listener in
`services/audit_service.py` early-returns unless `g.current_user_id` is set, and the
setter `set_current_user_for_audit()` is only called from tests.

**Decision**: File the issue (B9, P1) in `docs/progress.md` and `PROJECT_KNOWLEDGE.md §3`.
Do not fix in the docs PR — the fix is a behavioural change requiring its own ticket
and regression test (assert that creating a Country yields a new `audit_logs` row).

**Rationale**: The fix itself is small (~10 LoC, a Flask-Login `before_request` hook),
but rolling it into a docs-only PR would mix concerns. Tracking the gap explicitly so
nothing relies on audit-log data until it's wired up.

**Status**: Documented; fix pending separate ticket.

---

## 2026-04-28: Audit-2026-04-28 — strategy decisions

**Context**: External audit document (`audit-2026-04-28.md`) was validated against `main`
HEAD `ff6bca0` and decomposed into Phase 2A → 4 of work in
`docs/audits/audit-2026-04-28-plan.md`. This entry records the seven strategic decisions
captured in that plan's "Decisions" table, so they survive independently of the plan
document.

**Decisions**:

1. **TIK-14 / TIK-15 / TIK-17 priority** — keep current; do **not** bump to P3.
2. **PR #16 / #17 strategy** — close-and-replace via cherry-pick into fresh PRs on `main`
   (Phase 2C of the plan), **not** rebase-onto-main of the existing branches. Reason:
   avoid history rewrites on shared branches; existing branches may be deleted **after**
   `archive/pr-*` tags are pushed (see plan §6.5).
3. **B9 (audit-log wiring) phase** — Phase 3 (after the Phase 2 quick wins TIK-37 / TIK-38).
   Reason: Phase 2B fixes are <1h each; the B9 fix needs an integration test plus an
   AGENTS.md §5 rewrite that describes both audit mechanisms.
4. **Linter debt (T-D-1..D-4)** — defer to Phase 4 (separate Linear epics for mypy and
   flake8). Reason: non-blocking; tracked but not on the audit critical path.
5. **Concurrent PRs in flight** — strictly one code PR at a time, sequential merges.
   Reason: minimize merge-conflict and cherry-pick complexity in Phase 2C.
6. **PR #28 / `PROXY_FIX_X_FOR=1`** — closed without merge; prod stays on the existing
   default behind nginx. Reason: owner confirmed the nginx-fronted deployment makes the
   existing default safe; merging #28 without a coordinated prod env change would have
   broken per-IP rate limiting.
7. **Branch `feature/admin-enhancement`** — keep (do **not** delete during cleanup).
   Reason: kept as a readable history pointer to the late-April stabilization work that
   landed in `main` via PR #25.

**Implemented in**:
- Linear sync (TIK-12 / TIK-18 / TIK-19 cancelled, TIK-16 done, TIK-36 / TIK-37 / TIK-38
  created) — commit `7758bd6`.
- PR triage (PR #11 / #15 / #28 closed) — commit `5c47184`.
- Branch cleanup (16 stale merged branches deleted, source branches for PR #16 / #17
  preserved) — commit `9e41cdc`.

**Source of truth**: `docs/audits/audit-2026-04-28-plan.md` (Decisions table and Phase 2A
through Phase 4 schedule).

**Status**: Implemented for Phase 2A; Phases 2B → 4 outstanding.
