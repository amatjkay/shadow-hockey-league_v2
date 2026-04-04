# Architecture — Shadow Hockey League v2

**Дата:** 4 апреля 2026 г.
**Роль:** ARCHITECT (архитектура v2.2 утверждена)
**Статус:** 🟢 Проектирование аудита и управления кэшем завершено

---

## 🏗️ Архитектурный стиль

**Слоистая архитектура** (Layered Architecture):

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│  blueprints/main.py  │  blueprints/health.py            │
│  templates/*.html    │  static/{css,js,img}             │
│  Flask-Admin (Audit + Cache Control)                    │
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
│  validation_service │ audit_service (новый)             │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                     Data Layer                           │
│  models.py (SQLAlchemy ORM + Flask-Login + AuditLog)   │
│  data/ (countries_reference, managers_data)             │
│  migrations/ (Alembic + миграция для AuditLog)            │
└─────────────────────────────────────────────────────────┘
```

## 🧩 Компоненты и зависимости

```
app.py (Application Factory)
├── blueprints/main.py → services/rating_service.py → models
├── blueprints/health.py → services/cache_service.py → models
├── services/api.py → services/validation_service.py → models
├── services/admin.py → services/audit_service.py → models
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

**2. Изменение данных (запись + аудит + инвалидация):**

```
Admin → POST/PUT/DELETE → SecureModelView → validation → db.session.commit()
  → audit_service.log_action() → AuditLog table
  → invalidate_leaderboard_cache() → cache.delete('leaderboard')
  → return response
```

**3. Ручное управление кэшем:**

```
Admin → POST /admin/flush-cache → StatsAdminIndexView.flush_cache()
  → cache.delete('leaderboard') → flash('Cache flushed')
  → audit_service.log_action('FLUSH_CACHE') → redirect('/admin/')
```

---

## 🔧 Технологический стек

| Уровень        | Технология                | Версия        | Обоснование                                    |
| -------------- | ------------------------- | ------------- | ---------------------------------------------- |
| Backend        | Python + Flask            | 3.10+, 3.1+   | Лёгкий, подходит для 1GB RAM                   |
| ORM            | SQLAlchemy                | 2.0+          | Зрелый, поддержка миграций                     |
| БД             | SQLite (WAL)              | 3.x           | Zero-config, подходит для < 1000 менеджеров    |
| Миграции       | Alembic                   | 1.14+         | Стандарт для SQLAlchemy                        |
| Кэш            | Redis / SimpleCache       | 6+ / built-in | Redis для prod, SimpleCache fallback           |
| Админ          | Flask-Admin + Flask-Login | 1.6+, 0.6+    | Быстрая интеграция, CRUD из коробки            |
| Метрики        | prometheus-flask-exporter | 0.23+         | Автоматический сбор HTTP-метрик                |
| **Audit Log**  | **SQLAlchemy Table**      | **новый**     | **Структурированный аудит внутри основной БД** |
| **Cache Ctrl** | **Flask-Caching**         | **встроен**   | **Атомарная инвалидация по ключу**             |

---

## 📐 Паттерны проектирования

| Паттерн                     | Где применяется                         | Назначение                                |
| --------------------------- | --------------------------------------- | ----------------------------------------- |
| Application Factory         | app.py                                  | Тестируемость, чистая инициализация       |
| Cache-Aside                 | main.py                                 | Кэширование leaderboard с TTL 300с        |
| Cache Invalidation on Write | api.py, admin.py                        | Авто-инвалидация при CRUD                 |
| Fallback Strategy           | cache_service, rating_service           | Redis → SimpleCache, DB → hardcoded       |
| N+1 Prevention              | rating_service.py                       | joinedload/selectinload для eager loading |
| Singleton                   | cache, metrics, login_manager           | Глобальный доступ к сервисам              |
| **Admin Override Pattern**  | **services/admin.py (SecureModelView)** | **Перехват CRUD для аудита**              |
| **Audit Trail Pattern**     | **audit_service.py**                    | **Логирование действий в AuditLog**       |
| **Manual Cache Flush**      | **StatsAdminIndexView**                 | **Принудительная инвалидация по запросу** |

---

## 🔓 Открытые вопросы → РЕШЕНО

| Вопрос                                   | Решение                                                                      | Обоснование                               | Приоритет  |
| ---------------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------- | ---------- |
| Как логировать действия администратора?  | ✅ **ДА** — Override методов `after_model_change/delete` в `SecureModelView` | Гарантирует лог только UI-действий        | 🔴 Высокий |
| Где хранить логи?                        | ✅ **ДА** — Таблица `audit_logs` в основной SQLite БД                        | Простота, транзакционная целостность      | 🔴 Высокий |
| Как реализовать ручной сброс кэша?       | ✅ **ДА** — `@expose('/flush-cache')` в `StatsAdminIndexView`                | Интеграция в существующий админ-интерфейс | � Средний  |
| Как оптимизировать N+1 в rating_service? | ✅ **ДА** — Проверить и обеспечить `joinedload` для всех связанных моделей   | Уже реализовано, но требует аудита        | 🟡 Средний |

---

## ✅ Принятые архитектурные решения

| Решение                             | Статус       | Примечание                       |
| ----------------------------------- | ------------ | -------------------------------- |
| Application Factory pattern         | ✅ Принято   | —                                |
| Слоистая архитектура                | ✅ Принято   | —                                |
| Fallback стратегия                  | ✅ Принято   | —                                |
| Cache Invalidation on Write         | ✅ Принято   | —                                |
| SQLite WAL режим                    | ✅ Принято   | —                                |
| **Audit Log в основной БД**         | ✅ **Новое** | Таблица `audit_logs` с индексами |
| **Flask-Admin Override для аудита** | ✅ **Новое** | `SecureModelView` миксин         |
| **Ручной сброс кэша**               | ✅ **Новое** | Эндпоинт `/admin/flush-cache`    |
| **Оптимизация N+1**                 | ✅ **Новое** | Гарантированный `joinedload`     |

---

## ⚠️ Архитектурные риски

| Риск                                         | Влияние | Способ снижения                             |
| -------------------------------------------- | ------- | ------------------------------------------- |
| Рост таблицы audit_logs                      | Среднее | Периодическая очистка записей > 90 дней     |
| Нагрузка на диск при частых операциях        | Низкое  | Логирование только диффов (JSON) при UPDATE |
| Race condition при одновременном сбросе кэша | Низкое  | Атомарная операция `cache.delete()`         |
| Нехватка RAM (1GB VPS)                       | Высокое | Redis лимит 128MB, мониторинг ztv.su        |
| SQLite не масштабируется (> 1000 менеджеров) | Среднее | План миграции на PostgreSQL готов           |

---

## 📁 Планируемая структура проекта (v2.2)

```
shadow-hockey-league_v2/
├── app.py                      # Application Factory
├── models.py                   # SQLAlchemy модели + AuditLog
├── config.py                   # Конфигурация (Development/Production/Testing)
├── blueprints/                 # Flask blueprints (main, health)
├── services/                   # Бизнес-логика
│   ├── rating_service.py       # Расчёт рейтинга (joinedload)
│   ├── cache_service.py        # Кэширование и инвалидация
│   ├── api.py                  # REST API (с auth + пагинацией)
│   ├── admin.py                # Flask-Admin (с CSRF + Audit)
│   ├── audit_service.py        # **НОВЫЙ:** Логирование действий
│   ├── metrics_service.py      # Prometheus метрики
│   └── validation_service.py   # Валидация данных
├── data/                       # Справочные данные
├── templates/                  # Jinja2 шаблоны
│   └── admin/
│       ├── index.html          # **ОБНОВЛЕНИЕ:** Кнопка Flush Cache
│       └── shl_master.html     # **ОБНОВЛЕНИЕ:** Title для страниц
├── static/                     # CSS, JS, изображения
├── migrations/                 # Alembic миграции
│   └── versions/
│       └── add_audit_log.py    # **НОВАЯ:** Миграция для таблицы аудита
├── tests/                      # Тесты
│   ├── test_audit_service.py   # **НОВЫЙ:** Тесты аудита
│   └── ...
├── docs/                       # Документация
└── context/                    # Модульная система контекста
```

---

_Последнее обновление: 4 апреля 2026 г. — Архитектура v2.2 утверждена. Передача в планирование._
