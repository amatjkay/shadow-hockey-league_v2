# 🔴 Redis: Настройка, запуск и управление кэшем

**Версия:** 1.0
**Дата:** 3 апреля 2026 г.

---

## 📋 Обзор

Shadow Hockey League использует Redis для кэширования leaderboard с автоматической инвалидацией при изменении данных.

**Ключевые особенности:**
- Кэш leaderboard: 5 минут (300 секунд)
- Автоматическая инвалидация при CRUD операциях через Admin и API
- Fallback на SimpleCache если Redis недоступен
- Health check endpoint для мониторинга

---

## 🔧 Требования

| Компонент | Минимум | Рекомендуется |
|-----------|---------|---------------|
| Redis | 6.0+ | 7.0+ |
| Python redis | >=5.0.0 | >=5.0.0 |
| Flask-Caching | >=2.0.0 | >=2.0.0 |

---

## 🚀 Запуск Redis

### Windows (Docker)

```bash
# Установка и запуск
.\redis.bat install
.\redis.bat start

# Проверка статуса
.\redis.bat status

# Просмотр логов
.\redis.bat logs

# Подключение к CLI
.\redis.bat cli

# Остановка
.\redis.bat stop

# Перезапуск
.\redis.bat restart
```

### Linux/Mac (Docker)

```bash
# Установка и запуск
./redis.sh install
./redis.sh start

# Проверка статуса
./redis.sh status

# Просмотр логов
./redis.sh logs

# Подключение к CLI
./redis.sh cli

# Остановка
./redis.sh stop

# Перезапуск
./redis.sh restart
```

### Ручной запуск (без Docker)

```bash
# Установка Redis (Ubuntu/Debian)
sudo apt update && sudo apt install redis-server

# Запуск
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Проверка
redis-cli ping
# Ожидается: PONG
```

---

## ⚙️ Конфигурация

### Переменные окружения (.env)

```bash
# Redis connection
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # оставить пустым если без пароля

# Cache settings
CACHE_DEFAULT_TIMEOUT=300  # 5 минут
```

### Docker контейнер

```yaml
# redis.bat / redis.sh используют:
# Image: redis:7-alpine
# Port: 6379:6379
# Container name: shadow-redis
# Restart policy: unless-stopped
```

---

## 📊 Мониторинг

### Health Check

```bash
# Проверка через API
curl http://localhost:5000/health

# Ответ включает:
{
  "redis_status": "connected",    # или "disconnected"
  "cache_status": "working",      # или "error", "fallback"
  "cache_type": "RedisCache",     # или "SimpleCache"
  "redis_used_memory_mb": 2.5     # потребление памяти
}
```

### Redis CLI

```bash
# Подключение
.\redis.bat cli   # Windows
./redis.sh cli    # Linux/Mac

# Проверка ключей
KEYS *

# Проверка leaderboard кэша
GET leaderboard

# Статистика
INFO stats

# Потребление памяти
INFO memory

# Очистка всех ключей
FLUSHDB
```

---

## 🔄 Инвалидация кэша

### Автоматическая инвалидация

Кэш leaderboard автоматически инвалидируется при:

| Операция | Admin Panel | API |
|----------|-------------|-----|
| Создание страны | ✅ | ✅ |
| Обновление страны | ✅ | ✅ |
| Удаление страны | ✅ | ✅ |
| Создание менеджера | ✅ | ✅ |
| Обновление менеджера | ✅ | ✅ |
| Удаление менеджера | ✅ | ✅ |
| Создание достижения | ✅ | ✅ |
| Обновление достижения | ✅ | ✅ |
| Удаление достижения | ✅ | ✅ |

### Ручная инвалидация

```python
# Через Python shell
from app import create_app
from services.cache_service import invalidate_leaderboard_cache

app = create_app()
with app.app_context():
    invalidate_leaderboard_cache()
    print("Leaderboard cache invalidated")
```

