---
title: Know Logical Replication's Restrictions Before You Rely On It
impact: MEDIUM-HIGH
impactDescription: Prevents silent divergence and failed cutovers
tags: logical-replication, publication, replica-identity, ddl, sequences
---

## Know Logical Replication's Restrictions Before You Rely On It

Logical replication copies row changes, not everything. Teams reach for it for
upgrades and migrations and then get surprised by what it does *not* carry.
Learn the restrictions before the cutover, not during it.

The limits that bite most often:

- **DDL is not replicated.** Schema changes must be applied to the subscriber
  separately, usually subscriber-first for additive changes.
- **Sequences are not replicated.** After a cutover you must advance the
  target's sequences, or the first inserts collide.
- **`UPDATE`/`DELETE` need a replica identity.** A table with no primary key
  needs `REPLICA IDENTITY FULL` (every column in the WAL — expensive) or those
  changes error.
- **Large objects, truncate semantics, and some commands have caveats.**

**Correct:**

```sql
-- ensure every published table can replicate UPDATE/DELETE
alter table events replica identity full;      -- if no suitable unique key

create publication app_pub for table orders, events;
-- on the subscriber (schema already created there):
create subscription app_sub
  connection 'host=primary dbname=app'
  publication app_pub;

-- at cutover, advance target sequences past the source's values
select setval('orders_id_seq', (select max(id) from orders));
```

Confirm the sync completed (`pg_stat_subscription`, `srsubstate = 'r'`) before
sending traffic to the target, and reconcile sequences and any DDL applied
during the window.

Reference: [Logical Replication Restrictions](https://www.postgresql.org/docs/current/logical-replication-restrictions.html) · [Logical Replication](https://www.postgresql.org/docs/current/logical-replication.html)
