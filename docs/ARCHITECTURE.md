# 🏛️ Архитектура системы — Shadow Hockey League v2

**Версия:** 2.6.0
**Дата:** 13 апреля 2026 г.
**Статус:** ✅ Production

---

## 🎯 Бизнес-цели

- **BG-01**: Централизованное управление лигами, сезонами и достижениями
- **BG-02**: Безопасная админ-панель с RBAC и audit log
- **BG-03**: Мониторинг health/metrics для production
- **BG-04**: Автоматизация тестов критических путей (296 тестов, ~87%)

---

## 🏗️ Архитектурная схема

```
┌─────────────────┐
│     Client      │
│   (Web Browser) │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────────────────────┐
│   Nginx (Reverse Proxy + SSL)   │
│   - Port 443 (HTTPS)            │
│   - Port 80 (HTTP → HTTPS)      │
│   - Static files (/static)      │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│   Gunicorn (WSGI Server)        │
│   - 4 workers                   │
│   - Port 8000 (internal)        │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│   Flask Application             │
│   - Application Factory pattern │
│   - Blueprints (main, health,   │
│     admin_api)                  │
│   - Services (business logic)   │
└───┬─────────┬─────────┬─────────┘
    │         │         │
    ▼         ▼         ▼
┌───────┐ ┌──────┐ ┌────────┐
│SQLite │ │Redis │ │Promethe│
│  DB   │ │Cache │ │  us    │
└───────┘ └──────┘ └────────┘
```

---

## 📦 Технологический стек

| Уровень | Технология | Назначение |
|---------|-----------|------------|
| **Backend** | Python 3.10+, Flask 3.1+ | Web-фреймворк |
| **ORM** | SQLAlchemy 2.0+, Alembic | БД и миграции |
| **Caching** | Redis 6.0+ | Кэширование |
| **Admin** | Flask-Admin 2.0+ | Панель управления |
| **Auth** | Flask-Login, Flask-WTF CSRF | Аутентификация |
| **Rate Limit** | Flask-Limiter | Защита API |
| **Metrics** | Prometheus Flask | Мониторинг |
| **Infrastructure** | Nginx, Gunicorn, Ubuntu 22.04 | Хостинг |

---

## 📁 Структура проекта

```
shadow-hockey-league_v2/
├── app.py                      # Application Factory
├── models.py                   # SQLAlchemy модели
├── config.py                   # Dev/Prod/Test конфиг
├── wsgi.py                     # WSGI entry point
├── blueprints/                 # Flask blueprints
│   ├── main.py                 #   Главная страница
│   ├── health.py               #   Health check
│   └── admin_api.py            #   Admin API
├── services/                   # Бизнес-логика
│   ├── rating_service.py       #   Расчёт рейтинга
│   ├── cache_service.py        #   Кэширование
│   ├── api.py                  #   REST API
│   ├── admin.py                #   Flask-Admin
│   ├── api_auth.py             #   API Key auth
│   ├── audit_service.py        #   Audit Log
│   ├── validation_service.py   #   Валидация
│   ├── seed_service.py         #   JSON Seed
│   └── export_service.py       #   Экспорт
├── data/                       # Справочные данные
│   ├── seed/                   #   Исходные данные
│   ├── export/                 #   Экспорт из БД
│   └── schemas.py              #   Валидация JSON
├── tests/                      # 296 тестов (~87%)
│   ├── integration/            #   Интеграционные
│   └── e2e/                    #   E2E
├── docs/                       # Документация
├── scripts/                    # Утилиты
├── .qwen/                      # AI Agent config
├── requirements.txt
├── Makefile
└── alembic.ini
```

---

## 🗃️ Модель данных

### Основные таблицы

| Таблица | Описание |
|---------|----------|
| `countries` | Справочник стран (code, name, flag_path) |
| `leagues` | Лиги (1, 2.1, 2.2) |
| `seasons` | Сезоны с множителями |
| `achievement_types` | Типы достижений (TOP1, TOP2, ...) с базовыми очками |
| `managers` | Участники лиги (соло + тандемы) |
| `achievements` | Достижения менеджеров |
| `admin_users` | Пользователи админки (Flask-Login) |
| `api_keys` | API ключи (SHA-256 хеш, scopes) |
| `audit_logs` | Лог действий администраторов |

