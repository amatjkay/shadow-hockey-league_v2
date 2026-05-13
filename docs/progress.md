# Progress — Shadow Hockey League v2

> **Purpose:** Living document tracking only the **current** cycle of work.
> All agents MUST update this before ending their turn.
>
> Older sections live in `docs/archive/progress-pre-2026-04-29.md` and
> `docs/archive/2026-Q2.md`:
> - `## Progress (rotated 2026-05-04)` — 4 entries 2026-04-30 → 2026-05-01.
> - `## Progress (rotated 2026-05-13)` — 13 entries 2026-05-03 → 2026-05-08
>   (later), rotated per TIK-89 / T13 to keep the latest 10 active here.

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

---

## 2026-05-13: Rating — full-precision leaderboard totals + 3-decimal tiebreak display in top-10

User report: production leaderboard showed **two managers tied at rank 2**
(`Aliaksandr Naidzionau` and `Юрий Shestakov`, both displayed as `7.80`)
even though their achievement sets were completely different.

Root cause: `services/rating_service.calculate_achievement_points`
returned `round(base * mul, 2)` and `_build_leaderboard_impl` summed
those *already-rounded* per-achievement values into `total`. For the
reported pair the exact totals were `7.8000` vs `7.7955` (a real
0.0045 gap that should put them in distinct ranks), but the per-row
rounding inflated one of the four contributions for the second manager
(`0.45 × 0.70 = 0.315 → round(., 2) = 0.32`, +0.005) just enough to
make the rounded sums collide at `7.80`.

Fix (`PR-pending`, branch `devin/<ts>-leaderboard-precision-rank`):

- `calculate_achievement_points` now returns an additional un-rounded
  field `points_exact = base * mul` alongside the existing rounded
  `points` (which stays at 2dp for the per-achievement breakdown
  panel).
- `_build_leaderboard_impl` sums `points_exact` into `total`
  (`float`, was `int` initialised to `0`) and sorts / ranks on the
  exact value. Strict float equality is the right tiebreak here: two
  rows only share rank when every `base * mul` is bit-for-bit
  identical, i.e. when the careers really do produce the same total.
- New helper `_assign_total_display(result)` walks the top-10 rows,
  groups them by their 2-decimal display, and bumps the entire
  collision group to 3 decimals whenever those rows hold different
  ranks. Other rows (rank ≥ 11, or rank groups whose 2dp displays
  don't collide) keep the compact `XX.XX` format. True ties (same
  exact total → same rank) stay at 2dp — the shared rank pill
  already conveys the tie, so a trailing `0` would be noise.
- `templates/index.html` consumes the new `row.total_display` for
  both the score cell and the `data-total` row attribute. The
  breakdown panel still renders per-achievement `points` at 2dp via
  `breakdown_payload`.

Regression coverage in `tests/test_rating_service.py::TestLeaderboardPrecisionAndTies`:

- Phantom-tie scenario (Aliaksandr/Юрий arithmetic) → distinct ranks,
  `"7.800"` / `"7.796"` display.
- True tie (identical careers) → shared rank, `"7.80"` on both rows
  (no trailing-zero bump).
- Non-colliding rows keep 2dp (`"10.00"`, `"2.50"`).
- `points_exact` is exposed for callers that aggregate
  (`0.45 × 0.49 = 0.2205`, vs `points = 0.22`).

`make check` clean (black / isort / flake8 / mypy). `make test` —
576 passed (was 572); `services/rating_service.py` coverage 99 %.

---

## 2026-05-13: UI — fix points-formula tooltip positioning + outside-click + close button

Bug: clicking the `?` icon next to the *Очки* header opened the dialog
visually anchored to the bottom of the leaderboard table (often below
the fold) instead of centred in the viewport, and the backdrop only
covered the table — so clicks outside the table never reached the
backdrop and the modal stayed open.

