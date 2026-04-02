# 🔄 Инструкция по откату (Rollback Guide)

**Дата создания:** 2 апреля 2026 г.
**Версия:** 1.0

---

## 📋 Точки отката

| Тип | Название | Коммит | Описание |
|-----|----------|--------|----------|
| **Ветка** | `backup/main-before-merge-2026-04-02` | c0bcdfa | Состояние main перед мерджем |
| **Тег** | `backup-2026-04-02-before-merge` | c0bcdfa | Аннотированный тег для отката |

---

## 🚨 Когда нужен откат

| Ситуация | Действие |
|----------|----------|
| Критические ошибки в проде | **Немедленный откат** |
| Проблемы с БД (потеря данных) | **Немедленный откат** |
| Падение тестов после деплоя | Откат или hotfix |
| Проблемы с производительностью | Откат или оптимизация |

---

## 🔧 Способы отката

### Способ 1: Быстрый откат через тег (рекомендуется)

```bash
# 1. Переключиться на main
git checkout main

# 2. Сбросить до тега
git reset --hard backup-2026-04-02-before-merge

# 3. Отправить на сервер
git push origin main --force

# 4. Удалить тег (опционально)
git tag -d backup-2026-04-02-before-merge
git push origin --delete backup-2026-04-02-before-merge
```

**Время выполнения:** 2-3 минуты

---

### Способ 2: Откат через backup-ветку

```bash
# 1. Переключиться на main
git checkout main

# 2. Сбросить до backup-ветки
git reset --hard backup/main-before-merge-2026-04-02

# 3. Отправить на сервер
git push origin main --force
```

**Время выполнения:** 2-3 минуты

---

### Способ 3: Revert коммитов (без истории)

```bash
# 1. Переключиться на main
git checkout main

# 2. Отменить последний коммит мерджа
git revert -m 1 HEAD

# 3. Отправить на сервер
git push origin main
```

**Время выполнения:** 3-5 минут  
**Преимущество:** Сохраняется история изменений

---

## 🖥️ Откат на сервере (VPS)

### Через SSH

```bash
# 1. Подключиться к серверу
ssh shleague@shadow-hockey-league.ru

# 2. Перейти в директорию проекта
cd /home/shleague/shadow-hockey-league_v2

# 3. Откатить код
git fetch origin
git checkout backup-2026-04-02-before-merge
git reset --hard backup-2026-04-02-before-merge

# 4. Переустановить зависимости
source venv/bin/activate
pip install -r requirements.txt --quiet

# 5. Перезапустить приложение
sudo systemctl restart shadow-hockey-league

# 6. Проверить статус
sudo systemctl status shadow-hockey-league
curl https://shadow-hockey-league.ru/health
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
  "database_status": "connected"
}
```

### 2. Запуск тестов

```bash
cd /home/shleague/shadow-hockey-league_v2
source venv/bin/activate
python -m unittest discover -v
```

**Ожидаемый результат:** Все тесты проходят

### 3. Проверка логов

```bash
# Логи приложения
sudo journalctl -u shadow-hockey-league -n 50

# Логи Nginx
sudo tail -n 50 /var/log/nginx/access.log
sudo tail -n 50 /var/log/nginx/error.log
```

---

## 📞 Экстренный контакт

| Роль | Контакт |
|------|---------|
| **Разработчик** | @amatjkay (GitHub) |
| **Сервер** | VPS (Ubuntu 22.04) |
| **Домен** | shadow-hockey-league.ru |

---

## 📝 Чеклист после отката

- [ ] Проверить health endpoint
- [ ] Проверить основную страницу
- [ ] Проверить админ-панель
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

**Важно:** После отката НЕ удаляйте backup-ветку и тег до полного устранения проблемы!
