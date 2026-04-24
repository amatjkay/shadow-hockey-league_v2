# Decision Log

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
