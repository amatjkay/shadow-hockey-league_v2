# Test Plan — PR #79 Round-2 QA Fixes (TIK-74 / 75 / 76 / 77 / 78 / 79 / 80)

## What changed (user-visible)

| Ticket | Before | After |
|---|---|---|
| TIK-74 | Public header showed `Войти` button on every page | Header is empty for anon users; admin logs in via direct URL `/admin/login/` |
| TIK-75 | Season selector was a flat bootstrap `<select>` with sky-blue 1px border | Pill-shaped, dark-themed control with cyan caret + glass background + focus ring |
| TIK-76 | Add-Achievement → League 2.1 → Season dropdown was empty (zero options) | Dropdown contains `Season 2025/26` |
| TIK-77 | Saving Round 3 / Round 1 / Best Regular wrote a path to a non-existent SVG; public page hit 404 on `/static/img/cups/r3.svg` | Path resolves to canonical existing SVG (e.g. `hockey-sticks-and-puck.svg`); migration backfilled previously-broken rows |
| TIK-78 | Hover tooltip read `Shadow 2.1 league Round 3 League 2.1 Season 2025/26 s25/26` (League / Season duplicated) | Tooltip is concise: `Shadow 2.1 league Round 3 s25/26` |
| TIK-79 | Admin lists rendered `<Manager Felix>`, `<Achievement 1/1/2>`, `<Country Belarus (BLR)>` (raw `__repr__`) | Lists render `Felix`, `Feel Good — Top 1 (Elite League, Season 2022/23)`, `Belarus`, etc. via canonical `__str__`. Audit-log target column: `Vladislav Belov — Round 3 (Second League, Season 2023/24) — #86`. |
| TIK-80 | `/admin/manager/` and `/admin/achievement/` had no filter sidebar; search only matched `Manager.name`; no bulk recalc-points action. App startup logged `Could not initialize Flask-Admin/Login: 'Mapper' object has no attribute 'country'` and silently skipped admin init. | Russia-search returns all Russian managers (cross-relation search); FK-based filter sidebar on every list view; explicit `configure_mappers()` before view registration; `Пересчитать очки` bulk action available on the achievements list; default sort puts most-recently-edited rows first. |

## Source-of-truth references

- TIK-74 — [`templates/index.html:79-91, 124-135`](templates/index.html) — `{% if current_user.is_authenticated %}` now wraps the entire `<nav class="desktop-nav">` and the mobile menu.
- TIK-75 — [`static/css/sections.css:32-93`](static/css/sections.css) — `.filters-bar`, `.filters-bar__label`, `.filters-bar__select` rules.
- TIK-76 — [`migrations/versions/b5f2a8e1c34d_backfill_season_start_end_years.py`](migrations/versions/b5f2a8e1c34d_backfill_season_start_end_years.py) + [`data/seed_service.py:273-289`](data/seed_service.py).
- TIK-77 — [`models.py:161-172`](models.py) — `AchievementType.get_icon_url` fallback now returns `default.svg`. [`migrations/versions/c7d3e2f1a8b9_backfill_achievement_type_icon_path.py`](migrations/versions/c7d3e2f1a8b9_backfill_achievement_type_icon_path.py) — backfill + rewrite.
- TIK-78 — [`services/admin/views.py:177-182`](services/admin/views.py) — `model.title = type_resolved.name` only. [`migrations/versions/d8e4f3a2b9c0_normalize_admin_achievement_title.py`](migrations/versions/d8e4f3a2b9c0_normalize_admin_achievement_title.py) — normalises legacy verbose titles.

## Primary flow

ONE end-to-end recording on the staging tunnel that walks through every fix in a natural order: anon view → admin login → add a Round 3 / League 2.1 achievement → verify on the public page.

### Step 1 — Anon view (TIK-74 + TIK-75 + TIK-78 verification on existing data)

**Action:** Open `https://7b61b28494e0-tunnel-zzc1nhky.devinapps.com/` in a fresh tab (anonymous, no cookies).

**Assertions:**
- A1 (TIK-74): Header / top-right area contains **NO** button or link with the text `Войти`. Specifically, a textual check of the rendered DOM in the viewport must NOT contain the string `Войти` outside any login form.
- A2 (TIK-75): The element with class `filters-bar` is a rounded pill (`border-radius: 999px`), has a dark background (`rgba(0, 30, 60, …)`), and contains a `<select class="filters-bar__select">` whose dropdown caret is a cyan SVG (NOT the platform-default arrow). A broken implementation would leave the old flat sky-blue-bordered select.
- A3 (TIK-78, regression on existing rows): Hover any achievement icon in column "Кубки" of any manager. The tooltip text must match the pattern `^Shadow [0-9.]+ league [^ ]+( [^ ]+)?( [^ ]+)? s[0-9]{2}/[0-9]{2}$` and must NOT contain the substring `League 2.1 Season 2025/26` (or any other `League X Season YY/YY` duplication).
- A4 (TIK-77, regression): DevTools Network tab, filter `cups/`. Reload page. Every entry has status `200`. Zero entries have URL containing `r3.svg`, `r1.svg`, or `best.svg`.

**Pass/fail:** All four assertions must pass. A failure on any single one fails the test.

### Step 2 — Admin login (setup, NOT recorded as part of the test proof)

**Action:** Navigate to `/admin/login/`, submit `s3ifer / s3ifer1234`.

**Expected:** Redirect to `/admin/`. Header now shows `Админ-панель` + `Выйти (s3ifer)` (TIK-74 inverse — for authenticated users, header IS populated).

### Step 3 — Add Round 3 achievement on League 2.1 (TIK-76 + TIK-77 + TIK-78 — the central proof)

