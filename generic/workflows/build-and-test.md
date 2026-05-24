# Workflow: Build and test PostgreSQL

How a developer builds and tests PostgreSQL locally — recommended
configure flags, autoconf vs. Meson, vpath builds, ccache, the four
test commands and what each one covers, the isolation tester, TAP
under `prove`, and DocBook conventions for documentation patches.

## TL;DR — the recommended developer build

```sh
git clone https://git.postgresql.org/git/postgresql.git
cd postgresql

# Pick ONE: autoconf or Meson. Both work; CI runs both.

# --- autoconf (vpath build to keep src/ clean) ---
mkdir ../pg-build && cd ../pg-build
../postgresql/configure \
    --prefix=$HOME/pginstall \
    --enable-debug \
    --enable-cassert \
    --enable-tap-tests \
    --enable-injection-points \
    CFLAGS='-O0 -ggdb3' \
    CC='ccache gcc'
make -s -j$(nproc) world-bin
make install-world-bin
make check-world

# --- OR Meson (preferred on macOS / faster incremental) ---
cd postgresql
meson setup build \
    --prefix=$HOME/pginstall \
    -Ddebug=true \
    -Dcassert=true \
    -Dtap_tests=enabled \
    -Dinjection_points=true
ninja -C build
meson install -C build
meson test -C build --print-errorlogs
```

`--enable-cassert` and `-Dcassert=true` are the single most
important flag — it enables all `Assert(...)` invariants. **Never do
real PostgreSQL development with cassert off.** See
`generic/workflows/debug-backend.md` § "Where assertions fire".

## Recommended configure flags, explained

| Flag (autoconf) | Flag (Meson) | Why |
|---|---|---|
| `--enable-debug` | `-Ddebug=true` | `-g` debug symbols. |
| `--enable-cassert` | `-Dcassert=true` | `Assert(...)` guards fire. |
| `--enable-tap-tests` | `-Dtap_tests=enabled` | Build TAP tests under `prove`. |
| `--enable-injection-points` | `-Dinjection_points=true` | Build `INJECTION_POINT()` machinery. |
| `--enable-nls` | `-Dnls=enabled` | Translations. Optional for development. |
| `--with-icu` | `-Dicu=enabled` | ICU collations. On most modern systems. |
| `--with-llvm` | `-Dllvm=enabled` | JIT (LLVM-based). Optional. |
| `CFLAGS='-O0 -ggdb3'` | `-Dc_args='-O0 -ggdb3'` | gdb readability. |
| `CC='ccache gcc'` | (`CC` env var) | Speeds up rebuilds 5-10×. |

**Do not** use `--enable-cassert` for benchmarking. The asserts
slow operations 2–10× in some hot paths. See
`generic/workflows/perf-testing.md`.

## vpath builds (autoconf)

Build *outside* the source tree to keep `src/` clean and to support
multiple build configs side-by-side:

```sh
mkdir ~/pg-builds/master-debug
cd ~/pg-builds/master-debug
~/ws/postgres/configure --enable-debug --enable-cassert ...
make -s -j$(nproc)
```

`make` works because `configure` writes `Makefile`s in the build
directory that reference `vpath` rules pointing back at the source.

For Meson, vpath is the default (`meson setup build` *requires* an
out-of-tree build directory).

## Make targets, the full set

| Target | What it does |
|---|---|
| `make` (no target) | Build server, client, contrib. Equivalent to `world-bin` in modern trees. |
| `make world-bin` | Build server, client, contrib, but not docs. |
| `make world` | `world-bin` + docs. Slow. |
| `make install` | Install server, client. |
| `make install-world` | Install everything including docs. |
| `make install-world-bin` | Like above, no docs. |
| `make clean` | Remove build artifacts in current dir. |
| `make distclean` | Like clean, but also remove configure-generated files. |
| `make check` | Server regression tests, in a temp instance. |
| `make installcheck` | Server regression tests, against a running cluster you already started. |
| `make check-world` | `check` + every TAP suite + every contrib test + isolation tests. |
| `make check-isolation` | Just the isolation tester suite. |
| `make headerscheck` | Each installed `*.h` compiles standalone. |
| `make cpluspluscheck` | Each installed `*.h` compiles under `c++`. |
| `make docs` | Build the SGML documentation (HTML + man pages). |
| `make html` | HTML docs only. |