### Индексы

- `achievements(manager_id, league, season, achievement_type)` — UNIQUE
- `audit_logs(timestamp)`, `audit_logs(user_id, timestamp)` — для быстрого поиска
- `managers(country_id)` — FK индекс

---

## 🔌 API Архитетура

**Base URL:** `/api/`

**Authentication:** API Key (`X-API-Key` header) с scopes: `read`, `write`, `admin`

| Endpoint | Auth | Описание |
|----------|------|----------|
| `GET /api/countries` | ❌ | Все страны |
| `GET /api/managers` | ✅ | Менеджеры (пагинация) |
| `GET /api/achievements` | ✅ | Достижения (пагинация) |
| `POST/PUT/DELETE` | ✅ | CRUD операции |

**Features:** Pagination, Rate limiting (100 req/min), Cache invalidation, Audit logging

📖 **Полная документация:** [`API.md`](./API.md)

---

## 💾 Кэширование

**Стратегия:** Redis → SimpleCache fallback

**TTL:** 5 минут (по умолчанию)

**Инвалидация:**
- CREATE/UPDATE/DELETE в админке → leaderboard cache
- API мутации → leaderboard cache
- Flush Cache через UI → полная очистка

---

## 🔒 Безопасность

| Механизм | Реализация |
|----------|-----------|
| **Admin Auth** | Flask-Login (session-based) |
| **API Auth** | API Key (SHA-256 hash в БД) |
| **CSRF** | Flask-WTF для всех форм |
| **Rate Limiting** | 100 req/min на API ключ |
| **Пароли** | PBKDF2-SHA256 хеш |
| **SSL** | Let's Encrypt (автообновление) |
| **Audit** | Полный лог действий админов |

---

## 📊 Мониторинг

### Health Check (`/health`)

```json
{
  "status": "healthy",
  "managers_count": 50,
  "achievements_count": 200,
  "countries_count": 8,
  "response_time_ms": 15,
  "redis_status": "connected",
  "database_status": "connected"
}
```

### Prometheus Metrics (`/metrics`)

- `http_requests_total`
- `http_request_duration_seconds`
- `http_request_size_bytes`
- `http_response_size_bytes`

---

## 🚀 Деплой

### CI/CD Pipeline

```
Push to main
    ↓
GitHub Actions
    ↓
SSH to VPS
    ↓
Auto Backup БД
    ↓
git reset --hard origin/main
    ↓
pip install -r requirements.txt
    ↓
alembic upgrade head
    ↓
systemctl restart shadow-hockey-league
    ↓
Health Check → Success / Auto Rollback
```

### Backup Strategy

- **Ежедневно:** 03:00 UTC (cron)
- **Pre-deploy:** Перед каждым деплоем
- **Retention:** 10 последних бэкапов

---

## 🧪 Тестирование

| Метрика | Значение |
|---------|----------|
| **Всего тестов** | 296 |
| **Покрытие** | ~87% |
| **E2E** | 15 тестов |
| **Admin smoke** | 6 тестов |
| **API** | 28 тестов |

**Типы тестов:**
- **Unit:** rating service, validation, models, cache, API auth
- **Integration:** routes, API CRUD, database constraints, cache invalidation
- **Admin:** CSRF, auth, CRUD, smoke-тесты
- **E2E:** полный цикл приложения

---

## 📋 Формула расчёта очков

```
points = base_points(league, achievement_type) × season_multiplier
```

### Множители сезонов

| Сезон | Множитель |
|-------|-----------|
| 24/25 | ×1.00 |
| 23/24 | ×0.95 |
| 22/23 | ×0.90 |
| 21/22 | ×0.85 |

---

*Последнее обновление: 13 апреля 2026 г.*
