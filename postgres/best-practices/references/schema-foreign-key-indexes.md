---
title: Index Foreign Key Columns — Postgres Won't Do It For You
impact: HIGH
impactDescription: Fast joins and, critically, non-locking cascades
tags: foreign-key, indexes, joins, cascade, delete
---

## Index Foreign Key Columns — Postgres Won't Do It For You

Declaring a foreign key creates an index on the *referenced* side (it is
usually the PK) but **not** on the *referencing* column. Without that index,
joins scan, and worse, deleting or updating a parent row scans every child
table while holding locks.

**Incorrect:**

```sql
create table orders (
  id          bigint generated always as identity primary key,
  customer_id bigint references customers(id) on delete cascade
);
-- no index on customer_id:
delete from customers where id = 123;   -- seq-scans orders, holds locks
```

**Correct:**

```sql
create table orders (
  id          bigint generated always as identity primary key,
  customer_id bigint references customers(id) on delete cascade
);
create index on orders (customer_id);   -- now cascades and joins use it
```

Find unindexed foreign keys:

```sql
select c.conrelid::regclass as table_name,
       a.attname           as fk_column
from   pg_constraint c
join   pg_attribute  a on a.attrelid = c.conrelid and a.attnum = any(c.conkey)
where  c.contype = 'f'
  and  not exists (
         select 1 from pg_index i
         where i.indrelid = c.conrelid and a.attnum = any(i.indkey));
```

Reference: [Foreign Keys](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK)
