---
name: postgres-triage
description: >
  PostgreSQL skills for when things go wrong: incident response, crash
  recovery, decoding mysterious errors in the server log, diagnosing a hung or
  stuck database, finding the blocking query, corruption detection and repair,
  disk-full and out-of-memory events, and transaction-ID wraparound
  emergencies. Use when the database is down, slow, stuck, throwing errors you
  don't recognise, or refusing writes, and you need to stabilise it fast
  without making it worse.
license: CC0-1.0
metadata:
  author: ddx
  version: "0.1.0"
  persona: triage
---

# PostgreSQL — Triage (incident response & recovery)

Something is on fire. Your job is to stabilise first, diagnose from evidence,
and avoid the panic move that turns an outage into data loss. Work from the
server log and the catalogs, change one thing at a time, and write down what
you did.

## When to apply

The database is down, hung, refusing connections or writes, out of disk or
memory, throwing errors you do not recognise, or returning wrong/missing rows
that smell like corruption.

## First five minutes (stabilise, don't thrash)

1. **Read the actual server log.** The real cause is almost always there in
   plain text; do not theorise before reading it. `log_min_messages`,
   `log_lock_waits`, and `log_checkpoints` earn their keep here.
2. **Is it up at all?** `pg_isready`; check the postmaster process and the OS
   (dmesg for the OOM killer, `df -h` for the data and WAL directories).
3. **Find the blocker, not the blocked** — read
   `../best-practices/references/monitor-locks.md`:
   ```sql
   select pid, pg_blocking_pids(pid), wait_event_type, wait_event,
          left(query,120)
   from pg_stat_activity where cardinality(pg_blocking_pids(pid)) > 0;
   ```
   Cancel (`pg_cancel_backend`) before terminating (`pg_terminate_backend`),
   and fix the cause (a long/idle transaction) rather than reaping backends on
   a loop.

## Decoding the error classes that scare people

- **"database is not accepting commands to avoid wraparound data loss"** —
  transaction-ID wraparound. The cluster is in protective read-only mode.
  Recovery: connect in single-user or as superuser and `VACUUM` the tables
  with the oldest `age(datfrozenxid)` (worst first); find the blocker that let
  it get this far (a long-abandoned transaction, a dropped replication slot,
  autovacuum disabled). See `../best-practices/references/ops-autovacuum.md`.
- **"could not read block ... in file ..." / checksum failures** — storage or
  page corruption. Stop writers, take a physical copy of the data directory
  *before* touching anything, and verify with `pg_amcheck` / `pg_checksums`.
  Do not `VACUUM FULL` or `REINDEX` blindly — that can propagate the damage.
- **"out of shared memory" / "too many clients already"** — exhausted
  connections or lock slots; see `conn-limits.md`. The immediate relief is a
  pooler and killing idle-in-transaction sessions; the fix is sizing.
- **"canceling statement due to ... timeout"** — your own timeouts firing
  (that is them working); or a lock queue behind a long holder.
- **"remaining connection slots are reserved for ... superuser"** — you are at
  the connection ceiling; connect as superuser via the reserved slots to triage.
- **systemd-oomd killed the service / full box reboot** — memory *pressure*
  (PSI), not just usage, trips oomd even under a cgroup `MemoryMax`. Relief:
  stop the biggest non-essential memory consumer (which also kills swap
  thrash) rather than only raising the cap; a cap raise alone often does not
  clear the pressure.

## Crash recovery & "it won't start"

- A clean start after a crash replays WAL automatically; let it finish, watch
  the log. Do **not** reach for `pg_resetwal` to force a start — it discards
  WAL and virtually guarantees logical corruption. It is a last resort after a
  physical backup, not a startup trick.
- If startup fails on a specific relation/catalog, the log names it; a
  stale/未regenerated `pg_control` or an incompatible on-disk version is a
  common cause after a botched upgrade or a half-applied config.

## Corruption: detect, isolate, repair the smallest unit

- **Detect**: `pg_amcheck` (heap + btree), `pg_checksums`, and extension-
  specific checkers. A single truncated file can break many unrelated objects
  at once, so scope the blast radius before repairing.
- **Isolate**: quarantine the bad artifact (a truncated packfile, a corrupt
  index) rather than deleting; take a copy first.
- **Repair the smallest unit**: rebuild one index (`REINDEX`), restore one
  table from backup, or (for an append-only derived store) rebuild just the
  affected shard — not the whole database. Rebuildable caches (a derived search
  index, an overview cache) are quarantine-and-recreate, not restore-from-backup.
- Repairs that generate WAL must respect any standby mid-catch-up (see
  `postgres-replication`).

## Flagging the genuinely mysterious

When a log line is not in any runbook: capture it verbatim with surrounding
context, note what changed just before (a deploy, an upgrade, a config
reload, a backup, a reboot that re-enabled timers and reset runtime
overrides), and the `pg-ddx-research` skill in `../../tooling/pg-ddx-research/` to search the
pgsql-hackers archive for the exact error text — someone has usually hit it.
Record the finding so the next incident is not a first encounter.

## The triage stance

Stabilise before you diagnose; diagnose from the log and catalogs, not a hunch;
copy before you mutate anything that looks corrupt; change one variable at a
time; and write a short timeline as you go so the post-incident review is not
archaeology. The dangerous moves (`pg_resetwal`, blind `VACUUM FULL` on
suspected corruption, deleting "stuck" files) are the ones that convert
recoverable incidents into permanent loss.

Reference: [Monitoring](https://www.postgresql.org/docs/current/monitoring.html) · [Routine Vacuuming: Wraparound](https://www.postgresql.org/docs/current/routine-vacuuming.html#VACUUM-FOR-WRAPAROUND) · [amcheck](https://www.postgresql.org/docs/current/amcheck.html)
