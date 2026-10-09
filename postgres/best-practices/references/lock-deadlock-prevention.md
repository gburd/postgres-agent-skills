---
title: Prevent Deadlocks With a Consistent Lock Order
impact: MEDIUM-HIGH
impactDescription: Eliminates deadlock aborts under concurrency
tags: deadlocks, locking, ordering, transactions
---

## Prevent Deadlocks With a Consistent Lock Order

A deadlock happens when two transactions grab the same rows in opposite orders
and each waits on the other. Postgres detects it and aborts one — correct, but
your user sees an error. The cure is to always acquire locks in the same order.

**Incorrect:**

```sql
-- tx A locks row 1 then wants row 2; tx B locks row 2 then wants row 1
-- A: update accounts set balance = balance - 100 where id = 1;
-- B: update accounts set balance = balance -  50 where id = 2;
-- A: update ... where id = 2;   -- waits on B
-- B: update ... where id = 1;   -- waits on A  -> deadlock
```

**Correct:**

```sql
-- lock the whole working set up front, in a deterministic order
begin;
select id from accounts where id in (1, 2) order by id for update;
update accounts set balance = balance - 100 where id = 1;
update accounts set balance = balance + 100 where id = 2;
commit;
```

Or do it in one statement, which acquires its locks atomically:

```sql
update accounts
set balance = balance + case id when 1 then -100 when 2 then 100 end
where id in (1, 2);
```

Turn on `log_lock_waits` to catch contention before it becomes a deadlock.

Reference: [Deadlocks](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-DEADLOCKS)
