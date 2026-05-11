# Services

`services/` holds business logic. Two big monoliths (`api.py`, `admin.py`)
were split into packages in TIK-42 — keep them that way.

## Modules

- [`rating_service.py`](../../services/rating_service.py) — leaderboard
  computation. See [[Scoring and Rating]].
- [`scoring_service.py`](../../services/scoring_service.py) —
  `base_points × multiplier`; subleague-aware since TIK-58.
- [`recalc_service.py`](../../services/recalc_service.py) — admin-driven
  bulk recalculation. See [docs/ADMIN_RECALC.md](../ADMIN_RECALC.md).
- [`cache_service.py`](../../services/cache_service.py) — see [[Caching]].
- [`audit_service.py`](../../services/audit_service.py) — see [[Audit Log]].
- [`api_auth.py`](../../services/api_auth.py) — API-key auth + scopes.
- [`validation_service.py`](../../services/validation_service.py) — schema
  validation for seed / import.
- [`metrics_service.py`](../../services/metrics_service.py) — Prometheus
  custom metrics.
- [`extensions.py`](../../services/extensions.py) — shared Flask
  extensions (`Limiter`, etc.). Single source of truth.
- [`_types.py`](../../services/_types.py) — `SessionLike` shim for
  Flask-SQLAlchemy proxy attributes (TIK-53).

## Packages (post-TIK-42 splits)

- [`services/api/`](../../services/api/) — REST endpoints. See [[REST API]].
- [`services/admin/`](../../services/admin/) — Flask-Admin. See [[Admin Panel]].

## Conventions

- New modules ≤ 600 LOC, functions ≤ CC C — enforced informally per
  the TIK-42 cleanup.
- Cache invalidation: call
  `services.cache_service.invalidate_leaderboard_cache()` from the
  *canonical* import path (not re-imported elsewhere — TIK-43).
- Audit: ORM-level mutations are picked up by the `after_flush`
  listener; explicit user actions go through
  `audit_service.log_action(...)`.

## See also

- [docs/ARCHITECTURE.md](../ARCHITECTURE.md) — the layer diagram.
- `.agents/skills/codebase-map/SKILL.md` — grep + read-window pattern
  to navigate big packages without loading whole files.
