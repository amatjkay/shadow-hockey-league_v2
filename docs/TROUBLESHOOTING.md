# 🛠 Troubleshooting — Shadow Hockey League v2

**Версия:** 3.1
**Дата:** 13 апреля 2026 г.
**Production:** https://shadow-hockey-league.ru/

---

## 1. Проблемы с деплоем

### Windows-пути в `.env`

**Симптом:** `OperationalError: no such table: managers`

**Решение:**
```bash
nano /home/shleague/shadow-hockey-league_v2/.env
# DATABASE_URL=sqlite:////home/shleague/shadow-hockey-league_v2/instance/dev.db
```

### `systemctl` требует пароль

**Решение:**
```bash
sudo visudo -f /etc/sudoers.d/shleague-systemctl
# shleague ALL=(ALL) NOPASSWD: /bin/systemctl restart shadow-hockey-league
```

---

## 2. Проблемы с БД

### "no such table"

```bash
alembic upgrade head
```

### "Database is locked"

```bash
sqlite3 instance/dev.db "PRAGMA journal_mode=WAL;"
```

---

## 3. Ошибки приложения

### 500 Internal Server Error

```bash
journalctl -u shadow-hockey-league -n 50 --no-pager
systemctl restart shadow-hockey-league
```

### 502 Bad Gateway

```bash
systemctl status shadow-hockey-league
systemctl restart nginx
```

---

## 4. Инфраструктура

### Redis отключён

**Симптом:** Health check показывает `redis_status: disconnected`

**Решение:**
```bash
sudo systemctl restart redis-server
```

### CSS/JS 404

```bash
chmod -R 755 static/
```

---

## 5. Полезные команды

```bash
# Проверить статус
systemctl status shadow-hockey-league

# Посмотреть логи
journalctl -u shadow-hockey-league -f

# Health check
curl https://shadow-hockey-league.ru/health

# Проверить БД
sqlite3 instance/dev.db ".tables"

# Бэкап БД
cp instance/dev.db instance/dev.db.backup_$(date +%Y%m%d_%H%M%S)
```

---

*Последнее обновление: 13 апреля 2026 г.*
