# Active Context — Shadow Hockey League v2

> **Purpose:** Current focus + immediate next steps. Memory Bank file, read by all agents on session start (`AGENTS.md` § 1).

---

## Current Focus

**Phase:** Maintenance. M2 (synthwave brand refresh + polish v2) and the
`task-formulation` skill rollout are shipped; Linear backlog is empty.

**Last shipped:** PR #91 (TIK-86) — `_LEADERBOARD_LOCK` in
`services/rating_service.py` serializes `build_leaderboard()` to dodge a
SQLAlchemy 2.0 joinedload cython race that surfaced as `IndexError: tuple
index out of range` under concurrent reads. Sync gunicorn workers in prod
never contend the lock; it only matters for the threaded test client and
any future `--threads >1` worker.

---

## Status

- **Branch:** `main` (post TIK-86 merge).
- **Tests:** 561 unit/integration (`make test`, ~30s, ≥ 87% coverage gate, TIK-54).
- **Type check:** `mypy` in `make check` and CI (TIK-53) — 0 errors.
- **Dependency audit:** `make audit-deps` (`pip-audit`) wired into CI (TIK-52).
- **E2E:** `make e2e` (Playwright, 42 scenarios) — local via `make run` + `scripts/create_e2e_admin.py`; CI via `E2E Smoke (Playwright)` job (TIK-55).
- **Seeding:** 85 achievements, 63 managers, 8 countries, 5 seasons, 4 leagues. Baseline season 25/26.
- **Live dev server:** `http://127.0.0.1:5000`.
- **Production:** <https://shadow-hockey-league.ru/> — `gunicorn --workers 4 --sync` on Ubuntu + Nginx.

## Recent Changes (post-2026-05-03)

- **PR #60 (TIK-55 e2e in CI)** ✅ merged 2026-05-03 — `tests/e2e/test_smoke.py` wired into `E2E Smoke (Playwright)` GitHub Actions job.
- **PR #76 (TIK-59 batch)** ✅ merged 2026-05-06 — staging stabilisation.
- **PR #79 (TIK-72 round-2 QA: TIK-74…TIK-80)** ✅ merged 2026-05-07 — hidden `Войти`, pill-shaped season selector, season-dropdown fix, canonical SVG icon paths, concise achievement tooltips, admin `__str__` + filter sidebar, **compact-10 base-points rescaling** (TIK-80).
- **PR #86 (TIK-83 Concept A)** ✅ merged 2026-05-09 — M2 refresh.
- **PR #87 (TIK-84 synthwave + Concept C)** ✅ merged 2026-05-09 — M2 finalised.
- **PR #88 (TIK-85)** ✅ merged 2026-05-10 — leaderboard ghost-grid + rainbow top-10 fix.
- **PR #89 (polish v2)** ✅ merged 2026-05-10 — tandem badges, points-modal, medal pills, pastel light-theme override.
- **PR #90 (`task-formulation` skill + Obsidian wiki)** ✅ merged 2026-05-11 — 4-section checklist in `.agents/skills/task-formulation/`; `docs/wiki/` Obsidian vault.
- **PR #91 (TIK-86 `_LEADERBOARD_LOCK`)** ✅ merged 2026-05-11 — concurrent-leaderboard race fix + `test_concurrent_homepage_requests_stress`.

---

## Immediate Next Steps

- [ ] **Owner action — secret rotation.** `.env` was tracked in git history before PR #44.
  Rotate `GEMINI_API_KEY` at Google AI Studio; regenerate `SECRET_KEY`,
  `WTF_CSRF_SECRET_KEY`, `API_KEY_SECRET` (32+ char random) and replace in local `.env`.
  Decide whether to run `git filter-repo` to scrub history (irreversible, breaks any open
  forks/PRs). Tracked in `docs/progress.md` 2026-05-01 entry as a blocker.
- [ ] **Owner action — Vercel integration.** Production isn't on Vercel; the
  `Vercel` check on every PR is noise. Disconnect the GitHub ↔ Vercel
  integration (or remove `Vercel` from required checks).

