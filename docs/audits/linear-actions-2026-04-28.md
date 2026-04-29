# Linear actions — execution plan after audit-2026-04-28

> **Why a separate file?** The Linear MCP integration is installed at the org level, but its
> tools register only when a Devin session starts. The session that produced this analysis
> started **before** the integration was installed, so `mcp_linear_*` tools were unavailable
> in that session. This file is the exact action script that any subsequent session (or the
> Linear UI) can replay in a single pass.
>
> **Execution status:** Sections A and B were executed in commit `7758bd6` once the Linear
> MCP became available. This file is preserved as a historical execution record and as a
> template for future audit-driven Linear bulk operations.
>
> **Format:** for each action — desired outcome, ticket identifier (`TIK-NN`), tool calls
> (when running through the MCP), and a link back to the source in code or in the analysis
> document.

---

## A. Status changes for existing tickets

| ID | Action | Reason | Source |
|---|---|---|---|
| TIK-12 | **Cancel** | Premature optimization. `RatingService.build_leaderboard()` is already cached via `@cache.memoize` for 5 minutes (`services/rating_service.py`); no real performance degradation is observed. Reopen if the leaderboard becomes slow. | `audit-2026-04-28.md` §3, `audit-2026-04-28-analysis.md` §6 T-L-1 |
| TIK-16 | **Mark Done** | Already completed via TIK-33 / PR #24 (docs refresh). Points and multiplier tables are up to date in `PROJECT_KNOWLEDGE.md`. | `audit-2026-04-28.md` §3 |
| TIK-18 | **Cancel** | No clear scope. Tandem managers are already represented through `Manager.partner_id` (self-FK); what exactly should be "formalized" is undefined. Reopen if and when a concrete requirement appears. | `audit-2026-04-28.md` §3 |
| TIK-19 | **Cancel** | Already covered by tests. `tests/test_rating_service.py` contains 30 formula cases; a separate prod cross-check script is overkill. | `audit-2026-04-28.md` §3 |

### MCP tool calls (replay sequence)

```
# Step 1: fetch team UUID and workflow states
mcp_linear_linear_get_teams

# Step 2: resolve identifier → UUID
mcp_linear_linear_search_issues_by_identifier
  identifiers: ["TIK-12", "TIK-16", "TIK-18", "TIK-19"]

# Step 3: apply state changes (state UUIDs come from step 1)
mcp_linear_linear_edit_issue
  issueId: <TIK-12-uuid>
  stateId: <Cancelled-uuid>

mcp_linear_linear_edit_issue
  issueId: <TIK-16-uuid>
  stateId: <Done-uuid>

mcp_linear_linear_edit_issue
  issueId: <TIK-18-uuid>
  stateId: <Cancelled-uuid>

mcp_linear_linear_edit_issue
  issueId: <TIK-19-uuid>
  stateId: <Cancelled-uuid>
```

When cancelling, attach a comment that links back to this file and states the reason.

---

## B. New tickets for the confirmed bugs

> Create with `mcp_linear_linear_create_issue` (the exact tool name resolves on first MCP
> invocation). The `teamId` field is taken from `mcp_linear_linear_get_teams`.

### B.1. TIK-NN: B9 — Audit log not wired in production (P1)

**Title:** `[B9] Audit log not written in production — set_current_user_for_audit() never called from app code`

**Priority:** Urgent (P1)

**Labels:** `security`, `compliance`, `bug`

**Description:**

```markdown
## Problem

`AGENTS.md` §5 declares: "All admin CRUD actions logged via `audit_service.log_action()`".
In reality:

1. The function `audit_service.log_action()` **does exist** (`services/audit_service.py:27`)
   and is called from `services/recalc_service.py`, but it is **not used** by Flask-Admin
   for automatic CRUD logging. Automatic CRUD logging is implemented through a separate
   listener `@event.listens_for(Session, "after_flush")` at `services/audit_service.py:209-216`.
2. The listener early-returns when `flask.g.current_user_id` is empty:
   ```python
   current_user_id = getattr(g, "current_user_id", None)
   if not current_user_id:
       return  # Skip if no authenticated user
   ```
3. The setter `set_current_user_for_audit(user_id)` is defined in
   `services/audit_service.py:286-288`, but is **never called** from production code.
   `grep set_current_user_for_audit`:
   - 3 hits in `tests/test_audit_delete.py`
   - 8 hits in `tests/integration/test_audit_logging.py`
   - 1 hit — the definition itself
   - 3 hits — references to the same problem in `docs/decisionLog.md:114`,
     `docs/progress.md:126`, `PROJECT_KNOWLEDGE.md:42`

→ In production no admin action is written to `audit_log`. Compliance violation since
the mechanism was introduced.

## Acceptance criteria

- [ ] In `app.py::create_app()` register a `before_request` hook that reads
      `flask_login.current_user` and calls
      `set_current_user_for_audit(current_user.id)` for the authenticated user.
- [ ] Register a `teardown_request` (or equivalent) that resets the context.
- [ ] Add an integration test `tests/integration/test_audit_logging_e2e.py`:
      login → admin mutation → assert a row in `audit_log`.
- [ ] Update `AGENTS.md` §5 to describe **both** audit mechanisms — the explicit
      `log_action()` API (used for non-CRUD events) and the listener path (used by
      Flask-Admin CRUD). Do not delete the reference to `log_action()`.
- [ ] Remove B9 from `docs/activeContext.md` Active Blockers once the fix lands.

## References

- Code: `services/audit_service.py:209-216`, `services/audit_service.py:286-288`
- Audit: `audit-2026-04-28.md` §4 B9
- Analysis: `docs/audits/audit-2026-04-28-analysis.md` §1.1, §6 T-B9-1/2/3

## Effort

≤ 1 hour fix + 30 min test + 15 min docs.
```

