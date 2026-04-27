# Shadow Hockey League v2

Веб-приложение на **Flask** для управления хоккейной лигой: менеджеры (соло и тандемы), достижения, кубки и **рейтинг по очкам** на одной странице.

**Production:** https://shadow-hockey-league.ru/ | **Health:** `/health` | **Metrics:** `/metrics` | **Admin:** `/admin/`

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1+-green.svg)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/Tests-383%20passed-brightgreen.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#)

> Точное число тестов и фактический процент покрытия — выводятся командами `make test` и `make coverage`. Бейджи без CI-источника удалены: считайте только результаты `pytest`.

---

## 🚀 Быстрый старт

### Windows

```cmd
.\setup.bat    # Установка и настройка
.\run.bat      # Запуск сервера
```

### Linux/Mac

```bash
make setup     # Установка зависимостей + инициализация БД
make run       # Запуск сервера разработки
```

Приложение: `http://127.0.0.1:5000/`

---

## 📋 Возможности

- **Единая таблица «Рейтинг лиги»** — сортировка по очкам, детализация расчёта по нажатию
- **Тандемы** — поддержка парных участников с автоматическим бейджем
- **Формула из БД** — базовые очки × множитель сезона (AchievementType + Season)
- **Админ-панель** — CRUD для стран, менеджеров, достижений, типов достижений, сезонов, лиг
- **REST API** — API Key auth (read/write/admin scopes), пагинация, rate limiting
- **Кэширование** — Redis с SimpleCache fallback, автоматическая инвалидация
- **Audit Log** — фиксация всех действий администраторов
- **Мониторинг** — `/health` + `/metrics` (Prometheus)
- **CI/CD** — GitHub Actions с SSH-деплоем, автобэкапом и откатом

---

## 🏆 Расчёт очков

```
points = base_points(league, achievement_type) × season_multiplier
```

### Базовые очки

| Достижение   | Лига 1 | Лига 2 |
| ------------ | ------ | ------ |
| TOP1         | 800    | 300    |
| TOP2         | 550    | 200    |
| TOP3         | 450    | 100    |
| Best regular | 50     | 40     |
| Round 3      | 30     | 20     |
| Round 1      | 10     | 5      |

### Множители сезонов

| Сезон | Множитель       |
| ----- | --------------- |
| 25/26 | ×1.00 (текущий, базовый) |
| 24/25 | ×0.95 (−5%)     |
| 23/24 | ×0.90 (−10%)    |
| 22/23 | ×0.85 (−15%)    |
| 21/22 | ×0.80 (−20%)    |

Источник истины — таблица `seasons` в БД. Хардкод в `services/rating_service.SEASON_MULTIPLIER`
используется только как fallback при пустой таблице.

---

## 📁 Структура проекта

```
shadow-hockey-league_v2/
├── app.py                      # Application Factory
├── models.py                   # SQLAlchemy модели
├── config.py                   # Dev/Prod/Test конфиг
├── wsgi.py                     # WSGI entry point
├── blueprints/                 # Flask blueprints
│   ├── main.py                 #   Главная страница, leaderboard
│   ├── health.py               #   Health check
│   └── admin_api.py            #   Admin API endpoints
├── services/                   # Бизнес-логика
│   ├── rating_service.py       #   Расчёт рейтинга
│   ├── cache_service.py        #   Кэширование и инвалидация
│   ├── api.py                  #   REST API
│   ├── admin.py                #   Flask-Admin
│   ├── api_auth.py             #   API Key auth
│   ├── audit_service.py        #   Audit Log
│   ├── validation_service.py   #   Валидация данных
│   ├── seed_service.py         #   JSON Seed импорт
│   └── export_service.py       #   Экспорт из БД
├── data/                       # Справочные данные
│   ├── seed/                   #   Исходные данные (JSON)
│   ├── export/                 #   Экспорт из БД (JSON)
│   └── schemas.py              #   Валидация JSON схем
├── tests/                      # Pytest тесты
│   ├── integration/            #   Интеграционные тесты
│   └── e2e/                    #   E2E тесты
├── docs/                       # Memory Bank: activeContext, techContext,
│                               # progress, decisionLog, projectbrief, ADR-документация
├── scripts/                    # Утилиты (create_admin, check_*, benchmark, audit_data)
├── .agents/                    # AI Agent конфигурация
│   ├── agents/                 #   Роли: architect, coder, reviewer
│   └── skills/                 #   Воспроизводимые процедуры (db-migration, ...)
├── .windsurf/                  # Конфиг MCP-клиента (template; локальный — игнорируется)
├── AGENTS.md                   # Конституция для AI-агентов (memory bank, MCP-правила)
├── PROJECT_KNOWLEDGE.md        # База знаний (бизнес-правила, архитектура)
├── .antigravityrules           # Базовые правила кодирования и стека
├── requirements.txt            # Python зависимости
├── Makefile                    # Команды разработки
└── alembic.ini                 # Alembic миграции
```

