# 🛠 Руководство по устранению неполадок

**Цель:** Быстрое решение распространённых проблем в Shadow Hockey League.

**Последнее обновление:** 7 апреля 2026 г.

**Production:** https://shadow-hockey-league.ru/

---

## 📋 Оглавление

1. [Ошибки базы данных](#ошибки-базы-данных)
2. [Ошибки приложения](#ошибки-приложения)
3. [Проблемы со статикой](#проблемы-со-статикой)
4. [Проблемы с тестами](#проблемы-с-тестами)
5. [Проблемы деплоя (VPS)](#проблемы-деплоя-vps)
6. [Проблемы с Redis](#проблемы-с-redis)
7. [Проблемы с CI/CD](#проблемы-с-cicd)

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
ls -la /home/shleague/shadow-hockey-league_v2/instance/dev.db

# 2. Применить миграции
cd /home/shleague/shadow-hockey-league_v2
source venv/bin/activate
alembic upgrade head

# 3. Проверить путь в .env
cat .env | grep DATABASE_URL

# 4. Если нужно - переинициализировать (данные будут удалены!)
rm instance/dev.db
alembic upgrade head
python seed_db.py
```

**Профилактика:**
- Убедитесь, что `DATABASE_URL` в `.env` совпадает с реальным путём
- Всегда запускайте `alembic upgrade head` после обновления кода

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
# 1. Проверить WAL режим
sqlite3 /home/shleague/shadow-hockey-league_v2/instance/dev.db "PRAGMA journal_mode;"
# Должно вернуть: wal

# 2. Включить WAL если выключен
sqlite3 /home/shleague/shadow-hockey-league_v2/instance/dev.db "PRAGMA journal_mode=WAL;"

# 3. Перезапустить приложение
systemctl restart shadow-hockey-league
```

**Профилактика:**
- В production рассмотрите переход на PostgreSQL
- Используйте connection pooling

---

## Ошибки приложения

### ❌ Ошибка 500 Internal Server Error

**Симптомы:**
- Приложение возвращает 500
- В логах Gunicorn traceback

**Решение:**

```bash
# 1. Проверить логи Gunicorn
journalctl -u shadow-hockey-league -n 50 --no-pager

# 2. Проверить статус сервиса
systemctl status shadow-hockey-league

# 3. Перезапустить
systemctl restart shadow-hockey-league

# 4. Проверить health
curl http://127.0.0.1:8000/health
```

---

### ❌ Ошибка 502 Bad Gateway

**Симптомы:**
- Nginx возвращает 502
- Gunicorn не запущен

**Решение:**

```bash
# 1. Проверить Gunicorn
systemctl status shadow-hockey-league

# 2. Проверить порт
ss -tlnp | grep 8000

# 3. Если Gunicorn не запущен - запустить
systemctl start shadow-hockey-league

# 4. Проверить логи
journalctl -u shadow-hockey-league -n 100

# 5. Перезапустить Nginx
systemctl restart nginx
```

---

## Проблемы со статикой

### ❌ CSS/JS не загружаются

**Симптомы:**
- Страница без стилей
- 404 ошибки в консоли браузера

**Решение:**

```bash
# 1. Проверить права
ls -la /home/shleague/shadow-hockey-league_v2/static/
chmod -R 755 /home/shleague/shadow-hockey-league_v2/static
chmod 755 /home/shleague

# 2. Проверить Nginx конфиг
nginx -t
cat /etc/nginx/sites-available/shadow-hockey-league | grep static

# 3. Перезапустить Nginx
systemctl restart nginx
```

---

## Проблемы с тестами

### ❌ Тесты не проходят

**Решение:**

```bash
# 1. Запустить тесты локально
cd /home/shleague/shadow-hockey-league_v2
source venv/bin/activate
pytest -v

# 2. С покрытием
pytest --cov=. --cov-report=term-missing

# 3. E2E тесты
pytest tests/e2e/ -v

# 4. Проверить зависимости
pip install -r requirements.txt --quiet
```

---

## Проблемы деплоя (VPS)

### ❌ Деплой не работает

**Симптомы:**
- GitHub Actions завершается с ошибкой
- Сайт не обновляется после push

**Решение:**

```bash
# 1. Проверить SSH ключ
cat /home/shleague/.ssh/authorized_keys

# 2. Проверить логи SSH
tail -20 /var/log/auth.log | grep ssh

# 3. Проверить GitHub Actions
# Откройте: https://github.com/amatjkay/shadow-hockey-league_v2/actions

# 4. Ручной деплой
cd /home/shleague/shadow-hockey-league_v2
source venv/bin/activate
git reset --hard origin/main
pip install -r requirements.txt --quiet
alembic upgrade head
systemctl restart shadow-hockey-league

# 5. Проверить health
curl http://127.0.0.1:8000/health
```

---

### ❌ Rollback не работает

**Решение:**

```bash
# 1. Проверить бэкапы
ls -lh /backup/

# 2. Восстановить БД вручную
cp /backup/dev.db-YYYYMMDD-HHMMSS.gz /tmp/
cd /tmp
gunzip dev.db-YYYYMMDD-HHMMSS.gz
cp dev.db-YYYYMMDD-HHMMSS /home/shleague/shadow-hockey-league_v2/instance/dev.db
systemctl restart shadow-hockey-league

# 3. Или через GitHub Actions
# Откройте: https://github.com/amatjkay/shadow-hockey-league_v2/actions/workflows/rollback.yml
# Нажмите "Run workflow"
```

---

## Проблемы с Redis

### ❌ Redis не подключён

**Симптомы:**
- Health check показывает `redis_status: disconnected`
- Кэш не работает

**Решение:**

```bash
# 1. Проверить статус Redis
systemctl status redis-server
redis-cli ping
# Должно вернуть: PONG

# 2. Если не запущен
systemctl start redis-server
systemctl enable redis-server

# 3. Проверить память
redis-cli info memory | grep used_memory_human

# 4. Проверить конфиг
redis-cli CONFIG GET maxmemory
# Должно быть: 128mb

# 5. Перезапустить
systemctl restart redis-server
```

---

## Проблемы с CI/CD

### ❌ GitHub Actions не деплоит

**Причины:**
1. SSH ключ истёк
2. Секреты не настроены
3. Сервер недоступен

**Решение:**

```bash
# 1. Проверить секреты в GitHub
# Settings → Secrets and variables → Actions
# Должны быть: SERVER_IP, SSH_USER, SSH_PRIVATE_KEY

# 2. Проверить доступность сервера
ping shadow-hockey-league.ru

# 3. Проверить SSH
ssh -i ~/.ssh/id_ed25519 shleague@shadow-hockey-league.ru "echo success"

# 4. Перегенерировать ключ если нужно
ssh-keygen -t ed25519 -C "github-actions-deploy" -f github_actions_key
# Скопировать публичный ключ на сервер
```

---

## 📞 Дополнительные ресурсы

| Ресурс | URL |
|--------|-----|
| Production | https://shadow-hockey-league.ru/ |
| Health check | `/health` |
| Метрики | `/metrics` |
| GitHub Actions | https://github.com/amatjkay/shadow-hockey-league_v2/actions |
| Деплой инструкция | `docs/MIGRATION_GUIDE.md` |
| Rollback инструкция | `docs/ROLLBACK.md` |

---

**Последнее обновление:** 7 апреля 2026 г.
**Версия:** 2.0 (VPS)
