# Admin Templates & Recalc Service

This document describes recent additions to the admin UI and the backend recalculation service.

## 📦 Bulk Achievement Creation

The admin templates (`manager_edit.html`, `manager_list.html`) now support batch operations:

- **Bulk Add Achievements** (`manager_edit.html`):
  - Select a manager and choose achievement type/league/season via dynamic Select2 dropdowns.
  - Points are previewed in real time using the formula `base_points × season_multiplier`.
  - Submit sends an array of manager IDs and a target achievement definition; the backend creates entries via `recalc_service` logic.

- **Bulk Actions** (`manager_list.html`):
  - Checkbox selection enables batch deletion or re-calculation triggers.
  - Queue-based processing (via Celery/Redis in production) prevents request timeouts.

## 🔁 Recalc Service (`recalc_service.py`)

Central service for recomputing standings and points after data mutations.

### Responsibilities
- Re-calculate `Manager.total_points` and `Manager.matches_played` when a `Match` is created/updated/deleted.
- Ensure atomic updates within DB transactions to avoid partial state.
- Invalidate the Leaderboard cache after committing changes.

### Integration Points
- **API Endpoints**: `POST /admin/api/achievements/bulk-create`, `POST /admin/api/managers/<id>/achievements/bulk-add`
- **Signals / Hooks**: Called from model `save()` and `delete()` methods (orchestrated via service layer) to keep data consistent.

### Key Functions
- `recalc_manager_standings(manager_id)` — aggregates all achievements for a manager.
- `recalc_league_standings(league_id, season_id)` — recomputes the full table for a league/season.

## 🔗 Connection to Admin Templates

- When admins perform bulk actions, the frontend sends the same payload structure used by the API endpoints.
- Templates use `fetch` to call the respective endpoints and reflect updated points immediately.
- Error handling surfaces validation issues (e.g., duplicate achievements, negative points) inline.

## 📚 Related Documentation

- **API Reference** (`docs/API.md`) — endpoints for bulk operations.
- **Architecture** (`ARCHITECTURE.md`) — data model and service boundaries.
- **Migration Notes** (`MIGRATIONS.md`) — recent introduction of `Match` model and service extraction.