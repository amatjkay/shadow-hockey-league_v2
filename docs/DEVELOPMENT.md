# Development Guide — Shadow Hockey League v2

**Версия:** 2.6.0
**Дата:** 13 апреля 2026 г.

---

## 1. Разработка

### Code Style

- PEP 8 для Python
- Форматирование: `black`, `isort`
- Линтинг: `flake8`
- Типизация: `typing` модуль для аннотаций

### Workflow

1. Создать ветку для фичи/багфикса
2. Написать тесты
3. Убедиться что все тесты проходят
4. Обновить документацию
5. Закоммитить и создать PR

### Команды

```bash
make setup     # Установка зависимостей + БД
make run       # Запуск сервера
make test      # Запуск тестов
make lint      # Проверка кода
make format    # Форматирование
make clean     # Очистка
```

---

## 2. Тестирование

### Запуск

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=. --cov-report=term-missing

# Только integration
pytest tests/integration/ -v
```

### Статистика

| Метрика | Значение |
|---------|----------|
| Всего тестов | 296 |
| Покрытие | ~87% |
| E2E | 15 |
| Admin smoke | 6 |
| API | 28 |

### Структура тестов

```
tests/
├── conftest.py                 # Fixtures
├── test_rating_service.py      # Unit: рейтинг
├── test_validation.py          # Unit: валидация
├── test_cache_and_admin.py     # Unit: кэш
├── test_audit_service.py       # Unit: audit
├── test_api.py                 # Integration: API
├── test_api_auth.py            # Integration: API auth
├── test_blueprints.py          # Integration: routes
├── integration/                # Интеграционные тесты
│   ├── test_admin_smoke_flow.py
│   └── test_admin_api.py
└── e2e/                        # E2E тесты
    └── test_e2e.py
```

---

## 3. Деплой

### Production сервер

- **OS:** Ubuntu 22.04 LTS
- **Python:** 3.10+
- **Redis:** 6.0+
- **Nginx:** reverse proxy + SSL
- **Gunicorn:** 4 workers

### CI/CD

Автоматический деплой при пуше в `main`:

1. GitHub Actions → SSH к VPS
2. Auto backup БД
3. `git reset --hard origin/main`
4. `pip install -r requirements.txt`
5. `alembic upgrade head`
6. `systemctl restart shadow-hockey-league`
7. Health check → auto rollback при ошибке

### Ручной деплой

```bash
ssh shleague@server
cd /home/shleague/shadow-hockey-league_v2
source venv/bin/activate
git fetch origin main
git reset --hard origin/main
pip install -r requirements.txt
alembic upgrade head
systemctl restart shadow-hockey-league
```

---

*Последнее обновление: 13 апреля 2026 г.*
