# Operations and CI-CD

Deploy is SSH + restart, run by GitHub Actions. Live at
<https://shadow-hockey-league.ru>.

## CI/CD jobs

[`.github/workflows/deploy.yml`](../../.github/workflows/deploy.yml):

- **`Quality & Tests`** — `make check`, `make test`, `make audit-deps`,
  coverage gate. Redis service container for the 2 limiter tests.
- **`E2E Smoke (Playwright)`** — TIK-55, PR #60. Boots `make run` and
  runs `tests/e2e/test_smoke.py`. Uses `scripts/create_e2e_admin.py`
  to provision the `e2e_admin` super-admin.
- **Deploy** — SSH to prod on `main` push; auto-backup of `dev.db`
  before restart; auto-rollback on health-check failure
  ([`rollback.yml`](../../.github/workflows/rollback.yml)).

## Prod stack

- Nginx (SSL termination) → Gunicorn (4 workers) → Flask
  (`app:create_app()`).
- Redis cache + SQLite DB live on the same host.
- Health probe at `/health`; Prometheus at `/metrics`.

## Pre-commit

[`.pre-commit-config.yaml`](../../.pre-commit-config.yaml) — currently
only the `superpowers-skills-check` hook (sanity check for the
submodule bridge). Install with `make precommit-install`.

## Open infra blockers

See `docs/activeContext.md` § Active Blockers — currently:

- **Secret rotation** — `.env` was in history before PR #44. Owner
  action.
- **Vercel CI noise** — disconnect or drop required check.

## See also

- [[Architecture]] — the runtime topology.
- [[Testing and QA]] — what runs in CI.
