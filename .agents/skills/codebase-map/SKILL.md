# SKILL: Codebase Map

## Purpose

Find symbols, routes, and config keys by signature — without reading whole files. Replaces `cat services/admin/views.py` (375 lines) or `cat models.py` (~600 lines) with `grep -n '^def\|^class' …` plus a 20-line context window.

## When to Use

- Before any change in `services/api/`, `blueprints/admin_api/`, `services/admin/`, `services/rating_service.py`, `services/recalc_service.py`, `models.py`, `app.py`.
- Locating a route by URL pattern.
- Finding all callers of a service function.

## Package layout (post-TIK-42)

The three former monoliths are now Python packages — read the per-resource
leaf, not the package `__init__.py`:

| Old monolith | Package | Files |
| --- | --- | --- |
| `services/api.py` (920 LOC) | `services/api/` | `__init__.py` (api Blueprint) + `_helpers.py` + `countries.py` + `managers.py` + `achievements.py` |
| `blueprints/admin_api.py` (893 LOC) | `blueprints/admin_api/` | `__init__.py` (admin_api_bp) + `_helpers.py` + `lookups.py` + `achievements.py` |
| `services/admin.py` (635 LOC) | `services/admin/` | `__init__.py` (init_admin) + `base.py` (SHLModelView) + `views.py` (ModelViews) + `_rate_limit.py` |

Public imports are unchanged: `from services.api import api`, `from blueprints.admin_api import admin_api_bp`, `from services.admin import init_admin`.

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
grep -nE 'class \w+View\b' services/admin/views.py
grep -nE 'add_view\(' services/admin/__init__.py
```

### Find a public-API route

```bash
grep -rnE '@api\.route\("/<keyword>' services/api/
```

### Find an admin-API endpoint

```bash
grep -rnE '@admin_api_bp\.route\("/<keyword>' blueprints/admin_api/
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
