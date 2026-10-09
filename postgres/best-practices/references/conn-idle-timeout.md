---
title: Reclaim Idle and Idle-in-Transaction Connections
impact: HIGH
impactDescription: Frees connection slots and releases locks held by stuck sessions
tags: idle-in-transaction, timeout, locks, resource-management
---

## Reclaim Idle and Idle-in-Transaction Connections

A connection sitting "idle in transaction" is the dangerous one: it holds locks
and pins the transaction horizon, blocking vacuum and other writers. Set
timeouts so Postgres cleans these up instead of a human at 3am.

**Incorrect:**

```sql
show idle_in_transaction_session_timeout;  -- 0 (disabled)
-- a client began a transaction and wandered off; its locks block everyone
select pid, state, state_change from pg_stat_activity
where state = 'idle in transaction';       -- idle for hours
```

**Correct:**

```sql
-- abort transactions left idle (releases their locks and snapshot)
alter system set idle_in_transaction_session_timeout = '30s';
-- optionally close fully-idle sessions too
alter system set idle_session_timeout = '10min';
select pg_reload_conf();
```

Set `idle_in_transaction_session_timeout` aggressively — a well-behaved app
never holds an open transaction while idle. Be more conservative with
`idle_session_timeout` so you do not churn healthy pooled connections. If you
run a pooler, also set its own client/server idle timeouts.

Reference: [idle_in_transaction_session_timeout](https://www.postgresql.org/docs/current/runtime-config-client.html#GUC-IDLE-IN-TRANSACTION-SESSION-TIMEOUT)
