# Skill: Database Migration

## Goal

Ensure safe and reversible database schema changes using Alembic.

## Workflow

1. **Schema Check**:
   - Run `sqlite.describe_table` to see current schema.
   - Run `alembic current` to see current migration state.

2. **Generate Migration**:
   - Run `alembic revision --autogenerate -m "description"`.
   - **Review** the generated file in `migrations/versions/`.

3. **Validation**:
   - Provide the migration command to the user: `alembic upgrade head`.
   - **DO NOT** run it yourself unless the user explicitly asks.

4. **Rollback Plan**:
   - Always prepare `alembic downgrade -1` in case of failure.
