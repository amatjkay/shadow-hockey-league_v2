# Progress — Shadow Hockey League v2

> **Purpose:** Living document tracking only the **current** cycle of work.
> All agents MUST update this before ending their turn.
>
> Older sections live in `docs/archive/progress-pre-2026-04-29.md`.

## 2026-05-04: TIK-57 — sub-agents/skills sanity check + tools/MCP table corrections

### Completed
- [x] **TIK-57** (PR follow-up to #61) — Walked the verification, codebase-map,
  linear-sync, token-budget, db-migration, doc-rotation, and feature-research
  skills against the current Devin session. Verified `make check` (black + isort
  + flake8 + mypy ✅), `make audit-deps` (pip-audit ✅, no known CVEs), `make
  test` (470 passed locally without Redis; 472 in CI). Found two skills (`db-migration`,
  `feature-research`) and `AGENTS.md` § 4 / `docs/techContext.md` MCP tables
  referencing MCP servers that no longer exist in this session: `filesystem`,
  `github`, `sqlite`, `sequential-thinking`, `notebooklm`, `duckduckgo`. Live
  install verified via `mcp_tool` `command="list_servers"` → `context7`,
  `linear`, `playwright`, `redis`. Rewrote both skills around built-in tools
  (`read`/`edit`, `git`/`git_pr`, `web_search`/`web_get_contents`, `exec` for
  `sqlite3`/`alembic`) and refreshed the AGENTS / techContext tool tables to
  match. Also: corrected the test count from `464` to `472` everywhere it
  appeared (`docs/activeContext.md`, `docs/techContext.md`, `docs/progress.md`,
  `PROJECT_KNOWLEDGE.md`, `.agents/skills/verification/SKILL.md`) and added a
  caveat that 2 of the 472 tests need a real Redis service to pass (CI has it,
  local runs without Redis don't — `470 passed, 2 failed` is expected).

### Why it matters
- Agents reading the old AGENTS.md / techContext / db-migration / feature-research
  would call MCP tools that don't exist and waste a turn on the error. The
  correction is purely informational, no code changes.

## 2026-05-03: TIK-51 tech-debt continuation — deps audit, mypy, coverage, e2e in CI

### Completed
- [x] **TIK-52** (PR #57) — `pip-audit` wired into CI as a non-blocking-for-dev-deps gate. New `make audit-deps` target; runtime CVEs fail the build, dev-only CVEs are reported. Bumped `WTForms` 3.2.1 → 3.2.2 and dev tooling bumps that the audit surfaced.
- [x] **TIK-53** (PR #58) — Re-enabled `mypy` in `make check` and `Quality & Tests` CI. Fixed all 40 errors on the source tree. Added `services/_types.py::SessionLike` to model the Flask-SQLAlchemy session proxy for callers; preferred `cast()` + `is not None` guards over `# type: ignore`. Side-fix: removed double JSON encoding in `recalc_service`'s audit-log details payload (rows now store `"{...}"` instead of `"\"{...}\""`).
- [x] **TIK-54** (PR #59) — Coverage 83% → 87% via 49 new tests covering Redis socket-timeout error paths, admin view formatters, recalc/metrics corner cases, and `app.py` create-app failure modes. Added `tests/test_admin_views_formatters.py` (new), expanded `tests/test_health.py`, `tests/test_recalc_service.py`, `tests/test_metrics_service.py`, `tests/test_app.py`.
- [x] **TIK-55** (PR #60) — Wired `tests/e2e/test_smoke.py` (42-scenario Playwright suite) into CI as the `E2E Smoke (Playwright)` GitHub Actions job. New `scripts/create_e2e_admin.py` provisions the `e2e_admin` super-admin idempotently. New `make e2e` target for local runs. Workflow now has 3 stages: `quality-and-tests` → `e2e-smoke` → `deploy`. Fixed an early CI failure where `seed_db.py` ran on a fresh runner with no database — added a `Create database schema` step to the workflow that calls `db.create_all()` before seeding.

### Metrics delta

| Metric | Before (post-TIK-42) | After (post-TIK-55) |
|---|--:|--:|
| Tests | 423 | 472 |
| Coverage (services/blueprints/app/models) | 84% | 87% |
| `mypy` errors in `make check` | 40 (skip in CI) | 0 (gate in CI) |
| Dependency audit | manual | `pip-audit` in CI |
| E2E in CI | none | 42 scenarios per PR |

### Status
- [x] All 5 Linear tickets (TIK-51 epic + TIK-52..TIK-55) in **Done**.
- [x] All tech-debt-continuation remote branches deleted.
- [x] Smoke verification passed locally (delete `instance/dev.db` → schema bootstrap → seed → admin provision → 42/42 e2e green).

### Blockers
- [ ] None for this campaign. (Secret-rotation owner-action still open from 2026-05-01 entry below.)

### Forward contracts
- New `scripts/create_e2e_admin.py` is the single way to provision the e2e admin user; do not inline its logic into the CI workflow. Idempotent — safe to re-run.
- `make audit-deps` reports both runtime and dev-only CVEs; the CI step fails only on runtime CVEs (`pip-audit -r requirements.txt`). Dev-only audit (`pip-audit -r requirements-dev.txt`) is informational; promote a CVE to runtime-blocking by updating the dep, not by relaxing the gate.
- `services/_types.py::SessionLike` is the canonical alias for Flask-SQLAlchemy's `db.session` proxy. New service-layer code should use it rather than re-importing private SQLAlchemy types.

---

## 2026-05-03: TIK-42 cleanup campaign — splits, refactor, dedup, coverage

### Completed
- [x] **TIK-43** (PR #47) — vulture dead-code prune (5 unused locals) + canonicalised `invalidate_leaderboard_cache` to `services/cache_service`.
- [x] **TIK-44** (PR #48) — lowered cyclomatic complexity of 4 hot functions to ≤ C: `bulk_add_achievements` E33→C13, `bulk_create_achievements` D25→C11, `update_achievement` D25→B8, `validate_achievements` D21→A3.
- [x] **TIK-45** (PR #49) — split `services/api.py` (920 LOC monolith) into `services/api/` package: `__init__.py` (37) + `_helpers.py` (92) + `countries.py` (161) + `managers.py` (215) + `achievements.py` (331). External `from services.api import api` preserved.
- [x] **TIK-46** (PR #50) — split `blueprints/admin_api.py` (893 LOC) into `blueprints/admin_api/` package: `__init__.py` + `_helpers.py` + `lookups.py` + `achievements.py`. External `from blueprints.admin_api import admin_api_bp` preserved.
- [x] **TIK-47** (PR #51) — decomposed `services/admin.py` (635 LOC) into `services/admin/` package: `__init__.py` (209) + `base.py` (53, `SHLModelView`) + `views.py` (342, all 7 ModelViews) + `_rate_limit.py` (72, helpers).
- [x] **TIK-48** (PR #52) — removed 4 duplicate test classes from `tests/test_rating_service.py` (-331 LOC); renamed `tests/test_e2e.py` → `tests/integration/test_smoke_endpoints.py` (it was Flask test client, not Playwright).
- [x] **TIK-49** (PR #53) — archived `scratch/` (7 one-off prod-sync scripts) into `scripts/oneoff/` with README; updated `pyproject.toml` exclusions for black/isort/mypy.
- [x] **TIK-50** (PR #54) — added 28 tests targeting recalc/app/metrics error paths. Combined coverage on `services/blueprints/app.py` rose from 81% → 84% (target ≥ 87% remains; gap closed materially).
- [x] Stack consolidated via **PR #55** (devin/1777714229-tik48-tests-reorg → main) after sequential merges of #47-#54 stacked into each other instead of main. Resolved 2 textual conflicts in `blueprints/admin_api/achievements.py` and `services/admin/views.py` against TIK-43 (#47) which had landed on main separately.
- [x] **Smoke-tested on `main`** post-merge: 6 UI/API checks across all 3 split packages — leaderboard renders 42 managers, `/api/countries` JSON OK, admin login + dashboard + manager list + admin_api lookup all green. Server logs clean (no ImportError/AttributeError/500).
- [x] Pruned 9 stale `origin/devin/*` branches (TIK-42 epic stack heads).

### Metrics delta

| Metric | Before | After |
|---|--:|--:|
| Tests | 415 | 423 |
| Coverage (services/blueprints/app) | 81% | 84% |
| Files > 600 LOC | 3 | 0 |
| Functions with CC ≥ D | 4 | 0 |
| Dead code (vulture conf 80) | 5 | 0 |
| Duplicate test names | 13+ | 4 (intentional) |

### Status
- [x] All 9 Linear tickets (TIK-42 epic + TIK-43..TIK-50) in **Done**.
- [x] All cleanup-stack remote branches deleted.
- [x] Smoke tests recorded with annotations; report at `docs/audits/test-report-tik42-cleanup-2026-05-03.md` (when archived).

### Blockers
- [ ] None for this PR. (Secret-rotation blocker still open — see 2026-05-01 repo-hygiene entry below.)

---

## 2026-05-01: Cleanup pass — docs sync, branch prune, backlog drain

### Completed
- [x] Pruned 14 already-merged `origin/devin/*` branches (`git push --delete`).
- [x] Cancelled stale Linear backlog: TIK-14 (Player Search UI), TIK-15 (Admin Achievement Preview), TIK-17 (OpenAPI docs). Rationale documented in each ticket.
- [x] Synced `docs/activeContext.md` to post-PR-#43 state (Phase A→H plan retired; backlog now empty; only outstanding owner-action is the secret rotation tracked below).
- [x] Trimmed stale «Open work after this PR» from the 2026-04-30 entry below — referenced phases (D/E/F/G/H) are all closed.

### In Progress
- [ ] None.

### Blockers
- [ ] None for this PR. (Secret-rotation blocker still open — see 2026-05-01 repo-hygiene entry below.)

---

## 2026-05-01: Sub-agents + skills + prompt v2.0 (token-efficiency follow-up)

### Completed
- [x] `.agents/agents/token-auditor.md` — new sub-agent for finding token waste in repo, prompts, Memory Bank.
- [x] `.agents/agents/doc-curator.md` — new sub-agent for `progress.md` / `decisionLog.md` rotation.
- [x] `.agents/skills/token-budget/SKILL.md` — token-cost heuristics + lazy-load patterns.
- [x] `.agents/skills/doc-rotation/SKILL.md` — quarterly archive workflow with safety rules.
- [x] `.agents/skills/codebase-map/SKILL.md` — `grep -n` recipes for heavy files (admin_api, api, admin services).
- [x] `.agents/prompts/shl-optimizer.prompt.md` — SHL-OPTIMIZER prompt v2.0 (parametrized via `{{PROJECT_FACTS}}`).
- [x] `.agents/prompts/shl-optimizer.fewshot.md` — one example per role; loaded lazily on first activation.
- [x] `docs/INDEX.md` — single read-trigger map for `docs/*` so agents avoid full-file reads.
- [x] `AGENTS.md` §3 updated — new sub-agents registered with role-files, NOT-DO constraints, hand-off protocol entries; new "Skills" sub-section listing all 7 skills.
- [x] **Merged as PR #45** (2026-05-01).

### Blockers
- [ ] None for this PR. (Secret-rotation blocker tracked in companion repo-hygiene PR #44.)

---

## 2026-05-01: Repo hygiene PR (token-efficiency follow-up)

### Completed
- [x] Untracked `mcp-servers/` (18 178 files) via `git rm -r --cached`. Files remain on disk; reinstate via new `make mcp-install` target.
- [x] Untracked `dev.db` and `.env`; dropped the `!dev.db` exception from `.gitignore`.
- [x] Added `make mcp-install` target to `Makefile` for reproducible MCP-server install.
- [x] ADR appended to `docs/decisionLog.md` ("2026-05-01: Repo hygiene — untrack mcp-servers/, dev.db, .env").

### Status
- [x] **Merged as PR #44** (2026-05-01).

### Blockers
- [!] **Secret rotation required** — values that lived in the tracked `.env` (`SECRET_KEY`, `WTF_CSRF_SECRET_KEY`, `API_KEY_SECRET`, `GEMINI_API_KEY`, plus Redis host/port) are in public Git history. Untracking does not rewrite history. Owner must:
  1. Rotate `GEMINI_API_KEY` at Google AI Studio.
  2. Generate fresh `SECRET_KEY`, `WTF_CSRF_SECRET_KEY`, `API_KEY_SECRET` (any 32+ char random) and replace in the local `.env`.
  3. Decide whether to run `git filter-repo` to scrub history (irreversible, breaks any open forks/PRs).

---

## 2026-04-30: Token-efficiency pass

### Done

- **A1** Untracked `mcp-servers/` from git (505 MB / 18 178 files) — already in
  `.gitignore`, was committed before that. Cuts agent search/index noise.
- **A2** Replaced `.antigravityrules` (72 lines, ~70 % overlap with `AGENTS.md`)
  with a thin pointer file. `AGENTS.md` is now the single source of rules.
- **A3** Moved `docs/audits/*` → `docs/archive/audits/` and the bulk of
  `docs/progress.md` → `docs/archive/progress-pre-2026-04-29.md`.
- **A4** Added `docs/INDEX.md` — explicit map of "always-on vs on-demand vs
  archive" docs so agents only load what they need.
- **B1** Wired `Flask-Compress` (gzip + brotli) in `app.py::register_extensions`.
  Disabled in `TESTING` so unit tests stay byte-comparable.
- **B2** `ProductionConfig`: `JSONIFY_PRETTYPRINT_REGULAR=False`,
  `JSON_SORT_KEYS=False`. Removes whitespace from all JSON responses.
- **B3** `ProductionConfig.SEND_FILE_MAX_AGE_DEFAULT=31_536_000` — 1-year cache
  for `/static` (icons, CSS, JS). Bust by changing the static file path.
- **B4** Added `?fields=` query parameter support in `services/api.py` via
  `_parse_fields_param` + `_project`, plumbed through `paginate_query`.
  Clients can request `GET /api/managers?fields=id,name,country_code` to skip
  fields they don't need. Fully opt-in (no default change → tests unchanged).
- **C1** Confirmed `paginate_query` already enforces `max_per_page=100`.
- **C2** Added `joinedload`/`selectinload` to:
    - `GET /api/managers` (was N+1 on `country.code` and `len(achievements)`).
    - `GET /api/managers/<id>` (was N+1 on each achievement's type/league/season).
    - `GET /api/achievements` (was N+1 on type/league/season/manager).

### Verification

- `venv/bin/pytest tests --ignore=tests/e2e` → **415 passed** (after `fix(metrics)`).

### Status
- [x] **Merged as PR #43** (2026-05-01). Includes follow-up `fix(metrics)` removing
  the `TESTING` gate on Prometheus init and cleaning `prometheus_client.REGISTRY` in
  `reset_metrics()`, which unblocks the pre-existing `test_first_app_initializes_metrics`
  failure that was already red on `main`.

### Open work after this PR

- Optional follow-up: extend `?fields=` from listing endpoints to single-record
  endpoints (`GET /api/managers/<id>`, `GET /api/achievements/<id>`). No ticket;
  pick up if a client requests it.

---

## Project Metrics (as of 2026-05-01)

- **Total Tests:** 415 unit/integration passing + 42-scenario Playwright e2e
  smoke (manual) + 23/27 deep-probe checks.
- **Code Coverage:** ~87 % (target threshold).
- **Repo size on disk:** −505 MB after A1 (`mcp-servers/` no longer tracked).
- **Architecture:** Application Factory + blueprints + services + Flask-Compress
  for HTTP responses.

---

_Last updated: 2026-05-01 — cleanup pass (docs sync, branch prune, backlog drain)._
