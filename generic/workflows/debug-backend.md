# Workflow: Debug a backend

How to attach a debugger, reproduce a crash, raise log verbosity, and
introspect a live PostgreSQL backend. Covers the standard debugging
modes the project uses internally — `gdb -p`, `postgres --single`,
elevated `log_min_messages`, `pg_stat_activity` introspection, and
where assertions actually fire.

## TL;DR — what the agent does

```sql
-- in psql
SELECT pg_backend_pid();
```

Then in another terminal:

```sh
sudo gdb -p <PID>
(gdb) handle SIGUSR1 nostop noprint    # skip postgres signalling noise
(gdb) handle SIGUSR2 nostop noprint
(gdb) continue
```

For a crashing backend that won't survive long enough to attach,
build with `--enable-cassert --enable-debug` and run under
`postgres --single` to bypass the postmaster.

## Debug build prerequisites

```sh
./configure --enable-debug --enable-cassert --enable-tap-tests \
            --enable-injection-points CFLAGS='-O0 -ggdb3'
make -s -j$(nproc) && make install
```

Or under Meson:

```sh
meson setup build -Ddebug=true -Dcassert=true -Dtap_tests=enabled \
                  -Dinjection_points=true \
                  -Dc_args='-O0 -ggdb3'
ninja -C build && meson install -C build
```

`--enable-cassert` enables `Assert(...)` calls — most of the project's
defensive invariants are guarded by `Assert`, not `if (...) elog`.
Without cassert, you debug a different binary than the one that
catches bugs.

`-O0` keeps locals readable in `gdb`; `-ggdb3` includes macros so
`p MAKE_VARLENA1B(x)` etc. expands.

`--enable-injection-points` enables the in-tree fault-injection
mechanism (`src/test/modules/injection_points`); essential for
reproducing race conditions.

## Attach to a running backend

The standard pattern, assuming `psql` connects to the backend you
want to debug:

```sql
-- in your psql session
SELECT pg_backend_pid();
 pg_backend_pid
----------------
          12345
```

```sh
# in another terminal (root or postgres user)
gdb -p 12345
```

Useful gdb-init for postgres:

```
# ~/.gdbinit  (or ~/.config/gdb/gdbinit)
set print pretty on
set print elements 0
set pagination off
set history save on
handle SIGUSR1 nostop noprint
handle SIGUSR2 nostop noprint
handle SIGPIPE nostop noprint
```

Common commands once attached:

```
(gdb) bt full                       # current stack with locals
(gdb) thread apply all bt           # all threads (rare in PG)
(gdb) p *MyProc                     # current PGPROC
(gdb) p *CurrentMemoryContext       # active memory context
(gdb) p *ActiveSnapshot             # current snapshot
(gdb) p debug_query_string          # the SQL the backend is running
(gdb) call MemoryContextStats(TopMemoryContext)
                                    # dumps to stderr (i.e. server log)
```

`MemoryContextStats` is the project's canonical "what allocated all
this memory" introspection; it walks the context tree and prints
sizes. Output goes to stderr, which is the postmaster's log.

## Reproduce a crash without postmaster

`postgres --single` runs a single backend in your terminal, no
postmaster, no client protocol. Useful for:

- Debugging early startup / bootstrap-time issues.
- Crashing assertions where postmaster auto-restart hides the core.
- Testing recovery code paths where `gdb` on a forked backend is
  awkward.

```sh
# Stop any running cluster first
pg_ctl -D /path/to/data stop

# Run a single backend in template1
postgres --single -D /path/to/data template1 < /dev/null
```

You get a `backend>` prompt instead of `psql`. Type SQL terminated
by `;` and `^D`. Crash → core dump in `/path/to/data/`, no auto-
restart. To attach `gdb` from start:

```sh
gdb --args postgres --single -D /path/to/data template1
(gdb) run
```

For bootstrap-mode debugging (system catalogs):

```sh
postgres --boot -x1 -D /path/to/data
```

See `generic/workflows/debug-initdb.md` for the bootstrap-specific
flow.

## Raise log verbosity

Without restarting the cluster:

```sql
SET log_min_messages = 'DEBUG5';     -- session, lots of noise
SET client_min_messages = 'DEBUG5';  -- shows DEBUG output to psql
SET log_statement = 'all';           -- log every statement
SET log_min_duration_statement = 0;  -- log every statement's duration
SET log_lock_waits = on;             -- log lock waits >deadlock_timeout
SET log_temp_files = 0;              -- log every temp file
SET log_error_verbosity = 'verbose'; -- include funcname:linenumber
```

`DEBUG5` is the noisiest level. `DEBUG1` is the typical "I want
context" level for a focused investigation.

For server-wide:

```sql
ALTER SYSTEM SET log_min_messages = 'DEBUG1';
SELECT pg_reload_conf();
```

`pg_reload_conf()` does a SIGHUP to the postmaster, which re-reads
`postgresql.conf`. It works for SIGHUP-able GUCs (most of the
`log_*` family). Restart-required GUCs (`shared_buffers`,
`max_connections`) won't pick up.

## `pg_stat_activity` introspection

The most useful single view. Scoping to "backends doing something
right now":

```sql
SELECT pid, usename, application_name, state,
       wait_event_type, wait_event, query_id,
       LEFT(query, 80) AS query
FROM pg_stat_activity
WHERE state IS NOT NULL
  AND pid <> pg_backend_pid()
ORDER BY xact_start NULLS LAST;
```

