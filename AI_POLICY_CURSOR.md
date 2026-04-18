# AI Policy for Cursor IDE

## Purpose
Adapts [AI_POLICY.md](AI_POLICY.md) for Cursor IDE while maintaining full compatibility with other IDEs.

## Key Adaptations

### Role Mapping
- **Research Agents**: ANALYST, ARCHITECT, PLANNER, DESIGNER
- **Code Agents**: DEVELOPER, QA_TESTER, CODE_REVIEWER

### Workflow Integration
- Follows same pipeline as core policy
- Smart routing based on file type and keywords
- UAT gate enforcement with `@save` / `@approve`

### Safety Rules
- No silent breaking changes
- No unrelated modifications
- Minimal reversible changes preferred
- `.env` required for secrets

## Links
- Full policy: [AI_POLICY.md](AI_POLICY.md)
- Agent adapters: [.qwen/agents/cursor_adapters.md](.qwen/agents/cursor_adapters.md)
