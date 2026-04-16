# Migration Notes

This file summarizes recent structural changes to the codebase.

## v2.1.1 (admin-enhancement branch)

- **Role prompts consolidation**: Removed duplicate v1 role files from `.qwen/agents/`. Only versioned v2 prompts remain.
- **MasterRouter (CLAUDE.md)**: Introduced as the central orchestrator. All role coordination happens through context files and natural‑language delegation; Qwen-specific tags (`@role`, `@delegate`, `@save`) are eliminated.
- **Skill modules**: Created `.qwen/skills/` with reusable prompts (Clarify.md, Debug.md, Validation.md). Roles now reference these skills instead of duplicating logic.
- **RBAC enforcement**: Added `@admin_required` decorator in `services/admin.py` and applied to every admin endpoint in `blueprints/admin_api.py`. Non‑admin requests receive HTTP 403.
- **Database migrations**: All schema changes now require an Alembic migration. Run `alembic upgrade head` after any model change.
- **Multi‑model adapters**: Added `.qwen/adapters/` and `.qwen/adapters.yml` to support OpenAI GPT, Anthropic Claude, and local Qwen via a common `LLMAdapter` interface.
- **Controller → Service refactor**: Business logic moved from blueprints/controllers into `services/match_service.py` and `services/standings_service.py`. Controllers now call services and return HTTP responses.
- **Match model**: Added `models.Match` to store individual match results; standings are updated via `StandingsService.record_match_result`.
- **Observability improvements**: Structured logging and Prometheus metrics are enabled (except in testing). See `app.py` and `services/metrics_service.py` if added later.
- **Testing changes**: Added `tests/test_prompt_regression.py` for LLM prompt regression testing. Add golden outputs for key tasks to keep CI reliable.

## Future directions

- Add integration tests for end‑to‑end admin flows.
- Expand skill library with more reusable modules.
- Support dynamic model selection via `adapters.yml` at runtime.