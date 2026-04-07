# 🔧 Technical Specification

**Проект:** Shadow Hockey League v2  
**Версия:** 1.0  
**Дата:** 2 апреля 2026 г.  
**Статус:** ✅ Production

---

## 1. Архитектура системы

### 1.1 Общая схема

```
┌─────────────────┐
│     Client      │
│   (Web Browser) │
└────────┬────────
         │ HTTPS
         ▼
┌─────────────────────────────────┐
│   Nginx (Reverse Proxy + SSL)   │
│   - Port 443 (HTTPS)            │
│   - Port 80 (HTTP → HTTPS)      │
│   - Static files                │
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
│   - app.py (Application Factory)│
│   - services/* (Business Logic) │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│   SQLite Database               │
│   - /path/to/dev.db             │
│   - Alembic Migrations          │
└─────────────────────────────────┘
```

### 1.2 Компоненты

| Компонент      | Технология          | Версия        | Назначение           |
| -------------- | ------------------- | ------------- | -------------------- |
| **OS**         | Ubuntu Server       | 22.04 LTS     | Операционная система |
| **Web Server** | Nginx               | 1.18.0        | Reverse proxy, SSL   |
| **WSGI**       | Gunicorn            | 20.1.0        | Application server   |
| **Language**   | Python              | 3.10+         | Язык разработки      |
| **Framework**  | Flask               | 3.1+          | Web framework        |
| **ORM**        | SQLAlchemy          | 2.0+          | Database ORM         |
| **Database**   | SQLite              | 3.x           | Реляционная БД       |
| **Cache**      | Redis / SimpleCache | 6+ / built-in | Кэширование          |
| **Migrations** | Alembic             | 1.14+         | Миграции БД          |
| **Admin**      | Flask-Admin         | 2.0+          | Админ-панель         |
| **Auth**       | Flask-Login         | 0.6+          | Аутентификация       |
| **Metrics**    | Prometheus Exporter | 0.23+         | Экспорт метрик       |

---

## 2. Модель данных

### 2.1 Схема БД

```sql
-- Countries: справочник стран
CREATE TABLE countries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(3) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL DEFAULT 'Unknown',
    flag_path VARCHAR(100) NOT NULL
);

-- Managers: участники лиги
CREATE TABLE managers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    country_id INTEGER NOT NULL,
    FOREIGN KEY (country_id) REFERENCES countries(id) ON DELETE RESTRICT
);

-- Achievements: достижения менеджеров
CREATE TABLE achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    achievement_type VARCHAR(20) NOT NULL,
    league VARCHAR(10) NOT NULL,
    season VARCHAR(10) NOT NULL,
    title VARCHAR(100) NOT NULL,
    icon_path VARCHAR(100) NOT NULL,
    manager_id INTEGER NOT NULL,
    FOREIGN KEY (manager_id) REFERENCES managers(id) ON DELETE CASCADE,
    UNIQUE(manager_id, league, season, achievement_type)
);

-- Admin Users: пользователи админ-панели
CREATE TABLE admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL
);

-- Индексы
CREATE INDEX idx_countries_code ON countries(code);
CREATE INDEX idx_managers_name ON managers(name);
CREATE INDEX idx_managers_country ON managers(country_id);
CREATE INDEX idx_achievements_type ON achievements(achievement_type);
CREATE INDEX idx_achievements_league ON achievements(league);
CREATE INDEX idx_achievements_season ON achievements(season);
CREATE INDEX idx_achievements_manager ON achievements(manager_id);
CREATE INDEX idx_admin_users_username ON admin_users(username);
```

### 2.2 SQLAlchemy модели

#### Country

```python
class Country(db.Model):
    __tablename__ = "countries"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(3), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, default="Unknown")
    flag_path = db.Column(db.String(100), nullable=False)
    managers = db.relationship("Manager", backref="country", lazy="select")
```

#### Manager

```python
class Manager(db.Model):
    __tablename__ = "managers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    country_id = db.Column(
        db.Integer,
        db.ForeignKey("countries.id", ondelete="RESTRICT"),
        nullable=False
    )
    achievements = db.relationship(
        "Achievement",
        backref="manager",
        lazy="select",
        cascade="all, delete-orphan"
    )

    @property
    def is_tandem(self) -> bool:
        return self.name.startswith("Tandem:") or "," in self.name

    @property
    def display_name(self) -> str:
        if self.name.startswith("Tandem:"):
            return self.name[7:].strip()
        return self.name
```

#### Achievement

