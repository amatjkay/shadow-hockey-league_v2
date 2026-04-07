# 🏗️ АРХИТЕКТУРА СИСТЕМЫ - Shadow Hockey League v2

**Версия:** 2.4.0
**Дата:** 7 апреля 2026 г.
**Статус:** ✅ Production

---

## 1. Общая архитектура

### 1.1 Архитектурная схема

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
│   - Timeout: 120s               │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│   Flask Application             │
│   - app.py (Application Factory)│
│   - blueprints/ (Routes)        │
│   - services/ (Business Logic)  │
└───┬─────────┬─────────┬─────────┘
    │         │         │
    ▼         ▼         ▼
┌───────┐ ┌──────┐ ┌────────┐
│SQLite │ │Redis │ │Promethe│
│  DB   │ │Cache │ │  us    │
└───────┘ └──────┘ └────────┘
```

---

## 2. Компоненты системы

### 2.1 Backend

| Компонент | Технология | Версия | Назначение |
|-----------|-----------|--------|------------|
| **Language** | Python | 3.10+ | Язык разработки |
| **Framework** | Flask | 3.1+ | Web framework |
| **WSGI** | Gunicorn | 20.1+ | Application server |
| **ORM** | SQLAlchemy | 2.0+ | Database ORM |
| **Migrations** | Alembic | 1.14+ | Миграции БД |
| **Admin** | Flask-Admin | 2.0+ | Админ-панель |
| **Auth** | Flask-Login | 0.6+ | Аутентификация |
| **CSRF** | Flask-WTF | 1.2+ | CSRF защита |
| **Cache** | Flask-Caching | 2.3+ | Кэширование |
| **Rate Limit** | Flask-Limiter | 3.5+ | Rate limiting |
| **Metrics** | Prometheus Flask | 0.23+ | Экспорт метрик |

### 2.2 Infrastructure

| Компонент | Технология | Версия | Назначение |
|-----------|-----------|--------|------------|
| **OS** | Ubuntu Server | 22.04 LTS | Операционная система |
| **Web Server** | Nginx | 1.18+ | Reverse proxy, SSL |
| **Cache** | Redis | 6.0+ | Кэширование |
| **Database** | SQLite | 3.x | Реляционная БД |
| **SSL** | Let's Encrypt | - | HTTPS сертификаты |
| **CI/CD** | GitHub Actions | - | Автоматический деплой |

---

## 3. Структура приложения

### 3.1 Модульная архитектура

```
shadow-hockey-league_v2/
├── app.py                      # Application Factory
├── models.py                   # SQLAlchemy модели
├── config.py                   # Конфигурация (Dev/Prod/Test)
│
├── blueprints/                 # Flask blueprints
│   ├── main.py                 #   Главная страница, leaderboard
│   └── health.py               #   Health check endpoint
│
├── services/                   # Бизнес-логика
│   ├── rating_service.py       #   Расчёт рейтинга
│   ├── cache_service.py        #   Кэширование и инвалидация
│   ├── api.py                  #   REST API
│   ├── admin.py                #   Flask-Admin
│   ├── metrics_service.py      #   Prometheus метрики
│   ├── validation_service.py   #   Валидация данных
│   └── audit_service.py        #   Audit Log
│
├── data/                       # Справочные данные
│   ├── seed/                   #   Исходные данные
│   ├── export/                 #   Экспорт из БД
│   └── schemas.py              #   Валидация JSON
│
├── tests/                      # Тесты
│   ├── test_*.py               #   Unit тесты
│   ├── integration/            #   Integration тесты
│   └── e2e/                    #   E2E тесты (15 тестов)
│
├── migrations/                 # Alembic миграции
├── templates/                  # Jinja2 шаблоны
├── static/                     # CSS, JS, изображения
└── scripts/                    # Утилиты
    ├── create_admin.py         #   Создание админа
    ├── validate_db.py          #   Валидация БД
    └── deploy.sh.template      #   Скрипт деплоя
```

---

## 4. Модель данных

### 4.1 Основные таблицы

```sql
-- Countries: справочник стран
countries (id, code, name, flag_path)

-- Managers: участники лиги
managers (id, name, country_id)

-- Achievements: достижения менеджеров
achievements (id, achievement_type, league, season, title, icon_path, manager_id)

-- Achievement Types: типы достижений (формула в БД)
achievement_types (id, name, base_points_l1, base_points_l2)

-- Seasons: сезоны с множителями
seasons (id, name, multiplier)

-- Admin Users: пользователи админки
admin_users (id, username, password_hash)

