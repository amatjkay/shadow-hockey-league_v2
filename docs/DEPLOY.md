# 📤 Деплой на PythonAnywhere

**Цель:** Пошаговая инструкция по развёртыванию Shadow Hockey League на pythonanywhere.com.

**Статус:** ✅ Готово к деплою

**Последнее обновление:** 30 марта 2026 г.

---

## 📋 Требования

- Аккаунт на [PythonAnywhere](https://www.pythonanywhere.com/) (бесплатный или платный)
- Git репозиторий проекта
- Python 3.10+

---

## 🚀 Пошаговая инструкция

### Шаг 1: Загрузка файлов

#### Вариант A: Через Git (рекомендуется)

1. Войдите в консоль PythonAnywhere (Bash)
2. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/amatjkay/shadow-hockey-league_v2.git
   cd shadow-hockey-league_v2
   ```

#### Вариант B: Через ZIP-архив

1. Скачайте ZIP-архив проекта
2. В веб-интерфейсе PythonAnywhere перейдите в **Files**
3. Загрузите архив и распакуйте

---

### Шаг 2: Настройка виртуального окружения

1. Перейдите в **Web** → **Virtualenv**
2. Создайте новое окружение:
   ```bash
   python3 -m venv /home/amatjkay/.venvs/shadow-hockey-league_v2
   ```
3. Активируйте:
   ```bash
   source /home/amatjkay/.venvs/shadow-hockey-league_v2/bin/activate
   ```
4. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

---

### Шаг 3: Настройка WSGI

1. Перейдите в **Web** → **WSGI configuration file**
2. Замените содержимое на:

   ```python
   import sys
   import os

   project_home = '/home/amatjkay/shadow-hockey-league_v2'
   if project_home not in sys.path:
       sys.path.insert(0, project_home)

   os.environ['FLASK_ENV'] = 'production'

   from app import create_app
   application = create_app()
   ```

3. Сохраните

---

### Шаг 4: Настройка статических файлов

1. Перейдите в **Web** → **Static files**
2. Добавьте mapping:
   - **URL:** `/static/`
   - **Directory:** `/home/amatjkay/shadow-hockey-league_v2/static/`
3. Нажмите **Add another static files mapping**

---

### Шаг 5: Инициализация базы данных

1. Откройте Bash консоль
2. Активируйте виртуальное окружение:
   ```bash
   source /home/amatjkay/.venvs/shadow-hockey-league_v2/bin/activate
   ```
3. Инициализируйте БД:
   ```bash
   cd shadow-hockey-league_v2
   python seed_db.py
   ```

---

### Шаг 6: Настройка переменных окружения

1. Перейдите в **Web** → **Environment variables**
2. Добавьте переменные:
   ```
   FLASK_ENV=production
   DATABASE_URL=sqlite:///dev.db
   SECRET_KEY=your-secret-key-here
   LOG_LEVEL=INFO
   ```
3. **Важно:** Сгенерируйте уникальный `SECRET_KEY`:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

---

### Шаг 7: Запуск приложения

1. Перейдите в **Web**
2. Нажмите **Reload** кнопку (оранжевая кнопка сверху)
3. Откройте ваш сайт: `https://YOUR_USERNAME.pythonanywhere.com/`

---

## 🔧 Дополнительная настройка

### HTTPS

PythonAnywhere автоматически предоставляет HTTPS для всех сайтов.

### Домен

Для бесплатного аккаунта: `YOUR_USERNAME.pythonanywhere.com`

Для платного аккаунта можно использовать собственный домен.

### Логи

- **Error log:** `/var/log/username.pythonanywhere.com/error.log`
- **Server log:** `/var/log/username.pythonanywhere.com/server.log`

Просмотр через веб-интерфейс или:

```bash
tail -f /var/log/username.pythonanywhere.com/error.log
```

### Автоматический деплой (CI/CD)

> **⚠️ Важно:** На **бесплатном тарифе** PythonAnywhere API для reload и SSH недоступны.
> Используйте **Scheduled Tasks** (Вариант 2) или ручной деплой через консоль.

---

#### Вариант 1: GitHub Actions (Только для платного тарифа)

Настройте автоматический деплой при каждом пуше в ветку `main`:

**1. Создайте файл `.github/workflows/deploy.yml`:**

```yaml
name: Deploy to PythonAnywhere

on:
  push:
    branches: [main]
  workflow_dispatch: # Ручной запуск из UI GitHub

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to PythonAnywhere
        uses: pythonanywhere/action-pythonanywhere@v1
        with:
          username: ${{ secrets.PA_USERNAME }}
          api_key: ${{ secrets.PA_API_KEY }}
          domain: ${{ secrets.PA_DOMAIN }}
          action: reload
```

**2. Получите API ключ на PythonAnywhere:**

- Зайдите в **Settings** → **API**
- Создайте новый токен
- Скопируйте **Username** и **API Key**

**3. Добавьте секреты в GitHub:**

- В репозитории: **Settings** → **Secrets and variables** → **Actions**
- Добавьте три секрета:
  - `PA_USERNAME` — ваш логин на PythonAnywhere
  - `PA_API_KEY` — API токен из шага 2
  - `PA_DOMAIN` — ваш домен (например, `amatjkay.pythonanywhere.com`)

**Готово!** Теперь при каждом пуше в ветку `main`:

1. GitHub Actions автоматически вызовет API PythonAnywhere
2. PythonAnywhere сделает `git pull` и обновит код
3. Веб-приложение автоматически перезагрузится

**Преимущества:**

- ✅ Бесплатно (2000 минут/мес на GitHub Actions)
- ✅ Надёжно (официальное API PythonAnywhere)
- ✅ Безопасно (ключи хранятся в секретах GitHub)
- ✅ Мгновенный деплой после пуша

**⚠️ Ограничение:** Не работает на бесплатном тарифе PythonAnywhere

---

#### Вариант 2: Scheduled Task (Рекомендуется для бесплатного тарифа)

Настройте периодическую синхронизацию через планировщик задач PythonAnywhere:

**1. Создайте скрипт деплоя на сервере:**

Откройте **Bash консоль** на PythonAnywhere и выполните:

```bash
cd /home/amatjkay/shadow-hockey-league_v2

cat > deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Git pull
git pull origin main

# Activate virtualenv
source /home/amatjkay/.venvs/shadow-hockey-league_v2/bin/activate

# Install dependencies
pip install -r requirements.txt --quiet

# Reload app (touch WSGI file)
touch /var/www/amatjkay_pythonanywhere_com_wsgi.py

echo "✅ Deployment completed at $(date)"
EOF

chmod +x deploy.sh
```

**2. Настройте планировщик:**

- В PythonAnywhere перейдите в **Tasks** → **Schedule**
- Нажмите **Add a new task** → выберите **Bash**
- **Command:** `/home/amatjkay/shadow-hockey-league_v2/deploy.sh`
- **Расписание:** Например, `Hour: 3, Minute: 0` (каждый день в 3:00)

**Преимущества:**

- ✅ Работает на бесплатном тарифе
- ✅ Простая настройка
- ✅ Автоматическое обновление по расписанию

**Недостатки:**

- ⏰ Не мгновенный деплой (только по расписанию)
- 🔧 Требуется ручное создание скрипта на сервере

---

#### Вариант 3: Ручной деплой через консоль

Быстрое обновление вручную через Bash консоль PythonAnywhere:

```bash
cd /home/amatjkay/shadow-hockey-league_v2 && git pull && source /home/amatjkay/.venvs/shadow-hockey-league_v2/bin/activate && pip install -r requirements.txt --quiet && touch /var/www/amatjkay_pythonanywhere_com_wsgi.py
```

**Шаги:**

1. Откройте **Consoles** → **Bash console**
2. Вставьте команду выше
3. Нажмите Enter
4. Перезагрузите сайт через кнопку **Reload** на вкладке **Web**

---

#### Вариант 4: Webhook через Flask-эндпоинт

Создайте эндпоинт для триггера деплоя из GitHub webhooks:

**1. Добавьте в `app.py`:**

```python
@app.route('/deploy', methods=['POST'])
def deploy():
    """Trigger deployment via webhook."""
    import subprocess
    import os

    # Проверка токена безопасности
    token = request.headers.get('X-Deploy-Token')
    if token != os.environ.get('DEPLOY_TOKEN'):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        project_dir = '/home/amatjkay/shadow-hockey-league_v2'

        # Git pull
        subprocess.run(['git', 'pull'], cwd=project_dir, check=True, capture_output=True)

        # Install dependencies
        subprocess.run(
            ['pip', 'install', '-r', 'requirements.txt'],
            cwd=project_dir,
            check=True,
            capture_output=True
        )

        # Reload app (touch WSGI file)
        wsgi_file = '/var/www/amatjkay_pythonanywhere_com_wsgi.py'
        subprocess.run(['touch', wsgi_file], check=True)

        return jsonify({'status': 'success', 'message': 'Deployed successfully'})
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
```

**2. Добавьте `DEPLOY_TOKEN` в переменные окружения на PythonAnywhere:**

- **Web** → **Environment variables**
- Добавьте: `DEPLOY_TOKEN=your-secret-token-here`

**3. Настройте webhook в GitHub:**

- **Settings** → **Webhooks** → **Add webhook**
- **Payload URL:** `https://amatjkay.pythonanywhere.com/deploy`
- **Content type:** `application/json`
- **Secret:** тот же токен, что в `DEPLOY_TOKEN`
- **Trigger:** Push events

---

## 🛠 Устранение неполадок

### Ошибка 500 Internal Server Error

1. Проверьте логи ошибок
2. Убедитесь, что БД инициализирована
3. Проверьте переменные окружения

### Ошибка "ModuleNotFoundError"

1. Проверьте, что виртуальное окружение активно
2. Переустановите зависимости:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

### Статика не загружается

1. Проверьте путь в **Static files**
2. Убедитесь, что файлы существуют:
   ```bash
   ls /home/YOUR_USERNAME/shadow-hockey-league/static/
   ```

### БД не читается

Для бесплатного аккаунта SQLite работает только для чтения в некоторых случаях.
Решение:

- Использовать платный аккаунт
- Или перенести БД в MySQL (предоставляется бесплатно)

---

## 📊 Мониторинг

### Проверка здоровья

Откройте: `https://YOUR_USERNAME.pythonanywhere.com/health`

Ожидаемый ответ:

```json
{ "status": "healthy" }
```

### Статистика

PythonAnywhere предоставляет базовую статистику:

- Количество запросов
- Использование CPU
- Использование диска

Доступно в разделе **Stats**

---

## 📝 Чеклист деплоя

### Подготовка:

- [ ] Все изменения закоммичены и запушены
- [ ] Резервная копия локальной БД создана
- [ ] Тесты проходят: `python -m unittest discover -v`

### Развёртывание:

- [ ] Файлы загружены на PythonAnywhere
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] WSGI настроен
- [ ] Статические файлы настроены
- [ ] БД инициализирована (`python seed_db.py`)
- [ ] Переменные окружения заданы
- [ ] Приложение перезапущено (Reload)
- [ ] Сайт открывается без ошибок
- [ ] HTTPS работает
- [ ] Health check проходит

