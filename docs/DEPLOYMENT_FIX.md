# 🔧 Server Setup Instructions

**Дата:** 7 апреля 2026 г.
**Версия:** v2.4.0

---

## ⚠️ Критичные настройки для деплоя

После деплоя v2.4.0 сервер требует ручной настройки. Выполни эти шаги **один раз**.

---

## 1. Исправить .env файл

### Проблема
В `.env` на сервере содержится Windows-путь:
```
DATABASE_URL=sqlite:///c:/dev/shadow/shadow-hockey-league_v2/dev.db
```

### Решение
Подключись к серверу и исправь:

```bash
ssh shleague@YOUR_SERVER_IP
cd /home/shleague/shadow-hockey-league_v2

# Проверь текущее значение
cat .env | grep DATABASE_URL

# Исправь .env (замени Windows-путь на Linux)
nano .env
```

**Замени строку:**
```
DATABASE_URL=sqlite:///c:/dev/shadow/shadow-hockey-league_v2/dev.db
```

**На:**
```
DATABASE_URL=sqlite:////home/shleague/shadow-hockey-league_v2/instance/dev.db
```

---

## 2. Настроить sudo без пароля для systemctl

### Проблема
Пользователь `shleague` не может перезапускать сервис без пароля:
```
Failed to restart shadow-hockey-league.service: Interactive authentication required.
```

### Решение
Выполни от **root**:

```bash
# Подключись как root или используй sudo
ssh root@YOUR_SERVER_IP

# Создай файл sudoers для shleague
cat > /etc/sudoers.d/shleague-systemctl << 'EOF'
# Allow shleague to restart the app service without password
shleague ALL=(ALL) NOPASSWD: /bin/systemctl restart shadow-hockey-league
shleague ALL=(ALL) NOPASSWD: /bin/systemctl is-active shadow-hockey-league
shleague ALL=(ALL) NOPASSWD: /bin/systemctl status shadow-hockey-league
EOF

# Установи правильные права (ОБЯЗАТЕЛЬНО!)
chmod 440 /etc/sudoers.d/shleague-systemctl

# Проверь синтаксис
visudo -c

# Проверь что работает
su - shleague -c "sudo systemctl is-active shadow-hockey-league"
```

**Ожидаемый вывод:** `active`

---

## 3. Проверить расположение БД

### Убедись что БД существует

```bash
ssh shleague@YOUR_SERVER_IP

# Проверь наличие БД
ls -lh /home/shleague/shadow-hockey-league_v2/instance/dev.db

# Если файл в другом месте, найди его
find /home/shleague -name "dev.db" 2>/dev/null
```

### Если БД не в `instance/`

Если БД находится в корне проекта (`/home/shleague/shadow-hockey-league_v2/dev.db`), есть два варианта:

**Вариант A:** Перемести БД в `instance/` (рекомендуется)
```bash
mkdir -p /home/shleague/shadow-hockey-league_v2/instance
mv /home/shleague/shadow-hockey-league_v2/dev.db /home/shleague/shadow-hockey-league_v2/instance/dev.db
```

**Вариант B:** Обнови `.env` на текущий путь
```
DATABASE_URL=sqlite:////home/shleague/shadow-hockey-league_v2/dev.db
```

---

## 4. Проверить Alembic миграции

После исправления `.env`:

```bash
ssh shleague@YOUR_SERVER_IP
cd /home/shleague/shadow-hockey-league_v2
source venv/bin/activate

# Проверь текущую версию
alembic current

# Ожидаемый вывод: 1c8dd033101a (head)

# Если ошибка — значит .env всё ещё неверный
```

---

## 5. Ручной запуск деплоя

После всех исправлений:

```bash
# На сервере (shleague)
cd /home/shleague/shadow-hockey-league_v2

# Запусти скрипт деплоя
bash scripts/deploy.sh
```

Или через GitHub Actions:
1. Зайди на https://github.com/amatjkay/shadow-hockey-league_v2/actions
2. Выбери "Deploy to VPS"
3. Нажми "Run workflow" → ветка `main`

---

## 6. Проверка health endpoint

```bash
curl http://127.0.0.1:5000/health

# Ожидаемый ответ:
# {"status":"healthy","managers_count":42,"achievements_count":49,"countries_count":8,"response_time_ms":...}
```

---

## Чек-лист готовности сервера

- [ ] `.env` содержит корректный Linux-путь: `sqlite:////home/shleague/.../instance/dev.db`
- [ ] `sudo systemctl restart shadow-hockey-league` работает без пароля
- [ ] БД существует по пути из `.env`
- [ ] `alembic current` возвращает `1c8dd033101a (head)`
- [ ] Health endpoint возвращает `{"status":"healthy"}`

---

## Troubleshooting

### Alembic всё ещё использует неправильный путь

Проверь что `.env` загружается корректно:
```bash
cd /home/shleague/shadow-hockey-league_v2
set -a
source .env
set +a
echo $DATABASE_URL
# Должно быть: sqlite:////home/shleague/shadow-hockey-league_v2/instance/dev.db
```

### systemctl всё ещё требует пароль

Проверь файл sudoers:
```bash
# От root
cat /etc/sudoers.d/shleague-systemctl
ls -l /etc/sudoers.d/shleague-systemctl
# Должно быть: -r--r----- 1 root root ...

# Пересоздай если нужно
rm /etc/sudoers.d/shleague-systemctl
# И создай заново (см. шаг 2)
```

### БД не найдена

Проверь что директория существует:
```bash
mkdir -p /home/shleague/shadow-hockey-league_v2/instance
```

---

**После выполнения этих шагов** деплой должен работать автоматически через GitHub Actions.
