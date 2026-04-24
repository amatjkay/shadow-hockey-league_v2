# Active Context — Shadow Hockey League v2

> **Purpose:** This file tracks the current focus of work, recent changes, and immediate
> next steps. All agents MUST read this before starting any task.

---

## Current Focus

**Phase:** Feature Development Initialization
**Status:** ✅ Stabilization phase complete. System is ready for feature development.

---

## Status

- **Branch:** `feature/admin-enhancement` (merged from `fix`)
- **Goal:** Finalize stabilization of Admin Achievement infrastructure.
- **Seeding Status:** ✅ Database seeded and point alignment verified.

## Recent Changes (2026-04-24)

- **Admin Achievement Management**: Stabilized the achievement management workflow.
  - Consolidated `manager_edit.html` into a single AJAX-powered modal workflow.
  - Automated achievement field calculation in `services/admin.py` via `on_model_change`.
  - Centralized icon resolution in `AchievementType.get_icon_url()` with support for custom overrides.
  - Synchronized API responses and client-side scripts to use centralized icon logic.
  - Removed duplicate `AchievementModelView` class to prevent shadowed configuration.
  - Fixed JS syntax errors and standardized selectors in `achievement_create.html`.
- **Testing**: Implemented and verified `tests/test_admin_achievements.py` (100% pass rate).

- **Architecture Refactoring**: Isolated Flask-Admin/WTForms compatibility monkey-patches into `utils/patches.py`. Applied globally in `app.py`.
- **Frontend Cleanup**: Externalized large inline JavaScript blobs from `services/admin.py` into `static/js/admin/autofill.js`.
- **Environment Stabilization**: Removed legacy Windows `.bat` files. Verified `Makefile` as the primary task runner for Linux.
- **Quality Assurance**: Configured `.flake8` and `mypy` (via `pyproject.toml`).
- **E2E Testing**: Performed full manual and automated E2E verification of the leaderboard, admin panel, and point system.
- **Data Stabilization**: Aligned database point system with application logic and fixed reference data seeding.
- **Asset Resolution**: Resolved broken flag images on Linux via case-insensitive normalization.

---

## Immediate Next Steps

- [x] Merge `fix` into `feature/admin-enhancement`.
- [ ] Implement **Historical Season View** (filtering leaderboard by past seasons).
- [ ] Implement **Team-based Filtering** (filtering by specific hockey teams).
- [ ] Enhance **Admin Bulk Import** (CSV upload for achievements).

---

## Active Blockers

- [!] **Network Restriction**: Cannot install new Python packages via `pip`. Using pre-installed tools in `venv`.

---

## Notes for Next Agent

- **Monkey-Patches**: Now located in `utils/patches.py`. Applied via `apply_patches()` in `app.py`.
- **Admin JS**: Shared logic is in `static/js/admin/autofill.js`.
- **Testing**: Use `venv/bin/pytest`. Full suite takes ~1 minute.
- **Database**: `dev.db` is the primary SQLite database. Schema checks via `sqlite` MCP server recommended before mutations.

---

_Last updated: 2026-04-24_
