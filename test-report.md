# Test Report — PR #79 (TIK-74 / 75 / 76 / 77 / 78 / 79 / 80)

**Tested URL:** https://7b61b28494e0-tunnel-zzc1nhky.devinapps.com/ (staging tunnel)
**PR:** https://github.com/amatjkay/shadow-hockey-league_v2/pull/79
**Method:** ONE continuous browser-based E2E walkthrough on staging, with annotated screen recording. Anon flow → admin login (`s3ifer`) → search/filter/bulk-recalc → add new Round 3 / League 2.1 / Season 2025/26 achievement → verify on the public page.
**Test plan:** `test-plan.md` (committed in this PR).
**Result:** All 12 assertions across 7 tickets passed.

---

## TL;DR — All 12 assertions passed

| # | Ticket | Assertion | Result |
|---|---|---|---|
| A1 | TIK-74 | Anon header has no `Войти` button | PASS |
| A2 | TIK-75 | Season selector is a pill-shaped dark control with cyan caret | PASS |
| A3 | TIK-78 | Existing tooltip is concise (e.g. `Shadow 1 league TOP2 s23/24`) | PASS |
| A4 | TIK-77 | Public page: zero 404s under `/static/img/cups/`, zero refs to `r3.svg` | PASS |
| B1 | TIK-76 | Add Achievement modal: League 2.1 → Season dropdown contains `Season 2025/26` | PASS |
| B2 | TIK-77 | Saved Round 3 achievement icon = `hockey-sticks-and-puck.svg`, status 200 | PASS |
| B3 | TIK-78 | Saved Round 3 tooltip = `Shadow 2.1 league Round 3 s25/26` (no League/Season duplication) | PASS |
| C1 | TIK-79 | `/admin/achievement/` rows render plain strings, no `<Manager Felix>` reprs | PASS |
| C2 | TIK-79 | Audit-log target column renders `Name — Type (League, Season) — #id` (or `(deleted)`) | PASS |
| D1 | TIK-80 | `/admin/manager/?search=Russia` returned 48 Russian managers (cross-relation search) | PASS |
| D2/D3 | TIK-80 | `/admin/achievement/` filter sidebar narrows result set + default sort = `updated_at desc` | PASS |
| D4 | TIK-80 | Bulk action `Пересчитать очки` returns flash `Пересчитано 2 достижений.` (no 500) | PASS |

---

## Evidence

### A1 + A2 + A3 — Anon public page (TIK-74 + TIK-75 + TIK-78)

Header has zero `Войти` button. Season selector is a rounded dark pill with a cyan caret (no flat sky-blue bootstrap control). Existing achievement icons hover with concise tooltips like `Shadow 1 league TOP2 s23/24` — no duplicated `League X` / `Season YY/YY` segments.

