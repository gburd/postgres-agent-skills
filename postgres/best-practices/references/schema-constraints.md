---
title: Add Constraints Idempotently — There Is No ADD CONSTRAINT IF NOT EXISTS
impact: HIGH
impactDescription: Migrations that can re-run without failing
tags: constraints, migrations, idempotent, alter-table
---

## Add Constraints Idempotently — There Is No ADD CONSTRAINT IF NOT EXISTS

Postgres has `CREATE TABLE IF NOT EXISTS` and `ADD COLUMN IF NOT EXISTS`, but
**not** `ADD CONSTRAINT IF NOT EXISTS`. A migration written that way is a syntax
error. Guard the add with a catalog check so the migration is re-runnable.

**Incorrect:**

```sql
-- ERROR: syntax error at or near "not"
alter table profiles add constraint if not exists uq_handle unique (handle);
```

**Correct:**

```sql
do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'uq_handle' and conrelid = 'public.profiles'::regclass
  ) then
    alter table public.profiles add constraint uq_handle unique (handle);
  end if;
end $$;
```

For a large table, add the constraint in two steps to avoid a long exclusive
lock: `ADD CONSTRAINT ... NOT VALID` (fast, blocks only new rows), then
`VALIDATE CONSTRAINT` (scans existing rows under a weaker lock). See
`ops-migration-safety`.

Reference: [ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html) · [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