For Meson:

```sh
ninja -C build                  # everything
ninja -C build install
meson test -C build             # all tests
meson test -C build pg_regress  # specific suite
meson test -C build --suite contrib
meson test -C build --print-errorlogs    # show failures verbosely
meson test -C build -C build --setup running   # against running server
```

## `make check` vs. `make check-world` vs. `make installcheck`

- **`make check`** — *the most common dev-loop command*. Spins up a
  temp data directory and `postgres` instance using whatever `initdb`
  was just built; runs `src/test/regress/` against it; tears down.
  Fast (~1-2 min on a modern dev box).
- **`make installcheck`** — assumes you have a running server (e.g.
  one you started with `pg_ctl`). Runs the same regression suite
  against it. Useful for verifying that an installed package matches
  expected behaviour, but **collisions** with other `installcheck`
  runs are a hazard (see `community/conventions/committing-checklist.md`
  § "regress_ prefix").
- **`make check-world`** — the gold standard before posting a patch.
  Includes:
  - `src/test/regress/` (core regression).
  - `src/test/isolation/` (isolation tester).
  - `src/test/{recovery,subscription,authentication,ldap,ssl,kerberos,modules}/`
    (TAP suites).
  - `contrib/*` (each contrib's own regression / TAP / isolation).
  - `src/bin/*/` (TAP for `pg_dump`, `pg_basebackup`, `psql`, etc.).
  - `src/pl/*/` (the four procedural languages' tests).

  Slow (~10-30 min on a fast box, much longer on slow ARM animals).

## Isolation tester

`make check-isolation` runs `src/test/isolation/` — the project's
multi-session race-condition test harness.

Each test is a `*.spec` file that declares N sessions, defines steps
each session can take, and a sequence (or sequences) of step
interleavings. The isolation tester orchestrates them and checks the
output against an expected file.

```
src/test/isolation/specs/two-ids.spec       # spec file
src/test/isolation/expected/two-ids.out     # expected output
```

To run a single isolation test:

```sh
cd src/test/isolation
./pg_isolation_regress --temp-instance=/tmp/iso-tmp two-ids
```

When debugging an isolation test:

- Add `step "..." { LOG_STATEMENT }` to surface the SQL backend-side.
- Use `injection_points` for race conditions that can't be triggered
  by purely-SQL ordering. See `community/voices/michael-paquier.md`
  § "TAP test discipline".

## TAP under `prove`

TAP (Test Anything Protocol) tests live in `*.pl` files under
`src/test/*/t/` and `contrib/*/t/`. Each `*.pl` is a Perl program
using `PostgreSQL::Test::Cluster` and `Test::More`.

```sh
cd src/test/recovery
make check                     # runs all t/*.pl
PROVE_FLAGS="-v" make check    # verbose
PROVE_TESTS=t/001_stream_rep.pl make check
                               # just one test
```

To debug a TAP test:

- `PROVE_FLAGS="-v"` shows each `ok`/`not ok` line.
- The test cluster's data directory survives in `tmp_check/` (under
  the test directory) on failure; re-run with no `make clean` to
  inspect the logs there.
- `PG_TEST_NOCLEAN=1` in the environment keeps `tmp_check/` even on
  success.

The TAP infrastructure is in
`src/test/perl/PostgreSQL/Test/Cluster.pm`,
`src/test/perl/PostgreSQL/Test/Utils.pm`. Read these before writing
a new TAP test; they have helpers (`poll_query_until`,
`wait_for_log`, `safe_psql`, etc.) you should be using rather than
re-implementing.

## ccache

Drop-in compiler wrapper that caches object files keyed on
preprocessed source. PostgreSQL has a lot of TUs and a lot of
incremental builds; ccache typically gives 5–10× speedup on a
re-build after `git rebase` or `git checkout`.

```sh
sudo apt install ccache       # or: brew install ccache, dnf install ccache
ccache --max-size=10G         # or whatever fits
export CC='ccache gcc'        # set in your shell's rc
```

Then re-run `configure` so the project picks it up:

```sh
./configure CC='ccache gcc' ...
```

For Meson:

```sh
CC='ccache gcc' meson setup build ...
```

`ccache -s` shows the hit rate. >70% is healthy on a working
developer's machine.

## Documentation patches: DocBook conventions

The project's docs are DocBook XML in `doc/src/sgml/`. To build:

```sh
make docs                  # autoconf
ninja -C build doc/postgres-A4.pdf      # Meson, also html, man
```

Conventions:

- **Tag style**: `<filename>foo</filename>`, `<varname>bar</varname>`,
  `<command>VACUUM</command>`, `<literal>NULL</literal>`. Check
  existing docs for the right tag for the kind of thing you are
  citing. Don't use `<emphasis>` for emphasis — use the semantic tag.
- **Wrap at 78 columns** in SGML source.
- **One sentence per line** in many existing files (improves diff
  readability). Match the convention of the file you are editing.
- **Section IDs** (`<sect1 id="foo">`) are URL anchors; do not change
  one without checking incoming links.
- **`make docs` must succeed** with no warnings before posting.
- **Build with `--with-docs` (`-Ddocs=enabled`)** to enable the targets;
  recent trees may build them by default.

Peter Eisentraut owns most of the docs toolchain; see
`community/voices/index.md` § "Peter Eisentraut".

## Building only docs

```sh
make -C doc/src/sgml html        # autoconf
ninja -C build doc/postgres.html # Meson
```

Outputs to `doc/src/sgml/html/` (autoconf) or `build/doc/` (Meson).
Open `index.html` in a browser to verify rendering.

## Common build failures and their causes

| Symptom | Likely cause |
|---|---|
| `error: postgres.bki not found` | Missing `make install` before `make check`. |
| `Catalog version mismatch` | Forgot to bump `CATALOG_VERSION_NO` after editing `pg_*.h` / `*.dat`. |
| Random TAP test timeout | Test depends on timing; use injection points. |
| `make check` passes, `make installcheck` fails | Test relies on temp-instance config not in your running cluster. |
| Meson and autoconf produce different output | Build-system parity bug; see `community/voices/michael-paquier.md`. |
| `headerscheck` fails on a new header | Missing `#include` for a type the new header uses. |

## Sources

- Docs: <https://www.postgresql.org/docs/current/install-make.html>
  for the autoconf build flow.
- Docs: <https://www.postgresql.org/docs/current/install-meson.html>
  for the Meson build flow.
- Docs: <https://www.postgresql.org/docs/current/regress.html> for
  `make check`, `installcheck`, regression test architecture.
- Docs: <https://www.postgresql.org/docs/current/regress-tap.html>
  for the TAP harness.
- Docs: <https://www.postgresql.org/docs/current/regress-isolation.html>
  for the isolation tester (also `src/test/isolation/README`).
- `src/test/perl/PostgreSQL/Test/Cluster.pm`,
  `src/test/perl/PostgreSQL/Test/Utils.pm` — TAP helpers.
- `meson_options.txt`, `configure.ac` — build flags.
- Wiki: <https://wiki.postgresql.org/wiki/Compile_and_Install_from_source_code>.
- Wiki: <https://wiki.postgresql.org/wiki/Documentation_Tools>.
- Cross-reference: `generic/workflows/debug-backend.md` for
  `--enable-cassert` and `--enable-injection-points` rationale.
- Cross-reference: `generic/workflows/perf-testing.md` for the
  *no-cassert* perf-build that is *not* this build.
- Cross-reference: `community/conventions/committing-checklist.md`
  § "make check-world under both build systems",
  § "headerscheck", § "regress_ prefix on roles".
- Cross-reference: `community/voices/michael-paquier.md` § "Build
  system" for Meson + autoconf parity.
- Cross-reference: `community/voices/index.md` § "Peter Eisentraut"
  for ICU, locale, docs toolchain.
