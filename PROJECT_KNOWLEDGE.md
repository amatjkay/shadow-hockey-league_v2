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
- **TOP1**: L1 = 800 points | L2 = 300 points.
- **TOP2**: L1 = 550 points | L2 = 200 points.
- **TOP3**: L1 = 450 points | L2 = 100 points.
- **BEST_REG**: L1 = 50 points | L2 = 25 points.
- **ROUND_1**: L1 = 10 points | L2 = 5 points.
- **Baseline Season**: Season 25/26 (Multiplier = 1.0).
- **Historical Seasons**: Multipliers decrease by 0.05 each year (S24/25 = 0.95, S23/24 = 0.90, S22/23 = 0.85, S21/22 = 0.80).

## 2. Infrastructure & Tech Stack

- **Core**: Flask 3.1+ (Application Factory pattern in `app.py`).
- **Database**: SQLite (`dev.db`) + SQLAlchemy 2.0. Migrations via Alembic.
- **Admin**: Flask-Admin + AJAX-powered achievement management in `services/admin.py`.
- **Asset Resolution**: Centralized icon pathing in `AchievementType.get_icon_url()`. Flags normalized to uppercase (e.g., `RUS.png`).

## 3. Development Standards

- **Type Hints**: 100% coverage mandatory for all new code.
- **Testing**: Target ≥87% coverage. Run via `make test` or `venv/bin/pytest`.
- **Audit**: All admin actions logged to `AuditLog`. Snapshots taken before deletion.
- **Memory Bank**: Keep `docs/activeContext.md` and `docs/progress.md` updated.

## 4. Automation & Seeding

- `seed_db.py` handles idempotent data population.
- `--force` flag clears the database for a clean reseed (destructive).
- Mapping for legacy types (`BEST_REG`, `HOCKEY_STICKS_AND_PUCK`) is handled in `SeedService`.

---
_Last updated: 2026-04-24_
