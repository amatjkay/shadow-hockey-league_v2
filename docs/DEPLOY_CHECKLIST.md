# 📋 Чеклист деплоя на PythonAnywhere

**Проект:** Shadow Hockey League  
**Дата последнего деплоя:** _______________  
**Версия:** _______________

---

## 🔧 ПОДГОТОВКА (локально)

### Перед коммитом

- [ ] Все изменения закоммичены и запушены
- [ ] Тесты проходят локально: `python -m unittest discover -v`
- [ ] `config.py` использует абсолютные пути (проверить `DATABASE_URL`)
- [ ] `.env` **НЕ** закоммичен (проверить `.gitignore`)

### Проверка конфигурации

```bash
# Запустить проверку
python scripts/check_deploy.py

# Ожидаемый вывод:
# ✅ Все проверки пройдены!
```

---

## 🌐 НА PYTHONANYWHERE

### 1. Консоль Bash

- [ ] Виртуальное окружение активировано: `source ~/.venvs/shadow-hockey-league_v2/bin/activate`
- [ ] Зависимости установлены: `pip install -r requirements.txt`
- [ ] База данных инициализирована: `python seed_db.py`
- [ ] БД существует: `ls -la dev.db`

### 2. Web-раздел

#### Virtualenv
- [ ] Указан путь: `/home/amatjkay/.venvs/shadow-hockey-league_v2`

#### WSGI Configuration File
- [ ] `project_home` установлен правильно
- [ ] `DATABASE_URL` использует **абсолютный путь**:
  ```python
  os.environ['DATABASE_URL'] = f'sqlite:///{project_home}/dev.db'
  ```
- [ ] `SECRET_KEY` установлен (не дефолтный!)
- [ ] Файл сохранён

#### Static Files
- [ ] Mapping существует:
  - URL: `/static/`
  - Directory: `/home/amatjkay/shadow-hockey-league_v2/static/`

#### Environment Variables (если есть секция)
- [ ] `FLASK_ENV=production`
- [ ] `DATABASE_URL=sqlite:////home/amatjkay/shadow-hockey-league_v2/dev.db`
- [ ] `SECRET_KEY=<сгенерирован>`
- [ ] `LOG_LEVEL=INFO`

### 3. Reload
- [ ] Нажата оранжевая кнопка **Reload**

---

## ✅ ПРОВЕРКА ПОСЛЕ ДЕПЛОЯ

### Быстрые тесты

- [ ] Главная страница: https://amatjkay.pythonanywhere.com/
  - [ ] Загружается (статус 200)
  - [ ] Рейтинг отображается
  - [ ] Менеджеры видны

- [ ] Health check: https://amatjkay.pythonanywhere.com/health
  - [ ] Возвращает JSON
  - [ ] `"status": "healthy"`
  - [ ] `managers_count > 0`

### Проверка логов

```bash
# Посмотреть последние ошибки
tail -50 /var/log/amatjkay.pythonanywhere.com.error.log
```

- [ ] Нет критических ошибок
- [ ] Нет `OperationalError: no such table`

### Функциональная проверка

- [ ] Таблица рейтинга сортируется по очкам
- [ ] Тандемы отображаются с бейджем
- [ ] Детали расчёта раскрываются
- [ ] Статика (CSS, изображения) загружается

---

## 🆘 ЕСЛИ ЧТО-ТО ПОШЛО НЕ ТАК

### Ошибка 500

1. Проверь логи:
   ```bash
   tail -100 /var/log/amatjkay.pythonanywhere.com.error.log
   ```

2. Частые причины:
   - ❌ Относительный путь к БД → Используй абсолютный
   - ❌ БД не существует → Запусти `python seed_db.py`
   - ❌ SECRET_KEY не установлен → Сгенерируй и добавь

### Ошибка "no such table"

```bash
# Переинициализируй БД
cd ~/shadow-hockey-league_v2
python seed_db.py
```

### Статика не грузится

1. Проверь путь в Static files mapping
2. Проверь что файлы существуют:
   ```bash
   ls ~/shadow-hockey-league_v2/static/css/
   ```

---

## 📝 ЗАМЕТКИ

**Проблемы при деплое:**

| Дата | Проблема | Решение |
|------|----------|---------|
| 31.03.2026 | DATABASE_URL относительный путь | Изменил на абсолютный в WSGI |

**Контакты:**
- Telegram: @Алексеем, @Константином
- Репозиторий: https://github.com/amatjkay/shadow-hockey-league_v2

---

**Последнее обновление:** 31 марта 2026 г.
