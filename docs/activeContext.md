# Active Context — Shadow Hockey League v2

> **Purpose:** This file tracks the current focus of work, recent changes, and immediate
> next steps. All agents MUST read this before starting any task.

---

## Current Focus

**Phase:** Post-audit testing campaign (Phase A → H, started 2026-04-29).
**Status:** Audit-2026-04-28 remediation Phases 2A/2B/2C/3 all merged. Only Phase 4 (linter debt) remains.

Next milestone: complete the post-audit testing campaign (docs sync → Linear sync → test inventory → test optimization → gap analysis → mass run → linter debt → issue capture). Owner approved the full A→G scope plus running e2e (Playwright) on the local VM with Flask + Redis.

---

## Status

- **Branch:** `main` (HEAD `8a57cdc`, post PR #38 merge).
- **Goal:** Validate post-fix state via comprehensive testing; feed every finding into Linear.
- **Seeding Status:** 58 achievements, 42 managers, 5 seasons, baseline 25/26.
- **Live dev server (when running):** `http://127.0.0.1:5000`.

## Recent Changes (2026-04-28 → 2026-04-29)

- **PR #31** docs(audit) — analysis + plan + Linear action script for the 2026-04-28 audit. Open; superseded by Phase A docs sync (this branch) which lifts the same artifacts onto current `main` and marks Phases 2A–3 as ✅.
- **PR #32 (TIK-37 / B10)** ✅ merged — added `socket_timeout=1.0` to `redis.Redis(...)` in `blueprints/health.py:81` + regression test asserting both kwargs.
- **PR #33 (TIK-38 / B11)** ✅ merged — startup banner now derived from `services/metrics_service` constants (`METRICS_PREFIX` + `DEFAULT_METRIC_SUFFIXES`) so the announce-line cannot drift from what `prometheus_flask_exporter` actually emits.
- **PR #34 (TIK-16 / rate-limiter)** ✅ merged — replaces #16. Single shared `Limiter` instance in `services/extensions.py`, wired via `init_app(app)` with Redis storage in production and memory fallback in dev/test. All 15 API endpoints now use `@limiter.limit("100 per minute")`. Devin Review caught a seed-data bug in `tests/test_api.py` (TOP1/TOP2/TOP3 base points) — fixed in `06dafeb`.
- **PR #35 (TIK-17 / scoring)** ✅ merged — replaces #17. New helper `services/scoring_service.py::get_base_points(ach_type, league)` is the single source of truth; reads `League.base_points_field` (which honours `parent_code`) so subleagues like `2.1` correctly inherit `base_points_l2` from the parent. Plus tightened `validation_service` (format regex `^[1-9]\d*(\.\d+)?$` + business rule that L1 is flat).
- **PR #38 (TIK-36 / B9)** ✅ merged — added `register_audit_request_hook(app)` in `services/audit_service.py` and called it from `app.py::register_extensions` right after `init_admin`. The hook is a `@app.before_request` handler that reads `flask_login.current_user` and forwards the authenticated admin's id into `g.current_user_id`, so the existing `after_flush` listener now actually writes to `audit_logs` for admin CRUD. Three regression tests in `tests/integration/test_audit_logging.py::TestAuditRequestHook`.
- **2026-04-29 testing campaign** — owner asked for: docs/Linear actualization, test optimization (unit/integration/regression/UI/e2e), mass test run, every issue → Linear. Phase A in flight.

---

## Immediate Next Steps

- [x] Phase 2A — analysis verifications (T-V-2, T-V-3) committed.
- [x] Phase 2B — TIK-37 + TIK-38 merged.
- [x] Phase 2C — rate-limiter (PR #34) + subleague scoring (PR #35) merged.
- [x] Phase 3 — TIK-36 audit-log wiring merged.
- [ ] **Phase A (in flight)** — actualize docs (this file + `progress.md` + `techContext.md` + `audit-2026-04-28-plan.md` + `decisionLog.md`).
- [ ] **Phase B** — sync Linear (close TIK-36/37/38, create epic for the audit).
- [ ] **Phase C** — test inventory → `docs/audits/test-inventory-2026-04-29.md`.
- [ ] **Phase D** — test optimization (fixtures dedupe, slow tests, flakies).
- [ ] **Phase E** — gap analysis vs B1–B11 + new sub-systems.
- [ ] **Phase F** — mass run including e2e (Playwright on local Flask + Redis).
- [ ] **Phase G** — linter debt (= audit Phase 4).
- [ ] **Phase H** — every problem found → Linear ticket.

---

## Active Blockers

- None. Phase 4 (linter debt) is the only remaining audit task; everything else is unblocked.

---

## Notes for Next Agent

- **Flask-Admin compatibility**: Flask-Admin 2.0.2 ships with the `cls=self` fallback in `BaseView._run_view`, and WTForms 3.2.x no longer accepts `allow_blank` on the base `Field`. The previous `utils/patches.py` shim is therefore obsolete and was removed in TIK-34. If a future upgrade re-introduces the incompatibility, restore the patch and call it from `create_app()` before `init_admin(app)`.
- **Admin JS**: Shared logic is in `static/js/admin/autofill.js`.
- **Rate limiting**: shared `Limiter` lives in `services/extensions.py`. Both `app.py` (`@app.before_request`-style protection of the admin login form) and `services/api.py` (15 API endpoints) use it. Storage is Redis in production, in-memory in dev/test.
- **Subleague scoring**: always go through `services/scoring_service.py::get_base_points(ach_type, league)` — never compare `league.code == "1"` directly. The helper reads `League.base_points_field`, which respects `parent_code` so subleagues `2.1`/`2.2` inherit `base_points_l2` from parent `2`.
- **Audit log**: `register_audit_request_hook(app)` is wired in `app.py::register_extensions`. It populates `g.current_user_id` from `flask_login.current_user` so the existing `after_flush` listener writes to `audit_logs` for admin CRUD. `audit_service.log_action()` is still the explicit API used by `services/recalc_service.py` for non-CRUD events.
- **Testing**:
  - Unit/integration: `venv/bin/pytest --ignore=tests/e2e`. ~70s, expect ~402 pass.
  - Smoke e2e: requires a running dev server; see PROJECT_KNOWLEDGE.md §5 for the exact command.
- **Database**: `dev.db` is the primary SQLite database; schema checks via the `sqlite` MCP server are recommended before any mutation.
- **Cache key**: any new `@cache.cached` decorator that varies by query-string MUST use a callable `key_prefix` (see `blueprints/main.py::index`).

---

_Last updated: 2026-04-29 — Phase A docs sync._

---

## Next: agents+skills (PR B)

After repo-hygiene PR lands, follow up with:
- `.agents/agents/{token-auditor,doc-curator}.md`
- `.agents/skills/{token-budget,doc-rotation,codebase-map}/SKILL.md`
- `.agents/prompts/{shl-optimizer,shl-optimizer.fewshot}.md`
- `docs/INDEX.md`
- Update `AGENTS.md §3` to register the two new sub-agent roles.
