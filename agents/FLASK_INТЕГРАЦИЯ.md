# 🔌 Интеграция с Flask приложением

## 📋 Обзор

Система агентов интегрирована в ваше Flask приложение через Blueprint.
Это предоставляет REST API для управления агентами через HTTP запросы.

## 🚀 Подключение

### Шаг 1: Зарегистрируйте Blueprint в app.py

Откройте `app.py` и добавьте регистрацию blueprint в функцию `register_blueprints`:

```python
def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints."""
    # Main blueprint (leaderboard page)
    from blueprints.main import main
    app.register_blueprint(main)

    # Health check blueprint
    from blueprints.health import health
    app.register_blueprint(health)
    
    # =====> ДОБАВЬТЕ ЭТУ СТРОКУ <======
    # Agents blueprint (API для системы агентов)
    from agents.blueprint import agents_bp
    app.register_blueprint(agents_bp)
    # ====================================

    # API blueprint (if enabled)
    if app.config.get("ENABLE_API"):
        from services.api import api
        app.register_blueprint(api)
        # Exempt API from CSRF (uses API Key auth instead)
        if 'csrf' in app.extensions:
            app.extensions['csrf'].exempt(api)
    else:
        app.logger.info("REST API is disabled in this environment (ENABLE_API=False)")
```

### Шаг 2: Запустите приложение

```bash
python app.py
```

### Шаг 3: Проверьте API

```bash
# Проверка статуса
curl http://localhost:5000/api/agents/status

# Переключение режима
curl -X POST http://localhost:5000/api/agents/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "automatic"}'
```

## 📡 API Endpoints

### 1. Статус системы

```http
GET /api/agents/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "mode": "automatic",
    "agents": {
      "ANALYST": {
        "role": "ANALYST",
        "mode": "automatic",
        "tasks_completed": 5,
        "tasks_failed": 0,
        "total_tasks": 5
      }
    },
    "delegation_count": 2,
    "context_size": {
      "state_summary.md": {"chars": 1234, "tokens": 308},
      "total": {"chars": 5678, "tokens": 1419}
    }
  }
}
```

### 2. Выполнение задачи

```http
POST /api/agents/execute
Content-Type: application/json

{
  "role": "ANALYST",
  "task": "Проанализировать требования для системы уведомлений",
  "mode": "automatic"  // optional
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analysis": "Analysis completed",
    "task": "Проанализировать требования..."
  },
  "metadata": {},
  "artifacts": {
    "task": "Проанализировать требования...",
    "status": "analyzed"
  }
}
```

### 3. Выполнение воркфлоу

```http
POST /api/agents/workflow
Content-Type: application/json

{
  "workflow": [
    {"role": "ANALYST", "task": "Анализ требований"},
    {"role": "ARCHITECT", "task": "Проектирование архитектуры"},
    {"role": "DEVELOPER", "task": "Реализация"}
  ],
  "mode": "automatic"
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "success": true,
      "data": {...},
      "error": null,
      "needs_delegation": false,
      "delegation": null
    }
  ],
  "total": 3,
  "successful": 3
}
```

### 4. Переключение режима

```http
POST /api/agents/mode
Content-Type: application/json

{
  "mode": "manual"  // automatic, manual, hybrid
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "mode": "manual"
  }
}
```

### 5. Получение текущего режима

```http
GET /api/agents/mode
```

**Response:**
```json
{
  "success": true,
  "data": {
    "mode": "automatic"
  }
}
```

### 6. Статус контекста

```http
GET /api/agents/context
```

**Response:**
```json
{
  "success": true,
  "data": {
    "size": {
      "state_summary.md": {"chars": 1234, "tokens": 308},
      "total": {"chars": 5678, "tokens": 1419}
    },
    "needs_summarization": false
  }
}
```

### 7. Суммаризация контекста

```http
POST /api/agents/context/summarize
Content-Type: application/json

{
  "summary": "Краткая версия контекста..."
}
```

### 8. Сброс состояния

```http
POST /api/agents/reset
```

### 9. Получение .windsurfrules

```http
GET /api/agents/windsurfrules
```

**Response:**
```json
{
  "success": true,
  "data": {
    "rules": "# 🧠 MASTER ROUTER & CONTEXT MANAGER...",
    "available": true
  }
}
```

## 🔧 Примеры использования

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:5000/api/agents"

# Проверка статуса
response = requests.get(f"{BASE_URL}/status")
print(response.json())

# Выполнение задачи
response = requests.post(
    f"{BASE_URL}/execute",
    json={
        "role": "ANALYST",
        "task": "Проанализировать требования"
    }
)
print(response.json())

# Выполнение воркфлоу
response = requests.post(
    f"{BASE_URL}/workflow",
    json={
        "workflow": [
            {"role": "ANALYST", "task": "Анализ"},
            {"role": "DEVELOPER", "task": "Разработка"}
        ],
        "mode": "automatic"
    }
)
print(response.json())

# Переключение режима
response = requests.post(
    f"{BASE_URL}/mode",
    json={"mode": "manual"}
)
print(response.json())
```

### JavaScript (fetch)

```javascript
const BASE_URL = '/api/agents';

// Проверка статуса
const status = await fetch(`${BASE_URL}/status`);
const statusData = await status.json();
console.log(statusData);

// Выполнение задачи
const response = await fetch(`${BASE_URL}/execute`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    role: 'ANALYST',
    task: 'Проанализировать требования'
  })
});
const data = await response.json();
console.log(data);

// Выполнение воркфлоу
const workflowResponse = await fetch(`${BASE_URL}/workflow`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    workflow: [
      {role: 'ANALYST', task: 'Анализ'},
      {role: 'DEVELOPER', task: 'Разработка'}
    ],
    mode: 'automatic'
  })
});
```

### cURL

```bash
# Проверка статуса
curl http://localhost:5000/api/agents/status

# Выполнение задачи
curl -X POST http://localhost:5000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"role": "ANALYST", "task": "Анализ требований"}'

# Выполнение воркфлоу
curl -X POST http://localhost:5000/api/agents/workflow \
  -H "Content-Type: application/json" \
  -d '{
    "workflow": [
      {"role": "ANALYST", "task": "Анализ"},
      {"role": "DEVELOPER", "task": "Разработка"}
    ],
    "mode": "automatic"
  }'

# Переключение режима
curl -X POST http://localhost:5000/api/agents/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "manual"}'
```

## 🛡️ Безопасность

### CSRF Protection

Blueprint автоматически освобождается от CSRF защиты (в app.py):

```python
# В register_blueprints
if 'csrf' in app.extensions:
    app.extensions['csrf'].exempt(agents_bp)
```

### Rate Limiting

API endpoints защищены rate limiting через Flask-Limiter (настроен в app.py).

### API Keys

Для production рекомендуется добавить API Key аутентификацию (аналогично existing API blueprint).

## 📊 Мониторинг

### Prometheus Metrics

Все запросы к API агентов автоматически логируются и могут быть отслежены через Prometheus.

### Logging

```python
import logging

# Включите логирование для отладки
logging.getLogger("agents").setLevel(logging.DEBUG)
```

## ⚠️ Важно

- ✅ Blueprint **не модифицирует** старые файлы
- ✅ `.windsurfrules` остаётся рабочим
- ✅ Можно переключиться на ручной режим в любой момент
- ✅ Fallback на локальных агентов при ошибках

## 🎯 Следующие шаги

1. Добавьте UI для управления агентами (Admin panel)
2. Настройте мониторинг через Prometheus
3. Добавьте WebSocket для real-time обновлений
4. Интегрируйте с Qwen Subagents API когда станет доступен
