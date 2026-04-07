# 🤝 Руководство контрибьютора - Shadow Hockey League v2

**Версия:** 1.0
**Дата:** 7 апреля 2026 г.

---

## 📋 Обзор

Спасибо за интерес к проекту Shadow Hockey League v2! Это руководство поможет вам начать работу.

**Production:** https://shadow-hockey-league.ru/
**GitHub:** https://github.com/amatjkay/shadow-hockey-league_v2

---

## 🚀 Быстрый старт

### 1. Форкните репозиторий

```bash
# На GitHub нажмите кнопку "Fork"
```

### 2. Клонируйте форк

```bash
git clone https://github.com/YOUR_USERNAME/shadow-hockey-league_v2.git
cd shadow-hockey-league_v2
```

### 3. Настройте upstream

```bash
git remote add upstream https://github.com/amatjkay/shadow-hockey-league_v2.git
git fetch upstream
```

### 4. Создайте виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 5. Установите зависимости

```bash
pip install -r requirements.txt
```

### 6. Инициализируйте БД

```bash
python seed_db.py
```

### 7. Запустите приложение

```bash
python app.py
```

Откройте: http://127.0.0.1:5000/

---

## 🧪 Тестирование

### Запуск всех тестов

```bash
pytest -v
```

### С покрытием

```bash
pytest --cov=. --cov-report=term-missing
```

### Только unit тесты

```bash
pytest tests/ -v -k "not e2e"
```

### Только E2E тесты

```bash
pytest tests/e2e/ -v
```

**Важно:** Все тесты должны проходить перед созданием PR!

---

## 📝 Стиль кода

### Форматирование

```bash
# Black
black .

# isort
isort .

# Flake8 (проверка)
flake8
```

### Makefile команды

```bash
make setup      # Установка зависимостей + инициализация БД
make run        # Запуск сервера
make test       # Запуск тестов
make lint       # Проверка стиля
make format     # Форматирование кода
make clean      # Очистка временных файлов
```

### Правила

- ✅ Используйте type hints
- ✅ Docstrings для публичных функций
- ✅ Следуйте PEP 8
- ✅ Максимальная длина строки: 120 символов
- ✅ Имена переменных: snake_case
- ✅ Имена классов: PascalCase

---

## 🌿 Git Workflow

### Создание ветки

```bash
# Обновите main
git checkout main
git pull upstream main

# Создайте ветку
git checkout -b feature/your-feature-name
```

### Именование веток

| Тип | Формат | Пример |
|-----|--------|--------|
| Feature | `feature/description` | `feature/notification-system` |
| Bugfix | `fix/description` | `fix/rating-calculation` |
| Docs | `docs/description` | `docs/api-documentation` |
| Refactor | `refactor/description` | `refactor/cache-service` |

### Коммиты

```bash
# Формат коммита
<type>(<scope>): <description>

# Примеры
feat(api): add pagination support
fix(rating): correct calculation for tandem
docs(readme): update deployment instructions
test(cache): add unit tests for cache invalidation
```

**Типы коммитов:**
- `feat` - новая функциональность
- `fix` - исправление бага
- `docs` - документация
- `style` - форматирование
- `refactor` - рефакторинг
- `test` - тесты
- `chore` - обслуживание

---

## 📤 Создание Pull Request

### 1. Обновите ветку

```bash
git fetch upstream
git rebase upstream/main
```

### 2. Запустите тесты

```bash
pytest -v
make lint
```

### 3. Создайте PR

```bash
# Push ветки
git push origin feature/your-feature-name

# На GitHub создайте Pull Request
```

### 4. Заполните PR шаблон

```markdown
## Описание
Краткое описание изменений

## Тип изменений
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Тестирование
- [ ] Все тесты проходят
- [ ] Добавлены новые тесты
- [ ] Протестировано локально

## Чеклист
- [ ] Код отформатирован (black, isort)
- [ ] Flake8 не выдаёт ошибок
- [ ] Документация обновлена
- [ ] Нет конфликтов с main
```

---

## 📚 Документация

### Где документация

| Тема | Файл |
|------|------|
| Общая информация | `README.md` |
| Архитектура | `docs/ARCHITECTURE.md` |
| API | `docs/API.md` |
| Админ-панель | `docs/ADMIN.md` |
| Деплой | `docs/MIGRATION_GUIDE.md` |
| Тестирование | `docs/TESTING.md` |
| Безопасность | `docs/SECURITY.md` |
| Troubleshooting | `docs/TROUBLESHOOTING.md` |
| Changelog | `CHANGELOG.md` |

### Обновление документации

При изменении функционала:
- ✅ Обновите соответствующий документ
- ✅ Добавьте запись в CHANGELOG.md
- ✅ Обновите README если нужно

---

## 🐛 Баг-репорты

### Создание issue

**Шаблон баг-репорта:**

```markdown
## Описание
Краткое описание бага

## Шаги воспроизведения
1. Шаг 1
2. Шаг 2
3. Шаг 3

## Ожидаемое поведение
Что должно произойти

## Фактическое поведение
Что происходит

## Окружение
- OS: Ubuntu 22.04
- Python: 3.10
- Browser: Chrome 120

## Скриншоты/Логи
Если применимо
```

---

## 💡 Предложения функционала

### Создание feature request

**Шаблон:**

```markdown
## Описание
Что вы хотите добавить

## Обоснование
Почему это нужно

## Альтернативы
Какие есть альтернативы

## Дополнительная информация
Любые другие детали
```

---

## 🎯 Что можно улучшить

### Приоритетные задачи

- [ ] Система уведомлений (Email + In-App)
- [ ] Миграция на PostgreSQL
- [ ] WebSocket real-time обновления
- [ ] Docker контейнеризация
- [ ] Увеличение покрытия тестов до 90%
- [ ] GraphQL API
- [ ] Тёмная тема
- [ ] История рейтинга
- [ ] Страница менеджера

### Good First Issues

Ищите issues с меткой `good first issue` - это простые задачи для новичков.

---

## 📞 Связь

| Канал | Ссылка |
|-------|--------|
| GitHub Issues | https://github.com/amatjkay/shadow-hockey-league_v2/issues |
| Production | https://shadow-hockey-league.ru/ |

---

## 🎉 Спасибо!

Любой вклад важен! Не стесняйтесь задавать вопросы.

---

**Последнее обновление:** 7 апреля 2026 г.
**Версия:** 1.0
