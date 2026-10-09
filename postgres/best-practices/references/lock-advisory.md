---
title: Use Advisory Locks for Application-Level Mutual Exclusion
impact: MEDIUM
impactDescription: Coordinate without inventing a locking table
tags: advisory-locks, coordination, mutex, cron, leader-election
---

## Use Advisory Locks for Application-Level Mutual Exclusion

When you need "only one of these should run at a time" — a nightly report, a
migration step, a singleton worker — don't invent a table of dummy rows to lock.
Advisory locks give you a named, lightweight mutex keyed by an integer.

**Incorrect:**

```sql
-- a whole table whose only job is to be locked
create table locks (name text primary key);
insert into locks values ('nightly_report');
select * from locks where name = 'nightly_report' for update;
```

**Correct:**

```sql
-- transaction-scoped: released automatically at commit/rollback
begin;
select pg_advisory_xact_lock(hashtext('nightly_report'));
-- ... exclusive work ...
commit;

-- non-blocking variant: returns true if acquired, false if someone else holds it
select pg_try_advisory_lock(hashtext('singleton_worker'));
```

Prefer the `xact`-scoped variants so a crashed session cannot strand a
session-level lock. Advisory locks live in a single flat namespace per database
and are not tied to any row — they coordinate behaviour, they do not protect
data. For queue work prefer `SKIP LOCKED` (see `lock-skip-locked`).

Reference: [Advisory Locks](https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS)