---

## 🔧 Команды Makefile

| Команда       | Описание                                  |
| ------------- | ----------------------------------------- |
| `make setup`  | Установка зависимостей + инициализация БД |
| `make run`    | Запуск сервера разработки                 |
| `make test`   | Запуск тестов (383 теста, `pytest -n auto`)   |
| `make coverage` | Тесты + отчёт покрытия (`--cov`)        |
| `make lint`   | Проверка кода (flake8)                    |
| `make format` | Форматирование (black + isort)            |
| `make clean`  | Очистка временных файлов                  |

---

## 🧪 Тесты

**383 теста.** Цель покрытия — `≥ 87%` (`AGENTS.md §5`); фактическое фиксируйте прогоном `make coverage` (в том числе в CI — `.github/workflows/deploy.yml`).

- **Unit:** rating service, validation, cache, API auth, models
- **Integration:** routes, API CRUD, database constraints, cache invalidation
- **Admin:** CSRF, auth, CRUD, smoke-тесты
- **E2E:** полный цикл приложения

```bash
make test
# или
pytest --cov=. --cov-report=term-missing
```

---

## 🛠 Админ-панель

**URL:** `/admin/`

### Первый вход

```bash
python scripts/create_admin.py
```

### Возможности

- CRUD для стран, менеджеров, достижений, типов достижений, сезонов, лиг
- Реактивный калькулятор очков
- Bulk-операции для массового создания достижений
- Audit Log всех действий
- Автоматическая инвалидация кэша

---

## 📡 REST API

**Base URL:** `/api/`

| Endpoint                | Auth | Scope       | Описание               |
| ----------------------- | ---- | ----------- | ---------------------- |
| `GET /api/countries`    | ❌   | —           | Все страны             |
| `GET /api/managers`     | ✅   | read        | Менеджеры (пагинация)  |
| `GET /api/achievements` | ✅   | read        | Достижения (пагинация) |
| `POST/PUT/DELETE`       | ✅   | write/admin | CRUD операции          |

API Key передаётся в заголовке `X-API-Key`. Scopes: `read`, `write`, `admin`.

📖 **Полная документация:** [`docs/API.md`](docs/API.md)

---

## 📊 Мониторинг

### Health Check (`/health`)

```json
{
  "status": "healthy",
  "managers_count": 50,
  "redis_status": "connected",
  "database_status": "connected"
}
```

### Prometheus Metrics (`/metrics`)

`http_requests_total`, `http_request_duration_seconds`

---

## 🔐 Переменные окружения

| Переменная            | Описание              | По умолчанию        |
| --------------------- | --------------------- | ------------------- |
| `FLASK_ENV`           | Режим работы          | `development`       |
| `DATABASE_URL`        | URL базы данных       | абсолютный путь к `./dev.db` (`config.py`) |
| `SECRET_KEY`          | Ключ сессий           | dev fallback (обязателен в prod) |
| `WTF_CSRF_SECRET_KEY` | CSRF защита           | dev fallback (обязателен в prod) |
| `ENABLE_API`          | Включение REST API    | `True`              |
| `API_KEY_SECRET`      | Секрет для API ключей | dev fallback (обязателен в prod) |
| `REDIS_URL`           | Redis URL             | `redis://localhost` |

---

## 📚 Документация

| Файл                                                 | Описание                       |
| ---------------------------------------------------- | ------------------------------ |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)       | Архитектура системы            |
| [`docs/API.md`](docs/API.md)                         | REST API документация          |
| [`docs/MIGRATIONS.md`](docs/MIGRATIONS.md)           | Заметки по изменениям схемы БД |
| [`docs/ADMIN_RECALC.md`](docs/ADMIN_RECALC.md)       | Админка и логика перерасчета   |
| [`docs/AI_WORKFLOW.md`](docs/AI_WORKFLOW.md)         | Постановка задач для ИИ        |
| [`docs/GITHUB_CLI.md`](docs/GITHUB_CLI.md)           | Работа с GitHub через CLI      |
| [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) | Устранение неполадок           |
| [`CHANGELOG.md`](CHANGELOG.md)                       | История изменений              |

