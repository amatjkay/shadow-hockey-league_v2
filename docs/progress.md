# Progress Log — Shadow Hockey League v2

> **Purpose:** Living document tracking completed work, in-progress tasks, and blockers.
> All agents MUST update this before ending their turn.

## 2026-04-27: Analyst Audit — Documentation & Security

### Completed
- [x] Full repo audit produced (artifact in Devin session). 20 decomposed tasks
      (T-001..T-020) recorded.
- [x] **T-001** — `.env` removed from git tracking; `.gitignore` cleaned of
      stray markdown fences; `.env.example` updated (documented `GEMINI_API_KEY`,
      removed Windows-only DB path). PR #13 → `devin/integration-analyst-fixes`.
- [x] **T-005, T-006, T-018, T-019** — Documentation sync:
      `README.md` season table corrected to `25/26..21/22`; test count `296 → 383`;
      coverage badge dropped (was static, misleading); env-vars table refreshed.
      `docs/ARCHITECTURE.md` test count `381 → 383`. ADR-005 added to
      `docs/decisionLog.md` recording season baseline decision. PR #14 merged into
      `devin/integration-analyst-fixes`.
- [x] **T-002 + T-011** — Rate limiter unified into a single `services.extensions.limiter`
      Flask-Limiter instance bound via `init_app`. Storage URI is read from
      `REDIS_URL` (production) with `memory://` fallback; `RATELIMIT_ENABLED`
      mirrors `TESTING` so test suite isn't slowed by 50/hour defaults.
      `services/api.py` now uses `@limiter.limit("100 per minute")` for all
      15 REST endpoints (was the dead `@api_limiter` instance). Added
      `tests/test_api.py::TestAPIRateLimiting` proving the 101st request to
      `/api/countries` returns 429 (test count `383 → 384`). PR #16.
- [x] **T-003 + T-004 + T-007 + T-020** — Unified points calculation through
      `League.base_points_field` (parent_code-aware). New `services/scoring_service.py`
      exports `get_base_points(ach_type, league)` used by `services.api`,
      `services.rating_service`, `services.admin`, and `blueprints.admin_api`
      — every `league.code == '1' ? base_points_l1 : base_points_l2` branch
      replaced. `services.rating_service._get_base_points_from_db` rewritten
      to iterate `League` objects (was league_code strings). Validation in
      `services.validation_service.validate_achievement_data` now accepts the
      format `N` or `N.M` (`1`, `2`, `2.1`, `3.5`, ...) and rejects only
      malformed codes and L1 subleagues (per business rule “L1 has no
      subleagues”). Test count `384 → 390` (added 4 scoring-helper tests +
      2 validation format tests; 1 obsolete test repurposed).

### In Progress
- [ ] **T-009** — make `audit_service.log_action` transactionally neutral.
- [ ] **T-008** — defer `ApiKey.last_used_at` writes off the request hot path.
- [ ] **T-010** — drop `with db.session.begin()` in `blueprints/health.py`.

### Blockers
- [!] `GEMINI_API_KEY` and other publicly-committed secrets still live in git
      history. PR #13 untracks the file but does **not** rewrite history. User
      must rotate the Gemini key and decide on `git filter-repo` against `main`.

---

## 2026-04-23: Stability & Data Integrity Audit

### Completed
- [x] Created `scripts/benchmark.py` — verified ~0.86ms leaderboard generation time
- [x] Created `scripts/audit_data.py` — verified 100% data integrity and formula consistency
- [x] Updated `Makefile` with `make audit` and `make benchmark`
- [x] User successfully applied `9a30d278d31d` migration
- [x] Host environment updated with Google Chrome for future UI automation
- [x] Verified all core services and blueprints remain stable and fully typed
- [x] Populated `docs/projectbrief.md` with comprehensive business rules and formulas

### In Progress
- [ ] CI/CD pipeline verification on a real PR (Requires GitHub action run)

### Blockers
- [!] CI/CD pipeline on GitHub will fail until `requirements-dev.txt` tools are available or installed in the Actions runner (should be handled by the updated workflow automatically).

---

## 2026-04-23: Agent Architecture Setup

### Completed
- [x] Created `AGENTS.md` — project constitution
- [x] Created Memory Bank files (`docs/projectbrief.md`, `techContext.md`, `activeContext.md`, `decisionLog.md`)
- [x] Created subagent definitions (`.agents/agents/architect.md`, `coder.md`, `reviewer.md`)
- [x] Created skill workflows (`.agents/skills/db-migration/`, `feature-research/`, `linear-sync/`)

### In Progress
- [x] Initial documentation phase completed

### Blockers
_None_

---

## 2026-04-22: Optimization & Type Hints (Session 2)

### Completed
- [x] Type hints added to `services/admin.py`
- [x] Type hints added to `blueprints/admin_api.py`
- [x] N+1 query fix in `get_managers()` — added `joinedload(Manager.country)`
- [x] All 383 tests passing
- [x] `PROJECT_KNOWLEDGE.md` updated with optimization section

---

## 2026-04-22: Optimization & Type Hints (Session 1)

### Completed
- [x] Created `PROJECT_KNOWLEDGE.md`
- [x] Type hints added to `app.py`
- [x] Type hints added to `services/rating_service.py`
- [x] Type hints added to `services/api_auth.py`
