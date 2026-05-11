# Business Rules

Canonical, never duplicate: see [PROJECT_KNOWLEDGE.md](../../PROJECT_KNOWLEDGE.md)
§ 1. This note is the index.

## Point formula

```
Final Points = Base Points × Season Multiplier
```

- **Base points** — per `(AchievementType, League)`; League 1 uses
  `base_points_l1`, League 2 / 2.1 / 2.2 use `base_points_l2`.
- **Season multiplier** — per `Season.multiplier` (1.0 for the
  current baseline season).

| Code | Name | L1 | L2 |
| :--- | :--- | ---: | ---: |
| TOP1 | Чемпион | 800 | 400 |
| TOP2 | Финалист | 400 | 200 |
| TOP3 | Бронзовый призёр | 200 | 100 |
| BEST | Лучший в регулярке | 200 | 100 |
| R3   | Полуфинал (1/2)    | 100 | 50 |
| R1   | Четвертьфинал (1/4) | 50 | 25 |

Season multipliers: 25/26 ×1.00 · 24/25 ×0.80 · 23/24 ×0.50 ·
22/23 ×0.30 · 21/22 ×0.20.

## Source of truth

1. `data/seed/achievements.json` — declarative seed.
2. `seed_db.py` — idempotent loader.
3. `achievement_types` / `seasons` rows in `dev.db`.

Verify before changing:

```bash
sqlite3 dev.db 'SELECT code, base_points_l1, base_points_l2 FROM achievement_types;'
sqlite3 dev.db 'SELECT code, multiplier FROM seasons;'
```

## Computation site

[[Scoring and Rating]] — the `services/scoring_service.py` /
`services/rating_service.py` implementation, including subleague
parent resolution (TIK-58).