### B.2. TIK-NN: B10 — `/health` blocks without socket_timeout (P2)

**Title:** `[B10] /health endpoint blocks 5-7s when Redis unavailable — missing socket_timeout`

**Priority:** Medium (P2 dev / P3 prod)

**Labels:** `bug`, `performance`, `dev-experience`

**Description:**

```markdown
## Problem

`blueprints/health.py:75-82`:

```python
redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    socket_connect_timeout=2,
)
redis_client.ping()
```

`socket_connect_timeout=2` is set, but `socket_timeout` is not. If Redis accepts the
connection but does not respond (or the network has issues post-connect), `ping()`
hangs up to the system default. On dev environments without Redis, `/health` is
observed to hang for 5-7 seconds.

## Acceptance criteria

- [ ] Add `socket_timeout=1.0` to `redis.Redis(...)`.
- [ ] Local smoke (no Redis): `time curl localhost:5000/health` returns in <1.5s.
- [ ] Regression test: mock Redis simulating a slow read; `/health` does not hang.

## References

- Code: `blueprints/health.py:75-82`
- Audit: `audit-2026-04-28.md` §4 B10
- Analysis: `docs/audits/audit-2026-04-28-analysis.md` §1.5, §6 T-B10-1

## Effort

≤ 15 min fix + 30 min test.
```

### B.3. TIK-NN: B11 — Metrics banner mismatches /metrics output (P3)

**Title:** `[B11] App startup banner advertises http_requests_total but /metrics doesn't expose it`

**Priority:** Low (P3 cosmetic)

**Labels:** `bug`, `observability`

**Description:**

```markdown
## Problem

`app.py:233-236`:

```python
app.logger.info("Prometheus metrics enabled at /metrics")
app.logger.info(
    "Default metrics: http_requests_total, http_request_duration_seconds"
)
```

Per the audit, `/metrics` actually exposes only `http_request_duration_seconds`
(histogram). The counter `http_requests_total` is not registered in
`prometheus_flask_exporter`.

This is a **hypothesis** that needs verification (T-V-3): run the app locally, hit
`/metrics`, and dump the actual list of metric families.

## Acceptance criteria

- [ ] Run `make run` locally and dump `curl localhost:5000/metrics | grep -E '^# (HELP|TYPE)'`.
- [ ] If `http_requests_total` is missing — either remove it from the log banner, or
      register the counter through `PrometheusMetrics(app).request_counter` (if not yet).
- [ ] The log banner exactly matches the actual `/metrics` after the fix.

## References

- Code: `app.py:233-236`
- Audit: `audit-2026-04-28.md` §4 B11
- Analysis: `docs/audits/audit-2026-04-28-analysis.md` §1.6, §6 T-V-3, T-B11-1

## Effort

≤ 30 min (including T-V-3 verification).
```

### MCP tool calls (replay sequence)

```
mcp_linear_linear_create_issue
  teamId: <team-uuid>
  title: "[B9] Audit log not written in production..."
  description: <see B.1>
  priority: 1   # Urgent
  labels: ["security", "compliance", "bug"]

mcp_linear_linear_create_issue
  teamId: <team-uuid>
  title: "[B10] /health endpoint blocks 5-7s..."
  description: <see B.2>
  priority: 3   # Medium
  labels: ["bug", "performance"]

mcp_linear_linear_create_issue
  teamId: <team-uuid>
  title: "[B11] App startup banner mismatch..."
  description: <see B.3>
  priority: 4   # Low
  labels: ["bug", "observability"]
```

---

## C. Tickets that stay open without status changes

| ID | Action | Comment |
|---|---|---|
| TIK-14 | Keep open, lower priority to P3 | Player Search UI on the homepage — a real feature gap, but 42 managers fit on one page. Not urgent. |
| TIK-15 | Keep open, P3 | Admin Achievement Preview — minor UX polish. |
| TIK-17 | Keep open, P3 | OpenAPI spec — useful when external integrators appear. None today. |

---

## D. Checklist for the executing agent in a new Devin session

- [ ] Confirm the Linear MCP tools are registered (`mcp_linear_linear_get_teams` responds).
- [ ] Fetch team UUID and workflow states (especially the `Cancelled` and `Done` state UUIDs).
- [ ] Apply §A (4 status updates).
- [ ] Create the 3 new tickets per §B (B9 / B10 / B11) with the descriptions above.
- [ ] In each of the new tickets, add a link back to PR #31 (the analysis PR) and to the
      committed `docs/audits/audit-2026-04-28-analysis.md`.
- [ ] Update `docs/audits/audit-2026-04-28-analysis.md` §6 — replace `TIK-NN` placeholders
      with the real identifiers of the newly created tickets.
- [ ] Commit the update on branch `devin/1777399212-audit-analysis`.
