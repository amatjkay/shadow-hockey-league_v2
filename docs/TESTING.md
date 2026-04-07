# 🧪 Тестирование - Shadow Hockey League v2

**Версия:** 1.0
**Дата:** 7 апреля 2026 г.
**Статус:** ✅ 239 тестов, ~87% покрытие

---

## 📊 Общая статистика

| Метрика | Значение |
|---------|----------|
| **Всего тестов** | 239 |
| **Unit тесты** | ~150 |
| **Integration тесты** | ~74 |
| **E2E тесты** | 15 |
| **Покрытие кода** | ~87% |
| **Статус** | ✅ Все проходят |

---

## 🚀 Запуск тестов

### Все тесты

```bash
pytest
```

### С детализацией

```bash
pytest -v
```

### С покрытием

```bash
pytest --cov=. --cov-report=term-missing
```

### HTML отчёт о покрытии

```bash
pytest --cov=. --cov-report=html
# Откройте htmlcov/index.html
```

### Только unit тесты

```bash
pytest tests/ -v -k "not e2e"
```

### Только E2E тесты

```bash
pytest tests/e2e/ -v
```

### Один тестовый файл

```bash
pytest tests/test_rating_service.py -v
```

### Один тест

```bash
pytest tests/test_rating_service.py::test_rating_calculation -v
```

---

## 📁 Структура тестов

```
tests/
├── conftest.py                 # Fixtures (app, client, db)
├── test_rating_service.py      # Unit: расчёт рейтинга
├── test_validation_service.py  # Unit: валидация данных
├── test_models.py              # Unit: модели SQLAlchemy
├── test_cache_service.py       # Unit: кэширование
├── test_admin.py               # Integration: админ-панель
├── test_api.py                 # Integration: REST API
├── integration/                # Integration тесты
│   ├── test_routes.py          #   Маршруты приложения
│   ├── test_database.py        #   Ограничения БД
│   └── test_cache.py           #   Кэширование
└── e2e/                        # E2E тесты (15 тестов)
    ├── test_main_page.py       #   Главная страница
    ├── test_health.py          #   Health check
    ├── test_admin.py           #   Админ-панель
    └── test_api.py             #   API endpoints
```

---

## 🧪 Типы тестов

### Unit тесты

**Цель:** Тестирование отдельных модулей в изоляции

**Что тестируем:**
- Rating service - формула расчёта очков
- Validation service - валидация данных
- Cache service - кэширование и инвалидация
- Models - SQLAlchemy модели

**Пример:**
```python
def test_rating_calculation():
    service = RatingService()
    result = service.calculate(manager_id=1)
    assert result > 0
```

---

### Integration тесты

**Цель:** Тестирование взаимодействия компонентов

**Что тестируем:**
- Routes - HTTP маршруты
- API - REST API endpoints
- Database - ограничения и FK
- Cache - инвалидация кэша
- Admin - CSRF, auth, CRUD

**Пример:**
```python
def test_api_returns_json(client):
    response = client.get('/api/countries')
    assert response.status_code == 200
    assert response.is_json
```

---

### E2E тесты (15 тестов)

**Цель:** Полный цикл приложения

**Что тестируем:**
1. ✅ Главная страница загружается
2. ✅ Health check возвращает healthy
3. ✅ Метрики доступны
4. ✅ Админ-панель требует auth
5. ✅ CRUD операции в админке
6. ✅ CSRF защита работает
7. ✅ API endpoints работают
8. ✅ API требует auth
9. ✅ Статика загружается
10. ✅ Кэш работает
11. ✅ Audit log записывается
12. ✅ Flush cache работает
13. ✅ Rate limiting работает
14. ✅ Pagination работает
15. ✅ Ошибки обрабатываются

**Пример:**
```python
def test_main_page_loads(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Rating' in response.data
```

---

## 📈 Покрытие кода

### Текущее покрытие: ~87%

| Модуль | Покрытие | Статус |
|--------|----------|--------|
| `services/rating_service.py` | ~95% | ✅ |
| `services/validation_service.py` | ~90% | ✅ |
| `services/cache_service.py` | ~85% | ✅ |
| `services/api.py` | ~90% | ✅ |
| `services/admin.py` | ~85% | ✅ |
| `services/audit_service.py` | ~80% | ✅ |
| `services/metrics_service.py` | ~75% | ⚠️ |
| `blueprints/main.py` | ~85% | ✅ |
| `blueprints/health.py` | ~95% | ✅ |
| `models.py` | ~90% | ✅ |

### Цели

- **Минимум:** 80%
- **Цель:** 90%
- **Текущее:** ~87% ✅

---

## 🔧 Fixtures

### Основные fixtures (conftest.py)

```python
@pytest.fixture
def app():
    """Создание Flask приложения для тестов."""
    app = create_app(config_class='config.TestingConfig')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """HTTP клиент для тестов."""
    return app.test_client()

@pytest.fixture
def db_session(app):
    """Сессия БД для тестов."""
    with app.app_context():
        yield db.session
```

---

## 🎯 Best Practices

### Именование тестов

```python
# ✅ Хорошо
def test_rating_calculation_with_multiple_awards():
def test_api_returns_401_without_auth():
def test_csrf_blocks_post_without_token():

# ❌ Плохо
def test_1():
def test_api():
def test_stuff():
```

### Структура теста (AAA pattern)

```python
def test_something():
    # Arrange (подготовка)
    service = RatingService()
    manager_id = 1
    
    # Act (действие)
    result = service.calculate(manager_id)
    
    # Assert (проверка)
    assert result > 0
    assert isinstance(result, float)
```

### Что тестировать

✅ **Тестируем:**
- Бизнес-логику (формулы, расчёты)
- API endpoints (status codes, JSON structure)
- Валидацию данных
- Ограничения БД (UNIQUE, FK)
- CSRF защиту
- Rate limiting
- Кэширование и инвалидацию

❌ **Не тестируем:**
- Flask framework
- SQLAlchemy ORM
- Nginx конфигурацию
- Сторонние библиотеки

---

## 🐛 Debug тестов

### Запуск с pdb

```bash
pytest --pdb -v
```

### Print в тестах

```bash
pytest -s  # Показывает print()
```

### Логирование

```bash
pytest --log-cli-level=DEBUG
```

---

## 🚀 CI/CD

### GitHub Actions

Тесты запускаются автоматически при:
- Push в `main`
- Pull requests
- Workflow dispatch

**Workflow:** `.github/workflows/deploy.yml`

```yaml
- name: Run tests
  run: |
    pytest -v --cov=. --cov-report=term-missing
```

---

## 📊 Отчёты

### Генерация отчёта

```bash
pytest --cov=. --cov-report=html
```

### Просмотр

```bash
# Откройте в браузере
htmlcov/index.html
```

---

## 🔮 Планы

- [ ] Увеличить покрытие до 90%
- [ ] Добавить тесты на metrics_service
- [ ] Добавить нагрузочные тесты
- [ ] Добавить тесты безопасности
- [ ] Автоматическая генерация mocks

---

**Последнее обновление:** 7 апреля 2026 г.
**Версия:** 1.0
**Статус:** ✅ 239 тестов проходят
