# 🛠 Руководство по устранению неполадок

**Цель:** Быстрое решение распространённых проблем в Shadow Hockey League.

**Последнее обновление:** 30 марта 2026 г.

---

## 📋 Оглавление

1. [Ошибки базы данных](#ошибки-базы-данных)
2. [Ошибки приложения](#ошибки-приложения)
3. [Проблемы со статикой](#проблемы-со-статикой)
4. [Проблемы с тестами](#проблемы-с-тестами)
5. [Проблемы деплоя](#проблемы-деплоя)

---

## Ошибки базы данных

### ❌ Ошибка: "no such table: managers"

**Симптомы:**
- Страница 500 с ошибкой `OperationalError`
- В логах: `sqlite3.OperationalError: no such table: managers`

**Причины:**
1. База данных не инициализирована
2. Несоответствие пути к БД в конфигурации
3. Файл БД повреждён

**Решение:**

```bash
# 1. Проверить наличие файла БД
ls -la dev.db

# 2. Переинициализировать БД (данные будут удалены!)
rm dev.db
python seed_db.py

# 3. Проверить путь в .env
cat .env | grep DATABASE_URL

# 4. Проверить путь в alembic.ini
cat alembic.ini | grep sqlalchemy.url
```

**Профилактика:**
- Убедитесь, что `DATABASE_URL` в `.env` и `sqlalchemy.url` в `alembic.ini` совпадают
- Всегда запускайте `python seed_db.py` после создания новой БД

---

### ❌ Ошибка: "Database is locked"

**Симптомы:**
- Запросы выполняются медленно или таймаут
- В логах: `sqlite3.OperationalError: database is locked`

**Причины:**
1. Несколько процессов пытаются записать в БД одновременно
2. Транзакция не закрыта
3. SQLite WAL режим не включён

**Решение:**

```bash
# 1. Завершить зависшие процессы
ps aux | grep python
kill <PID>

# 2. Включить WAL режим для SQLite
sqlite3 dev.db "PRAGMA journal_mode=WAL;"

# 3. Проверить активные транзакции
sqlite3 dev.db "SELECT * FROM sqlite_master WHERE type='table';"
```

**Профилактика:**
- Используйте `with db.session.begin()` для всех транзакций
- В production рассмотрите переход на PostgreSQL

---

### ❌ Ошибка: "FOREIGN KEY constraint failed"

**Симптомы:**
- Ошибка при создании/удалении менеджера или достижения
- В логах: `sqlalchemy.exc.IntegrityError: FOREIGN KEY constraint failed`

**Причины:**
1. Попытка создать достижение для несуществующего менеджера
2. Попытка удалить страну, у которой есть менеджеры
3. FK ограничения включены, но данные некорректны

**Решение:**

```bash
# 1. Проверить целостность БД
sqlite3 dev.db "PRAGMA integrity_check;"

# 2. Проверить orphaned записи
sqlite3 dev.db "SELECT * FROM achievements WHERE manager_id NOT IN (SELECT id FROM managers);"

# 3. Исправить или удалить проблемные записи
sqlite3 dev.db "DELETE FROM achievements WHERE manager_id NOT IN (SELECT id FROM managers);"
```

**Профилактика:**
- Всегда создавайте страну перед менеджером
- Используйте каскадное удаление (`cascade="all, delete-orphan"`)

---

## Ошибки приложения

### ❌ Ошибка 500: "Error building leaderboard"

**Симптомы:**
- Страница 500 с сообщением об ошибке
- В логах: `Error building leaderboard: ...`

**Причины:**
1. Ошибка в `rating_service.py`
2. Некорректные данные в БД
3. Ошибка шаблона Jinja2

**Решение:**

```bash
# 1. Проверить логи с полным traceback
tail -100 /var/log/YOUR_USERNAME.pythonanywhere.com/error.log

# 2. Запустить тесты
python -m unittest tests.py -v

# 3. Проверить данные в БД
python -c "
from app import create_app
from models import db, Manager
app = create_app()
with app.app_context():
    print('Managers:', db.session.query(Manager).count())
"
```

---

### ❌ Ошибка 404: "Страница не найдена"

**Симптомы:**
- Страница 404 при доступе к `/` или `/rating`

**Причины:**
1. Маршруты не зарегистрированы
2. WSGI настроен неправильно
3. Приложение не перезапущено

**Решение:**

```bash
# 1. Проверить регистрацию маршрутов
python -c "
from app import create_app
app = create_app()
print('Routes:', [rule.rule for rule in app.url_map.iter_rules()])
"

# 2. Проверить WSGI файл
cat /var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py

# 3. Перезапустить приложение (кнопка Reload в веб-интерфейсе)
```

---

### ❌ Ошибка: "Working outside of application context"

**Симптомы:**
- Ошибка при запуске скриптов
- `RuntimeError: Working outside of application context`

**Причины:**
1. Прямой вызов `db.session` без контекста приложения
2. Скрипт не создаёт приложение правильно

**Решение:**

```python
# Неправильно:
from models import db
db.session.query(...)

# Правильно:
from app import create_app
from models import db

app = create_app()
with app.app_context():
    db.session.query(...)
```

---

## Проблемы со статикой

### ❌ Статика не загружается (404)

**Симптомы:**
- CSS/JS/изображения не загружаются
- В консоли браузера: `404 Not Found` для `/static/...`

**Причины:**
1. Неправильный путь в настройках PythonAnywhere
2. Файлы отсутствуют на сервере
3. Проблемы с правами доступа

**Решение:**

```bash
# 1. Проверить наличие файлов
ls -la /home/YOUR_USERNAME/shadow-hockey-league/static/

# 2. Проверить настройки в PythonAnywhere:
#    Web → Static files
#    URL: /static/
#    Directory: /home/YOUR_USERNAME/shadow-hockey-league/static/

# 3. Проверить права доступа
chmod -R 755 /home/YOUR_USERNAME/shadow-hockey-league/static/
```

---

### ❌ CSS не применяется

**Симптомы:**
- Страница загружается, но без стилей
- CSS файл загружается (статус 200)

**Причины:**
1. Неправильный MIME тип
2. Кэш браузера
3. Ошибка в CSS файле

**Решение:**

```bash
# 1. Проверить MIME тип в логах
grep "static/css" /var/log/YOUR_USERNAME.pythonanywhere.com/server.log

# 2. Очистить кэш браузера (Ctrl+Shift+R)

# 3. Проверить CSS на синтаксические ошибки
#    https://jigsaw.w3.org/css-validator/
```

---

## Проблемы с тестами

### ❌ Тесты не проходят: "no such table"

**Симптомы:**
- Тесты падают с `OperationalError: no such table`
- Unit тесты работают, интеграционные нет

**Причины:**
1. Тесты используют in-memory БД, но ожидается файл
2. `db.create_all()` не вызывается в `setUp`

**Решение:**

```python
# Проверить setUp метод:
def setUp(self) -> None:
    self.app = create_app("config.TestingConfig")
    self.client = self.app.test_client()
    
    with self.app.app_context():
        db.create_all()  # Должно быть!
```

---

### ❌ Тесты не проходят: "AssertionError"

**Симптомы:**
- Тесты падают с несоответствием ожидаемых значений
- Например: `AssertionError: 1322 != 1323`

**Причины:**
1. Округление в Python (banker's rounding)
2. Изменения в бизнес-логике
3. Устаревшие тесты

**Решение:**

```python
# Проверить расчёты вручную:
# 550 × 0.95 = 522.5 → 522 (banker's rounding: round to even)

# Обновить тест с правильным значением:
self.assertEqual(result['total'], 522)  # Было 523
```

---

## Проблемы деплоя

### ❌ Приложение не загружается после деплоя

**Симптомы:**
- Страница 500 или 404 после деплоя
- Логи пустые или с ошибками

**Причины:**
1. Зависимости не установлены
2. Переменные окружения не заданы
3. WSGI настроен неправильно

**Решение:**

```bash
# 1. Проверить зависимости
source /home/YOUR_USERNAME/.venvs/shadow-hockey-league/bin/activate
pip list | grep Flask

# 2. Проверить переменные окружения
#    PythonAnywhere → Web → Environment variables
#    Должны быть: FLASK_ENV, SECRET_KEY, DATABASE_URL

# 3. Проверить WSGI
cat /var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py

# 4. Перезапустить приложение
#    PythonAnywhere → Web → Reload
```

---

### ❌ API возвращает 404

**Симптомы:**
- `/api/managers` и другие endpoints возвращают 404

**Причины:**
1. API отключено в production (`ENABLE_API=False`)
2. Blueprint не зарегистрирован

**Решение:**

```bash
# 1. Проверить ENABLE_API
echo $ENABLE_API

# 2. Если нужно включить (не рекомендуется):
#    PythonAnywhere → Web → Environment variables
#    Добавить: ENABLE_API=True
#    Reload приложение

# 3. Проверить регистрацию blueprint
python -c "
from app import create_app
app = create_app()
print('Blueprints:', list(app.blueprints.keys()))
"
```

**Важно:** В production API должно быть отключено или защищено аутентификацией!

---

### ❌ Ошибка: "ImportError: No module named 'app'"

**Симптомы:**
- Ошибка в логах WSGI
- Приложение не запускается

**Причины:**
1. Неправильный путь в WSGI
2. Виртуальное окружение не активировано
3. Файлы не загружены на сервер

**Решение:**

```bash
# 1. Проверить путь в WSGI
cat /var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py
# Должно быть:
# project_home = '/home/YOUR_USERNAME/shadow-hockey-league'

# 2. Проверить наличие файлов
ls -la /home/YOUR_USERNAME/shadow-hockey-league/app.py

# 3. Проверить виртуальное окружение
source /home/YOUR_USERNAME/.venvs/shadow-hockey-league/bin/activate
python -c "import app; print('OK')"
```

---

## 📊 Диагностика

### Команды для быстрой диагностики:

```bash
# Проверка состояния приложения
curl -I https://YOUR_USERNAME.pythonanywhere.com/

# Проверка health endpoint
curl https://YOUR_USERNAME.pythonanywhere.com/health

# Проверка логов в реальном времени
tail -f /var/log/YOUR_USERNAME.pythonanywhere.com/error.log

# Проверка размера БД
du -h /home/YOUR_USERNAME/shadow-hockey-league/dev.db

# Проверка количества записей
sqlite3 dev.db "SELECT 'Managers:', COUNT(*) FROM managers UNION ALL SELECT 'Countries:', COUNT(*) FROM countries UNION ALL SELECT 'Achievements:', COUNT(*) FROM achievements;"
```

---

## 📞 Поддержка

Если проблема не решена:

1. **Проверьте логи** — 90% проблем видны в error.log
2. **Поищите в документации** — README.md, docs/*.md
3. **Запустите тесты** — `python -m unittest discover -v`
4. **Проверьте статус PythonAnywhere** — https://status.pythonanywhere.com/
5. **Обратитесь в поддержку PythonAnywhere** — для проблем с хостингом

---

## 📝 Чеклист быстрой диагностики

При возникновении проблемы:

- [ ] Проверить логи ошибок
- [ ] Проверить логи сервера
- [ ] Запустить тесты
- [ ] Проверить переменные окружения
- [ ] Проверить наличие файлов БД
- [ ] Проверить права доступа
- [ ] Перезапустить приложение

---

**Последнее обновление:** 30 марта 2026 г.
**Версия документа:** 1.0
