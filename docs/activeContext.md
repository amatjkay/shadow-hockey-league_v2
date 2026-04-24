# Active Context — Shadow Hockey League v2

## Current Focus
**Stabilization and Merging.** The project has reached a stable state where all critical bugs in the Admin Panel (specifically Achievement Management) and the point calculation system have been resolved.

## Recent Changes
- **Achievement System**: Consolidated the Manager Achievement UI into a single AJAX modal workflow.
- **Data Integrity**: Implemented server-side auto-calculation for achievement points and titles.
- **Icon Resolution**: Centralized icon pathing in `AchievementType.get_icon_url()` and updated all consumers.
- **Linux Compatibility**: Standardized flag filenames to uppercase and fixed case-sensitivity issues.
- **Point Alignment**: Synchronized `SeedService` and `RatingService` to use consistent base points (TOP1 = 800).
- **Code Hygiene**: Removed duplicate classes in `services/admin.py` and isolated monkey-patches.

## Next Steps
1. **Merge `fix` into `main`**: Perform a final verification and merge the development branch.
2. **Historical Season View**: Design and implement the frontend filtering for previous seasons on the leaderboard.
3. **Bulk Operations**: Implement CSV/Batch upload for manager achievements.

## Active Blockers
- **Outbound Network**: WSL environment cannot push directly to GitHub. Manual intervention required.
- **Tooling**: `gh` CLI missing.

---
_Last updated: 2026-04-24_
