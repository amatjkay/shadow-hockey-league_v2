# Decision Log

## 2026-05-03: TIK-51 tech-debt continuation — pip-audit, mypy, coverage gate, e2e in CI

**Context**: Post-TIK-42, three latent tech debts remained: (1) `pip-audit` was
not in CI, so dependency CVEs were caught only on demand; (2) `mypy` had been
disabled in CI (TIK-39 was a one-shot cleanup, no enforcement); (3) coverage on
`services/blueprints/app/models` had only reached 84% (target ≥ 87%); (4) the
42-scenario Playwright smoke suite ran only locally — regressions in admin
views or auth boundary could land on `main` undetected.

**Decision**:

1. **pip-audit gate (TIK-52)** — runtime CVEs (`requirements.txt`) fail CI;
   dev-only CVEs (`requirements-dev.txt`) are reported but do not fail. The
   `make audit-deps` target is the single entrypoint; the CI step shells out
   to it. Rationale: dev-only CVEs are common (e.g., test runners, formatters
   with transitive issues) and would create noise without buying production
   safety.
2. **mypy back in `make check` and CI (TIK-53)** — re-enabled with the existing
   `mypy.ini` config; fixed all 40 errors on the source tree; 0 errors today.
   Rationale: type safety is cheap to enforce after the one-shot fix and gives
   refactoring confidence. Where Flask-SQLAlchemy session proxies confused mypy,
   we introduced `services/_types.py::SessionLike` rather than `# type: ignore`.
3. **Coverage to 87% (TIK-54)** — added 49 targeted tests on previously low-cov
   files: Redis socket-timeout error paths in `blueprints/health.py`; admin view
   formatters in `services/admin/views.py`; recalc/metrics corner cases; create-
   app failure modes. Did not chase 100% — pragmatic stop where the remaining
   gaps are init guards and dead-on-startup branches.
4. **E2E Playwright smoke as a separate CI job (TIK-55)** — new
   `E2E Smoke (Playwright)` job in `.github/workflows/deploy.yml`, downstream of
   `quality-and-tests` and upstream of `deploy`. Same script as local
   (`tests/e2e/test_smoke.py`); `scripts/create_e2e_admin.py` provisions the
   `e2e_admin` super-admin idempotently. Rationale for keeping it separate from
   the unit-test job: e2e wants Redis service + browser binaries + a live dev
   server boot, all of which would slow `quality-and-tests` substantially even
   on green runs.

**Rationale**:
- All four debts had been listed in `docs/activeContext.md` as outstanding
  follow-ups. Closing them as a coordinated mini-epic (rather than ad hoc)
  ensured consistent CI shape and a single docs sync.
- Keeping `pip-audit` and `mypy` in the same `quality-and-tests` job rather than
  parallel jobs minimises matrix complexity for a low-traffic repo. If queue
  time becomes an issue we can split later.

**Trade-offs**:
- `pip-audit` adds ~10s to CI; `mypy` adds ~6s; e2e job adds ~90s end-to-end on
  fresh runners. Net CI wall-clock for a typical PR went from ~120s to ~210s.
  Worth it for type/security/UI regression coverage on every PR.
- The schema-bootstrap step (`db.create_all()`) in the e2e CI job duplicates
  what `make init-db` does locally. We accept the duplication because the CI
  flow boots a bare runner where `instance/dev.db` doesn't exist; pulling in
  the full Makefile target would drag dev-only build deps.

**Forward contracts**:
- `pip-audit` policy: `--ignore-vuln <ID>` is allowed only with a one-line
  rationale committed alongside the entry; never silence a CVE without
  documenting why.
- `mypy` policy: prefer `cast()` + narrowing over `# type: ignore`; if you must
  use `# type: ignore`, narrow it (`# type: ignore[arg-type]`) and add a
  one-line reason on the same line.
- E2E policy: the suite is a smoke check, not a feature spec. Keep it under
  ~90s wall-clock; if it grows past that, split per-domain jobs (admin vs
  public vs api) rather than one giant matrix.

---

## 2026-05-03: TIK-42 cleanup — 3 monolith→package splits, CC reduction, dedup

