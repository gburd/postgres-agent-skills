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
- **GiST** — geometry, range types, nearest-neighbour (KNN) ordering.
- **SP-GiST** — non-balanced structures: quadtrees, tries, some text/IP patterns.
- **BRIN** — huge, naturally-ordered tables (append-only time series); tiny index, coarse filtering.
- **Hash** — equality only; rarely worth choosing over B-tree.

Reference: [Index Types](https://www.postgresql.org/docs/current/indexes-types.html)
