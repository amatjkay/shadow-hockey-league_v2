# 🏛️ Архитектура системы - Shadow Hockey League v2

**Версия:** 1.0
**Дата:** 7 апреля 2026 г.
**Статус:** ✅ Production (v2.4.0)

---

## 📋 Обзор

Этот документ описывает **текущую архитекцию** системы Shadow Hockey League v2.

**Production:** https://shadow-hockey-league.ru/

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
│   - Blueprints для маршрутов    │
│   - Services для бизнес-логики  │
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

### Backend

| Технология | Версия | Назначение |
|-----------|--------|------------|
| Python | 3.10+ | Язык разработки |
| Flask | 3.1+ | Web framework |
| SQLAlchemy | 2.0+ | ORM |
| Alembic | 1.14+ | Миграции БД |
| Gunicorn | 20.1+ | WSGI server |

### Infrastructure

| Технология | Версия | Назначение |
|-----------|--------|------------|
| Ubuntu Server | 22.04 LTS | ОС |
| Nginx | 1.18+ | Reverse proxy, SSL |
| Redis | 6.0+ | Кэширование |
| SQLite | 3.x | База данных |
| Let's Encrypt | - | SSL сертификаты |

### Flask Extensions

- **Flask-Admin** - админ-панель
- **Flask-Login** - аутентификация
- **Flask-WTF** - CSRF защита
- **Flask-Caching** - кэширование
- **Flask-Limiter** - rate limiting
- **Prometheus Flask** - метрики

---

## 🗂️ Структура проекта

```
shadow-hockey-league_v2/
├── app.py                      # Application Factory
├── models.py                   # SQLAlchemy модели
├── config.py                   # Конфигурация
│
├── blueprints/                 # Маршруты
│   ├── main.py                 #   Главная страница
│   └── health.py               #   Health check
│
├── services/                   # Бизнес-логика
│   ├── rating_service.py       #   Расчёт рейтинга
│   ├── cache_service.py        #   Кэширование
│   ├── api.py                  #   REST API
│   ├── admin.py                #   Flask-Admin
│   ├── metrics_service.py      #   Метрики
│   ├── validation_service.py   #   Валидация
│   └── audit_service.py        #   Audit Log
│
├── data/                       # Данные
│   ├── seed/                   #   Исходные данные
│   ├── export/                 #   Экспорт из БД
│   └── schemas.py              #   Валидация JSON
│
├── tests/                      # Тесты (239 тестов)
├── migrations/                 # Alembic миграции
├── templates/                  # Jinja2 шаблоны
├── static/                     # CSS, JS, изображения
└── scripts/                    # Утилиты
```

---

## 🗄️ Модель данных

### Основные таблицы

| Таблица | Описание | Ключевые поля |
|---------|----------|---------------|
| **countries** | Справочник стран | id, code, name, flag_path |
| **managers** | Участники лиги | id, name, country_id |
| **achievements** | Достижения | id, type, league, season, manager_id |
| **achievement_types** | Типы достижений (формула) | id, name, base_points_l1/l2 |
| **seasons** | Сезоны с множителями | id, name, multiplier |
| **admin_users** | Пользователи админки | id, username, password_hash |
| **api_keys** | API ключи | id, key_hash, scope |
| **audit_logs** | Лог действий | id, user_id, action, timestamp |

### Уникальные ограничения

- `achievements(manager_id, league, season, achievement_type)` - UNIQUE
- `managers.name` - UNIQUE
- `countries.code` - UNIQUE

---

## 🔌 API

### REST API

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
- Pagination (`page`/`per_page`, max 100)
- Rate limiting (100 req/min)
- Cache invalidation при мутациях
- Audit logging всех мутаций

---

## ⚡ Кэширование

### Архитектура

```
Request → Cache Check → Hit → Return
                  ↓
                 Miss → Database Query → Cache Set → Return
```

### Стратегия

- **Backend:** Redis с fallback на SimpleCache
- **TTL:** 5 минут
- **Инвалидация:** При CREATE/UPDATE/DELETE в админке или API
- **Manual Flush:** Кнопка в админ-панели

---

## 🔒 Безопасность

### Аутентификация

- **Admin Panel:** Flask-Login (session-based)
- **API:** API Key (hash в БД)

### Защита

- **CSRF:** Flask-WTF для всех форм
- **Rate Limiting:** 100 req/min на API ключ
- **Passwords:** Werkzeug hash
- **Secrets:** Только в `.env`
- **SSL:** Let's Encrypt с автообновлением

---

## 🚀 Деплой

### CI/CD Pipeline

```
Push to main → GitHub Actions → SSH to VPS → Auto Backup → git reset --hard → pip install → alembic upgrade → restart → Health Check → Success/Rollback
```

### Backup Strategy

- **Ежедневно:** 3:00 UTC (cron)
- **Pre-deploy:** Перед каждым деплоем
- **Retention:** 10 бэкапов
- **Format:** gzip

### Rollback

- **GitHub Actions:** Workflow Dispatch
- **Manual:** Через SSH
- **Auto:** При failed health check

---

## 📊 Мониторинг

### Health Check

**Endpoint:** `/health`

**Returns:**
```json
{
  "status": "healthy",
  "managers_count": 50,
  "achievements_count": 200,
  "response_time_ms": 15,
  "redis_status": "connected",
  "database_status": "connected"
}
```

### Prometheus Metrics

**Endpoint:** `/metrics`

**Metrics:**
- `http_requests_total`
- `http_request_duration_seconds`
- `http_request_size_bytes`
- `http_response_size_bytes`

---

## 🧪 Тестирование

### Статистика

| Метрика | Значение |
|---------|----------|
| Всего тестов | 239 |
| Unit + Integration | 224 |
| E2E | 15 |
| Покрытие | ~87% |

### Типы тестов

- **Unit:** Rating service, validation, models
- **Integration:** Routes, API, database
- **E2E:** Полный цикл приложения
- **Admin:** CSRF, auth, CRUD

---

## 🔮 Будущие улучшения

### Planned

- [ ] Система уведомлений (Email + In-App)
- [ ] Миграция на PostgreSQL
- [ ] WebSocket real-time обновления
- [ ] Docker контейнеризация

### Considered

- [ ] GraphQL API
- [ ] Celery для фоновых задач
- [ ] Sentry для error tracking
- [ ] Grafana дашборды

---

**Последнее обновление:** 7 апреля 2026 г.
**Версия:** 2.4.0
**Статус:** ✅ Production
