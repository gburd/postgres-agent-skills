# Workflow: Debug initdb

`initdb` initialises a PostgreSQL data directory. When it fails, the
debugging is unusual: the postmaster does not exist yet, the system
catalogs are being populated from raw `.bki` files, and the binary at
fault is a single-process backend running in a special mode. This
skill covers the actual mechanics.

## TL;DR — what initdb does, in order

From `src/bin/initdb/initdb.c`'s leading block comment and the
sequence of helpers:

1. Validate environment (locale, ICU, user privileges, target dir).
2. Create the data directory and its subdirectories.
3. Compute & write `pg_control`.
4. Run **bootstrap mode** (`postgres --boot ...`) to populate
   template1's system catalogs from `postgres.bki`.
5. Run **standalone backend** (`postgres --single ...`) to issue
   SQL that creates the rest of `template1` (system views, default
   functions).
6. Copy `template1` to `template0` and `postgres` databases.
7. Vacuum and freeze.
8. Print "Success." or report a failure with the partial dir.

Each step has its own failure modes.

## Run initdb in debug mode

```sh
initdb -d -D /path/to/data --debug
```

`-d` (or `--debug`) sets `debug = true` in `initdb.c` and:

- Echoes the bootstrap and standalone-backend commands as they run.
- Prints `Running in debug mode.` at start.

Combine with `-n` (`--no-clean`):

```sh
initdb -d -n -D /path/to/data
```

`-n` (or `--no-clean`) leaves the partially-created data directory
in place after a failure. Without `-n`, `initdb` deletes the partial
directory on failure, taking the evidence with it.

## The two backend modes initdb spawns

From `initdb.c`:

```c
static const char *const boot_options =
    "-F -c log_checkpoints=false";
static const char *const backend_options =
    "--single -F -O -j -c search_path=pg_catalog "
    "-c exit_on_error=true -c log_checkpoints=false";
```

Decoded:

- `--boot` — bootstrap mode. The backend reads `postgres.bki` from
  `share/postgres.bki` and inserts catalog rows literally. No
  parser, no planner, no transactional semantics in the usual
  sense.
- `--single` — single-user standalone backend. No postmaster.
  Reads SQL from stdin, terminated by `^D`. Used after bootstrap
  for the parts of `template1` that need real SQL (CREATE VIEW,
  CREATE OPERATOR, etc.).
- `-F` — `fsync = off`. Initdb never fsyncs during creation; it
  fsyncs once at the end (unless `-N` / `--no-sync`).
- `-O` (single mode) — allow modifications of system catalogs.
- `-j` (single mode) — read input until `^D` instead of `;`.
- `-c search_path=pg_catalog` — bare names resolve to system
  catalogs. Required because the public schema doesn't exist yet.
- `-c exit_on_error=true` — first error aborts the backend.

## Running the bootstrap step alone

To debug a bootstrap-time crash, isolate it:

```sh
mkdir -p /tmp/pgdata-debug
cd /tmp/pgdata-debug

postgres --boot -F -D /tmp/pgdata-debug -x1 < /usr/local/share/postgresql/postgres.bki
```

The `-x1` flag (`BootstrapXlogFlag = 1` in `bootstrap.c`) tells the
boot backend it is operating on a fresh data directory. Most
bootstrap-time crashes are catalog-data inconsistencies: a `*.dat`
file that doesn't match the `*.h` it derives from.

To attach gdb:

```sh
gdb --args postgres --boot -F -D /tmp/pgdata-debug -x1
(gdb) run < /usr/local/share/postgresql/postgres.bki
```

When it crashes, `bt full` will reveal whether the failure is in
catalog parsing (`bki.c`, `bootparse.y`), heap insertion (`heap.c`),
or shared-memory setup (early in `bootstrap.c`).

## Running the standalone backend step

After bootstrap completes, initdb runs the standalone backend with a
sequence of SQL files baked into the binary plus `*.sql` from
`share/postgres/`. To replay a single one manually:

```sh
postgres --single -F -O -j -c search_path=pg_catalog \
                -c exit_on_error=true \
                -D /tmp/pgdata-debug template1 \
                < /usr/local/share/postgresql/system_views.sql
```

If a specific system view fails to create, this is the way to
reproduce.

For interactive single-mode poking:

```sh
postgres --single -D /tmp/pgdata-debug template1
```

You get a `backend>` prompt. Type SQL terminated by `^D` (not `;`).

## Common failure modes

### Locale / encoding

`initdb` validates locale support up front:

```
initdb: error: invalid locale name "xx_YY.UTF-8"
```

Resolved by:

- Verify `locale -a` lists the requested locale.
- For ICU on PG 16+, use `--locale-provider=icu --icu-locale=xx-YY`.
- The default behaviour: inherit `LANG` / `LC_*` from the calling
  shell's environment. To avoid surprises, run initdb under
  `LANG=C LC_ALL=C` for testing.

Peter Eisentraut's locale advice: use ICU on platforms where libc
collation correctness is uncertain. See
`community/voices/index.md` § "Peter Eisentraut".

### System catalog mismatch

If you modified `src/include/catalog/pg_*.h` or a `*.dat` file but
forgot to bump `CATALOG_VERSION_NO`:

