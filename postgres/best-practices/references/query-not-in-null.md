---
title: Never Use NOT IN With a Subquery — Use NOT EXISTS
impact: HIGH
impactDescription: Prevents a silent wrong-answer correctness bug
tags: not-in, not-exists, null, anti-join, correctness
---

## Never Use NOT IN With a Subquery — Use NOT EXISTS

If the subquery behind `NOT IN` returns even one `NULL`, the whole expression
evaluates to "unknown" for every row and the query returns **no rows** — not an
error, just a silently empty result. This is a correctness bug, not a
performance one, and it hides until a NULL appears in production data.

**Incorrect:**

```sql
-- if any customers.id is NULL, this returns zero rows, always
select * from orders
where customer_id not in (select id from customers where active);
```

**Correct:**

```sql
-- NOT EXISTS is NULL-safe and the planner turns it into an anti-join
select o.* from orders o
where not exists (
  select 1 from customers c where c.id = o.customer_id and c.active
);
```

`NOT EXISTS` is also usually faster: the planner implements it as a hashed or
merge anti-join, whereas `NOT IN` with a subquery often cannot be optimised the
same way. Reserve `IN`/`NOT IN` for small, literal, NULL-free value lists.

Reference: [Don't use NOT IN (wiki)](https://wiki.postgresql.org/wiki/Don%27t_Do_This#Don.27t_use_NOT_IN) · [Subquery Expressions](https://www.postgresql.org/docs/current/functions-subquery.html)