### Настройка CI/CD (опционально):

- [ ] Файл `.github/workflows/deploy.yml` создан
- [ ] API ключ PythonAnywhere получен (Settings → API)
- [ ] Секреты добавлены в GitHub (`PA_USERNAME`, `PA_API_KEY`, `PA_DOMAIN`)
- [ ] Тестовый запуск workflow через **Actions** → **Deploy** → **Run workflow**
- [ ] Проверка: пуш в `main` триггерит деплой

### Проверка:

- [ ] Главная страница загружается (< 3 сек)
- [ ] Рейтинг отображается корректно
- [ ] Ошиби в логах отсутствуют

---

## 📊 Тестирование после деплоя

### Автоматические тесты:

```bash
# Unit тесты (36 тестов)
python -m unittest tests.py -v

# Интеграционные тесты (12 тестов)
python -m unittest tests_integration.py -v
```

### Ручная проверка:

| Страница      | URL              | Ожидаемый результат     |
| ------------- | ---------------- | ----------------------- |
| Главная       | `/`              | Рейтинг загружен        |
| Health        | `/health`        | `{"status": "healthy"}` |
| API Managers  | `/api/managers`  | JSON список менеджеров  |
| API Countries | `/api/countries` | JSON список стран       |

---

## 🔐 Безопасность в production

### Настройки по умолчанию:

| Настройка               | Значение     | Описание                      |
| ----------------------- | ------------ | ----------------------------- |
| `FLASK_ENV`             | `production` | Режим продакшена              |
| `ENABLE_API`            | `False`      | API отключено (автоматически) |
| `SESSION_COOKIE_SECURE` | `True`       | HTTPS только для кук          |
| `LOG_TO_FILE`           | `True`       | Логирование в файл            |

### Рекомендации:

1. **Не коммитьте `.env`** — используйте `.env.example` как шаблон
2. **Регулярно обновляйте зависимости** — `pip list --outdated`
3. **Мониторьте логи** — `/var/log/YOUR_USERNAME.pythonanywhere.com/error.log`
4. **Создавайте резервные копии БД** — перед каждым обновлением

---

**Последнее обновление:** 30 марта 2026 г.
**Версия документа:** 1.1
