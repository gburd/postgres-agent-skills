# Whitespace and encoding

PostgreSQL is strict about whitespace and character encoding in source
and commit messages. The rules are simple, well-enforced, and easy to
violate by accident — most commonly by a misconfigured editor, a
copy-paste from a wiki, or a Windows checkout.

## TL;DR — what the agent must do

```sh
git diff --check                    # before every commit
git diff --check origin/master..    # before posting any patch series
file -bi <files>                    # confirm "charset=us-ascii"
```

If `git diff --check` reports anything, fix it. If `file -bi` reports
`utf-8` and the file is not under `src/test/regress/data/` /
`src/test/locale/`, you have stray non-ASCII characters that should
not be there.

## Indentation

- **Tabs for indentation.** One leading tab per nesting level in C
  source.
- **Spaces for alignment.** When you align a continued statement
  beyond the indentation column, use spaces, not tabs. The mix is
  intentional — tabs handle indentation, spaces handle alignment.
- **Tab width: 4.** Set your editor: `vim` `set ts=4 sw=4 noet`,
  Emacs `c-basic-offset 4`, VS Code `"editor.tabSize": 4,
  "editor.insertSpaces": false`.
- The `pg_bsd_indent` flags in `src/tools/pgindent/pgindent` encode
  this: `-i4 -ts4`. Do not override.

`pgindent` enforces tabs-for-indent automatically. See
`community/conventions/pgindent.md` for invocation.

## Trailing whitespace

- **None.** Trailing spaces or tabs at end-of-line are forbidden.
- `git diff --check` is the canonical detector. Exit code is non-zero
  on any whitespace error in the staged diff. Cite from the git docs:
  `git diff --check` "Output a warning if changes introduce
  conflict markers or whitespace errors".
- Empty lines must be truly empty (no trailing space).

Pre-commit hook to enforce locally:

```sh
#!/bin/sh
# .git/hooks/pre-commit
git diff --cached --check || exit 1
```

## Line endings

- **LF only.** No CRLF. No CR.
- A `\r` snuck into a `.c` file is a bug; agents should treat
  `git diff` output containing `^M` as a hard fail.
- Windows users: `git config --global core.autocrlf false` and
  `* text=auto eol=lf` in `.gitattributes` (the project's
  `.gitattributes` already sets this for tracked text).

## Character encoding

- **ASCII only** in `*.c`, `*.h`, `*.sgml`, `*.y`, `*.l`, `*.pl`,
  `*.pm`, `Makefile`, `meson.build`, and commit messages.
- **UTF-8 only when justified.** The exceptions:
  - `src/test/regress/data/` — regression test data deliberately
    exercises non-ASCII strings.
  - `src/test/locale/` — locale-specific test data.
  - `doc/src/sgml/release-*.sgml` author names where the author
    actually has a non-ASCII name. Use the canonical spelling.
  - `pgsql-translators` `*.po` files — translations are obviously
    non-ASCII.
- Commit messages are ASCII. If you have a contributor with a
  non-ASCII name, a `Co-authored-by:` or `Reviewed-by:` line *is*
  permitted to contain non-ASCII (the trailer parser handles UTF-8),
  but the body is ASCII.

Why ASCII-only: half the project's tooling pre-dates universal UTF-8
locale support, the buildfarm runs in mixed locales, and `psql` and
`pg_dump` regression tests want byte-exact diffs. Stray smart-quotes,
en-dashes, or non-breaking spaces from a wiki copy-paste produce
weird buildfarm failures hours after commit.

Detect with:

```sh
file -bi <file>                # should report charset=us-ascii
LC_ALL=C grep -P '[^\x00-\x7F]' <file>   # exact non-ASCII characters
```

For the in-tree check the project uses, see `make check-headerscheck`
and the regression tests under `src/test/regress/sql/encoding.sql`.

## Specific characters to never paste

These come in via wiki / Slack / email copy-paste and look fine until
they don't:

| Wrong | Right |
|---|---|
| `’` (U+2019, right single quote) | `'` (apostrophe / single quote) |
| `“ ”` (U+201C/D, smart double quotes) | `"` (straight) |
| `–` (U+2013, en dash) | `-` (hyphen-minus) |
| `—` (U+2014, em dash) | `--` |
| `…` (U+2026, horizontal ellipsis) | `...` |
| `\u00a0` (non-breaking space) | regular space |
| `\u200b` (zero-width space) | (delete) |

Modern macOS and iOS auto-correct convert ASCII to these on the fly.
Disable on any device used for commit-message authoring.

## Git config the project expects

Set these once globally:

```sh
git config --global core.autocrlf false
git config --global core.safecrlf true
git config --global apply.whitespace error      # `git apply` rejects whitespace errors
git config --global core.whitespace 'tab-in-indent,trailing-space,cr-at-eol'
git config --global blame.ignoreRevsFile .git-blame-ignore-revs
```

`tab-in-indent` looks counter-intuitive but is correct: with the
project's "tabs for indent, spaces for alignment" rule, the
*violation* `git diff --check` looks for is a *space* used in the
indentation column, not a tab. Read the `core.whitespace` man page
carefully; the default config covers the common cases.

## Trailing newline at end of file

- **Required.** Every text file ends with a single newline character.
- POSIX defines a "line" as terminated by a newline; some tools
  silently misbehave on files lacking the terminator.
- Recent enforcement: commit `79ac82125ef` "pgindent: ensure all C
  files end with a newline." (Tom Lane) — pgindent now adds a
  trailing newline if missing on `*.c` files.

`git diff --check` does not catch missing trailing newline. Detect
with:

```sh
[ -z "$(tail -c1 <file>)" ] || echo "missing trailing newline: <file>"
```

## Maximum line length

- **Soft cap 79.** `pgindent` flag `-l79` reflects this.
- **Long string literals are exempt** — wrapping a SQL error message
  to 79 cols mid-string would corrupt the message. Keep long strings
  on a single line.
- **URLs in comments are exempt** — a URL that wraps becomes
  unclickable.
- **Function declarations and call sites** wrap at the open
  parenthesis if they exceed 79 cols. `pgindent` handles this.

Exception: SGML / XML in `doc/src/sgml/` is wrapped at 78. Check
existing files in the same directory before guessing.

## Tabs in non-C files

- **Makefiles**: tabs are mandatory in recipe lines (POSIX make).
- **Python (`.py`)**: 4 spaces, no tabs (`pgperltidy` does not run on
  Python; the few Python scripts in the tree follow PEP 8).
- **Perl**: tabs in `*.pl` / `*.pm`, formatted by `pgperltidy`. See
  `community/conventions/pgindent.md` for the perltidy version pin.
- **SQL** (`.sql`): tabs.
- **YAML** (`.cirrus.yml`, GitHub Actions): spaces. YAML forbids
  tabs.
- **JSON** (`.json` test fixtures): spaces.

## Commit message whitespace

- Subject: no leading/trailing spaces; no tabs anywhere.
- Body: wrap at 72-78 cols (URLs excepted). No tabs.
- Trailers: one per line; no leading whitespace; one space after
  the colon: `Author: First Last <email@example.com>`.
- See `community/conventions/commit-message-format.md` for the
  trailer schema.

## How `git diff --check` is used socially

Committers run `git diff --check` on any patch they consider for
commit. A patch that fails the check goes straight back to the
author with "please fix whitespace and resend". This is a free
review-cycle the agent should never burn.

In CI, the cf-bot runs equivalent checks; whitespace failures
appear as a red flag on the commitfest entry.

## Detecting issues in an inbound patch

When applying a patch you received:

```sh
git apply --check --whitespace=error <patch>
```

`--whitespace=error` causes `git apply` to refuse to apply if the
patch contains whitespace errors. This is what committers do.

Alternative: `git am --whitespace=fix <patch>` to *auto-fix*
whitespace on apply, but only do this if you are the author. Do not
auto-fix someone else's patch and then commit it — they should fix
and resend.

## Sources

- Wiki: <https://wiki.postgresql.org/wiki/Submitting_a_Patch>
  § "Save us the trouble of reformatting" — tabs/spaces/encoding
  section.
- Wiki: <https://wiki.postgresql.org/wiki/Working_with_Git>
  § "Whitespace, line endings".
- Wiki: <https://wiki.postgresql.org/wiki/Creating_Clean_Patches>
  (Greg Smith) — `git diff --check` and `git diff --color` rationale.
- `src/tools/pgindent/pgindent` — flags `-i4 -ts4 -l79` documenting
  the indentation/tab/line-length policy.
- Commit `79ac82125ef` "pgindent: ensure all C files end with a
  newline." (Tom Lane) — trailing-newline enforcement.
- `git-diff(1)` man page § `--check` — whitespace error definitions.
- `git-config(1)` man page § `core.whitespace`,
  `apply.whitespace`.
- `.gitattributes` (postgres tree) — `* text=auto eol=lf` and per-
  file overrides.
- Cross-reference: `community/conventions/pgindent.md` for the
  formatter that enforces tabs-for-indent and the trailing-newline
  rule.
- Cross-reference: `community/conventions/commit-message-format.md`
  for the parallel rules on commit-message whitespace and ASCII-only.
- Cross-reference: `community/conventions/creating-clean-patches.md`
  § "Inspect your diff like a reviewer" for the review-your-own-diff
  workflow that catches encoding bugs.