Root cause: the table now carries `backdrop-filter: blur(3px)
saturate(115%)` (PR #99 glass refresh). Per the CSS spec, `filter` /
`backdrop-filter` / `transform` create a *containing block* for
`position: fixed` descendants. The tooltip dialog and its
`inset: 0` backdrop lived inside the table's `<th>`, so "fixed" was
fixed-to-the-table, not fixed-to-the-viewport.

Fix:
- `templates/index.html`: lift the `.tooltip-backdrop` and
  `.tooltip-content` siblings out of `<th>` and re-anchor them next to
  the `breakdown-sheet` aside at the document level — well clear of
  any containing-block-creating ancestor. Toggle button keeps its
  spot beside the *Очки* header. Add a small `× ` close button
  (`.tooltip-close`, `data-tooltip-close="points-help"`) in the
  modal's top-right.
- `static/js/script.js::shlInitTooltips`: new
  `[data-tooltip-close]` handler that mirrors the backdrop's
  `setOpen(id, false)` call.
- `static/css/components.css`: `.tooltip-body` is now
  `position: relative` so the close button can absolutely-position;
  `.tooltip-intro` gets `padding-right: 36px` so its text doesn't run
  under the new button. Light/dark theme tokens unchanged.

No source-code, schema, or test changes.

---

## 2026-05-13: UI — fuse season-filter tabs to leaderboard card

Small UI-only follow-up after the PR #99 glass-table refresh.

- `templates/index.html`: drop the `<span class="filters-bar__label">Сезон:</span>`
  caption and replace `aria-labelledby="season-filter-label"` with
  `aria-label="Выбор сезона"` directly on the radiogroup. Add modifier
  class `filters-bar--attached`.
- `static/css/sections.css`:
  - Remove dead `.filters-bar__label` + `::before` (calendar icon) rules and
    the matching mobile-media `.filters-bar--tabs .filters-bar__label` block.
  - Add `.filters-bar--attached` — matches `.table.league-table` width
    (`96% / max 1200px`), reuses `--shl-table-glass-bg` + `--shl-table-glass-border`,
    rounded top corners only, `border-bottom: 0`, same blur token as the table.
  - Adjacent-sibling rule: `.filters-bar--attached + .table-responsive .table.league-table`
    drops its top radius + top border so the filter bar and table render as
    one card across both themes.

No source-code, test, or schema changes; pure CSS + template tweak.

---


## 2026-05-13: TIK-88 — owner-actions catalog + secrets fail-fast + .gitignore

Batch A of the 14-item owner-actions catalog (T01 + T02 + T03 + T07 + T08).
Mirrors **TIK-88** in Linear; **TIK-89** + **TIK-90** track the follow-up
batches (B = agent-actionable cleanups, C = owner-only rotation / Vercel).

**What landed (per `docs/owner-actions.md`)**

- **T01** — `docs/owner-actions.md` published as the single source of truth
  for owner-actionable follow-ups (14 rows + open questions).
- **T02** — `config.py::validate_production_secrets()` raises `RuntimeError`
  when `SECRET_KEY` / `WTF_CSRF_SECRET_KEY` / `API_KEY_SECRET` are unset or
  still set to the dev placeholder; wired from `app.py::create_app()` when
  `FLASK_ENV=production`. No-op in dev / testing.
- **T03** — `.gitignore` now excludes `bandit_report*.json`, `.coverage.*`,
  `*.log`, `.tool-versions`. The tracked-but-empty `bandit_report.json`
  + `bandit_report_main.json` (each contained the literal string of their
  own path) are removed via `git rm`.
- **T07** — `docs/activeContext.md` § Immediate Next Steps replaced with a
  link to the catalog. The two inline owner-actions (secret rotation,
  Vercel) are now **T09** / **T12** in the catalog.
- **T08** — `docs/INDEX.md` registers the new catalog; `AGENTS.md` § 6
  Version History entry added.

**Tests**

- New file: `tests/test_config_fail_fast.py` (11 tests via parametrisation
  over `_PRODUCTION_SECRET_DEFAULTS`).
- Full suite: **561 → 572 passing** (+11). All other tests untouched.
- `make check` (black + isort + flake8 + mypy) clean.

**Out of scope (carried into follow-up tickets)**

- **TIK-89 / Batch B**: T04 (`.env.example` cleanup), T05 (pip-audit into
  `make check`), T06 (README precommit-install note), T10 (repo-root stub
  cleanup — *open question*), T13 (`progress.md` rotation — *open question*),
  T14 (`decisionLog.md` rotation — *open question*).
- **TIK-90 / Batch C — owner-only**: T09 (secret rotation incl.
  `GEMINI_API_KEY`), T11 (`git filter-repo` decision), T12 (Vercel
  disconnect).
- Architecture question (not catalog): `/health` SLA — response-time
  budget + degraded-state escalation.

## 2026-05-11: TIK-86 — leaderboard race fix (`_LEADERBOARD_LOCK`)

Bug fix landed after the `task-formulation` skill — first dogfooded use of
the checklist (Context / Result / DoD / Anti-Goals) on a real ticket.

**What landed**

- `services/rating_service.py` — added module-level
  `_LEADERBOARD_LOCK = threading.Lock()` and split `build_leaderboard`
  into the public lock wrapper + private `_build_leaderboard_impl`. The
  lock serialises the joinedload-heavy query across threads to dodge a
  SQLAlchemy 2.0.49 cython result-processor race
  (`IndexError: tuple index out of range`, sporadic `None` rows).
- `tests/integration/test_routes.py::TestConcurrentRequests` — added
  `test_concurrent_homepage_requests_stress` (20 × 10 threads) that
  reproduced the bug ≥29 / 2000 calls *without* the lock and is 100%
  green with it. Test count 472 → 561 (other recent PRs raised it too;
  this PR adds 1).

**Why**

CI [run #207](https://github.com/amatjkay/shadow-hockey-league_v2/actions/runs/25681486012)
(PR #89 merge, TIK-85 polish v2) failed on the pre-existing flaky
`test_concurrent_homepage_requests`, which skipped `Deploy to
Production` and stranded polish v2 on `main` without reaching prod.
Production uses `gunicorn --workers 4 --sync` so the race cannot fire
today (no in-process threads), but the test client + any future
`--threads N` worker would trip it. Lock is a no-op in the sync-worker
hot path because cache hits (`@cache.cached(timeout=300)`) skip
`build_leaderboard` entirely.

**Verification**

- `make check` — black/isort/flake8/mypy all clean.
- `make test` — 561 passed, 0 failures.
- Local stress repro: 200 iterations × 10 threads = 2000
  `build_leaderboard` calls. Without lock: 29 errors. With lock: 0
  errors.

**Open follow-ups**

- Upstream-report the SQLAlchemy joinedload+cython race to the
  SQLAlchemy issue tracker (out of scope per TIK-86 Anti-Goals).
- If ever switching gunicorn to `--threads N`, audit the rest of the
  read-path for similar joinedload races (e.g. admin views).

## 2026-05-11: `task-formulation` skill + Obsidian wiki (`docs/wiki/`)

Docs / tooling change only. No source-code, schema, or test edits.

**What landed**

- `.agents/skills/task-formulation/SKILL.md` — new skill registered in
  AGENTS.md § 3. Operationalises the 4-section task-checklist
  (Context / Result shape / Definition of Done / Scope & Anti-Goals)
  that gates non-trivial work into the
  `architect → coder → verification → reviewer` pipeline. Cross-links
  the existing `karpathy-guidelines` skill and the `feature-research`,
  `linear-sync`, `verification` skills.
- `.github/ISSUE_TEMPLATE/well-formed-task.md` — same checklist
  rendered as a GitHub issue form so the rule applies to human-filed
  tickets as well as AI-driven ones.
- `docs/AI_WORKFLOW.md` — shortened to a 19-line pointer at the new
  skill (was already a short English version of the same checklist;
  no canonical content lost).
- `docs/wiki/` — new Obsidian-compatible navigation vault (16 notes,
  ~50 LOC each). Thin by design: each note is a 5–15-line summary
  followed by wikilinks (in-vault) and markdown links (to canonical
  docs / source) — no duplicated content from `AGENTS.md`,
  `PROJECT_KNOWLEDGE.md`, `docs/ARCHITECTURE.md`, `docs/API.md`,
  `docs/MIGRATIONS.md`, `docs/SUPERPOWERS.md`. Open
  `docs/wiki/` as an Obsidian vault to get the graph view.
- `docs/INDEX.md` — added entries for the wiki Home and the new skill.
- `AGENTS.md` — added § 3 row for `task-formulation`; § 6 Version
  History entry for 2026-05-11.
- `.gitignore` — excludes `docs/wiki/.obsidian/` (Obsidian generates
  this locally on first open).

**Why**

Requested by owner: agents handling complex tasks need a reusable
template that surfaces the Context / DoD / Anti-Goals before any code
is written. Pairs with `karpathy-guidelines` (which says *think first*
in the abstract) by giving the concrete artefact. The Obsidian wiki
was a separate ask in the same turn — gives owner/contributors a
graph-style map of the project without forking the canonical docs.

**Verification**

- All edits are Markdown. `make check` / `make test` unaffected — no
  Python / template / config touched.
- Pre-commit hook (`scripts/install_superpowers.sh --check`) ran on
  commit and passed.
- Issue template syntax follows the same frontmatter convention as
  GitHub's built-in `bug-report.md` / `feature-request.md` examples.

**Open follow-ups**

- Optional: a matching `pull_request_template.md` that surfaces the
  4-section checklist at PR creation time. Held back this round to
  keep the diff surgical (`karpathy-guidelines` § 3); owner can ask
  for it as a separate small PR.
- Optional: link the wiki from the top-level `README.md`. Same
  reason — held until owner confirms the navigation direction.

## 2026-05-09: TIK-84 — M2 Synthwave brand refresh + Concept C (B3)

After PR #86 (TIK-83, Concept A Refresh) merged at `04d9eed`, owner asked
to skip Concept B (Leaderboard 2.0) and jump straight to **B3 — palette
swap + full Concept C**. Scope chosen: synthwave palette sampled from
the SHL logo via PIL (top-1% S×V per hue bucket), full light/dark
theme system, sticky top-nav, season tabs (replacing `<select>`),
loading skeletons, top-3 border hints, magenta-rainbow top-10 sheen,
Lighthouse polish, all in a single PR.

### Change ([PR](https://github.com/amatjkay/shadow-hockey-league_v2) — `devin/tik-84-1778353930-synthwave-c`)

Ten small commits, one per logical step:

1. **`feat(ui): synthwave palette token swap` (`35cd986`)** —
   replaces the cyan-only `:root` palette with the synthwave family
   (`--shl-magenta-500: #c323e0` primary, `--shl-cyan-secondary-500:
   #41baf8` secondary, violet/indigo tertiaries, sunset/pink
   highlights). Legacy `--shl-cyan-*` token names point at the new
   magenta primary so the eight existing CSS files keep working
   without a rename pass. All `rgba(0,166,255,…)` tints retuned to
   magenta. Background tokens shifted to deep purples
   (`--shl-bg-deep: #070423`).
2. **`feat(ui): light theme override + body-bg token` (`447548a`)** —
   `:root[data-theme="light"]` plus a `@media (prefers-color-scheme:
   light) :root:not([data-theme])` block redefine the same tokens
   with AA-safe values for light surfaces (magenta lifted to
   `#a018bd`, cyan to `#0079b8`, body bg to a lavender gradient).
   `--shl-body-bg` is now a token so the body background image
   stays pluggable.
3. **`feat(ui): theme toggle (FOUC-safe inline + button + JS)`
   (`81c4b82`)** — inline `<head>` script reads
   `localStorage('shl-theme')` and mirrors it on
   `<html data-theme>` before first paint (no flash). Sun/moon
   button in the desktop header and inside the mobile menu;
   buttons stay in sync via `data-theme-toggle`. Aria labels and
   `aria-pressed` flip with the active theme.
4. **`feat(ui): sticky top-nav + scroll-shadow + backdrop-blur`
   (`8057127`)** — `.header { position: sticky; top: 0;
   backdrop-filter: blur(8px); }`. A 1 px sentinel placed below
   the header is observed via `IntersectionObserver`; when it
   leaves the viewport, `.header.is-scrolled` adds a soft
   magenta drop-shadow. `prefers-reduced-motion` disables the
   transition.
5. **`feat(ui): season tabs replace <select>` (`4746e9a`)** —
   the `<select id="season-filter">` is gone. Replaced by a
   `role="radiogroup"` of visually-hidden `<input type="radio">`
   + adjacent `<label class="season-tabs__tab">`. `:checked +
   .season-tabs__tab` paints the active pill in primary magenta
   with a `box-shadow` glow. `scroll-snap-type: x mandatory`
   centres the active tab on overflow; JS scrolls it into view
   on mount. URL contract preserved (`?season=N`).
6. **`feat(ui): loading skeleton on season change` (`45a7ee3`)** —
   `showLeaderboardSkeleton(10)` injects 10 placeholder rows
   into `<tbody>` on tab click. Each cell holds a `.skeleton`
   span whose 220% gradient sweeps under a `skeleton-shimmer`
   keyframe (1.4 s linear). The pre-existing centre spinner
   (`is-loading::before`) was retired since the skeleton carries
   the same affordance with content-shape feedback.
   `prefers-reduced-motion` collapses the gradient to a static
   tint.
7. **`feat(ui): top-3 gold/silver/bronze border hints`
   (`6ea0158`)** — `.league-table tbody .table-row:nth-child(1
   /2/3) .rank-cell` gets a `box-shadow: inset 4px 0 0 …`
   accent (sunset / silver / bronze). No layout shift; skeleton
   rows opt out via `:not(.table-row--skeleton)`.
8. **`feat(ui): top-10 sheen synthwave rainbow magenta+violet+cyan`
   (`ca273a4`)** — the 6-second sheen now stops on
   `magenta-500 → violet-300 → cyan-secondary-500 → magenta-500`,
   making the top-10 read as a synthwave gradient instead of
   a single-hue cyan. Skeleton rows skipped.
9. **`feat(ui): Lighthouse polish` (`977a1dc`)** —
   `<meta>` SEO tags (description, OG title/description/image,
   Twitter card, dual `theme-color` for dark/light), explicit
   `width`/`height` on every `<img>` (logo 167×40, telegram 40×40,
   country flags 30×30) for CLS, `loading="lazy"` on
   below-the-fold images, `decoding="async"` everywhere.
10. **`docs(progress, activeContext): TIK-84 synthwave + Concept
    C` (this commit)** — these notes.

### Why each piece

- **Tokens.** The TIK-83 token scaffold is what made this PR
  cheap: only `:root` had to change colour. Files unchanged: the
  rest of the CSS still references `--shl-cyan-*` (now magenta-aliased)
  and `--shl-bg-*` (now deep-purple). Renaming the legacy tokens
  is intentionally deferred — call sites are 8 CSS files and the
  rename is a separate, riskier diff.
- **Light theme.** Per spec — synthwave is a vibe, light is its
  «gallery» reading. Magenta darkens to `#a018bd` (AA on
  lavender), cyan to `#0079b8`, sunset to `#d6700c`. System
  preference (`prefers-color-scheme`) is the default; the toggle
  is an explicit override.
- **FOUC-safe inline.** A blocking `<script>` in `<head>` (before
  CSS) reads `localStorage` and applies `data-theme` synchronously.
  Without it, dark-default users who saved «light» would flash
  dark for one frame on every navigation.
- **Sticky nav.** The header is the only navigation; on long
  leaderboards the user lost it after the first viewport.
  `IntersectionObserver` on a 1 px sentinel is cheaper than a
  scroll listener (no per-frame work).
- **Tabs.** A `<select>` on a page with ≤ 5 seasons is poor UX
  on desktop (extra click, no overview) and identical on mobile
  (native picker). Tabs surface all options at once; mobile gets
  scroll-snap so the active option is always centred. The
  `<input type=radio>` + adjacent label pattern keeps full
  keyboard semantics (Tab into group, arrow keys to move,
  Enter to confirm).
- **Skeletons.** The original spinner overlay was opaque on the
  whole page and blocked all rendering. Skeletons paint
  in-content shape feedback in < 1 frame; even on a
  fast reload the user gets something to look at.
- **Top-3 hints.** The brand has «кубки» semantics already on
  the icons in column 4 (gold / silver / bronze); echoing them
  on the rank cell of rows 1-3 makes the visual hierarchy
  immediate without adding a separate podium component
  (kept for a future Concept B revival).
- **Synthwave sheen.** The TIK-83 cyan-only sheen was tame but
  on-brand; the rainbow sheen makes the top-10 sing in the
  same language as the new logo gradient.
- **Lighthouse.** The `<meta>` block was missing OG/Twitter
  entirely — direct shares on Telegram or Twitter rendered as
  the page URL with no preview. `loading="lazy"` + `width/height`
  shave 100-300 ms off mobile FCP and prevent layout shift on
  the long flag-image list.

### Status

- `make check` (black + isort + flake8 + mypy): TBD
- `make test`: TBD (target 560+ passed, no test added/removed
  here, TIK-81 regex regression unaffected — server-rendered
  HTML untouched, skeleton injection is client-only)
- CI: pending — PR not yet opened.

### Forward-looking

- **Token rename.** `--shl-cyan-500` aliasing magenta is a debt
  artefact; a follow-up should rename to `--shl-primary-*` /
  `--shl-secondary-*`.
- **Concept B revival** (top-3 podium, sticky thead, drawer):
  not in this PR. Owner can open a follow-up if wanted.
- **Test-regex relaxation** (carry-over from TIK-83): still
  pending; would let future PRs add `<td>` attrs without
  test churn.

## 2026-05-08 (later²): TIK-83 — M2 UI-редизайн, Концепт A (Refresh)

After PR #85 (backlog audit) merged, M2 milestone «Современный UI-редизайн
(Task 2)» was empty. Owner request: разобрать и предложить редизайн. Audit
phase produced `audit_ui_2026-05-08.md` (15 ranked issues + 3 concepts A/B/C
within the locked stack: Jinja2 + vanilla CSS + vanilla JS, no framework, no
build step). Owner picked **Concept A (Refresh)** with intent to layer B/C
in follow-up tickets.

### Change ([PR #86](https://github.com/amatjkay/shadow-hockey-league_v2/pull/86) — `devin/tik-83-1778245378-ui-redesign-a`)

Five small commits inside one PR:

1. **`feat(ui): design tokens + AA contrast + h1 clamp` (`083c31a`)** —
   `:root` design-token system in `static/css/base.css` (cyan family,
   skyblue tints, surface overlays, deep-blue backgrounds, ink, radii,
   `--shl-h1-size: clamp(2rem, 6vw, 3.75rem)`). Token migration across
   `typography.css`, `layout.css`, `sections.css`, `components.css`,
   `mobile-menu.css`, `rating-rules.css`. Body-link contrast on light
   surfaces lifted from `#00a6ff` (~3.9 : 1 on white) to `#0077b6`
   (`--shl-cyan-700`, ~5.4 : 1) — WCAG AA. h1 fluid via `clamp()`.
2. **`feat(ui): top-10 cyan sheen + table hover + reduced-motion` (`f203dfd`)**
   — replaces the legacy red→yellow gradient on top-10 rows with a
   cyan-500 → cyan-100 → cyan-500 gradient, slows the animation from `3s`
   to `6s`, and disables it under `prefers-reduced-motion: reduce`. Adds
   a subtle `--shl-cyan-tint-06` hover state on `.league-table .table-row`
   (200 ms transition). Final color literals in `tables.css` migrated.
3. **`feat(ui): mobile data-labels via [data-label]::before` (`1af4b27`)**
   — at ≤ 600 px each row becomes a stacked card (token border + radius
   + translucent surface). `<thead>` switches from `display: none`
   (which removed it from the AT tree) to `clip-path: inset(50%)`
   (visually hidden but still associated by SR). Removes redundant
   `@media (max-width: 320px)` h1 override now that `clamp()` handles it.
4. **`feat(ui): remove ESPN-404 placeholder + add data-label attrs` (`d90a07d`)**
   — drops the `a.espncdn.com/.../espn-404@2x.png` `<img>` in both the
   desktop header and the mobile menu (always 404'd, hidden via
   `onerror`); also the original spec called for `data-label` attrs
   on each leaderboard `<td>` to drive mobile labels via
   `[data-label]::before { content: attr(data-label) }`.
5. **`fix(ui): drive mobile cell labels from class, not data-label` (`e52f941`)**
   — the `data-label` attrs broke the existing TIK-81 regression test
   `tests/integration/test_routes.py::TestLeaderboardTotalFormatting`,
   which uses a brittle regex `<td class="table-items score-cell">`
   that requires `>` immediately after the class attribute. Per the
   project rule «не модифицировать тесты, чтобы они проходили», the
   `data-label` attrs were reverted and the labels were moved into
   `responsive.css` keyed by the existing cell classes
   (`.rank-cell::before { content: "Место" }`, etc.). Functionally
   identical visually; trade-off documented in PR description for a
   future test-regex-relaxation follow-up.

### Why each piece

- **Tokens.** Every brand color now has a single source of truth.
  Future concepts B/C only have to override `:root` to repaint the site;
  no `rg -F skyblue` sweeps required.
- **AA contrast.** `#00a6ff` on `rgba(255,255,255,0.35)` was close to
  failing WCAG AA on body text (~ 3.9 : 1). `#0077b6` lifts it to
  ~ 5.4 : 1 on the light translucent surfaces (rating-breakdown summary,
  tooltip headings, rating-rules h4) without darkening the brand
  colour on dark surfaces (header `.section-heading` stays cyan-500).
- **h1 clamp().** The 60 px fixed size was forcing the title to overflow
  on 320 px viewports. `clamp(2rem, 6vw, 3.75rem)` scales smoothly and
  retires the duplicated `@media (max-width: 320px)` override.
- **Top-10 sheen.** The red→yellow gradient was the loudest element on
  the page and the source of repeated «слишком кричит» feedback during
  the audit. The cyan-only gradient stays in the brand language and
  6 s feels less hectic. `prefers-reduced-motion` disables it entirely.
- **Hover state.** Did not exist before — clicking on the right row was
  a coin flip on dense leaderboards.
- **Mobile labels.** The legacy `<th> display: none` rule meant mobile
  users saw a column of headerless values with no idea which number
  was «Очки» vs «Место». New `clip-path` keeps `<th>` accessible for
  SR while CSS `::before` paints the label visually for sighted users.
- **ESPN placeholder.** A long-standing artefact (probably copy-paste
  from a tutorial). Always 404'd, was hidden via `onerror`, and
  surfaced an alt-text «ESPN» that confused everybody.

### Status

- `make check` (black + isort + flake8 + mypy): ✅
- `make test`: **560 passed, 0 failed** (was 559 before this PR; no
  test added here — the 560th came from a prior merge, so the count is
  the post-merge baseline).
- CI: `Quality & Tests` + `E2E Smoke (Playwright)` ✅; `Vercel`
  canceled is the known non-issue for this Flask repo (handoff §4).
- PR #86 awaiting owner review. Linear TIK-83 → `In Review`.

### Forward-looking

- **Concept B** — leaderboard 2.0 (top-3 podium, sticky thead, full-row
  breakdown drawer): separate ticket once A is merged.
- **Concept C** — full redesign (sticky-nav, tabs vs select, light/dark
  toggle, skeletons, Lighthouse ≥ 90): separate ticket, only after B
  if owner still wants it.
- **Test-regex relaxation** — small follow-up to relax
  `<td class="table-items score-cell">` to `<td [^>]*class="…score-cell…"[^>]*>`
  so future PRs can add legitimate attributes without test churn.

