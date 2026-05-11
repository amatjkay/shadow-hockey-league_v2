# Blueprints

Public HTTP surface lives in [`blueprints/`](../../blueprints/). One
blueprint per concern; admin and REST API live elsewhere (see [[Admin Panel]]
and [[REST API]]).

## Modules

- [`main.py`](../../blueprints/main.py) — public site:
  - `/` — leaderboard (cached, partitioned by `?season=N`).
  - `/managers/<id>` — manager detail.
  - `/health` — liveness redirect (real check below).
- [`health.py`](../../blueprints/health.py) — `/health` JSON probe used
  by Nginx + CI.
- [`admin_api/`](../../blueprints/admin_api/) — JSON helpers used by
  Flask-Admin AJAX (post-TIK-42 split):
  - `_helpers.py` — shared validation / serialisation.
  - `achievements.py` — bulk achievement endpoints.
  - `lookups.py` — country / league / season / manager pickers.

## Conventions

- Every `@cache.cached` view that varies by query-string **must** use a
  callable `key_prefix` (see `blueprints/main.py::index`). A static
  prefix shares the bucket across `?season=` variants and silently
  serves the wrong data.
- Templates live in [`templates/`](../../templates/); static assets in
  [`static/`](../../static/). The admin master template is overridden
  to add the SHL navbar.

## See also

- [[Caching]] — cache key partitioning rules.
- [[REST API]] — public REST endpoints (separate blueprint).
- [[Admin Panel]] — Flask-Admin (not a blueprint itself).
