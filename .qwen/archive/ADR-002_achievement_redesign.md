# ADR-002: Achievement System Redesign

**Status:** Proposed
**Date:** 9 April 2026
**Author:** ARCHITECT
**Context:** Shadow Hockey League v2 — Achievement system restructure from standalone CRUD to manager-centric workflow with types-only reference page.

---

## 1. Problem Statement

The existing Achievement page (`AchievementModelView`) is a full CRUD that requires the admin to manually pick Manager + Type + League + Season in one form. This is inefficient when adding multiple achievements to the same manager, and it conflates two distinct concepts:

1. **Achievement Types** — the dictionary of what achievement kinds exist (TOP1, TOP2, BEST, R3, R1) and their base point values per league.
2. **Achievements** — the actual instances of achievements assigned to managers for a specific (Type, League, Season) combination.

The redesign separates these concerns:
- The "Achievement Types" page becomes a reference dictionary with a live calculator for previewing point values.
- Manager edit cards become the primary place where achievements are added, viewed, and deleted per manager.

---

## 2. Architecture Decisions

### 2A. Achievement Types Page Redesign

**Decision: Repurpose existing `AchievementTypeModelView` with a custom template — do NOT create a separate view.**

**Reasoning:**

- `AchievementTypeModelView` already exists in `services/admin.py` and handles CRUD for the `AchievementType` model (code, name, base_points_l1, base_points_l2).
- Creating a new BaseView would duplicate Flask-Admin scaffolding (list, create, edit, delete) that `ModelView` already provides.
- The live calculator is a UI concern — it needs only a custom `create_template` and `edit_template` for `AchievementTypeModelView`.
- The calculator does NOT create `Achievement` records; it is purely a preview tool that reads `AchievementType.base_points_l1/l2`, `League` data, and `Season.multiplier` to compute `final_points = base_points * multiplier`.

**Implementation approach:**

1. Set `create_template = 'admin/achievement_type_create.html'` and `edit_template = 'admin/achievement_type_edit.html'` on `AchievementTypeModelView`.
2. Templates extend `admin/model/create.html` / `admin/model/edit.html` and inject:
   - Two additional Select2 dropdowns (League, Season) that are NOT bound to the form model.
   - A live calculator display area showing: `base_points` (from type + league), `multiplier` (from season), `final_points` (calculated).
   - JavaScript that calls existing API endpoints:
     - `GET /admin/api/leagues` — populate league dropdown
     - `GET /admin/api/seasons?league_id=X` — cascade populate season dropdown
     - `GET /admin/api/achievement-types/{type_id}/points?league_id=X` — get base_points
3. No new API endpoints needed for the calculator — API-003 (seasons), API-004 (type points), API-006 (leagues) are sufficient.

**Template structure:**

```
templates/admin/
  achievement_type_create.html    # extends admin/model/create.html, adds calculator JS + UI
  achievement_type_edit.html      # extends admin/model/edit.html, adds calculator JS + UI
```

**Why not modify the existing achievement_create.html / achievement_edit.html?**
Those templates belong to the old `AchievementModelView` CRUD. They will be repurposed into the manager achievement modal components (see Section 2B). Keeping type calculator templates separate avoids template collision.

---

### 2B. Manager Achievement Table in Edit Form

**Decision: Embed inline in the manager edit form (below the main form), NOT as a separate view or modal-only approach.**

**Reasoning:**

- **Inline table** gives immediate visibility of all achievements without opening a modal. The admin sees the full picture at a glance.
- **"Add Another" workflow** should be primarily client-side: a modal form opens, the admin fills Type + League + Season, clicks "Add Another" which appends a row to the table and clears the modal form. This avoids round-trips to the server for each addition.
- **Batch-save only** — individual row saves would create partial state and trigger multiple rating recalculations. Batch-save is simpler, more performant, and matches the spec (FR-04).
- Each row in the pending table has an "X" button for client-side removal before save.

**Component design:**

