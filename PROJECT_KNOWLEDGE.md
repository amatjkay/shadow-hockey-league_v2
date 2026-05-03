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
- **Admin**: Flask-Admin + AJAX-powered achievement management in the `services/admin/` package (`__init__.py`, `base.py`, `views.py`, `_rate_limit.py`).
- **Asset Resolution**: Centralized icon pathing in `AchievementType.get_icon_url()`. Flags normalized to uppercase (e.g., `RUS.png`).

## 3. Development Standards

- **Type Hints**: 100% coverage mandatory for all new code; `mypy` enforces this in `make check` and CI (TIK-53).
- **Testing**: ≥ 87% coverage gate (TIK-54). Run via `make test`.
- **Audit**: All admin actions logged to `AuditLog`. Snapshots taken before deletion. The `after_flush` listener in `services/audit_service.py` is now wired via `register_audit_request_hook(app)` in `app.py::register_extensions`, which sets `g.current_user_id` from `flask_login.current_user` so production admin CRUD is captured.
- **Memory Bank**: Keep `docs/activeContext.md` and `docs/progress.md` updated.

## 4. Automation & Seeding

- `seed_db.py` handles idempotent data population.
- `--force` flag clears the database for a clean reseed (destructive). Note: this re-issues season `id` values starting at 1 (21/22) — hard-coded `?season=N` URLs may need updating after a `--force` reseed.
- Mapping for legacy seed names (`BEST_REG` → `BEST`, `HOCKEY_STICKS_AND_PUCK` → `R3`/`R1`) is handled in `SeedService`.

## 5. Testing

- **Unit / integration**: `make test` (or `pytest --ignore=tests/e2e -n auto`) — currently 464 passing. Coverage gate ≥ 87% (TIK-54).
- **Type check**: `mypy` is part of `make check` (TIK-53) and the `Quality & Tests` CI job — 0 errors on the source tree (78 files).
- **Dependency audit**: `make audit-deps` (`pip-audit` on `requirements.txt` + `requirements-dev.txt`) runs in CI (TIK-52).
- **Smoke e2e**: `tests/e2e/test_smoke.py` (Playwright, 42 scenarios). Locally: boot `make run`, then `python scripts/create_e2e_admin.py && make e2e`. CI runs the same script in the dedicated `E2E Smoke (Playwright)` job (TIK-55, PR #60). Excluded from `pytest` auto-collection via `tests/e2e/conftest.py`.
- **Cache key partitioning**: any `@cache.cached` view that varies by query-string MUST use a callable `key_prefix` (see `blueprints/main.py::index`); a static prefix shares the bucket across `?season=` variants.

---
_Last updated: 2026-05-03 — post-TIK-51 (mypy/pip-audit/e2e in CI, 87% coverage)._
