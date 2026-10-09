---
title: Mind Prepared Statements Under a Transaction-Mode Pooler
impact: HIGH
impactDescription: Avoids "prepared statement does not exist" errors under load
tags: prepared-statements, connection-pooling, transaction-mode, drivers
---

## Mind Prepared Statements Under a Transaction-Mode Pooler

A named prepared statement lives on one backend. In transaction-mode pooling
the next transaction may land on a different backend that never saw the
`PREPARE`, so `EXECUTE` fails with "prepared statement does not exist".

**Incorrect:**

```sql
prepare get_user as select * from users where id = $1;
-- next request, different backend from the pool:
execute get_user(123);   -- ERROR: prepared statement "get_user" does not exist
```

**Correct:**

```sql
-- Option A: deallocate within the same transaction
begin;
prepare get_user as select * from users where id = $1;
execute get_user(123);
deallocate get_user;
commit;

-- Option B: let the driver use the unnamed/extended-protocol statement
--   (parse+bind+execute in one round trip) instead of a durable named one.
-- Option C: run the client on a session-mode pool port.
```

Modern drivers increasingly support server-side prepared-statement caching that
is safe under transaction pooling (protocol-level statement names scoped per
transaction). If yours does not, disable client prepared statements for the
pooled connection or route it to session mode.

Reference: [PgBouncer: prepared statements](https://www.pgbouncer.org/features.html) · [PREPARE](https://www.postgresql.org/docs/current/sql-prepare.html)
