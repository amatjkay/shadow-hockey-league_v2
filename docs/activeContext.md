# Active Context — Shadow Hockey League v2

> **Purpose:** This file tracks the current focus of work, recent changes, and immediate
> next steps. All agents MUST read this before starting any task.

---

## Current Focus

**Phase:** Pre-prod hardening (post bugfix-pass)
**Status:** Public pages and admin CRUD verified end-to-end. Three known issues filed (B9 audit-log gap [P1], B10 /health Redis timeout [P2], B11 metrics banner mismatch [P3]).

Next milestone: deploy `feature/admin-enhancement` to `main` after a docs refresh, then schedule audit/optimization round to address B9/B10/B11 and the open `devin/integration-analyst-fixes` PR stack (#15/#16/#17/#18).

---

## Status

- **Branch:** `feature/admin-enhancement` (HEAD `1da8d6d`, post PR #23 merge).
- **Goal:** Land all stabilization work into `main`, then start audit/optimization phase.
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

---

## Immediate Next Steps

- [x] **[TIK-23–26]** earlier feature roadmap items (duplicate validation, player search, advanced filtering, audit log viz).
- [x] **[TIK-27–32]** post-PR #19 bugfix pass + e2e suite + Elite 24/25 data + admin Select2 cleanup.
- [x] **[TIK-33]** docs refresh (this PR).
- [ ] Merge `feature/admin-enhancement` → `main` (full diff review by user).
- [ ] Audit / optimization round: address B9 (audit log), B10 (/health performance), B11 (metrics banner).
- [ ] Decide fate of `devin/integration-analyst-fixes` PR stack (#15 docs sync, #16 Redis-Limiter, #17 base_points unification, #18 transaction-neutral audit) — merge as-is, rewrite onto current `feature/admin-enhancement`, or close.

---

## Active Blockers

- None for the docs refresh. Audit-round work (B9/B10/B11) is queued but unstarted, and a user decision is
  outstanding on the `devin/integration-analyst-fixes` PR stack.

---

## Notes for Next Agent

- **Monkey-Patches**: Located in `utils/patches.py`, applied via `apply_patches()` in `app.py`.
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

_Last updated: 2026-04-28_
