---
title: Diagnose Slow Queries With EXPLAIN (ANALYZE, BUFFERS)
impact: MEDIUM
impactDescription: Replaces guesswork with the actual plan and timings
tags: explain, analyze, buffers, query-plan, diagnostics
---

## Diagnose Slow Queries With EXPLAIN (ANALYZE, BUFFERS)

`EXPLAIN` shows the planner's estimate; `EXPLAIN (ANALYZE, BUFFERS)` runs the
query and shows what actually happened, including how many buffers were read.
Read the actual-vs-estimated row counts and the buffer numbers — that is where
the problem usually is.

**Incorrect:**

```sql
-- "it's slow, probably a missing index" — on which column, though?
select * from orders where customer_id = 123 and status = 'pending';
```

**Correct:**

```sql
explain (analyze, buffers)
select * from orders where customer_id = 123 and status = 'pending';
```

What to look for:

- **Seq Scan on a big table** with a selective filter → missing/unused index.
- **"Rows Removed by Filter"** large → the scan read far more than it returned.
- **estimated rows wildly off actual rows** → stale statistics; `ANALYZE` the
  table (see `ops-autovacuum`).
- **Buffers: read ≫ hit** → working set not cached.
- **"Sort Method: external merge Disk"** → `work_mem` too low for this query.

`ANALYZE` executes the statement — wrap data-modifying statements in a
transaction you `ROLLBACK`. For queries too slow to run, enable `auto_explain`
to capture plans from production.

Reference: [Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)
