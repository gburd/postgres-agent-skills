---
title: Upgrade Extensions Deliberately — Some Bumps Require a REINDEX
impact: MEDIUM-HIGH
impactDescription: Avoids broken indexes and recovery failures from a careless bump
tags: extensions, alter-extension, reindex, upgrade, replication
---

## Upgrade Extensions Deliberately — Some Bumps Require a REINDEX

An installed extension has a *catalog version* (`\dx`) that can lag the shipped
library. Upgrading is two steps: install the new files, then `ALTER EXTENSION
... UPDATE`. The hazard: some upgrades change an on-disk index format, so after
the update you must `REINDEX` or scans fail. Read the extension's upgrade notes
before bumping — do not assume a patch release is a drop-in.

**Incorrect:**

```sql
-- new library installed, but catalog never updated; or updated without
-- reading that this version changed the index format
alter extension my_index_am update;
select * from t where t.v <-> $1 < 10;   -- ERROR: index needs REINDEX
```

**Correct:**

```sql
-- 1. check current catalog version and what versions are available
select extname, extversion from pg_extension where extname = 'my_index_am';
select * from pg_available_extension_versions where name = 'my_index_am';

-- 2. read the extension's UPGRADING/CHANGELOG for the exact From->To row:
--    does it require a REINDEX? a shared_preload change? a restart?

-- 3. update the catalog, then reindex if the notes say so
alter extension my_index_am update to '2.0.0';
reindex index concurrently my_vector_idx;    -- only if required
```

Extra care on replicated systems: an extension that ships a **custom WAL
resource manager** can break standby recovery on version skew, so upgrade the
pair in a coordinated order. A version bump that rewrites indexes generates real
WAL — do not run it while a standby is still catching up; wait until replication
lag is zero, then do the `ALTER` + `REINDEX` as one deliberate maintenance step.

Reference: [ALTER EXTENSION](https://www.postgresql.org/docs/current/sql-alterextension.html) · [REINDEX](https://www.postgresql.org/docs/current/sql-reindex.html)
