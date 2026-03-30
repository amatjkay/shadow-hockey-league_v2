# 📦 Руководство по ручному обновлению проекта

**Цель:** Пошаговая инструкция по обновлению проекта Shadow Hockey League на сервере PythonAnywhere (или другом хостинге).

**Целевая аудитория:** Разработчики, администраторы, выполняющие ручное развёртывание.

---

## 📋 Предварительные требования

- Доступ к серверу PythonAnywhere (или другому хостингу)
- Git-репозиторий с проектом
- Резервная копия текущей базы данных

---

## 🚀 Пошаговая инструкция

### Шаг 1: Подготовка

#### 1.1. Проверка локальной версии

```bash
# Убедитесь, что все изменения закоммичены
git status
git add .
git commit -m "feat: описание изменений"
git push origin main
```

#### 1.2. Создание резервной копии БД

```bash
# На сервере PythonAnywhere (через Bash)
cd /home/YOUR_USERNAME/shadow-hockey-league
cp dev.db dev.db.backup.$(date +%Y%m%d_%H%M%S)
```

**Важно:** Всегда создавайте резервную копию перед обновлением!

---

### Шаг 2: Загрузка обновлений

#### Вариант А: Через Git (рекомендуется)

```bash
# На сервере PythonAnywhere
cd /home/YOUR_USERNAME/shadow-hockey-league
git pull origin main
```

#### Вариант Б: Через ZIP-архив

1. Скачайте ZIP-архив из GitHub
2. В веб-интерфейсе PythonAnywhere → Files → Upload
3. Распакуйте архив, заменив существующие файлы

---

### Шаг 3: Обновление зависимостей

```bash
# Активация виртуального окружения
source /home/YOUR_USERNAME/.venvs/shadow-hockey-league/bin/activate

# Обновление зависимостей
pip install -r requirements.txt --upgrade

# Проверка установленных версий
pip list
```

---

### Шаг 4: Миграции базы данных

#### Вариант А: Alembic (если есть миграции)

```bash
# Проверка состояния миграций
alembic current

# Применение миграций
alembic upgrade head

# Проверка результата
alembic current
```

#### Вариант Б: Пересоздание БД (если схема не изменилась)

```bash
# Только если нет новых миграций
python seed_db.py
```

#### Вариант В: Ручное обновление (для сложных случаев)

```bash
# Запуск скрипта валидации
python scripts/validate_db.py --check

# При необходимости — исправление
python scripts/validate_db.py --fix
```

---

### Шаг 5: Проверка конфигурации

```bash
# Проверка переменных окружения
echo $FLASK_ENV
echo $DATABASE_URL
echo $SECRET_KEY  # Должен быть установлен, но не отображать значение

# Проверка наличия .env файла
ls -la .env
```

**Ожидаемые значения:**

| Переменная | Значение |
| ---------- | -------- |
| `FLASK_ENV` | `production` |
| `DATABASE_URL` | `sqlite:///dev.db` |
| `SECRET_KEY` | установлен (не пустой) |

---

### Шаг 6: Тестирование

#### 6.1. Запуск тестов

```bash
# Активация виртуального окружения
source /home/YOUR_USERNAME/.venvs/shadow-hockey-league/bin/activate

# Запуск всех тестов
python -m unittest discover -v

# Проверка результата
# Ожидаемый вывод: "Ran XX tests in X.XXXs" + "OK"
```

#### 6.2. Проверка маршрутов

```bash
# Проверка главной страницы
curl -I https://YOUR_USERNAME.pythonanywhere.com/
# Ожидаемый статус: HTTP/1.1 200 OK

# Проверка health endpoint
curl https://YOUR_USERNAME.pythonanywhere.com/health
# Ожидаемый ответ: {"status": "healthy"}

# Проверка API (если включено)
curl https://YOUR_USERNAME.pythonanywhere.com/api/managers
# Ожидаемый ответ: JSON список менеджеров
```

---

### Шаг 7: Перезапуск приложения

#### В веб-интерфейсе PythonAnywhere:

1. Перейдите в **Web**
2. Найдите ваше приложение
3. Нажмите оранжевую кнопку **Reload**

#### Через консоль (если есть доступ):

```bash
# Перезапуск через touch (обновление timestamp WSGI файла)
touch /var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py
```

---

### Шаг 8: Финальная проверка

#### Чеклист успешного обновления:

- [ ] Главная страница загружается (< 3 сек)
- [ ] Рейтинг отображается корректно
- [ ] Все менеджеры на месте
- [ ] Очки рассчитаны правильно
- [ ] Тандемы отображаются с бейджем
- [ ] Анимация топ-10 работает
- [ ] Health check возвращает `{"status": "healthy"}`
- [ ] API возвращает данные (если включено)
- [ ] Ошибки в логах отсутствуют

#### Проверка логов:

