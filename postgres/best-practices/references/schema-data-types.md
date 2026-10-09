---
title: Choose Correct Column Types — text, numeric, boolean, bigint
impact: HIGH
impactDescription: Less storage, exact arithmetic, fewer whole classes of bug
tags: data-types, text, numeric, boolean, varchar, money, char
---

## Choose Correct Column Types — text, numeric, boolean, bigint

Postgres rewards picking the right type and punishes the common wrong ones.
`varchar(n)` buys you nothing over `text`; `char(n)` pads with spaces; `money`
has a fixed locale and limited precision; `float` cannot represent money
exactly; `int` keys overflow at ~2.1 billion.

**Incorrect:**

```sql
create table users (
  id         int,          -- overflows at 2.1e9
  email      varchar(255), -- arbitrary limit, no benefit
  is_active  varchar(5),   -- a boolean stored as text
  price      float,        -- 0.1 + 0.2 != 0.3
  code       char(10)      -- space-padded, surprising comparisons
);
```

**Correct:**

```sql
create table users (
  id         bigint generated always as identity primary key,
  email      text,
  is_active  boolean not null default true,
  price      numeric(10,2),   -- exact decimal
  code       text
);
```

Use `varchar(n)`/`char(n)` only when a hard length is a genuine domain
constraint — and even then a `text` column with a `CHECK (length(x) <= n)` is
often clearer. Use `numeric` for money, `bigint` for keys, `timestamptz` for
time (see `schema-timestamptz`).

Reference: [Data Types](https://www.postgresql.org/docs/current/datatype.html) · [Don't Do This: text (wiki)](https://wiki.postgresql.org/wiki/Don%27t_Do_This#Text_storage)
