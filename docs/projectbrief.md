# Project Brief: Shadow Hockey League v2

## Project Overview
Shadow Hockey League is a ranking system for hockey managers based on their multi-season performance across different leagues.

## Core Business Logic

### 1. Rating Calculation
Manager ranking is determined by the sum of points from all their achievements.
The points for each achievement are calculated using the formula:
**Points = Base Points × Season Multiplier**

#### Base Points by League and Type
| Achievement Type | League 1 (Elite) | League 2 |
| :--- | :--- | :--- |
| **TOP1** (Champion) | 800 | 300 |
| **TOP2** (Runner-up) | 550 | 200 |
| **TOP3** (Third place) | 450 | 100 |
| **BEST** (Best Regular Season) | 50 | 40 |
| **R3** (Round 3 Playoff) | 30 | 20 |
| **R1** (Round 1 Playoff) | 10 | 5 |

#### Season Multipliers (Recency Weighting)
To prioritize recent performance, older achievements have a discount multiplier:
- **25/26**: 1.00 (Current/Baseline)
- **24/25**: 0.95
- **23/24**: 0.90
- **22/23**: 0.85
- **21/22**: 0.80

### 2. Leaderboard Rules
- **Sorting**: Total points (Descending) → Name (Ascending).
- **Ranking**: Sequential ranks (1, 2, 3...). Managers with identical total points receive the same rank.
- **Tandems**: Managers can be marked as a "Tandem" (two managers operating one team).
- **Caching**: The leaderboard is cached (Redis/SimpleCache). Cache is invalidated automatically upon any achievement data mutation.

### 3. Data Integrity & Automation
- **Auto-Recalculation**: The system automatically recalculates achievement points before they are saved to the database (SQLAlchemy event triggers).
- **Audit Logging**: All administrative changes (CRUD on managers, achievements, etc.) are logged with timestamps and metadata.

## Technical Stack
- **Backend**: Python 3.12 + Flask 3.1
- **Database**: SQLite (SQLAlchemy 2.0 ORM)
- **Migrations**: Alembic
- **Admin**: Flask-Admin 2.0.2
- **Testing**: Pytest (Coverage target: 87%+)
- **CI/CD**: GitHub Actions (Linting, Typing, Testing)
