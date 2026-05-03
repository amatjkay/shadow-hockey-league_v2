# SKILL: Linear Task Synchronization

## Purpose

Read TIK-prefixed Linear tickets, update their status as work progresses, and
keep PR descriptions linked to the right ticket so the GitHub ↔ Linear
integration auto-closes them on merge.

## When to Use

- Starting a task that has a `TIK-NN` ticket.
- Transitioning a ticket between states (Todo → In Progress → In Review → Done).
- Cancelling stale tickets after backlog triage.
- Cross-referencing a PR to a ticket.

## MCP Server

- `linear` — see `mcp_tool` with `command="list_tools"` for the live signature.
  As of 2026-05-03 the Cognition `linear` MCP exposes `list_issues`,
  `get_issue`, `save_issue`, `list_issue_statuses`, `save_comment`,
  `list_comments`. Older `linear_*` tool names from this skill's earlier
  versions are obsolete.

## Project conventions

- **Ticket prefix:** `TIK-` (Tikispace team). Team ID is stable and discoverable
  via `list_issue_statuses({team: "Tikispace"})`.
- **Branch format:** `devin/<unix-ts>-tikNN-short-description` (matches the
  branch convention used since TIK-42).
- **PR linkage:** put `Closes TIK-NN` (or `Fixes TIK-NN`) in the PR body. The
  GitHub integration will (a) attach the PR to the ticket and (b) move the
  ticket to Done automatically when the PR merges into `main`. Do not also
  manually mark such tickets Done — let the integration do it.

## Workflow

### 1. Discover the ticket

```jsonc
// list_issues — fuzzy search
{"query": "TIK-55", "limit": 5}

// get_issue — full body, comments, attachments
{"id": "TIK-55"}
```

### 2. Find the target state

```jsonc
// list_issue_statuses — returns id+name+type for the team
{"team": "Tikispace"}
```

The Tikispace team uses these states (IDs are stable, but always re-fetch):

| Name | Type |
| :--- | :--- |
| Backlog | backlog |
| Todo | unstarted |
| In Progress | started |
| In Review | started |
| Done | completed |
| Canceled | canceled |
| Duplicate | canceled |

### 3. Move the ticket

```jsonc
// save_issue — for an existing issue, pass id; state accepts name OR uuid
{"id": "TIK-55", "state": "In Review"}
```

`save_issue` is **create-or-update**. For updates always pass `id`. Do NOT
pass `team` or `title` on updates — those are only required when creating.

### 4. Comment / attach evidence

```jsonc
// save_comment — append a comment
{"issueId": "TIK-55", "body": "PR https://github.com/.../pull/60 opened, CI green."}
```

### 5. PR-side wiring

In the PR body include a single line:

```
Closes TIK-55.
```

The Linear integration parses the `Closes`/`Fixes` keyword. Avoid wrapping it in
backticks — some integrations skip it.

## Safety

- Never bulk-cancel without user approval. Cancellations are recorded but not
  reversible without manual restoration.
- Never edit `description` on tickets you didn't open without the user's
  approval — Linear has no field-level revision history surfaced to MCP.
- For epic/sub-issue trees, transition the children first, then the epic.
  Linear does not auto-close epics when all children are Done.

## Common patterns

### Cancel a stale backlog ticket

```jsonc
{"id": "TIK-14", "state": "Canceled"}
// then leave a save_comment explaining why so the audit trail is clear.
```

### Promote In Progress → In Review on PR open

```jsonc
{"id": "TIK-55", "state": "In Review"}
```

Do this when you open the PR, not when CI goes green — the `In Review` semantic
is "ready for human eyes", which is the moment you ask for review.

### Re-fetch after change

`save_issue`'s response sometimes shows the *previous* status field (server
caching). To verify, immediately call `list_issues({"query": "TIK-NN"})` or
`get_issue({"id": "TIK-NN"})`.
