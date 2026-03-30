# 🧪 План интеграционных тестов

**Цель:** Описание сценариев интеграционного тестирования для Shadow Hockey League.

**Статус:** В разработке

---

## 📋 Обзор

Интеграционные тесты проверяют взаимодействие компонентов системы:
- Flask приложение ↔ База данных
- API endpoints ↔ Валидация данных
- Сервисы ↔ Модели данных

### Отличие от unit-тестов

| Unit-тесты | Интеграционные тесты |
| ---------- | -------------------- |
| In-memory SQLite | Реальный файл БД |
| Изолированные функции | Взаимодействие компонентов |
| Быстрые (< 1 сек) | Медленнее (1-5 сек) |
| Моки внешних зависимостей | Реальные зависимости |

---

## 🎯 Сценарии тестирования

### 1. Пустая база данных

**ID:** `IT-001`

**Описание:** Проверка поведения приложения при пустой базе данных.

**Предусловия:**
- БД существует, но не содержит записей

**Тест:**
```python
def test_empty_database_homepage():
    """Главная страница отображает сообщение при пустой БД."""
    # Arrange: БД пуста
    with app.app_context():
        db.session.query(Manager).delete()
        db.session.query(Country).delete()
        db.session.commit()
    
    # Act
    response = client.get('/')
    
    # Assert
    assert response.status_code == 200
    assert "Рейтинг пуст" in response.data.decode()
    # ИЛИ таблица отображается с сообщением "Нет данных"
```

**Ожидаемый результат:** Страница загружается, отображается сообщение об отсутствии данных.

---

### 2. Массовая загрузка данных

**ID:** `IT-002`

**Описание:** Проверка производительности при загрузке большого количества записей.

**Предусловия:**
- БД содержит 100+ менеджеров с достижениями

**Тест:**
```python
def test_bulk_load_performance():
    """Время загрузки рейтинга с большим количеством записей."""
    # Arrange: 100 менеджеров с достижениями
    with app.app_context():
        for i in range(100):
            country = Country(code=f"COD{i}", flag_path="/static/img/flags/test.png")
            db.session.add(country)
        db.session.commit()
        
        for i in range(100):
            manager = Manager(name=f"Manager {i}", country_id=i+1)
            db.session.add(manager)
        db.session.commit()
        
        for i in range(100):
            for j in range(5):  # 5 достижений на менеджера
                achievement = Achievement(
                    achievement_type="TOP1",
                    league="1",
                    season="24/25",
                    title="TOP1",
                    icon_path="/static/img/cups/top1.svg",
                    manager_id=i+1
                )
                db.session.add(achievement)
        db.session.commit()
    
    # Act: Замер времени загрузки
    import time
    start = time.time()
    response = client.get('/')
    elapsed = time.time() - start
    
    # Assert
    assert response.status_code == 200
    assert elapsed < 2.0  # Загрузка < 2 секунд
```

**Ожидаемый результат:** Страница загружается менее чем за 2 секунды.

---

### 3. Транзакции и откат

**ID:** `IT-003`

**Описание:** Проверка корректности транзакций и отката при ошибках.

**Предусловия:**
- БД инициализирована

**Тест:**
```python
def test_transaction_rollback():
    """Откат транзакции при ошибке."""
    # Arrange
    initial_count = db.session.query(Manager).count()
    
    # Act: Попытка создать менеджера с дублирующимся именем
    try:
        with db.session.begin():
            db.session.add(Manager(name="Duplicate", country_id=1))
            db.session.add(Manager(name="Duplicate", country_id=1))  # Ошибка unique constraint
    except Exception:
        pass  # Ожидаемая ошибка
    
    # Assert: Количество менеджеров не изменилось
    final_count = db.session.query(Manager).count()
    assert initial_count == final_count
```

**Ожидаемый результат:** Транзакция откатывается, данные не изменяются.

---

### 4. Конкурентный доступ

**ID:** `IT-004`

**Описание:** Проверка поведения при одновременных запросах.

**Предусловия:**
- БД содержит данные

**Тест:**
```python
def test_concurrent_requests():
    """Обработка одновременных запросов."""
    import threading
    
    results = []
    
    def make_request():
        response = client.get('/')
        results.append(response.status_code)
    
    # Act: 10 одновременных запросов
    threads = [threading.Thread(target=make_request) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Assert: Все запросы успешны
    assert all(code == 200 for code in results)
```

