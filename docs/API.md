# Shadow Hockey League REST API Documentation

**Base URL:** `http://127.0.0.1:5000/api`  
**Version:** 1.0  
**Format:** JSON

---

## 📋 Overview

REST API provides CRUD operations for managing countries, managers, and achievements in the Shadow Hockey League system.

### Authentication

Currently, the API does not require authentication. In production, consider adding:
- API keys
- JWT tokens
- OAuth 2.0

### Response Format

All responses are returned in JSON format:

**Success Response:**
```json
{
  "id": 1,
  "name": "Example",
  "message": "Operation successful"
}
```

**Error Response:**
```json
{
  "error": "Error description"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid data provided |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource already exists |
| 500 | Internal Server Error |

---

## 🌍 Countries API

### Get All Countries

**Endpoint:** `GET /api/countries`

**Response:**
```json
[
  {
    "id": 1,
    "code": "RUS",
    "flag_path": "/static/img/flags/rus.png"
  },
  {
    "id": 2,
    "code": "BEL",
    "flag_path": "/static/img/flags/bel.png"
  }
]
```

**Example (curl):**
```bash
curl http://127.0.0.1:5000/api/countries
```

---

### Get Country by ID

**Endpoint:** `GET /api/countries/<id>`

**Response:**
```json
{
  "id": 1,
  "code": "RUS",
  "flag_path": "/static/img/flags/rus.png"
}
```

**Example (curl):**
```bash
curl http://127.0.0.1:5000/api/countries/1
```

---

### Create Country

**Endpoint:** `POST /api/countries`

**Request Body:**
```json
{
  "code": "USA",
  "flag_path": "/static/img/flags/usa.png"
}
```

**Requirements:**
- `code`: 3 characters, unique
- `flag_path`: Valid path to flag image

**Response (201 Created):**
```json
{
  "id": 3,
  "code": "USA",
  "flag_path": "/static/img/flags/usa.png",
  "message": "Country created successfully"
}
```

**Example (curl):**
```bash
curl -X POST http://127.0.0.1:5000/api/countries \
  -H "Content-Type: application/json" \
  -d '{"code":"USA","flag_path":"/static/img/flags/usa.png"}'
```

---

### Update Country

**Endpoint:** `PUT /api/countries/<id>`

**Request Body:**
```json
{
  "code": "USA",
  "flag_path": "/static/img/flags/usa_new.png"
}
```

**Response:**
```json
{
  "id": 3,
  "code": "USA",
  "flag_path": "/static/img/flags/usa_new.png",
  "message": "Country updated successfully"
}
```

**Example (curl):**
```bash
curl -X PUT http://127.0.0.1:5000/api/countries/3 \
  -H "Content-Type: application/json" \
  -d '{"flag_path":"/static/img/flags/usa_new.png"}'
```

---

### Delete Country

**Endpoint:** `DELETE /api/countries/<id>`

**Response:**
```json
{
  "message": "Country deleted successfully"
}
```

**Note:** Cannot delete a country with existing managers (returns 409 Conflict).

**Example (curl):**
```bash
curl -X DELETE http://127.0.0.1:5000/api/countries/3
```

---

## 👤 Managers API

### Get All Managers

**Endpoint:** `GET /api/managers`

**Query Parameters:**
- `country_id` (optional): Filter by country ID
- `search` (optional): Search by name (case-insensitive)

**Response:**
```json
[
  {
    "id": 1,
    "name": "Feel Good",
    "display_name": "Feel Good",
    "is_tandem": false,
    "country_id": 2,
    "country_code": "BEL",
    "achievements_count": 3
  }
]
```

**Examples (curl):**
```bash
# Get all managers
curl http://127.0.0.1:5000/api/managers

# Filter by country
curl "http://127.0.0.1:5000/api/managers?country_id=1"

