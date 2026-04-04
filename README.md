# Shadow Hockey League v2

Веб-приложение на **Flask** с базой данных **SQLite**: таблица менеджеров (соло и тандемы) с кубками и **рейтинг по очкам** на одной странице.

**Production:** https://shadow-hockey-league.ru/ | **Health:** `/health` | **Metrics:** `/metrics`

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1+-green.svg)](https://flask.palletsprojects.com/)
[![Coverage](https://img.shields.io/badge/Coverage-81%25-yellowgreen.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#)

---

## 🚀 Быстрый старт

### Для Windows

#### Вариант 1: Использование .bat файлов (рекомендуется)

```cmd
REM 1. Установка и настройка
.\setup.bat

REM 2. Запуск сервера
.\run.bat
```

#### Вариант 2: Прямые команды PowerShell

```powershell
# 1. Установка зависимостей
pip install -r requirements.txt

# 2. Инициализация базы данных
python seed_db.py

# 3. Запуск сервера
python app.py
```

### Для Linux/Mac

```bash
# 1. Установка и настройка
make setup

# 2. Запуск сервера
make run
```

Приложение будет доступно по адресу: `http://127.0.0.1:5000/`

---

- Единая таблица **«Рейтинг лиги»** (колонки: **страна** · **Место** · **Очки** · **Участник** · **Кубки** · **Расчёт**). Детальный расчёт по наградам — в последней колонке, раскрывается по нажатию.
- Правила начисления очков — в блоке **«Как считаются очки»** (свернут по умолчанию).
- Для **топ-10** строк анимированный градиент на колонках **Место**, **Очки** и **Участник** синхронизирован (`background-attachment: fixed` и общий `@keyframes league-top10-sheen`).
- **Тандемы:** префикс `Tandem:` в интерфейсе не показывается (остаётся только состав, например `Vlad, whiplash 92`). Бейдж **«тандем»** выводится, если в **исходном** имени записи есть запятая (пара участников в данных).
- Старый URL `/rating` перенаправляет на главную с якорем `/#rating`.

## Расчёт очков

Логика в модуле `services/rating_service.py`: за каждую награду берётся **база** (лига и тип кубка) × **множитель сезона**, результат округляется, затем суммируется по строке участника.

### Множители сезонов

Текущий сезон — базовый (×1.00), старые сезоны имеют дисконт:

| Сезон  | Множитель       |
| ------ | --------------- |
| s24/25 | ×1.00 (базовый) |
| s23/24 | ×0.95 (−5%)     |
| s22/23 | ×0.90 (−10%)    |
| s21/22 | ×0.85 (−15%)    |

**Логика:** последние достижения ценнее старых — это мотивирует играть сейчас.

### Базовые очки

| Достижение   | Лига 1 | Лига 2 |
| ------------ | ------ | ------ |
| TOP1         | 800    | 300    |
| TOP2         | 550    | 200    |
| TOP3         | 450    | 100    |
| Best regular | 50     | 40     |
| Round 3      | 30     | 20     |
| Round 1      | 10     | 5      |
| Toxic        | 0      | 0      |

**Логика:** увеличен разрыв между TOP1 и остальными наградами, чтобы победа в Лиге 1 была значимее.

## Структура лиг

- **Лига 1** — высшая лига
- **Лига 2** — вторая лига (с сезона 25/26 разделена на **Лигу 2.1** и **Лигу 2.2**)
- **Сезон 24/25** — единая Лига 2 (без разделения)
- **Сезон 25/26** — Лига 2 разделена на две подлиги для розыгрыша повышения в Лигу 1

## Структура проекта

```
shadow-hockey-league_v2/
├── app.py                      # Application Factory (инициализация приложения)
├── models.py                   # SQLAlchemy модели (AdminUser, Country, Manager, Achievement, ApiKey)
├── config.py                   # Конфигурация (Development/Production/Testing)
├── wsgi.py                     # WSGI entry point для деплоя
├── blueprints/                 # Flask blueprints
│   ├── main.py                 #   Главная страница, leaderboard
│   └── health.py               #   Health check endpoint
├── services/                   # Бизнес-логика
│   ├── rating_service.py       #   Расчёт рейтинга (формула из БД)
│   ├── cache_service.py        #   Кэширование и инвалидация
│   ├── api.py                  #   REST API (auth + pagination)
│   ├── admin.py                #   Flask-Admin (CRUD + CSRF)
│   ├── metrics_service.py      #   Prometheus метрики
│   └── validation_service.py   #   Валидация данных
├── data/                       # Справочные данные (countries, managers)
├── templates/                  # Jinja2 шаблоны
├── static/                     # CSS, JS, изображения (флаги)
├── migrations/                 # Alembic миграции
├── tests/                      # Pytest тесты
│   ├── conftest.py             #   Fixtures
│   ├── test_*.py               #   Unit тесты
│   └── integration/            #   Интеграционные тесты
├── docs/                       # Документация
├── context/                    # Контекст модульной системы
├── prompts/                    # Промпты ролей AI
├── scripts/                    # Утилиты (create_admin, validate_db)
├── .env.example                # Пример переменных окружения
├── requirements.txt            # Python зависимости
├── Makefile                    # Команды для разработки
└── alembic.ini                 # Alembic конфигурация
```

## 🔧 Команды Makefile

| Команда         | Описание                                    |
| --------------- | ------------------------------------------- |
| `make setup`    | Установка зависимостей + инициализация БД   |
| `make install`  | Установка зависимостей из requirements.txt  |
| `make init-db`  | Инициализация БД (создание таблиц + seed)   |
| `make seed-db`  | Наполнение БД данными (без создания таблиц) |
| `make validate` | Проверка состояния БД                       |
| `make run`      | Запуск сервера разработки                   |
| `make test`     | Запуск тестов                               |
| `make lint`     | Проверка кода через flake8                  |
| `make format`   | Форматирование кода (black + isort)         |
| `make clean`    | Очистка временных файлов                    |
| `make clean-db` | Очистка БД (удаление всех данных)           |

## 🧪 Тесты

Проект содержит **тесты с покрытием 81%**, покрывающих логику рейтинга, API, маршруты, инвалидацию кэша, CSRF и аутентификацию API.

```bash
# Используя Makefile
make test

# С покрытием
pytest --cov=. --cov-report=term-missing

# Или вручную
python -m unittest discover -v
```

**Покрытие:**

- **Unit тесты:** rating service, validation, cache service, API auth, pagination
- **Integration тесты:** routes, API CRUD, database constraints, cache invalidation
- **Admin тесты:** CSRF защита, admin auth, CRUD операции
- **API тесты:** API Keys auth, rate limiting, scopes, pagination

> **Примечание:** Ранее указывалось 72 теста — актуальное количество может отличаться из-за рефакторинга. Используйте `pytest --cov` для актуальной метрики.

## 🛠 Админ-панель

Админ-панель для управления менеджерами, странами и достижениями.

**URL:** `/admin/`

### Первый вход

```bash
# Создать первого админа
python scripts/create_admin.py
```

### Возможности

- ✅ CRUD для стран, менеджеров, достижений
- ✅ Аутентификация (логин/пароль)
- ✅ Автоматическая инвалидация кэша
- ✅ Поиск и фильтры

**Подробная документация:** [`docs/ADMIN.md`](docs/ADMIN.md)

## 📊 Мониторинг

Приложение предоставляет эндпоинты для мониторинга:

### Health Check (`/health`)

```bash
curl https://shadow-hockey-league.ru/health
```

**Пример ответа:**

```json
{
  "status": "healthy",
  "managers_count": 50,
  "achievements_count": 200,
  "countries_count": 8,
  "response_time_ms": 15,
  "redis_status": "connected",
  "cache_status": "working",
  "database_status": "connected"
}
```

### Prometheus Metrics (`/metrics`)

Метрики в формате Prometheus для сбора статистики:

- `http_requests_total` — всего запросов
- `http_request_duration_seconds` — время ответа

**Подробная документация:** [`docs/MONITORING.md`](docs/MONITORING.md)

## 🔐 Переменные окружения

Проект использует файл `.env` для конфигурации:

| Переменная            | Описание                              | По умолчанию        |
| --------------------- | ------------------------------------- | ------------------- |
| `FLASK_ENV`           | Режим работы (development/production) | `development`       |
| `DATABASE_URL`        | URL базы данных                       | `sqlite:///dev.db`  |
| `SECRET_KEY`          | Ключ сессий                           | Автогенерация (dev) |
| `LOG_LEVEL`           | Уровень логирования                   | `INFO`              |
| `ENABLE_API`          | Включение REST API                    | `True`              |
| `API_KEY_SECRET`      | Секрет для генерации API ключей       | —                   |
| `WTF_CSRF_SECRET_KEY` | CSRF защита админ-панели              | —                   |
| `REDIS_URL`           | Redis URL для кэширования             | `redis://localhost` |

**Важно:** В production режиме `ENABLE_API=True` требует аутентификации через API Keys.

## 🛠 Устранение неполадок

### Ошибка "An error occurred"

```bash
# Переинициализируйте БД
python seed_db.py
```

### Ошибка "no such table"

```bash
# Пересоздайте БД
del dev.db
python seed_db.py
```

### Проблемы с путями к БД

Убедитесь, что `DATABASE_URL` в `.env` и `sqlalchemy.url` в `alembic.ini` указывают на один файл.

## 📚 Документация

| Файл                      | Описание                                            |
| ------------------------- | --------------------------------------------------- |
| `README.md`               | Этот файл — быстрый старт                           |
| `docs/API.md`             | REST API: auth, pagination, scopes, rate limiting   |
| `docs/ADMIN.md`           | Админ-панель: CSRF, API Keys management             |
| `docs/MIGRATION_GUIDE.md` | Пошаговый деплой на VPS (Ubuntu + Nginx + Gunicorn) |
| `docs/REDIS.md`           | Redis: настройка, запуск, управление кэшем          |
| `docs/MONITORING.md`      | Health check, Prometheus метрики                    |
| `docs/TROUBLESHOOTING.md` | Руководство по устранению неполадок                 |
| `CHANGELOG.md`            | История изменений версий                            |

## 📊 Статус проекта

| Этап | Название                              | Статус      |
| ---- | ------------------------------------- | ----------- |
| 0    | Базовая архитектура                   | ✅          |
| 1    | Кэширование (Redis + SimpleCache)     | ✅          |
| 2    | Метрики (Prometheus)                  | ✅          |
| 3    | Админ-панель + CSRF защита            | ✅          |
| 4    | Рефакторинг формулы (из БД)           | ✅          |
| 5    | API auth + pagination + rate limiting | ✅          |
| 6    | Интеграционные тесты (81% покрытие)   | ✅          |
| 7    | Документация и деплой                 | 🔴 В работе |

### Что реализовано

- ✅ Покрытие тестами **81%** (`pytest --cov`)
- ✅ Код отформатирован (`black`, `isort`, `flake8`)
- ✅ REST API с аутентификацией (API Keys, 3 scope)
- ✅ Пагинация API (`page`/`per_page`, max 100)
- ✅ Rate limiting (100 req/min на ключ)
- ✅ CSRF защита админ-панели
- ✅ Кэширование Redis с fallback на SimpleCache
- ✅ Автоматическая инвалидация кэша (Admin + API)
- ✅ UniqueConstraint на достижениях (нет дубликатов)
- ✅ Alembic миграции
- ✅ Формула расчёта очков из БД (AchievementType + Season)

---

## 🌐 Деплой

### Production сервер

Проект развёрнут на **VPS (Ubuntu 22.04)**:  
**https://shadow-hockey-league.ru/**

| Компонент  | Версия/Значение                |
| ---------- | ------------------------------ |
| ОС         | Ubuntu 22.04 LTS               |
| Веб-сервер | Nginx                          |
| WSGI       | Gunicorn (4 workers)           |
| Python     | 3.10                           |
| БД         | SQLite                         |
| SSL        | Let's Encrypt (автообновление) |
| Домен      | shadow-hockey-league.ru        |

### 📦 Автоматические бэкапы

- **Периодичность:** Ежедневно в 3:00 UTC
- **Хранение:** 7 дней
- **Очистка:** Автоматическая (старше 7 дней)
- **Формат:** `dev.db-YYYYMMDD-HHMMSS.gz`
- **Расположение:** `/backup/`

### 🔄 CI/CD (GitHub Actions)

Настроен автоматический деплой при пуше в ветку `main`:

```bash
git push origin main
```

**Workflow:** `.github/workflows/deploy.yml`

**Что делает:**

1. Подключается по SSH к серверу
2. Выполняет `git pull`
3. Обновляет зависимости
4. Перезапускает приложение

### 📝 Ручное обновление на сервере

```bash
cd /home/shleague/shadow-hockey-league_v2
source venv/bin/activate
git pull origin main
pip install -r requirements.txt --quiet
systemctl restart shadow-hockey-league
```

📖 **Подробная инструкция:** [`docs/VPS_DEPLOY.md`](docs/VPS_DEPLOY.md)

---

### PythonAnywhere (архив)

Старая версия на PythonAnywhere доступна по адресу:  
**https://amatjkay.pythonanywhere.com/**

📖 **Инструкция по деплою на PythonAnywhere:** [`docs/DEPLOY.md`](docs/DEPLOY.md)