**Ожидаемый результат:** Все запросы обрабатываются успешно.

---

### 5. API: CRUD операции

**ID:** `IT-005`

**Описание:** Полный цикл CRUD операций через API.

**Предусловия:**
- БД инициализирована

**Тест:**
```python
def test_api_crud_cycle():
    """Полный цикл CRUD через API."""
    # Create
    response = client.post('/api/managers', json={
        "name": "Test Manager",
        "country_id": 1
    })
    assert response.status_code == 201
    manager_id = response.get_json()['id']
    
    # Read
    response = client.get(f'/api/managers/{manager_id}')
    assert response.status_code == 200
    assert response.get_json()['name'] == "Test Manager"
    
    # Update
    response = client.put(f'/api/managers/{manager_id}', json={
        "name": "Updated Manager"
    })
    assert response.status_code == 200
    
    # Delete
    response = client.delete(f'/api/managers/{manager_id}')
    assert response.status_code == 200
    
    # Verify deletion
    response = client.get(f'/api/managers/{manager_id}')
    assert response.status_code == 404
```

**Ожидаемый результат:** Все CRUD операции работают корректно.

---

### 6. Валидация данных

**ID:** `IT-006`

**Описание:** Проверка валидации данных перед записью в БД.

**Тест:**
```python
def test_data_validation():
    """Валидация данных перед записью."""
    # Пустое имя
    response = client.post('/api/managers', json={
        "name": "",
        "country_id": 1
    })
    assert response.status_code == 400
    
    # Несуществующий country_id
    response = client.post('/api/managers', json={
        "name": "Test",
        "country_id": 9999
    })
    assert response.status_code == 400
    
    # Дублирующееся имя
    client.post('/api/managers', json={
        "name": "Duplicate",
        "country_id": 1
    })
    response = client.post('/api/managers', json={
        "name": "Duplicate",
        "country_id": 1
    })
    assert response.status_code == 409
```

**Ожидаемый результат:** Некорректные данные отклоняются.

---

### 7. Расчёт очков (rating_service)

**ID:** `IT-007`

**Описание:** Интеграция rating_service с реальной БД.

**Тест:**
```python
def test_rating_calculation_integration():
    """Расчёт очков с реальной БД."""
    from services.rating_service import build_leaderboard
    
    # Arrange: Менеджер с известными достижениями
    with app.app_context():
        country = Country(code="TST", flag_path="/static/img/flags/test.png")
        db.session.add(country)
        db.session.commit()
        
        manager = Manager(name="Rating Test", country_id=country.id)
        db.session.add(manager)
        db.session.commit()
        
        # TOP1 s24/25 (800 × 1.00 = 800)
        db.session.add(Achievement(
            achievement_type="TOP1", league="1", season="24/25",
            title="TOP1", icon_path="/static/img/cups/top1.svg",
            manager_id=manager.id
        ))
        # TOP2 s23/24 (550 × 0.95 = 522.5 → 523)
        db.session.add(Achievement(
            achievement_type="TOP2", league="1", season="23/24",
            title="TOP2", icon_path="/static/img/cups/top2.svg",
            manager_id=manager.id
        ))
        db.session.commit()
    
    # Act
    leaderboard = build_leaderboard(db.session)
    
    # Assert
    test_entry = next(e for e in leaderboard if e['name'] == 'Rating Test')
    assert test_entry['total'] == 1323  # 800 + 523
```

**Ожидаемый результат:** Очки рассчитываются корректно.

---

### 8. Обработка ошибок БД

**ID:** `IT-008`

**Описание:** Проверка обработки ошибок подключения к БД.

**Тест:**
```python
def test_database_error_handling():
    """Обработка ошибок БД."""
    # Simulate database error by closing connection
    with app.app_context():
        db.session.close()
        
        # Attempt to query
        response = client.get('/')
        
        # Should return 500 with user-friendly message
        assert response.status_code == 500
        assert "ошибка" in response.data.decode().lower()
```

**Ожидаемый результат:** Ошибка обрабатывается, пользователь видит понятное сообщение.

---

### 9. Миграции Alembic

**ID:** `IT-009`

**Описание:** Проверка применения миграций.

**Предусловия:**
- Есть новая миграция

