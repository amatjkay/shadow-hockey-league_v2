# Owner-Actions Catalog — Shadow Hockey League v2

> **Purpose.** Single source of truth for owner-actionable follow-ups across the
> project. Supersedes the inline list in `docs/activeContext.md` § Immediate Next
> Steps. Tracked in Linear under **TIK-88 / TIK-89 / TIK-90** (one ticket per
> batch).
>
> **Scope.** Items here are things the *owner* (or an agent acting on the owner's
> behalf) needs to decide / execute. They are not on the regular `architect →
> coder → reviewer` pipeline because they either (a) require credentials only the
> owner holds, (b) touch external integrations (Google AI Studio, Vercel,
> git history), or (c) need an explicit owner decision before code can be safely
> changed.

---

## Status legend

- **done** — landed on `main`.
- **this PR** — landed in the PR that introduces this catalog.
- **owner-only** — cannot be automated; requires the owner's hand.
- **follow-up** — actionable by an agent in a subsequent PR; decision-free.
- **open question** — needs an explicit owner decision before any code change.

---

## Catalog

| ID | Action | Status | Batch / Linear |
| :--- | :--- | :--- | :--- |
| **T01** | Create `docs/owner-actions.md` — this file. | this PR | A / TIK-88 |
| **T02** | `ProductionConfig` fail-fast: refuse to start when `SECRET_KEY` / `WTF_CSRF_SECRET_KEY` / `API_KEY_SECRET` are unset or set to a dev placeholder. | this PR | A / TIK-88 |
| **T03** | `.gitignore`: add `bandit_report*.json`, `.coverage.*`, `*.log`, `.tool-versions`. `git rm` the tracked-but-empty `bandit_report.json` + `bandit_report_main.json`. | this PR | A / TIK-88 |
| **T04** | Make `.env.example` platform-neutral (current `DATABASE_URL` default is a Windows path). | done | B / TIK-89 |
| **T05** | Wire `pip-audit` into `make check` (today it only runs via `make audit-deps` + CI). | done | B / TIK-89 |
| **T06** | README *Быстрый старт*: add a one-line note about `make precommit-install` (the git hook does not install itself). | done | B / TIK-89 |
| **T07** | `docs/activeContext.md` § Immediate Next Steps — replace the inline 2-item list with a link to this catalog. | this PR | A / TIK-88 |
| **T08** | `docs/INDEX.md` + `AGENTS.md` § 6 Version History — register this catalog. | this PR | A / TIK-88 |
| **T09** | Rotate secrets at the provider + regenerate locally (`SECRET_KEY`, `WTF_CSRF_SECRET_KEY`, `API_KEY_SECRET` via `python -c "import secrets; print(secrets.token_hex(32))"`; `GEMINI_API_KEY` at Google AI Studio). | owner-only | C / TIK-90 |
| **T10** | Repo-root stub files — 7 total: `bandit_report.json` + `bandit_report_main.json` removed in TIK-88 / Batch A; `locustfile.py`, `run_performance_test.py`, `test_mcp_client.py`, `test_linear_mcp.py`, `check_mcp_status.sh` removed in TIK-89 / Phase 2 along with all matching exclusions in `pyproject.toml` (`[tool.black]` `force-exclude`, `[tool.isort]` `skip`, `[tool.mypy]` `exclude`) and `.flake8` `exclude`. `pytest --collect-only` at the repo root now works without `tests/`. | done | B / TIK-89 |
| **T11** | Decide whether to scrub `.env` from git history via `git filter-repo`. Irreversible; breaks any open forks / PRs. Untracking the file (already done before PR #44) does **not** rewrite history. | owner-only | C / TIK-90 |
| **T12** | Disconnect the GitHub ↔ Vercel integration (project is not deployed on Vercel; the red `Vercel` check on every PR is noise). Alternative: remove `Vercel` from the required-checks set. | owner-only | C / TIK-90 |
| **T13** | Decompose `docs/progress.md` (1045 lines) — move entries older than 30 days to `docs/archive/<period>.md` verbatim, per the `doc-rotation` skill. | open question | B / TIK-89 |
| **T14** | Decompose `docs/decisionLog.md` (656 lines) — same rotation as T13. | open question | B / TIK-89 |

---

## Open questions (need owner input)

### T10 — repo-root stub files (resolved 2026-05-13)

The seven files in question were each one byte longer than their own
filename: they all contained the string `./<filename>:` and a newline,
the residue of a `for f in *; do echo "./$f:" > "$f"; done` mishap.
They broke `pytest --collect-only` at the repo root (3 of them started
with `test_`) and needed scoped exclusions in `pyproject.toml` and
`.flake8` to keep `make check` green.

**Resolution.** Deleted in two waves — `bandit_report.json` +
`bandit_report_main.json` in TIK-88 / Batch A (PR #96); the remaining
five (`locustfile.py`, `run_performance_test.py`, `test_mcp_client.py`,
`test_linear_mcp.py`, `check_mcp_status.sh`) plus all matching exclusions
in TIK-89 / Phase 2. `pytest --collect-only` at the repo root now
collects 576 tests cleanly without `tests/`. If load-testing or MCP
smoke-checking is genuinely needed, file a fresh ticket against a clean
baseline.

### T13 / T14 — doc decomposition

`docs/progress.md` and `docs/decisionLog.md` are growing past the 200-line
threshold the `doc-rotation` skill calls out. Decomposition is mechanical
(move >30-day entries verbatim to `docs/archive/<year-Qn>.md`), but the
*cutover date* needs an owner call. Default candidate: 2026-04-30 (matches
the last rotation in `docs/archive/2026-Q2.md`).

### `/health` SLA — orthogonal to T01..T14

Not in the catalog (it is an architectural decision, not an owner-action),
but tracked here for visibility. `blueprints/health.py` currently returns
`status: degraded` when Redis is disconnected or the DB query fails, but
there is no documented:

- response-time budget (today: target unknown; observed p50 ≈ 20 ms locally),
- allowed duration in `degraded` before paging,
- escalation path on `database_status: error`.

Filing this as a separate Linear ticket once the owner picks numbers.

---

## How this file is maintained

- **One entry per discrete owner-action.** Do not bundle multiple actions
  into a single row.
- **Status transitions** happen here first; mirror to Linear (`linear-sync`
  skill) and to `docs/progress.md` on landing.
- **Closed items** stay in the table with status `done` for one Linear
  cycle, then move to a `## Completed` section at the bottom (rotated to
  `docs/archive/owner-actions-YYYY-Qn.md` quarterly).

_Last updated: 2026-05-13 — initial publication, mirrors TIK-88 / TIK-89 /
TIK-90._