---

## 🤖 AI-агенты и MCP

Проект использует протокол **Memory Bank** и набор MCP-серверов для работы AI-агентов.
Источники истины:

- [`AGENTS.md`](AGENTS.md) — конституция агентов, правила MCP, разделение ролей.
- [`.antigravityrules`](.antigravityrules) — стандарты кода, тестов, бизнес-логики.
- [`.agents/agents/`](.agents/agents/) — описания ролей `architect`, `coder`, `reviewer`.
- [`.agents/skills/`](.agents/skills/) — воспроизводимые процедуры (db-migration, feature-research, linear-sync).
- [`docs/activeContext.md`](docs/activeContext.md), [`docs/techContext.md`](docs/techContext.md), [`docs/progress.md`](docs/progress.md), [`docs/decisionLog.md`](docs/decisionLog.md) — Memory Bank.

### MCP setup (Windsurf / Codeium)

Шаблон конфига: [`.windsurf/mcp_config.example.json`](.windsurf/mcp_config.example.json).
Локальный конфиг (`.windsurf/mcp_config.json` и `~/.codeium/windsurf/mcp_config.json`)
не коммитится — он содержит токены.

```bash
# 1. Скопировать шаблон в пользовательский конфиг Windsurf:
mkdir -p ~/.codeium/windsurf
cp .windsurf/mcp_config.example.json ~/.codeium/windsurf/mcp_config.json

# 2. Заменить <PROJECT_ROOT> на абсолютный путь к репозиторию
#    и проставить переменные окружения:
#      GITHUB_PERSONAL_ACCESS_TOKEN, CONTEXT7_API_KEY, LINEAR_API_KEY, ...

# 3. Перезапустить Windsurf, проверить, что серверы поднялись.
```

> ⚠️ Серверы запускаются через `npx`/`uvx`. **Закоммиченных** node_modules в репо нет:
> каталог `mcp-servers/` (если присутствует локально) находится в `.gitignore`.
> `notebooklm` в шаблоне помечен `disabled: true` — официального MCP-сервера нет,
> подключайте только если есть проверенный community-пакет.

---

## 📊 Статус проекта

| Этап | Название                          | Статус | Версия |
| ---- | --------------------------------- | ------ | ------ |
| 0    | Базовая архитектура               | ✅     | v2.0.0 |
| 1    | Кэширование (Redis + SimpleCache) | ✅     | v2.1.0 |
| 2    | Метрики (Prometheus)              | ✅     | v2.1.0 |
| 3    | Админ-панель + CSRF               | ✅     | v2.2.0 |
| 4    | Формула рейтинга из БД            | ✅     | v2.3.0 |
| 5    | REST API с API Key auth           | ✅     | v2.0.0 |
| 6    | Тестовый контур                   | ✅     | v2.2.0 |
| 7    | Деплой на VPS + CI/CD             | ✅     | v2.4.0 |
| 8    | Data sync (seed/export)           | ✅     | v2.3.0 |
| 9    | Надёжный деплой (backup/rollback) | ✅     | v2.4.0 |
| 10   | Расширение админки                | ✅     | v2.5.0 |
| 11   | Стабилизация админки              | ✅     | v2.5.0 |
| 12   | AI Policy Stabilization           | ✅     | v2.6.0 |

---

## 🌐 Деплой

### Production

**URL:** https://shadow-hockey-league.ru/

| Компонент  | Значение                         |
| ---------- | -------------------------------- |
| ОС         | Ubuntu 22.04 LTS                 |
| Веб-сервер | Nginx + SSL (Let's Encrypt)      |
| WSGI       | Gunicorn (4 workers)             |
| Python     | 3.10+                            |
| БД         | SQLite + Alembic                 |
| Кэш        | Redis (localhost:6379)           |
| CI/CD      | GitHub Actions → SSH deploy      |
| Бэкапы     | Ежедневно 03:00 UTC + pre-deploy |

---

## 🛠 Устранение неполадок

| Проблема          | Решение                                                             |
| ----------------- | ------------------------------------------------------------------- |
| `no such table`   | `alembic upgrade head`                                              |
| Health `degraded` | Проверить Redis: `sudo systemctl restart redis-server`              |
| 502 Bad Gateway   | `systemctl restart shadow-hockey-league && systemctl restart nginx` |

📖 **Полный гайд:** [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)
