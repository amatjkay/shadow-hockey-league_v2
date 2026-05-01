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
  without first running a `SELECT` schema check via the `sqlite` MCP server.
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

| Agent | Primary Focus | Allowed MCP Servers | Detailed role file |
| :--- | :--- | :--- | :--- |
| `architect` | System design, planning, analysis | `sequential-thinking`, `notebooklm`, `sqlite` (read-only) | `.agents/agents/architect.md` |
| `coder` | Implementation, refactoring, features | `filesystem`, `github`, `context7`, `duckduckgo` | `.agents/agents/coder.md` |
| `reviewer` | QA, security audit, code review | `filesystem`, `github` | `.agents/agents/reviewer.md` |
| `token-auditor` | Find token waste in repo, prompts, Memory Bank | `filesystem` | `.agents/agents/token-auditor.md` |
| `doc-curator` | Rotate `progress.md` / `decisionLog.md`; maintain `docs/INDEX.md` | `filesystem` | `.agents/agents/doc-curator.md` |

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

## 4. MCP Server Usage Rules

| MCP Server | Purpose | Safety Constraints |
| :--- | :--- | :--- |
| `filesystem` | Read/write project files | Never write outside project root |
| `github` | PRs, issues, code search | Always link PRs to Linear tickets (`Fixes TIK-ID`) |
| `sqlite` | Query `dev.db` schema/data | **Read-only** unless explicit user approval |
| `context7` | Fresh library documentation | Prefer over training data for API questions |
| `duckduckgo` | Web search for solutions | Verify results before applying |
| `sequential-thinking` | Complex problem decomposition | Use for multi-file changes or architecture decisions |
| `notebooklm` | Internal knowledge management | For research synthesis, not code generation |
| `linear` | Task management | Read tasks; update status only with user approval |

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
| `codebase-map` | `grep -n` symbol index + read-window pattern | navigating heavy files (`blueprints/admin_api.py`, `services/api.py`, `services/admin.py`) |

Full skill bodies live in `.agents/skills/<name>/SKILL.md`.

---

## 5. Coding Standards (Quick Reference)

These are enforced by `.antigravityrules` and reiterated here for agent compliance:

- **Type Hints**: Mandatory on all new functions and methods.
- **Docstrings**: Google-style, in English.
- **Imports**: Sorted by `isort`, formatted by `black`.
- **Testing**: Every new feature must have corresponding tests. Target: ≥87% coverage.
- **N+1 Prevention**: Use `joinedload()` for any query that accesses relationships in loops.
- **Cache Invalidation**: Call `invalidate_leaderboard_cache()` after any data mutation.
- **Audit Logging**: All admin CRUD actions logged via `audit_service.log_action()`.

---

## 6. Version History

| Date | Change | Author |
| :--- | :--- | :--- |
| 2026-04-23 | Initial creation — Memory Bank + Subagents | AI |
| 2026-05-01 | Add `token-auditor` + `doc-curator` sub-agents; add `token-budget`, `doc-rotation`, `codebase-map` skills; add `docs/INDEX.md`; commit SHL-OPTIMIZER prompt v2.0 to `.agents/prompts/` | AI |
