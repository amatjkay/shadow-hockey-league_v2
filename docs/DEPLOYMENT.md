# 🚀 Развёртывание Shadow Hockey League

**Версия:** 1.0  
**Дата:** 2 апреля 2026 г.

---

## 📋 Обзор

Инструкция по развёртыванию приложения на VPS (Ubuntu 22.04).

**Production:** https://shadow-hockey-league.ru/

---

## 🔧 Требования к серверу

| Ресурс | Минимум | Рекомендуется |
|--------|---------|---------------|
| CPU | 1 ядро | 2 ядра |
| RAM | 512 MB | 1 GB |
| Disk | 5 GB | 10 GB |
| OS | Ubuntu 20.04 | Ubuntu 22.04 LTS |

---

## 📦 Установка

### Шаг 1: Подготовка

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y python3-pip python3-venv nginx git
```

### Шаг 2: Клонирование

```bash
# Создайте пользователя
sudo useradd -m -s /bin/bash shleague

# Переключитесь на пользователя
sudo su - shleague

# Клонируйте репозиторий
git clone https://github.com/amatjkay/shadow-hockey-league_v2.git
cd shadow-hockey-league_v2
```

### Шаг 3: Виртуальное окружение

```bash
# Создайте venv
python3 -m venv venv

# Активируйте
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

### Шаг 4: База данных

```bash
# Примените миграции
alembic upgrade head

# Создайте начальные данные (опционально)
python seed_db.py

# Создайте админа
python scripts/create_admin.py
```

### Шаг 5: Конфигурация

```bash
# Создайте .env
cp .env.example .env
nano .env
```

**.env:**
```bash
FLASK_ENV=production
DATABASE_URL=sqlite:///dev.db
SECRET_KEY=<random-secret-key>
LOG_LEVEL=INFO
REDIS_HOST=localhost  # опционально
```

---

## 🌐 Nginx

### Конфигурация

```bash
sudo nano /etc/nginx/sites-available/shadow-hockey-league
```

**Конфиг:**
```nginx
server {
    listen 80;
    server_name shadow-hockey-league.ru;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /static {
        alias /home/shleague/shadow-hockey-league_v2/static;
        expires 30d;
    }
}
```

### Активация

```bash
# Включите сайт
sudo ln -s /etc/nginx/sites-available/shadow-hockey-league /etc/nginx/sites-enabled

# Проверьте конфиг
sudo nginx -t

# Перезапустите nginx
sudo systemctl restart nginx
```

---

## 🔒 SSL (Let's Encrypt)

```bash
# Установите Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получите сертификат
sudo certbot --nginx -d shadow-hockey-league.ru

# Автообновление (проверка)
sudo certbot renew --dry-run
```

---

## 🐘 Gunicorn

### Systemd service

```bash
sudo nano /etc/systemd/system/shadow-hockey-league.service
```

**Service:**
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

### Запуск

```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите service
sudo systemctl enable shadow-hockey-league

# Запустите
sudo systemctl start shadow-hockey-league

# Проверьте статус
sudo systemctl status shadow-hockey-league
```

---

## 🔄 Обновление

```bash
# Перейдите в директорию
cd /home/shleague/shadow-hockey-league_v2

# Активируйте venv
source venv/bin/activate

# Обновите код
git pull origin main

# Установите зависимости
pip install -r requirements.txt

# Примените миграции
alembic upgrade head

# Перезапустите приложение
sudo systemctl restart shadow-hockey-league
```

---

## 💾 Бэкапы

### Скрипт бэкапа

```bash
sudo nano /home/shleague/shadow-hockey-league_v2/backup/backup.sh
```

**Скрипт:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR=/backup
DB_FILE=/home/shleague/shadow-hockey-league_v2/dev.db

# Создайте директорию бэкапов
mkdir -p $BACKUP_DIR

# Создайте бэкап
gzip -c $DB_FILE > $BACKUP_DIR/dev.db-$DATE.gz

# Удалите старые бэкапы (> 7 дней)
find $BACKUP_DIR -name "dev.db-*" -mtime +7 -delete
```

### Cron задача

```bash
crontab -e
```

**Задача:**
```bash
0 3 * * * /home/shleague/shadow-hockey-league_v2/backup/backup.sh
```

---

## 🐛 Устранение неполадок

### Приложение не запускается

```bash
# Проверьте логи
sudo journalctl -u shadow-hockey-league -f

# Проверьте Gunicorn
sudo systemctl status shadow-hockey-league
```

### Ошибка 502 Bad Gateway

```bash
# Проверьте, запущен ли Gunicorn
sudo systemctl status shadow-hockey-league

# Проверьте Nginx
sudo nginx -t
sudo systemctl status nginx
```

### Ошибка БД

```bash
# Проверьте миграции
alembic current

# Примените миграции
alembic upgrade head
```

---

## 📊 Мониторинг

### Проверка доступности

```bash
# Health check
curl https://shadow-hockey-league.ru/health

# Метрики
curl https://shadow-hockey-league.ru/metrics
```

### Логи

```bash
# Логи приложения
sudo journalctl -u shadow-hockey-league -f

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

**Последнее обновление:** 2 апреля 2026 г.
