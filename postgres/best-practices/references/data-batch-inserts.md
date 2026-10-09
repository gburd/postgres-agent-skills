---
title: Batch Inserts — Multi-Row VALUES, or COPY for Bulk
impact: MEDIUM
impactDescription: 10-50x faster loads than row-at-a-time inserts
tags: insert, copy, bulk, batch, round-trips
---

## Batch Inserts — Multi-Row VALUES, or COPY for Bulk

A single-row `INSERT` per round trip spends almost all its time on protocol and
transaction overhead. Batch many rows into one statement, and for real bulk
loads use `COPY`, which is the fastest path into a table.

**Incorrect:**

```sql
insert into events (user_id, action) values (1, 'click');
insert into events (user_id, action) values (1, 'view');
-- ... one statement and round trip per row, thousands of times
```

**Correct:**

```sql
-- multi-row VALUES: one statement for a batch (a few hundred to ~1000 rows)
insert into events (user_id, action) values
  (1, 'click'), (1, 'view'), (2, 'click');   -- ...

-- bulk load: COPY is dramatically faster and bypasses per-row planning
copy events (user_id, action, created_at) from stdin with (format csv);
```

For a large initial load, consider loading into an unindexed table and building
indexes afterwards, and wrap the load in one transaction so it commits once. See
`ops-migration-safety` for doing this against a live table.

Reference: [COPY](https://www.postgresql.org/docs/current/sql-copy.html) · [Populating a Database](https://www.postgresql.org/docs/current/populate.html)
