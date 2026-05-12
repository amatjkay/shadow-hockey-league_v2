---
name: task-formulation
description: Checklist for transforming a vague request into a well-formed task before any code is written. Use whenever a request is complex (≥ 3 files, ≥ 2 packages, or unclear acceptance criteria) — gates the move from architect/research to coder.
---

# SKILL: Task Formulation Checklist

## Goal

Turn a vague request into a **well-formed task** before any code is written.
A well-formed task is one that another agent (or a future you) can execute
without further clarification, and where success can be verified objectively.

This skill is the entry-point checklist for the existing pipeline:
**user request → `task-formulation` → `feature-research` (if needed) →
`architect` → `coder` → `verification` → `reviewer`**.

## When to Use

Apply when **any** of these is true:

- The request touches ≥ 3 files or ≥ 2 packages (`services/api/`,
  `services/admin/`, `blueprints/admin_api/`, `models.py`, …).
- Acceptance criteria are unstated (the user said *"исправь"*, *"улучши"*,
  *"добавь"* without numbers, screens, or tests).
- A schema change, migration, or scoring formula tweak is hinted at.
- You catch yourself about to write code "to see what happens".

Trivial requests (one-file rename, one-paragraph doc edit) **skip** this
skill — see `karpathy-guidelines` § 1 ("for trivial tasks, use judgment").

## The Checklist

### 1. Context — Why?

- [ ] **Problem (pain or value):** what does the user actually want to
      change? Phrase it as *"the user can't X / sees wrong Y"*, **not**
      *"add button Z"*.
- [ ] **System components touched:** which packages / models / services
      are in scope? An LLM coming in cold should be able to read this and
      orient itself in 30 seconds. Link to wiki notes
      (`docs/wiki/Home.md`) or canonical docs (`docs/ARCHITECTURE.md`,
      `PROJECT_KNOWLEDGE.md`).

**Bad:** *"Сделай кнопку 'Выход' в шапке."*
**Good:** *"Авторизованный админ не может выйти из админки —
кнопка `logout` есть только во Flask-Admin sidebar и теряется на
мобиле. Затронем `templates/admin/master.html`, `blueprints/main.py`
(top-nav include), `static/js/admin/*` (мобильное меню)."*

### 2. Result Shape — What?

- [ ] **Happy path:** describe the ideal end-to-end flow as 3–7
      numbered steps from the user's POV.
- [ ] **Corner cases / failure modes:** at least 2 — empty data, wrong
      role, race with cache, broken network, partially seeded DB. If
      you can't think of any, you haven't thought about the task long
      enough (see `karpathy-guidelines` § 1).

### 3. Definition of Done

- [ ] **Acceptance criteria — 2 to 3 concrete bullets** that a reviewer
      can check off. *"Работает"* is not a criterion.
- [ ] **How to verify** — name the tests / make targets / curl commands
      / Playwright scenarios that turn green. If a new test is needed,
      say where it lives (`tests/test_<area>.py` or
      `tests/integration/test_<area>.py`).

**Example DoD block:**

```markdown
- [ ] `services/scoring_service.compute_points()` returns L1 base for any
      subleague whose parent league is L1; covered by
      `tests/test_scoring_service.py::test_subleague_resolves_to_parent`.
- [ ] `make check && make test` pass, coverage ≥ 87% (TIK-54).
- [ ] Admin recalc UI shows the recomputed value for season 25/26 within
      one cache TTL; Playwright `tests/e2e/test_smoke.py::admin_recalc`
      passes.
```

### 4. Scope & Anti-Goals

- [ ] **Out of scope (anti-goals):** name the adjacent refactors /
      cleanups you will **not** do in this task, even if you're
      tempted. *"Не трогаем мобильную вёрстку. Не меняем формулу
      рейтинга. Не апгрейдим Flask-Admin."*
- [ ] **Size sanity check:** is the resulting plan still ≤ ~300 LOC of
      code change and ≤ 1 working session? If not, **decompose** —
      open sub-tickets in Linear (`linear-sync` skill) and link them
      from the parent. Carry the same checklist into each sub-ticket.

If you can't keep the task to one session, that's a signal to stop and
decompose — not a signal to start coding faster.

## Workflow

1. Read the user's raw request.
2. Walk the 4 sections above; write the answers into a scratch file
   (`task.md` at repo root is fine — `architect` is allowed to write it,
   see `.agents/agents/architect.md`). For a Linear-tracked task,
   put the same content into the issue description.
3. **If a section can't be filled in,** stop and ask the user a focused
   question (max 3). Do **not** start implementation.
4. Once the checklist is complete:
   - For a Linear-tracked task: hand off to `feature-research` (if the
     library/API isn't familiar) or directly to `coder` via a
     `## Next: Implementation` block in `docs/activeContext.md`
     (`AGENTS.md` § 3 handoff protocol).
   - For an ad-hoc task: paste the checklist into the chat turn so
     the user can sanity-check before code lands.
5. **Before merge,** the same checklist is the reviewer's reading
   list — every "Definition of Done" item must be visible in the PR
   description (use `.github/ISSUE_TEMPLATE/well-formed-task.md` or
   `.github/pull_request_template.md` as the canonical form).

## Forbidden

- **Starting `coder` work without all four sections filled.** A missing
  Anti-Goals section is the #1 cause of unrelated refactors in this
  repo (see `karpathy-guidelines` § 3 — *surgical changes*).
- **Inventing acceptance criteria** the user never agreed to. If the
  user didn't ask for a feature, it's not in the DoD.
- **Skipping decomposition** when the task obviously won't fit in one
  session. Decomposing now is cheap; reverting half-done work is not.
- **Putting the checklist somewhere the reviewer can't see it.** It
  must live in the PR description, the Linear ticket, or both.

## Related

- `.agents/skills/karpathy-guidelines/SKILL.md` — behavioural rules
  (think before coding, simplicity, surgical changes, verifiable
  goals). The task-formulation checklist is how those rules become
  a concrete artefact.
- `.agents/skills/feature-research/SKILL.md` — invoke after the
  checklist is filled if the task involves an unfamiliar library/API.
- `.agents/skills/linear-sync/SKILL.md` — for syncing the checklist
  into a TIK-NN Linear ticket and back.
- `.agents/skills/verification/SKILL.md` — runs the DoD checks
  (`make check && make test && make audit-deps`) before handoff.
- `.github/ISSUE_TEMPLATE/well-formed-task.md` — the same checklist
  rendered as a GitHub issue form.
