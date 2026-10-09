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

Reference: [CREATE INDEX CONCURRENTLY](https://www.postgresql.org/docs/current/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY) · [ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html)
