# PostgreSQL extension conventions

An extension runs *inside* the backend as the superuser or the invoking role,
shares the server's symbol namespace, and persists across upgrades. The
conventions below are what separate an extension users trust from one that
breaks on the next `ALTER EXTENSION ... UPDATE` or collides with another
module's symbols.

## Build with PGXS

Use the server's build infrastructure rather than hand-rolling compiler flags.
A minimal `Makefile`:

```makefile
EXTENSION   = my_extension
DATA        = my_extension--1.0.sql my_extension--1.0--1.1.sql
MODULE_big  = my_extension
OBJS        = src/my_extension.o src/worker.o
REGRESS     = basic upgrade
PG_CONFIG   = pg_config
PGXS       := $(shell $(PG_CONFIG) --pgxs)
include $(PGXS)
```

- `PG_CONFIG` lets a user point the build at a specific server
  (`make PG_CONFIG=/opt/pg17/bin/pg_config`); never hardcode paths.
- `MODULE_big` + `OBJS` builds one shared library from several objects; use
  `MODULES` for single-file modules.
- `EXTENSION` names the control file; `DATA` lists the SQL scripts to install.
- `REGRESS` names the `pg_regress` test scripts (see
  `generic/workflows/package-an-extension.md`).

## Versioning and upgrade scripts

Use semantic versions in `default_version`. The install script for a released
version is **immutable**: never edit `my_extension--1.0.sql` after users have it
installed, or two databases claiming "1.0" will have different schemas.

To change anything, bump the version and ship a migration:

```
my_extension--1.0.sql            # install at 1.0 (frozen)
my_extension--1.1.sql            # install fresh at 1.1
my_extension--1.0--1.1.sql       # upgrade an existing 1.0 to 1.1
```

`ALTER EXTENSION my_extension UPDATE TO '1.1'` chains the `--old--new` scripts.
You can skip shipping a full `--1.1.sql` install script if a chain exists, but
most extensions ship both. Keep each upgrade script small and reversible in
intent.

## Idempotency

Install and upgrade scripts should tolerate reasonable re-entry. Prefer
`CREATE OR REPLACE FUNCTION`; for objects without a `REPLACE` form, guard with
`IF NOT EXISTS` where it exists, or `DROP ... IF EXISTS` before create in an
upgrade script. Do not assume a clean slate.

## Schema placement and relocatability

- A `relocatable = true` extension creates its objects in the schema named by
  `CREATE EXTENSION ... SCHEMA`, and `ALTER EXTENSION ... SET SCHEMA` can move
  them later. It must not hardcode schema-qualified names internally.
- Set `relocatable = false` and a fixed `schema = my_extension` in the control
  file if objects reference each other by qualified name or must live in a known
  schema.
- Objects pinned by the backend to a schema (operator classes used by indexes,
  for instance) usually force `relocatable = false`.

## Naming to avoid collisions

Multiple extensions share one SQL namespace and one C symbol namespace.

- Prefix SQL functions, types, and GUCs with the extension name
  (`my_extension.setting`, `my_double`), and call `MarkGUCPrefixReserved`.
- In C, make every function and global `static` unless it is deliberately part
  of the module's public API. Two extensions exporting a non-static `init()` or
  a global `errcount` will clash at load. The dynamic linker resolves to one of
  them, silently.
- Declare `PG_MODULE_MAGIC` exactly once per shared library; its absence or
  duplication is a load-time error.

## SQL-level security labels

Mark every SQL function with correct volatility and parallel safety — the
planner trusts these and will produce wrong results or crashes if they lie:

- `IMMUTABLE` only if the result depends solely on arguments (no catalog reads,
  no clock, no GUC). `STABLE` within a statement. `VOLATILE` (the default)
  otherwise.
- `PARALLEL SAFE` only if the function touches no session state and does nothing
  parallel-unsafe. Default to `PARALLEL UNSAFE` when unsure.
- `STRICT` to short-circuit NULL inputs.

For `SECURITY DEFINER` functions, pin `search_path` so a caller cannot shadow
objects you reference:

```sql
CREATE FUNCTION my_extension.privileged() RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path = my_extension, pg_temp
    AS $$ ... $$;
```

Always include `pg_temp` last so a caller's temp schema cannot hijack name
resolution. Grant execute narrowly; `SECURITY DEFINER` without a pinned
`search_path` is a privilege-escalation bug.

## Trust boundary and memory

The extension runs with backend privileges, so treat all SQL-supplied input as
untrusted: validate lengths and ranges, never build dynamic SQL by string
concatenation (use `format(%I/%L)` or parameterized `SPI_execute_with_args`),
and bound every allocation.

C memory lives in memory contexts, not in `malloc`. Allocate with `palloc` in
the right context: short-lived scratch in the current context (freed when it
resets), anything that must outlive the call in a longer-lived context you
chose deliberately. Returning a pointer into a context that is about to reset is
a use-after-free. `ereport(ERROR)` does a `longjmp`, so code after it does not
run and locals needing to survive a `PG_TRY/PG_CATCH` must be `volatile`. See
`community/coding-conventions.md` § "Memory Management" and § "PG_TRY /
PG_CATCH" for the full discipline.

## See also

`generic/workflows/write-an-extension.md`,
`generic/workflows/package-an-extension.md`,
`community/coding-conventions.md`,
`postgres/developer/SKILL.md` § "The security & trust model",
`postgres/overseer/SKILL.md` § "Judging extensions (gatekeep hard)",
<https://www.postgresql.org/docs/current/extend-pgxs.html>,
<https://www.postgresql.org/docs/current/extend-extensions.html#EXTEND-EXTENSIONS-UPDATE-SCRIPTS>,
<https://www.postgresql.org/docs/current/xfunc-volatility.html>,
<https://www.postgresql.org/docs/current/sql-createfunction.html>,
<https://www.postgresql.org/docs/current/sql-alterextension.html>.