`wait_event_type` and `wait_event` are the answer to "why is this
backend stuck?" The full set of wait events is documented at
<https://www.postgresql.org/docs/current/monitoring-stats.html#WAIT-EVENT-TABLE>.

For deeper introspection:

- `pg_stat_progress_*` views — vacuum, copy, basebackup,
  cluster, create-index, analyze each have a progress view.
- `pg_locks` joined with `pg_stat_activity` shows who holds /
  waits for what.
- `pg_stat_statements` (extension) — historical query data.
- `pg_buffercache` (extension) — what is in shared_buffers right now.

## Where assertions fire

`Assert(condition)` macros are spread throughout the source. A failing
assert calls `ExceptionalCondition` in `src/backend/utils/error/assert.c`,
which logs `TRAP: failed Assertion ...` and aborts the backend.

To find the most likely sites for a hang or wrongness in a subsystem:

```sh
git -P grep -n 'Assert(' src/backend/<subsystem>/ | wc -l
git -P grep -n 'Assert(' src/backend/storage/buffer/
```

`Assert` only runs in `--enable-cassert` builds (`USE_ASSERT_CHECKING`
in `c.h`). Production builds pass through silently. This means:

- A bug that triggers `Assert` in dev but not prod is still a real
  bug.
- The first agent action on a "works in prod, crashes locally" report
  is to confirm both sides built with the same `--enable-cassert`.

`elog(ERROR, ...)` and `ereport(ERROR, ...)` always fire; they are
not assertions. They roll back the current transaction and log.
Distinguish carefully: an `Assert` indicates "a project invariant was
violated, this is our bug"; an `ereport(ERROR)` indicates "a
condition we expected to be possible occurred, here is the message
to the user".

## `elog(LOG, ...)` for ad-hoc tracing

When `gdb` is too heavy and `DEBUG5` is too noisy, sprinkle
`elog(LOG, "in foo, x = %d", x);` into the path. `LOG` always fires
to the server log (above `log_min_messages`'s normal range — `LOG` >
`NOTICE` per `elog.h`). Remove before posting the patch — see
`community/conventions/creating-clean-patches.md` § "What 'clean'
means line-by-line".

## Core dumps

```sh
ulimit -c unlimited
echo '/tmp/core.%e.%p' | sudo tee /proc/sys/kernel/core_pattern
# trigger crash
gdb /path/to/postgres /tmp/core.postgres.12345
(gdb) bt full
```

The postmaster sets `coredump_filter` per child. If you get a 0-byte
core, your filesystem may not allow it (some Linux distros), or
`systemd-coredump` ate it (`coredumpctl list`).

## Injection points

For race-condition reproduction:

```c
/* in C source */
#include "utils/injection_point.h"
INJECTION_POINT("my-test-point");
```

```sql
-- from psql, in a test session
SELECT injection_points_attach('my-test-point', 'wait');
```

When the backend hits the named point, it blocks until you call
`injection_points_wakeup('my-test-point')`. The injection-point
test module is in `src/test/modules/injection_points/` (build it
with `--enable-injection-points`).

This is what Michael Paquier insists on instead of timing-based
TAP test synchronisation; see `community/voices/michael-paquier.md`
§ "TAP test discipline".

## When to step away from gdb

`gdb` is the wrong tool for:

- Performance investigation — use `perf`. See
  `generic/workflows/perf-testing.md`.
- Race conditions in production — use injection points + TAP tests.
- "Slow query" — `EXPLAIN (ANALYZE, BUFFERS, IO)`,
  `auto_explain`, `pg_stat_statements`.
- Memory-context bloat — `MemoryContextStats(TopMemoryContext)` from
  inside the running backend (callable from gdb or from C with
  `#include "utils/memutils.h"`).

## Sources

- Docs: <https://www.postgresql.org/docs/current/server-start.html>
  for `postgres --single` and `--boot` modes.
- Docs: <https://www.postgresql.org/docs/current/runtime-config-logging.html>
  for `log_min_messages`, `log_error_verbosity`, etc.
- Docs: <https://www.postgresql.org/docs/current/monitoring-stats.html>
  for `pg_stat_activity`, wait events, progress views.
- Docs: <https://www.postgresql.org/docs/current/regress-coverage.html>
  and <https://www.postgresql.org/docs/current/regress-evaluation.html>
  for cassert builds and how the regression suite uses them.
- `src/backend/utils/error/assert.c` — `ExceptionalCondition`
  implementation.
- `src/backend/utils/error/elog.c` — log levels and `ereport` shape.
- `src/include/utils/injection_point.h` and
  `src/test/modules/injection_points/` for the injection-point API.
- `src/include/utils/memutils.h`, `src/backend/utils/mmgr/mcxt.c` —
  `MemoryContextStats`.
- Wiki: <https://wiki.postgresql.org/wiki/Developer_FAQ> § "Debugging".
- Wiki: <https://wiki.postgresql.org/wiki/Getting_a_stack_trace_of_a_running_PostgreSQL_backend_on_Linux/BSD>.
- Cross-reference: `generic/workflows/debug-initdb.md` for bootstrap-
  mode debugging.
- Cross-reference: `generic/workflows/build-and-test.md` for the
  `--enable-cassert --enable-injection-points` configure flags.
- Cross-reference: `generic/workflows/perf-testing.md` for
  performance work where gdb is the wrong tool.
- Cross-reference: `community/voices/michael-paquier.md` § "TAP test
  discipline" for injection points as the synchronisation primitive.
