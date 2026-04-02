# 📊 Мониторинг Shadow Hockey League

**Версия:** 1.0  
**Дата:** 2 апреля 2026 г.

---

## 🎯 Обзор

Приложение предоставляет эндпоинты для мониторинга доступности и производительности.

---

## 🏥 Health Check (`/health`)

### Запрос

```bash
curl https://shadow-hockey-league.ru/health
```

### Ответ

```json
{
  "status": "healthy",
  "timestamp": "2026-04-02T12:00:00Z",
  "uptime_seconds": 3600,
  "managers_count": 50,
  "achievements_count": 200,
  "countries_count": 8,
  "response_time_ms": 15,
  "redis_status": "connected",
  "cache_status": "working",
  "database_status": "connected",
  "database_size_mb": 2.5
}
```

### Поля

| Поле                 | Тип    | Описание                           |
| -------------------- | ------ | ---------------------------------- |
| `status`             | string | `healthy`, `degraded`, `unhealthy` |
| `timestamp`          | string | Время проверки (UTC)               |
| `uptime_seconds`     | number | Время работы (секунды)             |
| `managers_count`     | number | Количество менеджеров в БД         |
| `achievements_count` | number | Количество достижений              |
| `countries_count`    | number | Количество стран                   |
| `response_time_ms`   | number | Время выполнения (мс)              |
| `redis_status`       | string | `connected`, `disconnected`        |
| `cache_status`       | string | `working`, `error`, `fallback`     |
| `database_status`    | string | `connected`, `error`               |
| `database_size_mb`   | number | Размер БД (MB)                     |

### Статусы

- **`healthy`** — все компоненты работают
- **`degraded`** — частичная деградация (например, Redis недоступен)
- **`unhealthy`** — критическая ошибка (БД недоступна)

---

## 📈 Prometheus Metrics (`/metrics`)

### Запрос

```bash
curl https://shadow-hockey-league.ru/metrics
```

### Метрики

| Метрика                                              | Описание             | Тип       |
| ---------------------------------------------------- | -------------------- | --------- |
| `shadow_hockey_league_http_requests_total`           | Всего запросов       | Counter   |
| `shadow_hockey_league_http_request_duration_seconds` | Время ответа         | Histogram |
| `shadow_hockey_league_http_requests_in_progress`     | Запросов в обработке | Gauge     |

### Метки (Labels)

- `endpoint` — маршрут (`/`, `/health`)
- `method` — HTTP метод (GET, POST)
- `status` — HTTP статус (200, 404, 500)

---

## 🖥 VPS Мониторинг

### Панель провайдера (ztv.su)

**Доступные метрики:**

- CPU — использование процессора (%)
- RAM — использование памяти (MB / 1024 MB)
- Disk — использование диска (MB / 10240 MB)
- Network — входящий/исходящий трафик

### Нормальные значения

| Метрика       | Норма     | Критично   |
| ------------- | --------- | ---------- |
| CPU           | < 50%     | > 90%      |
| RAM           | < 800 MB  | > 950 MB   |
| Disk          | < 8000 MB | > 10000 MB |
| Response time | < 100 ms  | > 1000 ms  |
| Uptime        | 100%      | < 99%      |

---

## 🐛 Устранение неполадок

### `/health` возвращает 500

**Причина:** Ошибка БД или кэша

**Решение:**

```bash
# Проверьте логи
sudo journalctl -u shadow-hockey-league -f

# Проверьте БД
python scripts/validate_db.py

# Перезапустите приложение
systemctl restart shadow-hockey-league
```

### Redis не подключается

**Причина:** Redis не запущен

**Решение:**

```bash
# Проверьте статус
sudo systemctl status redis

# Запустите
sudo systemctl start redis
```

### Высокое время ответа

**Причина:** Медленная БД или перегрузка CPU

**Решение:**

1. Проверьте VPS мониторинг (CPU/RAM)
2. Проверьте размер БД
3. Проверьте логи на ошибки

---

**Последнее обновление:** 2 апреля 2026 г.
