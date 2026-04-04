# Changelog

Все значимые изменения проекта Shadow Hockey League v2.

Формат основан на [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
