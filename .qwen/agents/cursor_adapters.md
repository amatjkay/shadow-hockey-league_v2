---
name: CURSOR_ADAPTERS
role: Infrastructure
---

# Cursor Adapters for Shadow Hockey League v2

## Agent Mapping

### Research Agents (Analysis, Design, Planning)
- **ANALYST**: Requirements, business logic, use cases
- **ARCHITECT**: System design, DB schema, API contracts  
- **PLANNER**: Task breakdown, prioritization, dependencies
- **DESIGNER**: UI/UX design, wireframes, user flows

### Code Agents (Implementation, Testing, Review)
- **DEVELOPER**: Production code, refactoring, bug fixes, tests
- **QA_TESTER**: Test plans, coverage, validation
- **CODE_REVIEWER**: Security audit, quality gate, final review

## Quick Reference

| Task Type | Agent | Command |
|-----------|-------|---------|
| Analysis needed | ANALYST | `@role ANALYST` |
| Architecture | ARCHITECT | `@role ARCHITECT` |
| Implementation | DEVELOPER | `@role DEVELOPER` |
| Tests | QA_TESTER | `@role QA_TESTER` |
| Review | CODE_REVIEWER | `@role CODE_REVIEWER` |

## Delegation Protocol
- `@delegate DEVELOPER Fix logic/security`
- `@delegate QA_TESTER Improve coverage`
- `@delegate CODE_REVIEWER Fix issues` (on reject)
- `@save + confirmation` (on approve)

## Performance Tips
- Agent auto-detection via file type (.py → Code Agent, .md → Research)
- Use `@summary` to view current context
- Pipeline stage detection from git branch
