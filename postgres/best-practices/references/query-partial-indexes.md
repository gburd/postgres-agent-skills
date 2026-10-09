---
title: Use Partial Indexes to Index Only the Rows You Query
impact: HIGH
impactDescription: Smaller index, cheaper writes, faster scans
tags: indexes, partial, where, soft-delete
---

## Use Partial Indexes to Index Only the Rows You Query

A partial index covers only rows matching a `WHERE` clause. If your queries
always carry the same predicate — active rows, pending jobs, non-null values —
a partial index is smaller, faster to scan, and cheaper to maintain on write.

**Incorrect:**

```sql
-- indexes every row, including the soft-deleted ones you never query
create index on users (email);

select * from users where email = 'a@example.com' and deleted_at is null;
```

**Correct:**

```sql
-- index only the live rows
create index on users (email) where deleted_at is null;

select * from users where email = 'a@example.com' and deleted_at is null;
```

For the planner to use a partial index, the query predicate must imply the
index predicate. A partial unique index is also the idiomatic way to enforce
"at most one active row per key": `create unique index on jobs (user_id) where
status = 'running'`.

Reference: [Partial Indexes](https://www.postgresql.org/docs/current/indexes-partial.html)
