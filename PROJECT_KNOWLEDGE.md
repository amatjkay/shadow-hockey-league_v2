# PROJECT_KNOWLEDGE.md — Core Principles & Business Rules

## 1. Achievement & Point System

### Point Calculation Formula
`Final Points = (Base Points * Season Multiplier)`

- **Base Points**: Determined by `AchievementType` and `League`.
  - League 1 (L1) uses `base_points_l1`.
  - League 2 (L2), 2.1, 2.2 use `base_points_l2`.
- **Multiplier**: Defined in the `Season` model.
- **Auto-calculation**: Achievements MUST be auto-calculated on the server-side via `on_model_change` to ensure database integrity.

### Reference Data Baselines

> Source of truth: `data/seed/achievements.json` + `seed_db.py` + `achievement_types`/`seasons` rows in `dev.db`. Verify with `SELECT code, base_points_l1, base_points_l2 FROM achievement_types` before changing.

| Code | Name | L1 (Elite) | L2 |
| :--- | :--- | ---: | ---: |
| `TOP1` | Top 1 | 800 | 400 |
| `TOP2` | Top 2 | 400 | 200 |
| `TOP3` | Top 3 | 200 | 100 |
| `BEST` | Best Regular | 200 | 100 |
| `R3` | Round 3 (semifinal exit) | 100 | 50 |
| `R1` | Round 1 (quarterfinal exit) | 50 | 25 |

- **Baseline Season**: 25/26 (Multiplier = 1.0).
- **Historical Multipliers**: 24/25 = 0.8, 23/24 = 0.5, 22/23 = 0.3, 21/22 = 0.2.

## 2. Infrastructure & Tech Stack

- **Core**: Flask 3.1+ (Application Factory pattern in `app.py`).
- **Database**: SQLite (`dev.db`) + SQLAlchemy 2.0. Migrations via Alembic.
- **Admin**: Flask-Admin + AJAX-powered achievement management in `services/admin.py`.
- **Asset Resolution**: Centralized icon pathing in `AchievementType.get_icon_url()`. Flags normalized to uppercase (e.g., `RUS.png`).

## 3. Development Standards

- **Type Hints**: 100% coverage mandatory for all new code.
- **Testing**: Target ≥87% coverage. Run via `make test` or `venv/bin/pytest`.
- **Audit**: All admin actions logged to `AuditLog`. Snapshots taken before deletion.
  - **Known gap (B9, 2026-04-28):** the `after_flush` listener in `services/audit_service.py` early-returns unless `g.current_user_id` is set, and `set_current_user_for_audit()` is currently only called from tests — production admin mutations are not actually being logged. Fix tracked separately.
- **Memory Bank**: Keep `docs/activeContext.md` and `docs/progress.md` updated.

## 4. Automation & Seeding

- `seed_db.py` handles idempotent data population.
- `--force` flag clears the database for a clean reseed (destructive). Note: this re-issues season `id` values starting at 1 (21/22) — hard-coded `?season=N` URLs may need updating after a `--force` reseed.
- Mapping for legacy seed names (`BEST_REG` → `BEST`, `HOCKEY_STICKS_AND_PUCK` → `R3`/`R1`) is handled in `SeedService`.

## 5. Testing

- **Unit / integration**: `pytest --ignore=tests/e2e` — currently 388 passing (3 pre-existing failures unrelated to current branch).
- **Smoke e2e**: `tests/e2e/test_smoke.py` (Playwright). Run manually against a live dev server: `BASE_URL=http://127.0.0.1:5000 E2E_ADMIN_USER=e2e_admin E2E_ADMIN_PASS=... ./venv/bin/python tests/e2e/test_smoke.py`. Excluded from `pytest` auto-collection via `tests/e2e/conftest.py`.
- **Cache key partitioning**: any `@cache.cached` view that varies by query-string MUST use a callable `key_prefix` (see `blueprints/main.py::index`); a static prefix shares the bucket across `?season=` variants.

---
_Last updated: 2026-04-28_
