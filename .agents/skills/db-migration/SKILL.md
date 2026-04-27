# SKILL: Safe Database Migration

## Purpose
Step-by-step workflow for safely modifying the `dev.db` schema using the `sqlite` MCP
for inspection and Alembic for migration execution.

## When to Use
- Adding new columns or tables
- Modifying column constraints
- Creating indexes
- Any schema change whatsoever

## Prerequisites
- `sqlite` MCP server connected to `<PROJECT_ROOT>/dev.db`
- Alembic configured (`alembic.ini` present in project root)
- Virtual environment activated

---

## Workflow

### Step 1: Inspect Current Schema
Use the `sqlite` MCP to understand the current state before making changes.

```
# List all tables
Tool: mcp_sqlite_list-tables

# Describe the target table
Tool: mcp_sqlite_describe-table
  tableName: "<target_table>"

# Check existing data that might be affected
Tool: mcp_sqlite_query
  sql: "SELECT COUNT(*) FROM <target_table>"

# Check foreign key references
Tool: mcp_sqlite_query
  sql: "SELECT * FROM pragma_foreign_key_list('<target_table>')"

# Check existing indexes
Tool: mcp_sqlite_query
  sql: "SELECT * FROM pragma_index_list('<target_table>')"
```

### Step 2: Modify the SQLAlchemy Model
Edit `models.py` to reflect the desired schema change:
- Add new columns with appropriate types, constraints, and defaults
- Add relationships if needed
- Follow existing patterns (see other models for examples)
- **Always** add `nullable=True` or `server_default` for new columns on existing tables

### Step 3: Generate Alembic Migration
```bash
# Generate migration script (do NOT run automatically — present to user)
cd <PROJECT_ROOT>
venv/bin/alembic revision --autogenerate -m "descriptive_migration_name"
```

### Step 4: Review Migration Script
- Open the generated file in `migrations/versions/`
- Verify the `upgrade()` and `downgrade()` functions are correct
- Check for batch operations (SQLite requires `batch_alter_table` for some ALTER operations)
- Ensure no data loss in downgrade path

### Step 5: Apply Migration (With User Approval)
```bash
# Show pending migrations
venv/bin/alembic history --verbose

# Apply migration
venv/bin/alembic upgrade head
```

### Step 6: Verify
```
# Confirm schema matches expectations
Tool: mcp_sqlite_describe-table
  tableName: "<target_table>"

# Run tests to ensure nothing broke
venv/bin/pytest
```

### Step 7: Update Documentation
- Update `docs/techContext.md` if the schema diagram changed
- Update `PROJECT_KNOWLEDGE.md` if new models or relationships were added
- Update `docs/progress.md` with migration status

---

## Safety Rules

> ⚠️ **NEVER** run raw `ALTER TABLE` or `DROP TABLE` via the `sqlite` MCP.
> Always use Alembic migrations.

> ⚠️ **ALWAYS** run a `SELECT` schema check before modifying anything.

> ⚠️ **ALWAYS** back up `dev.db` before applying migrations:
> ```bash
> cp dev.db dev.db.backup.$(date +%s)
> ```

## Common Pitfalls
1. **SQLite ALTER limitations**: Cannot drop columns or modify types in-place.
   Use `batch_alter_table` in Alembic.
2. **Foreign key enforcement**: SQLite doesn't enforce FK constraints by default.
   Check `PRAGMA foreign_keys` is enabled.
3. **Default values**: New non-nullable columns on existing tables need `server_default`.