### CLI команда (планируется)

```bash
# Будет добавлено в manage.py
python manage.py invalidate-cache
```

---

## ⚠️ Fallback режим

Если Redis недоступен при запуске приложения:

1. **Автоматический fallback** на `SimpleCache` (in-memory)
2. **Логирование** предупреждения: `Redis not available, falling back to simple cache`
3. **Кэш работает** но не распределённый

### Ограничения SimpleCache

| Характеристика | RedisCache | SimpleCache |
|----------------|------------|-------------|
| Распределённый | ✅ Да | ❌ Нет |
| Сохраняется при рестарте | ✅ Да | ❌ Нет |
| Multiple workers | ✅ Да | ❌ Нет |
| Memory limit | Настраиваемый | RAM процесса |

### Когда SimpleCache проблематичен

- **Gunicorn с multiple workers**: каждый worker имеет свой кэш
- **Перезапуск приложения**: кэш теряется
- **Горизонтальное масштабирование**: кэш не синхронизируется

**Решение:** Убедитесь что Redis запущен перед стартом приложения в production.

---

## 🐛 Устранение неполадок

### Redis не запускается

```bash
# Проверить Docker
docker ps | grep shadow-redis

# Если не запущен
.\redis.bat start   # Windows
./redis.sh start    # Linux/Mac

# Проверить порт
netstat -an | findstr 6379   # Windows
lsof -i :6379                # Linux/Mac
```

### Приложение не подключается к Redis

```bash
# Проверить переменные окружения
echo $REDIS_HOST
echo $REDIS_PORT

# Проверить Redis
redis-cli ping
# Ожидается: PONG

# Проверить логи приложения
grep -i "redis" logs/app.log
```

### Кэш не инвалидируется

```bash
# Проверить ключ в Redis
.\redis.bat cli
GET leaderboard

# Если ключ есть - кэш не инвалидирован
# Если ключа нет - инвалидация сработала

# Ручная инвалидация
DEL leaderboard
```

### Кэш не обновляется

```bash
# Проверить что приложение запущено
curl http://localhost:5000/health

# Проверить cache_type
# В health response: "cache_type": "RedisCache" или "SimpleCache"

# Если SimpleCache но Redis запущен:
# 1. Перезапустите приложение
# 2. Проверьте REDIS_HOST в .env
```

---

## 📈 Производительность

### Метрики кэша

| Метрика | Значение | Комментарий |
|---------|----------|-------------|
| Timeout | 300s | 5 минут |
| Key | `leaderboard` | Единственный ключ |
| Hit ratio | ~95%+ | При активной нагрузке |
| Generation time | 10-50ms | Single query с joinedload |

### Оптимизация

- **Eager loading**: `joinedload` предотвращает N+1 queries
- **Single query**: Все данные загружаются одним запросом
- **Сортировка**: В памяти после выборки (эффективно для <1000 записей)

---

## 🔒 Безопасность

### Production рекомендации

1. **Установите пароль на Redis**:
   ```bash
   REDIS_PASSWORD=your-secure-password
   ```

2. **Ограничьте доступ к Redis**:
   ```bash
   # redis.conf
   bind 127.0.0.1
   protected-mode yes
   ```

3. **Используйте отдельную БД**:
   ```bash
   REDIS_DB=1  # не 0 для isolation
   ```

---

## 📝 Чеклист запуска

Перед запуском приложения:

- [ ] Redis установлен (`redis-cli ping` → PONG)
- [ ] Redis запущен (`.\redis.bat status` → running)
- [ ] Переменные окружения заданы (`.env` с REDIS_HOST, REDIS_PORT)
- [ ] Приложение запущено и подключено к Redis
- [ ] Health check показывает `redis_status: connected`
- [ ] Кэш работает (`GET leaderboard` в Redis CLI после первого запроса)

---

**Последнее обновление:** 3 апреля 2026 г.
**Версия документа:** 1.0
