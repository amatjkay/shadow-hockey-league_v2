# AGENTS.md — Project Constitution for Shadow Hockey League v2

> **This file is the single source of truth for all AI agents operating on this project.**
> It supplements `.antigravityrules` with agent-coordination rules, memory bank protocols,
> and safety guardrails.

---

## 1. Memory Bank Protocol

All agents **MUST** follow this protocol at the start and end of every task:

### On Start (Before ANY Action)

1. Read `docs/activeContext.md` — understand current focus, blockers, and recent changes.
2. Read `docs/techContext.md` — understand architecture, dependencies, and MCP constraints.
3. Read `PROJECT_KNOWLEDGE.md` — verify business rules and coding standards.

### On Stop (Before Ending Turn)

1. Update `docs/progress.md` — log what was done, what's left, and any new blockers.
2. If models or architecture changed → update `docs/techContext.md` and `PROJECT_KNOWLEDGE.md`.
3. If a significant design decision was made → append to `docs/decisionLog.md`.

---

## 2. Safety Guardrails

### Database Safety

- **NEVER** perform destructive operations (`DROP`, `DELETE`, `ALTER`, `UPDATE`) on `dev.db`
  without first running a `SELECT` schema check (via `sqlite3 dev.db '.schema <table>'` or a Python read).
- **ALWAYS** use Alembic for schema migrations. Provide the migration command to the user;
  do not run `alembic upgrade head` automatically.
- Before any bulk `DELETE`, run a `SELECT COUNT(*)` to confirm the scope of the operation.

### Secret Management

- **NEVER** expose API keys, tokens, or secrets in code, commits, logs, or chat output.
- Environment variables from `.env` must be referenced by name only (e.g., `$SECRET_KEY`),
  never by value.
- If an API key is accidentally printed, immediately flag it for rotation.

### File Safety

- Do not overwrite `models.py`, `app.py`, or `config.py` without explicit user approval.
- Always use `edit_file` or `replace_file_content` over `write_file` for existing files.
- Never delete test files or fixtures.

---

## 3. Subagent Coordination Rules

### Role Separation

| Agent | Primary Focus | Allowed tools / MCP | Detailed role file |
| :--- | :--- | :--- | :--- |
| `architect` | System design, planning, analysis | `read`/`grep` over the repo, `sqlite3` CLI (read-only), `context7` MCP | `.agents/agents/architect.md` |
| `coder` | Implementation, refactoring, features | full filesystem (`read`/`edit`/`write`), `git`/`git_pr`/`git_comment`, `context7` MCP, `web_search`/`web_get_contents` | `.agents/agents/coder.md` |
| `reviewer` | QA, security audit, code review | full filesystem, `git`/`git_pr` (view + comment) | `.agents/agents/reviewer.md` |
| `token-auditor` | Find token waste in repo, prompts, Memory Bank | full filesystem (read mostly; writes only to `.gitignore`, `Makefile`, `docs/INDEX.md`, `.agents/prompts/`) | `.agents/agents/token-auditor.md` |
| `doc-curator` | Rotate `progress.md` / `decisionLog.md`; maintain `docs/INDEX.md` | full filesystem (move-only — never reword) | `.agents/agents/doc-curator.md` |

### Role Constraints (NOT-DO)

- **architect**:
    - **NEVER** write to source code files (except `implementation_plan.md` and `task.md`).
    - **NEVER** run `pip install` or `alembic upgrade`.
- **coder**:
    - **NEVER** change the database schema without an approved plan from `architect`.
    - **NEVER** skip unit test creation for new features.
- **reviewer**:
    - **NEVER** approve a PR that decreases test coverage below 87%.
    - **NEVER** ignore `mypy` or `flake8` errors.
- **token-auditor**:
    - **NEVER** delete or rewrite source files. Only flags waste; coder/doc-curator execute changes.
    - Allowed edits: `.gitignore`, `Makefile`, `docs/INDEX.md`, Memory Bank, `.agents/prompts/`.
- **doc-curator**:
    - **NEVER** delete or reword content — always move verbatim to `docs/archive/`.
    - **NEVER** drop ADR forward-contracts; keep stub anchors for any cross-referenced entry.

### Handoff Protocol

- When `architect` finishes a plan, it writes to `docs/activeContext.md` with a
  `## Next: Implementation` section for `coder` to pick up.
- When `coder` finishes implementation, it updates `docs/progress.md` with a
  `## Ready for Review` section for `reviewer`.
