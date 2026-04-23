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
