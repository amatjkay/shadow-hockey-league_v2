# 📊 Shadow Hockey League — Итоговая сводка

**Дата:** 1 апреля 2026 г.  
**Статус:** ✅ Production готов к работе

---

## 🌐 Production сервер

| Параметр | Значение |
|----------|----------|
| **Домен** | https://shadow-hockey-league.ru/ |
| **Сервер** | VPS KVM NVMe (Нидерланды) |
| **IP** | 46.29.239.8 |
| **ОС** | Ubuntu 22.04 LTS |
| **Хостинг** | Z-TV Hosting (250₽/мес) |

---

## 🏗 Архитектура

```
Internet → Nginx (80/443) → Gunicorn (8000) → Flask App → SQLite
                              ↓
                        4 workers
```

### Компоненты

| Компонент | Версия | Назначение |
|-----------|--------|------------|
| Nginx | 1.18.0 | Reverse proxy, SSL |
| Gunicorn | 20.1.0 | WSGI сервер (4 workers) |
| Python | 3.10.12 | Язык приложения |
| Flask | 3.1.x | Веб-фреймворк |
| SQLite | 3.x | База данных |
| Certbot | latest | SSL (Let's Encrypt) |

---

## 🔐 Безопасность

| Компонент | Статус |
|-----------|--------|
| HTTPS (Let's Encrypt) | ✅ Автообновление |
| SSH ключи | ✅ Без пароля |
| Бэкапы | ✅ Ежедневно в 3:00 |
| Firewall (UFW) | ✅ Порты открыты (80, 443, 60621) |

---

## 🔄 CI/CD (GitHub Actions)

**Workflow:** `.github/workflows/deploy.yml`

**Триггеры:**
- Пуш в ветку `main`
- Ручной запуск (workflow_dispatch)

**Процесс:**
```
git push → GitHub Actions → SSH → git pull → pip install → systemctl restart
```

**Секреты GitHub:**
- `SERVER_IP` = `46.29.239.8`
- `SSH_USER` = `shleague`
- `SSH_PRIVATE_KEY` = (приватный SSH ключ)

---

## 📦 Бэкапы

**Скрипт:** `/usr/local/bin/backup-db.sh`

**Расписание:** Ежедневно в 3:00 (cron)

**Хранение:** 7 дней в `/backup/`

**Формат:** `dev.db-YYYYMMDD-HHMMSS.gz`

**Команды:**
```bash
# Ручной запуск
/usr/local/bin/backup-db.sh

# Проверка бэкапов
ls -lh /backup/

# Логи
cat /var/log/backup-db.log
```

---

## 🛠 Управление сервисами

### Shadow Hockey League

```bash
# Статус
systemctl status shadow-hockey-league

# Перезапуск
systemctl restart shadow-hockey-league

# Логи
journalctl -u shadow-hockey-league -f
```

### Nginx

```bash
# Статус
systemctl status nginx

# Перезапуск
systemctl restart nginx

# Тест конфига
nginx -t

# Логи
tail -f /var/log/nginx/error.log
```

### SSL (Certbot)

```bash
# Статус сертификатов
certbot certificates

# Автообновление
systemctl status certbot.timer
```

---

## 📁 Структура на сервере

```
/home/shleague/shadow-hockey-league_v2/
├── app.py                      # Flask приложение
├── models.py                   # SQLAlchemy модели
├── requirements.txt            # Зависимости Python
├── venv/                       # Виртуальное окружение
├── instance/
│   └── dev.db                  # База данных SQLite
├── .env                        # Переменные окружения
└── static/                     # Статические файлы
```

### Systemd сервис

**Файл:** `/etc/systemd/system/shadow-hockey-league.service`

```ini
[Service]
User=shleague
WorkingDirectory=/home/shleague/shadow-hockey-league_v2
ExecStart=/home/shleague/shadow-hockey-league_v2/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"
```

### Nginx конфиг

**Файл:** `/etc/nginx/sites-available/shadow-hockey-league`

```nginx
server {
    listen 80;
    server_name shadow-hockey-league.ru www.shadow-hockey-league.ru;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
    }
    
    location /static {
        alias /home/shleague/shadow-hockey-league_v2/static;
    }
}
```

---

## 📖 Документация

| Файл | Описание |
|------|----------|
| [`README.md`](README.md) | Быстрый старт и общая информация |
| [`docs/VPS_DEPLOY.md`](docs/VPS_DEPLOY.md) | Полная инструкция по деплою на VPS |
| [`docs/DEPLOY.md`](docs/DEPLOY.md) | Инструкция по деплою на PythonAnywhere (архив) |
| [`docs/API.md`](docs/API.md) | REST API документация |

---

## 🔗 Ссылки

| Ресурс | URL |
|--------|-----|
| **Сайт** | https://shadow-hockey-league.ru/ |
| **GitHub** | https://github.com/amatjkay/shadow-hockey-league_v2 |
| **Actions** | https://github.com/amatjkay/shadow-hockey-league_v2/actions |
| **PythonAnywhere** | https://amatjkay.pythonanywhere.com/ (архив) |

---

## 💰 Стоимость

| Услуга | Стоимость |
|--------|-----------|
| VPS (Z-TV Hosting) | 250₽/мес |
| Домен (.ru) | 169₽/год (~14₽/мес) |
| SSL (Let's Encrypt) | 0₽ (бесплатно) |
| **Итого** | **~264₽/мес** |

---

## ✅ Чеклист готовности

### Инфраструктура
- [x] VPS настроен (Ubuntu 22.04)
- [x] Домен настроен (A-запись на IP)
- [x] HTTPS настроен (Let's Encrypt)
- [x] Nginx настроен (reverse proxy)
- [x] Gunicorn настроен (4 workers)

### Приложение
- [x] Flask приложение развёрнуто
- [x] База данных инициализирована
- [x] Systemd сервис запущен
- [x] Статические файлы доступны

### Автоматизация
- [x] Бэкапы настроены (ежедневно в 3:00)
- [x] CI/CD настроен (GitHub Actions)
- [x] Автообновление SSL (Certbot)

### Безопасность
- [x] SSH ключи (без пароля)
- [x] Firewall настроен (UFW)
- [x] Приватные ключи не в git

---

## 📞 Контакты

| Роль | Контакт |
|------|---------|
| Разработчик | amaneit@yandex.ru |
| Хостинг | Z-TV Hosting (ztv.su) |
| Домен | Reg.ru |

---

**Документ создан:** 1 апреля 2026 г.  
**Версия:** 1.0  
**Статус:** ✅ Production ready
