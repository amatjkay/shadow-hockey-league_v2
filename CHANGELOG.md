# Changelog

Все значимые изменения проекта Shadow Hockey League v2.

Формат основан на [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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

| Symbol | Meaning |
|--------|---------|
| Added | Новые функции |
| Changed | Изменения в существих функциях |
| Fixed | Исправления багов |
| Security | Изменения безопасности |
| Deprecated | Устаревшие функции |
| Removed | Удалённые функции |
