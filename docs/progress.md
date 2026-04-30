# Progress — Shadow Hockey League v2

> **Purpose:** Living document tracking only the **current** cycle of work.
> All agents MUST update this before ending their turn.
>
> Older sections live in `docs/archive/progress-pre-2026-04-29.md`.

## Token-efficiency pass (2026-04-30)

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

- `venv/bin/pytest tests --ignore=tests/e2e` → **402 passed** (unchanged).

### Open work after this PR

- **Phase D / E / F / G / H** of the post-audit testing campaign continue
  unchanged. See `docs/activeContext.md` for the full plan.
- Optional follow-up: extend `?fields=` from listing endpoints to single-record
  endpoints (`GET /api/managers/<id>`, `GET /api/achievements/<id>`).

---

## Project Metrics (as of 2026-04-30)

- **Total Tests:** 402 unit/integration passing + 42-scenario Playwright e2e
  smoke (manual) + 23/27 deep-probe checks.
- **Code Coverage:** ~87 % (target threshold).
- **Repo size on disk:** −505 MB after A1 (`mcp-servers/` no longer tracked).
- **Architecture:** Application Factory + blueprints + services + Flask-Compress
  for HTTP responses.

---

_Last updated: 2026-04-30 — token-efficiency pass._
