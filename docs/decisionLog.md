# Decision Log — Shadow Hockey League v2

> **Purpose:** Architectural Decision Records (ADRs) for significant technical choices.
> Each entry documents the context, decision, rationale, and consequences.

---

## ADR-001: SQLite as Production Database

**Date:** 2024 (project inception)
**Status:** Active

### Context
The project needed a simple, file-based database that could be easily deployed on a VPS
without requiring a separate database server process.

### Decision
Use SQLite with SQLAlchemy 2.0 ORM and Alembic for migrations.

### Rationale
- Zero-config deployment — no PostgreSQL/MySQL process to manage
- File-based backups — simple `cp dev.db dev.db.bak`
- Sufficient for expected load (single admin, moderate API traffic)
- SQLAlchemy abstraction allows future migration to PostgreSQL if needed

### Consequences
- No true concurrent write support — tests use thread-safety workarounds
- No `ARRAY`, `JSON`, or advanced column types — using `Text` with JSON strings
- Alembic migrations are the only safe way to modify schema

---

## ADR-002: Redis with SimpleCache Fallback

**Date:** 2024
**Status:** Active

### Context
Leaderboard queries with rating calculations are expensive. Caching was needed,
but Redis availability couldn't be guaranteed on all environments.

### Decision
Use Flask-Caching with Redis as primary backend and `SimpleCache` as automatic fallback.

### Rationale
- Redis provides shared cache across Gunicorn workers in production
- SimpleCache works for development and testing without Redis dependency
- Tests use `_FakeRedis` (in-memory mock) for deterministic behavior

### Consequences
- Cache invalidation must be explicit — no TTL-based auto-refresh for data mutations
- `invalidate_leaderboard_cache()` must be called after every CREATE/UPDATE/DELETE

---

## ADR-003: Flask-Admin with Monkey-Patches

**Date:** 2025
**Status:** Active — Critical

### Context
Flask-Admin 2.0.2 has incompatibilities with WTForms 3.x and its own `BaseView._run_view`.

### Decision
Apply targeted monkey-patches in `services/admin.py` rather than pinning older library versions.

### Rationale
- Pinning WTForms < 3.0 would block security patches
- Upstream Flask-Admin fixes are slow to release
- Patches are minimal (2 functions) and well-documented

### Consequences
- ⚠️ Patches must be tested after any Flask-Admin or WTForms upgrade
- Patches are clearly marked with comments and docstrings explaining the fix

---

## ADR-004: Denormalized Points on Achievement Records

**Date:** 2024
**Status:** Active

### Context
The rating formula `base_points × season_multiplier` could be calculated on-the-fly,
but this would require joining 3 tables for every leaderboard render.

### Decision
Store `base_points`, `multiplier`, and `final_points` directly on each `Achievement` row.

### Rationale
- Eliminates expensive JOINs for the most frequent query (leaderboard)
- Points are recalculated automatically via `recalc_service.py` when base values change
- SQLAlchemy event listeners trigger recalculation on `AchievementType` or `Season` updates

### Consequences
- Data redundancy — must ensure recalculation triggers are reliable
- Bulk imports must calculate points correctly at insert time

---

## ADR-005: Agent Architecture with Memory Bank

**Date:** 2026-04-23
**Status:** Active

### Context
Multiple AI agents working on the project need shared context, consistent standards,
and safety guardrails to prevent destructive actions.

### Decision
Implement a Memory Bank (`docs/`) + Subagent definitions (`.agents/`) + Skills
(`.agents/skills/`) architecture governed by `AGENTS.md`.

### Rationale
- Memory Bank provides persistent context across agent sessions
- Subagent roles prevent context window bloat by separating concerns
- Skills enable reusable, auditable workflows for common operations
- `AGENTS.md` serves as a single constitution all agents must follow

### Consequences
- Agents must read context files before acting (adds startup overhead)
- `docs/progress.md` must be maintained as a living document
- New skills can be added incrementally without modifying core architecture

---

## ADR-005: Season `25/26` is the Current Baseline (multiplier 1.00)

**Date:** 2026-04-27
**Status:** Active

### Context
README.md and `docs/projectbrief.md` disagreed on which season carries the baseline
multiplier of 1.00. README listed `24/25` as current; `projectbrief.md`,
`services/rating_service.SEASON_MULTIPLIER`, and the `seasons` reference table
all point to `25/26`.

