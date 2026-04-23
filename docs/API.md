# Shadow Hockey League REST API Documentation

**Base URL:** `https://shadow-hockey-league.ru/api` (production) | `http://127.0.0.1:5000/api` (dev)
**Version:** 2.1
**Format:** JSON
**Дата:** 13 апреля 2026 г.

---

## 📋 Overview

REST API предоставляет CRUD-операции для управления странами, менеджерами и достижениями в системе Shadow Hockey League.

**Возможности:**

- ✅ Аутентификация через API Keys (3 уровня доступа)
- ✅ Пагинация для списковых endpoints
- ✅ Rate limiting (100 req/min на ключ)
- ✅ Автоматическая инвалидация кэша leaderboard
- ✅ Валидация данных и уникальные ограничения

---

## 🔐 Аутентификация

Все API-эндпоинты (кроме `/api/countries` GET) требуют аутентификации через API-ключ.

### API Keys

Ключ передаётся в заголовке `X-API-Key`:

```bash
curl -H "X-API-Key: shl_abc123..." https://shadow-hockey-league.ru/api/managers
```

### Scopes (уровни доступа)

| Scope   | Описание        | Доступные методы               |
| ------- | --------------- | ------------------------------ |
| `read`  | Только чтение   | `GET`                          |
| `write` | Чтение + запись | `GET`, `POST`, `PUT`           |
| `admin` | Полный доступ   | `GET`, `POST`, `PUT`, `DELETE` |

### Иерархия scopes

```
admin > write > read
```

- `admin` ключ может выполнять все операции
- `write` ключ может читать и создавать/обновлять, но не удалять
- `read` ключ может только получать данные

### Ошибки аутентификации

| Код | Описание                          | Решение                                 |
| --- | --------------------------------- | --------------------------------------- |
| 401 | Отсутствует заголовок `X-API-Key` | Добавить заголовок                      |
| 401 | Неверный API-ключ                 | Проверить ключ или создать новый        |
| 401 | Ключ отозван (revoked)            | Создать новый ключ                      |
| 401 | Ключ истёк (expired)              | Создать новый ключ или увеличить срок   |
| 403 | Недостаточный scope               | Использовать ключ с более широким scope |

### Примеры ошибок

**401 — Missing API key:**

```json
{
  "error": "Missing API key. Provide X-API-Key header."
}
```

**401 — Invalid API key:**

```json
{
  "error": "Invalid API key."
}
```

**401 — Expired API key:**

```json
{
  "error": "API key has expired."
}
```

**403 — Insufficient scope:**

```json
{
  "error": "Insufficient scope. Required: admin, has: read"
}
```

---

## 🔑 Управление API-ключами

API-ключи создаются и отзываются через админ-панель (`/admin/`) или программно.

### Создание ключа (программно)

```python
from services.api_auth import create_api_key

# Создать read-ключ без срока действия
plain_key, api_key = create_api_key(name="My App", scope="read")
print(f"API Key: {plain_key}")  # Сохранить — больше не покажется!

# Создать write-ключ на 90 дней
plain_key, api_key = create_api_key(name="Integration", scope="write", expires_in_days=90)

# Создать admin-ключ на 365 дней
plain_key, api_key = create_api_key(name="Admin Tool", scope="admin", expires_in_days=365)
```

### Отзыв ключа (программно)

```python
from services.api_auth import revoke_api_key

revoke_api_key(key_id=1)  # True если ключ найден и отозван
```

### Модель ApiKey

| Поле           | Тип              | Описание                   |
| -------------- | ---------------- | -------------------------- |
| `id`           | int              | Автоинкремент              |
| `key_hash`     | str(64)          | SHA-256 хеш ключа          |
| `name`         | str              | Человекочитаемое имя       |
| `scope`        | str              | `read` / `write` / `admin` |
| `created_at`   | datetime         | Дата создания              |
| `last_used_at` | datetime         | Последнее использование    |
| `expires_at`   | datetime \| None | Дата истечения             |
| `revoked`      | bool             | Флаг отзыва                |

---

## 🚦 Rate Limiting

Все эндпоинты ограничены **100 запросов в минуту** на один API-ключ.

- Лимит считается по заголовку `X-API-Key` (или IP, если ключа нет)
- При превышении возвращается `429 Too Many Requests`
- Лимит общий для всех эндпоинтов

**Пример ответа при rate limit:**

```json
{
  "error": "Too many requests"
}
```

---

## 📄 Пагинация

Списковые endpoints (`GET /api/managers`, `GET /api/achievements`) поддерживают пагинацию.

### Параметры

| Параметр   | Тип | По умолчанию | Максимум | Описание            |
| ---------- | --- | ------------ | -------- | ------------------- |
| `page`     | int | 1            | —        | Номер страницы      |
| `per_page` | int | 20           | 100      | Записей на страницу |

### Response wrapper

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

### Примеры

