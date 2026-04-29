# Active Context — Shadow Hockey League v2

> **Purpose:** This file tracks the current focus of work, recent changes, and immediate
> next steps. All agents MUST read this before starting any task.

---

## Current Focus

**Phase:** Audit-2026-04-28 execution (post triage + Linear sync)
**Status:** External audit (`docs/audits/audit-2026-04-28-analysis.md`) validated against `main`
HEAD `ff6bca0`; triage closed PR #11/#15/#28, cancelled TIK-12/18/19, marked TIK-16 done,
created TIK-36/37/38 for the three confirmed bugs B9/B10/B11.

Next milestone: execute Phase 2B → 4 of `docs/audits/audit-2026-04-28-plan.md`
(TIK-37 health socket_timeout, TIK-38 metrics banner, cherry-pick of PR #16/#17 onto
`main`, TIK-36 audit-log wiring, then linter-debt roadmap).

---

## Status

- **Branch:** `main` (HEAD `519fe67`, post PR #36 merge). `feature/admin-enhancement` was
  merged into `main` via PR #25 and is preserved as a history pointer.
- **Goal:** Execute Phases 2B → 4 of `docs/audits/audit-2026-04-28-plan.md`.
- **Seeding Status:** ✅ 58 achievements (post TIK-30), 42 managers, 5 seasons, baseline 25/26.
- **Live dev server (when running):** `http://127.0.0.1:5000`.

## Recent Changes (2026-04-27 → 2026-04-28)

- **PR #19 (TIK-27/28/29)** — fixed 6 production-impacting bugs found by the user on the live dev:
  homepage 500 (missing `request` import), Achievement form 500 (`form_args` regression),
  trophy 404s (`icon_path` pointed to `/icons/` instead of `/cups/`),
  leaderboard cache key not partitioned by `?season=`, `RatingService.build_leaderboard()` ignored its
  `season_id` parameter, hard-coded season dropdown.
- **PR #20 (TIK-30)** — added the 9 missing Shadow 1 League 24/25 awards (Elite TOP1…R1)
  to `data/seed/achievements.json`; reseeded `dev.db`. Brought lifetime total from 49 → 58.
- **PR #21 (TIK-31)** — added Playwright smoke suite at `tests/e2e/test_smoke.py` (42 scenarios,
  excluded from `pytest` auto-collection). Run command lives in PROJECT_KNOWLEDGE.md §5.
- **PR #22 (TIK-32)** — removed dead jQuery-race-prone Select2 locale-init script
  from `templates/admin/shl_master.html`; admin console errors now 0.
- **PR #23** — single rollup of TIK-30/31/32 onto `feature/admin-enhancement` after a
  stacked-PR base mismatch left the original PRs merging into PR #19's staging branch.
- **Deep e2e probe (2026-04-28)** — added `/tmp/e2e_artifacts/deep/BUGS.md` documenting B9 (audit
  log not written in prod), B10 (/health Redis blocking), B11 (metrics banner mismatch). All three
  pre-existed this branch; surfaced now because the branch is otherwise clean.
- **Audit-2026-04-28 triage pass (2026-04-28, PR #31)** — validated external audit against
  `main` HEAD `ff6bca0`; closed PR #11 / #15 / #28; cancelled TIK-12/18/19; marked TIK-16 done;
  created TIK-36/37/38; deleted 16 stale merged branches. Artifacts: `docs/audits/audit-2026-04-28-{analysis,plan}.md`,
  `docs/audits/linear-actions-2026-04-28.md`. Decisions captured in `docs/decisionLog.md`.

---

## Immediate Next Steps

- [x] **[TIK-23–26]** earlier feature roadmap items (duplicate validation, player search, advanced filtering, audit log viz).
- [x] **[TIK-27–32]** post-PR #19 bugfix pass + e2e suite + Elite 24/25 data + admin Select2 cleanup.
- [x] **[TIK-33]** docs refresh (PR #25).
- [x] **Merge** `feature/admin-enhancement` → `main` (PR #25, 2026-04-28).
- [x] **Audit-2026-04-28 triage** — Linear sync, PR triage, branch cleanup (PR #31, this PR).
- [ ] **Phase 2B** — TIK-37 (`socket_timeout` in `/health`), TIK-38 (metrics banner alignment).
- [ ] **Phase 2C** — cherry-pick PR #16 (rate-limiter) and #17 (subleague scoring) onto `main`
  as fresh PRs; close stale #16 / #17.
- [ ] **Phase 3** — TIK-36 (B9): wire `set_current_user_for_audit` in `before_request` hook,
  add e2e integration test, rewrite `AGENTS.md` §5 to describe both audit mechanisms.
- [ ] **Phase 4** — linter-debt roadmap (T-D-1..D-4): mypy and flake8 inventory + Linear epics.

---

## Active Blockers

- **B9 / TIK-36 (P1)** — admin-CRUD audit logging is not wired in production:
  `services/audit_service.py:209-216` early-returns when `g.current_user_id` is missing,
  and `set_current_user_for_audit()` is not called from any production code path. Scheduled
  for Phase 3 of `docs/audits/audit-2026-04-28-plan.md`.
- **B10 / TIK-37 (P2)** and **B11 / TIK-38 (P3)** — queued for Phase 2B of the same plan.
- **PR stack `devin/integration-analyst-fixes`** — PR #15 / #28 already closed. PR #16 / #17
  to be replaced by fresh PRs on `main` via cherry-pick (Phase 2C). Source branches
  `devin/1777322380-rate-limiter-fix` and `devin/1777323700-points-unification` MUST be
  preserved (or archived as `archive/pr-*` tags) until the cherry-picks are merged.

---

## Notes for Next Agent

- **Flask-Admin compatibility**: Flask-Admin 2.0.2 ships with the `cls=self` fallback in `BaseView._run_view`, and WTForms 3.2.x no longer accepts `allow_blank` on the base `Field`. The previous `utils/patches.py` shim is therefore obsolete and was removed in TIK-34. If a future upgrade re-introduces the incompatibility, restore the patch and call it from `create_app()` before `init_admin(app)`.
- **Admin JS**: Shared logic is in `static/js/admin/autofill.js`.
- **Testing**:
  - Unit/integration: `venv/bin/pytest --ignore=tests/e2e`. ~1 minute, expect 388 pass / 3 pre-existing failures.
  - Smoke e2e: requires a running dev server; see PROJECT_KNOWLEDGE.md §5 for the exact command.
  - Deep probe: `/tmp/deep_e2e.py` (one-shot diagnostic; not committed). Use as a template for new
    audit checks.
- **Database**: `dev.db` is the primary SQLite database; schema checks via the `sqlite` MCP server
  are recommended before any mutation. After `seed_db.py --force` season `id`s start at 1 (21/22).
- **Audit-log gap (B9)**: keep this in mind when working on admin features — currently no audit
  rows are written from production code, even though the listener and tables are in place.
- **Cache key**: any new `@cache.cached` decorator that varies by query-string MUST use a callable
  `key_prefix` (see `blueprints/main.py::index`).

---

_Last updated: 2026-04-29 (PR #31 follow-up — Devin Review address pass)_
