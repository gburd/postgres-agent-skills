---
title: Kill N+1 Queries With ANY(array) or a JOIN
impact: MEDIUM-HIGH
impactDescription: One round trip instead of one-per-row
tags: n-plus-one, batching, any, join, round-trips
---

## Kill N+1 Queries With ANY(array) or a JOIN

The N+1 pattern runs one query to get a list, then one more query per item in a
loop. The database is fine; the network round trips are the cost. Fetch the
children in a single query.

**Incorrect:**

```sql
-- 1 query for the users...
select id from users where active;
-- ...then N queries, one per user id
select * from orders where user_id = 1;
select * from orders where user_id = 2;   -- ... x N
```

**Correct:**

```sql
-- pass the ids as one array parameter
select * from orders where user_id = any($1::bigint[]);

-- or join and get everything in one shot
select u.id, o.*
from   users u
left join orders o on o.user_id = u.id
where  u.active;
```

`= ANY(array)` keeps a single parameterised statement (good for plan caching);
a `JOIN` is better when you also need columns from the parent. Either way it is
one round trip, not N.

Reference: [Array Functions and Operators](https://www.postgresql.org/docs/current/functions-array.html)
