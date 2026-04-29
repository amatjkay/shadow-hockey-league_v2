# Test inventory — Shadow Hockey League v2 (2026-04-29)

Generated as **Phase C** of the post-audit testing campaign
(see `docs/audits/audit-2026-04-28-plan.md`). Tracks every test file
under `tests/` after the merge of PRs #32, #33, #34, #35, #37, #38.

Linear tracker: **TIK-41** (post-audit campaign 2026-04-29).

---

## 1. Counts at a glance

| Type        | Files | Test fns | LOC   | Notes                                        |
|-------------|------:|---------:|------:|----------------------------------------------|
| Unit (broad) |  14  |     268  |  3236 | All `tests/test_*.py` except `test_metrics.py`; **includes** `tests/test_e2e.py` which is actually a Flask test-client integration smoke (re-categorised in §2.3 / §4) |
| Integration |   10  |     134  |  3264 | Real Flask app + SQLite/in-memory DB         |
| Regression  |  (★) |       7  |  (mixed) | Tests that pin a specific audit/B-bug fix; counted once in their owning category and listed in §3 |
| E2E (browser)|   1  |       0  |   464 | `tests/e2e/test_smoke.py` (Playwright, 42 scenarios). Opt-in only; **0 auto-collectable** because `tests/e2e/conftest.py` sets `collect_ignore_glob = ["*.py"]` |
| Broken/script|   1  |       0  |    41 | `tests/test_metrics.py` — top-level prints, no test fns. Removed in Phase D. |
| **Auto-collectable total** | **24** | **402** | **6694** | matches `pytest --collect-only -q tests/` and the 2026-04-29 baseline run: **402 passed, 1916 warnings, 82.26s** |

(★) Regression tests live inside the Unit/Integration files; counted once
in their owning category and listed separately in §3 below.

---

## 2. Per-file classification

### 2.1 Unit tests (no app context required, or app fixture only)

| File | Tests | Subject | Notes |
|---|---:|---|---|
| `tests/test_admin_achievements.py`     |   4 | Admin form custom widgets / select choices | imports models only |
| `tests/test_admin_service.py`          |  16 | `services/admin.py` ModelViews + flag handling | uses `app` fixture |
| `tests/test_api.py`                    |  15 | API-key auth, scopes, pagination edges | mocks Redis |
| `tests/test_api_auth.py`               |  22 | `ApiKey` model + token generation/hashing | pure model unit |
| `tests/test_audit_delete.py`           |   2 | `set_current_user_for_audit` + delete diff | regression for B9-adjacent behaviour |
| `tests/test_audit_service.py`          |  23 | `services/audit_service.py` listener + helpers | partial regression — see §3 |
| `tests/test_blueprints.py`             |  18 | `blueprints/health.py` / main BP smoke | **B10 regression** (`socket_timeout`) |
| `tests/test_cache_and_admin.py`        |   9 | `services/cache.py` `_FakeRedis` + admin auth | uses CDP-free flow |
| `tests/test_data_services.py`          |  40 | `services/data/*` (export, seed, schemas) | parametrized |
| `tests/test_e2e.py`                    |  15 | High-level page-render checks via Flask test-client | **mis-categorised**; really an integration smoke — see §2.3 / §4 |
| `tests/test_rating_formula.py`         |  27 | Pure formula correctness (decay, multipliers, base points) | parametrized |
| `tests/test_rating_service.py`         |  41 | `services/rating_service.py` (build_leaderboard, recalc) | largest file (768 LOC) |
| `tests/test_scoring_service.py`        |   4 | `services/scoring_service.get_base_points` | **PR #35 regression** |
| `tests/test_validation.py`             |  32 | `services/validation_service.py` (codes, dupes) | partial PR #35 regression |
| **Subtotal**                           | **268** across **14** files (excludes `test_metrics.py`) | | |

### 2.2 Integration tests (Flask app + real ORM)