### Decision
The current season is **`25/26`**. Past seasons receive a 5% per-year discount:
`24/25=0.95`, `23/24=0.90`, `22/23=0.85`, `21/22=0.80`. Source of truth is the
`seasons` DB table; the hardcoded `SEASON_MULTIPLIER` constant in
`services/rating_service.py` is a fallback only.

### Rationale
Code and the more recent project brief already reflect `25/26`. README simply
fell out of sync. Aligning documentation prevents incorrect business assumptions
when new managers/achievements are imported for the just-finished `25/26`
season.

### Consequences
- README.md updated to list `25/26..21/22`.
- `docs/ARCHITECTURE.md` test count corrected (`381 → 383`).
- Any future shift of the baseline (when `26/27` opens) requires:
  1. Updating the `seasons` table.
  2. Updating `services/rating_service.SEASON_MULTIPLIER` fallback.
  3. Appending a new ADR entry here.

---

## ADR-006: Untrack `.env` and vendored `mcp-servers/`; switch MCP servers to `npx`/`uvx`

**Date:** 2026-04-27
**Status:** Active (Phase 1 — working tree). Phase 2 (history rewrite via `git filter-repo`) pending owner approval.

### Context
- `.env` was tracked in `main` (blob `3b9c79c8…`) and contained a real third-party API key.
  Root cause: `.gitignore` was wrapped in Markdown code fences (` ``` ` on lines 1 and 63),
  making every rule (including `.env`) inert.
- `mcp-servers/` was a committed `node_modules`-style tree (505 MB, 18 178 files in the index),
  bloating clones and CI checkout.
- `AGENTS.md §4` describes 8 MCP servers but the repo had no client config, so the rules
  were descriptive only.

### Decision
1. Fix `.gitignore` (drop fences, add explicit rules for `.env*`, `mcp-servers/`, `node_modules/`,
   `*.db`, IDE artefacts).
2. `git rm --cached .env` and `git rm -r --cached mcp-servers/` — keep working-tree copies but
   stop tracking.
3. Add `.windsurf/mcp_config.example.json` describing all 8 servers from `AGENTS.md §4`,
   launched via `npx`/`uvx` with secrets via `${env:VARNAME}`.
4. Replace hard-coded `/home/tiki/...` paths in `docs/techContext.md` and
   `.agents/skills/db-migration/SKILL.md` with `<PROJECT_ROOT>`.
5. Document `GEMINI_API_KEY` in `.env.example` as an optional, never-committed variable.
6. Defer git-history rewrite to a separate, owner-approved phase (`git filter-repo --path .env
   --path mcp-servers/ --invert-paths` followed by force-push and a coordinated re-clone).

### Rationale
- Phase 1 is non-destructive and enforceable on-merge: the broken `.gitignore` was the root
  cause of the leak and must be fixed regardless of the history rewrite.
- Vendoring 505 MB of npm packages slows every clone and CI run; `npx` resolves the same
  packages on-demand and stays in sync with upstream patches.
- A single source of truth for MCP wiring (`.windsurf/mcp_config.example.json`) makes
  `AGENTS.md §4` operational rather than aspirational.
- Splitting Phase 1 (untrack) from Phase 2 (history rewrite) avoids force-pushing without
  explicit approval and lets the leaked credential be rotated independently.

### Consequences
- The leaked credential remains in git history until Phase 2 completes — the owner must
  rotate (or has rotated) the key out-of-band; the value alone is not sufficient evidence
  of safety.
- Existing local clones still contain `mcp-servers/` until users run `git clean`/re-clone.
- `notebooklm` MCP entry is `disabled: true` in the template (no official server published);
  enabling requires choosing a vetted community package.
- Conflict between `AGENTS.md §3` (`coder` not allowed `sqlite`) and the `db-migration` skill
  (built on `sqlite` MCP) is **left untouched in this PR** and tracked as an open item to be
  resolved in a follow-up.

---

_Template for new entries:_

```markdown
## ADR-NNN: [Title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Active | Deprecated | Superseded by ADR-XXX

### Context
[What problem or situation prompted this decision?]

### Decision
[What was decided?]

### Rationale
[Why was this the best option?]

### Consequences
[What are the trade-offs and implications?]
```
