# 📊 Мониторинг Shadow Hockey League

Руководство по мониторингу приложения: метрики, health checks и VPS мониторинг.

---

## 🎯 Обзор

Приложение предоставляет следующие эндпоинты для мониторинга:

| Эндпоинт | Описание | Формат |
|----------|----------|--------|
| `/health` | Расширенная проверка здоровья | JSON |
| `/metrics` | Prometheus метрики | Prometheus text format |

---

## 🏥 Health Check (`/health`)

### Пример запроса

```bash
curl https://shadow-hockey-league.ru/health
```

### Пример ответа

```json
{
  "status": "healthy",
  "timestamp": "2026-04-02T00:00:00Z",
  "uptime_seconds": 3600,
  "managers_count": 50,
  "achievements_count": 200,
  "countries_count": 8,
  "response_time_ms": 15,
  "redis_status": "connected",
  "redis_used_memory_mb": 12.5,
  "cache_status": "working",
  "database_status": "connected",
  "database_size_mb": 2.5
}
```

### Поля ответа

| Поле | Тип | Описание |
|------|-----|----------|
| `status` | string | Общий статус: `healthy`, `degraded`, `unhealthy` |
| `timestamp` | string | Время проверки (UTC) |
| `uptime_seconds` | number | Время работы приложения (секунды) |
| `managers_count` | number | Количество менеджеров в БД |
| `achievements_count` | number | Количество достижений в БД |
| `countries_count` | number | Количество стран в БД |
| `response_time_ms` | number | Время выполнения проверки (мс) |
| `redis_status` | string | Статус Redis: `connected`, `disconnected`, `unknown` |
| `redis_used_memory_mb` | number | Используемая память Redis (MB) |
| `cache_status` | string | Статус кэша: `working`, `error`, `fallback` |
| `database_status` | string | Статус БД: `connected`, `error` |
| `database_size_mb` | number | Размер файла БД (MB) |

### Статусы

- **`healthy`** — все компоненты работают
- **`degraded`** — частичная деградация (например, Redis недоступен, но работает SimpleCache)
- **`unhealthy`** — критическая ошибка (БД недоступна)

---

## 📈 Prometheus Metrics (`/metrics`)

### Пример запроса

```bash
curl https://shadow-hockey-league.ru/metrics
```

### Пример ответа

```
# HELP shadow_hockey_league_http_requests_total Total number of HTTP requests
# TYPE shadow_hockey_league_http_requests_total counter
shadow_hockey_league_http_requests_total{endpoint="/",method="GET",status="200"} 150.0

# HELP shadow_hockey_league_http_request_duration_seconds HTTP request duration in seconds
# TYPE shadow_hockey_league_http_request_duration_seconds histogram
shadow_hockey_league_http_request_duration_seconds_bucket{endpoint="/",le="0.005"} 120.0
shadow_hockey_league_http_request_duration_seconds_bucket{endpoint="/",le="0.01"} 145.0
shadow_hockey_league_http_request_duration_seconds_bucket{endpoint="/",le="0.025"} 150.0
```

### Доступные метрики

| Метрика | Описание | Тип |
|---------|----------|-----|
| `http_requests_total` | Всего запросов | Counter |
| `http_request_duration_seconds` | Время ответа | Histogram |
| `http_requests_in_progress` | Запросов в обработке | Gauge |

### Метки (Labels)

- `endpoint` — маршрут (например, `/`, `/health`)
- `method` — HTTP метод (GET, POST, etc.)
- `status` — HTTP статус (200, 404, 500)

---

## 🖥 VPS Мониторинг (ztv.su)

### Доступные метрики в панели ztv.su

1. **CPU** — использование процессора (%)
2. **RAM** — использование оперативной памяти (MB / 1024 MB)
3. **Диск** — использование дискового пространства (MB / 10240 MB)
4. **Сеть** — входящий/исходящий трафик (MB)

### Как настроить HTTP монитор

1. Войдите в панель управления ztv.su
2. Перейдите в раздел "Мониторинг" или "Monitoring"
3. Добавьте новый HTTP монитор:
   - **URL:** `https://shadow-hockey-league.ru/health`
   - **Интервал:** 60 секунд
   - **Метод:** GET
   - **Ожидаемый статус:** 200
4. Сохраните настройки

### Что отслеживать

| Метрика | Нормальное значение | Критическое значение |
|---------|---------------------|----------------------|
| CPU | < 50% | > 90% |
| RAM | < 800 MB | > 950 MB |
| Диск | < 8000 MB | > 10000 MB |
| Response time (`/health`) | < 100 ms | > 1000 ms |
| Uptime | 100% | < 99% |

---

## 🔧 Настройка для production

### Переменные окружения

```bash
# Redis (опционально, иначе используется SimpleCache)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_password

# Логирование
LOG_LEVEL=INFO

# Режим работы
FLASK_ENV=production
```

### Проверка подключения к Redis

```bash
# Локально
redis-cli ping
# Должен вернуть: PONG

# На VPS
ssh user@server
redis-cli ping
```

---

## 📊 Интерпретация метрик

### Здоровое приложение

```json
{
  "status": "healthy",
  "redis_status": "connected",
  "cache_status": "working",
  "database_status": "connected",
  "response_time_ms": 15
}
```

### Частичная деградация (Redis недоступен)

```json
{
  "status": "degraded",
  "redis_status": "disconnected",
  "cache_status": "fallback",
  "cache_type": "SimpleCache",
  "database_status": "connected",
  "response_time_ms": 25
}
```

⚠️ **Не критично:** Приложение работает с fallback кэшем.

### Критическая ошибка (БД недоступна)

```json
{
  "status": "unhealthy",
  "database_status": "error",
  "database_error": "no such table: managers",
  "response_time_ms": 5
}
```

️ **Требует вмешательства:** Проверьте БД, логи приложения.

---

## 🐛 Устранение неполадок

### `/health` возвращает 500

**Причина:** Ошибка БД или кэша.

**Решение:**
```bash
# Проверьте логи
tail -f logs/app.log

# Проверьте БД
python scripts/validate_db.py

# Перезапустите приложение
systemctl restart shadow-hockey-league
```

### Redis не подключается

**Причина:** Redis не запущен или недоступен.

**Решение:**
```bash
# Проверьте статус Redis
sudo systemctl status redis

# Запустите Redis
sudo systemctl start redis

# Проверьте логи Redis
sudo journalctl -u redis
```

### Высокое время ответа (`response_time_ms > 1000`)

**Причина:** Медленная БД или перегрузка CPU.

**Решение:**
1. Проверьте VPS мониторинг (CPU/RAM)
2. Проверьте размер БД
3. Проверьте логи на наличие ошибок
4. Рассмотрите включение кэширования

---

## 📝 Чек-лист мониторинга

- [ ] `/health` возвращает `status: healthy`
- [ ] `response_time_ms < 100`
- [ ] `redis_status: connected` (если Redis используется)
- [ ] `cache_status: working`
- [ ] `database_status: connected`
- [ ] VPS CPU < 50%
- [ ] VPS RAM < 800 MB
- [ ] VPS Диск < 8000 MB

---

**Последнее обновление:** 2 апреля 2026 г.  
**Версия документа:** 1.0
