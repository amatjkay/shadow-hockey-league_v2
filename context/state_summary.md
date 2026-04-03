# State Summary — Shadow Hockey League v2

**Дата:** 3 апреля 2026 г.
**Роль:** ANALYST (глубокий анализ завершён)
**Статус:** 🟢 Контекст актуализирован

## 🎯 Цель

Production Flask-приложение для управления фентезийной хоккейной лигой с рейтингом менеджеров, админ-панелью, кэшированием и мониторингом.
**Production URL:** https://shadow-hockey-league.ru/

## 🛠 Стек

- **Backend:** Python 3.10+, Flask 3.1+, SQLAlchemy 2.0+
- **БД:** SQLite (WAL режим), Alembic 1.14+ миграции
- **Кэш:** Redis (128MB лимит) / SimpleCache fallback, Flask-Caching
- **Админ:** Flask-Admin + Flask-Login
- **Метрики:** prometheus-flask-exporter (без сервера)
- **VPS:** Ubuntu 22.04, Nginx + Gunicorn (4 workers), 1 CPU / 1GB RAM
- **CI/CD:** GitHub Actions (deploy.yml)
- **Линтер:** flake8, black, isort

## 📊 Функциональные блоки

1. **Рейтинг лиги** — расчёт очков: `base_points(league, achievement_type) × season_multiplier`, 6 типов достижений, 2+ лиги, 5 сезонов
2. **Админ-панель** — CRUD стран/менеджеров/достижений, аудит, Flask-Login auth, авто-инвалидация кэша
3. **REST API** — Countries, Managers, Achievements (отключено в production, ENABLE_API=False)
4. **Кэширование** — TTL 300с, инвалидация при записи (Admin + API)
5. **Мониторинг** — `/health` (БД, Redis, кэш, uptime), `/metrics` (Prometheus export), VPS ztv.su

## 📋 Статус этапов

| Этап | Название             | Статус               |
| ---- | -------------------- | -------------------- |
| 0    | Базовая архитектура  | ✅ Готово            |
| 1    | Кэширование          | ✅ Готово            |
| 2    | Метрики              | ✅ Готово            |
| 3    | Админ-панель         | ⚠️ В работе (3 бага) |
| 4    | Рефакторинг формулы  | ⏳ Не начато         |
| 5    | Доп. функционал      | ⏳ Не начато         |
| 6    | Интеграционные тесты | ⏳ Не начато         |
| 7    | Документация         | ✅ Готово            |

## ⚠️ Ключевые риски

| Риск                            | Вероятность | Влияние | Митигация                            |
| ------------------------------- | ----------- | ------- | ------------------------------------ |
| Нехватка RAM (1GB VPS)          | Средняя     | Высокое | Redis лимит 128MB, мониторинг ztv.su |
| SQLite не масштабируется        | Средняя     | Среднее | План миграции на PostgreSQL готов    |
| Расхождение в тестах (72 vs 48) | Высокая     | Низкое  | Требуется аудит тестовой базы        |
| BUG-001: Login/Logout не в меню | Высокая     | Среднее | В работе (Этап 3)                    |
| BUG-002: Нет заголовков страниц | Средняя     | Низкое  | Запланировано                        |
| BUG-003: Выбор флага вручную    | Высокая     | Среднее | В работе (dropdown)                  |

## 📝 Допущения

- Менеджеров < 1000, достижений < 10000
- Трафик < 1000 посетителей/день
- Изменений данных < 50 операций/день
- Один администратор

## 📁 Структура проекта

```
shadow-hockey-league_v2/
├── app.py                      # Application Factory
├── models.py                   # SQLAlchemy модели (AdminUser, Country, Manager, Achievement, + reference tables)
├── config.py                   # Config, DevelopmentConfig, ProductionConfig, TestingConfig
├── blueprints/                 # main.py, health.py
├── services/                   # rating_service.py, cache_service.py, api.py, admin.py, metrics_service.py, validation_service.py
├── data/                       # Справочные данные (countries_reference.py, managers_data.py)
├── templates/                  # Jinja2 шаблоны
├── static/                     # CSS, JS, изображения (флаги)
├── migrations/                 # Alembic миграции
├── docs/                       # BUSINESS_REQUIREMENTS.md, TECHNICAL_SPECIFICATION.md, ADMIN.md, API.md, REDIS.md, MONITORING.md, DEPLOYMENT.md, VPS_DEPLOY.md, TROUBLESHOOTING.md
└── tests*.py                   # 5 тестовых файлов в корне (tests.py, test_metrics.py, tests_cache_and_admin.py, tests_integration.py, tests_api_cache_invalidation.py)
```

## 🔗 Полезные ссылки

- **Production:** https://shadow-hockey-league.ru/
- **Health:** https://shadow-hockey-league.ru/health
- **Metrics:** https://shadow-hockey-league.ru/metrics
- **VPS мониторинг:** ztv.su
- **GitHub:** https://github.com/amatjkay/shadow-hockey-league_v2

---

_Последнее обновление: 3 апреля 2026 г. после глубокого анализа роли ANALYST_
