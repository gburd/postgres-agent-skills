---
title: Index the Columns You Filter and Join On
impact: CRITICAL
impactDescription: Turns sequential scans into index scans; often 100-1000x on large tables
tags: indexes, sequential-scan, joins, where
---

## Index the Columns You Filter and Join On

A query that filters or joins on an unindexed column forces a sequential scan
of the whole table. That cost grows with the table; what is instant on 10k rows
is a timeout on 10M.

**Incorrect:**

```sql
-- no index on customer_id -> Seq Scan over every order
select * from orders where customer_id = 123;
```

**Correct:**

```sql
create index on orders (customer_id);

-- now an Index Scan: a handful of pages, not the whole heap
select * from orders where customer_id = 123;
```

Index the referencing side of every join. For `a JOIN b ON b.a_id = a.id`, the
column that needs an index is `b.a_id`.

Confirm the planner actually uses the index with `EXPLAIN` (see
`monitor-explain-analyze`). An index the planner ignores (wrong type, low
selectivity, stale statistics) is dead weight on writes.

Reference: [Indexes](https://www.postgresql.org/docs/current/indexes.html)