```python
class Achievement(db.Model):
    __tablename__ = "achievements"
    __table_args__ = (
        UniqueConstraint(
            "manager_id", "league", "season", "achievement_type",
            name="uq_achievement_manager_league_season_type"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    achievement_type = db.Column(db.String(20), nullable=False, index=True)
    league = db.Column(db.String(10), nullable=False, index=True)
    season = db.Column(db.String(10), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    icon_path = db.Column(db.String(100), nullable=False)
    manager_id = db.Column(
        db.Integer,
        db.ForeignKey("managers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
```

#### AdminUser

```python
class AdminUser(db.Model, UserMixin):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
```

---

## 3. Формула расчёта очков

### 3.1 Базовые очки

| Достижение   | Лига 1 | Лига 2 |
| ------------ | ------ | ------ |
| TOP1         | 800    | 300    |
| TOP2         | 550    | 200    |
| TOP3         | 450    | 100    |
| Best regular | 50     | 40     |
| Round 3      | 30     | 20     |
| Round 1      | 10     | 5      |

### 3.2 Множители сезонов

| Сезон | Множитель       |
| ----- | --------------- |
| 25/26 | ×1.00 (базовый) |
| 24/25 | ×0.95 (-5%)     |
| 23/24 | ×0.90 (-10%)    |
| 22/23 | ×0.85 (-15%)    |
| 21/22 | ×0.80 (-20%)    |

### 3.3 Формула

```
Очки = Σ(Базовые_очки × Множитель_сезона)
```

**Пример:**

- Менеджер имеет TOP1 в Лиге 1 за сезон 23/24
- Расчёт: 800 × 0.95 = 760 очков

---

## 4. API Endpoints

### 4.1 Публичные endpoints

| Endpoint   | Method | Описание                   | Auth |
| ---------- | ------ | -------------------------- | ---- |
| `/`        | GET    | Главная страница (рейтинг) | No   |
| `/health`  | GET    | Health check               | No   |
| `/metrics` | GET    | Prometheus метрики         | No   |

### 4.2 Админ-панель

| Endpoint              | Method              | Описание        | Auth |
| --------------------- | ------------------- | --------------- | ---- |
| `/admin/`             | GET                 | Главная админки | Yes  |
| `/admin/login`        | GET/POST            | Вход            | No   |
| `/admin/logout`       | GET                 | Выход           | Yes  |
| `/admin/country/`     | GET/POST/PUT/DELETE | CRUD стран      | Yes  |
| `/admin/manager/`     | GET/POST/PUT/DELETE | CRUD менеджеров | Yes  |
| `/admin/achievement/` | GET/POST/PUT/DELETE | CRUD достижений | Yes  |
| `/admin/adminuser/`   | GET/POST/PUT/DELETE | CRUD админов    | Yes  |

### 4.3 REST API (включено в production с auth)

| Endpoint            | Method              | Описание        | Статус     |
| ------------------- | ------------------- | --------------- | ---------- |
| `/api/countries`    | GET                 | Список стран    | ✅ Enabled |
| `/api/managers`     | GET                 | Список менеджеров | ✅ Enabled |
| `/api/achievements` | GET                 | Список достижений | ✅ Enabled |

**Authentication:** API Key с scopes (`read`, `write`, `admin`)
**Rate Limiting:** 100 запросов/мин на ключ
**Pagination:** `page`/`per_page` (max 100)

**Cache Invalidation:** Все API endpoints (CREATE/UPDATE/DELETE) автоматически инвалидируют кэш leaderboard.

**Unique Constraint:** `POST /api/achievements` возвращает `409 Conflict` при попытке создать дубликат (same manager_id, league, season, achievement_type).

**Audit Log:** Все мутации логируются в AuditLog.

---

## 5. Конфигурация

### 5.1 Переменные окружения (.env)

```bash
# Режим работы
FLASK_ENV=production

# База данных
DATABASE_URL=sqlite:///dev.db

# Безопасность
SECRET_KEY=<random-secret-key>

# Логирование
LOG_LEVEL=INFO

# Redis (опционально)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# API
ENABLE_API=false
```

### 5.2 Конфигурация Flask

```python
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # Caching
    CACHE_TYPE = "RedisCache"  # или "SimpleCache"
    CACHE_REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    CACHE_REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
    CACHE_DEFAULT_TIMEOUT = 300  # 5 минут
```

---

## 6. Деплой

### 6.1 Требования к серверу

| Ресурс | Минимум      | Рекомендуется    |
| ------ | ------------ | ---------------- |
| CPU    | 1 ядро       | 2 ядра           |
| RAM    | 512 MB       | 1 GB             |
| Disk   | 5 GB         | 10 GB            |
| OS     | Ubuntu 20.04 | Ubuntu 22.04 LTS |

### 6.2 Установка

```bash
# Клонирование репозитория
git clone https://github.com/amatjkay/shadow-hockey-league_v2.git
cd shadow-hockey-league_v2

# Виртуальное окружение
python -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Инициализация БД
alembic upgrade head
python seed_db.py

# Создание админа
python scripts/create_admin.py

# Настройка .env
cp .env.example .env
nano .env  # отредактировать значения
```

