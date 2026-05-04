# SKILL: Feature Research

## Purpose

A structured workflow for researching complex features before implementation by
combining the project's own Memory Bank, fresh library documentation, and the
open web — using the tools that this repo's agent sessions actually expose.

## When to Use

- Implementing a feature involving an unfamiliar library or external API.
- Evaluating multiple approaches before writing code.
- Upgrading dependencies and understanding breaking changes (pair with `make audit-deps`).
- Investigating production issues with unclear root causes.

## Tools used (verified 2026-05-04)

This skill uses only tools that are actually present in the current Devin
session. Older versions of this skill referenced `duckduckgo` and `notebooklm`
MCP servers — they are no longer installed.

- **Memory Bank** — `read` / `grep` over `docs/`, `PROJECT_KNOWLEDGE.md`, `AGENTS.md`.
- **`context7` MCP** — fresh, version-pinned library documentation. Always
  prefer this over training data for API questions.
- **`web_search` / `web_get_contents`** — built-in tools that replace the old
  `duckduckgo` MCP. Use for community patterns, blog posts, GitHub issues.
- **`linear` MCP + `git`/`git_pr`** — for cross-referencing existing tickets
  and prior PRs that touched the area.

---

## Workflow

### Step 1 — Define the research question

Before any tool call, write down (in your turn message or a scratch comment):

- **What** do we need to implement or understand?
- **Why** is research needed? (unfamiliar API, multiple approaches, version skew)
- **What does a successful answer look like?** A concrete API call, a chosen
  library, an ADR-ready decision matrix, etc.

### Step 2 — Check internal knowledge first

```bash
grep -nE 'TIK-[0-9]+' docs/progress.md docs/decisionLog.md | head
grep -rni '<feature keyword>' docs/ PROJECT_KNOWLEDGE.md AGENTS.md
```

Also check Linear for prior work via the `linear` MCP:

```jsonc
// linear.list_issues — fuzzy search on past tickets
{"query": "<feature keyword>", "limit": 5}
```

If a prior ADR exists, read it before generating new options.

### Step 3 — Fetch authoritative library docs (`context7` MCP)

```jsonc
// resolve the library id once per session
{"libraryName": "Flask"}

// query the docs with a precise, narrowly scoped question
{"libraryId": "<resolved id>", "query": "how to do X with Y"}
```

**Rule:** Always use `context7` for library-specific questions before web
search. Libraries change frequently and training-data answers can be wrong.

### Step 4 — Web search for patterns and gotchas

```jsonc
// web_search — community patterns, Stack Overflow, GitHub issues
{"query": "Flask <feature> best practices 2025", "num_results": 5}

// web_get_contents — pull the full text of the most promising 1–3 URLs
{"urls": ["https://...", "https://..."]}
```

Time-box this step: 2–3 search iterations at most.

### Step 5 — Synthesize findings

Pick **one** of these depending on persistence needed:

- **Throwaway** — write a 5-bullet summary in the chat turn for the user. No
  files modified.
- **Decision-grade** — append an ADR to `docs/decisionLog.md` (Context →
  Options → Decision → Consequences → Forward contracts). Use this when the
  result will affect future code.
- **Implementation-grade** — write a `## Next: Implementation` block in
  `docs/activeContext.md` for `coder` to pick up.

### Step 6 — Cross-reference with the existing codebase

Before declaring research complete, check whether the project already has a
helper or convention for the feature:

```bash
grep -rn '<symbol_or_url>' --include='*.py' services/ blueprints/
```

If it does, the recommendation should reuse the existing helper, not introduce
a parallel one.

---

## Best Practices

1. **`context7` first, web search second.** Library docs are more authoritative
   than blog posts.
2. **Limit scope.** Don't fall into research rabbit holes; time-box to 3 search
   iterations and one `context7` deep-dive.
3. **Verify versions.** Match found examples to `requirements.txt` / `pyproject.toml`.
   `context7` is version-aware; web examples often aren't.
4. **Cross-reference.** If `context7` and a blog post disagree, trust `context7`.
5. **Document decisions, not surveys.** Future agents should read the *outcome*
   in `docs/decisionLog.md`, not the entire research transcript.

## Forbidden

- Recommending a library that isn't in `requirements.txt` without flagging it
  as a new dependency (and pairing the recommendation with a `pip-audit` plan).
- Citing training-data API signatures for fast-moving libraries (Flask,
  SQLAlchemy, Pydantic, Playwright, Pytest) without a `context7` confirmation.
- Calling MCP servers that aren't in the current install (`duckduckgo`,
  `notebooklm`, `sqlite`, `sequential-thinking`, `filesystem`, `github`) —
  they were removed; use the equivalents in **Tools used** above.
