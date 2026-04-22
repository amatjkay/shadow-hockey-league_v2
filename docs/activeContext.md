# Active Context — Shadow Hockey League v2

> **Purpose:** This file tracks the current focus of work, recent changes, and immediate
> next steps. All agents MUST read this before starting any task.

---

## Current Focus

**Phase:** Post-optimization stabilization
**Status:** ✅ All optimization tasks complete

---

## Recent Changes (2026-04-23)

### Type Hints (Complete)
- Added Python Type Hints to all primary modules:
  - `app.py` — Application factory, context processors
  - `services/rating_service.py` — Rating calculations, SQLAlchemy event listeners
  - `services/api_auth.py` — API key authentication decorator
  - `services/admin.py` — Flask-Admin views, monkey-patches, helper functions
  - `blueprints/admin_api.py` — All REST API endpoint functions

### N+1 Query Optimization (Complete)
- Fixed N+1 in `get_managers()` endpoint — added `joinedload(Manager.country)` to both
  the standard paginated search and the bulk ID fetch paths.
- Verified existing `joinedload` usage in `get_manager_achievements()` for
  `Achievement.type`, `Achievement.league`, and `Achievement.season`.

### Agent Architecture (Complete)
- Created `AGENTS.md` — project constitution with memory bank protocol and safety guardrails
- Created Memory Bank (`docs/`) — projectbrief, techContext, activeContext, decisionLog
- Created Subagent definitions (`.agents/agents/`) — architect, coder, reviewer
- Created Skills (`.agents/skills/`) — db-migration, feature-research, linear-sync

### Test Verification
- All **383 tests passed** (pytest, 70s runtime)
- No regressions from type hints or query optimizations

---

## Immediate Next Steps

- [ ] Populate `docs/projectbrief.md` with detailed business rules after user clarification
- [ ] Run `flake8` and `black` to verify code style compliance after type hint additions
- [ ] Consider adding `mypy` to CI pipeline for static type checking
- [ ] Review remaining modules for type hint coverage (e.g., `services/cache_service.py`,
      `services/audit_service.py`, `blueprints/main.py`)

---

## Active Blockers

_None at this time._

---

## Notes for Next Agent

- The Flask-Admin monkey-patches in `services/admin.py` (lines 21-44) are **critical**.
  Do not modify or remove them without thorough testing of the admin panel.
- Redis is optional — the app falls back to `SimpleCache` if Redis is unavailable.
- The `Match` model exists in `models.py` but the corresponding services
  (`standings_service.py`, `match_service.py`) were deleted as obsolete. The model is kept
  for potential future use.

---

_Last updated: 2026-04-23_
