# REST API

Public read/write JSON surface lives in
[`services/api/`](../../services/api/) (post-TIK-42 split). Mounted as
a Flask blueprint via `services/api/__init__.py`. Full reference:
[docs/API.md](../API.md) — do **not** read it whole; grep for the
endpoint you need.

## Layout

- `__init__.py` — blueprint registration.
- `_helpers.py` — shared pagination / error / serialisation helpers.
- `countries.py` — `/api/countries/*`.
- `managers.py` — `/api/managers/*`.
- `achievements.py` — `/api/achievements/*`.

## Auth and scopes

- Key-based auth: [`services/api_auth.py`](../../services/api_auth.py).
- Three scopes: `read`, `write`, `admin`. Decorators enforce the
  minimum scope per route.
- Rate limiting: shared `Limiter` in
  [`services/extensions.py`](../../services/extensions.py); storage is
  Redis in prod, in-memory in dev.

## Conventions

- All responses use the helpers in `_helpers.py` (no ad-hoc
  `jsonify({...})` in resource modules).
- Pagination: query params `?page=&per_page=`; max page size enforced
  in `_helpers.paginate(...)`.
- Tests: `tests/test_api.py`, `tests/test_api_auth.py`,
  `tests/test_api_helpers.py`, plus integration in
  `tests/integration/test_api_extended.py`.

## See also

- [docs/API.md](../API.md) — full per-endpoint reference.
- [[Admin Panel]] — the admin surface (separate auth, separate blueprint).
