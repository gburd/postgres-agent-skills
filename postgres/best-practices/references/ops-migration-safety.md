---
title: Run Migrations Online — Don't Lock Out the Application
impact: MEDIUM-HIGH
impactDescription: Schema changes on a live database without an outage
tags: migrations, online-ddl, concurrently, lock-timeout, add-column
---

## Run Migrations Online — Don't Lock Out the Application

Most DDL takes a strong lock. On a busy table the danger is not the DDL itself
but the lock queue it creates: one `ALTER` waiting behind a long query blocks
every query that arrives after it. Use the concurrent/online forms and bound
the wait.

**Incorrect:**

```sql
create index on orders (customer_id);          -- ACCESS EXCLUSIVE: blocks writes
alter table orders add column notes text default 'n/a' not null;  -- rewrites table
```

**Correct:**

```sql
-- build the index without blocking writes (runs outside a txn, can't be in one)
create index concurrently on orders (customer_id);

-- add a nullable column: metadata-only on modern Postgres, no rewrite
alter table orders add column notes text;
-- backfill in batches, then add the NOT NULL as a validated constraint:
alter table orders add constraint notes_not_null check (notes is not null) not valid;
-- ... backfill ...
alter table orders validate constraint notes_not_null;   -- weak lock

-- cap how long any migration statement will wait for its lock, and retry
set lock_timeout = '3s';
```

Rules of thumb: `CREATE INDEX CONCURRENTLY` / `REINDEX CONCURRENTLY`; add
columns nullable (a plain default is fine on PG 11+, but `NOT NULL` + default
on an old version rewrites); add constraints `NOT VALID` then `VALIDATE`; set a
short `lock_timeout` so a blocked migration fails fast and retries instead of
freezing the application. A `CONCURRENTLY` build that fails leaves an `INVALID`
index — drop it before retrying.

## Which DDL takes which lock

| Lock | Blocks | Example DDL |
|---|---|---|
| `ACCESS EXCLUSIVE` | Everything, including `SELECT` | `ADD COLUMN` with a volatile default; `SET NOT NULL` (pre-PG12 or without a prior validated `CHECK`); most `ALTER TYPE` column-type changes that rewrite storage; `ADD PRIMARY KEY`; `DROP COLUMN`; `TRUNCATE`; a non-concurrent `CREATE INDEX` |
| `SHARE UPDATE EXCLUSIVE` | Other DDL and `VACUUM`, but not reads/writes | `CREATE INDEX CONCURRENTLY`; `VALIDATE CONSTRAINT`; `ALTER TABLE ... VALIDATE`; `ANALYZE` |

Even the weaker lock still queues behind, and blocks, anything stronger
requested after it — pair every DDL statement with a short `lock_timeout` and
a retry, not just the ones you know take `ACCESS EXCLUSIVE`.

## Type changes that do NOT rewrite the table

Most `ALTER COLUMN ... TYPE` changes rewrite every row under `ACCESS
EXCLUSIVE`. A few widening casts are exempt because the on-disk
representation is unchanged, so Postgres only updates the catalog:

```sql
-- none of these rewrite the table or its indexes
alter table account alter column notes type text;             -- varchar(10) -> text
alter table account alter column notes type varchar(50);       -- varchar(10) -> varchar(50)
alter table account alter column balance type numeric(12,2);   -- numeric precision increase
```

Narrowing a type, changing a numeric's *scale* downward, or converting
between genuinely different representations (e.g. `text` to `integer`) still
rewrites. Check `pg_attribute`/the release notes for the specific pair before
assuming a cast is free.

## Expand / contract for a real type or shape change

When the change is not one of the free casts above, don't rewrite in place —
expand, migrate, then contract:

1. **Expand** — add the new column/table/index alongside the old; deploy
   application code that writes *both*, reads the old.
2. **Migrate** — backfill old → new in batches, pausing between batches so
   autovacuum and replication keep up (never one `UPDATE`/`INSERT` touching
   the whole table in a single transaction); deploy application code that
   reads the new.
3. **Contract** — once nothing reads the old column/table/index, drop it
   (`DROP ... CONCURRENTLY` where that form exists).

Each of the three steps is independently reversible and never holds a long
lock, unlike an in-place rewrite of a large table.

Reference: [CREATE INDEX CONCURRENTLY](https://www.postgresql.org/docs/current/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY) · [ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html) · [Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html)
