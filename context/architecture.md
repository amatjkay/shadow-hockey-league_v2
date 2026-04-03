# Architecture — Shadow Hockey League v2

**Дата:** 3 апреля 2026 г.
**Роль:** ARCHITECT (глубокий анализ завершён)
**Статус:** 🟢 Архитектура документирована, решения зафиксированы

---

## 🏗️ Архитектурный стиль

**Слоистая архитектура** (Layered Architecture):

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│  blueprints/main.py  │  blueprints/health.py            │
│  templates/*.html    │  static/{css,js,img}             │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    Application Layer                     │
│  app.py (Application Factory + Extension Registry)      │
│  config.py (Development/Production/Testing)             │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                     Service Layer                        │
│  rating_service │ cache_service │ api │ admin │ metrics  │
│  validation_service                                     │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                     Data Layer                           │
│  models.py (SQLAlchemy ORM + Flask-Login)               │
│  data/ (countries_reference, managers_data)             │
│  migrations/ (Alembic)                                  │
└─────────────────────────────────────────────────────────┘
```

## 🧩 Компоненты и зависимости

```
app.py (Application Factory)
├── blueprints/main.py → services/rating_service.py → models
├── blueprints/health.py → services/cache_service.py → models
├── services/api.py → services/validation_service.py → models
├── services/admin.py → services/cache_service.py → models
└── services/metrics_service.py (singleton) → prometheus_flask_exporter
```

### Потоки данных

**1. Запрос leaderboard (чтение):**

```
User → GET / → main.index() → cache.get('leaderboard')
  ├─ HIT → return cached HTML
  └─ MISS → db.session.query(Manager) → rating_service.build_leaderboard()
            → cache.set('leaderboard', html, timeout=300) → return HTML
```

**2. Изменение данных (запись + инвалидация):**

```
Admin/API → POST/PUT/DELETE → validation → db.session.commit()
  → invalidate_leaderboard_cache() → cache.delete('leaderboard')
  → audit_logger.log() → return response
```

**3. Health check:**

```
GET /health → check_db() + check_redis() + check_cache() + calc_uptime()
  → return {status, components, counts, uptime}
```

---

## 🔧 Технологический стек

| Уровень      | Технология                   | Версия        | Обоснование                                 |
| ------------ | ---------------------------- | ------------- | ------------------------------------------- |
| Backend      | Python + Flask               | 3.10+, 3.1+   | Лёгкий, подходит для 1GB RAM                |
| ORM          | SQLAlchemy                   | 2.0+          | Зрелый, поддержка миграций                  |
| БД           | SQLite (WAL)                 | 3.x           | Zero-config, подходит для < 1000 менеджеров |
| Миграции     | Alembic                      | 1.14+         | Стандарт для SQLAlchemy                     |
| Кэш          | Redis / SimpleCache          | 6+ / built-in | Redis для prod, SimpleCache fallback        |
| Админ        | Flask-Admin + Flask-Login    | 1.6+, 0.6+    | Быстрая интеграция, CRUD из коробки         |
| Метрики      | prometheus-flask-exporter    | 0.23+         | Автоматический сбор HTTP-метрик             |
| Web Server   | Nginx + Gunicorn             | 4 workers     | Nginx reverse proxy + SSL                   |
| CI/CD        | GitHub Actions               | deploy.yml    | Бесплатный, интеграция с GitHub             |
| Линтер       | flake8 + black + isort       | —             | Стандарт Python сообщества                  |
| **API Auth** | **API Keys + Flask-Limiter** | **новый**     | **Простой, лёгкий, отзываемый**             |
| **CSRF**     | **Flask-WTF CSRFProtect**    | **встроен**   | **Низкая сложность, встроенная защита**     |

---

## 📐 Паттерны проектирования

| Паттерн                     | Где применяется               | Назначение                               |
| --------------------------- | ----------------------------- | ---------------------------------------- |
| Application Factory         | app.py                        | Тестируемость, чистая инициализация      |
| Cache-Aside                 | main.py                       | Кэширование leaderboard с TTL 300с       |
| Cache Invalidation on Write | api.py, admin.py              | Авто-инвалидация при CRUD                |
| Fallback Strategy           | cache_service, rating_service | Redis → SimpleCache, DB → hardcoded      |
| N+1 Prevention              | rating_service.py             | joinedload для eager loading             |
| Singleton                   | cache, metrics, login_manager | Глобальный доступ к сервисам             |
| Result Tuple                | validation_service.py         | Валидация возвращает (bool, str \| None) |
| **API Key Authentication**  | **api.py (планируется)**      | **Аутентификация API запросов**          |
| **Pagination**              | **api.py (планируется)**      | **Пагинация ответов API**                |

---

## 🔓 Открытые вопросы → РЕШЕНО

| Вопрос                                        | Решение                                                                   | Обоснование                                    | Приоритет           |
| --------------------------------------------- | ------------------------------------------------------------------------- | ---------------------------------------------- | ------------------- |
| Перенести тесты в `tests/` директорию?        | ✅ **ДА**                                                                 | Стандартная структура Python, поддержка pytest | 🔴 Высокий          |
| Добавить аутентификацию для API?              | ✅ **ДА** — API Keys + Flask-Limiter                                      | Простой, отзываемый, rate limiting             | 🔴 Высокий          |
| Вынести формулу расчёта в конфиг/БД?          | ✅ **ДА** — использовать существующие таблицы `AchievementType`, `Season` | Гибкость без деплоя, таблицы уже есть          | 🔴 Высокий (Этап 4) |
| Заменить `FLASK_ENV` на кастомную переменную? | ⏸ **При необходимости**                                                   | `FLASK_ENV` deprecated, но работает            | 🟢 Низкий           |
| Добавить пагинацию в API?                     | ✅ **ДА** — `page`/`per_page` params                                      | Производительность при росте данных            | 🟡 Средний          |
| Внедрить CSRF защиту в админке?               | ✅ **ДА** — Flask-WTF CSRFProtect                                         | Низкая сложность, встроенная защита            | 🟡 Средний (Этап 3) |

---

## ✅ Принятые архитектурные решения

| Решение                             | Статус       | Примечание                       |
| ----------------------------------- | ------------ | -------------------------------- |
| Application Factory pattern         | ✅ Принято   | —                                |
| Слоистая архитектура                | ✅ Принято   | —                                |
| Fallback стратегия                  | ✅ Принято   | —                                |
| Cache Invalidation on Write         | ✅ Принято   | —                                |
| SQLite WAL режим                    | ✅ Принято   | —                                |
| API отключено в production          | ✅ Принято   | —                                |
| Prometheus export без сервера       | ✅ Принято   | —                                |
| **API Keys для аутентификации API** | ✅ **Новое** | Flask-Limiter для rate limiting  |
| **Пагинация API (page/per_page)**   | ✅ **Новое** | Default: 20, max: 100            |
| **Формула расчёта из БД**           | ✅ **Новое** | AchievementType + Season таблицы |
| **Перенос тестов в tests/**         | ✅ **Новое** | Стандартная структура Python     |
| **CSRF защита в админке**           | ✅ **Новое** | Flask-WTF CSRFProtect            |

---

## ⚠️ Архитектурные риски

| Риск                                                      | Влияние | Способ снижения                                          |
| --------------------------------------------------------- | ------- | -------------------------------------------------------- |
| SQLite не масштабируется (> 1000 менеджеров)              | Среднее | План миграции на PostgreSQL готов (docs/)                |
| Нехватка RAM (1GB VPS)                                    | Высокое | Redis лимит 128MB, Gunicorn 4 workers, мониторинг ztv.su |
| API без аутентификации                                    | Высокое | **Решено:** API Keys + Flask-Limiter (планируется)       |
| Хардкод формулы расчёта                                   | Среднее | **Решено:** Вынос в БД (Этап 4)                          |
| Thread-unsafe запись в config (`LAST_LEADERBOARD_GEN_MS`) | Низкое  | Заменить на thread-local storage                         |
| Глобальные синглтоны (cache, metrics, login_manager)      | Низкое  | Усложняет тестирование, есть reset функции               |
| Расхождение тестов (72 vs 48 в docs)                      | Низкое  | Аудит тестовой базы (планируется)                        |

---

## 📁 Планируемая структура проекта (после рефакторинга)

```
shadow-hockey-league_v2/
├── app.py                      # Application Factory
├── models.py                   # SQLAlchemy модели
├── config.py                   # Конфигурация (Development/Production/Testing)
├── blueprints/                 # Flask blueprints (main, health)
├── services/                   # Бизнес-логика
│   ├── rating_service.py       # Расчёт рейтинга (формула из БД)
│   ├── cache_service.py        # Кэширование и инвалидация
│   ├── api.py                  # REST API (с auth + пагинацией)
│   ├── admin.py                # Flask-Admin (с CSRF)
│   ├── metrics_service.py      # Prometheus метрики
│   └── validation_service.py   # Валидация данных
├── data/                       # Справочные данные
├── templates/                  # Jinja2 шаблоны
├── static/                     # CSS, JS, изображения
├── migrations/                 # Alembic миграции
├── tests/                      # ✅ НОВАЯ СТРУКТУРА
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_rating_service.py
│   ├── test_cache_service.py
│   ├── test_api.py
│   ├── test_admin.py
│   ├── test_health.py
│   ├── test_models.py
│   ├── test_validation.py
│   └── integration/
│       ├── test_routes.py
│       └── test_cache_invalidation.py
├── docs/                       # Документация
└── context/                    # Модульная система контекста
```

---

_Последнее обновление: 3 апреля 2026 г. после анализа роли ARCHITECT_
_Решения пользователя зафиксированы: API Keys, пагинация, формула из БД, тесты в tests/, CSRF_