| File | Tests | Subject | Notes |
|---|---:|---|---|
| `tests/integration/test_admin_api.py`           | 28 | `/admin/api/*` JSON endpoints (countries, managers, seasons, achievement-types, leagues) | covers form-helper APIs |
| `tests/integration/test_admin_api_extended.py`  |  9 | bulk-create / validate / delete on `/admin/api/*` | targets coverage gaps |
| `tests/integration/test_admin_integration.py`   | 18 | Flask-Admin `ModelView` classes (auto-calc, dashboard, server-control) | UI-flavoured but server-rendered |
| `tests/integration/test_admin_smoke_flow.py`    |  6 | login → dashboard → achievements API → logout cycle | catches `BuildError` / 500s |
| `tests/integration/test_admin_views.py`         | 20 | `services/admin.py` validation/bulk-op/points endpoints | targets coverage gaps |
| `tests/integration/test_api_extended.py`        |  9 | DELETE endpoints + error edges in `services/api.py` | targets coverage gaps |
| `tests/integration/test_audit_logging.py`       | 11 | end-to-end `audit_logs` writes + **`TestAuditRequestHook`** | **B9 regression — PR #38** |
| `tests/integration/test_cache_invalidation.py`  | 14 | every CRUD endpoint invalidates leaderboard cache | parametrized |
| `tests/integration/test_recalc.py`              |  7 | `recalc_by_*` flows + audit/cache side-effects | slowest file in this group |
| `tests/integration/test_routes.py`              | 12 | Flask routes ↔ DB ↔ services round-trip | 658 LOC, broadest |
| **Subtotal**                                    | **134** | | |

### 2.3 UI / browser-driven

| File | Tests | Engine | Notes |
|---|---:|---|---|
| `tests/test_e2e.py`               | 15 | Flask test-client | static-asset / cache / metrics page checks; **no real browser** |
| `tests/e2e/test_smoke.py`         |  1 (Playwright session) | Playwright | full suite (42 scenarios) — see §4 |

### 2.4 Broken / non-pytest

| File | Symptom |
|---|---|
| `tests/test_metrics.py` | Top-level `print()` script style; **0 collected tests**. Should be deleted or rewritten as a proper pytest module. Tracked under Phase D. |

---

## 3. Regression tests pinning specific audit/B-bugs

These deserve named visibility — they are the canaries that prevent
audit-2026-04-28 bugs from re-appearing.

