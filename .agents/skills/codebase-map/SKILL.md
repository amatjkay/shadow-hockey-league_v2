# SKILL: Codebase Map

## Purpose

Find symbols, routes, and config keys by signature — without reading whole files. Replaces `cat blueprints/admin_api.py` (893 lines) with `grep -n '^def\|^class' …` plus a 20-line context window.

## When to Use

- Before any change in `blueprints/admin_api.py`, `services/api.py`, `services/admin.py`, `services/rating_service.py`, `models.py`.
- Locating a route by URL pattern.
- Finding all callers of a service function.

## CLI Recipes

### Symbol index for a Python file

```bash
grep -nE '^(def |class |async def )' <path>
```

Returns `line:def name(...)` — read 20 lines around any hit.

### Find a route by URL

```bash
grep -rnE '@(api|admin|main|health)_bp.route\("/<keyword>' blueprints/ services/
```

### Find all callers of a function

```bash
grep -rn 'function_name(' --include='*.py' | grep -v 'def function_name'
```

### Find a config key

```bash
grep -nE '"\w+"\s*:|^\s*\w+\s*=' config.py | head -40
```

### Find an Alembic migration touching a table

```bash
grep -rln '<table_name>' migrations/versions/
```

### List all admin views

```bash
grep -nE 'class \w+View\b|add_view\(' services/admin.py
```

## Read-Window Pattern

```bash
LINE=$(grep -n '^def build_leaderboard' services/rating_service.py | cut -d: -f1)
sed -n "$((LINE-2)),$((LINE+40))p" services/rating_service.py
```

## Forbidden

- `cat <file>` for any file > 200 lines unless you genuinely need the whole thing.
- `find . -name '*.py'` without `-not -path './mcp-servers/*'` and `-not -path './.git/*'`.
- Recursive `grep` without a `--include` filter.

## Output

When using this skill, your context-budget block must list the exact `grep`/`sed` commands and the line ranges actually read — not the whole file.

Example:
```
## Контекст-бюджет: services/rating_service.py:1-40, services/rating_service.py:85-120 (build_leaderboard + helpers via grep)
```
