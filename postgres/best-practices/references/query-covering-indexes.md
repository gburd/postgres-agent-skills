---
title: Add INCLUDE Columns for Index-Only Scans
impact: MEDIUM-HIGH
impactDescription: Skips the heap fetch; 2-5x on hot read paths
tags: indexes, covering, include, index-only-scan
---

## Add INCLUDE Columns for Index-Only Scans

If an index contains every column a query needs, Postgres can answer from the
index alone — an index-only scan — and skip fetching the row from the heap. Use
`INCLUDE` to carry columns you select but do not filter on.

**Incorrect:**

```sql
create index on users (email);

-- index finds the row, then the heap is read for name, created_at
select email, name, created_at from users where email = 'a@example.com';
```

**Correct:**

```sql
create index on users (email) include (name, created_at);

-- all columns served from the index; no heap access
select email, name, created_at from users where email = 'a@example.com';
```

Index-only scans depend on the visibility map being current, so they pay off
most on tables that are vacuumed regularly and not constantly updated. Do not
`INCLUDE` wide or frequently-updated columns — it bloats the index and slows
writes.

Reference: [Index-Only Scans and Covering Indexes](https://www.postgresql.org/docs/current/indexes-index-only-scans.html)
