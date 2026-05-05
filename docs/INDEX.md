# Docs Index — when to load what

> Goal: keep AI-agent context small. Load **only the docs relevant to the
> current task**, not every file under `docs/`.

## Always-on (read on session start, per `AGENTS.md`)

`AGENTS.md` itself is loaded by the agent runtime as the rule set and is
already in context. The Memory Bank Protocol (`AGENTS.md` § 1) explicitly
mandates the three `docs/`+`PROJECT_KNOWLEDGE.md` files marked **MB** below;
`AGENTS.md` is listed here for completeness so this table doubles as the
"what's in your initial context window" view.

| File | Purpose |
| :--- | :--- |
| `AGENTS.md` (repo root) | Single source of truth for rules, guardrails, MCP usage. Supersedes `.antigravityrules`. |
| `PROJECT_KNOWLEDGE.md` (repo root) **MB** | Business rules: point formula, baselines, achievement codes. |
| `docs/activeContext.md` **MB** | What's in flight right now + immediate next steps. |
| `docs/techContext.md` **MB** | Stack/architecture diagram. Skim only the sections relevant to your task. |

## On-demand (load only when working in that area)

| File | When to load |
| :--- | :--- |
| `docs/API.md` | Touching the `services/api/` package or any `/api/*` endpoint. |
| `docs/ARCHITECTURE.md` | Cross-cutting refactors, new service, or layout changes. |
| `.agents/skills/codebase-map/SKILL.md` | Navigating the `services/api/` / `blueprints/admin_api/` / `services/admin/` packages without reading whole files. |
| `.agents/skills/verification/SKILL.md` | Pre-handoff QA recipe (lint + types + tests + audit-deps + e2e). |
| `.agents/skills/linear-sync/SKILL.md` | Updating `TIK-NN` ticket status via the `linear` MCP. |
| `docs/MIGRATIONS.md` | Adding/changing an Alembic migration. |
| `docs/ADMIN_RECALC.md` | Working on rating recalculation or admin recalc UI. |
| `docs/AI_WORKFLOW.md` | Decomposing a complex multi-step task. |
| `docs/GITHUB_CLI.md` | Need a less-common `gh` command. |
| `docs/TROUBLESHOOTING.md` | Investigating a bug or environmental flake. |
| `docs/decisionLog.md` | About to make (or look up) a non-trivial design decision. Use `tail -5` or grep by date — never read whole. |
| `docs/progress.md` | Need recent progress / open work items. Use `tail -50` — never read whole. |
| `docs/SUPERPOWERS.md` | Per-platform install commands for the obra/superpowers skill bridge (`scripts/install_superpowers.sh`). See `AGENTS.md` § 7. |

## Archive (do NOT auto-load)

`docs/archive/` — historical material kept for traceability:

- `docs/archive/audits/` — past audit artefacts (analysis, plans, inventories).
  Reference only when explicitly asked.
- `docs/archive/progress-pre-2026-04-29.md` — pre-cycle progress entries.
- `docs/archive/2026-Q2.md` — rotated `progress.md` (4 entries 2026-04-30 →
  2026-05-01) + `decisionLog.md` (8 entries 2026-04-23 → 2026-04-29). Verbatim
  move; reference only when asked about pre-2026-04-30 design history.

## Conventions

- New historical artefacts (audits, retros, point-in-time inventories) go
  under `docs/archive/<year-month>/...`.
- Active docs (`activeContext.md`, `progress.md`) keep only the **current**
  cycle. Older sections are moved to `docs/archive/` as they age out.

## Forbidden full-read

`progress.md`, `decisionLog.md`, `API.md`, `mcp-servers/**` — never read whole;
use `grep -n` + line ranges or the `codebase-map` / `token-budget` skills.