```bash
# Первая страница, 20 записей (по умолчанию)
curl -H "X-API-Key: KEY" https://shadow-hockey-league.ru/api/managers

# Страница 3, по 50 записей
curl -H "X-API-Key: KEY" "https://shadow-hockey-league.ru/api/managers?page=3&per_page=50"

# Максимальный лимит (100 записей)
curl -H "X-API-Key: KEY" "https://shadow-hockey-league.ru/api/managers?per_page=100"
```

> **Примечание:** `GET /api/countries` **не использует пагинацию** (~22 записи, не растёт).

---

## 📡 Endpoints

### 🌍 Countries

| Метод  | Эндпоинт              | Auth | Scope   | Описание                   |
| ------ | --------------------- | ---- | ------- | -------------------------- |
| GET    | `/api/countries`      | ❌   | —       | Все страны (без пагинации) |
| GET    | `/api/countries/<id>` | ❌   | —       | Страна по ID               |
| POST   | `/api/countries`      | ✅   | `write` | Создать страну             |
| PUT    | `/api/countries/<id>` | ✅   | `write` | Обновить страну            |
| DELETE | `/api/countries/<id>` | ✅   | `admin` | Удалить страну             |

#### GET /api/countries

**Response:**

```json
[
  {
    "id": 1,
    "code": "RUS",
    "flag_path": "/static/img/flags/rus.png"
  }
]
```

#### POST /api/countries

**Request:**

```json
{
  "code": "USA",
  "flag_path": "/static/img/flags/usa.png"
}
```

**Response (201):**

```json
{
  "id": 3,
  "code": "USA",
  "flag_path": "/static/img/flags/usa.png",
  "message": "Country created successfully"
}
```

**Ошибки:**

- `400` — Неверный формат (code должен быть 3 символа)
- `409` — Страна с таким кодом уже существует

#### DELETE /api/countries/<id>

**Ошибки:**

- `404` — Страна не найдена
- `409` — Нельзя удалить страну с менеджерами

---

### 👤 Managers

| Метод  | Эндпоинт             | Auth | Scope   | Описание                  |
| ------ | -------------------- | ---- | ------- | ------------------------- |
| GET    | `/api/managers`      | ✅   | `read`  | Все менеджеры (пагинация) |
| GET    | `/api/managers/<id>` | ✅   | `read`  | Менеджер по ID            |
| POST   | `/api/managers`      | ✅   | `write` | Создать менеджера         |
| PUT    | `/api/managers/<id>` | ✅   | `write` | Обновить менеджера        |
| DELETE | `/api/managers/<id>` | ✅   | `admin` | Удалить менеджера         |

#### GET /api/managers

**Query параметры:**

- `country_id` (int, optional) — Фильтр по стране
- `search` (str, optional) — Поиск по имени (case-insensitive)
- `page` (int, default: 1) — Страница
- `per_page` (int, default: 20, max: 100) — Записей на страницу

**Response:**

