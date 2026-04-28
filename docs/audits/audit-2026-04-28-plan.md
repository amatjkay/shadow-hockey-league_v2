# Audit 2026-04-28 — Execution Plan

> Source of truth for ordered execution of remaining audit tasks.
> See `docs/audits/audit-2026-04-28-analysis.md` for full validation/decomposition.
> See `docs/audits/linear-actions-2026-04-28.md` for the Linear MCP action script.

## Status snapshot

- **Linear sync:** ✅ done — TIK-12/18/19 cancelled, TIK-16 done, TIK-36/37/38 created (commit `7758bd6`).
- **PR triage:** ✅ done — PR #11 closed earlier; PR #15 + #28 closed in commit `5c47184`.
- **Branch cleanup:** ✅ done — 16 stale branches deleted in commit `9e41cdc`.
- **Plan locked:** see phases below.

## Decisions (recorded for traceability)

| Question | Owner answer | Date |
|----------|--------------|------|
| §C — bump TIK-14/15/17 → P3? | **No** (skip — current priorities kept) | 2026-04-28 |
| PR #16/#17 — strategy? | **Cherry-pick into new PRs on `main`** | 2026-04-28 |
| TIK-36 (B9) audit log — when? | **Phase 3** (after Phase 2 quick wins) | 2026-04-28 |
| Linter debt (T-D-1..D-4) — do? | **Yes** (Phase 4) | 2026-04-28 |
| Concurrent PRs in flight? | **One at a time** (sequential merge) | 2026-04-28 |
| PR #28 / `PROXY_FIX_X_FOR=1` on prod? | **No** — prod stays on existing default behind nginx | 2026-04-28 |
| Branch `feature/admin-enhancement` keep? | **Yes** (history) | 2026-04-28 |

## Execution sequence

### Phase 2A — Foundation (analysis doc completion + #31 merge)

| # | Task | File(s) touched | Done? |
|---|------|----------------|-------|
| 1 | **T-V-2** Document `League.base_points_field` for subleagues 2.1/2.2/2.x | `docs/audits/audit-2026-04-28-analysis.md` | ✅ |
| 2 | **T-V-3** Run app locally, capture real `/metrics` output, save in analysis doc | `docs/audits/audit-2026-04-28-analysis.md` | ✅ |
| 3 | Commit Phase 2A and request user approval to merge PR #31 | — | ⏳ |
| 4 | Merge PR #31 → `main` | (after owner approve) | ⏳ |

### Phase 2B — Quick wins (two small PRs on `main`)

| # | Task | File(s) touched | Done? |
|---|------|----------------|-------|
| 5 | **TIK-37 (B10)** Add `socket_timeout=1.0` to `redis.Redis(...)` in health blueprint + regression test | `blueprints/health.py`, `tests/test_health.py` | ⏳ |
| 6 | **TIK-38 (B11)** Sync app startup banner with actual `/metrics` (relies on T-V-3 output) | `app.py` (line ~233-236) | ⏳ |

### Phase 2C — Revive orphan stack via cherry-pick

| # | Task | Source commit | Done? |
|---|------|---------------|-------|
| 7 | **PR #16 → new PR on `main`** rate-limiter consolidation (T-002, T-011) | `9e5c220` from `devin/1777322380-rate-limiter-fix` | ⏳ |
| 8 | **PR #17 → new PR on `main`** subleague scoring unification (T-003, T-004, T-007, T-020) | head of `devin/1777323700-points-unification` | ⏳ |
| | After both merged: close stale #16 / #17 with `replaced by #NN` comment. | — | ⏳ |

### Phase 3 — Audit log compliance fix

| # | Task | File(s) touched | Done? |
|---|------|----------------|-------|
| 9 | **TIK-36 (B9)** Wire `set_current_user_for_audit` in `before_request` hook + e2e integration test + update AGENTS.md/decisionLog/activeContext | `app.py`, `tests/integration/test_audit_logging_e2e.py`, `AGENTS.md`, `docs/decisionLog.md`, `docs/activeContext.md` | ⏳ |

### Phase 4 — Linter debt roadmap

| # | Task | File(s) touched | Done? |
|---|------|----------------|-------|
| 10 | **T-D-1** Run `mypy .` and save 84 errors with file/line breakdown | `docs/audits/mypy-debt-2026-04-28.md` (new) | ⏳ |
| 11 | **T-D-2** Run `flake8` (with `extend-ignore` disabled) and save 131 violations grouped by error code | `docs/audits/flake8-debt-2026-04-28.md` (new) | ⏳ |
| 12 | **T-D-3** Linear epic "mypy zero" + 18 sub-tasks (one per file with errors) | Linear MCP | ⏳ |
| 13 | **T-D-4** Linear epic "flake8 zero" + sub-tasks per error code | Linear MCP | ⏳ |

## Constraints (do-not-do list)

- Do **not** touch production env (`PROXY_FIX_X_FOR`, systemd) — owner kept current default.
- Do **not** merge PR #31 without owner approval (analysis doc is authoritative for future agents).
- Do **not** run `git push --force` on `main` or shared branches.
- Do **not** keep more than one in-flight code PR at a time — sequential merges only.
- Do **not** modify tests to silence the 3 pre-existing failures (rating calc assertion, flush-cache redirect code, admin CRUD) — these are tracked separately.

## Done criteria for the whole audit

- All Phase 2A/2B/2C/3/4 rows above marked ✅.
- `docs/progress.md` final entry recording audit closure.
- Linear: every B1–B11 finding has a closed-state ticket linked from this plan.
- `git branch -r` contains only `main`, `feature/admin-enhancement`, `release/feature-admin-enhancement-to-main`, and active PR branches.
