# Active Plan — Shadow Hockey League v2

**Дата:** 4 апреля 2026 г.
**Роль:** PLANNER (план v2.2 утверждён)
**Статус:** 🟢 План реализации аудита и управления кэшем готов
**Общий объём:** 12 Story Points

---

## 📋 Сводная таблица этапов

| Этап | Название                 | Приоритет | Подзадачи                                                                 | SP    | Зависимости |
| ---- | ------------------------ | --------- | ------------------------------------------------------------------------- | ----- | ----------- |
| 8.1  | Audit Log Infrastructure | 🔴        | Модель AuditLog, миграция, audit_service.py, интеграция в SecureModelView | **5** | —           |
| 8.2  | Cache Control UI         | �         | Метод flush_cache, кнопка в admin/index.html, CSRF, тестирование          | **3** | 8.1         |
| 8.3  | N+1 Optimization & QA    | 🟡        | Аудит rating_service.py, оптимизация, тесты аудита, интеграционные тесты  | **4** | 8.1         |

---

## 🗂️ Детализация этапов

### Этап 8.1: Audit Log Infrastructure (5 SP)

**Модель AuditLog:**

- Поля: `id` (PK), `user_id` (FK AdminUser), `action` (String), `target_model` (String, nullable), `target_id` (Integer, nullable), `changes` (JSON/Text, nullable), `timestamp` (DateTime)
- Индексы: `timestamp`, `(user_id, timestamp)`

**Миграция Alembic:**

- Файл: `migrations/versions/add_audit_log.py`
- Использовать `op.create_table()` с `sa.Column()` и `op.create_index()`

**Сервис логирования:**

- Файл: `services/audit_service.py`
- Функция: `log_action(user_id, action, target_model=None, target_id=None, changes=None)`
- Обработка ошибок с fallback в logger

**Интеграция в админку:**

- Расширить `SecureModelView` в `services/admin.py`
- Переопределить `after_model_change()` и `after_model_delete()`
- Логировать CREATE, UPDATE, DELETE, LOGIN, FLUSH_CACHE

**Файлы:** `models.py`, `migrations/versions/add_audit_log.py`, `services/audit_service.py`, `services/admin.py`
**Критерий приёмки:** Таблица создана, миграция работает, все CRUD операции в админке логируются

---

### Этап 8.2: Cache Control UI (3 SP)

**Эндпоинт сброса кэша:**

- Метод: `@expose('/flush-cache', methods=['POST'])` в `StatsAdminIndexView`
- CSRF-токен через `@csrf.exempt` + ручная проверка или встроенный механизм
- Действие: `cache.delete('leaderboard')`

**UI интеграция:**

- Шаблон: `templates/admin/index.html`
- Кнопка: `<form method="POST" action="/admin/flush-cache">` с CSRF токеном
- Flash-сообщение: `flash('Cache flushed successfully', 'success')`

**Логирование:**

- Вызов `audit_service.log_action('FLUSH_CACHE', user_id=current_user.id)`

**Файлы:** `services/admin.py`, `templates/admin/index.html`
**Критерий приёмки:** Кнопка работает, кэш сбрасывается, действие логируется

---

### Этап 8.3: N+1 Optimization & QA (4 SP)

**Аудит rating_service.py:**

- Проверить `build_leaderboard()` на использование `joinedload`
- Вывести SQL-запросы через `db.session.query(Manager).options(joinedload(...))`
- Если достижений > 20 на менеджера — рассмотреть `selectinload`

**Тесты аудита:**

- Файл: `tests/test_audit_service.py`
- Тесты: CREATE, UPDATE, DELETE, LOGIN, FLUSH_CACHE
- Проверка записи в AuditLog и корректности полей

**Интеграционные тесты:**

- Файл: `tests/integration/test_audit_and_cache.py`
- Тест: Полный цикл CRUD → проверка лога → сброс кэша → проверка инвалидации

**Файлы:** `services/rating_service.py`, `tests/test_audit_service.py`, `tests/integration/test_audit_and_cache.py`
**Критерий приёмки:** N+1 запросы отсутствуют, все тесты проходят, покрытие > 90%

---

## 🛑 Блокеры и риски

| Риск                             | Вероятность | Влияние | Митигация                                                            |
| -------------------------------- | ----------- | ------- | -------------------------------------------------------------------- |
| Конфликт миграций Alembic        | Средняя     | Высокое | Проверить текущую последнюю миграцию, использовать `down_revision`   |
| Нагрузка на диск при логировании | Низкая      | Среднее | Логировать только диффы при UPDATE, настроить очистку старых записей |
| Race condition при сбросе кэша   | Низкая      | Низкое  | Атомарная операция `cache.delete()`                                  |

---

## 🔄 Рекомендуемый порядок выполнения

```
Этап 8.1 (Audit Infrastructure) ──► Этап 8.2 (Cache UI) ──► Этап 8.3 (Optimization & QA)
```

---

## 🎯 Потенциальные этапы v2.3

| Этап | Название | Приоритет | SP | Описание |
| ---- | -------- | --------- | -- | -------- |
| 9.1 | Миграция на `datetime.now(datetime.UTC)` | 🟢 | 2 | Убрать 63 deprecation warnings (Python 3.14) |
| 9.2 | Очистка старых audit_logs | 🟡 | 1 | Настроить периодическую очистку > 90 дней |
| 9.3 | E2E тестирование production | 🟡 | 3 | Проверка на реальном сервере |
| 9.4 | Мониторинг RAM (1GB VPS) | 🟡 | 2 | Redis 128MB limit alerts |
| 9.5 | План миграции на PostgreSQL | 🟢 | 4 | Подготовка к росту > 1000 менеджеров |

---

## 🔄 История изменений

| Дата       | Изменение                        | Автор     |
| ---------- | -------------------------------- | --------- |
| 2026-04-04 | Инициализация модульной системы  | AI        |
| 2026-04-04 | План v2.2 сформирован (12 SP)    | PLANNER   |
| 2026-04-04 | Архитектура v2.2 утверждена      | ARCHITECT |
| 2026-04-04 | Требования v2.2 от ANALYST       | ANALYST   |
| 2026-04-04 | **План v2.2 готов к реализации** | PLANNER   |
| 2026-04-04 | **Этапы 8.1-8.2 реализованы**    | DEVELOPER |
| 2026-04-04 | **Баги BUG-001-009 исправлены**  | DEVELOPER |
| 2026-04-04 | **План v2.2 ЗАВЕРШЁН**           | PLANNER   |
| 2026-04-04 | **E2E тестирование завершено**   | QA_TESTER |
| 2026-04-04 | **BUG-010, BUG-011 исправлены**  | QA_TESTER |
| 2026-04-04 | **Релиз v2.2 слит в develop**    | DEVELOPER |
| 2026-04-04 | **Ветка feature/audit-log-v2.2 удалена** | DEVELOPER |

---

_Последнее обновление: 4 апреля 2026 г. — Релиз v2.2 слит в develop. Ветка удалена. Готово к планированию v2.3._
