# MCP Configuration — Shadow Hockey League

**Последнее обновление:** 2 апреля 2026 г.

---

## 📋 Обзор

Проект использует **Model Context Protocol (MCP)** для расширения возможностей AI-ассистентов при работе с кодовой базой.

---

## 🔧 Установленные MCP серверы

### Глобальная конфигурация (Windsurf)

**Путь:** `C:\Users\tiki\.codeium\windsurf\mcp_config.json`

| Сервер                | Статус | Описание                  |
| --------------------- | ------ | ------------------------- |
| `filesystem`          | ✅     | Доступ к файловой системе |
| `mcp-playwright`      | ✅     | Автоматизация браузера    |
| `sequential-thinking` | ✅     | Последовательное мышление |
| `fetch`               | ❌     | HTTP запросы              |
| `github-mcp-server`   | ❌     | GitHub API (Docker)       |
| `redis`               | ❌     | Redis кэширование         |

### Проектная конфигурация

**Путь:** `.qwen/mcp.json` (в корне проекта)

---

## 📦 Проектные MCP серверы

### 1. Filesystem ✅

**Назначение:** Доступ к файловой системе проекта с ограничением на директорию проекта.

```json
{
  "command": "npx",
  "args": [
    "-y",
    "@modelcontextprotocol/server-filesystem",
    "c:\\dev\\shadow\\shadow-hockey-league_v2"
  ]
}
```

**Возможности:**

- Чтение файлов проекта
- Поиск по файловой системе
- Безопасный доступ (только директория проекта)

---

### 2. Redis ✅

**Назначение:** Подключение к Redis для работы с кэшированием (Этап 1).

```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-redis"],
  "env": {
    "REDIS_URL": "redis://localhost:6379/0"
  }
}
```

**Возможности:**

- Просмотр ключей кэша
- Отладка кэширования
- Мониторинг Redis

**Требования:**

- Установленный Redis на `localhost:6379`
- Настроенный `Flask-Caching` в проекте

---

### 3. GitHub ⚠️ (Отключен)

**Назначение:** Работа с GitHub API для управления репозиторием.

```json
{
  "command": "docker",
  "args": [
    "run",
    "-i",
    "--rm",
    "-e",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ghcr.io/github/github-mcp-server"
  ],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
  }
}
```

**Возможности:**

- Управление issue/pull request
- Просмотр коммитов
- Работа с файлами репозитория

**Требования:**

- Установленный Docker Desktop
- GitHub Personal Access Token в переменной окружения `GITHUB_TOKEN`

---

### 4. Fetch ✅

**Назначение:** HTTP запросы для тестирования API и health checks.

```json
{
  "command": "uvx",
  "args": ["mcp-server-fetch", "--user-agent", "Shadow-Hockey-League-MCP/1.0"]
}
```

**Возможности:**

- Тестирование `/health` endpoint
- Проверка `/metrics`
- API тестирование
- Проверка внешних URL

**Примеры использования:**

- "Проверь http://localhost:5000/health"
- "Получи http://localhost:5000/metrics"
- "Проверь доступность https://shadow-hockey-league.ru/"

**Установка:**

```bash
# uvx устанавливается автоматически при первом запуске
# или вручную:
pip install uv
```

---

### 5. Sequential Thinking ✅

**Назначение:** Последовательное мышление для сложных задач анализа.

```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
}
```

**Возможности:**

- Пошаговый анализ кода
- Декомпозиция сложных задач
- Структурированное решение проблем

---

### 6. Playwright ⚠️ (Отключен)

**Назначение:** Автоматизация браузера для интеграционных тестов.

```json
{
  "command": "npx",
  "args": ["-y", "@playwright/mcp@latest"]
}
```

**Возможности:**

- E2E тестирование
- Скриншоты страниц
- Автоматизация UI тестов

**Требования:**

- Установленный Playwright (`playwright install`)

---

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Установка MCP CLI
pip install "mcp[cli]"

# Проверка версии
mcp version
```

### 2. Активация серверов

Отредактируйте `.qwen/mcp.json` и измените `disabled: true` на `disabled: false` для нужных серверов.

### 3. Настройка Redis

**Вариант A: Docker (рекомендуется)**

```bash
# Запуск Redis
docker run -d --name shadow-redis -p 6379:6379 --restart unless-stopped redis:7-alpine

# Проверка
docker exec shadow-redis redis-cli ping
# Должен вернуть: PONG

# Управление Redis (Windows)
redis.bat start
redis.bat stop
redis.bat status
redis.bat logs

# Управление Redis (Linux/Mac)
./redis.sh start
./redis.sh stop
./redis.sh status
```

**Вариант B: Нативная установка**

Установите Redis с https://redis.io/download

### 4. Настройка переменных окружения

Создайте файл `.env` (если не существует):

```bash
# GitHub token (для GitHub MCP сервера)
GITHUB_TOKEN=ghp_your_token_here

# Redis URL (для Redis MCP сервера)
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

---

## 📊 Использование с этапы проекта

| Этап                     | Рекомендуемые MCP серверы            |
| ------------------------ | ------------------------------------ |
| **Этап 1: Кэширование**  | `filesystem`, `redis`                |
| **Этап 2: Метрики**      | `filesystem`, `fetch`                |
| **Этап 3: Админ-панель** | `filesystem`, `playwright`           |
| **Этап 4: Рефакторинг**  | `filesystem`, `sequential-thinking`  |
| **Этап 5: Интеграция**   | `filesystem`, `github`, `playwright` |
| **Этап 6: Тесты**        | `filesystem`, `playwright`, `fetch`  |

---

## 🔐 Безопасность

### Рекомендации

1. **Не коммитьте `.qwen/mcp.json` с токенами** — используйте переменные окружения
2. **Ограничьте доступ filesystem** — только директория проекта
3. **Используйте Docker для GitHub** — изоляция от основной системы

### Переменные окружения

```bash
# .env (не коммитить в git!)
GITHUB_TOKEN=ghp_...
REDIS_URL=redis://localhost:6379/0
```

---

## 🛠 Устранение неполадок

### MCP сервер не запускается

```bash
# Проверка установки
pip show mcp

# Переустановка
pip uninstall mcp && pip install "mcp[cli]"
```

### Redis не подключается

```bash
# Проверка Redis (Docker)
docker ps --filter "name=shadow-redis"
docker exec shadow-redis redis-cli ping

# Перезапуск Redis
docker restart shadow-redis

# Или через скрипт
redis.bat restart
```

### GitHub сервер требует Docker

```bash
# Проверка Docker
docker --version

# Проверка, что Docker запущен
docker ps

# Если Docker не запущен - запустите Docker Desktop
```

### Ошибки кэширования в приложении

```bash
# Проверка подключения к Redis
python -c "import redis; r = redis.Redis(); print(r.ping())"

# Должно вернуть: True

# Просмотр логов Redis
docker logs shadow-redis

# Очистка Redis
docker exec shadow-redis redis-cli FLUSHALL
```

---

## 📚 Ссылки

- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP Server Registry](https://github.com/modelcontextprotocol/servers)
- [Windsurf Documentation](https://docs.windsurf.ai/)

---

_Этот файл следует обновлять при изменении конфигурации MCP._