![A1+A2+A3 anon public page with pill selector + concise tooltip](https://app.devin.ai/attachments/bd7353c6-0de1-4029-89d1-4c2151b43e17/01_anon_public_pill_tooltip.png)

### D1 — Cross-relation search (TIK-80)

`/admin/manager/?search=Russia` returns 48 managers — search now hits `country.name` (no manager is literally named "Russia").

![D1 cross-relation manager search](https://app.devin.ai/attachments/9a0ac1fc-a667-4502-9ca7-05fa5047dee2/02_admin_manager_search_russia.png)

### C1 + D3 — Achievement list, human-readable + default sort (TIK-79 + TIK-80)

Cells render plain strings (`Feel Good | Top 1 | Elite League | Season 2022/23`). Default sort puts the most recently updated row first.

![C1+D3 achievement list, default sort](https://app.devin.ai/attachments/f9a57ed8-2d58-48fe-92c5-7596c92e7008/03_admin_achievement_list_default_sort.png)

### D2 — Filter sidebar exists (TIK-80)

`Add Filter` exposes 4 FK-based filters (Type, League, Season, Manager).

![D2 filter sidebar](https://app.devin.ai/attachments/9a7500b0-f226-472c-9076-0be1636399ab/04_admin_achievement_filter_sidebar.png)

### D2 — Filter actually narrows result set (TIK-80)

`season.code contains 25/26` returns 27 rows, all `Season 2025/26`.

![D2 filter applied](https://app.devin.ai/attachments/df366fee-caed-43dd-82ff-ca7ab4d4b33a/05_admin_achievement_filter_25_26.png)

### D4 — Bulk action dropdown (TIK-80)

`With selected` dropdown contains both built-in `Delete` and the custom `Пересчитать очки`.

![D4 with selected dropdown](https://app.devin.ai/attachments/6b5a8de9-969b-497c-9337-a908b95514e1/06_admin_achievement_with_selected.png)

### D4 — Bulk recalc flash (TIK-80)

After ticking 2 rows + applying `Пересчитать очки` (with confirmation dialog), the page reloads with flash `Пересчитано 2 достижений.` and HTTP 200, no 500 / "не удалось" message.

![D4 bulk recalc flash](https://app.devin.ai/attachments/682d8f3d-86ec-45fd-b332-c96946c0c08c/07_admin_bulk_recalc_flash.png)

### C2 — Audit log target labels (TIK-79)

Each row's `Target ID/Link` is a human-readable label of the form `Name — Type (League, Season) — #id`. Stale rows pointing at deleted parents render as `Achievement #87 (deleted)` instead of crashing or showing a bare integer.

![C2 audit log human-readable](https://app.devin.ai/attachments/d581e97f-a53b-438d-9dbb-c2037b9a3a84/08_admin_audit_log_human_readable.png)

### B1 + B2 — Add Achievement → Round 3 / League 2.1 / Season 2025/26 saved (TIK-76 + TIK-77)

Modal populated correctly, including the Season dropdown that was previously empty. After save, the new row appears in the manager-edit panel with icon `hockey-sticks-and-puck.svg` (no `r3.svg`).

![B1+B2 admin after save](https://app.devin.ai/attachments/b2bd19a1-3499-4eee-8282-75f4e3093ea0/09_admin_after_save_round3_l21.png)

### B2 + B3 — Public page after save (TIK-77 + TIK-78)

Feel Good (rank 8) now has a 4th icon. Inline DOM verification:

```html
<img title="Shadow 2.1 league Round 3 s25/26"
     src="/static/img/cups/hockey-sticks-and-puck.svg"/>
```

`performance.getEntriesByType('resource')` filtered to `/static/img/cups/`:

```json
{
  "total": 5,
  "realBrokenCount": 0,
  "statusBreakdown": { "200": 5 },
  "allUrls": [
    "top2.svg", "top3.svg", "best-reg.svg",
    "hockey-sticks-and-puck.svg", "top1.svg"
  ]
}
```

Zero 404s, zero references to `r3.svg` / `r1.svg` / `best.svg`.

![B2+B3 public page after save](https://app.devin.ai/attachments/0136acc9-444a-4dd2-a8f9-3733b80e715c/10_public_after_save_with_round3_tooltip.png)

---

## Recording

Full annotated walkthrough (all 12 assertions in one continuous video):
https://app.devin.ai/attachments/39149772-924e-402a-822e-79b2616222c8/rec-d0caef92-9a71-4d6f-b68a-0110d30c52c3-edited.mp4

---

## Adversarial reasoning

For each assertion I asked "would this look identical if the change were broken?":

- A1 — broken would still show `Войти`. Distinct.
- A2 — broken would have flat sky-blue select with native arrow. Visually distinct from the cyan-pill version.
- A3 / B3 — broken tooltip would include `League 2.1` and `Season 2025/26` as duplicated segments. Distinct exact-string check.
- A4 / B2 — broken would emit 404 for `cups/r3.svg`. Distinct status-code check.
- B1 — broken Season dropdown would have `options.length === 1` (only `-- Select --`). Distinct count check.
- C1 — broken cells would be wrapped in angle brackets (`<Manager Felix>`). Distinct regex check.
- C2 — broken target column would be a bare integer. Distinct shape check.
- D1 — broken search would return zero rows (no manager is named "Russia"). Distinct row-count check.
- D2 — broken filter would either be missing entirely or fail to narrow. Distinct row-count check.
- D3 — broken default sort would put oldest row first. Distinct timestamp-ordering check.
- D4 — broken bulk action would either be absent from the dropdown or 500 on click. Distinct "dropdown option exists" + "POST returns 200 + flash" check.

No assertion is "vibes-based"; every one has a concrete observable.

---

## Out of scope (not tested in this run)

- Owner-admin provisioning script (`scripts/ensure_owner_admin.py`) — not user-facing; covered indirectly by the fact that login as `s3ifer` works.
- Re-running the entire pytest suite — already green in CI on this PR (Quality & Tests + E2E Smoke).
- Visual regression beyond TIK-75 — not in scope of this PR.
- Vercel preview — known non-issue (this is a Flask app, not deployed to Vercel).