| Test | File | Bug pinned |
|---|---|---|
| `test_health_endpoint_redis_client_uses_socket_timeout` | `tests/test_blueprints.py` | **B10** (PR #32) |
| metrics-banner sync via constants | covered indirectly by `services/metrics_service` constants tests | **B11** (PR #33) |
| rate-limiter: shared `Limiter`, `init_app` wiring | added in `tests/test_api.py` / API auth suite | **B-rate-limit** (PR #34) |
| `test_subleague_inherits_base_points_from_parent` | `tests/test_scoring_service.py` | **PR #35** |
| `test_create_app_wires_audit_request_hook` | `tests/integration/test_audit_logging.py::TestAuditRequestHook` | **B9** (PR #38) |
| `test_request_hook_is_noop_for_anonymous_requests` | `tests/integration/test_audit_logging.py::TestAuditRequestHook` | **B9** (PR #38) |
| `test_set_current_user_for_audit_populates_g` | `tests/integration/test_audit_logging.py::TestAuditRequestHook` | **B9** (PR #38) |

---

## 4. Mis-categorisations / known smells

1. **`tests/test_e2e.py` is not E2E** — it uses Flask's in-process test client.
   It belongs under `tests/integration/` (or under a new `tests/page-rendering/`
   bucket). The actual E2E suite lives at `tests/e2e/test_smoke.py` and is a
   Playwright opt-in run.
2. **`tests/test_metrics.py` is not a test** — it's a `print()` script left over
   from migration. Yields 0 collectable tests, contributes to `pytest`
   warnings. Either rewrite as `def test_metrics_singleton_*()` or delete.
3. **`tests/e2e/conftest.py` sets `collect_ignore_glob = ["*.py"]`** — the
   Playwright suite is intentionally hidden from auto-collection. Only `BASE_URL`
   + admin creds in env trigger it. This is by design (see `PROJECT_KNOWLEDGE.md`
   §5) but should be flagged in `docs/techContext.md` (already linked there).
4. **Duplicate fixtures** — `seeded_db`, `admin_user`, `app_context` re-defined in
   nested conftests in some integration files. Fold into top-level
   `tests/conftest.py` (Phase D).
5. **No explicit `slow` markers** — pytest currently runs everything; 402 tests
   take ≥ 30 s on a cold start because some integration tests rebuild the
   schema. Phase D should add `@pytest.mark.slow` and split the CI step.
6. **Coverage of new modules from audit-2026-04-28**:
   - `services/extensions.py::limiter` — covered indirectly via `test_api*.py`,
     no direct unit test for `init_app`. Phase E gap.
   - `services/scoring_service.py::get_base_points` — covered (`tests/test_scoring_service.py`),
     but no parametrized test asserting `2.1 → parent_code "2" → l2 column`.
     Phase E gap.
   - `services/audit_service.register_audit_request_hook` — covered
     (PR #38 added 3 tests). No further gap.

---

## 5. What Phase D will change (forward-looking)

1. Delete or rewrite `tests/test_metrics.py`.
2. Move `tests/test_e2e.py` → `tests/integration/test_page_rendering.py` (rename,
   no logic change) and update imports.
3. Consolidate `seeded_db` / `admin_user` / `app_context` fixtures into the
   top-level `tests/conftest.py`. Remove duplicates from nested conftests.
4. Mark all tests > 1 s with `@pytest.mark.slow` and split CI: `pytest -m "not slow"`
   on PR, full suite on `main`/`develop`.
5. Add `@pytest.mark.regression` to the 7 entries listed in §3 — makes
   `pytest -m regression` a one-liner audit guard.

## 6. What Phase E will add (gap analysis)

1. Direct unit test for `services/extensions.init_app` ensuring `limiter._storage`
   uses `RedisStorage` when `REDIS_URL` is present and `MemoryStorage` otherwise.
2. Parametrized test asserting `get_base_points(ach_type, league)` with leagues
   `1`, `2`, `2.1`, `2.2`, `3`, `3.1` — locks PR #35 invariants.
3. End-to-end audit-log write test using a Flask test-client session, asserting
   that an admin DELETE produces an `AuditLog` row with the correct `actor_id`.
   Stronger than the unit-level PR #38 tests because it exercises Flask-Login
   middleware too.
4. (optional) Test for `health.py::/health` happy path that asserts elapsed
   time < `socket_timeout * 2` so a regression of B10 surfaces immediately.

## 7. Phase F — mass run plan

1. `pytest tests/ -q --maxfail=5 --durations=20` — capture baseline.
2. `pytest tests/ -q -m "not slow"` — fast lane time-budget.
3. `pytest tests/ -q -m regression` — audit guard.
4. Playwright: start `make run` (Flask + Redis), set `BASE_URL=http://127.0.0.1:5000`,
   run `pytest tests/e2e/test_smoke.py` with `--no-header`. Capture
   `/tmp/e2e_artifacts/report.json`.
5. Any failure / flake → log under §8 below + Linear ticket (Phase H).

## 8. Findings log (filled by Phases D–F)

Baseline `pytest tests/ --ignore=tests/e2e` (commit on `main` after PR #38, executed 2026-04-29 on the VM):

```
402 passed, 1916 warnings in 82.26s
slowest call: tests/integration/test_routes.py::TestBulkLoadPerformance::test_leaderboard_load_performance — 2.05s
```

Warnings break down to 4 distinct sources but ~1900 occurrences:

| F# | Phase | Source | Symptom | Severity | Linear |
|---|---|---|---|---|---|
| F-1 | D | `services/admin.py:63-73` (also `tests/integration/test_audit_logging.py:116,175`) | ~1850 `flask_admin.contrib.sqla.ModelView` `DeprecationWarning`: «Passing a session object directly is deprecated and will be removed in version 3.0. Please pass the SQLAlchemy db object instead.» | low (forward-compat, very loud) | TBD |
| F-2 | D | `data/seed_service.py:159, 179, 200, 239, 249, 273` (only on `test_seed_all_force_clears_data`) | 9× `SAWarning: Identity map already had an identity for (...) replacing it with newly flushed object.` Suggests `force=True` truncates without flushing the session. | medium (real seed-bug smell, only one test exercises it) | TBD |
| F-3 | D | `tests/test_e2e.py:127` + `_pytest/python.py:166` | `ResourceWarning: unclosed file <_io.BufferedReader …>` for static `.png`/`.css` reads. Fixture opens via `open()` without `with`. | low (clean-up only) | TBD |
| F-4 | D | `tests/test_admin_achievements.py:126` | `LegacyAPIWarning: Query.get() considered legacy as of 1.x; use Session.get()`. | low (1 occurrence) | TBD |
| F-5 | D | `tests/test_metrics.py` | 0 collectable tests; module is a `print()` script left over from migration. Adds noise to `pytest -q` output. | medium (dead code in tests dir) | TBD |
| F-6 | E | `services/extensions.py::limiter` | No direct unit test for `init_app(app)` — only smoke-tested via API endpoints. | low (gap) | TBD |
| F-7 | E | `services/scoring_service.get_base_points` | No parametrized test across leagues `1`, `2`, `2.1`, `2.2`, `3`, `3.1`. PR #35 invariants are pinned by 4 tests but not exhaustively. | medium (gap) | TBD |

**Phase D action plan derived from this table:**

1. F-1 — touch `services/admin.py` to pass `db` instead of `db.session`; verify Flask-Admin works; update tests if needed. Drops ~1850 warnings to 0.
2. F-2 — investigate `seed_service.force=True` path; either fix the autoflush conflict or wrap in `no_autoflush`. Add explicit assertion that the identity map is empty after `_clear_all_tables`.
3. F-3 — replace `open(path)` with `with open(path)` in `tests/test_e2e.py:127`.
4. F-4 — replace `Query.get()` with `Session.get()` in the test.
5. F-5 — delete `tests/test_metrics.py` (its assertions are duplicated by metrics-related integration tests in `test_blueprints.py`); or rewrite as `def test_metrics_singleton()`.
6. F-6, F-7 — Phase E gap tests.

---

## Appendix A — file → category quick lookup

```
tests/__init__.py                                    skipped (empty)
tests/conftest.py                                    fixtures
tests/test_admin_achievements.py                     unit
tests/test_admin_service.py                          unit
tests/test_api.py                                    unit
tests/test_api_auth.py                               unit
tests/test_audit_delete.py                           unit (regression-adjacent)
tests/test_audit_service.py                          unit
tests/test_blueprints.py                             unit + B10 regression
tests/test_cache_and_admin.py                        unit
tests/test_data_services.py                          unit
tests/test_e2e.py                                    "UI" — actually integration
tests/test_metrics.py                                BROKEN (script, 0 tests)
tests/test_rating_formula.py                         unit
tests/test_rating_service.py                         unit
tests/test_scoring_service.py                        unit + PR-#35 regression
tests/test_validation.py                             unit + PR-#35 partial regression
tests/integration/test_admin_api.py                  integration
tests/integration/test_admin_api_extended.py         integration
tests/integration/test_admin_integration.py         integration
tests/integration/test_admin_smoke_flow.py           integration (smoke)
tests/integration/test_admin_views.py                integration
tests/integration/test_api_extended.py               integration
tests/integration/test_audit_logging.py              integration + B9 regression
tests/integration/test_cache_invalidation.py         integration
tests/integration/test_recalc.py                     integration
tests/integration/test_routes.py                     integration
tests/e2e/conftest.py                                opt-in only (collect_ignore)
tests/e2e/test_smoke.py                              E2E (Playwright)
```

---

_Last updated: 2026-04-29. Phase C of audit-2026-04-28 testing campaign._
