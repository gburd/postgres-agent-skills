# Committing checklist

The full pre-commit checklist a PostgreSQL committer runs before
pushing a patch to `master` or a back-branch. Distilled from Álvaro
Herrera's wiki page <https://wiki.postgresql.org/wiki/Committing_checklist>.
**The agent does not commit to upstream — only committers do — but the
agent should run this checklist on every patch they propose, because a
committer's first act on accepting a patch is to run it.** Failing the
checklist after a committer has invested time is the cheapest way to
exhaust their patience.

## TL;DR — the committer's mental loop

```
0. Build clean (master, no local cruft)
1. Apply the patch with `git am`; check no conflicts
2. Read the diff in full
3. Run pgindent and re-diff
4. make check-world (Meson and autoconf both)
5. Special builds: cassert, valgrind, CLOBBER_CACHE_ALWAYS,
   wal_consistency_checking, headerscheck, ABI checks on back-branches
6. Bump catversion if needed (master only)
7. Sync postgresql.conf.sample if a GUC changed
8. Verify trailers: Author / Reviewed-by / Discussion / Backpatch-through
9. Commit
10. Watch the buildfarm
```

What the agent should do: run steps 1–9 on their own patch *before
posting*. Step 10 is committer-only.

## 1. Apply the patch cleanly

```sh
git checkout master
git pull --ff-only origin master
git am < proposed.patch          # for series, `git am v3-*.patch`
```

`git am` rejects whitespace-broken patches by default if `apply.whitespace
= error` is set (which it should be — see
`community/conventions/git-workflow.md`). If `git am` fails, the patch
needs the author to clean up and resend.

## 2. Read the diff

```sh
git -P log -p origin/master..HEAD
```

Eyeball every hunk for:

- Unrelated reformats / "while-I-was-here" changes
  (`community/voices/tom-lane.md` § "Don't reformat unrelated code").
