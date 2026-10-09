---
title: Index JSONB by How You Query It — GIN Operator Classes vs Expression Index
impact: MEDIUM
impactDescription: 10-100x on JSONB lookups, with a smaller index when you can use it
tags: jsonb, gin, jsonb-path-ops, expression-index, containment
---

## Index JSONB by How You Query It — GIN Operator Classes vs Expression Index

An unindexed `jsonb` query scans the table. The right index depends on *how*
you query: containment and key-existence want a GIN index; a single hot scalar
key is better served by a plain B-tree expression index.

**Incorrect:**

```sql
-- no index: both of these scan every row
select * from products where attributes @> '{"color":"red"}';
select * from products where attributes->>'brand' = 'Nike';
```

**Correct:**

```sql
-- containment / key-existence (@>, ?, ?&, ?|): GIN
create index on products using gin (attributes);
select * from products where attributes @> '{"color":"red"}';

-- a specific scalar key you filter on by equality: B-tree expression index
create index on products ((attributes->>'brand'));
select * from products where attributes->>'brand' = 'Nike';
```

Pick the GIN operator class by need: the default `jsonb_ops` supports all the
containment/existence operators; `jsonb_path_ops` supports only `@>` but builds
a smaller, faster index — use it when `@>` is all you need:

```sql
create index on products using gin (attributes jsonb_path_ops);
```

If a value is queried constantly, promoting it to a real column (or a generated
column) with its own index usually beats any JSONB index.

Reference: [JSON Types: Indexing](https://www.postgresql.org/docs/current/datatype-json.html#JSON-INDEXING) · [GIN Indexes](https://www.postgresql.org/docs/current/gin.html)
