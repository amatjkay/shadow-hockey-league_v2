# SKILL: Linear Task Synchronization

## Purpose
A workflow for using the `linear` MCP server to read task requirements from Linear,
track progress, and update ticket statuses as work progresses.

## When to Use
- Starting a new task that has a Linear ticket
- Updating task status during implementation
- Linking Git branches and PRs to Linear tickets
- Reviewing task backlog for prioritization

## MCP Server Used
- `linear` — Task and issue management

## Project Convention
- **Ticket prefix:** `TIK-` (e.g., `TIK-42`)
- **PR format:** Include `Fixes TIK-ID` in PR description for auto-linking
- **Branch format:** `tik-42/short-description`

---

## Workflow

### Step 1: Discover Available Tasks
```
# Get team information and workflow states
Tool: mcp_linear_linear_get_teams

# Search for tasks assigned or relevant
Tool: mcp_linear_linear_search_issues
  query: "<search term>"
  states: ["Todo", "In Progress"]

# Or get a specific ticket by identifier
Tool: mcp_linear_linear_get_issue
  identifier: "TIK-42"
```

### Step 2: Read Task Requirements
```
# Get full issue details including comments and description
Tool: mcp_linear_linear_get_issue
  identifier: "TIK-42"
```

Extract from the issue:
- **Title** — What needs to be done
- **Description** — Detailed requirements and acceptance criteria
- **Comments** — Additional context or clarifications
- **Priority** — 0 (No priority) to 1 (Urgent)
- **Labels** — Feature area or type

### Step 3: Update Status → In Progress
```
# First, find the issue UUID (not the identifier)
Tool: mcp_linear_linear_search_issues_by_identifier
  identifiers: ["TIK-42"]

# Get team states to find the "In Progress" state ID
Tool: mcp_linear_linear_get_teams

# Update the issue status
Tool: mcp_linear_linear_edit_issue
  issueId: "<uuid>"
  stateId: "<in_progress_state_uuid>"
```

### Step 4: Work on the Task
Follow the Coder agent workflow:
1. Create a branch: `tik-42/short-description`
2. Implement the changes
3. Write tests
4. Update `docs/progress.md`

### Step 5: Update Status → Done / In Review
```
# When implementation is complete
Tool: mcp_linear_linear_edit_issue
  issueId: "<uuid>"
  stateId: "<done_state_uuid>"
```

### Step 6: Link PR to Ticket
When creating a PR via GitHub MCP, include in the PR body:
```
Fixes TIK-42

## Changes
- [description of changes]

## Testing
- [how it was tested]
```

---

## Common Operations

### List all projects
```
Tool: mcp_linear_linear_list_projects
```

### Search by priority
```
Tool: mcp_linear_linear_search_issues
  priority: 1  # Urgent
  states: ["Todo"]
```

### Bulk update tickets
```
Tool: mcp_linear_linear_bulk_update_issues
  issueIds: ["<uuid1>", "<uuid2>"]
  update:
    stateId: "<target_state_uuid>"
```

---

## Safety Rules

> ⚠️ **Do not** change ticket status without user approval for production-impacting tasks.

> ⚠️ **Do not** delete tickets — deactivate or move to backlog instead.

> ⚠️ **Always** verify the ticket exists before updating status.

## Notes
- Linear uses UUIDs internally, not the human-readable identifiers like `TIK-42`.
  Always resolve the identifier to a UUID first.
- The `get_teams` endpoint returns all workflow states (Todo, In Progress, Done, etc.)
  with their UUIDs — use these for status transitions.