```json
{
  "data": [
    {
      "id": 1,
      "name": "Feel Good",
      "display_name": "Feel Good",
      "is_tandem": false,
      "country_id": 2,
      "country_code": "BEL",
      "achievements_count": 3
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

#### POST /api/managers

**Request:**

```json
{
  "name": "John Doe",
  "country_id": 1
}
```

**Для тандемов:**

```json
{
  "name": "Tandem: Player One, Player Two",
  "country_id": 1
}
```

**Response (201):**

```json
{
  "id": 5,
  "name": "John Doe",
  "display_name": "John Doe",
  "is_tandem": false,
  "country_id": 1,
  "message": "Manager created successfully"
}
```

**Ошибки:**

- `400` — Отсутствует имя или неверный country_id
- `409` — Менеджер с таким именем уже существует

#### GET /api/managers/<id>

**Response:**

```json
{
  "id": 1,
  "name": "Feel Good",
  "display_name": "Feel Good",
  "is_tandem": false,
  "country_id": 2,
  "country_code": "BEL",
  "achievements": [
    {
      "id": 1,
      "achievement_type": "TOP1",
      "league": "1",
      "season": "22/23",
      "title": "TOP1",
      "icon_path": "/static/img/cups/top1.svg"
    }
  ]
}
```

#### DELETE /api/managers/<id>

> **Внимание:** Удаление менеджера каскадно удаляет все его достижения.

---

### 🏆 Achievements

| Метод  | Эндпоинт                 | Auth | Scope   | Описание                   |
| ------ | ------------------------ | ---- | ------- | -------------------------- |
| GET    | `/api/achievements`      | ✅   | `read`  | Все достижения (пагинация) |
| GET    | `/api/achievements/<id>` | ✅   | `read`  | Достижение по ID           |
| POST   | `/api/achievements`      | ✅   | `write` | Создать достижение         |
| PUT    | `/api/achievements/<id>` | ✅   | `write` | Обновить достижение        |
| DELETE | `/api/achievements/<id>` | ✅   | `admin` | Удалить достижение         |

#### GET /api/achievements

**Query параметры:**

- `manager_id` (int, optional) — Фильтр по менеджеру
- `league` (str, optional) — Фильтр по лиге ("1" или "2")
- `season` (str, optional) — Фильтр по сезону (e.g., "24/25")
- `achievement_type` (str, optional) — Фильтр по типу (e.g., "TOP1")
- `page` (int, default: 1) — Страница
- `per_page` (int, default: 20, max: 100) — Записей на страницу

**Response:**

```json
{
  "data": [
    {
      "id": 1,
      "achievement_type": "TOP1",
      "league": "1",
      "season": "23/24",
      "title": "TOP1",
      "icon_path": "/static/img/cups/top1.svg",
      "manager_id": 1,
      "manager_name": "Feel Good"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 200,
    "pages": 10,
    "has_next": true,
    "has_prev": false
  }
}
```

#### POST /api/achievements

**Request:**

```json
{
  "achievement_type": "TOP1",
  "league": "1",
  "season": "24/25",
  "title": "Shadow 1 league TOP1",
  "icon_path": "/static/img/cups/top1.svg",
  "manager_id": 1
}
```

**Допустимые типы достижений:**
| Тип | Описание |
|-----|----------|
| `TOP1` | 1 место |
| `TOP2` | 2 место |
| `TOP3` | 3 место |
| `BEST` | Лучший регулярный сезон |
| `R3` | Раунд 3 |
| `R1` | Раунд 1 |

**Response (201):**

```json
{
  "id": 10,
  "achievement_type": "TOP1",
  "league": "1",
  "season": "24/25",
  "title": "Shadow 1 league TOP1",
  "icon_path": "/static/img/cups/top1.svg",
  "manager_id": 1,
  "message": "Achievement created successfully"
}
```

**Ошибки:**

- `400` — Неверный формат данных
- `404` — Менеджер не найден
- `409` — Достижение уже существует (unique: manager_id + league + season + type)

---

## 📊 Расчёт очков

Очки рассчитываются по формуле:

```
points = base_points(league, achievement_type) × season_multiplier
```

### Базовые очки

| Достижение   | Лига 1 | Лига 2 |
| ------------ | ------ | ------ |
| TOP1         | 800    | 300    |
| TOP2         | 550    | 200    |
| TOP3         | 450    | 100    |
| Best regular | 50     | 40     |
| Round 3      | 30     | 20     |
| Round 1      | 10     | 5      |

### Множители сезонов

| Сезон | Множитель       |
| ----- | --------------- |
| 24/25 | ×1.00 (базовый) |
| 23/24 | ×0.95 (−5%)     |
| 22/23 | ×0.90 (−10%)    |
| 21/22 | ×0.85 (−15%)    |

---

## 🔄 Cache Invalidation

Все эндпоинты, изменяющие данные (CREATE/UPDATE/DELETE), автоматически инвалидируют кэш leaderboard.

| Операция                     | Инвалидация кэша |
| ---------------------------- | ---------------- |
| POST /api/countries          | ✅               |
| PUT /api/countries/:id       | ✅               |
| DELETE /api/countries/:id    | ✅               |
| POST /api/managers           | ✅               |
| PUT /api/managers/:id        | ✅               |
| DELETE /api/managers/:id     | ✅               |
| POST /api/achievements       | ✅               |
| PUT /api/achievements/:id    | ✅               |
| DELETE /api/achievements/:id | ✅               |

---

## 🔒 Уникальные ограничения

### Achievements

Composite unique constraint: `(manager_id, league, season, achievement_type)`.

Попытка создать дубликат вернёт `409 Conflict`:

```json
{
  "error": "Achievement already exists for this manager, league, season, and type"
}
```

---

## 🧪 Тестирование

```bash
# Все тесты
make test

# Только API тесты
pytest tests/test_api.py tests/test_api_auth.py -v

# С покрытием
pytest --cov=services/api --cov=services/api_auth -v
```

---

## 📝 Примеры использования

### Полный CRUD цикл

```bash
# 1. Создать API-ключ (через Python)
python -c "from services.api_auth import create_api_key; print(create_api_key('My Key', 'admin')[0])"

# 2. Получить все страны (без auth)
curl https://shadow-hockey-league.ru/api/countries

# 3. Создать менеджера (write scope)
curl -X POST https://shadow-hockey-league.ru/api/managers \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"name":"New Manager","country_id":1}'

# 4. Добавить достижение (write scope)
curl -X POST https://shadow-hockey-league.ru/api/achievements \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"achievement_type":"TOP1","league":"1","season":"24/25","title":"TOP1","icon_path":"/static/img/cups/top1.svg","manager_id":1}'

# 5. Получить менеджера с достижениями (read scope)
curl -H "X-API-Key: YOUR_KEY" https://shadow-hockey-league.ru/api/managers/1

# 6. Удалить менеджера (admin scope)
curl -X DELETE -H "X-API-Key: YOUR_KEY" https://shadow-hockey-league.ru/api/managers/1
```

---

**Версия:** 2.0
**Дата:** 3 апреля 2026 г.
**Изменения:** Добавлена аутентификация API Keys, пагинация, rate limiting, scopes
