# Skill: Database Migration

## Goal

Ensure safe and reversible database schema changes using Alembic.

## When to Use

- Adding / dropping a column or index.
- Renaming a model or relationship.
- Any change to `models.py` that affects table structure.

## Tools used (verified 2026-05-04)

- `exec` running the project's own CLIs: `sqlite3`, `alembic`, `python`.
  There is **no** `sqlite` MCP server in this session — the older instruction
  to call `sqlite.describe_table` is obsolete.
- `read` / `edit` for reviewing the generated migration file.

## Workflow

1. **Schema check** — read the current shape of the affected table:

   ```bash
   ./venv/bin/python -c "from app import create_app; from models import db; \
       app = create_app(); ctx = app.app_context(); ctx.push(); \
       print(db.metadata.tables['<table>'].columns.keys())"
   # OR straight from the dev DB
   sqlite3 instance/dev.db ".schema <table>"
   ```

2. **Generate the migration**:

   ```bash
   ./venv/bin/alembic revision --autogenerate -m "<description>"
   ```

   Open the new file in `migrations/versions/` and **review it manually**.
   Autogenerate misses index/constraint renames and check constraints — fix
   those by hand if needed.

3. **Validation**:

   - Provide `./venv/bin/alembic upgrade head` to the user as the apply command.
   - Run `./venv/bin/alembic upgrade head --sql > migration.sql` first to inspect
     the generated DDL when the change is non-trivial.
   - **DO NOT** run `upgrade head` yourself unless the user explicitly asks.

4. **Rollback plan** — always include in the handoff message:

   ```bash
   ./venv/bin/alembic downgrade -1
   ```

5. **Tests**:

   - Add or update a test in `tests/` that exercises the new field/relationship.
   - Run `make test` to confirm the migration plays well with the test DB
     (which uses `db.create_all()`, not Alembic — so any imperative migration
     SQL needs to keep `models.py` in sync).
