# Audit 2026-04-28 — Execution Plan

> Source of truth for ordered execution of remaining audit tasks.
> See `docs/archive/audits/audit-2026-04-28-analysis.md` for full validation/decomposition.
> See `docs/archive/audits/linear-actions-2026-04-28.md` for the Linear MCP action script.

## Status snapshot (2026-05-01 — audit closed)

- **Linear sync:** ✅ done — TIK-12/18/19 cancelled, TIK-16 done, TIK-36/37/38 created (commit `7758bd6`).
- **PR triage:** ✅ done — PR #11 closed earlier; PR #15 + #28 closed in commit `5c47184`.
- **Branch cleanup:** ✅ done — 16 stale branches deleted in commit `9e41cdc`; another 14 pruned 2026-05-01.
- **Phase 2A:** ✅ done — analysis verifications (T-V-2, T-V-3) committed, plan locked.
- **Phase 2B:** ✅ done — PR #32 (TIK-37 socket_timeout) and PR #33 (TIK-38 metrics banner) merged.
- **Phase 2C:** ✅ done — PR #34 (rate-limiter, replaces #16) and PR #35 (subleague scoring, replaces #17) merged. Old PRs closed.
- **Phase 3:** ✅ done — PR #38 (TIK-36 audit-log wiring) merged. B9 closed.
- **Phase 4:** ✅ done — PR #42 closed both TIK-39 (mypy zero) and TIK-40 (flake8 zero); debt inventories live at `docs/archive/audits/{mypy,flake8}-debt-2026-04-29.md`.
- **Phases A–H (post-audit testing campaign):** ✅ done — docs sync, Linear sync, test inventory + optimization, gap analysis, mass run (415 unit/integration), linter debt (Phase 4), issue capture all completed and merged via PRs #41, #42, #43.
- **Audit closure:** ✅ done — see `docs/progress.md` 2026-05-01 cleanup entry.

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
| Post-Phase-3 testing campaign scope? | **Full A→G** (docs + Linear sync + test inventory + optimization + gap analysis + mass run + linter debt) | 2026-04-29 |

## Execution sequence

### Phase 2A — Foundation (analysis doc completion + #31 merge)

| # | Task | File(s) touched | Done? |
|---|------|----------------|-------|
| 1 | **T-V-2** Document `League.base_points_field` for subleagues 2.1/2.2/2.x in §1.3 of analysis doc | `docs/audits/audit-2026-04-28-analysis.md` | ✅ |
| 2 | **T-V-3** Run app locally, capture real `/metrics` output, save in §1.6 of analysis doc | `docs/audits/audit-2026-04-28-analysis.md` | ✅ |
| 3 | Commit Phase 2A and request user approval to merge PR #31 | — | ✅ |
| 4 | Merge PR #31 → `main` (or replace with successor PR carrying same docs) | (owner-merged superseding PR) | ✅ |

### Phase 2B — Quick wins (two small PRs on `main`)

