# pgindent — running PostgreSQL's C formatter without breaking your patch

`pgindent` is the wrapper script (Perl) around `pg_bsd_indent` that enforces
PostgreSQL's uniform C layout. Every commit that touches `*.c` or `*.h` is
expected to be pgindent-clean. This is enforced socially, not by CI: a
committer running pgindent on your patch and seeing it produce a diff is a
review red flag.

## TL;DR — what the agent must do

Before sending any C patch:

```sh
src/tools/pgindent/pgindent <files-you-changed>
git diff --check                    # no whitespace errors
git diff <files-you-changed>        # eyeball the formatting changes
```

If `pgindent` reformats lines you did not touch, **that is the bug** — your
new typedef is probably missing from `src/tools/pgindent/typedefs.list`. Add
it, re-run, and the spurious diff disappears.

## Prerequisites

`pgindent` requires:

1. `pg_bsd_indent` on `$PATH`. Source: `src/tools/pg_bsd_indent/`. The current
   pinned version is `INDENT_VERSION = "2.1.2"` (declared at the top of the
   `pgindent` script). `pg_bsd_indent` will refuse to run if its reported
   version does not match.
2. `perltidy` for the optional `pgperltidy` companion. **Version 20230309
   exactly** — older and newer releases make different formatting choices,
   and the project tracks one specific release. Install via:

   ```sh
   cpan SHANCOCK/Perl-Tidy-20230309.tar.gz
   # or
   cpanm https://cpan.metacpan.org/authors/id/S/SH/SHANCOCK/Perl-Tidy-20230309.tar.gz
   ```

The standard indent options live in the script, not a config file:

```
-bad -bap -bbb -bc -bl -cli1 -cp33 -cdb -nce -d0 -di12 -nfc1 -i4
-l79 -lp -lpl -nip -npro -sac -tpg -ts4
```

Tab width is 4 (`-i4 -ts4`), target line length 79 (`-l79`). Do not override.

## Three modes you actually use

### 1. Format only your changed files (normal patch workflow)

```sh
# files you touched
src/tools/pgindent/pgindent path/to/foo.c path/to/foo.h

# everything modified vs. master, scoped by commit range
src/tools/pgindent/pgindent --commit master..

# whole tree (only do this for a release-cycle reformat run)
src/tools/pgindent/pgindent .
```

`--commit <range>` is the most useful flag: it only touches files modified
in the named range, so you cannot accidentally re-flow files outside your
patch.

### 2. Check-mode (pre-commit hook, CI)

```sh
src/tools/pgindent/pgindent --check <files>
```

Exit codes (from the script header):

- `0` — all clean
- `1` — error invoking pgindent, nothing done
- `2` — `--check` mode and at least one file requires changes
- `3` — `pg_bsd_indent` failed on at least one file

### 3. Diff-mode (preview the reformat without writing)

```sh
src/tools/pgindent/pgindent --diff <files>
```

Prints the unified diff `pgindent` *would* apply. Use to triage whether the
script wants to touch lines outside your patch.

## The typedefs.list problem

`pg_bsd_indent` is not a real C parser — it cannot tell a typedef name from a
variable name. To format `MyType *p` correctly (no space around `*`) it needs
to be told that `MyType` is a typedef. This is the job of
`src/tools/pgindent/typedefs.list` (≈4350 names as of mid-2025).

Rule: **every new public typedef you add belongs in `typedefs.list`**, in the
same patch that introduces the typedef. If you forget:

- `pgindent` will mangle declarations and uses of your new type.
- It will also mangle pre-existing typedefs that happen to alphabetically
  neighbour your name in some lookup path.
- The diff suddenly contains "ugly whitespace changes around typedefs your
  commit adds" — the README's exact phrasing.

To rebuild the canonical list from the buildfarm (do this once per release
cycle, not per patch):

```sh
wget -O src/tools/pgindent/typedefs.list \
    https://buildfarm.postgresql.org/cgi-bin/typedefs.pl
```

The buildfarm extracts typedefs from compiled object files across every
animal, so it is authoritative. Per-back-branch versions:
`https://buildfarm.postgresql.org/cgi-bin/typedefs.pl?show_list`.

## Files pgindent does not touch

`src/tools/pgindent/exclude_file_patterns` lists what `pgindent` skips —
inline assembly, atomics, C++ headers, and a few generated files. Notable:

```
src/include/storage/s_lock\.h$
src/include/port/atomics/
src/include/jit/llvmjit\.h$            # C++ constructs
src/include/jit/SectionMemoryManager\.h$
```

