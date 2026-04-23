# Skill: Database Migration (Alembic-First)

## Description
Safe and structured database schema management using Alembic.

## Steps
1. **Schema Check**: Run `sqlite` MCP to inspect current tables.
2. **Backup**: Ensure `dev.db` is backed up before structural changes.
3. **Generate**: Run `alembic revision --autogenerate -m "description"`.
4. **Verify**: Review the generated script in `migrations/versions/`.
5. **Apply**: Provide the `alembic upgrade head` command to the user.

## Constraints
- **NEVER** modify `dev.db` directly for structural changes.
- **NEVER** run `upgrade head` automatically.