**Тест:**
```bash
# В консоли
alembic downgrade base  # Откат к чистой БД
alembic upgrade head    # Применение всех миграций
python -m unittest tests.py  # Проверка работы
```

**Ожидаемый результат:** Миграции применяются без ошибок.

---

### 10. Сценарий "Удаление менеджера"

**ID:** `IT-010`

**Описание:** Проверка каскадного удаления достижений.

**Тест:**
```python
def test_manager_delete_cascade():
    """Каскадное удаление достижений при удалении менеджера."""
    # Arrange: Менеджер с достижениями
    with app.app_context():
        country = Country(code="DEL", flag_path="/static/img/flags/test.png")
        db.session.add(country)
        db.session.commit()
        
        manager = Manager(name="Delete Test", country_id=country.id)
        db.session.add(manager)
        db.session.commit()
        
        manager_id = manager.id
        
        achievement = Achievement(
            achievement_type="TOP1", league="1", season="24/25",
            title="TOP1", icon_path="/static/img/cups/top1.svg",
            manager_id=manager_id
        )
        db.session.add(achievement)
        db.session.commit()
        
        # Count achievements before
        before_count = db.session.query(Achievement).filter_by(manager_id=manager_id).count()
        assert before_count == 1
    
    # Act: Удаление менеджера через API
    response = client.delete(f'/api/managers/{manager_id}')
    assert response.status_code == 200
    
    # Assert: Достижения удалены (CASCADE)
    with app.app_context():
        after_count = db.session.query(Achievement).filter_by(manager_id=manager_id).count()
        assert after_count == 0
```

**Ожидаемый результат:** Достижения удаляются каскадно.

---

## 📊 Узкие места (Bottlenecks)

### Выявленные потенциальные проблемы:

| # | Проблема | Влияние | Решение |
| - | -------- | ------- | ------- |
| 1 | N+1 запросы при загрузке менеджеров | Высокое | ✅ `joinedload` в rating_service.py |
| 2 | Отсутствие индексов на `achievements.manager_id` | Среднее | Проверить индексы |
| 3 | Блокировки при записи в SQLite | Низкое | Использовать WAL режим |
| 4 | Нет кэширования leaderboard | Среднее | Добавить кэш на 1-5 мин |
| 5 | Синхронная загрузка статики | Низкое | CDN для статики |

### Проверка индексов:

```sql
-- В SQLite консоли
.schema achievements
-- Ожидаемый результат: индексы на manager_id, achievement_type, league, season
```

### Рекомендации по оптимизации:

1. **Кэширование:** Добавить Redis или Flask-Caching для leaderboard
2. **Пагинация API:** Ограничить количество записей в API ответах
3. **Асинхронность:** Для тяжёлых операций использовать Celery
4. **Мониторинг:** Добавить логирование медленных запросов

---

## 🚀 Запуск интеграционных тестов

### Команды:

```bash
# Запуск всех интеграционных тестов
python -m unittest tests_integration.py -v

# Запуск конкретного теста
python -m unittest tests_integration.TestDatabaseScenarios.test_empty_database -v

# Запуск с покрытием
coverage run --source=. -m unittest tests_integration.py
coverage report
```

### Требования:

- Python 3.10+
- SQLite
- Flask тестовое окружение

---

## 📝 Статус выполнения

| ID | Сценарий | Статус | Примечание |
| -- | -------- | ------ | ---------- |
| IT-001 | Пустая БД | 🔄 В работе | Требуется обработка в app.py |
| IT-002 | Массовая загрузка | ⏳ Ожидает | |
| IT-003 | Транзакции | ⏳ Ожидает | |
| IT-004 | Конкурентный доступ | ⏳ Ожидает | |
| IT-005 | API CRUD | ⏳ Ожидает | |
| IT-006 | Валидация | ⏳ Ожидает | |
| IT-007 | Расчёт очков | ⏳ Ожидает | |
| IT-008 | Обработка ошибок | 🔄 В работе | Требуется обработка в app.py |
| IT-009 | Миграции | ⏳ Ожидает | |
| IT-010 | Каскадное удаление | ⏳ Ожидает | |

**Легенда:**
- ✅ Выполнено
- 🔄 В работе
- ⏳ Ожидает

---

**Последнее обновление:** 30 марта 2026 г.
**Версия документа:** 1.0
