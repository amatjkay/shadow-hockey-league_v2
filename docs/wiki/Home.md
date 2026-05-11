# Home

**Shadow Hockey League v2** — Flask 3.1 web app for managing a hockey
league (managers, achievements, cups, points-based rating). Production
at <https://shadow-hockey-league.ru>.

Canonical docs (read these in the repo root, not here):

- [README.md](../../README.md) — quick start, project structure, formulas.
- [AGENTS.md](../../AGENTS.md) — single source of truth for AI agents.
- [PROJECT_KNOWLEDGE.md](../../PROJECT_KNOWLEDGE.md) — business rules.
- [docs/ARCHITECTURE.md](../ARCHITECTURE.md) — full architecture write-up.

## Map of this vault

### Domain & business

- [[Business Rules]] — point formula, base values, season multipliers.
- [[Scoring and Rating]] — `scoring_service` + `rating_service` details.

### Application layers

- [[Architecture]] — the big picture (Nginx → Gunicorn → Flask → SQLite/Redis).
- [[Models and Database]] — SQLAlchemy models, FK graph, key tables.
- [[Migrations]] — Alembic conventions and the inspector-based pattern.
- [[Services]] — what lives in `services/` and how packages were split.
- [[Blueprints]] — routes in `blueprints/` and public templates.
- [[Admin Panel]] — Flask-Admin via `services/admin/`.
- [[REST API]] — `services/api/` endpoints, auth scopes, pagination.
- [[Caching]] — Redis with SimpleCache fallback, invalidation contract.
- [[Audit Log]] — `audit_service` and the `after_flush` listener.

### Engineering practice

- [[Testing and QA]] — `make check`, `make test`, Playwright e2e, gates.
- [[Operations and CI-CD]] — GitHub Actions, deploy, rollback.
- [[MCP and Tooling]] — what MCP servers and built-in tools are wired up.
- [[Agents and Skills]] — sub-agent roles + skill index (incl.
  [[Task Formulation]]).

### Reference

- [[Task Formulation]] — checklist for turning a vague request into a
  well-formed task. Apply before any non-trivial code change.

## Where to start if you are…

- **A new contributor** → [[Architecture]] → [[Services]] → [[Testing and QA]].
- **An AI agent (architect)** → AGENTS.md § 1 (Memory Bank) →
  [[Task Formulation]] → [[Agents and Skills]].
- **Investigating a scoring bug** → [[Business Rules]] →
  [[Scoring and Rating]] → [[Caching]].
- **Adding a column or table** → [[Migrations]] → [[Models and Database]] →
  `.agents/skills/db-migration/SKILL.md`.
