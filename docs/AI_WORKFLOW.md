# AI Task Formulation Checklist — pointer

The canonical, agent-discoverable version of this checklist lives in
[`.agents/skills/task-formulation/SKILL.md`](../.agents/skills/task-formulation/SKILL.md).

Quick recap (do **all four** before any code change in a non-trivial task):

1. **Context — Why?** Problem (pain/value) + system components touched.
2. **Result shape — What?** Happy path + corner cases.
3. **Definition of Done.** 2–3 acceptance bullets + how to verify
   (tests, `make` targets, Playwright scenarios).
4. **Scope & Anti-Goals.** What we will NOT do + size sanity check
   (decompose if the task won't fit one session).

Render this into a PR or Linear ticket via
[`.github/ISSUE_TEMPLATE/well-formed-task.md`](../.github/ISSUE_TEMPLATE/well-formed-task.md).

See also the wiki entry [`docs/wiki/Agents & Skills.md`](wiki/Agents%20%26%20Skills.md)
for how this skill fits into the architect → coder → reviewer pipeline.
