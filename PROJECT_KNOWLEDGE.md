# PROJECT_KNOWLEDGE.md — Core Principles & Business Rules

> **This file contains the foundational logic and business rules for Shadow Hockey League v2.**
> It is the primary reference for AI agents to ensure logical consistency.

---

## 1. Achievement & Point System

### Point Calculation Formula
`Final Points = (Base Points * Season Multiplier)`

- **Base Points**: Determined by `AchievementType` and `League`.
    - League 1 (L1) uses `base_points_l1`.
    - League 2 (L2), 2.1, 2.2 use `base_points_l2`.
- **Multiplier**: Defined in the `Season` model.
- **Auto-calculation**: Achievements MUST be auto-calculated on the server-side via `on_model_change` to ensure database integrity.

### Reference Data Baselines
- **TOP1**: L1 = 800 points | L2 = 400 points.
- **Baseline Season**: Season 25/26 (Multiplier = 1.0).
- **Historical Seasons**: Multipliers decrease as seasons get older (e.g., S23/24 = 0.5).

---

## 2. Icon & Asset Resolution

### Flags
- Flags are stored in `/static/img/flags/`.
- Filenames MUST be uppercase (e.g., `RUS.png`, `CAN.png`).
- Resolution is case-insensitive in logic but sensitive on the Linux filesystem.

### Achievement Icons
- Icons are stored in `/static/img/cups/`.
- **Standard Pattern**: `{achievement_type_code}.svg` (lowercase).
- **Centralized Resolution**: Use `AchievementType.get_icon_url()` in Python or the `icon_path` field from API responses in JS.
- **Fallback**: `/static/img/cups/default.svg`.

---

## 3. Database Constraints

- **Unique Achievements**: A manager cannot have two achievements of the same `Type` in the same `League` and `Season`.
- **League Compatibility**: Leagues 2.1 and 2.2 are strictly valid only for seasons starting from 2025 (Season 25/26).

---

## 4. UI/UX Standards

- **Admin Modal**: Achievement management in the Manager Edit view uses a centralized AJAX modal to prevent form submission conflicts.
- **Tandem Detection**: Any manager name containing a comma or starting with "Tandem:" is flagged as a tandem in the UI.
- **Caching**: The leaderboard is heavily cached via Redis. Any mutation to managers or achievements MUST trigger `invalidate_leaderboard_cache()`.

---

## 5. Security & Auditing

- **Audit Logs**: Every admin action (CREATE/UPDATE/DELETE) is logged with a JSON diff of changes.
- **CSRF**: All POST/PUT/DELETE actions require a CSRF token, except for specific internal APIs (exempted in `app.py`).

---

_Last updated: 2026-04-24_
