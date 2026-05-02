# One-off prod-sync scripts (archived from `scratch/`)

> **Status:** archived. Kept as historical reference only. Do **not** add new scripts here — write a proper management command, Alembic migration, or CLI command instead.

These scripts were created during early development to back-fill / reconcile data between the dev DB and a production snapshot before formal data migrations existed. They are kept for forensic reference (so you can see what state `Achievement.final_points`, `Season.multiplier`, etc. were last reconciled to) but are **not** part of any current workflow.

## Inventory

| Script | Purpose (historical) |
|---|---|
| `clear_cache.py` | Wipes the Flask-Caching cache via `cache.clear()`. Use the `/admin/flush-cache/` POST route or `services.cache_service.invalidate_leaderboard_cache()` instead. |
| `recalc_points.py` | Recomputes `Achievement.final_points` for all rows. Superseded by `services.recalc_service.recalc_all()`. |
| `verify_points.py` | Asserts no negative `final_points`. Replicate via a one-off Alembic data migration if needed. |
| `sync_ids.py` | Reconciles `Achievement.season_id` with `Season.code`. Superseded by FK-enforced schema. |
| `sync_seasons.py` | Sets `Season.multiplier` to canonical values. Superseded by Alembic seed migrations. |
| `final_prod_sync.py` | Last reconciliation pass before going production. Frozen in time. |
| `full_prod_recalc.py` | Combined recalc + sync invoked once during cut-over. Frozen in time. |

## Why archived (not deleted)

Per [TIK-49](https://linear.app/tikispace/issue/TIK-49) discussion, archiving keeps the audit trail (e.g. you can git-blame back to the exact code that produced today's `final_points` values) without polluting the project root. The directory is excluded from coverage reports and CI test discovery — it is reference material, not active code.

## If you must run one

1. Read the script first; some hardcode values that were correct in 2026-04-29 but may not be today.
2. Run inside an app context: `python -c "from app import create_app; app = create_app(); ctx = app.app_context(); ctx.push(); from scripts.oneoff.recalc_points import recalculate_all_achievements; recalculate_all_achievements()"`.
3. Always take a DB snapshot first.
