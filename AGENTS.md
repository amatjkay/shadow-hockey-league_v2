# AI Agent Orchestration

## Core Rule

This project uses MCP tools and role-based agents.

The AI MUST follow these rules:

1. For any non-trivial task:
   → FIRST use MCP tool `sequential_thinking`

2. BEFORE using:
   - bash
   - filesystem
   - reading files

   → MUST call `sequential_thinking`

3. Continue calling `sequential_thinking`
   until `nextThoughtNeeded = false`

4. Only AFTER that:
   → execute actions (bash, files, etc.)

---

## Tool Priority

1. sequential_thinking (planning, reasoning)
2. filesystem (reading project)
3. bash (execution)

---

## Behavior Rules

- NEVER skip sequential_thinking for multi-step tasks
- NEVER start with bash
- NEVER explore repo before planning
- ALWAYS produce structured reasoning first

---

## Fallback Mode

If MCP tools are unavailable:
- fallback to internal reasoning
- but still follow step-by-step thinking

---

## Source of Truth

All detailed rules are defined in:
→ AI_POLICY.md