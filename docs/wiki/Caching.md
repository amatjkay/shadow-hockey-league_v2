# Caching

[`services/cache_service.py`](../../services/cache_service.py) wraps
Flask-Caching. **Redis in prod, SimpleCache fallback in dev/test.**

## Contract

- `invalidate_leaderboard_cache()` — call from `services/cache_service`
  **only**. Re-importing it from anywhere else fragments the import
  graph (TIK-43 fixed this).
- Any data mutation that changes the leaderboard (achievement CRUD,
  season multiplier change, manager rename) **must** invalidate. The
  audit `after_flush` listener does this automatically for ORM-level
  changes; explicit admin actions call it manually.
- `@cache.cached` on a view that reads `?season=N` **must** use a
  *callable* `key_prefix` — see [[Blueprints]] for the canonical
  example in `blueprints/main.py::index`.

## Gotcha (TIK-43)

A static `key_prefix` will silently serve the leaderboard for season X
to a request for season Y. Test:
`tests/integration/test_cache_invalidation.py`.

## Local dev

- Redis required for `tests/test_app_extra.py::TestCreateAppEnvFallback`
  (2 of 572 tests). CI brings up a `redis` service container. Locally
  expect `559 passed, 2 failed` if Redis isn't running — that's not a
  regression. See `.agents/skills/verification/SKILL.md`.

## `/health` contract (TIK-91)

`blueprints/health.py` formalises Redis-down behaviour:

| Scenario | HTTP | JSON `status` |
| :--- | :--- | :--- |
| DB up + Redis up | 200 | `healthy` |
| DB up + Redis down, **no** `?strict` | 200 | `degraded` |
| DB up + Redis down, `?strict=1` *or* `X-Health-Mode: strict` | 503 | `degraded` |
| DB down (any `strict` value) | 503 | `down` |

- Uptime checkers (Better Stack, plain `curl`) call `/health` unchanged
  and keep seeing `200 + degraded` when Redis is gone — the app is still
  serving requests via the SimpleCache fallback.
- k8s `readinessProbe` (or any LB health check) must call
  `/health?strict=1` so the pod is rotated out while Redis is gone.
- Latency is observed on the `health_response_seconds` Prometheus
  histogram (labels: `status` ∈ `{healthy, degraded, down}`, buckets
  `0.005…2.5 s`). Grafana alert:
  `histogram_quantile(0.95, rate(health_response_seconds_bucket[5m])) > 0.1`.

## See also

- [[Audit Log]] — invalidation is triggered from there for ORM events.
- [[Operations and CI-CD]] — Redis service container config.
