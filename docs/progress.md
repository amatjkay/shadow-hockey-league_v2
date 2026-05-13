# Progress — Shadow Hockey League v2

> **Purpose:** Living document tracking only the **current** cycle of work.
> All agents MUST update this before ending their turn.
>
> Older sections live in `docs/archive/progress-pre-2026-04-29.md` and
> `docs/archive/2026-Q2.md`:
> - `## Progress (rotated 2026-05-04)` — 4 entries 2026-04-30 → 2026-05-01.
> - `## Progress (rotated 2026-05-13)` — 13 entries 2026-05-03 → 2026-05-08
>   (later), rotated per TIK-89 / T13.
> - `## Progress (rotated 2026-05-13, part 2 — TIK-92)` — 8 entries
>   2026-05-08 → 2026-05-13, rotated per TIK-92 to hold this file under
>   ~200 lines per the `doc-rotation` skill / TIK-92 DoD.

## 2026-05-13: TIK-98 — models.py: inline League.code uniqueness for native Postgres CREATE TABLE

Follow-up to TIK-95 (PR #115). On Postgres, `db.create_all()` failed
because `models.py::League.code` declared `unique=True, index=True`,
which made SQLAlchemy emit a separate `CREATE UNIQUE INDEX
ix_leagues_code` rather than an inline `UNIQUE (code)` constraint —
Postgres rejects the self-referential FK
`leagues.parent_code -> leagues.code` during `CREATE TABLE` when the
referent's uniqueness only arrives via a later index. Owner-approval
to touch `models.py` was granted for this single change.

**What landed**

- `models.py::League.code`: dropped `index=True`, kept `unique=True`,
  so SQLAlchemy renders `UNIQUE (code)` inline in `CREATE TABLE
  leagues`. Verified via `CreateTable(...).compile(dialect=postgresql)`
  and `db.metadata.tables['leagues'].constraints`.
- New alembic revision `3f6f9ed6c154_inline_league_code_unique.py`
  (down_revision `a4f1e9b2c5d7`): drops the now-redundant
  `ix_leagues_code` index via `batch_alter_table`. The inline UNIQUE
  constraint was already created by revision `b2c3d4e5f6a7`
  (`op.create_table(..., sa.UniqueConstraint("code"), ...)`).
  `downgrade()` recreates the original non-unique `ix_leagues_code`.
- `tests/integration/conftest.py`: removed the
  `_pg_create_all` / `_pg_drop_all` monkey-patch shim (TIK-95
  follow-up). The Postgres `TestingConfig` URL override stays in
  place, and a one-shot `db.drop_all()` runs at conftest import to
  clear data seeded by `alembic upgrade head` (the CI step before
  pytest) so each test's `setUp` starts on empty tables — real
  `db.drop_all` / `db.create_all` cycles between tests are now safe
  on Postgres thanks to the inline `UNIQUE (code)` constraint.

**Verification**

- `make check` — clean (`black`, `isort`, `flake8` count=0, `mypy`
  0 issues in 90 source files; `pip-audit` no known vulnerabilities).
- `pytest tests --ignore=tests/e2e -n auto --cov --cov-fail-under=87`
  — **579 passed**, total coverage **94.65%**.
- `docker run -d postgres:16-alpine` + `alembic upgrade head` —
  applied 24 revisions cleanly (`a4f1e9b2c5d7 -> 3f6f9ed6c154`); on
  the resulting schema, `leagues` shows `leagues_code_key` (UNIQUE
  CONSTRAINT) and no `ix_leagues_code` per `\d leagues`.
- `RUN_INTEGRATION_POSTGRES=1 pytest tests/integration/test_admin_integration.py tests/integration/test_cache_invalidation.py -v`
  — **33 passed** (DoD asked for 32; one extra test currently lives
  in the suite).

**Ready for Review**

- PR: `[TIK-98] models.py: inline League.code uniqueness for native
  Postgres CREATE TABLE`.

---

## 2026-05-13: TIK-92 — Memory Bank rotation part 2 (progress.md + decisionLog.md → 2026-Q2 archive)

Doc-curator follow-up to TIK-89 / Phase 3 (PR #109). Per the `doc-rotation`
skill, `docs/progress.md` and `docs/decisionLog.md` re-crossed the 200-line
threshold once TIK-89 Phases 1–3 + the same-day rating / UI / TIK-88 entries
landed. TIK-92 narrows each file to the latest ~30 days *and* ≤ 200 lines.
Move-only — no rewording, no content loss.

**What landed**

- `docs/progress.md`: moved entries 4–11 (lines 151–653, 8 entries
  2026-05-08 → 2026-05-13: Rating precision, UI tooltip, UI season-filter
  fuse, TIK-88, TIK-86, `task-formulation`, TIK-84, TIK-83) verbatim into
  a new `## Progress (rotated 2026-05-13, part 2 — TIK-92)` section of
  `docs/archive/2026-Q2.md`. The latest 3 entries (TIK-89 Phase 1 / 2 / 3,
  all 2026-05-13) stay active.
- `docs/decisionLog.md`: moved entries 2–9 (lines 127–653, 8 ADRs
  2026-05-03 → 2026-05-11: TIK-86 lock, task-formulation, Inspector
  backfill, admin-observer, Kilocode adapter, TIK-57 superpowers, TIK-51
  tech-debt, TIK-42 cleanup) verbatim into
  `## Decision Log (rotated 2026-05-13, part 2 — TIK-92)` of the same
  archive file. The latest ADR (2026-05-13 leaderboard precision) stays
  active. Three of the moved ADRs (task-formulation, Inspector, TIK-51)
  carried `**Forward contracts**` blocks; those blocks are preserved
  verbatim under `## Active Forward Contracts` at the top of
  `docs/decisionLog.md` per the `doc-rotation` skill safety rule.
- `docs/INDEX.md`: archive bullet expanded to list the two new
  `(rotated 2026-05-13, part 2 — TIK-92)` sections.
- `docs/owner-actions.md`: T13 / T14 rows annotated with the TIK-92 link
  alongside the existing TIK-89 / Phase 3 reference. Both stay `done`.

**Verification**

- `wc -l` before / after: `progress.md` 653 → ~200; `decisionLog.md`
  653 → ~160; `docs/archive/2026-Q2.md` 1100 → ~2150. Net repo delta:
  +0 lines (move-only). `make check` + `pytest --ignore=tests/e2e -n
  auto --cov --cov-fail-under=87` clean (see PR description for tails).

**Catalog (`docs/owner-actions.md`)**

- T13 + T14 stay `done` (already flipped in TIK-89 / Phase 3); both rows
  now cross-reference TIK-92 so future curators can find the second-pass
  rotation without re-reading the archive.

---

## 2026-05-13: TIK-97 — split `templates/index.html` (498 LOC) into `templates/partials/_*.html`

D6 of the maintenance backlog: decompose the leaderboard's single-file
Jinja template into reusable partials so future point-edits (e.g.
PR #105's top-10 cup icon tweak) touch a 30–100-line file instead of
scrolling through 498 lines.

**What landed**

- New `templates/partials/` with six includes:
  - `_head.html` — doctype + `<html lang="ru">` + `<head>` (meta, theme
    FOUC-fix, CSS modules).
  - `_header.html` — `<header>` (logo + Telegram + theme toggle + admin
    nav), header-sentinel, and the slide-in `.mobile-menu` (logically
    part of header navigation).
  - `_season_selector.html` — pill-shaped `filters-bar` with
    `season-tabs` radio group.
  - `_leaderboard_table.html` — empty-state branch + the league
    `<table>` (rating rows, medal pills, tandem badges, breakdown
    `data-*` payload, points-help tooltip trigger).
  - `_breakdown_drawer.html` — `<aside id="breakdown-sheet">` modal
    populated from clicked-row `data-*` attributes.
  - `_footer.html` — `<footer class="footer">` copyright block.
- `templates/index.html` rewritten as a thin shell using
  `{% include 'partials/_*.html' %}`. Jinja2 inherits the controller
  context automatically, so the points-help formula tooltip
  (`season_multipliers` + `achievement_types`) and the page-title
  `<h1>` stay in `index.html` (they don't fit any DoD partial and the
  DoD's anti-goal is "no new UI blocks").
- `blueprints/main.py::index` unchanged — same `rating_rows`,
  `seasons`, `selected_season_id`, `season_multipliers`,
  `achievement_types` context contract.
- No CSS, JS, controller, or business-logic changes. `templates/admin/*`
  untouched.

**Why this matters**

- `index.html` shrinks 498 → 90 lines (a thin layout shell); each
  partial is 7–95 lines and self-contained.
- Surgical edits (e.g. changing a single breakdown-sheet aria attribute
  or a season-tab label) now touch a focused file instead of scrolling
  through the full template.
- Diffs in future PRs are scoped — reviewers immediately see whether
  a change is in the header, the leaderboard table, or the breakdown
  modal.

**Verification**

- `curl http://127.0.0.1:5000/` and `curl http://127.0.0.1:5000/?season=5`
  before vs after — md5 identical (3114 / 3040 lines, same hash):
  - root  `cbd7ca0c5d17bdb130f392247e3e675d` (before == after).
  - s=5   `934968f2c241a3a41a20dbbedf748cb6` (before == after).
- `make check` — clean (black, isort, flake8, mypy, pip-audit).
- `make test` — 576 passed in ~24s (+4 vs the post-TIK-86 baseline of
  572; the delta comes from tests added in TIK-92..TIK-96 already
  merged to `main` before this branch).
- `make coverage` — 89% line coverage (services + blueprints + app +
  models) — above the ≥ 87% gate (TIK-54).
- `tests/integration/test_routes.py::Test*Homepage*` — all green
  without any test edits.

**Definition of Done**

- [x] `templates/partials/` populated with the 6 DoD files.
- [x] `templates/index.html` uses `{% include 'partials/_*.html' %}`.
- [x] `blueprints/main.py` unchanged.
- [x] `tests/integration/test_routes.py` passes without edits.
- [x] `make check` + `make test` green; coverage ≥ 87 % (89 %).
- [x] Before/after HTML render byte-identical (md5 match).
- [x] `docs/progress.md` updated (this entry).

## 2026-05-13: TIK-95 — CI: add Postgres matrix job (alembic + integration)

Non-blocking `integration-postgres` job added to
`.github/workflows/deploy.yml`. Validates that all 23 Alembic
migrations apply cleanly against `postgres:16-alpine` and that a
subset of integration tests (`test_admin_integration.py`,
`test_cache_invalidation.py`) pass on Postgres.

**What landed**

- `.github/workflows/deploy.yml`: new `integration-postgres` job
  (`continue-on-error: true`; not in `deploy.needs`).
- `requirements.txt`: added `psycopg2-binary>=2.9.9`.
- `tests/integration/conftest.py`: monkey-patches
  `config.TestingConfig` to use the Postgres `DATABASE_URL` when
  `RUN_INTEGRATION_POSTGRES=1`. Skips `test_routes.py` (hard-coded
  SQLite setup; TODO for follow-up).
- `docs/TROUBLESHOOTING.md`: new § 5 «Локальный прогон под Postgres».
- `docs/techContext.md`: CI pipeline description updated.

**No changes** to `models.py`, `app.py`, `config.py`, `seed_db.py`.

---

## 2026-05-13: TIK-93 — README badges: bump Coverage 87 → 95.07 % / Tests 572 → 576

Trivial doc drift fix flagged by TIK-93. README badge block (lines 9–10)
still advertised the pre-TIK-86 / pre-TIK-89-Phase-2 baseline (`Coverage
87% / Tests 572 passed`), even though the real numbers since those two
landings have been **576 passed, 95.07 % coverage** (recorded inline in
this file on 2026-05-13 under both Phase 1 and Phase 2 entries).

Note: TIK-94 landed in parallel and bumped the count to **578** by adding
`tests/test_rating_fallback_consistency.py`. TIK-93's badge bump is still
strictly the right floor (it removes a ≥4-test drift); the next badge
bump to `578` can ride on whichever follow-up doc-accuracy sweep cleans
up the 3 inline `572` mentions deeper in the README.

**What landed**

- `README.md` badges only:
  - `Coverage-87%-yellowgreen` → `Coverage-95.07%-brightgreen`.
  - `Tests-572%20passed-brightgreen` → `Tests-576%20passed-brightgreen`.

**Out of scope** (per Linear scope-in "обновление двух бейджей"):

- The three inline `572` mentions deeper in `README.md` (structure tree,
  `make test` table row, testing-section heading) — left for a follow-up
  doc-accuracy sweep. Same rationale as the `activeContext.md` Tests
  line (`AGENTS.md § 2` forbids editing it from this ticket).

**Verification**

- `pytest tests --ignore=tests/e2e -n auto --cov --cov-fail-under=87 -q`
  — **576 passed, 95.07 % coverage** (last 5 lines pasted into the PR
  description). Recorded *before* TIK-94 merged; rebasing onto post-TIK-94
  `main` would show 578 passed, but that's TIK-94's bump, not TIK-93's.
- `make check` — clean (`pip-audit`, `black --check`, `isort --check`,
  `flake8`, `mypy` — 0 errors).

**Catalog (`docs/owner-actions.md`)**

- N/A — TIK-93 is a docs-only badge bump, not in the T01..T14
  owner-actions catalog.

---

## 2026-05-13: TIK-96 — prefix invalidation for `leaderboard*` cache keys

**What landed**

- `services/cache_service.invalidate_leaderboard_cache()` now dispatches on
  the live backend instead of calling `cache.clear()`:
  - `RedisCache`: `SCAN` over `{CACHE_KEY_PREFIX}leaderboard*` via
    `cache.cache._write_client` + bulk `DELETE`. Honours
    `CACHE_KEY_PREFIX` automatically (cachelib stores it on
    `RedisCache.key_prefix`).
  - `SimpleCache`: iterate `cache.cache._cache` and `cache.delete`
    keys starting with `"leaderboard"`.
  - Unknown backend: fall back to `cache.clear()` with a warning log.
- Docstring rewritten to spell out the new contract and the
  per-backend behaviour.
- New regression test
  `tests/integration/test_cache_invalidation.py::TestPrefixInvalidation::test_prefix_invalidation_preserves_unrelated_keys`
  warms `/`, sets `cache.set("unrelated_key", "value")`, calls
  `invalidate_leaderboard_cache()`, and asserts `cache.get("leaderboard")
  is None` while `cache.get("unrelated_key") == "value"`. Runs on
  TestingConfig (`SimpleCache`).

**Why this matters**

- `cache.clear()` previously scrubbed every key in the configured
  backend on each CRUD — including Flask-Limiter rate-limiter counters
  whenever they share the cache Redis. Surface today is small; left
  in place this would scale into a real cost as more cached
  namespaces land. Now we only touch the keys the view actually owns.
- The cache-key contract (`leaderboard` + `leaderboard:{season_id}`)
  in `blueprints/main.py::_leaderboard_cache_key` is unchanged
  (TIK-96 anti-goal).

**Verification**

- `pytest tests/integration/test_cache_invalidation.py -v` — 15 passed
  (existing 14 + new `test_prefix_invalidation_preserves_unrelated_keys`).
- `make check` — clean (black / isort / flake8 / mypy + `pip-audit`).
- `make test` — 561 passed, ≥ 87 % coverage gate held.

---

## 2026-05-13: TIK-94 — tests: fallback consistency (`BASE_POINTS`/`SEASON_MULTIPLIER` ↔ seed)

Detection-only consistency tests (P3 from the rating-service audit) for the
two fallback dictionaries `services.rating_service` keeps in case
`achievement_types` / `seasons` are empty.

**What landed**

- `tests/test_rating_fallback_consistency.py` — new file, 2 tests:
  - `test_base_points_fallback_matches_seeded_reference_data`: seeds the
    reference tables via `data.seed_service.SeedService._seed_reference_data`
    (the same codepath `seed_db.py` runs), then iterates every
    `(root_league.code, ach_type.code)` in DB and compares
    `services.scoring_service.get_base_points(ach_type, league)` against
    `services.rating_service.BASE_POINTS[(league_code, type_code)]`
    with tolerance `1e-9`. Asserts both directions (no missing keys in
    fallback, no extras either). Subleagues (`parent_code is not None`,
    i.e. `2.1`/`2.2`) are intentionally skipped — they inherit
    `base_points_l2` via `League.base_points_field` and the flat
    `BASE_POINTS` dict only covers root leagues `1` and `2`.
  - `test_season_multiplier_fallback_matches_seeded_reference_data`:
    iterates every seeded `Season` and compares `Season.multiplier`
    against `SEASON_MULTIPLIER[s.code]` with tolerance `1e-9`. Asserts
    both directions.
- On drift either test collects every offending key into a single
  `pytest.fail()` so the diff is visible at a glance.

**Anti-Goals respected (per TIK-94)**

- No edits to `services/rating_service.py`, `services/scoring_service.py`,
  `models.py`, or `data/seed/*.json`.
- If a real drift were found, the follow-up is a separate ticket + an
  `xfail` marker on the offending test — not a silent fix here.

**Verification**

- `./venv/bin/pytest tests/test_rating_fallback_consistency.py -v` — 2/2 pass.
- `./venv/bin/pytest tests --ignore=tests/e2e -n auto --cov=...` —
  578 passed in ~31s, coverage 89% (≥ 87% gate, TIK-54).
- `make check` (black/isort/flake8/mypy + pip-audit) — clean.

---

## 2026-05-13: TIK-89 Phase 3 — rotate `docs/progress.md` + `docs/decisionLog.md` to `docs/archive/2026-Q2.md` (T13 + T14)

Batch B Phase 3 of the 14-item owner-actions catalog (T13 + T14).
Memory-Bank rotation per the `doc-rotation` skill — verbatim move, no
rewording.

**What landed**

- `docs/progress.md`: moved entries 11–23 (lines 595–1282, 688 lines,
  13 entries 2026-05-03 → 2026-05-08 (later)) into a new
  `## Progress (rotated 2026-05-13)` section of
  `docs/archive/2026-Q2.md`. Latest 10 entries (2026-05-08 →
  2026-05-13, inclusive of TIK-83 / TIK-84 / TIK-86 / TIK-88 / TIK-89
  Phase 1 / Phase 2 / rating-precision / UI tooltip / UI season-filter)
  stay active.
- `docs/decisionLog.md`: moved entries 10–12 (lines 607–730, 124 lines,
  3 entries 2026-04-30 + 2026-05-01 ×2 — the chronologically oldest
  block, matching the user-recommended cutoff
  `2026-04-30 / стык с docs/archive/2026-Q2.md`) into a new
  `## Decision Log (rotated 2026-05-13)` section of the same archive
  file. All three entries contained `**Forward contracts**` blocks; per
  the `doc-rotation` skill safety rule, those blocks are preserved
  verbatim at the top of `docs/decisionLog.md` under a new
  `## Active Forward Contracts` heading.
- `docs/INDEX.md`: archive bullet expanded to reference all four
  rotated sections inside `docs/archive/2026-Q2.md`.

**Why this matters**

- Per-turn token cost of reading `docs/progress.md` drops from ~1282
  lines (~14 K tokens) to ~593 lines — agents bringing the file into
  context every turn (per Memory Bank Protocol §1) pay roughly half.
- `docs/decisionLog.md` drops from 730 → ~606 lines. Smaller win in
  absolute terms but every Active Forward Contract is now visible in
  the first ~50 lines instead of buried 600+ lines deep.
- No content is lost; `git revert <rotation-sha>` restores the
  pre-rotation state atomically.

**Verification**

- `wc -l` before / after: `progress.md` 1282 → 594; `decisionLog.md`
  730 → 606; `docs/archive/2026-Q2.md` 268 → 1100. Net repo delta:
  +0 lines (move-only).
- `grep -nE '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' docs/progress.md` — 10
  entries, range 2026-05-08 → 2026-05-13.
- `grep -nE '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' docs/decisionLog.md` — 9
  entries, range 2026-05-03 → 2026-05-13.
- `make check` — clean.

**Catalog (`docs/owner-actions.md`)**

- T13 + T14 flipped from `open question` → `done`. Open questions are
  now down to `/health` SLA (separate Linear ticket TIK-91, Phase 4).

---

## 2026-05-13: TIK-89 Phase 2 — delete 5 repo-root stub files + drop their lint exclusions (T10)

Batch B Phase 2 of the 14-item owner-actions catalog (T10 only).

**What landed**

- Deleted 5 single-line stub files at the repo root: `locustfile.py`,
  `run_performance_test.py`, `test_mcp_client.py`, `test_linear_mcp.py`,
  `check_mcp_status.sh`. Each contained only `./<filename>:` — residue
  of a `for f in *; do echo "./$f:" > "$f"; done` mishap, no real
  implementation. The matching `bandit_report*.json` pair was already
  cleared in TIK-88.
- Removed the now-orphaned exclusions:
  - `pyproject.toml::[tool.black].force-exclude` (whole block, 4
    entries) plus the now-stale paragraph in the leading comment.
  - `pyproject.toml::[tool.isort].skip` (4 entries).
  - `pyproject.toml::[tool.mypy].exclude` (4 entries).
  - `.flake8::exclude` (4 entries).

**Why this matters**

`pytest --collect-only` at the repo root previously crashed on the three
`test_*.py` stubs (the parser tried to import them as test modules and
failed on `./test_mcp_client.py:` syntax). The work-around was the
`tests/` path override everywhere; the proper fix is no work-around.

**Verification**

- `pytest --collect-only -q` (no path, from repo root) — **576 tests
  collected in 0.25s**, no errors.
- `make check` — clean (`pip-audit`: "No known vulnerabilities found";
  `black`: 88 files unchanged; `isort`: skipped 14 files, was 18, the
  4 stubs are gone; `flake8`: 0 errors; `mypy`: "Success: no issues
  found in 88 source files").
- `pytest tests --ignore=tests/e2e -n auto --cov --cov-fail-under=87 -q`
  — **576 passed, 95.07% coverage** (unchanged from main baseline).

**Catalog (`docs/owner-actions.md`)**

- T10 flipped from `open question` → `done`. T13 / T14 stay
  `open question` (next PR / Phase 3).

---

## 2026-05-13: TIK-89 Phase 1 — `.env.example` cross-platform + `pip-audit` in `make check` + README pre-commit note

Batch B Phase 1 of the 14-item owner-actions catalog (T04 + T05 + T06).
Three surgical follow-ups, no source-code changes.

**What landed**

- **T04** — `.env.example` `DATABASE_URL` default flipped from a Windows-only
  absolute path (`sqlite:///C:/dev/shadow/shadow-hockey-league_v2/dev.db`) to
  a relative path (`sqlite:///dev.db`) that `config.get_database_url()`
  resolves to an absolute path off `BASE_DIR` on any platform. The
  Windows / Linux / VPS absolute-path examples remain in the comment block
  above as an escape hatch.
- **T05** — `make check` now lists `audit-deps` as a prerequisite, so
  `pip-audit -r requirements.txt -r requirements-dev.txt` runs in the same
  gate developers use locally and CI runs in `quality-and-tests`. `make
  audit-deps` stays as a standalone entry point.
- **T06** — README *Быстрый старт* (Linux/Mac block) now lists
  `make precommit-install` as an explicit step alongside `make setup` and
  `make run`, with a short paragraph explaining why `make setup` does *not*
  call it (hooks live in `.git/hooks/`, opt-in per checkout; CI still runs
  `make check` + `make test` + `make audit-deps` regardless).

**Verification**

- `make check` — clean (`pip-audit`: "No known vulnerabilities found";
  `black` / `isort` / `flake8` / `mypy` all 0 errors).
- `pytest tests --ignore=tests/e2e -n auto --cov --cov-fail-under=87 -q` —
  **576 passed, ≥ 87% coverage** (baseline bumped to 576 by the rating /
  tiebreak work that landed below in PR #103; T04/T05/T06 add no new
  tests).

**Catalog (`docs/owner-actions.md`)**

- T04 / T05 / T06 flipped from `follow-up` → `done`. T10 / T13 / T14 stay
  `open question` (separate PRs in Phase 2 + Phase 3).