```
Manager Edit Page (/admin/manager/{id}/edit/)
├── Standard Flask-Admin form (name, country)
├── [Achievement Table Section]
│   ├── Existing achievements (rendered server-side, each with Delete button)
│   ├── Pending achievements (added via modal, client-side rows)
│   └── Total points (sum of final_points)
└── [➕ Add Achievement Button] → Opens modal
    ├── Type (Select2 AJAX → /admin/api/achievement-types)
    ├── League (Select2 AJAX → /admin/api/leagues)
    ├── Season (Select2 AJAX, cascaded → /admin/api/seasons?league_id=X)
    ├── Points (readonly, auto-calculated)
    ├── [Add Another] → appends row to table, clears form
    └── [Save All] → POST to bulk-add API
```

**Client-side vs server-side "Add Another":**
- Client-side for pending rows (no server round-trip per row).
- Server-side validation on Save All (check duplicates, league/season compatibility, calculate points on server).
- This matches the spec's "Add Another clears form for next entry" and "Save All saves all, recalculates rating."

**Individual row deletability:**
- Existing achievements: each row has a Delete button → `DELETE /admin/api/managers/{manager_id}/achievements/{achievement_id}`.
- Pending achievements (not yet saved): client-side "X" button removes from the DOM only.

---

### 2C. API Changes

#### New Endpoints

**1. `POST /admin/api/managers/{manager_id}/achievements/bulk-add` (API-005)**

Request body:
```json
{
  "achievements": [
    { "type_id": 3, "league_id": 1, "season_id": 7 },
    { "type_id": 4, "league_id": 2, "season_id": 8 }
  ]
}
```

Response:
```json
{
  "success": true,
  "summary": {
    "total_requested": 2,
    "created": 2,
    "skipped_duplicates": 0,
    "errors": 0
  },
  "details": {
    "created_ids": [101, 102],
    "skipped": [],
    "errors": []
  },
  "manager_total_points": 1800.0,
  "recalculation_triggered": true,
  "timestamp": "2026-04-09T12:00:00"
}
```

Business logic:
- Validate all type_id, league_id, season_id exist.
- Check VR-004: league 2.1/2.2 → season start_year >= 2025.
- Check VR-003: uniqueness per (manager_id, type_id, league_id, season_id).
- Calculate base_points from AchievementType (l1 vs l2 based on league code).
- Calculate final_points = base_points * season.multiplier.
- Create Achievement records with auto-filled title and icon_path.
- Call `invalidate_leaderboard_cache()`.
- Return `manager_total_points` = SUM of all achievements for this manager.

**2. `GET /admin/api/managers/{manager_id}/achievements`**

Response:
```json
{
  "manager_id": 5,
  "manager_name": "Feel Good",
  "total_points": 1800.0,
  "achievements": [
    {
      "id": 101,
      "type": { "id": 3, "code": "TOP1", "name": "TOP1" },
      "league": { "id": 1, "code": "1", "name": "League 1" },
      "season": { "id": 7, "code": "24/25", "name": "24/25", "multiplier": 1.0 },
      "base_points": 800.0,
      "multiplier": 1.0,
      "final_points": 800.0,
      "title": "TOP1 League 1 24/25",
      "icon_path": "/static/img/achievements/TOP1.png"
    }
  ]
}
```

Purpose: Load achievement table data for the manager edit page via AJAX.

**3. `DELETE /admin/api/managers/{manager_id}/achievements/{achievement_id}`**

Response:
```json
{
  "success": true,
  "deleted_id": 101,
  "manager_total_points": 1000.0,
  "recalculation_triggered": true
}
```

Business logic:
- Verify achievement belongs to the specified manager (prevent cross-manager deletion).
- Delete the achievement record.
- Call `invalidate_leaderboard_cache()`.
- Return updated manager total points.

#### Existing Endpoints — Changes Needed

| Endpoint | Change |
|----------|--------|
| `GET /admin/api/achievement-types` | No change — already returns Select2-compatible items |
| `GET /admin/api/achievement-types/{type_id}/points?league_id=X` | No change — used by calculator |
| `GET /admin/api/seasons?league_id=X` | No change — cascade filtering works |
| `GET /admin/api/leagues` | No change |
| `POST /admin/api/achievements/bulk-create` | No change — this is for bulk-creating the SAME achievement across MULTIPLE managers (different use case) |

The existing `bulk-create` endpoint (for multiple managers, one achievement) and the new `bulk-add` endpoint (for one manager, multiple achievements) serve different purposes and should coexist.

---

### 2D. Data Flow Diagrams

#### Achievement Types Calculator Flow

