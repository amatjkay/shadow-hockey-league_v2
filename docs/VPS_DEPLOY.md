# 🚀 Деплой на VPS (Ubuntu 22.04)

**Цель:** Пошаговая инструкция по развёртыванию Shadow Hockey League на собственном VPS сервере.

**Статус:** ✅ Развёрнуто на сервере `46.29.239.8`

**Домен:** https://shadow-hockey-league.ru/

**Последнее обновление:** 1 апреля 2026 г.

---

## 📋 Требования

- VPS с Ubuntu 22.04 (минимум 1 CPU, 512 MB RAM, 5 GB диск)
- Домен или IP-адрес
- SSH доступ (root)
- Git репозиторий проекта

---

## 🏗 Архитектура

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Internet  │ ──> │    Nginx    │ ──> │  Gunicorn   │
│  (порт 80)  │     │ (порт 80)   │     │ (порт 8000) │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │  Flask App  │
                                       │   SQLite    │
                                       └─────────────┘
```

---

## 📦 Шаг 1: Обновление системы

```bash
apt update && apt upgrade -y
```

---

## 📦 Шаг 2: Установка зависимостей

```bash
apt install -y nginx python3-pip python3-venv python3-dev \
             git curl wget build-essential
```

---

## 📦 Шаг 3: Создание пользователя

```bash
# Создаём пользователя для приложения
adduser --disabled-password --gecos "" shleague
usermod -aG sudo shleague
```

---

## 📦 Шаг 4: Клонирование репозитория

```bash
# Переключаемся на пользователя
su - shleague

# Клонируем репозиторий
git clone https://github.com/amatjkay/shadow-hockey-league_v2.git
cd shadow-hockey-league_v2

# Создаём виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

---

## 📦 Шаг 5: Настройка .env и БД

```bash
# Создаём директорию для БД
mkdir -p /home/shleague/shadow-hockey-league_v2/instance

# Создаём .env файл
cat > /home/shleague/shadow-hockey-league_v2/.env << EOF
FLASK_ENV=production
DATABASE_URL=sqlite:////home/shleague/shadow-hockey-league_v2/instance/dev.db
SECRET_KEY=$(openssl rand -hex 32)
LOG_LEVEL=INFO
EOF

# Создаём таблицы БД
python -c "from app import create_app, db; app = create_app();
with app.app_context(): db.create_all(); print('Tables created!')"

# Наполняем БД данными
python seed_db.py
```

---

## 📦 Шаг 6: Создание systemd сервиса

```bash
# Выходим к root
exit

# Создаём systemd сервис
cat > /etc/systemd/system/shadow-hockey-league.service << 'EOF'
[Unit]
Description=Shadow Hockey League Flask Application
After=network.target

[Service]
User=shleague
Group=shleague
WorkingDirectory=/home/shleague/shadow-hockey-league_v2
ExecStart=/home/shleague/shadow-hockey-league_v2/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"

[Install]
WantedBy=multi-user.target
EOF

# Запускаем сервис
systemctl daemon-reload
systemctl enable shadow-hockey-league
systemctl start shadow-hockey-league
systemctl status shadow-hockey-league
```

---

## 📦 Шаг 7: Настройка Nginx

```bash
# Создаём конфиг сайта
cat > /etc/nginx/sites-available/shadow-hockey-league << 'EOF'
server {
    listen 80;
    server_name shadow-hockey-league.ru www.shadow-hockey-league.ru;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/shleague/shadow-hockey-league_v2/static;
        expires 30d;
    }
}
EOF

# Включаем сайт
ln -s /etc/nginx/sites-available/shadow-hockey-league /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверяем и перезапускаем
nginx -t
systemctl restart nginx
```

---

## 📦 Шаг 8: Настройка прав доступа

```bash
# Даём права на чтение
chmod 755 /home/shleague
chmod 755 /home/shleague/shadow-hockey-league_v2
chmod -R 755 /home/shleague/shadow-hockey-league_v2/static
```

---

## 🔒 Шаг 9: Настройка HTTPS (Let's Encrypt)

```bash
# Установите Certbot
apt install -y certbot python3-certbot-nginx

# Получите сертификат
certbot --nginx -d shadow-hockey-league.ru -d www.shadow-hockey-league.ru

# Введите:
# - Email для уведомлений
# - A (согласие с условиями)
# - N (рассылка - по желанию)
# - 2 (редирект HTTP → HTTPS)

# Проверьте автообновление
systemctl enable certbot.timer
systemctl start certbot.timer
```

---

## 📦 Шаг 10: Настройка автоматических бэкапов

### 10.1: Создание скрипта бэкапа

```bash
# Создать директорию для бэкапов
mkdir -p /backup

# Создать скрипт
cat > /usr/local/bin/backup-db.sh << 'EOF'
#!/bin/bash

# Настройки
DB_FILE="/home/shleague/shadow-hockey-league_v2/instance/dev.db"
BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/dev.db-${DATE}"

# Создать бэкап
cp "${DB_FILE}" "${BACKUP_FILE}"

# Сжать бэкап
gzip "${BACKUP_FILE}"

# Очистить старые бэкапы (старше 7 дней)
find "${BACKUP_DIR}" -name "dev.db-*" -mtime +7 -delete

echo "✅ Backup created: ${BACKUP_FILE}.gz"
echo "✅ Old backups cleaned (>7 days)"
EOF

# Дать права на выполнение
chmod +x /usr/local/bin/backup-db.sh
```

