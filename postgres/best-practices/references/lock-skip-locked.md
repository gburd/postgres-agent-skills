---
title: Build Work Queues With FOR UPDATE SKIP LOCKED
impact: MEDIUM-HIGH
impactDescription: Workers never block each other; near-linear queue throughput
tags: skip-locked, queue, workers, concurrency, for-update
---

## Build Work Queues With FOR UPDATE SKIP LOCKED

A table-as-queue works well in Postgres if workers do not fight over the same
head-of-queue row. `FOR UPDATE SKIP LOCKED` lets each worker grab the next row
that nobody else has locked, instead of waiting.

**Incorrect:**

```sql
-- every worker targets the same oldest pending row and serialises on its lock
begin;
select * from jobs where status = 'pending'
order by created_at limit 1 for update;   -- worker 2 waits for worker 1
```

**Correct:**

```sql
-- claim-and-mark in a single statement; each worker gets a different row
update jobs
set    status = 'running', worker_id = $1, started_at = now()
where  id = (
  select id from jobs
  where  status = 'pending'
  order  by created_at
  for update skip locked
  limit  1
)
returning *;
```

Keep the claim transaction short (see `lock-short-transactions`) and make the
job handler idempotent — a worker can crash after claiming but before
finishing. For high-churn queues, a partial index on `(created_at) where status
= 'pending'` keeps the scan cheap, and partition or archive done rows to limit
bloat.

Reference: [SELECT ... FOR UPDATE / SKIP LOCKED](https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE)
