# Active Context — Shadow Hockey League v2

> **Purpose:** This file tracks the current focus of work, recent changes, and immediate
> next steps. All agents MUST read this before starting any task.

---

## Current Focus

**Phase:** Feature Expansion
**Status:** ✅ Stabilization & Testing complete. System is stable and optimized.

---

## Status

- **Branch:** `feature/admin-enhancement`
- **Goal:** Feature expansion (Bulk Import, Player Search).
- **Seeding Status:** ✅ Database consolidated and verified.

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

- [x] Fix and Optimize **Historical Season View**.
- [x] Resolve Admin critical bugs (CSRF, UnboundLocalError).
- [x] **[TIK-23]** — Real-time duplicate validation for achievements in Admin.
- [x] **[TIK-24]** — Player search on Leaderboard.
- [x] **[TIK-25]** — Advanced Filtering (country, achievement type).
- [x] **[TIK-26]** — Enhanced Audit Log Visualization.

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

_Last updated: 2026-04-27_
