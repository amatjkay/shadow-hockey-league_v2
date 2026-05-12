# Task Formulation

Canonical: [`.agents/skills/task-formulation/SKILL.md`](../../.agents/skills/task-formulation/SKILL.md).
Issue template: [`.github/ISSUE_TEMPLATE/well-formed-task.md`](../../.github/ISSUE_TEMPLATE/well-formed-task.md).

## The 4 sections

Before any non-trivial code change, fill in:

1. **Context — Why?** Problem (pain/value) + system components touched.
2. **Result shape — What?** Happy path + corner cases.
3. **Definition of Done.** 2–3 acceptance bullets + how to verify.
4. **Scope & Anti-Goals.** What we will NOT do + size sanity check
   (decompose if the task won't fit one session).

## How it plugs into the pipeline

`user request → task-formulation → feature-research (if needed) →
architect → coder → verification → reviewer → merge`.

- The architect writes the filled-in checklist into `task.md` (allowed
  scratch file) or into the Linear ticket description.
- The coder reads the checklist; treats anti-goals as a hard fence.
- The reviewer treats the checklist as the merge gate — every DoD
  bullet must be visible in the PR description.

## Trigger

Apply when **any** is true:

- ≥ 3 files or ≥ 2 packages touched.
- Acceptance criteria unstated (*"исправь / улучши / добавь"* without
  numbers, screens, tests).
- Schema / migration / scoring formula change is hinted at.
- You catch yourself about to write code "to see what happens".

Trivial requests (one-file rename, one-paragraph doc) **skip** this
skill — see `karpathy-guidelines` § 1.

## See also

- [[Agents and Skills]] — where this fits in the bigger picture.
- `karpathy-guidelines` skill — behavioural rules the checklist
  operationalises.