Generated files derived from `*.y` / `*.l` are excluded **but the `*.y` and
`*.l` sources themselves are also excluded** — flex/bison input is not
pgindented (its formatting is the parser-generator's job).

`ecpg`'s headers are *not* excluded; some get copied verbatim into ecpg
output, so a pgindent run can break the ecpg regression tests. The README
explicitly warns about this and tells you to update ecpg's expected files.

## Pre-commit hook

The community-recommended hook is in the wiki page "Working with Git". A
minimal version that only re-indents staged-and-changed C files:

```sh
#!/bin/sh
# .git/hooks/pre-commit
files=$(git diff --cached --name-only --diff-filter=ACM | \
        grep -E '\.[ch]$' || true)
[ -z "$files" ] && exit 0
src/tools/pgindent/pgindent --check $files
```

`exit 1` (via the `--check` non-zero exit) blocks the commit. Authors who
prefer auto-fixing run without `--check` and then `git add` the result.

## Comment-block protection

`pgindent` will reflow any comment block that is not at the left margin. If
you have a hand-formatted ASCII-art table, an aligned column comment, or a
deliberately wrapped paragraph, fence it:

```c
/*----------
 * Text here will not be touched by pgindent.
 * This includes deliberate         column
 * alignment and ASCII art.
 *----------
 */
```

The `----------` after `/*` and before `*/` is the marker. Every other
comment style is fair game for reformatting.

## Function-vs-typedef name collision

`pgindent` mangles both the declaration and the definition of any C function
whose name matches a typedef. (The script cannot tell which is which.) The
README is blunt: "the best workaround is to choose non-conflicting names."
If you inherit a collision and cannot rename, fence the function in
`exclude_file_patterns` rather than fight the formatter.

## #if-mismatched-braces footgun

If a function has `#if`/`#else` arms whose brace counts differ
(syntactically valid for the compiler, since only one arm is taken), the
indentation engine gets confused and produces nonsense. The README's advice
mirrors the human reviewer's advice: "rearrange the `#if` tests to avoid
it" — the unindented output is also unreadable to humans.

## Release-cycle reformat (committers only, but agent should recognise the pattern)

Once per release cycle, a committer runs:

1. Fetch fresh `typedefs.list` from buildfarm (above).
2. `src/tools/pgindent/pgindent .` (whole tree).
3. `src/tools/pgindent/pgperltidy .` (Perl files).
4. `cd src/include/catalog && make reformat-dat-files`.
5. Single commit "Run pgindent." (or "Run pgperltidy", etc).
6. Append the resulting commit hash to `.git-blame-ignore-revs` so
   `git blame --ignore-revs-file=.git-blame-ignore-revs` skips the bulk
   reformat.

Recent examples on `master`:

- `1d1612aec76` (2025-07-29) "Run pgindent." — typical post-feature-freeze sweep.
- `b27644bade0` "Sync typedefs.list with the buildfarm." — the precursor commit.
- `7e9c216b523` "Re-pgindent nbtpreprocesskeys.c after commit 796962922e." —
  spot-fix when a feature commit went in slightly mis-indented and the fix
  is its own commit.

A non-committer should never push a "Run pgindent" sweep commit to
-hackers; that is committer prerogative tied to the `git-blame-ignore-revs`
mechanic.

## Cleanup after a failed run

`pgindent` leaves `*.BAK` files in place when something goes wrong;
`pgperltidy` leaves `*.LOG` files. Always run `git status` after pgindent —
the README says "there shouldn't be any newly-created files." If there are,
something failed and the diff is wrong.

To revert a single file's reformat:

```sh
git checkout -- path/to/foo.c
```

Then patch the file by hand, or fence the offending construct with
`/*----------` markers, and re-run.

## Sources

- `src/tools/pgindent/README` (PostgreSQL tree). The canonical reference;
  the prerequisites, the per-commit and per-release procedures, the
  cleanup section, and the BSD-indent rationale all come from here.
- `src/tools/pgindent/pgindent` (Perl script). Source of truth for the
  exact indent flags, version pin (`$INDENT_VERSION = "2.1.2"`), and exit
  codes.
- `src/tools/pgindent/exclude_file_patterns`. Authoritative list of what
  the formatter skips and why.
- `src/tools/pgindent/typedefs.list` (≈4350 lines). The typedef list.
- Wiki: <https://wiki.postgresql.org/wiki/PgIndent>.
- Wiki: <https://wiki.postgresql.org/wiki/Submitting_a_Patch> § "Save us
  the trouble of reformatting" and the link to "Suggestions from Tom" on
  pre-commit pgindent invocation.
- Wiki: <https://wiki.postgresql.org/wiki/Working_with_Git> § pre-commit
  hook template.
- Wiki: <https://wiki.postgresql.org/wiki/Creating_Clean_Patches> (Greg
  Smith) for the reviewer-perspective rationale.
- Wiki: <https://wiki.postgresql.org/wiki/Committing_checklist> for the
  release-cycle reformat sequence and the `.git-blame-ignore-revs`
  protocol.
- Buildfarm: <https://buildfarm.postgresql.org/cgi-bin/typedefs.pl>;
  per-branch list at <https://buildfarm.postgresql.org/cgi-bin/typedefs.pl?show_list>.
- Blog: <http://adpgtech.blogspot.com/2015/05/running-pgindent-on-non-core-code-or.html>
  (Andrew Dunstan, 2015) — referenced from the README, useful when running
  `pgindent` on out-of-tree extensions.
- `.git-blame-ignore-revs` (postgres tree). The header documents how to
  add new bulk-reformat commits to the ignore list.
- perltidy 20230309: <https://cpan.metacpan.org/authors/id/S/SH/SHANCOCK/>.
