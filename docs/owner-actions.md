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
| **T13** | Decompose `docs/progress.md` — 13 entries 2026-05-03 → 2026-05-08 (later) rotated into `## Progress (rotated 2026-05-13)` of `docs/archive/2026-Q2.md` in TIK-89 / Phase 3 (PR #109). Second pass under TIK-92 (this PR) moved 8 more entries (2026-05-08 → 2026-05-13) into `## Progress (rotated 2026-05-13, part 2 — TIK-92)`; `wc -l` 1282 → 594 → ~200. | done | B / TIK-89, D1 / TIK-92 |
| **T14** | Decompose `docs/decisionLog.md` — 3 entries (2026-04-30 + 2026-05-01 ×2) rotated into `## Decision Log (rotated 2026-05-13)` of `docs/archive/2026-Q2.md` in TIK-89 / Phase 3 (PR #109). Second pass under TIK-92 (this PR) moved 8 more ADRs (2026-05-03 → 2026-05-11) into `## Decision Log (rotated 2026-05-13, part 2 — TIK-92)`; `Forward contracts` blocks of the 3 archived ADRs that carried them preserved verbatim under `## Active Forward Contracts` at the top of `docs/decisionLog.md`. `wc -l` 730 → 606 → ~160. | done | B / TIK-89, D1 / TIK-92 |

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

### T13 / T14 — doc decomposition (resolved 2026-05-13)

**Resolution (TIK-89 / Phase 3, PR #109).** Rotated per the
`doc-rotation` skill. `docs/progress.md` keeps the latest 10 entries
(2026-05-08 → 2026-05-13); the older 13 move verbatim into
`## Progress (rotated 2026-05-13)` of `docs/archive/2026-Q2.md`.
`docs/decisionLog.md` keeps the latest 9 entries (2026-05-03 →
2026-05-13); the 3 oldest (2026-04-30 + 2026-05-01 ×2 — the
chronologically oldest block, matching the cutoff candidate below) move
into `## Decision Log (rotated 2026-05-13)` of the same archive file.
All three archived ADRs contained `**Forward contracts**` blocks; those
blocks are preserved verbatim at the top of `docs/decisionLog.md` under
a new `## Active Forward Contracts` heading.

**Second-pass resolution (TIK-92, this PR).** After TIK-89 Phases 1–3
plus the same-day rating / UI / TIK-88 entries landed, both files
re-crossed the 200-line threshold. TIK-92 narrows each file to the
latest ~30 days *and* ≤ 200 lines per the `doc-rotation` skill: 8 more
progress entries (2026-05-08 → 2026-05-13) move into
`## Progress (rotated 2026-05-13, part 2 — TIK-92)` and 8 more ADRs
(2026-05-03 → 2026-05-11) into `## Decision Log (rotated 2026-05-13,
part 2 — TIK-92)`. Forward-contracts blocks of the 3 archived ADRs
that carried them (2026-05-11 task-formulation, 2026-05-05 Inspector,
2026-05-03 TIK-51) are appended verbatim under the same
`## Active Forward Contracts` heading. Final sizes: `progress.md` ~196,
`decisionLog.md` ~161.

**Original wording (kept for context):**

`docs/progress.md` and `docs/decisionLog.md` are growing past the 200-line
threshold the `doc-rotation` skill calls out. Decomposition is mechanical
(move >30-day entries verbatim to `docs/archive/<year-Qn>.md`), but the
*cutover date* needs an owner call. Default candidate: 2026-04-30 (matches
the last rotation in `docs/archive/2026-Q2.md`).

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
TIK-90; T13 / T14 second-pass rotation cross-linked to TIK-92._
