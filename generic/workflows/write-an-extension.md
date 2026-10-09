# Workflow: Write a PostgreSQL extension

An "extension" is a packaged bundle PostgreSQL tracks as a single object:
`CREATE EXTENSION my_extension` runs an SQL script, records every object it
creates in `pg_depend`, and lets `DROP EXTENSION` remove them as a unit. The
SQL script may be pure SQL, or it may bind to C functions in a shared library.
This skill is the map, not the whole territory.

## Inputs

- `task`: what the extension needs to do, in enough detail to decide SQL-only
  vs. C (step 1).

## Steps

### 1. Decide SQL-only vs. C before writing anything

If everything can be expressed as SQL/PL functions, views, and types, you need
no C and no shared library — drop `module_pathname`, write only the `.sql`, and
you are done. Reach for C when you need raw server internals, performance that
SQL cannot give, hooks, background workers, or new access methods.

### 2. Write the two mandatory files

Every extension needs a control file and at least one version SQL script,
installed into `$(pg_config --sharedir)/extension/`.

**`my_extension.control`** — the metadata PostgreSQL reads before running
anything:

```
# my_extension extension
comment = 'does one useful thing'
default_version = '1.0'
module_pathname = '$libdir/my_extension'
relocatable = true
requires = ''
```

- `default_version` — what `CREATE EXTENSION my_extension` installs with no
  `VERSION` clause. It must match a `my_extension--<version>.sql` file.
- `module_pathname` — expands `MODULE_PATHNAME` in the SQL script to the shared
  library path. Omit it for a SQL-only extension.
- `relocatable` — whether `ALTER EXTENSION ... SET SCHEMA` can move it later.
- `requires` — comma-separated other extensions that must be installed first.

**`my_extension--1.0.sql`** — the install script. It runs inside a transaction;
every object it creates is captured as a member of the extension. The build
substitutes `MODULE_PATHNAME` and leaves the rest verbatim:

```sql
-- complain if run directly rather than via CREATE EXTENSION
\echo Use "CREATE EXTENSION my_extension" to load this file. \quit

CREATE FUNCTION my_double(int) RETURNS int
    AS 'MODULE_PATHNAME', 'my_double'
    LANGUAGE C IMMUTABLE STRICT PARALLEL SAFE;
```

### 3. For C: follow the fmgr calling convention

C functions callable from SQL do not use ordinary C argument lists. They go
through the function manager (fmgr): one `Datum` return, arguments pulled from a
`FunctionCallInfo`. Every loadable module declares the magic block exactly once,
and marks each SQL-visible function.

```c
#include "postgres.h"
#include "fmgr.h"

PG_MODULE_MAGIC;                 /* once per .so; version-checked at load */

PG_FUNCTION_INFO_V1(my_double);  /* for each SQL-callable function */

Datum
my_double(PG_FUNCTION_ARGS)
{
    int32 arg = PG_GETARG_INT32(0);
    PG_RETURN_INT32(arg * 2);
}
```

- `PG_MODULE_MAGIC` embeds the server version/ABI; a mismatched `.so` is
  rejected at load, not left to crash.
- `PG_GETARG_<TYPE>(n)` unpacks argument `n`; `PG_RETURN_<TYPE>(x)` packs the
  result. Pass-by-reference types (text, arrays) use `PG_GETARG_TEXT_PP`,
  `PG_GETARG_DATUM`, detoasting macros, etc. Mark the SQL function `STRICT` so
  the server short-circuits NULL arguments and you never see them.

### 4. Hook into `_PG_init` if you need hooks, GUCs, or a bgworker

A loadable module may define `_PG_init(void)`, called once when the library is
first loaded. This is where you register hooks, GUCs, background workers, and
shared memory requests. Chain hooks — save the previous value and call it — so
you coexist with other modules:

```c
static ExecutorStart_hook_type prev_ExecutorStart = NULL;

static void
my_ExecutorStart(QueryDesc *queryDesc, int eflags)
{
    if (prev_ExecutorStart)
        prev_ExecutorStart(queryDesc, eflags);
    else
        standard_ExecutorStart(queryDesc, eflags);
    /* your logic */
}

void
_PG_init(void)
{
    prev_ExecutorStart = ExecutorStart_hook;
    ExecutorStart_hook = my_ExecutorStart;
}
```

Anything that hooks executor/planner internals, requests shared memory
(`shmem_request_hook` + `RequestAddinShmemSpace`), or starts a background worker
must be loaded via `shared_preload_libraries` — `_PG_init` then runs at
postmaster start, before backends exist.

### 5. Register GUCs with a reserved prefix

Register configuration variables in `_PG_init` with the `DefineCustomXxxVariable`
family; use a reserved prefix matching your extension so settings read as
`my_extension.enabled`:

```c
DefineCustomBoolVariable("my_extension.enabled",
                         "Enables the feature.",
                         NULL,
                         &my_enabled,
                         true,
                         PGC_SUSET, 0,
                         NULL, NULL, NULL);
MarkGUCPrefixReserved("my_extension");
```

### 6. Sketch a background worker and shared memory, if needed

A background worker is registered in `_PG_init` via
`RegisterBackgroundWorker(&worker)` with `bgw_main_function` and
`bgw_library_name`/`bgw_function_name`. Shared memory is requested in
`shmem_request_hook` with `RequestAddinShmemSpace(size)` and attached in
`shmem_startup_hook` with `ShmemInitStruct` under a named LWLock. Both paths
require `shared_preload_libraries`. These are deep topics — read the bgworker
and shmem docs before building one.

### 7. Load it

```sql
CREATE EXTENSION my_extension;        -- runs my_extension--1.0.sql
SELECT my_double(21);                 -- 42
```

## Outputs

A control file plus install script (and, if C is involved, a compiled shared
library) that loads cleanly with `CREATE EXTENSION` and exposes a first
working function. Once the mechanism works, follow
`community/conventions/extension-conventions.md` for build, versioning, and
security before you ship.

## See also

`community/conventions/extension-conventions.md`,
`community/coding-conventions.md` § "Memory Management", § "PG_TRY / PG_CATCH",
`postgres/developer/SKILL.md` § "The security & trust model",
`generic/workflows/package-an-extension.md`,
<https://www.postgresql.org/docs/current/extend-extensions.html>,
<https://www.postgresql.org/docs/current/xfunc-c.html>,
<https://www.postgresql.org/docs/current/sql-createextension.html>,
<https://www.postgresql.org/docs/current/bgworker.html>,
<https://www.postgresql.org/docs/current/xfunc-c.html#XFUNC-SHARED-ADDIN>.
