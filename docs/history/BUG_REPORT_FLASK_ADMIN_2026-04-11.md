# Bug Report: Flask-Admin 2.0.2 Compatibility Issues

**Date**: 2026-04-11  
**Version**: Flask-Admin 2.0.2 + WTForms 3.2.1 + SQLAlchemy 1.4.54  
**Status**: Open (8 issues identified)

---

## Summary

After upgrading to Flask-Admin 2.0.2 with compatibility patches, the following issues have been identified in the admin interface. These issues affect manager editing, achievement management, and bulk operations.

---

## Bug List

| ID | Title | Priority | Status | Component |
|----|-------|----------|--------|-----------|
| [BUG-01](#bug-01) | Season dropdown not working in Points Calculator | HIGH | OPEN | UI/JavaScript |
| [BUG-02](#bug-02) | Points Calculator Preview not calculating | HIGH | OPEN | UI/JavaScript |
| [BUG-03](#bug-03) | Achievements table showing "0" instead of data | HIGH | OPEN | API/Frontend |
| [BUG-04](#bug-04) | Add Achievement button not working | HIGH | OPEN | UI/JavaScript |
| [BUG-05](#bug-05) | Country Code and Flag Preview fields visible | MEDIUM | OPEN | UI/Template |
| [BUG-06](#bug-06) | Manager creation fails with AttributeError | HIGH | OPEN | Backend/Forms |
| [BUG-07](#bug-07) | Select2 errors in bulk actions | MEDIUM | OPEN | UI/JavaScript |
| [BUG-08](#bug-08) | API returning null for achievement relations | HIGH | OPEN | API/ORM |

---

## Detailed Reports

### BUG-01: Season dropdown not working in Points Calculator {#bug-01}

**Priority**: HIGH  
**Component**: UI/JavaScript  
**Affected Pages**:
- `/admin/achievementtype/edit/?id=X`
- `/admin/manager/edit/?id=X`

#### Description
The Season dropdown in the Points Calculator (Preview) section does not respond to user interactions. The dropdown appears disabled or fails to load season options when a league is selected.

#### Steps to Reproduce
1. Navigate to `/admin/manager/edit/?id=9`
2. Scroll to "Points Calculator (Preview)" section
3. Select a League from the "League (for preview)" dropdown
4. Attempt to select a Season from "Season (for preview)" dropdown

#### Expected Result
- Season dropdown should populate with available seasons for the selected league
- User should be able to select a season
- Points calculation should update based on season multiplier

#### Actual Result
- Season dropdown remains empty or disabled
- No options are loaded
- Points calculation cannot be performed

#### Root Cause Analysis
Likely JavaScript event handler issue after Select2 removal. The cascade from League to Season is not functioning.

---

### BUG-02: Points Calculator Preview not calculating {#bug-02}

**Priority**: HIGH  
**Component**: UI/JavaScript  
**Affected Pages**:
- `/admin/achievementtype/edit/?id=X`
- `/admin/manager/edit/?id=X`

#### Description
The Points Calculator in the preview section does not calculate points based on selected achievement type, league, and season.

#### Steps to Reproduce
1. Navigate to `/admin/manager/edit/?id=9`
2. Scroll to "Points Calculator (Preview)" section
3. Select Achievement Type, League, and Season
4. Observe the "Final Points" value

#### Expected Result
- Final Points should display calculated value: `base_points × season_multiplier`
- Value should update dynamically when selections change

#### Actual Result
- Final Points shows "0.00" or remains empty
- No calculation is performed

#### Root Cause Analysis
Depends on BUG-01 (Season dropdown). Calculator logic cannot execute without valid season selection.

---

### BUG-03: Achievements table showing "0" instead of data {#bug-03}

**Priority**: HIGH  
**Component**: API/Frontend  
**Affected Pages**:
- `/admin/manager/edit/?id=X`

#### Description
The Achievements table displays "0" in all columns (Type, League, Season, Base, Multi, Points) even though the database contains actual achievement data for the manager.

#### Steps to Reproduce
1. Navigate to `/admin/manager/edit/?id=9`
2. Scroll to "Achievements" section
3. Observe the achievements table

#### Expected Result
- Table should display actual achievement data:
  - Type: Achievement type code and name (e.g., "BEST (Best regular)")
  - League: League code and name (e.g., "1 (League 1)")
  - Season: Season code and name (e.g., "22/23")
  - Base: Base points value
  - Multi: Season multiplier
  - Points: Final calculated points

#### Actual Result
- All columns show "0" or empty values
- Total shows "0.00"

#### Technical Details
API endpoint `/admin/api/managers/{id}/achievements` returns JSON with null values for nested objects:
```json
{
  "type": {"id": 1, "code": "", "name": ""},
  "league": {"id": 1, "code": "", "name": ""},
  "season": {"id": 1, "code": "", "name": "", "multiplier": 1.0}
}
```

#### Root Cause Analysis
SQLAlchemy joinedload not properly loading related entities (type, league, season) for achievements.

---

### BUG-04: Add Achievement button not working {#bug-04}

**Priority**: HIGH  
**Component**: UI/JavaScript  
**Affected Pages**:
- `/admin/manager/edit/?id=X`

#### Description
The "➕ Add Achievement" button does not open the modal dialog for adding new achievements.

#### Steps to Reproduce
1. Navigate to `/admin/manager/edit/?id=9`
2. Scroll to "Achievements" section
3. Click the "➕ Add Achievement" button

#### Expected Result
- Modal dialog should open
- Form with Type, League, Season dropdowns should appear
- Points should calculate automatically

#### Actual Result
- Button click has no effect
- Modal does not open
- JavaScript error may be present in browser console

#### Root Cause Analysis
Event handler not attached to button or modal initialization failing.

---

### BUG-05: Country Code and Flag Preview fields visible {#bug-05}

**Priority**: MEDIUM  
**Component**: UI/Template  
**Affected Pages**:
- `/admin/manager/edit/?id=X`

#### Description
The "Country Code" and "Flag Preview" fields are displayed on the manager edit page, but these fields should be hidden as they are not needed for manager editing.

#### Steps to Reproduce
1. Navigate to `/admin/manager/edit/?id=9`
2. Observe the form below the main fields

#### Expected Result
- Country Code field should be hidden
- Flag Preview field should be hidden

#### Actual Result
- Both fields are visible on the page
- Fields show country code and flag image

#### Root Cause Analysis
CSS `display: none` not properly applied or fields removed from template.

---

### BUG-06: Manager creation fails with AttributeError {#bug-06}

**Priority**: HIGH  
**Component**: Backend/Forms  
**Affected Pages**:
- `/admin/manager/new/`

#### Description
Creating a new manager fails with `AttributeError: 'str' object has no attribute '_sa_instance_state'` when submitting the form.

#### Steps to Reproduce
1. Navigate to `/admin/manager/new/`
2. Fill in Name and select Country
3. Click "Save"

#### Expected Result
- Manager should be created successfully
- User should be redirected to manager list or edit page

#### Actual Result
- Server returns 500 Internal Server Error
- Traceback shows:
```
AttributeError: 'str' object has no attribute '_sa_instance_state'
File "...\admin.py", line 360, in create_model
    model = super().create_model(form)
```

#### Root Cause Analysis
The `country` form field returns a string ID (e.g., "5") instead of a Country ORM object. The `form.populate_obj()` method attempts to set `manager.country = "5"` (string), but SQLAlchemy expects a Country object.

---

### BUG-07: Select2 errors in bulk actions {#bug-07}

**Priority**: MEDIUM  
**Component**: UI/JavaScript  
**Affected Pages**:
- `/admin/manager/`

#### Description
JavaScript errors related to Select2 appear in browser console when using bulk actions feature on the manager list page.

#### Steps to Reproduce
1. Navigate to `/admin/manager/`
2. Select one or more managers using checkboxes
3. Click "With selected..." dropdown
4. Select "Add achievement..."

#### Expected Result
- Bulk achievement modal should open
- Type, League, Season dropdowns should work

#### Actual Result
- JavaScript error: `Uncaught Error: Option 'ajax' is not allowed for Select2 when attached to a <select> element`
- Dropdowns may not function correctly

#### Root Cause Analysis
Select2 4.x does not support `ajax` option on `<select>` elements (only on `<input type="hidden">`). The bulk action modal uses Select2 with ajax on select elements.

#### Fix Applied
- Removed Select2 ajax configuration
- Implemented manual option loading via jQuery AJAX
- Changed event handlers from `select2:select` to `change`

---

### BUG-08: API returning null for achievement relations {#bug-08}

**Priority**: HIGH  
**Component**: API/ORM  
**Affected Endpoints**:
- `GET /admin/api/managers/{id}/achievements`

#### Description
The API returns null values for achievement type, league, and season relationships, even though the database contains valid data.

#### Steps to Reproduce
1. Access API directly: `curl http://127.0.0.1:5000/admin/api/managers/9/achievements`
2. Observe the JSON response

#### Expected Result
```json
{
  "achievements": [
    {
      "id": 1,
      "type": {"id": 1, "code": "BEST", "name": "Best regular"},
      "league": {"id": 1, "code": "1", "name": "League 1"},
      "season": {"id": 1, "code": "22/23", "name": "2022/23", "multiplier": 1.0}
    }
  ]
}
```

#### Actual Result
```json
{
  "achievements": [
    {
      "id": 1,
      "type": {"id": 1, "code": "", "name": ""},
      "league": {"id": 1, "code": "", "name": ""},
      "season": {"id": 1, "code": "", "name": "", "multiplier": 1.0}
    }
  ]
}
```

#### Root Cause Analysis
SQLAlchemy `joinedload()` not properly eager-loading related entities. Possible causes:
- ORM mapping issues with SQLAlchemy 1.4.x
- Relationship lazy-loading despite joinedload
- Data inconsistency in database

---

## Environment

- **Flask**: 2.3.3
- **Flask-Admin**: 2.0.2 (with compatibility patches)
- **WTForms**: 3.2.1
- **SQLAlchemy**: 1.4.54
- **Flask-SQLAlchemy**: 3.0.5

## Compatibility Patches Applied

1. `_run_view` patch - passes `self` as positional argument instead of `cls` keyword
2. `Field.__init__` patch - removes `allow_blank` parameter for WTForms 3.x compatibility

## Next Steps

1. Investigate BUG-08 (API null values) - this is likely the root cause for BUG-03
2. Fix BUG-06 (Manager creation) by properly handling country field in form
3. Restore JavaScript functionality for BUG-01, BUG-02, BUG-04
4. Apply CSS fix for BUG-05
5. Verify BUG-07 fixes are complete

---

**Reported by**: QA_TESTER  
**Date**: 2026-04-11
