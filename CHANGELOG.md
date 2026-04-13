# Changelog

Все значимые изменения проекта Shadow Hockey League v2.

Формат основан на [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [2.6.0] — 2026-04-13

### AI Policy Stabilization & Project Cleanup

### Added

- **AI_POLICY.md v1.2** — единый источник правил для всех AI-агентов (7 ролей)
- **Thin IDE adapters** — `.windsurfrules`, `.cursorrules`, `copilot-instructions.md`
- **CODE_REVIEWER prompt** — `prompts/07_CODE_REVIEWER.md`
- **Policy validation script** — `scripts/check_policy_sync.py`
- **UAT Gate** — блокировка `@save` до `@approve`

### Changed

- **Documentation** — полная актуализация README.md, docs/ARCHITECTURE.md, docs/API.md, docs/DEVELOPMENT.md, docs/OPERATIONS.md, docs/TROUBLESHOOTING.md
- **datetime.utcnow()** → **datetime.now(timezone.utc)** — устранены все 14 deprecation warnings
- **Context files** — `.qwen/context/state_summary.md`, `active_plan.md` обновлены

### Removed

- **Dead agent system** — 11 файлов `agents/` (не интегрировано в app.py)
- **Duplicate prompts** — 7 файлов `prompts/` (дублировали `.qwen/agents/`)
- **Debug scripts** — `check_*.py`, `smoke_test.py`, `export_to_seed.py`, `wsgi_template.py`, `manage.py`
- **Archive** — `docs/history/`, `PATCH_REPORT_V2.3.3.json`
- **Data duplicates** — `data/countries_reference.py`, `data/managers_data.py`
- **.idea/** — удалены из git tracking

---

## [2.5.0] — 2026-04-11

### Admin Stabilization

### Added

- **Smoke-тесты** — 6 тестов login → dashboard → logout
- **Admin API тесты** — 28 тестов
- **Reactive Points Calculator** — серверная валидация в админке

### Fixed

- **BuildError: achievement.index_view** в dashboard
- **500** в `GET /admin/api/managers/{id}/achievements`
- **BuildError: admin_login** при logout
- **Debug-логи** — удалены 23 строки из production-кода
- **datetime.utcnow() deprecation** — исправлено в production

---

## [2.3.3] — 2026-04-09

### 🎉 Admin Panel Enhancement & Bug Fixes

Полное завершение разработки админки: flag preview, tandem warning, bulk operations, country flag source.

### Added

- **Flag Preview в Manager формах** — Country code и флаг автоматически заполняются при выборе страны
- **Tandem Warning** — Предупреждение при обнаружении запятой в имени менеджера (JS + server-side)
- **Bulk Operations UI** — Чекбоксы, modal форма, progress dialog, results summary для массового создания достижений
- **Country Flag Source поля** — `flag_source_type` (local/api), `flag_url` для поддержки FlagCDN API
- **Migration** — `1fdc901fa43e_add_country_flag_source_fields.py`
- **Permission check** — `has_permission('create')` в bulk-create endpoint для предотвращения privilege escalation
- **Rate limiting** — Максимум 100 менеджеров за одну bulk операцию

### Changed

- **CountryModelView** — Упрощены form_columns до ('code', 'name', 'flag_path') для устранения WTForms конфликта
- **Bulk-create N+1 queries** — Batch-load через `WHERE id IN(...)` — 100 queries → 2 queries (50x improvement)
- **Bulk-create icon_path** — Используется `ach_type.code.lower()` вместо hardcoded '/static/img/cups/top1.svg'
- **API-001 /admin/api/countries** — Возвращает `flag_display_url` вместо `flag_path` для корректной поддержки API-sourced флагов
- **Manager list checkbox ID extraction** — Улучшен regex с fallback chain: edit link → data attr → cell text

### Fixed

- **BUG-001** (Critical) — Country form TypeError: `BaseModelView.edit_view() got an unexpected keyword argument 'cls'`
- **BUG-002** — CountryModelView form_columns Select2 поля не определены корректно
- **BUG-003** — COUNTRY_AUTOFILL_JS ссылается на несуществующие элементы
- **BUG-004** — Manager list checkbox ID extraction unreliable
- **BUG-005** — Broken image icon при начальной загрузке manager edit/create
- **BUG-006** — CountryModelView form_args validators могут быть неполными
- **form_overrides conflict** — Удалён `form_overrides` вызывавший WTForms cls конфликт

### Security

- **Permission enforcement** — Bulk-create endpoint теперь проверяет `create` permission
- **Rate limiting** — Ограничение на количество менеджеров в bulk операции

---

## [2.4.0] — 2026-04-04

### 🎉 Reliable Deployment System

Полная переработка процесса деплоя: от ручного `git pull` до автоматизированного конвейера с бэкапами и откатом.

### Added

- **scripts/deploy.sh.template** — полноценный скрипт деплоя для сервера:
  - **Atomic Update**: `git reset --hard origin/main` вместо `checkout`.
  - **Auto Backup**: Бэкап БД с суффиксом `.pre-deploy` перед миграциями.
  - **Safe Migrations**: Явная передача `DATABASE_URL` из `.env` в Alembic.
  - **Health Check**: Валидация JSON от `/health` с ретраями.
  - **Auto Rollback**: При любой ошибке скрипт сам возвращает код и БД в предыдущее состояние.
- **rollback.yml** — ручной откат через GitHub Actions (Workflow Dispatch).
  - Восстановление кода и БД из последнего бэкапа.
- **Backup Retention**: Хранение последних 10 бэкапов.

### Fixed

- **BUG-5**: Деплой больше не использует закешированный локальный `main`.
- **BUG-7**: Деплой падает, если приложение в статусе `degraded` (например, отвалился Redis).
- **BUG-11**: Rollback теперь корректно восстанавливает схему БД из бэкапа.

### Changed

- **deploy.yml**: Стал "тонким" клиентом, вызывает `scripts/deploy.sh` на сервере.
- **CI/CD**: Тесты теперь проходят с Redis (Prod-Like) и без Rate Limits (скорость).

---

## [2.3.0] — 2026-04-04

### 🎉 Data Synchronization Layer

Полная переработка слоя работы с данными. Переход от хардкода к JSON-конфигурации и двусторонней синхронизации БД ↔ файлы.

### Added

- **JSON Seed/Export** — возможность выгружать данные из БД в файлы и наоборот.
  - `python seed_db.py --export` — экспорт текущих данных (Backup).
  - `python seed_db.py` — безопасный импорт (пропуск существующих).
  - `python seed_db.py --force` — полный сброс и импорт.
- **Centralized Static Paths** — `data/static_paths.py` заменяет разрозненные константы. Автоматическое определение путей к флагам/кубкам.
- **Schemas Validation** — `data/schemas.py` для проверки структуры JSON файлов перед импортом.
- **Seed Service & Export Service** — модульные сервисы для управления данными.
- **Разделение данных**:
  - `data/seed/` — исходные данные для развертывания.
  - `data/export/` — актуальные бэкапы из БД.

### Changed

- **seed_db.py** — полностью переписан. Теперь это тонкая обёртка над `SeedService`.
- **Архитектура данных** — удален `managers_data.py`. Данные хранятся в JSON.
- **Производительность** — устранена N+1 проблема при импорте достижений.

### Fixed

- **BUG-012** — Удален устаревший `managers_data.py`.
- **BUG-013** — Оптимизирован импорт достижений (один SQL запрос вместо N).
- **BUG-014** — Улучшен маппинг флагов (проверка наличия файлов на диске).

---

## [2.2.0] — 2026-04-04

### 🎉 Audit Log + Cache Control Release

Полная реализация аудита действий администратора, ручного управления кэшем и E2E тестирования.

### Added

- **Audit Log** — модель `AuditLog` для фиксации всех CRUD операций в админке
  - Поля: `user_id`, `action`, `target_model`, `target_id`, `changes`, `timestamp`
  - Индексы: `timestamp`, `(user_id, timestamp)`, `action`, `target_model`, `target_id`
- **audit_service.py** — сервис логирования с функциями:
  - `log_action()` — запись действий с диффами для UPDATE
  - `get_audit_logs()` — фильтрация по user/action/model с пагинацией
  - `cleanup_old_audit_logs()` — очистка записей старше 90 дней
  - `setup_audit_events()` — SQLAlchemy event listeners для автоматического аудита
- **Интеграция в SecureModelView** — перехват CREATE, UPDATE, DELETE
- **Логирование LOGIN** — фиксация успешных входов в админку
- **Flush Cache UI** — кнопка «Flush Cache» на главной странице админки
  - Endpoint: `POST /admin/flush-cache`
  - Логирование действия FLUSH_CACHE в AuditLog
- **Alembic миграция** — `1c8dd033101a_add_audit_log.py`
- **E2E тесты** — 15 тестов для полной проверки приложения:
  - Главная страница, health, metrics, админка, API, статика, кэш, audit log
- **Покрытие тестов ~87%** — 239 тестов (224 unit+integration + 15 E2E)

### Changed

- **`app.py`** — обёртка `with app.app_context()` для корректной инициализации Flask-Admin
- **`services/admin.py`** — исправлен `login_manager.login_view` → `'admin_login.index'`
- **`templates/admin/index.html`** — добавлена карточка управления кэшем
- **Интеграционные тесты** — переписаны на использование `SecureModelView` вместо прямой записи в БД

### Fixed

- **BUG-001-009** — исправлены 9 багов в тестах audit service
  - Mocking, ObjectDeletedError, race condition, serialization
- **BUG-010** — `login_manager.login_view` → `'admin_login.index'`
- **BUG-011** — `inaccessible_callback` → `'admin_login.index'`
- **Flask-Admin redirect** — корректный редирект на login page при доступе без авторизации

### Security

- **Audit Trail** — полная трассируемость действий администратора
- **CSRF защита** — сохранена для Flush Cache endpoint
- **Thread safety** — `_audit_lock` для конкурентных записей в AuditLog

---

## [2.0.0] — 2026-04-03

### 🎉 Major Release

Полный рефакторинг проекта с переходом на модульную архитектуру, добавлением аутентификации API, CSRF защиты и расширенного тестирования.

### Added

- **Аутентификация API** — API Keys с 3 уровнями доступа (read/write/admin)
- **Пагинация API** — `page`/`per_page` для endpoints `/api/managers` и `/api/achievements`
- **Rate Limiting** — 100 req/min на API ключ (Flask-Limiter)
- **CSRF защита** — Flask-WTF CSRF защита для админ-панели
- **Модель ApiKey** — хранение хешей ключей, scope, срок действия, отзыв
- **CRUD API-ключей** — управление ключами через админ-панель
- **Интеграционные тесты** — полный CRUD цикл API с auth, cache invalidation
- **Покрытие тестов 81%** — pytest-cov для измерения покрытия
- **Формула расчёта из БД** — использование таблиц `AchievementType` и `Season` вместо хардкода
- **Документация**:
  - `docs/API.md` v2.0 — auth, pagination, scopes, rate limiting
  - `docs/ADMIN.md` v2.0 — CSRF, API Keys management
  - `docs/MIGRATION_GUIDE.md` — пошаговый деплой на VPS
  - `CHANGELOG.md` — история изменений

### Changed

- **Структура проекта** — переход к слоистой архитектуре (blueprints/, services/, tests/)
- **Тесты** — перенос из `tests.py` в директорию `tests/` (193 теста)
- **Формула расчёта** — вынесена в БД (AchievementType.base_points, Season.multiplier)
- **API в production** — включено (`ENABLE_API=True`) с обязательной аутентификацией
- **README.md** — обновлена структура, команды, статус этапов, badges
- **`.env.example`** — добавлены `API_KEY_SECRET`, `WTF_CSRF_SECRET_KEY`, `ENABLE_API`
- **Админ-панель** — добавлена CSRF защита, управление API-ключами

### Fixed

- **Расхождение в тестах** — актуализировано количество (72 → 193)
- **Импорты в тестах** — добавлен `from typing import Any` (8 ошибок F821)
- **Уникальные ограничения** — добавлен UniqueConstraint для достижений
- **Инвалидация кэша** — API endpoints теперь корректно инвалидируют кэш

### Security

- **API Keys** — SHA-256 хеширование ключей перед хранением
- **CSRF токены** — защита админ-панели от CSRF атак
- **Rate limiting** — защита от brute-force и DDoS (100 req/min)
- **Пароли** — PBKDF2-SHA256 хеширование
- **Сессии** — безопасные cookie с `SECRET_KEY`

---

## [1.0.0] — 2026-03-29

### Initial Release

Базовая версия приложения с рейтингом лиги, админ-панелью и REST API.

### Added

- Рейтинг лиги с расчётом очков
- Админ-панель (Flask-Admin) для CRUD операций
- REST API (без аутентификации)
- Кэширование (Redis + SimpleCache fallback)
- Health check (`/health`) и Prometheus метрики (`/metrics`)
- Alembic миграции
- 72 unit + integration теста
- Документация (API, Redis, Deploy, Monitoring, Troubleshooting)
- CI/CD через GitHub Actions
- Поддержка Windows и Linux

---

## Legend

| Symbol     | Meaning                        |
| ---------- | ------------------------------ |
| Added      | Новые функции                  |
| Changed    | Изменения в существих функциях |
| Fixed      | Исправления багов              |
| Security   | Изменения безопасности         |
| Deprecated | Устаревшие функции             |
| Removed    | Удалённые функции              |
