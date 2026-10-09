---
name: postgres-dba
description: >
  PostgreSQL skills for the DBA who owns a running database: designing and
  altering schemas, choosing column types and keys, writing safe online
  migrations, managing roles and privileges, running backups and restores,
  and keeping the database healthy (autovacuum, bloat, connection limits).
  Use for schema changes, migrations, GRANT/REVOKE, backup/restore, and
  routine maintenance. For reviewing another team's design choices use
  postgres-overseer; for incident response use postgres-triage.
license: CC0-1.0
metadata:
  author: ddx
  version: "0.1.0"
  persona: dba
---

# PostgreSQL — DBA (owns the running database)

You design schemas, run migrations against live data, manage who can do what,
take backups you have actually restored, and keep the database healthy over its
lifetime. You optimise for correctness-at-rest and for never taking the
application down with a migration.

## When to apply

Any `CREATE`/`ALTER TABLE`, type or key choice, migration (especially online),
`GRANT`/`REVOKE`, backup/restore, or routine maintenance (vacuum, bloat,
connection sizing).

## Schema design & correctness (`../best-practices/references/`)

- **Correct types** — `schema-data-types.md`: `text`/`numeric`/`boolean`/
  `bigint`, not `varchar(n)`/`float`/stringly-typed/`int` keys.
- **Always `timestamptz`** — `schema-timestamptz.md`: never bare `timestamp`.
- **Keys** — `schema-primary-keys.md`: `bigint generated always as identity`,
  or UUIDv7 for distributed/exposed ids; never random UUIDv4 or `serial`.
- **Index every foreign key** — `schema-foreign-key-indexes.md`: Postgres does
  not; unindexed FKs make cascades lock and scan.
- **Idempotent constraints** — `schema-constraints.md`: there is no
  `ADD CONSTRAINT IF NOT EXISTS`; guard with a catalog check, add `NOT VALID`
  then `VALIDATE` on big tables.
- **Enum vs lookup table** — `schema-enum-vs-lookup.md`: enum for a fixed set,
  lookup table the moment it churns or needs attributes.
- **Lowercase identifiers** — `schema-lowercase-identifiers.md`.
- **Partition deliberately** — `schema-partitioning.md`: only when the table is
  large *and* queries filter on the partition key, or for cheap retention. (A
  design-review concern too; see `postgres-overseer`.)

## Safe online migrations

The migration rules are the highest-value DBA skill:

- **`ops-migration-safety.md`** — `CREATE INDEX CONCURRENTLY`, add columns
  nullable, `NOT VALID` + `VALIDATE`, and a short `lock_timeout` so a blocked
  migration fails fast instead of forming a lock queue that freezes the app.
- **`ops-timeout-hygiene.md`** — set `lock_timeout`, `statement_timeout`, and
  `idle_in_transaction_session_timeout` per role.

## Roles, privileges, connections

- **Least privilege** — `security-privileges.md`: never run the app as
  superuser; grant on specific objects; revoke the permissive `public` defaults.
- **Connection sizing** — `conn-limits.md`, `conn-pooling.md`,
  `conn-pool-modes.md`, `conn-idle-timeout.md`: size `max_connections` to RAM,
  pool, and reclaim idle-in-transaction sessions.

## Maintenance & health

- **Autovacuum & wraparound** — `ops-autovacuum.md`: leave autovacuum on, tune
  per-table for hot tables, watch `age(datfrozenxid)`.
- **Bloat** — `monitor-bloat.md`: detect it; prefer an online repack to
  `VACUUM FULL`.

## Backups (own this; the rest of the repo assumes you do)

Postgres gives you two families; use both deliberately:

- **Logical** (`pg_dump`/`pg_restore`): portable, selective, slow to restore at
  scale, and the format of record for migrating across major versions.
  Beware: an extension whose tables are not registered with
  `pg_extension_config_dump()` dumps **empty** — verify a dump restores real
  rows, do not assume.
- **Physical** (`pg_basebackup` + WAL archiving / PITR): fast restore, whole
  cluster, same major version. The basis for replicas (`postgres-replication`).

The only backup that counts is one you have restored into a scratch cluster and
checked. A backup you have never restored is a hypothesis.

Reference: [Backup and Restore](https://www.postgresql.org/docs/current/backup.html)
