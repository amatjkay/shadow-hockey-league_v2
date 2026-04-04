# 🚀 Migration Guide — Деплой Shadow Hockey League v2

**Версия:** 1.0
**Дата:** 3 апреля 2026 г.
**Цель:** Пошаговая инструкция для развёртывания приложения на чистом VPS

---

## 📋 Оглавление

1. [Требования](#требования)
2. [Подготовка сервера](#подготовка-сервера)
3. [Установка зависимостей](#установка-зависимостей)
4. [Настройка приложения](#настройка-приложения)
5. [Настройка БД](#настройка-бд)
6. [Настройка Gunicorn](#настройка-gunicorn)
7. [Настройка Nginx](#настройка-nginx)
8. [Настройка HTTPS](#настройка-https)
9. [Настройка Redis](#настройка-redis)
10. [Настройка бэкапов](#настройка-бэкапов)
11. [Настройка CI/CD](#настройка-cicd)
12. [Финальная проверка](#финальная-проверка)
13. [Troubleshooting](#troubleshooting)

---

## Требования

### Минимальные

| Компонент | Значение |
|-----------|----------|
| ОС | Ubuntu 22.04 LTS |
| CPU | 1 ядро |
| RAM | 1 GB |
| Диск | 10 GB SSD |
| Сеть | 100 Mbps |

### Рекомендуемые

| Компонент | Значение |
|-----------|----------|
| ОС | Ubuntu 22.04 LTS |
| CPU | 2 ядра |
| RAM | 2 GB |
| Диск | 20 GB SSD |
| Сеть | 1 Gbps |

### Предварительные знания

- Базовое понимание Linux/SSH
- Умение работать с Git
- Основы Nginx и systemd

---

## Подготовка сервера

### 1. Подключение по SSH

```bash
ssh root@YOUR_SERVER_IP
```

### 2. Обновление системы

```bash
apt update && apt upgrade -y
```

### 3. Настройка часового пояса

```bash
timedatectl set-timezone Europe/Moscow
```

### 4. Создание пользователя для приложения

```bash
adduser --disabled-password --gecos "" shleague
usermod -aG sudo shleague
```

---

## Установка зависимостей

### 1. Системные пакеты

```bash
apt install -y nginx python3-pip python3-venv python3-dev \
             git curl wget build-essential redis-server
```

### 2. Проверка версий

```bash
python3 --version    # Должно быть 3.10+
nginx -v             # Должно быть 1.18+
redis-server --version  # Должно быть 6.0+
```

---

## Настройка приложения

### 1. Клонирование репозитория

```bash
su - shleague
git clone https://github.com/amatjkay/shadow-hockey-league_v2.git
cd shadow-hockey-league_v2
```

### 2. Виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### 3. Создание .env файла

```bash
# Генерация секретных ключей
SECRET_KEY=$(openssl rand -hex 32)
API_KEY_SECRET=$(openssl rand -hex 32)
WTF_CSRF_SECRET_KEY=$(openssl rand -hex 32)

# Создание .env
cat > .env << EOF
FLASK_ENV=production
DATABASE_URL=sqlite:////home/shleague/shadow-hockey-league_v2/instance/dev.db
SECRET_KEY=${SECRET_KEY}
API_KEY_SECRET=${API_KEY_SECRET}
WTF_CSRF_SECRET_KEY=${WTF_CSRF_SECRET_KEY}
LOG_LEVEL=INFO
ENABLE_API=True
REDIS_URL=redis://localhost:6379/0
EOF
```

> **Важно:** Сохраните значения секретных ключей! Они не подлежат восстановлению.

### 4. Создание директории для БД

```bash
mkdir -p /home/shleague/shadow-hockey-league_v2/instance
```

---

## Настройка БД

### 1. Инициализация базы данных

```bash
cd /home/shleague/shadow-hockey-league_v2
source venv/bin/activate

# Alembic миграции
alembic upgrade head

# Наполнение данными
python seed_db.py
```

### 2. Создание первого администратора

```bash
python scripts/create_admin.py
```

### 3. Проверка БД

```bash
python -c "
from app import create_app
app = create_app()
with app.app_context():
    from models import db, Country, Manager
    print(f'Countries: {db.session.query(Country).count()}')
    print(f'Managers: {db.session.query(Manager).count()}')
"
```

---

## Настройка Gunicorn

### 1. Создание systemd сервиса

```bash
# Выйти к root
exit

cat > /etc/systemd/system/shadow-hockey-league.service << 'EOF'
[Unit]
Description=Shadow Hockey League Flask Application
After=network.target

[Service]
User=shleague
Group=shleague
WorkingDirectory=/home/shleague/shadow-hockey-league_v2
Environment="PATH=/home/shleague/shadow-hockey-league_v2/venv/bin"
ExecStart=/home/shleague/shadow-hockey-league_v2/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    "app:create_app()"

# Restart policy
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
```

### 2. Запуск сервиса

```bash
systemctl daemon-reload
systemctl enable shadow-hockey-league
systemctl start shadow-hockey-league
systemctl status shadow-hockey-league
```

### 3. Проверка логов

```bash
journalctl -u shadow-hockey-league -f
```

---

## Настройка Nginx

### 1. Создание конфигура сайта

```bash
cat > /etc/nginx/sites-available/shadow-hockey-league << 'EOF'
server {
    listen 80;
    server_name YOUR_DOMAIN www.YOUR_DOMAIN;

    # Логи
    access_log /var/log/nginx/shleague-access.log;
    error_log /var/log/nginx/shleague-error.log;

    # Проксирование на Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Статические файлы
    location /static {
        alias /home/shleague/shadow-hockey-league_v2/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Флаги
    location /static/img/flags {
        alias /home/shleague/shadow-hockey-league_v2/static/img/flags;
        expires 30d;
    }
}
EOF
```

> **Замените** `YOUR_DOMAIN` на ваш домен (e.g., `shadow-hockey-league.ru`).

### 2. Активация сайта

```bash
ln -s /etc/nginx/sites-available/shadow-hockey-league /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl restart nginx
```

### 3. Настройка прав доступа

```bash
chmod 755 /home/shleague
chmod -R 755 /home/shleague/shadow-hockey-league_v2/static
```

---

## Настройка HTTPS

### 1. Установка Certbot

```bash
apt install -y certbot python3-certbot-nginx
```

### 2. Получение сертификата

```bash
certbot --nginx -d YOUR_DOMAIN -d www.YOUR_DOMAIN
```

Следуйте инструкциям:
- Введите email для уведомлений
- Примите условия (A)
- Откажитесь от рассылки (N)
- Выберите редирект HTTP → HTTPS (2)

### 3. Проверка автообновления

```bash
systemctl enable certbot.timer
systemctl start certbot.timer
systemctl status certbot.timer
```

### 4. Проверка сертификата

```bash
certbot certificates
```

---

## Настройка Redis

### 1. Запуск Redis

```bash
systemctl enable redis-server
systemctl start redis-server
systemctl status redis-server
```

### 2. Ограничение памяти (128MB)

```bash
cat >> /etc/redis/redis.conf << 'EOF'

# Shadow Hockey League settings
maxmemory 128mb
maxmemory-policy allkeys-lru
EOF

systemctl restart redis-server
```

### 3. Проверка подключения

```bash
redis-cli ping
# Должно вернуть: PONG

redis-cli info memory | grep used_memory_human
```

---

## Настройка бэкапов

### 1. Скрипт бэкапа

```bash
mkdir -p /backup

cat > /usr/local/bin/backup-db.sh << 'EOF'
#!/bin/bash

DB_FILE="/home/shleague/shadow-hockey-league_v2/instance/dev.db"
BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/dev.db-${DATE}"

# Копирование БД
cp "${DB_FILE}" "${BACKUP_FILE}"

# Сжатие
gzip "${BACKUP_FILE}"

# Очистка старых бэкапов (>7 дней)
find "${BACKUP_DIR}" -name "dev.db-*" -mtime +7 -delete

echo "✅ Backup created: ${BACKUP_FILE}.gz"
EOF

chmod +x /usr/local/bin/backup-db.sh
```

### 2. Настройка cron (ежедневно в 3:00 UTC)

```bash
(crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/backup-db.sh >> /var/log/backup-db.log 2>&1") | crontab -
```

### 3. Тестовый запуск

```bash
/usr/local/bin/backup-db.sh
ls -lh /backup/
```

---

## Настройка CI/CD

### 1. Генерация SSH ключа (локально)

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f github_actions_key
```

### 2. Копирование публичного ключа на сервер

```bash
# На сервере (root)
mkdir -p /home/shleague/.ssh
echo "ВАШ_ПУБЛИЧНЫЙ_КЛЮЧ" >> /home/shleague/.ssh/authorized_keys
chown -R shleague:shleague /home/shleague/.ssh
chmod 700 /home/shleague/.ssh
chmod 600 /home/shleague/.ssh/authorized_keys
```

### 3. Добавление секретов в GitHub

Перейдите в **Settings → Secrets and variables → Actions** и добавьте:

| Secret | Значение |
|--------|----------|
| `SERVER_IP` | IP вашего сервера |
| `SSH_USER` | `shleague` |
| `SSH_PRIVATE_KEY` | Содержимое `github_actions_key` |

### 4. Workflow файл

Файл уже создан: `.github/workflows/deploy.yml`

При пуше в `main` автоматически:
1. Подключается по SSH
2. Выполняет `git pull`
3. Обновляет зависимости
4. Перезапускает приложение

---

## Финальная проверка

### 1. Health check

```bash
curl https://YOUR_DOMAIN/health
```

Ожидаемый ответ:
```json
{
  "status": "healthy",
  "managers_count": 50,
  "achievements_count": 200,
  "countries_count": 8,
  "response_time_ms": 15,
  "redis_status": "connected",
  "cache_status": "working",
  "database_status": "connected"
}
```

### 2. Prometheus метрики

```bash
curl https://YOUR_DOMAIN/metrics
```

### 3. Главная страница

```bash
curl -s https://YOUR_DOMAIN/ | head -20
```

### 4. API (без auth)

```bash
curl https://YOUR_DOMAIN/api/countries
```

### 5. Проверка SSL

```bash
curl -I https://YOUR_DOMAIN
# Должно быть: HTTP/2 200
```

---

## Troubleshooting

### Сайт не открывается

```bash
# Проверка сервисов
systemctl status shadow-hockey-league
systemctl status nginx
systemctl status redis-server

# Проверка портов
ss -tlnp | grep -E '80|443|8000|6379'

# Логи
journalctl -u shadow-hockey-league -n 50
tail -50 /var/log/nginx/error.log
```

### Ошибка "no such table"

```bash
su - shleague
cd shadow-hockey-league_v2
source venv/bin/activate
alembic upgrade head
python seed_db.py
```

### Ошибка подключения к Redis

```bash
# Проверка Redis
redis-cli ping

# Если не работает
systemctl restart redis-server

# Проверка конфигурации
redis-cli CONFIG GET maxmemory
```

### Ошибка 502 Bad Gateway

```bash
# Проверка Gunicorn
systemctl status shadow-hockey-league

# Проверка, что Gunicorn слушает порт
ss -tlnp | grep 8000

# Перезапуск
systemctl restart shadow-hockey-league
systemctl restart nginx
```

### Статика не загружается

```bash
# Проверка прав
ls -la /home/shleague/shadow-hockey-league_v2/static/

# Исправление прав
chmod -R 755 /home/shleague/shadow-hockey-league_v2/static
chmod 755 /home/shleague

# Проверка Nginx
nginx -t
systemctl restart nginx
```

### Проблемы с БД (WAL режим)

```bash
# Проверка WAL режима
sqlite3 /home/shleague/shadow-hockey-league_v2/instance/dev.db "PRAGMA journal_mode;"
# Должно вернуть: wal

# Если не WAL
sqlite3 /home/shleague/shadow-hockey-league_v2/instance/dev.db "PRAGMA journal_mode=WAL;"
```

---

## 📊 Чеклист деплоя

### Подготовка

- [ ] VPS с Ubuntu 22.04 (минимум 1 CPU, 1GB RAM)
- [ ] Домен настроен (A-запись на IP)
- [ ] SSH доступ работает

### Установка

- [ ] Системные зависимости установлены
- [ ] Пользователь `shleague` создан
- [ ] Репозиторий склонирован
- [ ] Виртуальное окружение настроено
- [ ] Python зависимости установлены

### Конфигурация

- [ ] `.env` создан со всеми переменными
- [ ] `SECRET_KEY`, `API_KEY_SECRET`, `WTF_CSRF_SECRET_KEY` сгенерированы
- [ ] Директория `instance/` создана

### База данных

- [ ] Alembic миграции выполнены
- [ ] БД наполнена данными (`seed_db.py`)
- [ ] Первый администратор создан

### Сервисы

- [ ] Gunicorn systemd сервис создан и запущен
- [ ] Nginx настроен и запущен
- [ ] Redis запущен, лимит 128MB
- [ ] HTTPS настроен (Certbot)

### Бэкапы

- [ ] Скрипт бэкапа создан
- [ ] Cron настроен (ежедневно в 3:00)
- [ ] Тестовый бэкап успешен

### CI/CD

- [ ] SSH ключ сгенерирован
- [ ] Публичный ключ на сервере
- [ ] Секреты добавлены в GitHub
- [ ] Тестовый деплой успешен

### Проверка

- [ ] Health check возвращает `healthy`
- [ ] Главная страница загружается
- [ ] Статика загружается
- [ ] API работает (с ключом и без)
- [ ] Redis подключён
- [ ] Ошибки в логах отсутствуют

---

## 🔗 Полезные ссылки

| Ресурс | URL |
|--------|-----|
| Production | https://shadow-hockey-league.ru/ |
| Health check | `/health` |
| Метрики | `/metrics` |
| Админ-панель | `/admin/` |
| GitHub | https://github.com/amatjkay/shadow-hockey-league_v2 |
| API документация | `docs/API.md` |
| ADMIN документация | `docs/ADMIN.md` |

---

**Версия:** 1.0
**Дата:** 3 апреля 2026 г.
**Автор:** DEVELOPER (Этап 7.4)
