---
title: Pool Connections — Don't Open One Per Request
impact: CRITICAL
impactDescription: Handle 10-100x more concurrent clients on the same server
tags: connection-pooling, pgbouncer, scalability, backends
---

## Pool Connections — Don't Open One Per Request

Every Postgres connection is a backend process with its own memory (roughly
1-3 MB plus whatever `work_mem` a query uses). Opening a connection per request
exhausts RAM and the process table long before you run out of CPU. Put a pooler
between the application and Postgres.

**Incorrect:**

```sql
-- app opens a fresh connection per request
-- 500 concurrent requests -> 500 backends -> out of memory
select count(*) from pg_stat_activity;  -- 487
```

**Correct:**

```sql
-- app connects to a pooler (PgBouncer, pgcat, or a built-in driver pool);
-- the pooler multiplexes a small set of real backends
-- 500 concurrent requests share, say, 20 backends
select count(*) from pg_stat_activity;  -- 20
```

A useful starting pool size is roughly `(core_count * 2) + effective_spindle
count`; measure, don't guess. More backends past that point reduces throughput
because they contend for CPU and locks. See `conn-pool-modes` for which pooling
mode to run.

Reference: [Number Of Database Connections (wiki)](https://wiki.postgresql.org/wiki/Number_Of_Database_Connections)