```bash
# Просмотр последних ошибок
tail -50 /var/log/YOUR_USERNAME.pythonanywhere.com/error.log

# Проверка на наличие критических ошибок
grep -i "error\|exception\|critical" /var/log/YOUR_USERNAME.pythonanywhere.com/error.log | tail -20
```

---

## 🔄 Откат к предыдущей версии

Если обновление прошло неудачно:

### 1. Откат кода

```bash
cd /home/YOUR_USERNAME/shadow-hockey-league
git revert HEAD
# Или откат к конкретному коммиту
git reset --hard <commit-hash>
```

### 2. Восстановление БД

```bash
# Остановка приложения (через веб-интерфейс)
# Восстановление из резервной копии
cp dev.db.backup.YYYYMMDD_HHMMSS dev.db

# Запуск приложения
```

### 3. Перезапуск

- Нажмите **Reload** в веб-интерфейсе PythonAnywhere

---

## 🛠 Устранение неполадок

### Проблема: Ошибка 500 после обновления

**Причины:**

1. Не установлены зависимости
2. Ошибка миграции БД
3. Переменные окружения не заданы

**Решение:**

```bash
# 1. Проверка зависимостей
pip install -r requirements.txt

# 2. Проверка БД
python scripts/validate_db.py --check

# 3. Проверка переменных
printenv | grep FLASK

# 4. Просмотр логов
tail -100 /var/log/YOUR_USERNAME.pythonanywhere.com/error.log
```

---

### Проблема: Ошибка "no such table"

**Причина:** БД не инициализирована или миграции не применены

**Решение:**

```bash
# Вариант 1: Применить миграции
alembic upgrade head

# Вариант 2: Пересоздать БД (если данные не важны)
rm dev.db
python seed_db.py

# Вариант 3: Восстановить из резервной копии
cp dev.db.backup.YYYYMMDD_HHMMSS dev.db
```

---

### Проблема: Статика не загружается

**Причина:** Неправильный путь к static files

**Решение:**

1. В веб-интерфейсе PythonAnywhere → **Static files**
2. Проверьте mapping:
   - **URL:** `/static/`
   - **Directory:** `/home/YOUR_USERNAME/shadow-hockey-league/static/`
3. При необходимости исправьте и сохраните
4. Нажмите **Reload**

---

### Проблема: API возвращает 404

**Причина:** API отключено в production (`ENABLE_API=False`)

**Решение:**

```bash
# Проверка переменной
echo $ENABLE_API

# Если нужно включить (не рекомендуется для публичного API):
# В веб-интерфейсе PythonAnywhere → Environment variables
# Добавьте: ENABLE_API=True
# Нажмите Reload
```

**Важно:** Включение API в production требует дополнительной аутентификации!

---

## 📊 Мониторинг после обновления

### Метрики для проверки:

| Метрика | Норма | Проверка |
| ------- | ----- | -------- |
| Время загрузки страницы | < 3 сек | Browser DevTools |
| Время ответа API | < 500 мс | `curl -w "%{time_total}"` |
| Количество ошибок в час | < 5 | Логи PythonAnywhere |
| Использование CPU | < 50% | PythonAnywhere Stats |
| Использование диска | < 100 MB | PythonAnywhere Files |

### Команды для мониторинга:

```bash
# Статистика запросов (PythonAnywhere Stats)
# Веб-интерфейс → Stats

# Последние ошибки
tail -f /var/log/YOUR_USERNAME.pythonanywhere.com/error.log

# Размер базы данных
du -h dev.db

# Количество записей в БД
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); print('Managers:', db.session.query(__import__('models').Manager).count())"
```

---

## 📝 Чеклист обновления

### Перед обновлением:

- [ ] Все изменения закоммичены и запушены
- [ ] Резервная копия БД создана
- [ ] Тесты проходят локально
- [ ] Документация обновлена

### Во время обновления:

- [ ] Код загружен на сервер
- [ ] Зависимости обновлены
- [ ] Миграции применены
- [ ] Конфигурация проверена
- [ ] Тесты пройдены

### После обновления:

- [ ] Главная страница работает
- [ ] Health check проходит
- [ ] Ошибки в логах отсутствуют
- [ ] Резервная копия сохранена (7 дней)

---

## 🔐 Безопасность

### Рекомендации:

1. **Не храните секреты в коде:** Используйте переменные окружения
2. **Регулярно обновляйте зависимости:** `pip list --outdated`
3. **Мониторьте логи:** Настройте алерты на критические ошибки
4. **Ограничьте доступ к API:** В production API должно быть отключено или защищено
5. **Резервное копирование:** Автоматизируйте создание бэкапов БД

---

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи ошибок
2. Поищите решение в документации
3. Проверьте статус PythonAnywhere: https://status.pythonanywhere.com/
4. Обратитесь в поддержку PythonAnywhere

---

**Последнее обновление:** 30 марта 2026 г.
**Версия документа:** 1.0
