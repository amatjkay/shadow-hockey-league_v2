# Operations Guide — Shadow Hockey League v2

**Версия:** 2.6.0
**Дата:** 13 апреля 2026 г.

---

## 1. Админ-панель

### Первый вход

```bash
source venv/bin/activate
python scripts/create_admin.py
```

**URL:** `/admin/`

### Возможности

- CRUD: страны, менеджеры, достижения, типы достижений, сезоны, лиги
- Реактивный калькулятор очков
- Bulk-операции для массового создания достижений
- Audit Log всех действий
- Flush Cache кнопка

---

## 2. Безопасность

| Механизм | Описание |
|----------|----------|
| **Admin Auth** | Flask-Login (session-based) |
| **API Auth** | API Key (SHA-256 hash) |
| **CSRF** | Flask-WTF для всех форм |
| **Rate Limiting** | 100 req/min |
| **SSL** | Let's Encrypt |

---

## 3. Мониторинг

### Health Check (`/health`)

```bash
curl https://shadow-hockey-league.ru/health
```

### Prometheus Metrics (`/metrics`)

Используется для сбора метрик через Prometheus/Grafana.

### Caching

- **Redis:** `localhost:6379`
- **TTL:** 5 минут
- **Инвалидация:** автоматическая при мутациях
- **Flush:** кнопка в админке

---

## 4. Бэкапы и откат

### Бэкапы

- **Ежедневно:** 03:00 UTC (cron)
- **Pre-deploy:** перед каждым деплоем
- **Retention:** 10 последних бэкапов

### Откат

```bash
# Автоматический — при failed health check
# Ручной — через GitHub Actions Workflow Dispatch
```

---

*Последнее обновление: 13 апреля 2026 г.*
