# Agents and Skills

This repo runs AI agents under a small "constitution". Canonical source:
[AGENTS.md](../../AGENTS.md). This note is the entry-point index.

## Sub-agent roles (AGENTS.md § 3)

| Role | Focus | Role file |
| :--- | :--- | :--- |
| `architect` | Planning, design, schema oversight | [`.agents/agents/architect.md`](../../.agents/agents/architect.md) |
| `coder` | Implementation, refactor, features | [`.agents/agents/coder.md`](../../.agents/agents/coder.md) |
| `reviewer` | QA, security, PR review | [`.agents/agents/reviewer.md`](../../.agents/agents/reviewer.md) |
| `token-auditor` | Find token-waste in repo / prompts | [`.agents/agents/token-auditor.md`](../../.agents/agents/token-auditor.md) |
| `doc-curator` | Rotate `progress.md` / `decisionLog.md` | [`.agents/agents/doc-curator.md`](../../.agents/agents/doc-curator.md) |

## Skills (callable by any agent)

Project skills live in [`.agents/skills/<name>/SKILL.md`](../../.agents/skills/).

| Skill | When to invoke |
| :--- | :--- |
| [[Task Formulation]] (`task-formulation`) | Before any non-trivial code change — gate from request to architect/coder. |
| `karpathy-guidelines` | Behavioural guardrails (think first, simplicity, surgical, verifiable). |
| `feature-research` | Unfamiliar library / API. |
| `db-migration` | Adding table / column / index. |
| `verification` | Pre-handoff QA (lint + types + tests + audit-deps + e2e). |
| `linear-sync` | Update a TIK-NN ticket. |
| `token-budget` | Before reading files > 200 lines. |
| `doc-rotation` | `progress.md` / `decisionLog.md` > 200 lines. |
| `codebase-map` | Grep + read-window navigation of big packages. |

Plus upstream `obra/superpowers` skills exposed via the submodule
bridge — see [[MCP and Tooling]] and AGENTS.md § 7.

## Memory Bank protocol (AGENTS.md § 1)

On **start**, every agent reads:

- [docs/activeContext.md](../activeContext.md) — current focus + blockers.
- [docs/techContext.md](../techContext.md) — stack + architecture.
- [PROJECT_KNOWLEDGE.md](../../PROJECT_KNOWLEDGE.md) — business rules.

On **stop**, the agent updates:

- [docs/progress.md](../progress.md) — what was done / left.
- [docs/decisionLog.md](../decisionLog.md) — if a non-trivial design
  decision was made.
- [docs/techContext.md](../techContext.md) + PROJECT_KNOWLEDGE.md — if
  the architecture or rules changed.

## Pipeline

`user request → [[Task Formulation]] → feature-research (if needed) →
architect → coder → verification → reviewer → merge`. The
task-formulation checklist must be filled in **before** entering the
pipeline; the same checklist is the reviewer's reading list at merge time.
