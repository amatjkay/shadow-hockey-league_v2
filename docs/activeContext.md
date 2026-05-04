# Active Context — Shadow Hockey League v2

> **Purpose:** This file tracks the current focus of work, recent changes, and immediate
> next steps. All agents MUST read this before starting any task.

---

## Current Focus

**Phase:** TIK-58 in flight — owner-driven feature: seed Season 25/26 League 2.2
results (subleagues `2.1`/`2.2`, 14 new managers, 9 achievements, Denis → Denys
rename, idempotent Alembic data migration).
**Status:** PR open against `main`. Awaiting CI green + user review. `make
check` / `make audit-deps` clean locally; coverage at 87% gate.

Next milestone: merge TIK-58, then back to maintenance mode.

---

## Status

- **Branch:** `main` (post PR #60 merge).
- **Goal:** Maintenance mode. Awaiting next feature/bug request.
- **Tests:** 472 unit/integration (`make test`) + 42-scenario Playwright e2e
  smoke (`make e2e` locally; `E2E Smoke (Playwright)` job in CI).
- **Coverage gate:** ≥ 87% (TIK-54).
- **Type check:** `mypy` is back in `make check` and CI as of TIK-53 — 0 errors
  on the source tree (78 files).
- **Dependency audit:** `make audit-deps` (pip-audit) wired into CI as of
  TIK-52.
- **Seeding:** 58 achievements, 42 managers, 5 seasons, baseline 25/26.
- **Live dev server (when running):** `http://127.0.0.1:5000`.

## Recent Changes (post-2026-05-01)

- **PR #46 (docs sync 2026-05-01)** ✅ merged — retired Phase A→H plan; backlog drained.
- **PR #47-#54 (TIK-43..TIK-50)** ✅ merged via **PR #55 (TIK-42 epic)** on 2026-05-03 — dead code purge, CC reduction, 3 monolith→package splits, test dedup, scratch archive, coverage boost. Net: 423 tests / 84% coverage / 0 files > 600 LOC / 0 functions ≥ CC D.
- **PR #56 (docs sync 2026-05-03)** ✅ merged — TIK-42 cleanup campaign summary.
- **PR #57 (TIK-52 deps)** ✅ merged — `pip-audit` + `make audit-deps` + CI step. WTForms 3.2.1 → 3.2.2 + dev pkg bumps.
- **PR #58 (TIK-53 mypy)** ✅ merged — re-enabled `mypy` in `make check` and CI; fixed all 40 errors on the source tree (introduces `services/_types.py::SessionLike` for Flask-SQLAlchemy proxy compat).
- **PR #59 (TIK-54 coverage)** ✅ merged — coverage 83% → 87% via 49 new tests targeting health error paths, admin views formatters, recalc/metrics corner cases.
- **PR #60 (TIK-55 e2e in CI)** ✅ merged 2026-05-03 — wired `tests/e2e/test_smoke.py` into a dedicated `E2E Smoke (Playwright)` GitHub Actions job; new `scripts/create_e2e_admin.py` provisions the `e2e_admin` super-admin idempotently; `make e2e` target for local runs.

---

## Immediate Next Steps

- [x] All audit-2026-04-28 phases (2A → G) closed.
- [x] All TIK-42 cleanup epic sub-tickets closed (PR #55).
- [x] All TIK-51 tech-debt continuation sub-tickets closed (PRs #57-#60).
- [x] Backlog Linear empty.
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

- **[Owner-action] Secret rotation** — see «Immediate Next Steps» above. Untracking the
  file does not rewrite history.
- **[Owner-action] Vercel CI noise** — see «Immediate Next Steps» above.

---

## Notes for Next Agent

- **Flask-Admin compatibility**: Flask-Admin 2.0.2 ships with the `cls=self` fallback in `BaseView._run_view`, and WTForms 3.2.x no longer accepts `allow_blank` on the base `Field`. The previous `utils/patches.py` shim is therefore obsolete and was removed in TIK-34. If a future upgrade re-introduces the incompatibility, restore the patch and call it from `create_app()` before `init_admin(app)`.
- **Admin JS**: Shared logic is in `static/js/admin/autofill.js`.
- **Rate limiting**: shared `Limiter` lives in `services/extensions.py`. Both `app.py` (`@app.before_request`-style protection of the admin login form) and the `services/api/` package (15 API endpoints across `countries.py`, `managers.py`, `achievements.py`) use it. Storage is Redis in production, in-memory in dev/test. Admin-side login throttling lives in `services/admin/_rate_limit.py`.
- **Subleague scoring**: always go through `services/scoring_service.py::get_base_points(ach_type, league)` — never compare `league.code == "1"` directly. The helper reads `League.base_points_field`, which respects `parent_code` so subleagues `2.1`/`2.2` inherit `base_points_l2` from parent `2`.
- **Audit log**: `register_audit_request_hook(app)` is wired in `app.py::register_extensions`. It populates `g.current_user_id` from `flask_login.current_user` so the existing `after_flush` listener writes to `audit_logs` for admin CRUD. `audit_service.log_action()` is still the explicit API used by `services/recalc_service.py` for non-CRUD events.
- **Admin views**: All `ModelView` subclasses live in `services/admin/views.py` (Country, League, Season, Manager, Achievement, AuditLog, SystemControl). Base class `SHLModelView` is in `services/admin/base.py`. `init_admin(app)` lives in `services/admin/__init__.py` and is the single entrypoint called from `app.py`.
- **Public API**: `services/api/` is a package; routes are split per resource (`countries.py`, `managers.py`, `achievements.py`) and registered onto a single `api` Blueprint created in `services/api/__init__.py`. Admin-side lookup endpoints are in `blueprints/admin_api/lookups.py`.
- **Type narrowing**: where mypy needs help with Flask-SQLAlchemy session proxies or `Optional[Foo]` fields after a `is not None` guard, use the `SessionLike` alias from `services/_types.py` and `cast(Foo, model.field)` rather than `# type: ignore`. Pattern established in TIK-53.
- **Prometheus metrics**: `services/metrics_service.py` is a singleton. `app.py::register_extensions` initialises it unconditionally (even under `TESTING`); `reset_metrics()` cleans `prometheus_client.REGISTRY` so test fixtures can rebind cleanly. Production behaviour is unchanged — `TESTING=False` there.
- **HTTP compression**: Flask-Compress is wired in `app.py::register_extensions` (br + gzip, level 6, `>=500 B`). Disabled in `TESTING` so `test_client` responses stay byte-comparable.
- **`?fields=` projection**: opt-in only, plumbed through `paginate_query` for listing endpoints (`GET /api/managers`, `GET /api/achievements`, ...). Single-record endpoints (`/<id>`) still return the full record.
- **Testing**:
  - Unit/integration: `venv/bin/pytest tests --ignore=tests/e2e -n auto`. ~40s, expect 472 pass (or 470 + 2 skipped/failing locally if no Redis service is running — those 2 tests need a real Redis to set up Flask-Limiter).
  - Smoke e2e (local): boot `make run` in one shell; in another, run `python scripts/create_e2e_admin.py` then `make e2e`. The CI `E2E Smoke (Playwright)` job does the same in a fresh runner with a Redis service.
- **Database**: `dev.db` is the primary SQLite database (untracked since PR #44); recreate locally via `make init-db` (or, for the e2e flow specifically, `python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"` — the bare schema bootstrap CI uses).
- **Cache key**: any new `@cache.cached` decorator that varies by query-string MUST use a callable `key_prefix` (see `blueprints/main.py::index`).
- **mcp-servers/**: untracked since PR #44. Reinstate via `make mcp-install`.

---

_Last updated: 2026-05-03 — post-TIK-51 sync (PRs #57-#60 merged: deps audit, mypy back in CI, 87% coverage, e2e in CI)._
