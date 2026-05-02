# Progress — Shadow Hockey League v2

> **Purpose:** Living document tracking only the **current** cycle of work.
> All agents MUST update this before ending their turn.
>
> Older sections live in `docs/archive/progress-pre-2026-04-29.md`.

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