```
User opens Achievement Types create/edit page
         │
         ▼
  Page loads with form (code, name, base_points_l1, base_points_l2)
         │
         ▼
  User selects League (Select2 → GET /admin/api/leagues)
         │
         ▼
  User selects Season (Select2 cascaded → GET /admin/api/seasons?league_id=X)
         │
         ├─────────────────────────────────────┐
         ▼                                     ▼
  GET /admin/api/achievement-types/{type_id}/points?league_id=X
         │                                     │
         ▼                                     ▼
  Response: { base_points: 800 }        GET /admin/api/seasons (cached)
                                         │
                                         ▼
                                  Response: { multiplier: 1.0 }
         │                                     │
         └─────────────────┬───────────────────┘
                           ▼
              Calculate: final_points = 800 * 1.0 = 800.00
                           │
                           ▼
              Display: "800 × 1.00 = 800.00 points"
```

Note: The calculator on the Achievement Types page is a PREVIEW ONLY. It does NOT create any records. The user is editing the AchievementType's base_points_l1/l2 values — the calculator just helps them understand what the final points would be for any League+Season combination.

#### Manager Achievement Addition Flow

```
User opens Manager edit page
         │
         ▼
  Page loads with:
    - Standard form (name, country)
    - Achievement table (loaded via GET /admin/api/managers/{id}/achievements)
         │
         ▼
  User clicks "➕ Add Achievement" → Modal opens
         │
         ▼
  Modal form:
    1. Select Type (Select2 → /admin/api/achievement-types)
    2. Select League (Select2 → /admin/api/leagues)
    3. Select Season cascaded (Select2 → /admin/api/seasons?league_id=X)
    4. Points auto-calculated (readonly)
         │
    ┌────┴────┐
    ▼         ▼
  "Add      "Save
  Another"   All"
    │         │
    ▼         ▼
  Append    POST /admin/api/managers/{id}/achievements/bulk-add
  row to      │
  table,      ▼
  clear   Response: { created: [...], skipped: [...], errors: [...], total_points }
  modal       │
  form        ▼
         Reload achievement table (or update client-side)
              │
              ▼
         Flash success message with summary
```

#### Delete Achievement Flow

```
User clicks "❌ Delete" on an achievement row
         │
         ▼
  Confirmation dialog
         │
         ▼
  DELETE /admin/api/managers/{manager_id}/achievements/{achievement_id}
         │
         ▼
  Response: { success: true, manager_total_points: 1000.0 }
         │
         ▼
  Remove row from DOM, update total
  Invalidate leaderboard cache
```

---

### 2E. Component Structure

#### New Templates

| File | Purpose |
|------|---------|
| `templates/admin/achievement_type_create.html` | AchievementType create form with live calculator |
| `templates/admin/achievement_type_edit.html` | AchievementType edit form with live calculator |
| `templates/admin/manager_achievement_table.html` | Reusable macro/template for rendering achievement table (used in manager_edit.html) |
| `templates/admin/manager_list.html` | (If not already exists) Custom list view with achievement count column |

#### New JavaScript Components

| Component | Purpose |
|-----------|---------|
| `achievement_calculator.js` (inline in type templates) | Live calculator logic for Achievement Types page |
| `manager_achievements.js` (inline in manager_edit.html) | Achievement table management, modal form, bulk-add workflow |

#### Changed Views

| View | Change |
|------|--------|
| `AchievementTypeModelView` (admin.py) | Add `create_template`, `edit_template` for calculator templates |
| `AchievementModelView` (admin.py) | **Remove from menu** — achievements are now managed exclusively through manager cards. Keep the view class for potential admin override access but hide from navigation. |
| `ManagerModelView` (admin.py) | Add achievement table to edit form via custom `edit_form()` method that injects achievement data |
| `ManagerModelView._manage_achievements` formatter | Already shows count — keep as-is, ensure link goes to manager edit page |

#### Changed API Endpoints

| Endpoint | Action |
|----------|--------|
| `POST /admin/api/managers/{manager_id}/achievements/bulk-add` | New — API-005 |
| `GET /admin/api/managers/{manager_id}/achievements` | New |
| `DELETE /admin/api/managers/{manager_id}/achievements/{achievement_id}` | New |

---

## 3. Implementation Plan Outline

