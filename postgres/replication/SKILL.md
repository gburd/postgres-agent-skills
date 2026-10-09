---
name: postgres-replication
description: >
  PostgreSQL skills for the replication specialist: physical streaming
  replication and hot standbys, replication slots and slot invalidation,
  synchronous vs asynchronous, cascading and delayed replicas, logical
  replication (publications/subscriptions) and its restrictions, failover and
  switchover, and major-version upgrades via logical replication. Use when
  setting up, operating, debugging, or failing over any form of Postgres
  replication, or when a standby falls behind or a slot is lost.
license: CC0-1.0
metadata:
  author: ddx
  version: "0.1.0"
  persona: replication
---

# PostgreSQL — Replication specialist

You know the ways Postgres copies data between servers, which to use when, and
how each fails. You treat replication as the thing standing between the
business and data loss, so you verify lag and slot health rather than assuming.

## When to apply

Setting up or operating a standby, choosing physical vs logical, tuning
synchronous commit, doing a failover/switchover, upgrading across a major
version with minimal downtime, or debugging a replica that stalls, diverges, or
loses its slot.

## The two families

**Physical (streaming) replication** — byte-for-byte WAL shipping; the standby
is an exact copy of the whole cluster, same major version. Use it for high
availability and read scaling.

- A standby replays WAL received over a streaming connection, falling back to
  archived WAL. Hot standby serves read-only queries.
- Protect against the primary recycling WAL the standby still needs with a
  **physical replication slot** (`pg_create_physical_replication_slot`), which
  holds WAL until the standby has consumed it.
- Guard the slot itself with `max_slot_wal_keep_size` so a dead/slow standby
  cannot fill the primary's disk — but understand the trade-off below.

**Logical replication** — decodes WAL into row changes and replays them via a
publication/subscription. Cross-version, selective (per-table), and the basis
for near-zero-downtime major upgrades. Read `../best-practices/references/ops-logical-replication.md`
for the restrictions that bite: **no DDL, no sequences, replica identity
required for UPDATE/DELETE, large-object caveats.**

## Synchronous vs asynchronous

- **Asynchronous** (default): the primary commits without waiting; a failover
  can lose the last few transactions. Lowest latency.
- **Synchronous** (`synchronous_standby_names` + `synchronous_commit`): the
  primary waits for the standby to flush/apply. No data loss on failover, at
  the cost of commit latency and an availability coupling — a lone sync standby
  going away *stalls the primary*. Use `ANY n (...)`/`FIRST n (...)` quorum and
  at least two candidates if you require sync.
- `synchronous_commit` is per-transaction: keep critical writes synchronous and
  let bulk/throwaway writes be `local`/`off`.

## Slot invalidation during a long catch-up (the classic HA failure)

A standby that has been down or is doing a multi-hour archive catch-up can have
its slot **invalidated** when the primary generates/recycles WAL past
`max_slot_wal_keep_size`. Symptoms: the standby logs `could not start WAL
streaming: ERROR: can no longer access replication slot ... invalidated due to
"wal_removed"`, then waits for WAL that no longer exists; on the primary the
slot's `wal_status` shows `lost`.

Recovery (only once the standby has archive-replayed to near the live edge —
compare its "waiting at <LSN>" to the primary's `pg_current_wal_lsn()`):

```sql
-- on the primary, recreate the slot reserving WAL at the current LSN
select pg_drop_replication_slot('standby_slot');
select * from pg_create_physical_replication_slot('standby_slot', true);
```

The standby then transitions from archive-catchup to `streaming` within
seconds. To help a lagging standby converge, reduce the primary's WAL
generation rate (pause heavy batch writers) rather than only raising keep-size.

## Monitoring (do this before trusting any replica)

```sql
-- on the primary: who is connected, in what state, how far behind (bytes)
select application_name, state,
       pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) as lag_bytes
from   pg_stat_replication;

-- slot health: 'lost' means a reseed/recreate is needed
select slot_name, slot_type, active, wal_status,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) as retained
from   pg_replication_slots;

-- on the standby
select status, latest_end_lsn, last_msg_receipt_time from pg_stat_wal_receiver;
select pg_is_in_recovery(), pg_last_wal_replay_lsn();
```

## Failover & switchover

- **Switchover** (planned): stop writes, let the standby catch up to zero lag,
  promote it (`pg_ctl promote` / `pg_promote()`), repoint the old primary as a
  standby (often needs `pg_rewind` if it diverged). No data loss if you drained
  first.
- **Failover** (primary is gone): promote a standby. With async replication you
  accept the loss of unreplicated commits; with sync you do not. **Fence the
  old primary** before promoting to avoid split-brain, and reseed any other
  standbys that followed the old timeline (or use `pg_rewind`).
- A promotion creates a new timeline; other standbys must follow it
  (`recovery_target_timeline = 'latest'`).

## Sequencing other work around replication

A `REINDEX` or an extension bump that rewrites indexes generates real WAL —
never run it while a standby is mid-catch-up; wait until
`pg_stat_wal_receiver` shows `streaming` and lag is ~0, then do the
maintenance on the primary as one deliberate step. Coordinate extension
upgrades across the pair (see `../best-practices/references/ops-extension-upgrades.md`),
especially extensions with a custom WAL resource manager, which can break
standby recovery on version skew.

Reference: [High Availability, Load Balancing, and Replication](https://www.postgresql.org/docs/current/high-availability.html) · [Logical Replication](https://www.postgresql.org/docs/current/logical-replication.html) · [Replication Slots](https://www.postgresql.org/docs/current/warm-standby.html#STREAMING-REPLICATION-SLOTS)
