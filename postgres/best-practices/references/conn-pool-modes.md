---
title: Choose the Right Pooling Mode — Transaction vs Session
impact: HIGH
impactDescription: Transaction mode packs far more clients onto each backend
tags: connection-pooling, transaction-mode, session-mode, pgbouncer
---

## Choose the Right Pooling Mode — Transaction vs Session

Poolers run in one of three modes. The choice decides how many clients share
one backend and which Postgres features keep working.

- **Session** — a backend is tied to a client for its whole connection.
  Everything works (session state, `SET`, temp tables, named prepared
  statements) but you get little multiplexing.
- **Transaction** — a backend is returned to the pool at each `COMMIT`/
  `ROLLBACK`. Dense multiplexing, but session state does not survive between
  transactions.
- **Statement** — returned after every statement; no multi-statement
  transactions. Niche.

**Incorrect:**

```sql
-- transaction-mode pool, but relying on session state across transactions
set my.tenant = '42';      -- runs on one backend
commit;
select current_setting('my.tenant');  -- may run on a different backend -> gone
```

**Correct:**

```sql
-- scope session-like state to the transaction that uses it
begin;
set local my.tenant = '42';   -- SET LOCAL lasts only this transaction
select ... ;                  -- same backend, same transaction
commit;
```

Default to transaction mode for web workloads. Use session mode only for
clients that genuinely need durable session state. See
`conn-prepared-statements` for the prepared-statement caveat that trips people
up in transaction mode.

Reference: [PgBouncer pooling modes](https://www.pgbouncer.org/features.html) · [SET](https://www.postgresql.org/docs/current/sql-set.html)
