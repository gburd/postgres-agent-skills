---
title: Paginate by Keyset, Not OFFSET
impact: MEDIUM-HIGH
impactDescription: Page 10,000 is as fast as page 1
tags: pagination, keyset, seek, offset, performance
---

## Paginate by Keyset, Not OFFSET

`OFFSET n` makes the database generate and throw away `n` rows before returning
the page. Deep pages get linearly slower and can also skip or repeat rows when
data changes underneath. Keyset ("seek") pagination remembers the last row seen
and asks for rows after it — index-backed and constant time.

**Incorrect:**

```sql
-- page 10,000: fetches and discards 199,980 rows first
select * from products order by id limit 20 offset 199980;
```

**Correct:**

```sql
-- remember the last id from the previous page, then seek past it
select * from products where id > $last_id order by id limit 20;
```

For multi-column ordering, compare the whole tuple so ties are handled
correctly:

```sql
select * from products
where  (created_at, id) > ($last_created_at, $last_id)
order  by created_at, id
limit  20;
```

Keyset pagination needs an index matching the `ORDER BY`. It gives "next/
previous" naturally; arbitrary "jump to page N" is the one thing it does not do
cheaply — and that feature is rarely worth the deep-OFFSET cost anyway.

Reference: [SELECT: LIMIT and OFFSET](https://www.postgresql.org/docs/current/queries-limit.html)
