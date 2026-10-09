---
title: Size max_connections to RAM, Not Optimism
impact: CRITICAL
impactDescription: Prevents out-of-memory crashes under concurrency
tags: max-connections, work-mem, memory, stability
---

## Size max_connections to RAM, Not Optimism

Raising `max_connections` does not add capacity; it adds the risk of running
out of memory. Each backend can use up to `work_mem` per sort/hash node, and a
single query can have several such nodes. The ceiling is memory, and a pooler
(see `conn-pooling`) is how you serve many clients from few backends.

**Incorrect:**

```sql
-- "we had connection errors, so we raised the limit"
alter system set max_connections = 1000;   -- on an 8 GB server
-- a few heavy queries each grab work_mem several times over -> OOM
```

**Correct:**

```sql
-- keep backends modest; multiplex clients through a pooler instead
alter system set max_connections = 100;
-- budget work_mem so a realistic concurrent load stays well under RAM:
--   peak_backends * nodes_per_query * work_mem  <<  usable RAM
alter system set work_mem = '16MB';
-- apply (max_connections needs a restart; work_mem a reload)
select pg_reload_conf();
```

Watch actual usage rather than guessing:

```sql
select state, count(*) from pg_stat_activity group by state;
```

Reference: [Connection Settings](https://www.postgresql.org/docs/current/runtime-config-connection.html) · [Resource Consumption: work_mem](https://www.postgresql.org/docs/current/runtime-config-resource.html#GUC-WORK-MEM)
