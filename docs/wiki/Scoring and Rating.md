# Scoring and Rating

Two services collaborate; never duplicate the formula in templates or
blueprints.

## `services/scoring_service.py`

- Computes a single `Achievement.points = base_points × multiplier`
  given `(achievement_type, league, season)`.
- Subleague-aware (TIK-58): if `league.parent_id` is set, resolves to
  the parent's `base_points_l1` / `base_points_l2`.
- Pure function — no DB writes, no cache calls.
- Tested by `tests/test_scoring_service.py` and
  `tests/test_rating_formula.py`.

## `services/rating_service.py`

- Aggregates per-manager totals for the leaderboard.
- Uses `joinedload()` aggressively to avoid N+1 (AGENTS.md § 5).
- Returns a list of dicts; templates only read, never recompute.
- Tested by `tests/test_rating_service.py`.

## `services/recalc_service.py`

- Admin-driven bulk recompute (after `seed_db.py --force`, formula
  tweak, or seasoned multiplier change).
- UI: see [docs/ADMIN_RECALC.md](../ADMIN_RECALC.md).
- Always followed by `invalidate_leaderboard_cache()` — see [[Caching]].

## Source of truth for numbers

[[Business Rules]] + [PROJECT_KNOWLEDGE.md § 1](../../PROJECT_KNOWLEDGE.md).
**Do not** hard-code base values in services — read from
`achievement_types` / `seasons`.

## See also

- [[Models and Database]] — the entities.
- [[Caching]] — when the leaderboard becomes stale.