# Search by name
curl "http://127.0.0.1:5000/api/managers?search=feel"
```

---

### Get Manager by ID

**Endpoint:** `GET /api/managers/<id>`

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

**Example (curl):**
```bash
curl http://127.0.0.1:5000/api/managers/1
```

---

### Create Manager

**Endpoint:** `POST /api/managers`

**Request Body:**
```json
{
  "name": "John Doe",
  "country_id": 1
}
```

**Requirements:**
- `name`: Unique manager name
- `country_id`: Must reference existing country

**For Tandems:**
```json
{
  "name": "Tandem: Player One, Player Two",
  "country_id": 1
}
```

**Response (201 Created):**
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

**Example (curl):**
```bash
curl -X POST http://127.0.0.1:5000/api/managers \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","country_id":1}'
```

---

### Update Manager

**Endpoint:** `PUT /api/managers/<id>`

**Request Body:**
```json
{
  "name": "Jane Doe",
  "country_id": 2
}
```

**Response:**
```json
{
  "id": 5,
  "name": "Jane Doe",
  "display_name": "Jane Doe",
  "is_tandem": false,
  "country_id": 2,
  "message": "Manager updated successfully"
}
```

**Example (curl):**
```bash
curl -X PUT http://127.0.0.1:5000/api/managers/5 \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Doe"}'
```

---

### Delete Manager

**Endpoint:** `DELETE /api/managers/<id>`

**Response:**
```json
{
  "message": "Manager deleted successfully"
}
```

**Note:** Deleting a manager also deletes all their achievements (CASCADE).

**Example (curl):**
```bash
curl -X DELETE http://127.0.0.1:5000/api/managers/5
```

---

## 🏆 Achievements API

### Get All Achievements

**Endpoint:** `GET /api/achievements`

**Query Parameters:**
- `manager_id` (optional): Filter by manager ID
- `league` (optional): Filter by league ("1" or "2")
- `season` (optional): Filter by season (e.g., "24/25")
- `achievement_type` (optional): Filter by type (e.g., "TOP1")

**Response:**
```json
[
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
]
```

**Examples (curl):**
```bash
# Get all achievements
curl http://127.0.0.1:5000/api/achievements

# Filter by manager
curl "http://127.0.0.1:5000/api/achievements?manager_id=1"

# Filter by league and season
curl "http://127.0.0.1:5000/api/achievements?league=1&season=23/24"
```

---

### Get Achievement by ID

**Endpoint:** `GET /api/achievements/<id>`

**Response:**
```json
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
```

**Example (curl):**
```bash
curl http://127.0.0.1:5000/api/achievements/1
```

---

### Create Achievement

**Endpoint:** `POST /api/achievements`

**Request Body:**
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

**Requirements:**
- `achievement_type`: TOP1, TOP2, TOP3, BEST, R3, R1
- `league`: "1" or "2"
- `season`: Format "YY/YY" (e.g., "24/25")
- `title`: Human-readable title
- `icon_path`: Path to achievement icon
- `manager_id`: Must reference existing manager

**Response (201 Created):**
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

**Example (curl):**
```bash
curl -X POST http://127.0.0.1:5000/api/achievements \
  -H "Content-Type: application/json" \
  -d '{
    "achievement_type":"TOP1",
    "league":"1",
    "season":"24/25",
    "title":"Shadow 1 league TOP1",
    "icon_path":"/static/img/cups/top1.svg",
    "manager_id":1
  }'
```

---

### Update Achievement

**Endpoint:** `PUT /api/achievements/<id>`

**Request Body:**
```json
{
  "achievement_type": "TOP2",
  "league": "1",
  "season": "24/25",
  "title": "Shadow 1 league TOP2",
  "icon_path": "/static/img/cups/top2.svg",
  "manager_id": 2
}
```

**Response:**
```json
{
  "id": 10,
  "achievement_type": "TOP2",
  "league": "1",
  "season": "24/25",
  "title": "Shadow 1 league TOP2",
  "icon_path": "/static/img/cups/top2.svg",
  "manager_id": 2,
  "message": "Achievement updated successfully"
}
```

**Example (curl):**
```bash
curl -X PUT http://127.0.0.1:5000/api/achievements/10 \
  -H "Content-Type: application/json" \
  -d '{"achievement_type":"TOP2"}'
```

---

### Delete Achievement

**Endpoint:** `DELETE /api/achievements/<id>`

**Response:**
```json
{
  "message": "Achievement deleted successfully"
}
```

**Example (curl):**
```bash
curl -X DELETE http://127.0.0.1:5000/api/achievements/10
```

---

## 📊 Rating Calculation

Points are calculated using the formula:

```
points = base_points(league, achievement_type) × season_multiplier
```

### Base Points

| Achievement  | League 1 | League 2 |
|--------------|----------|----------|
| TOP1         | 800      | 300      |
| TOP2         | 550      | 200      |
| TOP3         | 450      | 100      |
| Best regular | 50       | 40       |
| Round 3      | 30       | 20       |
| Round 1      | 10       | 5        |

### Season Multipliers

| Season | Multiplier |
|--------|------------|
| 24/25  | ×1.00      |
| 23/24  | ×0.95      |
| 22/23  | ×0.90      |
| 21/22  | ×0.85      |

**Logic:** Recent achievements are more valuable than old ones.

---

## 🔍 Error Handling

All errors return a JSON response with an `error` field:

**404 Not Found:**
```json
{
  "error": "Manager with ID 999 not found"
}
```

**409 Conflict:**
```json
{
  "error": "Manager with name 'John Doe' already exists"
}
```

**400 Bad Request:**
```json
{
  "error": "Manager name is required; Valid country ID is required"
}
```

---

## 🧪 Testing

Run API tests using:

```bash
# Using Makefile
make test

# Or directly
python -m unittest discover -v
```

API tests are located in `tests.py` under `TestAPIEndpoints`.

---

**Last Updated:** 29 марта 2026 г.