- `reviewer` validates against this `AGENTS.md` and `.antigravityrules` before approving.
- `token-auditor` writes its findings to a one-off report (chat or
  `docs/audits/token-audit-YYYY-MM-DD.md`) and hands off to `doc-curator` for
  rotation actions or to `coder` for `.gitignore` / `Makefile` / prompt edits.
- `doc-curator` works in isolation; writes a short summary to `docs/progress.md`
  and updates `docs/INDEX.md` if archive files were added.

---

## 4. Tools and MCP Server Usage Rules

Devin sessions on this repo expose two layers:

**Built-in tools** (always available, no MCP needed):

| Tool family | Purpose | Safety constraints |
| :--- | :--- | :--- |
| `read` / `edit` / `write` / `grep` / `find_file_by_name` | Filesystem access | Never write outside the repo root. |
| `git` / `git_pr` / `git_comment` | PRs, issues, comments, CI checks | Always link PRs to a Linear ticket via `Closes TIK-NN`. Use `git_pr(action="fetch_template")` before opening a PR. |
| `web_search` / `web_get_contents` | Web search + page fetching | Verify before applying; prefer `context7` for library APIs. |
| `exec` (sqlite3, alembic, pytest, …) | Anything CLI | DB destructive ops only after a `SELECT` schema check (see § 2). |

**MCP servers** (current install — verify with `mcp_tool` `command="list_servers"`):

| MCP Server | Purpose | Safety constraints |
| :--- | :--- | :--- |
| `context7` | Fresh library documentation (1000+ packages) | Prefer over training data for API questions. |
| `linear` | TIK-* ticket management | Read freely; transition state only with user approval; see `.agents/skills/linear-sync/SKILL.md`. |
| `playwright` | Browser automation (e2e smoke locally + CI) | Run against local dev server only; do not point at production URLs. |
| `redis` | Direct query access to local Redis | Read-only unless cache invalidation is explicitly the task. Production cache is owned by the app, not by agents. |

---

### Skills (callable by name from any agent)

| Skill | Purpose | When to invoke |
| :--- | :--- | :--- |
| `db-migration` | Safe Alembic migrations | new table / column / index |
| `feature-research` | Cross-source research synthesis | unfamiliar library / API |
| `linear-sync` | Read TIK-ID, update status with user approval | task tied to a Linear ticket |
| `verification` | Pre-handoff QA (lint + type + tests) | before any `coder → reviewer` handoff |
| `token-budget` | Estimate token cost; enforce lazy loading | before reading files > 200 lines |
| `doc-rotation` | Move > 30-day entries to `docs/archive/<period>.md` | `progress.md` / `decisionLog.md` > 200 lines |
| `codebase-map` | `grep -n` symbol index + read-window pattern | navigating the `services/api/`, `blueprints/admin_api/`, `services/admin/` packages and other heavy files |

Full skill bodies live in `.agents/skills/<name>/SKILL.md`.

---

## 5. Coding Standards (Quick Reference)

These are enforced by `.antigravityrules` and reiterated here for agent compliance:

- **Type Hints**: Mandatory on all new functions and methods.
- **Docstrings**: Google-style, in English.
- **Imports**: Sorted by `isort`, formatted by `black`.
- **Testing**: Every new feature must have corresponding tests. Target: ≥ 87% coverage (enforced as the CI gate since TIK-54).
- **Type Checking**: `mypy` is back in `make check` and CI as of TIK-53. Prefer `cast()` + narrowing over `# type: ignore`; if you must ignore, narrow the code (`# type: ignore[arg-type]`) and add a one-line reason.
- **Dependency Audit**: `make audit-deps` runs `pip-audit` on both `requirements.txt` and `requirements-dev.txt`. Runtime CVEs are blocking in CI; dev-only are reported.
- **N+1 Prevention**: Use `joinedload()` for any query that accesses relationships in loops.
- **Cache Invalidation**: Call `invalidate_leaderboard_cache()` from `services/cache_service` after any data mutation. Do NOT re-import it from elsewhere — the canonical location was set in TIK-43.
- **Audit Logging**: All admin CRUD actions logged via `audit_service.log_action()` (or, for ORM-level mutations, the `after_flush` listener registered by `register_audit_request_hook(app)` in `app.py::register_extensions`).

---

## 6. Version History

