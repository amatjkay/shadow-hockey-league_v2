# 🔍 Аудит проекта — 9 апреля 2026

## Цель

Проверить текущее состояние кода и документации, выявить подтверждённые проблемные места и сформировать основу для плана доработок.

## Что проверено

- Контекст проекта: `.qwen/context/state_summary.md`, `.qwen/context/active_plan.md`, `.qwen/context/memory.md`
- Документация: `README.md`, `docs/BUSINESS_REQUIREMENTS.md`, `docs/SPECIFICATION.md`, `docs/TECHNICAL_SPECIFICATION.md`
- Код: `app.py`, `models.py`, `services/admin.py`, `blueprints/admin_api.py`, `templates/admin/index.html`
- Тесты: `pytest -q tests/test_admin_service.py tests/test_cache_and_admin.py tests/integration/test_admin_integration.py` (43 passed)
- Смоук-проверки через `Flask test client` для login/dashboard/logout/admin API

## Подтверждённые проблемы

### P0-1: Падение админ-дашборда после логина

- Файл: `templates/admin/index.html:65`
- Симптом: `BuildError: Could not build url for endpoint 'achievement.index_view'`
- Причина: endpoint `achievement.*` больше не зарегистрирован, но ссылка осталась в шаблоне.

### P0-2: `500` в API достижений менеджера

- Файл: `blueprints/admin_api.py:512-514`
- Симптом: `GET /admin/api/managers/<id>/achievements` возвращает `500`
- Ошибка: `expected ORM mapped attribute for loader strategy argument`
- Причина: вызов `db.joinedload(Achievement)...` вместо `joinedload(Manager.achievements)...`.

### P0-3: Падение logout в админке

- Файл: `services/admin.py:1101`
- Симптом: `BuildError: Could not build url for endpoint 'admin_login'`
- Причина: используется `url_for('admin_login')` вместо `url_for('admin_login.index')`.

---

## Новые дефекты (выявлены при UAT 10 апреля 2026)

### NEW-1: AttributeError в Country Edit View [P0]

- Файл: `services/admin.py:462-478`
- Симптом: `AttributeError: 'StringField' object has no attribute 'has_groups'`
- Причина: `flag_path` и `code` используют `Select2Widget` с `StringField` вместо `SelectField`.
- Статус: Исправлено в "Admin Stabilization v2".

### NEW-2: Select2 Ajax Error в AchievementType [P1]

- Файл: `templates/admin/achievement_type_edit.html:71-115`
- Симптом: `Option 'ajax' is not allowed for Select2 when attached to a <select> element`
- Причина: Select2 4.x не поддерживает ajax на `<select>`, только на `<input type="hidden">`.
- Статус: Исправлено в "Admin Stabilization v2".

### NEW-3: Countries в категории Data вместо Reference [P2]

- Файл: `services/admin.py:166`
- Симптом: Countries отображается в меню "Data" вместо "Reference".
- Причина: Countries является справочной таблицей, как AchievementType, League, Season.
- Статус: Исправлено в "Admin Stabilization v2".

## Дополнительные риски (не блокеры, но требуют фиксации)

### P1-1: Недостаточное покрытие tests для `blueprints/admin_api.py`

- Поиск по `tests/**/*.py` не выявил сценариев для `/admin/api/*`.
- Риск: regressions в критичных ручках не ловятся CI.

### P1-2: Рассинхрон документации/контекста

- `state_summary.md` указывает на v2.5.0 и завершённый этап.
- `active_plan.md` и часть docs остаются на более старом состоянии (v2.4.x/ранние допущения).

## Что уже в хорошем состоянии

- Базовые admin/integration тесты из существующего набора проходят (43/43).
- Основная архитектура (Flask + SQLAlchemy + Redis fallback + audit + RBAC) работает.
- Ветка содержит активную работу по админке с новыми API и шаблонами.

## Вывод

Система в рабочем состоянии, но текущая ветка содержит 3 критических runtime-дефекта в ключевом admin flow. До UAT/релиза нужно закрыть P0-блок, затем добрать автотесты и синхронизировать документацию.
