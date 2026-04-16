# QA Bug Report: Admin Panel Issues
**QA Engineer:** QA_TESTER (via MasterRouter v2.3.3)
**Date:** 2026-04-09
**Build:** v2.3.3-admin-completion (commits: 44a4ff2, 0586150, 4001965)
**Status:** 🔴 BLOCKERS FOUND

---

## BUG-001: Country edit/create формы — TypeError при открытии

**Severity:** 🔴 Critical (Blocker)
**Component:** CountryModelView
**URL:** `/admin/country/edit/?id=X` или `/admin/country/new/`
**Steps to reproduce:**
1. Открыть `/admin/country/`
2. Click Edit на любой стране (или Create New)
3. Форма не открывается — TypeError

**Expected:** Форма редактирования страны открывается
**Actual:** TypeError: BaseModelView.edit_view() got an unexpected keyword argument 'cls'

**Traceback:**
```
File "services/admin.py", line 505, in edit_form
    form = super().edit_form(obj, **kwargs)
...
TypeError: BaseModelView.edit_view() got an unexpected keyword argument 'cls'
```

**Root cause (предположительно):**
Конфликт `form_overrides` или `form_widget_args` с Flask-Admin form generation. Возможно `flag_source_type` поле создаётся как несовместимый тип формы.

---

## BUG-002: CountryModelView form_columns содержат несуществующие поля для Select2

**Severity:** 🟡 Suggestion
**Component:** CountryModelView
**File:** `services/admin.py:453`

**Issue:** `form_columns = ('code', 'name', 'flag_source_type', 'flag_path', 'flag_url')`
`flag_source_type` — это строковое поле с default='local', но Flask-Admin может некорректно обрабатывать его как SelectField без явного определения choices.

**Fix:** Добавить явную обработку `flag_source_type` в `create_form`/`edit_form`:
```python
def create_form(self, **kwargs):
    form = super().create_form(**kwargs)
    form.code.widget = Select2Widget()
    form.code.choices = COUNTRY_CHOICES
    form.flag_path.widget = Select2Widget()
    form.flag_path.choices = get_flag_choices()
    # Добавить обработку flag_source_type
    form.flag_source_type.choices = [('local', 'Local file'), ('api', 'FlagCDN API')]
    form.extra_js = COUNTRY_AUTOFILL_JS
    ...
```

---

## BUG-003: COUNTRY_AUTOFILL_JS ссылается на несуществующие элементы

**Severity:** 🟡 Suggestion
**Component:** Country AUTOFILL JS
**File:** `services/admin.py:208-271`

**Issue:** JS код ссылается на `$('#flag_source_type')` и `$('#flag_url')`, но Flask-Admin генерирует ID полей с префиксом формы (например `#flag_source_type_0` или другой формат).

**Fix:** Проверить сгенерированные ID полей в HTML и обновить селекторы в JS.

---

## BUG-004: Manager list template — checkbox ID extraction unreliable

**Severity:** 🟡 Suggestion
**Component:** Manager list template
**File:** `templates/admin/manager_list.html:93-120`

**Issue:** Checkbox IDs извлекаются через regex parsing href и fallback на text content first cell. Это fragile и может сломаться при изменении column_list.

**Fix:** Добавить `data-manager-id` атрибут через custom column formatter.

---

## BUG-005: manager_edit.html — flag preview показывает broken image на load

**Severity:** 🟢 Minor
**Component:** Manager edit template
**File:** `templates/admin/manager_edit.html:100`

**Issue:** `#flag_preview_img` имеет `display: block` но пустой `src=""` при начальной загрузке → broken image icon.

**Fix:** Изменить на `display: none` в CSS, показывать через JS только когда src установлен:
```css
#flag_preview_img {
    display: none;
    ...
}
```

---

## BUG-006: CountryModelView — form_args дублирование всё ещё может быть проблемой

**Severity:** 🟡 Suggestion
**Component:** CountryModelView
**File:** `services/admin.py:463-475`

**Issue:** После удаления `form_overrides`, `form_args` и `form_widget_args` объединены, но `flag_source_type` не имеет `validators` в dict, что может вызвать проблемы с required полями.

**Fix:** Убедиться что `flag_source_type` имеет корректные validators:
```python
'flag_source_type': {
    'label': 'Flag Source Type',
    'choices': [...],
    'validators': []
}
```

---

## Summary

| ID | Severity | Status | Component |
|----|----------|--------|-----------|
| BUG-001 | 🔴 Critical | OPEN | Country forms |
| BUG-002 | 🟡 Suggestion | OPEN | CountryModelView |
| BUG-003 | 🟡 Suggestion | OPEN | Country AUTOFILL JS |
| BUG-004 | 🟡 Suggestion | OPEN | Manager list template |
| BUG-005 | 🟢 Minor | OPEN | Manager edit template |
| BUG-006 | 🟡 Suggestion | OPEN | CountryModelView |

**Blockers:** 1 (BUG-001)
**Ready for DEVELOPER:** ✅

---

## Recommendation for DEVELOPER

**Priority order:**
1. **BUG-001** — исправить немедленно (блокирует Country CRUD)
2. **BUG-002 + BUG-003** — вероятно связаны с BUG-001
3. **BUG-004** — важно для bulk operations
4. **BUG-005** — minor UX issue
5. **BUG-006** — проверить после исправления BUG-001

**Suggested approach:**
- Протестировать Country форму локально после каждого изменения
- Проверить сгенерированный HTML для `flag_source_type` поля
- Возможно потребуется кастомный form class вместо `form_overrides`