-- API Keys: ключи для API
api_keys (id, key_hash, scope, description, created_at)

-- Audit Log: лог действий администраторов
audit_logs (id, user_id, action, target_model, target_id, changes, timestamp)
```

### 4.2 Индексы

- `achievements.manager_id` - FK индекс
- `achievements(manager_id, league, season, achievement_type)` - UNIQUE constraint
- `audit_logs.timestamp` - для быстрого поиска по времени
- `audit_logs(user_id, timestamp)` - composite индекс
- `managers.country_id` - FK индекс

---

## 5. API Архитектура

### 5.1 REST API

**Base URL:** `/api/`

**Authentication:** API Key с scopes:
- `read` - GET запросы
- `write` - POST/PUT/DELETE
- `admin` - все операции

**Endpoints:**
- `GET /api/countries` - Список стран
- `GET /api/managers` - Список менеджеров
- `GET /api/achievements` - Список достижений

**Features:**
- Pagination (`page`/`per_page`)
- Rate limiting (100 req/min)
- Cache invalidation при мутациях
- Audit logging

---

## 6. Кэширование

### 6.1 Архитектура кэша

```
┌──────────────┐
│  Request     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Cache Check │
└──┬───────┬───┘
   │       │
   │ Hit   │ Miss
   │       │
   ▼       ▼
┌─────┐ ┌──────────┐
│Cache│ │Database  │
│Return│ │Query +   │
└─────┘ │Cache Set │
        └──────────┘
```

### 6.2 Стратегия инвалидации

- **CREATE/UPDATE/DELETE** в админке → инвалидация leaderboard cache
- **API мутации** → инвалидация leaderboard cache
- **Flush Cache** через UI → полная очистка кэша
- **TTL:** 5 минут (default timeout)

---

## 7. Безопасность

### 7.1 Аутентификация

- **Admin Panel:** Flask-Login с session-based auth
- **API:** API Key с hash хранением в БД
- **CSRF:** Flask-WTF CSRF protection для всех форм

### 7.2 Авторизация

- **Admin Users:** CRUD через Flask-Admin
- **API Keys:** 3 scope (read, write, admin)
- **Rate Limiting:** 100 запросов/мин на API ключ

### 7.3 Защита данных

- **Пароли:** Хранятся как hash (Werkzeug)
- **API Keys:** Хранятся как hash
- **Secrets:** Только в `.env`, не коммитятся
- **SSL:** Let's Encrypt с автообновлением

---

## 8. Деплой

### 8.1 CI/CD Pipeline

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
Health Check
    ↓
Success / Auto Rollback
```

### 8.2 Backup Strategy

- **Ежедневно:** В 3:00 UTC (cron)
- **Pre-deploy:** Перед каждым деплоем
- **Retention:** 10 последних бэкапов
- **Format:** gzip сжатие

### 8.3 Rollback

- **GitHub Actions:** Workflow Dispatch
- **Ручной:** Через SSH
- **Auto:** При failed health check

---

## 9. Мониторинг

### 9.1 Health Check

**Endpoint:** `/health`

**Returns:**
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

### 9.2 Prometheus Metrics

**Endpoint:** `/metrics`

**Metrics:**
- `http_requests_total` - количество запросов
- `http_request_duration_seconds` - время ответа
- `http_request_size_bytes` - размер запроса
- `http_response_size_bytes` - размер ответа

---

## 10. Тестирование

### 10.1 Статистика

| Метрика | Значение |
|---------|----------|
| **Всего тестов** | 239 |
| **Unit + Integration** | 224 |
| **E2E** | 15 |
| **Покрытие** | ~87% |

### 10.2 Типы тестов

- **Unit:** Rating service, validation, models
- **Integration:** Routes, API, database, constraints
- **E2E:** Полный цикл приложения
- **Admin:** CSRF, auth, CRUD операции

---

## 11. Будущие улучшения

### 11.1 Planned

- [ ] Система уведомлений (Email + In-App)
- [ ] Миграция на PostgreSQL
- [ ] WebSocket real-time обновления
- [ ] Docker контейнеризация
- [ ] Kubernetes orchestration

### 11.2 Рассмотреть

- [ ] GraphQL API
- [ ] Celery для фоновых задач
- [ ] Sentry для error tracking
- [ ] Grafana дашборды
- [ ] Log aggregation (ELK stack)

---

**Последнее обновление:** 7 апреля 2026 г.
**Версия:** 2.4.0
**Статус:** ✅ Production