| # | Task | File(s) touched | Done? |
|---|------|----------------|-------|
| 5 | **TIK-37 (B10)** Add `socket_timeout=1.0` to `redis.Redis(...)` in health blueprint + regression test (PR #32 merged) | `blueprints/health.py`, `tests/test_blueprints.py` | ✅ |
| 6 | **TIK-38 (B11)** Sync app startup banner with actual `/metrics` — banner now derived from `metrics_service` constants (PR #33 merged) | `app.py`, `services/metrics_service.py` | ✅ |

### Phase 2C — Revive orphan stack via cherry-pick

Source SHAs in this section reference commits living **only** on the open PR branches.
Source branches were preserved in-flight; archive tagging skipped because PRs landed before any cleanup.

| # | Task | Source commit | PR | Done? |
|---|------|---------------|----|-------|
| 6.5 | **Pre-condition:** tag source commits before any branch cleanup (skipped — source branches preserved while cherry-picks were in flight). | — | n/a | n/a |
| 7 | **PR #16 → PR #34 on `main`** rate-limiter consolidation (T-002, T-011). Devin Review caught seed-data bug in `tests/test_api.py` — fixed in commit `06dafeb`. | `9e5c220` from `devin/1777322380-rate-limiter-fix` cherry-picked to PR #34 | #34 merged | ✅ |
| 8 | **PR #17 → PR #35 on `main`** subleague scoring unification (T-003, T-004, T-007, T-020). New helper `services/scoring_service.py::get_base_points()`. | scoring changes from `devin/1777323700-points-unification` cherry-picked to PR #35 | #35 merged | ✅ |
| 8.5 | After both merged: close stale #16 / #17 with `replaced by #NN` comment. | — | — | ✅ |

### Phase 3 — Audit log compliance fix

| # | Task | File(s) touched | Done? |
|---|------|----------------|-------|
| 9 | **TIK-36 (B9)** Wire `set_current_user_for_audit` in `before_request` hook + 3 regression tests (PR #38 merged). New helper `register_audit_request_hook(app)` lives in `services/audit_service.py` and is called from `app.py::register_extensions` right after `init_admin`. | `app.py`, `services/audit_service.py`, `tests/integration/test_audit_logging.py` | ✅ |

### Phase 4 — Linter debt roadmap

| # | Task | File(s) touched | Done? |
|---|------|----------------|-------|
| 10 | **T-D-1** Run `mypy .` and save errors with file/line breakdown | `docs/archive/audits/mypy-debt-2026-04-29.md` | ✅ |
| 11 | **T-D-2** Run `flake8` (with `extend-ignore` disabled) and save violations grouped by error code | `docs/archive/audits/flake8-debt-2026-04-29.md` | ✅ |
| 12 | **T-D-3** Linear ticket "mypy zero" (TIK-39) | Linear MCP | ✅ |
| 13 | **T-D-4** Linear ticket "flake8 zero" (TIK-40) | Linear MCP | ✅ |

## Post-audit testing campaign (Phase A–H, 2026-04-29 → 2026-05-01)

Triggered by owner request: "Актуализируй документацию и задачи в Linear, оптимизируй и
актуализируй тесты (Unit, integration, regression, ui, e2e) и проведи масштабное
тестирование. Все проблемы фиксируй в Linear."

| # | Phase | Scope | Done? |
|---|-------|-------|-------|
| A | Docs sync | This file + `progress.md` + `techContext.md` + `activeContext.md` + `decisionLog.md` | ✅ |
| B | Linear sync | Close TIK-36/37/38; status updates on TIK-16/17 | ✅ |
| C | Test inventory | Categorized every test file → `docs/archive/audits/test-inventory-2026-04-29.md` | ✅ |
| D | Test optimization | Fixture dedupe, slow-test refactor, flaky cleanup landed via PR #41 | ✅ |
| E | Gap analysis | Coverage vs B1–B11 + new sub-systems; missing regressions added in PR #41 | ✅ |
| F | Mass run | 415 unit/integration passing; e2e (Playwright) sampled manually | ✅ |
| G | Linter debt (= Phase 4) | mypy/flake8 reports + Linear tickets TIK-39/40 closed via PR #42 | ✅ |
| H | Issue capture | All findings filed; campaign tickets TIK-39/40/41 closed | ✅ |

## Constraints (do-not-do list)

- Do **not** touch production env (`PROXY_FIX_X_FOR`, systemd) — owner kept current default.
- Do **not** run `git push --force` on `main` or shared branches.
- Do **not** keep more than one in-flight code PR at a time — sequential merges only.
- Do **not** modify tests to silence the 3 pre-existing failures (rating calc assertion, flush-cache redirect code, admin CRUD) — these are tracked separately.
- Do **not** delete branches `devin/1777322380-rate-limiter-fix` or
  `devin/1777323700-points-unification` until tagged for archive (currently still on origin
  for forensic reference; can be deleted now that PR #34 / #35 are merged).

## Done criteria for the whole audit

- All Phase 2A/2B/2C/3/4 rows above marked ✅. **Status: ✅ — all phases closed.**
- `docs/progress.md` final entry recording audit closure. **Status: ✅ — 2026-05-01 cleanup entry written.**
- Linear: every B1–B11 finding has a closed-state ticket linked from this plan. **Status: ✅ — TIK-36/37/38 (B9/B10/B11) closed; TIK-39/40 (linter debt) closed.**
- `git branch -r` contains only `main`, `feature/admin-enhancement`, `release/feature-admin-enhancement-to-main`, and active PR branches. **Status: ✅ — 16 stale branches deleted in commit `9e41cdc`; another 14 deleted 2026-05-01.**
