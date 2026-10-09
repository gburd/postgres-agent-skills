---
title: Use Composite Indexes for Multi-Column Filters, Equality First
impact: HIGH
impactDescription: One index scan instead of a bitmap AND of two indexes
tags: indexes, composite, multicolumn, column-order
---

## Use Composite Indexes for Multi-Column Filters, Equality First

When a query filters on several columns together, one composite index usually
beats several single-column indexes the planner has to combine. Column order is
not cosmetic: put equality columns first, range/inequality columns last.

**Incorrect:**

```sql
create index on orders (status);
create index on orders (created_at);

-- planner must bitmap-AND two indexes
select * from orders where status = 'pending' and created_at > '2024-01-01';
```

**Correct:**

```sql
-- equality column (status) first, range column (created_at) last
create index on orders (status, created_at);

select * from orders where status = 'pending' and created_at > '2024-01-01';
```

The leftmost-prefix rule governs reuse: an index on `(status, created_at)`
serves `WHERE status = ...` and `WHERE status = ... AND created_at > ...`, but
not `WHERE created_at > ...` alone. Order columns so the common query is a
prefix.

Reference: [Multicolumn Indexes](https://www.postgresql.org/docs/current/indexes-multicolumn.html)
