# 📤 Деплой на PythonAnywhere

**Цель:** Пошаговая инструкция по развёртыванию и обновлению Shadow Hockey League на pythonanywhere.com.

**Статус:** ✅ Развёрнуто на бесплатном тарифе

**Последнее обновление:** 1 апреля 2026 г.

---

## 📋 Требования

- Аккаунт на [PythonAnywhere](https://www.pythonanywhere.com/) (бесплатный или платный)
- Git репозиторий проекта
- Python 3.10+

---

## ⚠️ Ограничения бесплатного тарифа

| Функция         | Доступность   | Примечание                   |
| --------------- | ------------- | ---------------------------- |
| API для reload  | ❌ Недоступно | Только для платных аккаунтов |
| SSH доступ      | ❌ Недоступно | Только для платных аккаунтов |
| Scheduled Tasks | ✅ Доступно   | 1 задача, раз в день         |
| Git pull        | ✅ Доступно   | Через Bash консоль           |
| Веб-приложение  | ✅ Доступно   | С ручной перезагрузкой       |

**Вывод:** На бесплатном тарифе автоматический CI/CD через GitHub Actions **невозможен**. Обновление выполняется вручную или по расписанию через Scheduled Tasks.

---

## 🚀 Первоначальная настройка

### Шаг 1: Клонирование репозитория

1. Откройте **Bash консоль** на PythonAnywhere
2. Выполните:
   ```bash
   git clone https://github.com/amatjkay/shadow-hockey-league_v2.git
   cd shadow-hockey-league_v2
   ```

### Шаг 2: Настройка виртуального окружения

```bash
python3 -m venv /home/amatjkay/.venvs/shadow-hockey-league_v2
source /home/amatjkay/.venvs/shadow-hockey-league_v2/bin/activate
pip install -r requirements.txt
```

### Шаг 3: Настройка WSGI

1. Перейдите в **Web** → **WSGI configuration file**
2. Замените содержимое на:

   ```python
   import sys
   import os

   project_home = '/home/amatjkay/shadow-hockey-league_v2'
   if project_home not in sys.path:
       sys.path.insert(0, project_home)

   from app import create_app
   application = create_app()
   ```

3. Сохраните

### Шаг 4: Настройка статических файлов

1. Перейдите в **Web** → **Static files**
2. Добавьте mapping:
   - **URL:** `/static/`
   - **Directory:** `/home/amatjkay/shadow-hockey-league_v2/static/`

### Шаг 5: Инициализация базы данных

```bash
cd /home/amatjkay/shadow-hockey-league_v2
source /home/amatjkay/.venvs/shadow-hockey-league_v2/bin/activate
python seed_db.py
```

### Шаг 6: Переменные окружения

1. Перейдите в **Web** → **Environment variables**
2. Добавьте:
   ```
   FLASK_ENV=production
   DATABASE_URL=sqlite:////home/amatjkay/shadow-hockey-league_v2/dev.db
   SECRET_KEY=ваш-уникальный-ключ
   LOG_LEVEL=INFO
   ```

### Шаг 7: Запуск

1. Перейдите в **Web**
2. Нажмите **Reload**
3. Откройте: `https://amatjkay.pythonanywhere.com/`

---

## 🔄 Обновление на сервере

### Вариант 1: Ручное обновление (быстро)

**Одной командой:**

```bash
cd /home/amatjkay/shadow-hockey-league_v2 && git pull && source /home/amatjkay/.venvs/shadow-hockey-league_v2/bin/activate && pip install -r requirements.txt --quiet && touch /var/www/amatjkay_pythonanywhere_com_wsgi.py
```

**По шагам:**

```bash
# 1. Перейдите в директорию проекта
cd /home/amatjkay/shadow-hockey-league_v2

# 2. Получите последние изменения
git pull origin main

# 3. Активируйте виртуальное окружение
source /home/amatjkay/.venvs/shadow-hockey-league_v2/bin/activate

# 4. Обновите зависимости
pip install -r requirements.txt --quiet

# 5. Перезагрузите веб-приложение
touch /var/www/amatjkay_pythonanywhere_com_wsgi.py
```

Затем нажмите кнопку **Reload** на вкладке **Web**.

---

### Вариант 2: Автоматическое обновление (Scheduled Task)

**1. Создайте скрипт деплоя:**

Откройте **Bash консоль** и выполните:

```bash
cd /home/amatjkay/shadow-hockey-league_v2

cat > deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting deployment at $(date)..."

# Git pull
git pull origin main

# Activate virtualenv
source /home/amatjkay/.venvs/shadow-hockey-league_v2/bin/activate

# Install dependencies
pip install -r requirements.txt --quiet

# Reload app (touch WSGI file)
touch /var/www/amatjkay_pythonanywhere_com_wsgi.py

echo "✅ Deployment completed!"
EOF

chmod +x deploy.sh
```

**2. Настройте планировщик:**

1. Перейдите в **Tasks** → **Schedule**
2. Нажмите **Add a new task** → выберите **Bash**
3. **Command:** `/home/amatjkay/shadow-hockey-league_v2/deploy.sh`
4. **Расписание:** Например, `Hour: 3, Minute: 0` (каждый день в 3:00 UTC)

**Преимущества:**

- ✅ Работает на бесплатном тарифе
- ✅ Автоматическое обновление по расписанию

**Недостатки:**

- ⏰ Не мгновенный деплой (только по расписанию)
- Минимум 1 раз в день

---

### Вариант 3: Через GitHub (только платный тариф)

На платном тарифе можно настроить автоматический деплой через GitHub Actions:

```yaml
name: Deploy to PythonAnywhere

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Trigger reload
        run: |
          curl -X POST \
            "https://www.pythonanywhere.com/api/v0/user/${{ secrets.PA_USERNAME }}/webapps/${{ secrets.PA_DOMAIN }}/reload/" \
            -H "Authorization: Token ${{ secrets.PA_API_KEY }}"
```

---

## 🛠 Устранение неполадок

### Ошибка: "Your local changes to the following files would be overwritten by merge"

**Проблема:** Локальные изменения в файлах (обычно `.env`) конфликтуют с git pull.

**Решение:**

```bash
# Сохраните локальные изменения
cp .env .env.backup

# Сбросьте изменения
git reset --hard origin/main

# Восстановите .env
cp .env.backup .env

# Перезагрузите приложение
touch /var/www/amatjkay_pythonanywhere_com_wsgi.py
```

### Ошибка: "no such table"

**Проблема:** База данных не инициализирована.

**Решение:**

```bash
cd /home/amatjkay/shadow-hockey-league_v2
source /home/amatjkay/.venvs/shadow-hockey-league_v2/bin/activate
python seed_db.py
```

### Сайт не загружается после обновления

**Решение:**

1. Проверьте логи: **Web** → **Error log**
2. Перезагрузите приложение: кнопка **Reload** на вкладке **Web**
3. Проверьте, что WSGI файл существует:
   ```bash
   ls -la /var/www/amatjkay_pythonanywhere_com_wsgi.py
   ```

---

## 📊 Чеклист обновления

### Перед обновлением:

- [ ] Все изменения закоммичены и запушены в `main`
- [ ] Тесты проходят локально: `python -m unittest discover -v`

### После обновления:

- [ ] `git pull` выполнен без ошибок
- [ ] Зависимости установлены
- [ ] Веб-приложение перезапущено (touch WSGI + Reload)
- [ ] Сайт открывается без ошибок
- [ ] Данные в БД корректны

---

## 🔗 Полезные ссылки

| Ресурс                   | URL                                                                                |
| ------------------------ | ---------------------------------------------------------------------------------- |
| Веб-приложение           | https://amatjkay.pythonanywhere.com/                                               |
| PythonAnywhere Dashboard | https://www.pythonanywhere.com/user/amatjkay/                                      |
| Логи ошибок              | https://www.pythonanywhere.com/files/var/log/amatjkay.pythonanywhere.com/error.log |
| Репозиторий GitHub       | https://github.com/amatjkay/shadow-hockey-league_v2                                |

---

**Последнее обновление:** 1 апреля 2026 г.  
**Версия документа:** 2.0 (обновлено с учётом ограничений бесплатного тарифа)
