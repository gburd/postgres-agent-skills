---
title: Enum vs Lookup Table — Pick by How Often the Set Changes
impact: MEDIUM
impactDescription: Avoids painful enum migrations for churny value sets
tags: enum, lookup-table, foreign-key, schema, check-constraint
---

## Enum vs Lookup Table — Pick by How Often the Set Changes

An `enum` type is compact and self-documenting, but editing it is awkward: you
can `ADD VALUE` (not inside a transaction block before PG 12; appended, not
reorderable without recreating the type) and you cannot easily *remove* a value.
A lookup table is a plain table with a foreign key — trivial to add, rename,
retire, and annotate.

**Incorrect:**

```sql
-- a set that will churn, modelled as an enum
create type order_status as enum ('pending','paid','shipped');
-- later: remove 'shipped', rename 'paid', add 'refunded' with metadata...
-- all of this is a type-recreation dance
```

**Correct:**

```sql
-- stable, tiny, never-changing set: enum is fine
create type weekday as enum
  ('mon','tue','wed','thu','fri','sat','sun');

-- churny set, or one that needs attributes: lookup table + FK
create table order_statuses (
  code  text primary key,
  label text not null,
  is_terminal boolean not null default false
);
create table orders (
  id     bigint generated always as identity primary key,
  status text not null references order_statuses(code)
);
```

Rule of thumb: enum for a short, fixed, attribute-free set (days, suits of
cards); lookup table the moment values change, carry metadata, or need
referential joins. A `text` column with a `CHECK (status in (...))` is a middle
ground for a small set with no metadata.

Reference: [Enumerated Types](https://www.postgresql.org/docs/current/datatype-enum.html) · [ALTER TYPE](https://www.postgresql.org/docs/current/sql-altertype.html)
