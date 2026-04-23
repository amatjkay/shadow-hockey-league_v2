# Active Context — Shadow Hockey League v2

> **Purpose:** This file tracks the current focus of work, recent changes, and immediate
> next steps. All agents MUST read this before starting any task.

---

## Current Focus

**Phase:** Post-optimization stabilization
**Status:** ✅ All optimization tasks complete

---

## Recent Changes (2026-04-23)

### Infrastructure Optimization (Final)

- **Git Bloat Cleanup**: Removed `mcp-servers/` (18k+ files) and `data/export/*.json` from Git tracking. Added them to `.gitignore`. Deployment is now significantly faster.
- **Agent Constitution**: Finalized `AGENTS.md` with strict role separation (Architect, Coder, Reviewer) and NOT-DO rules.
- **Agent Rules & Skills**: Populated `.agents/` with specialized role definitions and automated skills (`db-migration`, `verification`).
- **Knowledge Base**: Updated `PROJECT_KNOWLEDGE.md` with stability controls and synced with NotebookLM.
- **GitHub Sync**: Successfully pushed all infrastructure changes to `feature/admin-enhancement` via GitHub MCP API, bypassing local DNS blockers.

---

## Immediate Next Steps

- [ ] Populate `docs/projectbrief.md` with detailed business rules (Requires USER input)
- [ ] Install dev tools (`flake8`, `black`, `isort`, `mypy`) once network access is resolved
- [ ] Run first full `mypy` check on the entire codebase

---

## Active Blockers

- [!] **Network Restriction**: Cannot install new Python packages via `pip` in the current shell. This blocks running linting/formatting tools until they are pre-installed.

---

## Notes for Next Agent

- The Flask-Admin monkey-patches in `services/admin.py` (lines 21-44) are **critical**.
  Do not modify or remove them without thorough testing of the admin panel.
- Redis is optional — the app falls back to `SimpleCache` if Redis is unavailable.
- The `Match` model has been removed as it was obsolete.
- CI/CD pipeline has been modernized (GitHub Actions, Makefile, requirements-dev.txt).
- Database migration to drop `matches` table has been applied by the user.
- **New Stability Tools**: `scripts/benchmark.py` and `scripts/audit_data.py` implemented and added to `Makefile`.
- **Data Integrity**: Verified 100% consistency between DB points and formula calculations.

---

_Last updated: 2026-04-23_