### 10.2: Настройка cron (ежедневно в 3:00)

```bash
# Открыть crontab
crontab -e

# Добавить строку
0 3 * * * /usr/local/bin/backup-db.sh >> /var/log/backup-db.log 2>&1
```

### 10.3: Проверка бэкапов

```bash
# Тестовый запуск
/usr/local/bin/backup-db.sh

# Проверить бэкапы
ls -lh /backup/

# Проверить crontab
crontab -l
```

---

## 🔐 Шаг 11: Настройка CI/CD (GitHub Actions)

### 11.1: Генерация SSH ключа (локально)

```powershell
# В PowerShell на вашем компьютере
ssh-keygen -t ed25519 -C "github-actions" -f C:\dev\shadow\shadow-hockey-league_v2\github_actions_key -N ""
```

### 11.2: Копирование публичного ключа на сервер

```powershell
# Получаем содержимое публичного ключа
Get-Content C:\dev\shadow\shadow-hockey-league_v2\github_actions_key.pub
```

```bash
# На сервере (SSH root)
mkdir -p /home/shleague/.ssh
echo "ВАШ_ПУБЛИЧНЫЙ_КЛЮЧ" >> /home/shleague/.ssh/authorized_keys
chown -R shleague:shleague /home/shleague/.ssh
chmod 700 /home/shleague/.ssh
chmod 600 /home/shleague/.ssh/authorized_keys
```

### 11.3: Добавление секретов в GitHub

| Название          | Значение                        |
| ----------------- | ------------------------------- |
| `SERVER_IP`       | `46.29.239.8`                   |
| `SSH_USER`        | `shleague`                      |
| `SSH_PRIVATE_KEY` | Содержимое `github_actions_key` |

### 11.4: Workflow файл

Создайте `.github/workflows/deploy.yml`:

```yaml
name: Deploy to VPS

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_ed25519
          chmod 600 ~/.ssh/id_ed25519
          ssh-keyscan -H ${{ secrets.SERVER_IP }} >> ~/.ssh/known_hosts

      - name: Deploy to server
        run: |
          ssh -i ~/.ssh/id_ed25519 ${{ secrets.SSH_USER }}@${{ secrets.SERVER_IP }} << 'ENDSSH'
            cd /home/${{ secrets.SSH_USER }}/shadow-hockey-league_v2
            
            git pull origin main
            
            source venv/bin/activate
            pip install -r requirements.txt --quiet
            
            systemctl restart shadow-hockey-league
            
            echo "✅ Deployment completed!"
          ENDSSH
```

---

## 🛠 Управление сервисом

```bash
# Статус
systemctl status shadow-hockey-league

# Перезапуск
systemctl restart shadow-hockey-league

# Остановка
systemctl stop shadow-hockey-league

# Логи
journalctl -u shadow-hockey-league -f
```

---

## 🛠 Управление Nginx

```bash
# Статус
systemctl status nginx

# Перезапуск
systemctl restart nginx

# Логи ошибок
tail -f /var/log/nginx/error.log
```

---

## 🔧 Устранение неполадок

### Ошибка: "Permission denied" для статики

```bash
chmod -R 755 /home/shleague/shadow-hockey-league_v2/static
chmod 755 /home/shleague
```

### Ошибка: "no such table"

```bash
su - shleague
cd shadow-hockey-league_v2
source venv/bin/activate
python -c "from app import create_app, db; app = create_app();
with app.app_context(): db.create_all()"
python seed_db.py
```

### Сайт не загружается

```bash
# Проверка Gunicorn
systemctl status shadow-hockey-league

# Проверка Nginx
systemctl status nginx
nginx -t

# Логи
journalctl -u shadow-hockey-league -n 50
tail -20 /var/log/nginx/error.log
```

---

## 📊 Мониторинг

### Проверка здоровья

```bash
curl http://46.29.239.8/health
```

### Логи приложения

```bash
# Логи Gunicorn
journalctl -u shadow-hockey-league -f

# Логи Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

---

## 📊 Чеклист деплоя

### Подготовка:

- [ ] VPS с Ubuntu 22.04
- [ ] SSH доступ (root)
- [ ] Домен/IP настроен

### Развёртывание:

- [ ] Зависимости установлены
- [ ] Пользователь создан
- [ ] Репозиторий склонирован
- [ ] Виртуальное окружение настроено
- [ ] Зависимости Python установлены
- [ ] .env создан
- [ ] БД инициализирована
- [ ] Systemd сервис создан и запущен
- [ ] Nginx настроен
- [ ] Права доступа настроены

### CI/CD:

- [ ] SSH ключ сгенерирован
- [ ] Публичный ключ на сервере
- [ ] Секреты добавлены в GitHub
- [ ] Workflow файл создан
- [ ] Тестовый деплой успешен

### Проверка:

- [ ] Сайт открывается
- [ ] Статика загружается
- [ ] Ошибки в логах отсутствуют

---

**Последнее обновление:** 1 апреля 2026 г.  
**Версия документа:** 1.0
