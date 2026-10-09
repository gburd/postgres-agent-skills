---
title: Keep Transactions Short — Never Hold a Lock Across an API Call
impact: MEDIUM-HIGH
impactDescription: More throughput, fewer deadlocks, vacuum can keep up
tags: transactions, locking, contention, statement-timeout
---

## Keep Transactions Short — Never Hold a Lock Across an API Call

A transaction holds its locks and pins the snapshot horizon until it commits.
Do slow work — HTTP calls, user think-time, heavy computation — *outside* the
transaction, and open the transaction only for the writes.

**Incorrect:**

```sql
begin;
select * from orders where id = 1 for update;   -- lock acquired
-- app now calls a payment API for 2-5 seconds, holding the row lock
update orders set status = 'paid' where id = 1;
commit;
```

**Correct:**

```sql
-- do the slow call first, with no transaction open
-- then take the lock only for the write
begin;
update orders
set    status = 'paid', payment_id = $1
where  id = $2 and status = 'pending'
returning *;
commit;                                           -- lock held for milliseconds
```

Back it up with a `statement_timeout` so a stray long statement cannot pin
locks indefinitely (see `ops-timeout-hygiene`). An open idle transaction is the
worst case — see `conn-idle-timeout`.

Reference: [Transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html) · [Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html)
