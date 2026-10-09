---
title: Set Timeouts — lock_timeout, statement_timeout, idle-in-transaction
impact: MEDIUM-HIGH
impactDescription: Turns indefinite hangs into fast, retryable failures
tags: lock-timeout, statement-timeout, idle-in-transaction, guc, resilience
---

## Set Timeouts — lock_timeout, statement_timeout, idle-in-transaction

By default a statement will wait forever for a lock, run forever, and an idle
open transaction will hold its locks forever. Each of these turns a small
problem into an outage. Set bounds so Postgres fails fast and the client can
retry.

**Incorrect:**

```sql
-- all three unbounded (the defaults are 0 = disabled)
show lock_timeout;                            -- 0
show statement_timeout;                       -- 0
show idle_in_transaction_session_timeout;     -- 0
```

**Correct:**

```sql
-- per role, so OLTP and batch jobs differ sensibly
alter role app_oltp  set statement_timeout = '15s';
alter role app_oltp  set lock_timeout = '3s';
alter role app_oltp  set idle_in_transaction_session_timeout = '30s';
alter role app_batch set statement_timeout = '30min';

-- or scope to one risky statement
set local lock_timeout = '2s';
```

Guidance: a short `lock_timeout` is especially important for migrations (see
`ops-migration-safety`) so DDL does not form a lock queue. `statement_timeout`
protects against runaway queries; set it generously for known-long batch roles,
tightly for user-facing ones. `idle_in_transaction_session_timeout` is the one
that saves vacuum — a leaked open transaction otherwise pins the cleanup
horizon indefinitely.

Reference: [Client Connection Defaults](https://www.postgresql.org/docs/current/runtime-config-client.html)