```
initdb: error: input file "/usr/.../share/postgresql/postgres.bki"
does not belong to PostgreSQL <version>
```

Or the bootstrap crashes with an `Assert` in `bki.c` because the
generated `postgres.bki` shape doesn't match the `pg_*.h` the
running backend was compiled against. Fix:

```sh
cd ../master
make -C src/backend/catalog clean
make
make install            # re-installs share/postgres.bki
```

Then re-run initdb.

See `community/conventions/committing-checklist.md` § "catversion
bump".

### `template0` / `postgres` missing

If initdb crashes after creating `template1` but before copying it,
you end up with a half-built cluster. The postmaster will refuse to
start with:

```
FATAL: database "postgres" does not exist
```

Fix: `rm -rf /path/to/data` and re-run `initdb`.

### Permissions / SELinux

```
initdb: error: could not change permissions of directory "...": Operation not permitted
```

Either the target dir is on a filesystem that doesn't support
`chmod` (e.g. CIFS, some FUSE mounts), or SELinux is denying the
operation. Switch to a local ext4/xfs mount or `audit2allow` your
way out.

## `pg_bootstrap` invariants

The bootstrap backend has these invariants that an agent should
respect when modifying anything in this path:

1. **No transactions** in the usual sense. Bootstrap-mode "commits"
   are fire-and-forget tuple inserts.
2. **No system caches** are used during bootstrap; lookups go
   through `pg_class` / `pg_attribute` directly.
3. **No buffer manager replacement policy.** Bootstrap loads pages
   into shared_buffers and never evicts; `shared_buffers` must be
   sized for the entire bootstrap data set. The default config
   handles this.
4. **No autovacuum, no WAL writer, no checkpointer.** The single
   process does everything.
5. **No `Assert(...)` failures must reach release** — the
   bootstrap backend is what initdb runs against the production
   binary. A debug-only assertion that fires during bootstrap on a
   developer machine but not in CI is still a release blocker.

## Useful environment variables

- `PGOPTIONS='-c log_min_messages=DEBUG5'` — propagates to both the
  bootstrap and standalone backends initdb spawns. Fills the initdb
  output with verbose backend chatter; useful for tracing where a
  particular catalog row gets inserted.
- `LC_ALL=C` — defangs locale issues during testing.
- `PGSHAREDIR=/tmp/my-share` — overrides where initdb looks for
  `postgres.bki`, `system_views.sql`, etc. Useful when testing a
  patch against a different share dir than the one your installed
  binary normally uses.

## Inspecting the result

```sh
ls /tmp/pgdata-debug/
# base/   global/   pg_wal/   pg_xact/   pg_multixact/   ...
# pg_control   postgresql.conf   pg_hba.conf   PG_VERSION

# Verify catalog version:
pg_controldata /tmp/pgdata-debug/ | grep "Catalog version"

# Start the cluster:
pg_ctl -D /tmp/pgdata-debug -l /tmp/pgdata-debug/log start
```

`pg_controldata` is the canonical inspector for the cluster's control
file. The "Catalog version" must match `CATALOG_VERSION_NO` in the
running binary's `catversion.h`.

## When initdb succeeds but startup fails

This is usually:

- WAL path mismatch (`pg_wal` symlinked elsewhere on creation, but
  the link target gone now).
- `pg_hba.conf` rejecting your client.
- Wrong `postgres` binary (the one initdb spawned vs. the one
  `pg_ctl start` invokes — `which postgres` matters).
- Mismatched extensions: `shared_preload_libraries` references a
  module that doesn't exist in the installed `lib/` dir.

The first place to look is `pg_controldata`, then the postmaster log.

## Sources

- `src/bin/initdb/initdb.c` — the program itself, top-of-file block
  comment and the `boot_options` / `backend_options` strings.
- `src/backend/bootstrap/bootstrap.c` — the `--boot` mode entry.
- `src/backend/bootstrap/bootparse.y` — the BKI grammar.
- `src/backend/catalog/genbki.pl` — generates `postgres.bki` from
  `pg_*.h` and `*.dat` files.
- `src/backend/tcop/postgres.c` — the `--single` mode entry
  (`PostgresMain` with no postmaster).
- `src/include/catalog/catversion.h` — the version-bump location.
- Docs: <https://www.postgresql.org/docs/current/app-initdb.html>
  for the user-facing invocation.
- Docs: <https://www.postgresql.org/docs/current/app-postgres.html>
  for `--single` and `--boot` modes.
- Docs: <https://www.postgresql.org/docs/current/app-pg-controldata.html>.
- Wiki: <https://wiki.postgresql.org/wiki/BootStrapping> — the
  catalog-bootstrap design overview.
- Cross-reference: `generic/workflows/debug-backend.md` § "Reproduce
  a crash without postmaster" — the `--single` story shared with
  this workflow.
- Cross-reference: `generic/workflows/build-and-test.md` — for the
  initdb that `make check` runs internally.
- Cross-reference: `community/conventions/committing-checklist.md`
  § "catversion bump".
- Cross-reference: `community/voices/index.md` § "Peter Eisentraut"
  — locale and ICU advice.