See companion document: `IMPLEMENTATION_PLAN_achievement_redesign.md`

**Phases:**

| Phase | Description | Estimated Effort |
|-------|-------------|-----------------|
| Phase 1 | Achievement Types page with calculator | 2-3 hours |
| Phase 2 | Manager achievement table + add form | 3-4 hours |
| Phase 3 | Bulk-add API endpoint (API-005) | 2-3 hours |
| Phase 4 | Delete achievement + validation | 1-2 hours |
| Phase 5 | Cleanup old achievement CRUD | 1 hour |

**Total estimated effort:** 9-13 hours

---

## 4. Risk Assessment

### 4.1. What Could Go Wrong

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Flask-Admin template override conflicts** | Medium | Medium | Test thoroughly — Flask-Admin's template inheritance can be fragile. Use `{{ super() }}` to preserve base functionality. |
| **Select2 cascade timing issues** | Medium | Low | The existing achievement_create.html already handles this pattern. Reuse proven code. |
| **Batch-save partial failures** | Medium | High | If 3 of 5 achievements save successfully and 2 fail, the user sees a confusing state. Mitigate by returning detailed `created`, `skipped`, `errors` arrays and allowing retry. |
| **Concurrent edits** | Low | Medium | Two admins editing the same manager's achievements simultaneously. Mitigate with unique constraint (uq_achievement_manager_league_season_type) — second save will fail gracefully. |
| **Points calculation drift** | Low | High | Client-side calculated points may differ from server-side. Mitigate by ALWAYS recalculating on server. Client-side values are display-only. |

### 4.2. Migration Considerations

- **No schema changes required** — the `Achievement` model already has the correct FK structure (`type_id`, `league_id`, `season_id`).
- **Existing Achievement records are unaffected** — the `AchievementModelView` CRUD still works at the database level; we are only changing the UI access pattern.
- **If `AchievementModelView` is hidden from menu**, existing deep links to `/admin/achievement/` will still work for users with appropriate permissions.

### 4.3. Backward Compatibility

| Aspect | Impact |
|--------|--------|
| Existing API endpoints | No changes — all 6 existing endpoints remain functional |
| Deep links to `/admin/achievement/` | Still work (Flask-Admin URL routing unchanged) — only the menu entry is hidden |
| Manager edit page | Extended with new achievement table — existing fields unchanged |
| Achievement Types page | Extended with calculator — existing CRUD fields unchanged |
| `bulk-create` endpoint (multiple managers) | Unchanged — separate use case from new `bulk-add` (single manager) |

### 4.4. Test Impact

- Existing unit tests for API endpoints must continue to pass (no endpoint signatures changed).
- New tests needed for:
  - `bulk-add` endpoint (API-005) — validation, duplicate handling, points calculation.
  - `GET /managers/{id}/achievements` endpoint.
  - `DELETE /managers/{id}/achievements/{achievement_id}` endpoint.
  - Achievement calculator UI (integration/selenium tests, if available).

---

## 5. Alternatives Considered

### 5A. Separate Achievement Types View

**Alternative:** Create a new `BaseView` subclass for the Achievement Types reference page instead of repurposing `AchievementTypeModelView`.

**Rejected because:** It would duplicate the CRUD scaffolding that `ModelView` already provides (list, search, filter, create, edit, delete). The calculator is purely a UI concern and does not require backend changes.

### 5B. Modal-Only Achievement Management

**Alternative:** Hide the achievement table entirely and require opening a modal to see/add/delete achievements.

**Rejected because:** The spec (FR-03.1) explicitly calls for a visible table on the manager edit page. Immediate visibility of all achievements is a core UX requirement.

### 5C. Individual Row Save (Non-Batch)

**Alternative:** Each achievement row has its own "Save" button for independent persistence.

**Rejected because:** It would trigger multiple rating recalculations and create a more complex state model. Batch-save is simpler, faster, and aligns with the spec's "Save All" workflow.

---

## 6. References

- `docs/SPECIFICATION.md` — FR-03, FR-03.1, FR-04, API-005
- `models.py` — Achievement, AchievementType, League, Season models
- `services/admin.py` — AchievementModelView, AchievementTypeModelView, ManagerModelView
- `blueprints/admin_api.py` — Existing API endpoints (API-001 through API-006)
