# Shadow Hockey League v2

Веб-приложение на **Flask** для управления хоккейной лигой: менеджеры (соло и тандемы), достижения, кубки и **рейтинг по очкам** на одной странице.

**Production:** https://shadow-hockey-league.ru/ | **Health:** `/health` | **Metrics:** `/metrics` | **Admin:** `/admin/`

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1+-green.svg)](https://flask.palletsprojects.com/)
[![Coverage](https://img.shields.io/badge/Coverage-87%25-yellowgreen.svg)](#)
[![Tests](https://img.shields.io/badge/Tests-472%20passed-brightgreen.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#)

---

## 🚀 Быстрый старт

### Windows

```cmd
.\setup.bat    # Установка и настройка
.\run.bat      # Запуск сервера
```

### Linux/Mac

```bash
make setup     # git submodules + установка зависимостей + инициализация БД
make run       # Запуск сервера разработки
```

`make setup` ставит цель `submodules-init` первой, чтобы инициализировать
git-submodule `skills/superpowers` (см. [AGENTS.md § 7](AGENTS.md#7-superpowers-skill-bridge-since-2026-05-04)).
Без этого симлинки `.agents/skills/superpowers` и `.kilo/skills/superpowers`
указывают в пустой каталог — superpowers-скиллы не загрузятся.

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

Источник истины — `data/seed/achievements.json` + таблица `achievement_types` в `dev.db`.

| Код    | Достижение           | Лига 1 | Лига 2 |
| ------ | -------------------- | ------ | ------ |
| `TOP1` | Чемпион              | 800    | 400    |
| `TOP2` | Финалист             | 400    | 200    |
| `TOP3` | Бронзовый призёр     | 200    | 100    |
| `BEST` | Лучший в регулярке   | 200    | 100    |
| `R3`   | Полуфинал (1/2)      | 100    | 50     |
| `R1`   | Четвертьфинал (1/4)  | 50     | 25     |

### Множители сезонов

| Сезон | Множитель       |
| ----- | --------------- |
| 25/26 | ×1.00 (базовый) |
| 24/25 | ×0.80           |
| 23/24 | ×0.50           |
| 22/23 | ×0.30           |
| 21/22 | ×0.20           |

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
│   └── admin_api/              #   Admin API package (post-TIK-42)
│       ├── __init__.py         #     admin_api_bp blueprint
│       ├── _helpers.py
│       ├── lookups.py
│       └── achievements.py
├── services/                   # Бизнес-логика
│   ├── rating_service.py       #   Расчёт рейтинга
│   ├── recalc_service.py       #   Пересчёт рейтинга (admin)
│   ├── scoring_service.py      #   base_points × multiplier (TIK-58: subleague-aware)
│   ├── cache_service.py        #   Кэширование и инвалидация
│   ├── extensions.py           #   Flask-Limiter и др. shared extensions
│   ├── metrics_service.py      #   Prometheus метрики
│   ├── api/                    #   REST API package (post-TIK-42)
│   │   ├── __init__.py         #     api blueprint
│   │   ├── _helpers.py
│   │   ├── countries.py
│   │   ├── managers.py
│   │   └── achievements.py
│   ├── admin/                  #   Flask-Admin package (post-TIK-42)
│   │   ├── __init__.py         #     init_admin()
│   │   ├── base.py             #     SHLModelView
│   │   ├── views.py            #     ModelView'ы
│   │   └── _rate_limit.py
│   ├── api_auth.py             #   API Key auth
│   ├── audit_service.py        #   Audit Log
│   ├── validation_service.py   #   Валидация данных
│   ├── seed_service.py         #   JSON Seed импорт
│   ├── export_service.py       #   Экспорт из БД
│   └── _types.py               #   SessionLike + mypy shim (TIK-53)
├── data/                       # Справочные данные
│   ├── seed/                   #   Исходные данные (JSON)
│   ├── export/                 #   Экспорт из БД (JSON)
│   └── schemas.py              #   Валидация JSON схем
├── tests/                      # Pytest тесты (472 теста, ≥ 87% gate)
│   ├── integration/            #   Интеграционные тесты
│   └── e2e/                    #   Playwright smoke (запуск вручную, см. README ниже)
├── docs/                       # Документация
├── scripts/                    # Утилиты (create_admin, check_*, install_superpowers)
├── .agents/                    # Sub-agent роли, скиллы, промпты, workflows (Devin/Antigravity)
│   └── skills/superpowers/     #   → ../../skills/superpowers/skills (symlink)
├── .kilo/                      # Kilocode orchestrator + платформенные скиллы
│   └── skills/superpowers/     #   → ../../skills/superpowers/skills (symlink)
├── skills/superpowers/         # obra/superpowers submodule (см. AGENTS.md § 7)
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
| `make test`   | Запуск тестов (472 unit/integration)      |
| `make lint`   | Проверка кода (flake8)                    |
| `make format` | Форматирование (black + isort)            |
| `make clean`  | Очистка временных файлов                  |

---

## 🧪 Тесты

**472 unit/integration теста** (≥ 87% покрытие — CI gate с TIK-54) + **42-сценарный Playwright smoke**:

- **Unit:** rating service, validation, cache, API auth, models
- **Integration:** routes, API CRUD, database constraints, cache invalidation
- **Admin:** CSRF, auth, CRUD, smoke-тесты
- **E2E (manual):** `tests/e2e/test_smoke.py` — публичные страницы, REST API, Flask-Admin views, console error budget. Не подхватывается `pytest` (требует живой dev-сервер).

```bash
make test
# или
pytest --ignore=tests/e2e --cov=. --cov-report=term-missing

# E2E (требует запущенный сервер):
BASE_URL=http://127.0.0.1:5000 \
E2E_ADMIN_USER=e2e_admin E2E_ADMIN_PASS=... \
./venv/bin/python tests/e2e/test_smoke.py
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
| `DATABASE_URL`        | URL базы данных       | `sqlite:///dev.db`  |
| `SECRET_KEY`          | Ключ сессий           | Автогенерация       |
| `ENABLE_API`          | Включение REST API    | `True`              |
| `API_KEY_SECRET`      | Секрет для API ключей | —                   |
| `WTF_CSRF_SECRET_KEY` | CSRF защита           | —                   |
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
| [`docs/SUPERPOWERS.md`](docs/SUPERPOWERS.md)         | obra/superpowers skill bridge  |
| [`CHANGELOG.md`](CHANGELOG.md)                       | История изменений              |

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
