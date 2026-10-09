---
title: Match the Index Type to the Query
impact: HIGH
impactDescription: The right access method is 10-100x; the wrong one is a seq scan
tags: indexes, btree, gin, gist, brin, hash, spgist
---

## Match the Index Type to the Query

B-tree is the default and the right choice for equality and ordered ranges. It
is the wrong choice for containment, arrays, full text, and geometry — there a
B-tree silently falls back to a sequential scan.

**Incorrect:**

```sql
-- B-tree cannot serve the @> containment operator
create index on products (attributes);
select * from products where attributes @> '{"color":"red"}';  -- Seq Scan
```

**Correct:**

```sql
-- GIN indexes containment, arrays, and full text
create index on products using gin (attributes);
select * from products where attributes @> '{"color":"red"}';
```

Decision guide:

- **B-tree** — `=`, `<`, `>`, `BETWEEN`, `IN`, `ORDER BY`, `IS NULL`. The default.
- **GIN** — many values per row: arrays, `jsonb` containment, `tsvector` full text.
  GIN's write cost is amortized by a pending list (`fastupdate`, on by
  default): inserts land in an unsorted pending list first and are folded into
  the main index later (by `VACUUM` or when the pending list fills past
  `gin_pending_list_limit`), trading faster individual inserts for occasional
  slower ones and a slightly stale index until the next flush. Turn
  `fastupdate` off (`create index ... with (fastupdate = off)`) on an index
  queried immediately after every write, where that latency spike is worse
  than steady-state slower inserts.
- **GiST** — geometry, range types, nearest-neighbour (KNN) ordering.
- **SP-GiST** — non-balanced structures: quadtrees, tries, some text/IP patterns.
- **BRIN** — huge, naturally-ordered tables (append-only time series); tiny index, coarse filtering.
- **Hash** — equality only; rarely worth choosing over B-tree.

## Index an expression, not just a column

A plain B-tree on `email` cannot serve a case-insensitive lookup; index the
expression you actually filter on:

```sql
-- Incorrect: forces a sequential scan when the query normalizes case
select * from account where lower(email) = 'jane@example.com';

-- Correct: index the expression the query uses
create index on account (lower(email));
select * from account where lower(email) = 'jane@example.com';
```

The query must use the *exact* indexed expression (same function, same
argument types) for the planner to match it — `lower(email)` in the query and
`lower(email)` in the index, not `lower(email::text)` on one side only.

## The HOT-update caveat

A Heap-Only Tuple (HOT) update — one that changes no column referenced by any
index — skips index maintenance entirely: PostgreSQL writes the new tuple
version in the same page and chains it from the old one, without touching a
single index. This is why updates to unindexed columns are so much cheaper
than updates to indexed ones. The corollary: adding an index on a column that
is frequently updated converts those updates from HOT (cheap) to non-HOT
(every index on the table must be maintained on every such update) — weigh a
new index's read benefit against this write-side cost on hot, frequently-
updated columns.

Reference: [Index Types](https://www.postgresql.org/docs/current/indexes-types.html)
