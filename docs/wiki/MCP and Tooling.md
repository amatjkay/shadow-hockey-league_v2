# MCP and Tooling

Agent sessions on this repo combine **built-in tools** (always present)
and a small set of **MCP servers**. Canonical list in AGENTS.md § 4.
Verify the live install with `mcp_tool` `command="list_servers"`.

## Built-in tools

| Family | Purpose |
| :--- | :--- |
| `read` / `edit` / `write` / `grep` / `find_file_by_name` | Filesystem |
| `git` / `git_pr` / `git_comment` | PRs, comments, CI checks |
| `web_search` / `web_get_contents` | Web research |
| `exec` | Any CLI (`sqlite3`, `alembic`, `pytest`, `pip-audit`, `playwright`) |

## MCP servers (current install)

| Server | Purpose | Constraints |
| :--- | :--- | :--- |
| `context7` | Fresh library docs (1000+ packages) | Prefer over web for API questions. |
| `linear` | TIK-NN ticket CRUD | State transitions require user approval; see `linear-sync` skill. |
| `playwright` | Browser automation | Local dev server only — never prod. |
| `redis` | Query local Redis | Read-only unless cache invalidation is the explicit task. |

Retired / not installed (older docs may reference these): `duckduckgo`,
`notebooklm`, `sqlite`, `sequential-thinking`, `filesystem`, `github`.
Use the built-in equivalents above.

## Skills bridge

Project skills live under [`.agents/skills/<name>/SKILL.md`](../../.agents/skills/);
upstream `obra/superpowers` is mounted as a git submodule at
[`skills/superpowers/`](../../skills/) and symlinked into
`.agents/skills/superpowers`. See AGENTS.md § 7 and
[docs/SUPERPOWERS.md](../SUPERPOWERS.md).

## See also

- [[Agents and Skills]] — the skill index + sub-agent roles.
- AGENTS.md § 4 — canonical tool / MCP table.