| Date | Change | Author |
| :--- | :--- | :--- |
| 2026-04-23 | Initial creation — Memory Bank + Subagents | AI |
| 2026-05-01 | Add `token-auditor` + `doc-curator` sub-agents; add `token-budget`, `doc-rotation`, `codebase-map` skills; add `docs/INDEX.md`; commit SHL-OPTIMIZER prompt v2.0 to `.agents/prompts/` | AI |
| 2026-05-03 | TIK-42 cleanup epic: split `services/api.py`, `blueprints/admin_api.py`, `services/admin.py` into per-resource Python packages; lower CC of 4 hot functions to ≤ C; dedup tests; archive `scratch/` to `scripts/oneoff/`; coverage 81 → 84%. Public imports unchanged. | AI |
| 2026-05-03 | TIK-51 tech-debt continuation: `pip-audit` gate in CI; `mypy` back in `make check` and CI (0 errors); coverage 84 → 87% (enforced as CI gate); `tests/e2e/test_smoke.py` wired into a dedicated `E2E Smoke (Playwright)` GitHub Actions job. Updated skills `verification`, `codebase-map`, `linear-sync` to match the new toolchain. | AI |
| 2026-05-04 | TIK-57 sub-agents/skills sanity check: rewrote `db-migration` + `feature-research` skills around built-in tools (`exec` for `sqlite3`/`alembic`, `web_search`/`web_get_contents`); replaced AGENTS § 4 + techContext MCP tables with the actual current install (`context7`, `linear`, `playwright`, `redis`); corrected test count 464 → 472 everywhere; added Redis-service caveat to `verification` skill. | AI |
| 2026-05-04 | TIK-57 (Linear-tracked) — bootstrap obra/superpowers skill bridge: added § 7 below, `scripts/install_superpowers.{sh,ps1}`, `.superpowersrc`, `.pre-commit-config.yaml`, `Makefile` targets `superpowers-{install,status,update}` + `precommit-install`, `docs/SUPERPOWERS.md`, and the `skills/superpowers` git submodule pinned at upstream tag `v5.0.7`. Existing § 1–6 unchanged. | AI |

---

## 7. Superpowers Skill Bridge (since 2026-05-04)

[obra/superpowers](https://github.com/obra/superpowers) is a *methodology-level*
skill set (TDD, brainstorming, writing-plans, subagent-driven-development,
requesting-code-review, finishing-a-development-branch, …) bootstrapped by
[`scripts/install_superpowers.sh`](scripts/install_superpowers.sh) (POSIX) /
[`.ps1`](scripts/install_superpowers.ps1) (Windows). Source of truth:
[`.superpowersrc`](.superpowersrc).

These skills **complement, not replace**, the project-specific skills in
`.agents/skills/<name>/SKILL.md` (§ 3). On any name collision the project
skill wins; explicitly disable an upstream skill via `disabled_skills` in
`.superpowersrc`.

### Per-platform install matrix

| Platform | What the script does | Repo-modifying? |
| :--- | :--- | :--- |
| Claude Code | prints `/plugin install superpowers@claude-plugins-official` | no |
| Cursor | prints `/add-plugin superpowers` | no |
| Codex CLI | prints `/plugins → superpowers → Install` | no |
| Codex App | prints sidebar walkthrough | no |
| OpenCode | merges `superpowers@git+…` into `opencode.json[plugin]` | yes (`opencode.json`) |
| Copilot CLI | prints `copilot plugin marketplace add … && plugin install …` | no |
| Gemini CLI | prints `gemini extensions install …` | no |
| Kilocode | submodule `skills/superpowers` + symlink `.kilocode/skills/superpowers` | yes |
| Hermes | submodule + `external_skill_dirs` snippet for `~/.hermes/config.toml` | yes (submodule only) |
| Antigravity / **Devin.io** / unknown | submodule + symlink `.agents/skills/superpowers` | yes |

Devin/Antigravity expose superpowers skills under
**`.agents/skills/superpowers/`** — the symlink target — so existing
skill-discovery (which already scans `.agents/skills/<name>/SKILL.md`) picks
them up alongside the seven project skills in § 3.

### Verification

- `make superpowers-status` — dry-run; prints detected platform + target path.
- `git -C skills/superpowers describe --tags` — confirms the upstream pin.
- `scripts/install_superpowers.sh --check` — pre-commit-friendly sanity check.
- Native plugin platforms: `/superpowers status` slash command (or equivalent)
  inside the agent.

### Updating

```bash
make superpowers-update                       # remote-fast-forward submodule
git -C skills/superpowers checkout v5.x.y     # or pin to a different tag
git add skills/superpowers .superpowersrc     # bump upstream_ref: too
git commit -m "chore(superpowers): bump to v5.x.y"
```

Full docs: [`docs/SUPERPOWERS.md`](docs/SUPERPOWERS.md).
