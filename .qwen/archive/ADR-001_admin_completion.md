# Architecture Decision Record (ADR)
## Shadow Hockey League Admin Panel Completion

**ADR ID:** ADR-001  
**Date:** 2026-04-09  
**Status:** Proposed  
**Author:** ARCHITECT (via MasterRouter v2.3.3)  
**Phase:** Architecture Design

---

## Context

Админка Shadow Hockey League v2 находится в состоянии ~65% готовности. Инфраструктура (модели, API, Auth, Audit) полностью реализована. Требуется завершить frontend-компоненты для соответствия требованиям requirements.json (FR-01 — FR-05).

### Текущее состояние:
- ✅ Select2 AJAX для Manager country (manager_edit.html)
- ✅ Select2 AJAX для Achievement FK (type, league, season)
- ✅ Cascading filters League → Season (JS)
- ✅ Auto-calculation points (base_points × multiplier)
- ✅ API endpoints (/admin/api/*) — 6 эндпоинтов
- ❌ Bulk operations UI (чекбоксы, modal, progress)
- ❌ Flag source type в модели Country (local vs FlagCDN API)
- ❌ Tandem warning UI
- ❌ Real-time flag preview в форме менеджера (есть код, но скрыт)

### Ограничения:
- Flask-Admin framework (ограничивает кастомизацию)
- SQLAlchemy models (требуют миграцию для новых полей)
- CSRF protection (нужно_exempt для bulk API)
- Flask-Login auth (все эндпоинты требуют auth)

---

## Decision 1: Cascading Filters Strategy

### Варианты:
**A. Client-side JS only** — загрузить все данные при инициализации, фильтровать на клиенте  
**B. Server-side API** — AJAX запросы при изменении parent поля  
**C. Hybrid** — initial load + AJAX refresh

### Решение: **B. Server-side API**

**Обоснование:**
- Seasons могут обновляться (новые сезоны)
- League→Season фильтрация требует проверки start_year >= 2025 для League 2.1/2.2
- Меньше трафика (не грузим все сезоны при загрузке страницы)
- Уже реализовано в API-003 (`/admin/api/seasons?league_id=X`)

**Реализация:**
- JS слушает `select2:select` на League
- Вызывает `/admin/api/seasons?league_id={id}`
- Перезаполняет Season dropdown
- Отключает недоступные сезоны

**Статус:** ✅ Уже реализовано в `achievement_edit.html` и `achievement_create.html`

---

## Decision 2: Bulk Operations UI Architecture

### Варианты:
**A. Flask-Admin custom list template** — кастомизация `admin/model/list.html`  
**B. Standalone page** — отдельная страница с полным контролем  
**C. Modal overlay** — Bootstrap modal поверх списка

### Решение: **C. Modal overlay + A (custom list template)**

**Обоснование:**
- Flask-Admin предоставляет `list_template` override
- Чекбоксы можно добавить через `column_extra_row_actions`
- Modal позволяет показать preview и прогресс
- Не ломаем стандартный UX Flask-Admin

**Реализация:**
1. Создать `templates/admin/manager_list.html` (extends `admin/model/list.html`)
2. Добавить чекбоксы в начало каждой строки
3. Добавить dropdown "With selected..." над таблицей
4. Создать Bootstrap modal для формы bulk creation
5. AJAX вызов к API-006 (`/admin/api/achievements/bulk-create`)
6. Progress bar + results dialog

**Структура файлов:**
```
templates/admin/
├── manager_list.html          # Custom list with checkboxes
├── bulk_achievement_modal.html # Modal template (include)
└── js/
    └── bulk_operations.js     # Bulk operations logic
```

**API изменения:** Не требуются (API-006 уже реализован)

---

## Decision 3: Country Flag Source Enhancement

### Варианты:
**A. Добавить поля в Country модель** — `flag_source_type`, `flag_url`  
**B. Вычисляемое поле** — генерировать URL из code  
**C. Внешняя таблица** — `CountryFlagSource`

### Решение: **A. Добавить поля в Country модель**

**Обоснование:**
- requirements.json FR-02 явно требует `flag_source_type` (local/API)
- Нужно хранить выбор пользователя (local file vs FlagCDN API)
- Простая миграция (2 колонки)
- Без ломания существующего функционала

**Изменения модели:**
```python
class Country(db.Model):
    # Существующие поля
    id = db.Column(...)
    code = db.Column(...)
    name = db.Column(...)
    flag_path = db.Column(...)  # Local file path
    is_active = db.Column(...)
    
    # Новые поля
    flag_source_type = db.Column(
        db.String(20), nullable=False, default='local',
        comment="local or api"
    )
    flag_url = db.Column(
        db.String(200), nullable=True,
        comment="FlagCDN API URL or custom URL"
    )
    
    @property
    def flag_display_url(self):
        """Resolved flag URL for display."""
        if self.flag_source_type == 'api' and self.flag_url:
            return self.flag_url
        return self.flag_path or f"https://flagcdn.com/w320/{self.code.lower()}.png"
```

**Миграция:**
```python
def upgrade():
    op.add_column('countries', sa.Column('flag_source_type', sa.String(20), nullable=False, server_default='local'))
    op.add_column('countries', sa.Column('flag_url', sa.String(200), nullable=True))

def downgrade():
    op.drop_column('countries', 'flag_url')
    op.drop_column('countries', 'flag_source_type')
```

**UI изменения:**
- `CountryModelView`: добавить radio group (local/api)
- Показать/скрыть поля в зависимости от выбора
- Auto-generate FlagCDN URL при вводе code

---

## Decision 4: Tandem Warning UI

### Варианты:
**A. JS validation** — клиентская проверка  
**B. Server validation** — серверная проверка с flash  
**C. Both** — клиентская + серверная

### Решение: **C. Both**

**Обоснование:**
- Клиентская проверка даёт мгновенный feedback
- Серверная проверка защищает от обхода JS
- requirements.json FR-01 требует `"rule": "tandem_detection"`

**Реализация:**
```javascript
// Client-side (manager_edit.html)
$('#name').on('input', function() {
    if (this.value.includes(',')) {
        showWarning('Tandem detected. Ensure both players represent one country');
    }
});
```

```python
# Server-side (ManagerModelView.on_model_change)
def on_model_change(self, form, model, is_created):
    if ',' in model.name:
        flash('Warning: Tandem detected. Ensure both players represent one country', 'warning')
```

---

## Decision 5: Real-time Flag Preview в Manager Form

### Статус: ✅ Уже реализовано (но требует активации)

`manager_edit.html` и `manager_create.html` уже содержат:
- Select2 AJAX для country
- Auto-fill country_code
- Flag preview image
- JS для обновления при выборе

**Проблема:** Поля `country_code` и `flag_preview` не отображаются в форме (скрыты через `display:none`)

**Решение:** Сделать поля видимыми через изменение `form_columns` в `ManagerModelView`:

```python
class ManagerModelView(SecureModelView):
    form_columns = ('name', 'country_id', 'country_code_display', 'flag_preview_display')
    # Добавить form_extra_fields для отображения
```

---

## Summary of Decisions

| # | Decision | Choice | Status |
|---|----------|--------|--------|
| 1 | Cascading Filters | Server-side API | ✅ Implemented |
| 2 | Bulk Operations UI | Modal + custom list | ❌ Requires development |
| 3 | Flag Source Enhancement | Add fields to Country | ❌ Requires migration + UI |
| 4 | Tandem Warning | Client + Server validation | ❌ Requires JS + Python |
| 5 | Flag Preview in Manager | Show existing hidden fields | ⚠️ Partial (code exists) |

---

## Consequences

### Positive:
- Минимальные изменения в существующем коде
- Обратная совместимость API
- Сохранение Flask-Admin patterns
- Чёткая структура для DEVELOPER

### Risks:
- Миграция БД требует downtime (minimal, <1s)
- Bulk UI может усложнить шаблон (mitigation: вынести JS в отдельный файл)
- FlagCDN API может быть недоступен (mitigation: fallback на local files)

---

## Next Steps

1. **ARCHITECT → PLANNER**: Декомпозировать решения в задачи
2. **PLANNER → DEVELOPER**: Приоритизировать и назначить
3. **DEVELOPER**: Реализовать по фазам:
   - Фаза 1: Показать flag preview в manager form (5 мин)
   - Фаза 2: Tandem warning (30 мин)
   - Фаза 3: Country flag source migration (1 час)
   - Фаза 4: Bulk operations UI (4-6 часов)

---

## Appendix

### Files to Modify:
1. `models.py` — добавить поля в Country
2. `services/admin.py` — ManagerModelView, CountryModelView
3. `templates/admin/manager_list.html` — создать
4. `templates/admin/js/bulk_operations.js` — создать
5. `migrations/versions/` — новая миграция

### Files Already Complete:
- `templates/admin/manager_edit.html` — Select2 + flag preview ✅
- `templates/admin/achievement_edit.html` — cascading + calc ✅
- `blueprints/admin_api.py` — 6 endpoints ✅
- `models.py` — FK relationships ✅

---

**Approved by:** Awaiting review  
**Implemented by:** Pending  
**Reviewed by:** Pending