**Action:** Navigate to `/admin/manager/edit/?id=1` (manager Feel Good). Scroll to the achievements section. Click `+ Добавить достижение` (or whatever the Add-Achievement trigger is — confirmed below).

In the Add Achievement modal:
- Pick AchievementType = `Round 3`
- Pick League = `League 2.1`

**Assertion B1 (TIK-76):** The Season `<select>` populates with at least one option, and that option's text contains `25/26` or `2025/26`. A broken implementation would leave the dropdown empty (zero options) or disabled. **Specifically: `select.options.length >= 1` AND first option innerText matches `/25\/26|2025\/26/`.**

Pick Season = `Season 2025/26`. Save.

**Assertion B2 (TIK-77):** After save, navigate to `/` (public page). DevTools Network filter `cups/` and reload. Zero 404 responses. Zero URLs containing `r3.svg`. The new achievement icon for Feel Good in League 2.1 column resolves via a request to `/static/img/cups/hockey-sticks-and-puck.svg` returning **200**.

**Assertion B3 (TIK-78):** Hover the new icon. The browser tooltip equals exactly `Shadow 2.1 league Round 3 s25/26`. It must NOT contain the substrings `League 2.1` or `Season 2025/26` (those would indicate the legacy duplicated title).

**Pass/fail:** B1, B2, B3 must all pass. Any failure fails the central proof.

### Step 4 — TIK-79 readability check (admin-list rendering)

**Action:** Still logged in. Open `/admin/achievement/` (sortable list of all achievements).

**Assertion C1 (TIK-79):** The first table row's `Менеджер`, `Тип`, `Лига`, `Сезон` cells render as plain human-readable strings. Verifiable substrings:
- The cell text MUST NOT match the regex `^<[A-Z][a-zA-Z]+ .*>$` (i.e. nothing wrapped in angle brackets).
- The cell text MUST NOT contain the literal substring `<Manager `, `<AchievementType `, `<League `, `<Season `, or `<Achievement `.
- The cell text SHOULD contain the manager's `display_name` and the league name (e.g. `Feel Good`, `Top 1`, `Elite League`, `Season 22/23`).

**Action:** Open `/admin/auditlog/` (or whatever the audit-log slug is in this build).

**Assertion C2 (TIK-79):** The `Target` column on every row MUST contain a human-readable label of the form `<str(model)> — #<id>` (e.g. `Vladislav Belov — Round 3 (Second League, Season 2023/24) — #86`) or, for stale rows pointing at a deleted parent, exactly `<Model> #<id> (deleted)`. It MUST NOT be a bare integer.

### Step 5 — TIK-80 search / filter / bulk action (admin polish)

**Action:** Still logged in. Open `/admin/manager/?search=Russia`.

**Assertion D1 (TIK-80, cross-relation search):** Page returns HTTP 200. Every visible manager row's `Страна` column equals `Russia` (i.e. the search bar found managers via their country, not just by manager name). A broken implementation would return zero rows, since no manager is named "Russia".

**Action:** Open `/admin/achievement/`. Sidebar — set filter `type.name` = `Top 1`.

**Assertion D2 (TIK-80, sidebar filter):** Page returns HTTP 200. Every visible achievement row's `Тип` column equals `Top 1` (the FK-based filter actually narrowed the result set).

**Assertion D3 (TIK-80, default sort):** Without specifying any sort manually, the first row's `Обновлено` column is the most-recent timestamp — i.e. the table is sorted `updated_at desc` by default. A broken implementation would still sort ascending by ID.

**Action:** On the same `/admin/achievement/` page, tick the checkbox for one or two visible rows. Open the `С выбранными` dropdown.

**Assertion D4 (TIK-80, bulk recalc):** The dropdown contains an entry `Пересчитать очки`. Pick it, confirm the dialog, and verify the page reloads with a flash message `Пересчитано N достижений.` (where N matches the number of rows ticked). The selected rows' `Очки` column is unchanged from the pre-action value (since the helper recomputes the same value when reference data is unchanged) — but no error / 500 / "не удалось" flash appears. A broken implementation would either lack the dropdown option entirely or 500 on click.

**Pass/fail:** C1, C2, D1, D2, D3, D4 must all pass.

### Adversarial reasoning

For each assertion I asked "would this look identical if the change were broken?":

- A1: would-broken would still show `Войти` button. Distinct.
- A2: would-broken would have flat select with sky-blue border + native arrow. Visually distinct from the cyan-pill version.
- A3: would-broken would render a longer tooltip with the duplication. Distinct text-content check.
- A4 + B2: would-broken would emit 404 in Network. Distinct status-code check.
- B1: would-broken Season dropdown would be empty. Distinct `options.length` check.
- B3: would-broken tooltip would be the long verbose form. Distinct exact-string check.
- C1: would-broken admin-list cells would render `<Manager Felix>` etc. Distinct angle-bracket regex check.
- C2: would-broken audit log would show `42` instead of `Felix — Round 3 — #42`. Distinct shape — bare-int vs `str(...) — #id`.
- D1: would-broken Russia search would return zero rows (no manager is named Russia). Distinct row-count check.
- D2: would-broken filter would either be missing entirely or fail to filter. Distinct `Тип`-column equality check.
- D3: would-broken default sort would put oldest row first instead of newest. Distinct timestamp-ordering check.
- D4: would-broken bulk action would either be absent from the dropdown or emit a 500. Distinct "dropdown option exists" + "post returns 200 + flash" check.

No assertion is "vibes-based"; every one has a concrete observable.

## Out of scope

- Owner-admin provisioning script (`scripts/ensure_owner_admin.py`) — not user-facing; covered indirectly by the fact that login as `s3ifer` works.
- Re-running the entire 533-test pytest suite — already green in CI.
- Visual regression beyond TIK-75 — not in this PR.
