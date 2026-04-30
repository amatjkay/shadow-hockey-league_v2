# Decision Log

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