- Author/date attribution in comments
  (`community/conventions/code-comments.md` § "What never goes in
  comments").
- Editor-debris (printf debugging, commented-out code, BOM).
- Missing doc updates.

## 3. Run pgindent

```sh
src/tools/pgindent/pgindent --commit origin/master..HEAD
git diff
```

If `pgindent` produces a non-empty diff that touches lines outside
the patch, the patch is missing a `typedefs.list` entry. Hold the
patch; ask the author to fix. See `community/conventions/pgindent.md`
§ "The typedefs.list problem".

## 4. `make check-world` under both build systems

The full regression / TAP / isolation / contrib suite. Run twice —
once under autoconf, once under Meson — because parity is required:

```sh
# autoconf
./configure --enable-debug --enable-cassert --enable-tap-tests \
            --enable-injection-points
make -s -j$(nproc)
make -s -j$(nproc) check-world

# Meson
meson setup build-meson \
      -Dcassert=true -Dtap_tests=enabled -Dinjection_points=true
ninja -C build-meson
meson test -C build-meson --print-errorlogs
```

If the patch touches build-system files, this is the audit step
Michael Paquier insists on (`community/voices/michael-paquier.md` §
"Build system: Meson and autoconf parity"). If it touches anything
else, do it anyway — parity drift is how flakes start.

`make check-world` includes:

- `make check` — core regression tests.
- `make check-isolation` — isolation tester.
- `make check` in every `src/test/{recovery,subscription,...}/`.
- `make check` in every `contrib/*` module.
- `make installcheck` is *not* run by `check-world`; it is the
  separate "test against an existing installation" path.

## 5. Special builds and slow checks

These are not run on every commit, but a committer runs them on
"big" or "scary" patches. The agent should run them when the patch
touches:

| Touch this | Run this |
|---|---|
| Memory contexts, allocators, palloc | `--enable-cassert` + `valgrind` (`src/test/regress/Makefile` has `valgrind` target). |
| Catalog cache lookups | `-DCLOBBER_CACHE_ALWAYS` build, then `make check`. |
| WAL records, redo functions | `wal_consistency_checking = all` GUC during regression. |
| Relation lifecycle, locks | `make check-isolation` plus `wal_consistency_checking`. |
| Public headers (`*.h` in installed paths) | `make headerscheck` (verifies headers compile standalone). |
| Public function signatures | ABI check on back-branches (see step 8). |

```sh
# CLOBBER_CACHE_ALWAYS rebuild
./configure --enable-debug --enable-cassert \
            CFLAGS="-DCLOBBER_CACHE_ALWAYS -O0"
make -s -j$(nproc) && make -s check

# valgrind
make USE_VALGRIND=1 check     # via src/tools/valgrind.supp suppressions

# wal_consistency_checking
PG_TEST_INITDB_EXTRA_OPTS=     \
PGOPTIONS='-c wal_consistency_checking=all' \
make check
```

These take 5–60× longer than baseline `make check`. Plan accordingly.

## 6. catversion bump (master only)

If the patch:

- Adds, removes, or modifies a system catalog table, view, or column
  (`src/include/catalog/pg_*.h` or `*.dat`).
- Changes the on-disk format of any catalog tuple.
- Changes the WAL record format (also requires `XLOG_PAGE_MAGIC`
  bump in some cases).
- Changes the in-memory layout of any persistent struct.

then `CATALOG_VERSION_NO` in `src/include/catalog/catversion.h` must
be bumped to today's date in `YYYYMMDDN` form.

```c
/* src/include/catalog/catversion.h */
#define CATALOG_VERSION_NO   202605240
```

The bump goes in the *same commit* as the catalog change. **Never on
back-branches** — back-branches must remain on-disk-compatible with
their initial release. See `community/voices/michael-paquier.md` §
"Back-patching mechanics".

## 7. postgresql.conf.sample sync

If the patch adds, removes, or renames a GUC (`DefineCustomXxxVariable`
or an entry in `src/backend/utils/misc/guc_tables.c`), then
`src/backend/utils/misc/postgresql.conf.sample` must be updated to
match. The sample file is what `initdb` installs; users diff against
it.

The wiki's committing checklist explicitly calls out the sync as a
common miss.

## 8. ABI checks on back-branches

Back-branches enforce ABI compatibility. Forbidden in a back-patched
commit:

- Adding a new field to a struct exposed in an installed header.
- Changing a function signature exposed in an installed header.
- Removing or renaming an exported symbol.
- Changing the size or alignment of any installed struct.

Tools:

```sh
# generate the ABI snapshot of the installed shared libraries
abidw <path/to/libpq.so.5>     # libabigail
# or use the project's own ABI-tracking buildfarm output
```

If the back-patch *requires* an ABI change, the change is illegal —
implement the fix without changing ABI, or do not back-patch.

## 9. Verify the trailers

The commit message must contain at minimum:

```
Author: <name> <email>           # if not the committer
Discussion: https://postgr.es/m/<id>
```

And, for back-patches:

```
Backpatch-through: <branch>
```

Trailers in their canonical order (per
`community/conventions/commit-message-format.md`):

```
Author:
Co-authored-by:
Reported-by:
Reviewed-by:
Tested-by:
Suggested-by:
Discussion:
Backpatch-through:
```

Specific traps:

- A `Reviewed-by:` line is reserved for *substantive* reviewers, not
  "+1" replies. The committer audits the thread to determine who
  qualifies.
- `Discussion:` URL must be the canonical thread, not a follow-up
  bug-report.
- `Backpatch-through:` should be the *oldest* branch that gets the
  fix.

## 10. Special checks for specific subsystems

### `regress_` prefix on roles

Any role / user / mapping created by a regression test must have a
name starting with `regress_`:

```sql
CREATE ROLE regress_alice;
CREATE ROLE regress_bob LOGIN;
```

Bare names (`alice`, `test_role`, `myuser`) collide with users on a
shared installation that runs `make installcheck` and produce
spurious failures. The regression harness checks the prefix.

### `headerscheck`

```sh
make -s headerscheck
make -s cpluspluscheck
```

Verifies that every installed `*.h` file (a) compiles standalone
under `cc`, and (b) compiles standalone under `c++`. A new header
that depends on a previous `#include` you forgot to declare will
fail one of these.

### Doc patches

If the patch is user-visible, `doc/src/sgml/*.sgml` is updated in the
same commit. `make docs` builds the SGML; `make html` produces HTML
to inspect. See `generic/workflows/build-and-test.md` § "Docs".

### Translations

The `.po` files under `src/backend/po/` and similar are updated by
the translators, not by feature authors. A patch that adds a new
user-facing message (`ereport`, `errmsg`, `psql` strings) need only
extract the new strings via `make update-po`; do not commit the
re-translated `.po` files.

## After commit (committer-only)

The committer pushes, then watches the buildfarm at
<https://buildfarm.postgresql.org/cgi-bin/show_status.pl> for the
next 24 hours. Common red animals on a fresh commit:

- Slow ARM animals — race conditions.
- 32-bit animals — pointer-sized assumptions, format-string `%lu` on
  `Size`.
- AIX, Solaris, NetBSD — unusual libc / locale behaviour.
- BSD make animals — Makefile assumptions about GNU make features.

If an animal goes red, the committer reverts or hot-fixes within
hours. The agent's job ends at "patch posted"; revert / hot-fix is
committer responsibility.

## Sources

- Wiki: <https://wiki.postgresql.org/wiki/Committing_checklist>
  (curated by Álvaro Herrera and others). The canonical document
  this skill condenses.
- Wiki: <https://wiki.postgresql.org/wiki/ABI_Policy>.
- Wiki: <https://wiki.postgresql.org/wiki/Submitting_a_Patch>
  § "What gets posted to hackers".
- `src/include/catalog/catversion.h` — the bump location.
- `src/backend/utils/misc/postgresql.conf.sample` — GUC sample sync.
- `src/test/regress/sql/regression.dat` and the regression harness'
  role-prefix check.
- `Makefile.global.in` and `meson.build` for `headerscheck`,
  `cpluspluscheck`, `check-isolation`, `check-world` targets.
- `src/tools/valgrind.supp` for valgrind suppressions used in the
  USE_VALGRIND=1 build.
- Buildfarm: <https://buildfarm.postgresql.org/cgi-bin/show_status.pl>.
- Cross-reference: `community/conventions/pgindent.md`.
- Cross-reference: `community/conventions/commit-message-format.md`.
- Cross-reference: `community/conventions/whitespace-and-encoding.md`.
- Cross-reference: `community/conventions/code-comments.md`.
- Cross-reference: `community/conventions/git-workflow.md`.
- Cross-reference: `community/conventions/creating-clean-patches.md`.
- Cross-reference: `community/voices/michael-paquier.md` § "Back-
  patching mechanics" and § "Build system".
- Cross-reference: `community/voices/tom-lane.md` § "Don't reformat
  unrelated code", § "Don't paper over the symptom".
- Cross-reference: `generic/workflows/build-and-test.md`.
- Cross-reference: `generic/workflows/submit-patch.md`.
