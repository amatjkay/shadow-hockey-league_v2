# SKILL: Stability Verification

## Goal

Pre-handoff QA: prove that lint, types, tests, security audit, and (when relevant)
the live HTTP surface are all green before declaring a task done.

## When to Use

- Before any `coder → reviewer` handoff.
- Before opening or updating a PR.
- When the user asks "is everything green?".

## Workflow

1. **Lint + format + types** — single shot:

   ```bash
   make check
   ```

   Runs `black --check`, `isort --check`, `flake8`, `mypy` over the whole tree.
   `mypy` is back in CI as of TIK-53 (PR #58, 2026-05-03); a non-zero exit means
   the build will fail — do not skip or `# type: ignore` away unless the type is
   genuinely external (e.g., Flask-SQLAlchemy proxy attributes).

2. **Unit + integration tests**:

   ```bash
   make test                                                # all 472 tests, parallel
   ./venv/bin/pytest tests --ignore=tests/e2e -n auto       # equivalent
   ```

   Coverage gate is **≥ 87%** (TIK-54, PR #59) — `pytest --cov` reports it.

   **Local caveat:** 2 of the 472 tests (`tests/test_app_extra.py::TestCreateAppEnvFallback`)
   need a real Redis listening on `localhost:6379` to set up Flask-Limiter. CI brings up
   a `redis` service container, so they pass there. Locally you'll see `470 passed, 2
   failed` if you don't have Redis running — that's expected, not a regression.

3. **Dependency audit** (security):

   ```bash
   make audit-deps
   ```

   Wraps `pip-audit` (TIK-52, PR #57). CVEs in runtime deps are blocking; CVEs in
   dev-only deps are flagged but do not fail CI.

4. **E2E smoke** (when touching routes, templates, or admin views):

   ```bash
   # shell 1: dev server
   make run

   # shell 2: provision admin + run Playwright suite
   ./venv/bin/python scripts/create_e2e_admin.py
   make e2e
   ```

   Hits 42 scenarios (public pages, REST API auth boundary, admin CRUD per
   ModelView, browser-console error budget). On CI this runs as the dedicated
   `E2E Smoke (Playwright)` job (TIK-55, PR #60) — the same script, same env vars.

5. **Performance / data integrity** (only when the task touches scoring or recalc):

   ```bash
   make benchmark    # scripts/benchmark.py — leaderboard generation latency
   make audit        # scripts/audit_data.py — formula consistency / orphans
   ```

   Targets: leaderboard generation < 1 ms; 100% formula consistency.
   `make audit` checks **data**, not dependencies — for CVE scanning use
   `make audit-deps` (step 3 above).

## Forbidden

- `--no-verify` / `git commit -n` to bypass pre-commit hooks.
- `# type: ignore` without a `[narrow-error-code]` and a one-line reason.
- Pushing a PR without `make check` — CI will catch it but it wastes a round-trip.
