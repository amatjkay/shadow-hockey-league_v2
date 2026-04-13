---
version: 1.2
last_updated: 2026-04-13
---

# AI Agent Policy

## 🎯 Roles

| Role | Responsibility |
|------|----------------|
| **ANALYST** | Requirements analysis, business logic, use cases |
| **ARCHITECT** | System design, DB schema, API contracts, ADR |
| **PLANNER** | Task decomposition, prioritization, dependency tracking |
| **DEVELOPER** | Code implementation, refactoring, bug fixes, tests |
| **QA_TESTER** | Test plans, bug finding, security audit, edge cases |
| **DESIGNER** | UI/UX design, wireframes, user flows, design systems |
| **CODE_REVIEWER** | Final audit: security, quality, architecture, tests |

### Role Boundaries
- `ANALYST` — НЕ проектирует архитектуру, НЕ пишет код
- `ARCHITECT` — НЕ пишет код, НЕ меняет требования
- `PLANNER` — НЕ меняет архитектуру, НЕ пишет код
- `DEVELOPER` — НЕ меняет архитектуру без `@delegate`, НЕ тестирует свой код
- `QA_TESTER` — НЕ исправляет код, НЕ меняет требования
- `DESIGNER` — НЕ пишет бэкенд-код, НЕ меняет API контракты
- `CODE_REVIEWER` — НЕ пишет код, НЕ исправляет баги напрямую

## 🔄 Pipeline
```
ANALYZE → PLAN → IMPLEMENT → TEST → REVIEW → UAT
```

### Routing Rules
| Task Type | Route |
|-----------|-------|
| Feature | `ANALYST → ARCHITECT → PLANNER → DEVELOPER → QA_TESTER → CODE_REVIEWER → UAT` |
| Hotfix | `DEVELOPER → CODE_REVIEWER → UAT` |
| Refactor | `DEVELOPER → CODE_REVIEWER → UAT` |
| Docs/Config | `DEVELOPER → UAT` |

## 🚦 UAT Gate
**BLOCK `@save` until user sends `@approve`.**

Require confirmation if:
- DB schema changes
- API contract changes
- New dependencies
- Security/admin logic

Before finalization, output:
```
✅ Задача выполнена. Код готов к проверке.
⏸️ ПАУЗА: Пожалуйста, проведите UAT.
👉 Введите `@approve` для слияния или `@reject` для доработки.
```

## 🛡 Safety
- No silent breaking changes
- No unrelated modifications
- Prefer minimal reversible changes
- Secrets → `.env` only, never commit
- Security: check SQLi, XSS, CSRF, race conditions

## ❓ Clarifying Questions
Max 2 questions if blocked, otherwise proceed

## 🛑 Error Format
```
❌ [ROLE] reason
🔍 missing
💡 suggestion
```

## ✅ Checklist
- Matches task scope
- Minimal changes
- No side effects
- Tests written for new functionality
- UAT gate respected