### 6.3 Nginx конфигурация

```nginx
server {
    listen 80;
    server_name shadow-hockey-league.ru;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/shadow-hockey-league_v2/static;
    }
}
```

### 6.4 Gunicorn systemd service

```ini
[Unit]
Description=Shadow Hockey League Gunicorn
After=network.target

[Service]
User=shleague
Group=www-data
WorkingDirectory=/home/shleague/shadow-hockey-league_v2
ExecStart=/home/shleague/shadow-hockey-league_v2/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    app:app

[Install]
WantedBy=multi-user.target
```

---

## 7. Мониторинг

### 7.1 Health Check

**Endpoint:** `GET /health`

**Ответ:**

```json
{
  "status": "healthy",
  "timestamp": "2026-04-02T12:00:00Z",
  "uptime_seconds": 3600,
  "managers_count": 50,
  "achievements_count": 200,
  "countries_count": 8,
  "response_time_ms": 15,
  "redis_status": "connected",
  "cache_status": "working",
  "database_status": "connected",
  "database_size_mb": 2.5
}
```

### 7.2 Prometheus метрики

**Endpoint:** `GET /metrics`

**Метрики:**

- `shadow_hockey_league_http_requests_total` — всего запросов
- `shadow_hockey_league_http_request_duration_seconds` — время ответа
- `shadow_hockey_league_http_requests_in_progress` — запросов в обработке

### 7.3 VPS мониторинг

| Метрика | Источник      | Нормальное значение |
| ------- | ------------- | ------------------- |
| CPU     | ztv.su панель | < 50%               |
| RAM     | ztv.su панель | < 800 MB            |
| Disk    | ztv.su панель | < 8 GB              |
| Uptime  | /health       | > 99%               |

---

## 8. Бэкапы

### 8.1 Автоматические бэкапы

**Скрипт:** `/backup/backup.sh`

```bash
#!/bin/bash
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR=/backup
DB_FILE=/home/shleague/shadow-hockey-league_v2/dev.db

# Создаём бэкап
gzip -c $DB_FILE > $BACKUP_DIR/dev.db-$DATE.gz

# Удаляем старые бэкапы (> 7 дней)
find $BACKUP_DIR -name "dev.db-*" -mtime +7 -delete
```

**Cron:** Ежедневно в 3:00

```bash
0 3 * * * /home/shleague/shadow-hockey-league_v2/backup/backup.sh
```

### 8.2 Восстановление из бэкапа

```bash
# Остановить приложение
systemctl stop shadow-hockey-league

# Восстановить БД
gunzip -c /backup/dev.db-20260402-030000.gz > /home/shleague/shadow-hockey-league_v2/dev.db

# Запустить приложение
systemctl start shadow-hockey-league
```

---

## 9. Безопасность

### 9.1 Security headers

```python
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
```

### 9.2 SSL/TLS

- **Provider:** Let's Encrypt
- **Auto-renewal:** Certbot (cron)
- **Min. TLS:** 1.2

### 9.3 Пароли

- **Хеширование:** Werkzeug (PBKDF2-SHA256)
- **Мин. длина:** 6 символов
- **Хранение:** Только хеш в БД

---

## 10. Тестирование

### 10.1 Запуск тестов

```bash
# Все тесты
python -m unittest discover -v

# С покрытием
coverage run --source=. -m unittest discover
coverage report
```

### 10.2 Типы тестов

| Тип                    | Файл                              | Покрытие                              |
| ---------------------- | --------------------------------- | ------------------------------------- |
| Unit                   | `tests.py`                        | Rating service, validation            |
| Integration            | `tests_integration.py`            | Routes, API, database, constraints    |
| Cache & Admin          | `tests_cache_and_admin.py`        | Cache invalidation, admin auth        |
| API Cache Invalidation | `tests_api_cache_invalidation.py` | API → cache invalidation, leaderboard |

**Всего тестов:** 239 (224 unit+integration + 15 E2E, покрытие ~87%)

---

## 11. Известные проблемы

| ID      | Проблема                               | Статус        | Workaround                   |
| ------- | -------------------------------------- | ------------- | ---------------------------- |
| BUG-001 | Login/Logout не в меню админки         | ✅ Решено     | Реализовано в v2.2.0         |
| BUG-002 | Нет заголовков страниц админки         | ✅ Решено     | Реализовано в v2.2.0         |
| BUG-003 | Выбор флага требует ручного ввода пути | ✅ Решено     | Выпадающий список реализован |

---

**Документ актуализирован:** 7 апреля 2026 г.
**Следующий пересмотр:** При изменении архитектуры
