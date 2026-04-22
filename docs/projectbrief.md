# Project Brief — Shadow Hockey League v2

## Overview

Shadow Hockey League v2 is a web application for managing a fantasy/shadow hockey league.
It tracks managers (players), their achievements across seasons and leagues, and computes
a unified rating leaderboard based on a points formula.

**Production URL:** https://shadow-hockey-league.ru/

---

## Core Business Logic

### Rating Formula
```
final_points = base_points(league, achievement_type) × season_multiplier
```

- **Base points** are determined by the combination of achievement type and league tier.
- **Season multiplier** applies a decay factor: current season = ×1.00, each prior season loses 5%.
- Points are stored denormalized on each `Achievement` record for query performance.

### Achievement Types
| Code | Description       | League 1 | League 2 |
|------|-------------------|----------|----------|
| TOP1 | Champion          | 800      | 300      |
| TOP2 | Runner-up         | 550      | 200      |
| TOP3 | Third place       | 450      | 100      |
| BEST | Best regular      | 50       | 40       |
| R3   | Round of 16/QF    | 30       | 20       |
| R1   | First round exit  | 10       | 5        |

### Leagues
- League 1 — main league (code: `1`)
- League 2 — secondary league (code: `2`)
- Sub-leagues 2.1 and 2.2 — available only from season 25/26 onwards

### Seasons
- Format: `YY/YY` (e.g., `24/25`)
- Each season has a `multiplier` (float), `start_year`, and `end_year`
- At least one season must remain active at all times

### Managers
- Each manager belongs to exactly one country
- **Tandems**: A manager whose name contains a comma (`,`) or starts with `Tandem:` is a tandem (pair of players)
- Managers can be deactivated (soft delete via `is_active` flag)

### Countries
- Identified by ISO 3-letter code (e.g., `RUS`, `CAN`, `USA`)
- Each country has a flag image (local file or CDN URL)
- Cannot delete a country that has managers attached

---

## Key User Flows

1. **Leaderboard** — Public page showing all managers ranked by total points
2. **Admin Panel** (`/admin/`) — Authenticated CRUD for all entities
3. **Bulk Achievement Creation** — Create the same achievement for multiple managers at once
4. **REST API** — Programmatic access with API Key authentication (scopes: read/write/admin)
5. **Audit Log** — All admin actions are logged and visible in the admin panel

---

## Non-Functional Requirements

- **Performance**: Redis caching with automatic invalidation; N+1 prevention via `joinedload`
- **Security**: CSRF protection on web forms; API key auth on REST endpoints; rate limiting
- **Monitoring**: `/health` endpoint + Prometheus metrics at `/metrics`
- **Deployment**: Ubuntu 22.04 + Nginx + Gunicorn + GitHub Actions CI/CD
- **Testing**: 383+ tests, ~87% coverage, using pytest with FakeRedis

---

## Open Questions

> _To be populated based on evolving requirements._