---

## Active Blockers

- **[Owner-action] Secret rotation** — see «Immediate Next Steps». Untracking the file does not rewrite history.
- **[Owner-action] Vercel CI noise** — see «Immediate Next Steps».

---

## Notes for Next Agent

- **Concurrency in `build_leaderboard()`**: protected by `_LEADERBOARD_LOCK` (TIK-86). Production sync workers never contend it; test client + threaded workers do. If you split the function further or move it, keep the lock at the public entrypoint.
- **Flask-Admin compatibility**: Flask-Admin 2.0.2 ships with the `cls=self` fallback in `BaseView._run_view`, and WTForms 3.2.x no longer accepts `allow_blank` on the base `Field`. The previous `utils/patches.py` shim is therefore obsolete and was removed in TIK-34.
- **Admin JS**: Shared logic is in `static/js/admin/autofill.js`.
- **Rate limiting**: shared `Limiter` in `services/extensions.py`. `app.py` (admin-login protection) and `services/api/` (15 endpoints across `countries.py`, `managers.py`, `achievements.py`) both use it. Redis in prod, in-memory in dev/test. Admin login throttling: `services/admin/_rate_limit.py`.
- **Subleague scoring**: always go through `services/scoring_service.py::get_base_points(ach_type, league)` — never compare `league.code == "1"` directly. The helper reads `League.base_points_field`, which respects `parent_code` so subleagues `2.1`/`2.2` inherit `base_points_l2` from parent `2`.
- **Audit log**: `register_audit_request_hook(app)` is wired in `app.py::register_extensions`. It populates `g.current_user_id` from `flask_login.current_user` so the existing `after_flush` listener writes `audit_logs` for admin CRUD. `audit_service.log_action()` is the explicit API for non-CRUD events (used by `services/recalc_service.py`).
- **Admin views**: All `ModelView` subclasses live in `services/admin/views.py` (Country, League, Season, Manager, Achievement, AuditLog, SystemControl). Base `SHLModelView` in `services/admin/base.py`. `init_admin(app)` is the single entrypoint, called from `app.py`.
- **Public API**: `services/api/` is a package; routes split per resource (`countries.py`, `managers.py`, `achievements.py`), all registered onto a single `api` Blueprint in `services/api/__init__.py`. Admin-side lookup endpoints: `blueprints/admin_api/lookups.py`.
- **Type narrowing**: prefer `SessionLike` alias from `services/_types.py` + `cast(Foo, model.field)` over `# type: ignore`. Pattern established in TIK-53.
- **Prometheus metrics**: `services/metrics_service.py` is a singleton. `app.py::register_extensions` initialises it unconditionally; `reset_metrics()` cleans `prometheus_client.REGISTRY` for test fixtures. Production unchanged.
- **HTTP compression**: Flask-Compress in `app.py::register_extensions` (br + gzip, level 6, `>=500 B`). Disabled under `TESTING`.
- **`?fields=` projection**: opt-in via `paginate_query` for listing endpoints. Single-record `/<id>` endpoints always return full record.
- **Cache key partitioning**: any `@cache.cached` view that varies by query-string MUST use a callable `key_prefix` (see `blueprints/main.py::index`); a static prefix shares the bucket across `?season=` variants.
- **Testing locally**: `make test` (~30s, 561 passing). Two tests in `tests/test_app_extra.py::TestCreateAppEnvFallback` need a real Redis on `localhost:6379` to set up Flask-Limiter — CI brings up a `redis` service container; locally you'll see `559 passed, 2 failed` without it. That's expected.
- **Database**: `dev.db` is the primary SQLite (untracked since PR #44); recreate via `make init-db`.
- **mcp-servers/**: untracked since PR #44; reinstate via `make mcp-install`.

---

_Last updated: 2026-05-12 — post-TIK-86 (`_LEADERBOARD_LOCK`) + docs cleanup._
