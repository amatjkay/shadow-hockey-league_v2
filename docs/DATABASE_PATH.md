# 🗄️ Database Path Configuration

## Проблема

Flask-SQLAlchemy по умолчанию создаёт SQLite базу данных в папке `instance/`, если путь к БД не является абсолютным.

### Симптомы

- В БД `instance/shadow_league.db` только тестовые данные
- В БД `dev.db` все реальные данные
- Приложение показывает только тестового менеджера

### Причина

1. **Относительный путь в `.env`**: `DATABASE_URL=sqlite:///dev.db`
2. **Flask instance_relative_config**: По умолчанию Flask создаёт папку `instance/` для хранения данных

## Решение

### 1. Используйте абсолютный путь в `.env`

**Windows:**
```env
DATABASE_URL=sqlite:///C:/dev/shadow/shadow-hockey-league_v2/dev.db
```

**Linux/Mac:**
```env
DATABASE_URL=sqlite:////home/user/projects/shadow-hockey-league_v2/dev.db
```

**PythonAnywhere:**
```env
DATABASE_URL=sqlite:////home/amatjkay/shadow-hockey-league_v2/dev.db
```

### 2. Отключите instance_relative_config в app.py

```python
# app.py
app = Flask(__name__, instance_relative_config=False)
```

### 3. Удалите старую БД

```bash
# Windows
del instance\shadow_league.db
rmdir instance

# Linux/Mac
rm -rf instance/
```

## Проверка

Запустите скрипт для проверки:

```bash
python check_db.py
```

Ожидаемый результат:
- Countries: 8
- Managers: 42
- Achievements: 49

## Профилактика

1. **Всегда используйте абсолютные пути** в `.env`
2. **Проверьте `.env.example`** — там должен быть пример с абсолютным путём
3. **Добавьте `instance/` в `.gitignore`** (уже сделано)

## Ссылки

- [Flask-SQLAlchemy Configuration](https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/config/)
- [Flask Instance Applications](https://flask.palletsprojects.com/en/3.0.x/patterns/appfact/#instance-applications)
