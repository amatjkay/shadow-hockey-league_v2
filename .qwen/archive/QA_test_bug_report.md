# QA TESTER BUG REPORT
**Date:** 2026-04-09
**Tester:** QA_TESTER (via MasterRouter v2.3.3)
**Status:** 🔴 BLOCKER FOUND — Tests failing before deployment

---

## BUG-TEST-001: test_cache_invalidation.py uses outdated Achievement fields

**Severity:** 🔴 Critical (Blocks deployment)
**File:** `tests/integration/test_cache_invalidation.py:47-55`
**Test:** `TestAPICacheInvalidation.setUp()`

### Issue
Test creates `Achievement` using old field names:
```python
achievement = Achievement(
    achievement_type="TOP1",  # WRONG — doesn't exist
    league="1",               # WRONG — doesn't exist
    season="25/26",           # WRONG — doesn't exist
    ...
)
```

### Expected (current model)
```python
achievement = Achievement(
    type_id=ach_type.id,      # FK to achievement_types
    league_id=league.id,      # FK to leagues
    season_id=season.id,      # FK to seasons
    title="TOP1 1 25/26",
    icon_path="/static/img/cups/top1.svg",
    manager_id=self.manager_id,
    base_points=800.0,
    multiplier=1.0,
    final_points=800.0,
)
```

### Fix Required
1. Create `AchievementType`, `League`, `Season` records in setUp
2. Use `type_id`, `league_id`, `season_id` instead of string fields
3. Add `base_points`, `multiplier`, `final_points` values

### Impact
- 1 test fails (stops test suite with `-x` flag)
- Other tests may have same issue
- Cannot verify cache invalidation works correctly

---

## NEXT STEPS

1. **DEVELOPER** должен исправить `test_cache_invalidation.py`
2. **DEVELOPER** должен проверить все тесты на использование правильных полей
3. **QA** перезапустит `pytest` после исправлений
4. **НЕ ДЕПЛОИТЬ** пока все тесты не пройдут

---

**Recommendation:** НЕ ДЕПЛОИТЬ до исправления всех тестов.
