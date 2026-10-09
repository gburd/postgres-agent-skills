# Postgres skills

PostgreSQL-first skills, grouped by **how you interact with the database**.
Load the persona that matches your role on the current task; each persona
`SKILL.md` is a short map that curates the relevant rules from the shared
rule library in [`best-practices/`](best-practices/).

| Persona | You are… | Load for |
|---------|----------|----------|
| [`user/`](user/SKILL.md) | someone who runs queries | writing/tuning SQL, pagination, batching, N+1, slow-query triage of your own query |
| [`dba/`](dba/SKILL.md) | the database owner | schema design, types/keys, online migrations, roles/privileges, backup/restore, autovacuum/health |
| [`overseer/`](overseer/SKILL.md) | the reviewer/architect | reviewing design, PL/pgSQL, partitioning, index selection, extension choice, server + OS config |
| [`replication/`](replication/SKILL.md) | the replication specialist | physical/logical replication, slots, sync vs async, failover, cross-version upgrades |
| [`triage/`](triage/SKILL.md) | first responder | the database is down/stuck/slow, mysterious log errors, corruption, wraparound, OOM |
| [`developer/`](developer/SKILL.md) | a core/extension developer | C patches to the backend or extensions, patch-series discipline, internals, submission |

## Shared rule library

[`best-practices/`](best-practices/SKILL.md) holds 41 impact-ordered rules
(query, connection, security, schema, locking, data-access, monitoring,
operations, advanced), each naming an antipattern, the fix in runnable SQL, and
a canonical `postgresql.org` cross-reference. The personas point into it rather
than duplicating it.

Everything here is CC0-1.0 (public domain). See the repo root `LICENSE`.
