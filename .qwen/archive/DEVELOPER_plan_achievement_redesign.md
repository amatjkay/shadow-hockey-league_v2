# DEVELOPER Plan: Achievement Redesign

**From:** PLANNER
**To:** DEVELOPER
**Priority:** P0 — Blocks new admin panel launch

---

## Context

ACHITECTURE документи:
- `ADR-002_achievement_redesign.md` — архитектурные решения
- `IMPLEMENTATION_PLAN_achievement_redesign.md` — детальный план (698+ строк)

Спецификация:
- `docs/SPECIFICATION.md` — FR-03, FR-03.1, FR-04, API-005

**Суть изменений:**
1. Страница "Достижения" → справочник Achievement Types с калькулятором очков
2. Карточка менеджера → таблица достижений + кнопка "Добавить"
3. Массовое добавление достижений одному менеджеру (bulk-add API)
4. Удалить отдельный Achievement CRUD из меню

**Модели БД:** ✅ Уже правильные — миграции НЕ нужны

---

## Phase 1: Achievement Types Calculator (2-3h)

### Files:
- `templates/admin/achievement_type_create.html` — **СОЗДАТЬ**
- `templates/admin/achievement_type_edit.html` — **СОЗДАТЬ**
- `services/admin.py` — `AchievementTypeModelView`

### Steps:
1. Создать два шаблона (extends `admin/model/create.html` / `admin/model/edit.html`)
2. В `{% block tail %}` добавить:
   - Select2 dropdowns для League и Season (не form-bound, только для превью)
   - Блок калькулятора с градиентным фоном
   - JS: при выборе League → показать base_points из формы, при выборе Season → показать multiplier, final_points = base × multiplier
3. В `AchievementTypeModelView` добавить:
   ```python
   create_template = 'admin/achievement_type_create.html'
   edit_template = 'admin/achievement_type_edit.html'
   ```

### Acceptance:
- [ ] Калькулятор показывает correct base_points при выборе лиги
- [ ] Каскад League → Season работает
- [ ] Final points обновляется в реальном времени

---

## Phase 2: Manager Achievement Table (3-4h)

### Files:
- `templates/admin/manager_edit.html` — **ИЗМЕНИТЬ** (добавить таблицу достижений + модалку)
- `services/admin.py` — `ManagerModelView._manage_achievements` formatter

### Steps:
1. В `manager_edit.html` после основной формы добавить:
   - Таблица существующих достижений (загружается через AJAX)
   - Кнопка "+ Add Achievement" → открывает модалку
   - Модалка с Select2 полями: Type, League, Season, Points (readonly)
   - Кнопки: "+ Add Another" (добавляет в pending таблицу), "Save All" (POST к API)
   - Pending achievements таблица (жёлтый фон, не сохранено ещё)
2. В `_manage_achievements` formatter изменить ссылку на `.edit_view` вместо `.create_view`

### Acceptance:
- [ ] Таблица достижений показывает существующие записи
- [ ] Модалка открывается, Select2 работают
- [ ] Каскад League → Season работает
- [ ] Points auto-calculate в модалке
- [ ] "Add Another" добавляет строку в pending таблицу
- [ ] "Save All" вызывает bulk-add API
- [ ] Delete button удаляет достижения
- [ ] Total points показывает сумму

---

## Phase 3: API Endpoints (2-3h)

### Files:
- `blueprints/admin_api.py` — **ДОБАВИТЬ 3 эндпоинта**

### Endpoints:

#### 1. `GET /admin/api/managers/{manager_id}/achievements`
Возвращает все достижения менеджера + total_points

#### 2. `POST /admin/api/managers/{manager_id}/achievements/bulk-add`
Принимает массив `achievements: [{type_id, league_id, season_id}, ...]`
- Валидация: все поля обязательны, макс 50 записей
- Batch-load reference data (types, leagues, seasons)
- Duplicate check против существующих + intra-batch
- VR-004: League 2.1/2.2 → season.start_year >= 2025
- Расчёт points на сервере
- Создать записи, commit, invalidate cache
- Вернуть: created_ids, skipped, errors, manager_total_points

#### 3. `DELETE /admin/api/managers/{manager_id}/achievements/{achievement_id}`
- Проверить permission `delete`
- Проверить что achievement принадлежит этому менеджеру
- Удалить, commit, invalidate cache
- Вернуть: manager_total_points

### Acceptance:
- [ ] Все 3 эндпоинта работают
- [ ] Permission checks работают
- [ ] Duplicate detection работает
- [ ] Cache invalidation срабатывает

---

## Phase 4: Validation + Error Handling (1-2h)

### Files:
- `templates/admin/manager_edit.html` — JS валидация
- `blueprints/admin_api.py` — server-side валидация

### Steps:
1. Inline duplicate detection в модалке (проверить против загруженных достижений)
2. Duplicate detection в pending таблице (intra-batch)
3. Error display: подсветить проблемные строки красным/жёлтым
4. Server validation: VR-001 (имя), VR-002 (код), VR-005 (points range)

### Acceptance:
- [ ] Дубликаты подсвечиваются до отправки
- [ ] Ошибки API показываются пользователю
- [ ] "Save All" неактивна пока есть ошибки

---

## Phase 5: Cleanup (1h)

### Files:
- `services/admin.py` — скрыть AchievementModelView из меню
- `templates/admin/manager_list.html` — обновить ссылку

### Steps:
1. В `init_admin()` убрать `admin.add_view(AchievementModelView(...))`
2. Ссылку "Управление наградами (N)" вести на менеджер edit page
3. Убедиться что старые achievement_create/edit.html не ломают ничего

### Acceptance:
- [ ] В меню админки нет отдельной страницы Achievements
- [ ] Ссылка из списка менеджеров ведёт на edit page с таблицей

---

## Execution Order

```
Phase 1 → Phase 3 → Phase 2 → Phase 4 → Phase 5
```

**Почему Phase 3 перед Phase 2:** Phase 2 зависит от API endpoints из Phase 3.

---

## Test Checklist

После всех фаз:
```bash
python -m pytest tests/ -v --tb=short
# Ожидание: 297 passed, 0 failed
```

---

**Ready for DEVELOPER:** ✅
**Next routing:** DEVELOPER → QA_TESTER → CODE_REVIEWER → @save
