# Migrations

Alembic-only. **Never** call `db.create_all()` in production; **never**
hand-edit `migrations/versions/*` after merge. Canonical recipe lives
in [docs/MIGRATIONS.md](../MIGRATIONS.md); a richer how-to is in
`.agents/skills/db-migration/SKILL.md`.

## When you need a migration

- New table, column, index, or constraint.
- Backfilling a column that already exists in some envs (use the
  inspector pattern — see [decisionLog 2026-05-05](../decisionLog.md)).
- Server-default change that must propagate to prod.

## Quick recipe

```bash
# 1. Edit models.py.
# 2. Generate the migration:
alembic revision --autogenerate -m "TIK-NN: add <table>.<column>"
# 3. Hand-edit the generated file to be idempotent / no-op on dev DBs
#    where the column already exists (sa.inspect() + _has_column()).
# 4. Apply locally:
alembic upgrade head
# 5. Verify parity:
pytest tests/test_migrations_schema_parity.py
```

**Never auto-run `alembic upgrade head` for the user** — provide the
command, let the user run it (AGENTS.md § 2).

## Inspector-based idempotent column backfill

The repo's preferred pattern when the same column was added by
`db.create_all()` in some dev DBs but is missing in prod. Walks
`sa.inspect(op.get_bind()).get_columns(table)` before each
`op.add_column(...)`. Full rationale: `docs/decisionLog.md`
`2026-05-05 — Inspector-based idempotent column backfill`.

## See also

- [[Models and Database]] — the model layer this maps to.
- `.agents/skills/db-migration/SKILL.md` — the executable checklist.
