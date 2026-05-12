# Testing and QA

Single source of truth: `.agents/skills/verification/SKILL.md`. This note
just summarises the gates.

## Gates (enforced by CI)

| Gate | Command | Threshold |
| :--- | :--- | :--- |
| Formatting | `make check` (`black --check`, `isort --check`) | 0 violations |
| Lint | `make check` (`flake8`) | 0 errors |
| Type check | `make check` (`mypy`) | 0 errors (TIK-53) |
| Unit + integration | `make test` | 561 passing, coverage ≥ 87 % (TIK-54) |
| Dependency CVEs | `make audit-deps` | 0 runtime CVEs (TIK-52) |
| E2E smoke | `make e2e` (Playwright) | 42 scenarios green (TIK-55) |

## Test layout

- [`tests/`](../../tests/) — unit and component tests, parallelised by
  `pytest-xdist`.
- [`tests/integration/`](../../tests/integration/) — Flask app context,
  hits the DB and cache.
- [`tests/e2e/`](../../tests/e2e/) — Playwright; excluded from default
  pytest collection via `conftest.py`. Boot with `make run` in one
  shell, `python scripts/create_e2e_admin.py && make e2e` in another.

## Coverage gate

`pytest --cov` is wired into `make test`; the gate is **87 %** since
TIK-54 (PR #59). Dropping below is a blocking CI failure — add tests,
do not lower the gate.

## Local caveats

- 2 of 561 tests require Redis on `localhost:6379`. CI brings up a
  service container; locally you'll see `559 passed, 2 failed`
  without Redis — not a regression. See `verification` skill § 2.

## See also

- [[Operations and CI-CD]] — the GitHub Actions wiring.
- [[Task Formulation]] — the DoD section names *which* tests must turn
  green for a given change.
