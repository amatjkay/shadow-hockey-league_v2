# 🔄 Инструкция по откату (Rollback Guide)

**Дата обновления:** 7 апреля 2026 г.
**Версия:** 2.0 (с GitHub Actions)

---

## 🚨 Когда нужен откат

| Ситуация | Действие |
|----------|----------|
| Критические ошибки в проде | **Немедленный откат** |
| Проблемы с БД (потеря данных) | **Немедленный откат + восстановление из бэкапа** |
| Падение тестов после деплоя | Откат или hotfix |
| Проблемы с производительностью | Откат или оптимизация |

---

## 🔧 Способы отката

### Способ 1: Через GitHub Actions (рекомендуется) ⭐

**Время выполнения:** 5-10 минут
**Преимущество:** Автоматическое восстановление кода и БД

```bash
# 1. Откройте: https://github.com/amatjkay/shadow-hockey-league_v2/actions/workflows/rollback.yml

# 2. Нажмите "Run workflow"

# 3. Выберите параметры:
#    - Branch: main
#    - Backup suffix: .pre-deploy (последний бэкап перед деплоем)

# 4. Нажмите "Run workflow"

# 5. Мониторьте прогресс в Actions
```

**Что делает:**
1. Подключается к серверу по SSH
2. Восстанавливает код из последнего бэкапа
3. Восстанавливает БД из `.pre-deploy` бэкапа
4. Перезапускает приложение
5. Проверяет health endpoint

---

### Способ 2: Ручной откат через SSH

**Время выполнения:** 5-10 минут

```bash
# 1. Подключиться к серверу
ssh shleague@shadow-hockey-league.ru

# 2. Перейти в директорию проекта
cd /home/shleague/shadow-hockey-league_v2

# 3. Посмотреть доступные бэкапы
ls -lh /backup/

# 4. Откатить код (к последнему стабильному коммиту)
git log --oneline -10  # Найти последний рабочий коммит
git reset --hard <COMMIT_HASH>

# 5. Восстановить БД из бэкапа
# Найти последний бэкап
ls -lh /backup/ | grep ".pre-deploy"

# Восстановить
cp /backup/dev.db-YYYYMMDD-HHMMSS.pre-deploy.gz /tmp/
cd /tmp
gunzip dev.db-*.pre-deploy.gz
cp dev.db-*.pre-deploy /home/shleague/shadow-hockey-league_v2/instance/dev.db

# 6. Переустановить зависимости
source venv/bin/activate
pip install -r requirements.txt --quiet

# 7. Перезапустить приложение
sudo systemctl restart shadow-hockey-league

# 8. Проверить статус
sudo systemctl status shadow-hockey-league
curl http://127.0.0.1:8000/health
```

---

### Способ 3: Откат через git revert

**Время выполнения:** 3-5 минут
**Преимущество:** Сохраняется история изменений

```bash
# 1. Локально
git checkout main
git revert <BAD_COMMIT_HASH>
git push origin main

# 2. Деплой произойдёт автоматически через CI/CD
```

---

## 💾 Бэкапы

### Расположение

```
/backup/
├── dev.db-20260407-030000.gz          # Ежедневный бэкап
├── dev.db-20260406-143022.pre-deploy.gz  # Бэкап перед деплоем
├── dev.db-20260405-030000.gz
└── ...
```

### Retention policy

- **Хранение:** Последние 10 бэкапов
- **Ежедневные:** В 3:00 UTC
- **Pre-deploy:** Перед каждым деплоем

### Ручное создание бэкапа

```bash
# На сервере
/usr/local/bin/backup-db.sh

# Или вручную
cp /home/shleague/shadow-hockey-league_v2/instance/dev.db /backup/dev.db-$(date +%Y%m%d-%H%M%S)
gzip /backup/dev.db-*
```

---

## 📊 Проверка после отката

### 1. Health Check

```bash
curl https://shadow-hockey-league.ru/health
```

**Ожидаемый ответ:**
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

### 2. Запуск тестов

```bash
cd /home/shleague/shadow-hockey-league_v2
source venv/bin/activate
pytest -v
```

**Ожидаемый результат:** Все 239 тестов проходят

### 3. Проверка логов

```bash
# Логи приложения
sudo journalctl -u shadow-hockey-league -n 50

# Логи Nginx
sudo tail -n 50 /var/log/nginx/access.log
sudo tail -n 50 /var/log/nginx/error.log

# Логи деплоя (если есть)
cat /var/log/deploy.log
```

---

## 📝 Чеклист после отката

- [ ] Проверить health endpoint (`/health`)
- [ ] Проверить основную страницу
- [ ] Проверить админ-панель
- [ ] Проверить API endpoints
- [ ] Проверить логи на ошибки
- [ ] Уведомить команду об откате
- [ ] Создать issue для анализа проблемы
- [ ] Запланировать исправление

---

## 🔍 Анализ причин

После отката создайте issue с меткой `rollback` и опишите:

1. **Что пошло не так?**
2. **Когда обнаружена проблема?**
3. **Какие пользователи затронуты?**
4. **Время простоя**
5. **План исправления**

---

## 🔗 Полезные ссылки

| Ресурс | URL |
|--------|-----|
| GitHub Actions | https://github.com/amatjkay/shadow-hockey-league_v2/actions |
| Rollback Workflow | https://github.com/amatjkay/shadow-hockey-league_v2/actions/workflows/rollback.yml |
| Deploy Workflow | https://github.com/amatjkay/shadow-hockey-league_v2/actions/workflows/deploy.yml |
| Production | https://shadow-hockey-league.ru/ |
| Health Check | `/health` |

---

**Важно:** После отката НЕ удаляйте бэкапы до полного устранения проблемы!

**Последнее обновление:** 7 апреля 2026 г.
