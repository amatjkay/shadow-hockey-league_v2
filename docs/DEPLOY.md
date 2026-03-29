# 📤 Деплой на PythonAnywhere

Инструкция по развёртыванию Shadow Hockey League на pythonanywhere.com.

---

## 📋 Требования

- Аккаунт на [PythonAnywhere](https://www.pythonanywhere.com/) (бесплатный или платный)
- Git репозиторий проекта

---

## 🚀 Пошаговая инструкция

### Шаг 1: Загрузка файлов

#### Вариант A: Через Git (рекомендуется)

1. Войдите в консоль PythonAnywhere (Bash)
2. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/YOUR_USERNAME/shadow-hockey-league.git
   cd shadow-hockey-league
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
   python3 -m venv /home/YOUR_USERNAME/.venvs/shadow-hockey-league
   ```
3. Активируйте:
   ```bash
   source /home/YOUR_USERNAME/.venvs/shadow-hockey-league/bin/activate
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

   project_home = '/home/YOUR_USERNAME/shadow-hockey-league'
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
   - **Directory:** `/home/YOUR_USERNAME/shadow-hockey-league/static/`
3. Нажмите **Add another static files mapping**

---

### Шаг 5: Инициализация базы данных

1. Откройте Bash консоль
2. Активируйте виртуальное окружение:
   ```bash
   source /home/YOUR_USERNAME/.venvs/shadow-hockey-league/bin/activate
   ```
3. Инициализируйте БД:
   ```bash
   cd shadow-hockey-league
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

### Автоматический деплой

Для автоматического деплоя через Git:

1. В **Web** → **Code** → **Automatic updates**
2. Укажите:
   - **Source code:** `/home/YOUR_USERNAME/shadow-hockey-league`
   - **Repository:** (ваш Git URL)
   - **Branch:** `main`

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
{"status": "healthy"}
```

### Статистика

PythonAnywhere предоставляет базовую статистику:
- Количество запросов
- Использование CPU
- Использование диска

Доступно в разделе **Stats**

---

## 📝 Чеклист деплоя

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

---

**Готово!** 🎉 Ваше приложение доступно публично.