**Context**: Post-audit (audit-2026-04-28 closed in PRs #41-#46), three Python files
exceeded 600 LOC (`services/api.py` 920, `blueprints/admin_api.py` 893, `services/admin.py`
635), four functions had cyclomatic complexity ≥ D, and `tests/test_rating_service.py`
contained four duplicate test classes. Coverage on services/blueprints/app was 81%.

**Decision**:

1. **Decompose each large file into a package**, not a flat split:
   - Create `<module>/__init__.py` that owns the Flask `Blueprint` (or `init_admin`
     entrypoint) and re-exports the public symbols.
   - Move per-resource handlers (countries / managers / achievements; ModelViews;
     lookups) into sibling submodules.
   - Submodules import the Blueprint from `__init__.py` and register routes via
     decorator. Circular-import safe because the Blueprint is created BEFORE the
     submodule imports inside `__init__.py`.
   - Keep `from services.api import api`, `from blueprints.admin_api import
     admin_api_bp`, `from services.admin import init_admin` working unchanged so
     consumers (chiefly `app.py`) need no edits.
2. **Cap cyclomatic complexity at C** for hot functions; refactor by extracting
   per-branch helpers (e.g. `_validate_one`, `_persist_batch`, `_render_summary`)
   rather than rewriting business logic.
3. **Dedup tests** by removing duplicate `TestAppRoutes`, `TestSecurityHeaders`,
   `TestValidationService`, `TestAPIEndpoints` classes from
   `tests/test_rating_service.py`. The canonical copies live in their topic-named
   files. Rename `tests/test_e2e.py` → `tests/integration/test_smoke_endpoints.py`
   because it uses Flask test client, not Playwright — the previous name lied.
4. **Archive `scratch/` to `scripts/oneoff/`** with a README explaining provenance,
   instead of deleting. One-off prod-sync scripts retain historical reference and
   stay out of agent search via `pyproject.toml` exclusions.
5. **Coverage boost** via targeted error-path tests in `recalc_service` /
   `metrics_service` / `app.py`. Did not chase 100% — pragmatic stop at the
   exception handlers and singleton corner cases.
6. **Stack landing**: PRs #47-#54 stacked into each other instead of main. After the
   user merged them sequentially they all collapsed into PR #55 (the final stack
   head). Resolved 2 conflicts against TIK-43 (#47, which had landed independently)
   by keeping HEAD — the splits already incorporated the canonical cache import.
7. **Verification**: 423 unit/integration tests pass; six-test smoke run on `main`
   covers all 3 split packages via UI (leaderboard, public API, admin login,
   manager list, lookup endpoint).

**Rationale**:
- Package-level decomposition beats flat split because per-resource files become
  navigable and reviewable in isolation, while the `__init__.py` stays the only
  place that knows about cross-resource glue.
- Backward-compat re-exports remove churn: no consumer change in `app.py`, no
  fixture change in tests, no doc change for "where does X live".
- Capping CC at C (not B) keeps reviews short — going below C usually means
  splitting a meaningful business operation across files for cosmetic reasons.

**Trade-offs**:
- More files, deeper directory tree. Mitigated by `docs/INDEX.md` map and the
  `codebase-map` skill.
- Coverage on `app.py` and `recalc_service` still below 87% target. Closing the
  gap fully needs end-to-end fixtures, which were out-of-scope.
- `services/admin/views.py` is still 342 LOC. Splitting per-ModelView file would
  be cosmetic — kept as a single file because all views share the `SHLModelView`
  base patterns and reading them together helps debugging.

**Source**: `docs/progress.md` 2026-05-03 entry; PRs #47-#55; Linear epic TIK-42.

---

## 2026-04-30: Token-efficiency pass

**Context**: Owner asked to "make the system efficient and consume fewer tokens
in requests/responses". The repo was loading 505 MB / 18 178 vendored MCP files
into git and ~3 000 lines of duplicated agent-context docs into every AI
session, and HTTP responses were uncompressed.

**Decision**:

1. **Stop tracking `mcp-servers/` in git** (already in `.gitignore`, was
   committed before that). Cuts agent search/index noise drastically.
2. **`AGENTS.md` becomes the single source of agent rules.** `.antigravityrules`
   reduced to a thin pointer file. Docs split into "always-on / on-demand /
   archive" via `docs/INDEX.md`. `docs/audits/*` and pre-2026-04-29 `progress.md`
   sections moved under `docs/archive/`.
3. **HTTP responses compressed at the framework level**: `Flask-Compress`
   (br + gzip, level 6, ≥500 B) wired in `app.py::register_extensions`.
   Skipped in `TESTING` so unit tests stay byte-comparable.
4. **JSON minified in production**: `JSONIFY_PRETTYPRINT_REGULAR=False`,
   `JSON_SORT_KEYS=False` on `ProductionConfig`.
5. **Static assets cached for 1 year**: `SEND_FILE_MAX_AGE_DEFAULT=31_536_000`
   on `ProductionConfig`. Bust by editing the asset path / hash.
6. **Optional client-side field selection**: `?fields=id,name,...` on any
   paginated `/api/*` listing endpoint. `id` is always preserved. Fully
   opt-in (no default change).
7. **N+1 fixes** on three hot listing endpoints (`/api/managers`,
   `/api/managers/<id>`, `/api/achievements`) via `joinedload` /
   `selectinload`.

**Rationale**:
- AI-agent context files and the 18 178-file `mcp-servers/` dump were the
  largest hidden cost — every grep/list/index pulled them.
- Framework-level HTTP compression beats per-endpoint shrinkage and is safe
  to enable globally because the mimetype allow-list excludes already-compressed
  formats.
- `?fields=` is opt-in so existing clients are unaffected.
- The N+1 fixes are pure performance; serialisation output is byte-identical.

**Forward contracts** (do not regress):
- `Flask-Compress` MUST stay disabled in `TESTING` (otherwise `response.data`
  in test clients comes back as compressed bytes and assertions break).
- `mcp-servers/` MUST remain in `.gitignore`. Don't `git add mcp-servers/`.
- `paginate_query` is the canonical pagination helper. New listing endpoints
  should go through it so they pick up `?fields=` for free.

**Status**: PR open against `main`. CI must pass before merge.

---

## 2026-05-01: Sub-agents + skills + SHL-OPTIMIZER prompt v2.0

**Context**: Token-economy audit of the project surfaced three structural sources of waste — heavy Memory Bank files read whole every turn (`docs/progress.md` 258 lines, `docs/decisionLog.md` 150 lines, `docs/API.md` 590 lines), the three biggest source modules read whole rather than indexed (`blueprints/admin_api.py` 893, `services/api.py` 861, `services/admin.py` 635), and duplicated coding-standards rules across `AGENTS.md` / `.antigravityrules` / `PROJECT_KNOWLEDGE.md` / `docs/techContext.md`. The pre-existing role topology (`architect`, `coder`, `reviewer`) had no role responsible for finding or fixing this waste, and no skill catalog covered "how to read a heavy file without reading the whole thing."

**Decision** — implement all of:

1. **Two new sub-agents** under `.agents/agents/`:
   - `token-auditor` — finds token waste in repo, prompts, Memory Bank. Read-only with respect to source code; allowed edits limited to `.gitignore`, `Makefile`, `docs/INDEX.md`, Memory Bank, `.agents/prompts/`.
   - `doc-curator` — rotates `progress.md` / `decisionLog.md` entries older than ~30 days into `docs/archive/<period>.md`. Verbatim move-only; no rewording or content deletion; preserves ADR forward-contracts.

2. **Three new skills** under `.agents/skills/`:
   - `token-budget` — token-cost heuristics (tokens/line per artefact type) + lazy-load patterns + per-call self-check before reading any file > 200 lines.
   - `doc-rotation` — quarterly archive workflow with safety rules and rollback via `git revert`.
   - `codebase-map` — `grep -n '^def\|^class'` recipes + `sed -n 'A,Bp'` read-window pattern; replaces full-file reads of the three heaviest modules.

3. **SHL-OPTIMIZER prompt v2.0** under `.agents/prompts/`:
   - `shl-optimizer.prompt.md` — single role-router with three robustness guards (empty/garbage input, unknown-task classification, multi-role requests). Parametrized via `{{PROJECT_FACTS}}` so the same skeleton applies to other Flask projects.
   - `shl-optimizer.fewshot.md` — one example per role; loaded lazily on first activation per session via `@include` in Instructions §4 (NOT inlined into the system prompt every turn).

4. **`docs/INDEX.md`** — single read-trigger map for `docs/*` plus the Memory Bank files. Tells agents which file to read for which trigger and the recommended `head`/`tail`/`grep` cap. The "forbidden full-read" list covers `progress.md`, `decisionLog.md`, `API.md`, and `mcp-servers/**`.

5. **`AGENTS.md` §3 amendments** — roles table extended with the two new sub-agents and a "Detailed role file" column; NOT-DO constraints added; Handoff Protocol entries plug the new roles into the existing `architect → coder → reviewer` flow; new "Skills" sub-section listing all 7 skills (4 existing + 3 new).

**Rationale**:

- Two new roles instead of extending existing ones because both have *read-only-with-respect-to-source* constraints that don't fit the existing `coder`/`reviewer` mandate. Mixing them risks accidental source rewrites under "let coder also do token cleanup".
- Lazy `@include` of fewshot (rather than inline) avoids paying the ~1.6k-token cost of fewshot examples on every turn when only one role is active.
- Move-only rotation (no rewording) ensures historical record stays auditable; ADR forward-contracts can be referenced years later without "we summarised it" loss.
- `docs/INDEX.md` as a read-trigger map is the smallest possible thing that lets agents avoid full-file reads of the heavy docs.
- `{{PROJECT_FACTS}}` parametrization separates project-specific facts (stack, sources of truth, invariants) from the generic role-router skeleton, so the same prompt can be reused on other Flask projects with a single replacement.

**Status**: Implemented in PR #45. Companion to PR #44 (repo-hygiene) but mergeable independently.

**Forward contracts** (do not regress):

- `shl-optimizer.fewshot.md` MUST be loaded only via `@include` from Instructions §4 of `shl-optimizer.prompt.md` — never inlined into the system prompt and never duplicated in the `## Few-shot` section of the prompt file.
- `docs/archive/<period>.md` is the **only** destination for rotated `progress.md` / `decisionLog.md` entries. Never `git rm` historical records.
- `docs/INDEX.md` MUST be updated whenever an archive file is added under `docs/archive/`.
- `token-auditor` and `doc-curator` MUST NOT modify source code or test files. If a token-waste fix requires source/test changes, hand off to `coder`.
- `progress.md`, `decisionLog.md`, `docs/API.md`, and `mcp-servers/**` are on the `forbidden_full_read` list — agents must use `grep -n` + section-only reads.

---

## 2026-05-01: Repo hygiene — untrack mcp-servers/, dev.db, .env

**Context**: Despite `.gitignore` listing `mcp-servers/`, `*.db`, and `.env`, all three were still tracked in `main`:
- `mcp-servers/` — 18 178 files / ~505 MB of Node dependencies committed in `cbf3f48`.
- `dev.db` — 155 KB SQLite snapshot kept tracked via the explicit `!dev.db` exception in `.gitignore`.
- `.env` — committed alongside the initial repo despite `.env` being gitignored on its own line.

This contradicts the prior 2026-04-23 ADR ("Removal of mcp-servers from Git") and the 2026-04-21 commit `5ffe365` ("chore(security): untrack .env and vendored mcp-servers"). Both attempts left main in the same state — vendored deps + dev DB + `.env` tracked. Dangling commit `d1361f2` re-did the untrack on 2026-04-30 but never landed on `main`.

**Decision**: One consolidated PR removes all three from version control via `git rm --cached` (files stay on disk for active dev environments), drops the `!dev.db` exception, and adds `make mcp-install` so contributors can reinstate `mcp-servers/` locally via `npm install`.

**Rationale**:
- `mcp-servers/` is `node_modules`-like — must be reproducible from a manifest, not vendored. Tracked vendoring inflates clone size, slows `git status`/`grep`/`find`, and pollutes every agent's context window.
- `dev.db` is a local development artifact; reproducible from `make seed-db`.
- `.env` is a secret store. Values currently in the file (`SECRET_KEY`, `WTF_CSRF_SECRET_KEY`, `API_KEY_SECRET`, `GEMINI_API_KEY`, plus Redis host/port) MUST be treated as **compromised** since they have lived in public Git history since the initial commit. **Action required: rotate every secret in `.env` before/after this PR merges.** New values go into a fresh local `.env` (template lives in `.env.example`).

**Implementation**:
1. `git rm -r --cached mcp-servers/` (18 178 files removed from tracking; on-disk copies untouched).
2. `git rm --cached dev.db .env`.
3. `.gitignore`: drop `!dev.db` exception.
4. `Makefile`: add `mcp-install` target that runs `npm install` inside `mcp-servers/` when a `package.json` exists.
5. ADR (this entry) and `docs/progress.md` updated per Memory Bank protocol.

**Status**: Implemented in PR `devin/<ts>-repo-hygiene`.

**Forward contracts**:
- Never re-add `mcp-servers/` to tracking. Reinstall via `make mcp-install` (or `cd mcp-servers && npm install`).
- Never re-add `dev.db`. Recreate via `make init-db`.
- Never commit `.env`. Use `.env.example` as the only template.

---

## 2026-04-29: Audit-2026-04-28 remediation completed (Phases 2A–3)

**Context**: External audit on 2026-04-28 surfaced 11 deep-probe e2e bugs (B1–B11) plus stale PR/branch debt. Owner approved a phased remediation plan (`docs/audits/audit-2026-04-28-plan.md`) with sequential PRs (one in flight at a time, owner-merged via GitHub UI).

**Decision** — implement and merge:

1. **Phase 2B** (PR #32 / TIK-37 / B10) — `socket_timeout=1.0` on `redis.Redis()` in `blueprints/health.py` so `/health` cannot block for 5–7 s when Redis is degraded. Regression test in `tests/test_blueprints.py`.
2. **Phase 2B** (PR #33 / TIK-38 / B11) — `/metrics` startup banner now derived from `services/metrics_service` constants (`METRICS_PREFIX` + `DEFAULT_METRIC_SUFFIXES`) so the announce-line cannot drift from `prometheus_flask_exporter`.
3. **Phase 2C** (PR #34 / TIK-16) — replaces stale PR #16. Single shared `Limiter` instance in `services/extensions.py`, wired via `init_app(app)` with Redis storage in production / memory fallback in dev/test. All 15 API endpoints use `@limiter.limit(...)`. Devin Review caught a seed-data bug in `tests/test_api.py` (TOP1/TOP2/TOP3 base points) — fixed in commit `06dafeb`.
4. **Phase 2C** (PR #35 / TIK-17) — replaces stale PR #17. New helper `services/scoring_service.py::get_base_points(ach_type, league)` is the only correct way to look up base points. Reads `League.base_points_field` (which honours `parent_code`) so subleagues inherit from parent. Tightened `validation_service` (format regex `^[1-9]\d*(\.\d+)?$` + business rule that L1 is flat).
5. **Phase 3** (PR #38 / TIK-36 / B9) — `register_audit_request_hook(app)` in `services/audit_service.py`, wired from `app.py::register_extensions` after `init_admin`. The hook is a `@app.before_request` handler that copies `flask_login.current_user.id` into `g.current_user_id`, so the existing `after_flush` listener finally writes to `audit_logs` for admin CRUD. Three regression tests in `tests/integration/test_audit_logging.py::TestAuditRequestHook`.

**Rationale**:
- Each phase is a separate, sequentially-merged PR — minimises blast radius.
- Old PR #16 and #17 cherry-picked rather than merged in-place because their base branch (`devin/integration-analyst-fixes`) was abandoned and full of unrelated noise.
- Owner gates every merge via GitHub UI; agent only opens PRs.

**Status**: All five PRs merged. Phase 4 (linter debt — mypy/flake8 documentation + Linear epics) still pending. See `docs/audits/audit-2026-04-28-plan.md` for full execution table.

**Forward contracts** (do not regress):
- `services/extensions.py::limiter` is the single Limiter instance for the whole app.
- `services/scoring_service.py::get_base_points()` is the only entry point for base-points lookup. **Never compare `league.code == "1"` directly.**
- `register_audit_request_hook(app)` MUST be called from `app.py::register_extensions` after `init_admin`. If removed, `audit_logs` silently stops being written.

---

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
