# Code comments

PostgreSQL has unwritten but consistent conventions for comments in
`*.c` and `*.h`. They are enforced socially through review, not
mechanically. The patterns below are derived from the actual frequency
of each marker in `origin/master` (sampled with `grep -rIhE` on
`src/**/*.[ch]`).

## TL;DR — what the agent must do

- Use `/* ... */`, never `//`. **Zero `//` comments exist** in the C
  source tree (sample of `src/**/*.[ch]`: 0 hits). Even C99 sets the
  rule; the project's CI rejects them.
- Use `XXX` for unresolved suspicions / known sub-optimal code.
- Use `NB:` for invariants the next reader needs to notice.
- Use `TODO:` only for genuine future work, not handwaving.
- Use `FIXME:` only for known-broken code.
- A comment block placed just before a function describes *why* it
  exists; an inline comment describes a *non-obvious* line. Obvious
  comments are review red flags.
- New comments should "look like they have always been there" — match
  surrounding tone, abbreviation style, and capitalisation.

## Marker frequency in the tree

Sampled from `src/` on `origin/master` (mid-2026):

| Marker | C-comment count (`/* MARK[: ] */`) |
|---|---|
| `XXX` | 158 |
| `NB` (often `NB:`) | 25 |
| `NOTE` | 22 |
| `TODO:` | 17 |
| `FIXME:` | 7 |
| `BUG:` | 0 |
| `HACK:` | 0 |

`BUG:` and `HACK:` exist informally in the wider C culture but the
project does not use them; if you find one, it was probably written
by a non-PostgreSQL contributor. Don't introduce them.

`//` comments exist in zero `*.[ch]` files. Don't introduce them.

## What each marker means in this project

### `XXX` (158 hits)

The dominant marker. Used for "this is suspicious / sub-optimal /
known-but-not-yet-resolved". Often paired with a question.

Real examples from the tree:
```c
/* XXX record free space in FSM? */
/* XXX shouldn't we fall through to look at xmax? */
/* XXX assumes index has only one attribute */
/* XXX: we should assert that a snapshot is pushed or registered */
/* XXX we could presumably do this without a lock. */
```

When to use: you are introducing code you know is not the final shape
but is the right shape *for now*. The `XXX` invites the next reader
to challenge it. Don't strip prior `XXX` comments without a thread on
-hackers; they are intentional artifacts.

### `NB:` (25 hits)

"Note bene." Used to highlight a load-bearing invariant. Stronger than
a normal comment because it implies the next reader will probably
*want* to violate it and shouldn't.

Real examples:
```c
/* NB: xid must be known committed here! */
/* NB: do NOT reorder the mergeclauses */
/* NB: caller must ReleaseSysCache the type tuple when done with it */
/* NB: intentionally counting invalidated slots */
```

When to use: you are about to write code where the obvious refactor
would break a non-obvious invariant. Tell the next reader.

### `NOTE` (22 hits)

Lighter than `NB:`. Used for "by the way, here is context the next
reader needs". Often used to point at a related file or function.
Frequently spelled with no colon: `/* NOTE: ... */` or `/* NOTE ... */`.

When to use: contextual reference, no warning attached.

### `TODO:` (17 hits)

Genuine future work, scoped narrowly. Real examples:
```c
/* TODO: Check that only allowed strategy numbers exist */
/* TODO: Consider fillfactor */
/* TODO: Encapsulate cleanup from the PG_TRY and PG_CATCH blocks */
```

When *not* to use: do not write `TODO: make this work` for code that
doesn't work today. That's a `FIXME` (or a bug that should not be
committed). Do not write `TODO: refactor when we have time` — that's
a wishlist, not a project artifact. The wiki TODO list at
<https://wiki.postgresql.org/wiki/Todo> is the project's actual
backlog; in-tree `TODO:` is for narrowly-scoped follow-ups *adjacent
to the code where the comment lives*.

### `FIXME:` (7 hits)

Known-broken or known-incomplete code. Rare because review usually
catches and rejects code at this status. Real examples:
```c
/* FIXME: validate event mask */
/* FIXME: we might send it ok, but get an error */
/* FIXME: destructor is never called in Win32. */
```

When to use: only when the code is known-incorrect *but the project
has consciously chosen to ship it as-is*. A reviewer or committer
will ask why a FIXME exists; have an answer.

## Block-comment shape

- Function-leading block:
  ```c
  /*
   * FunctionName
   *      One-line description. Period at end.
   *
   * Longer paragraph(s) describing semantics, invariants, lock
   * ordering, side effects. Wrapped to ~78 cols.
   */
  ```
- Two leading spaces after the opening `*` for the first content line
  is the project idiom; subsequent paragraphs are flush.
- Multi-paragraph blocks are separated by ` *` lines (asterisk + space).

Do not mimic Doxygen / Javadoc tags (`@param`, `@return`). The project
does not parse them. Describe params in prose.

## Inline-comment placement

- Above the line it describes, indented to match.
- *Same-line* trailing comments are common but reserved for short
  remarks; keep the comment under ~30 chars or move it to its own
  line above. The pgindent flag `-cdb` "comment delimited block" and
  the comment-handling rules in `src/tools/pgindent/pgindent` reflow
  long trailing comments into block form.

```c
/* OK: describes next line */
ptr = palloc(size);

ptr = palloc(size);  /* ok-trailing if short */
```

## Comments in `.h` headers vs. `.c` files

- **Headers** describe *contract*: what a function takes, what it
  returns, what invariants it requires. The block comment above the
  prototype in the header is the canonical reference.
- **Implementation files** describe *mechanism*: how the function
  achieves its contract, what edge cases the body handles.
- Do not duplicate the contract verbatim in both. Update both when
  the contract changes; cross-reference with the function name (the
  reader uses `git grep` to find the other).
- Struct definitions get a block comment in the header explaining
  *what the struct represents*; field-level comments go on the
  fields where the meaning is non-obvious.
- `static` functions in `.c` files often get only a one-line comment;
  `extern` functions deserve full block comments (in the header *or*
  the `.c` if the declaration is module-internal).

## Comment placement in catalogs

`src/include/catalog/pg_*.h` files use a special comment shape: each
catalog table's column gets a one-line `/* foo bar */` after the
field declaration. Tools (`bki`, `genbki.pl`, `gen_node_support.pl`)
parse these. Do not reformat them; do not lengthen them.

## "Should look like it's always been there"

A repeated review comment from Tom Lane and Bruce Momjian: when
modifying an existing comment block, match the surrounding style
exactly. Don't switch from "ok" to "OK", don't switch from
abbreviated `xact` to spelled-out `transaction`, don't introduce a
new abbreviation that doesn't appear elsewhere in the file. The
goal is that a future reader cannot tell which lines are 1996 and
which are 2026.

This applies to:

- Capitalisation (`SQL`, not `Sql`; `MVCC`, not `Mvcc`; `OID`, not
  `Oid` *in prose comments*, but `Oid` *in C identifiers*).
- Tense (the file is overwhelmingly present tense; don't switch to
  past).
- Abbreviation set: stick to the abbreviations already used in the
  file. New abbreviations need a one-line definition somewhere
  visible.

## What never goes in comments

- **Author attribution**: `/* added by Foo, 2024 */`. The project
  records authorship in commit messages, not in code. `git blame`
  is canonical.
- **Date stamps**: `/* updated 2024-05-15 */`. Stale within months.
- **Bug-tracker IDs**: there is no project bug tracker; commitfest
  and -hackers thread URLs are in the commit message, not in the
  code.
- **Copyright on individual files**: the project's copyright lives
  in the file header (already present, do not alter) and in
  `COPYRIGHT`. Do not add per-edit copyright lines.
- **Commented-out code**: delete it. `git log` is the archive.

## Pre-flight grep on a patch

```sh
git diff origin/master.. -- '*.c' '*.h' | grep -E '^\+.*//'
# Any hit is a forbidden C++ comment.

git diff origin/master.. -- '*.c' '*.h' | \
    grep -E '^\+.*/\*\s*(BUG|HACK)\s*[: ]'
# Any hit is a non-project marker.

git diff origin/master.. -- '*.c' '*.h' | \
    grep -E '^\+.*\*.*\b(added|modified|updated)\s+(by|on)\b'
# Any hit is forbidden author/date attribution.
```

## Sources

- Empirical: `grep -rIhE "/\*[[:space:]]*<MARK>[: ]" --include="*.[ch]"
  src/` on `origin/master`. Counts as of mid-2026:
  XXX=158, NB=25, NOTE=22, TODO=17, FIXME=7, BUG=0, HACK=0,
  C++-style `//` comments=0.
- `src/tools/pgindent/pgindent` — comment-handling flags (`-cdb`,
  `-cli1`, `-cp33`) and the comment-fence (`/*----------`) protocol;
  see `community/conventions/pgindent.md` § "Comment-block protection".
- Wiki: <https://wiki.postgresql.org/wiki/Coding_Conventions> —
  general C style, including the no-`//` rule.
- Wiki: <https://wiki.postgresql.org/wiki/Todo> — the project's
  out-of-tree TODO list, distinct from in-tree `TODO:` markers.
- `src/include/catalog/pg_*.h` for catalog-column comment shape.
- Cross-reference: `community/conventions/pgindent.md` for the
  comment-fence (`/*----------`) that prevents pgindent reflow of
  hand-formatted comments.
- Cross-reference: `community/voices/tom-lane.md` § "Don't reformat
  unrelated code" — applies to comment reformatting too.
- Cross-reference: `community/conventions/commit-message-format.md`
  for the parallel "what goes in commit messages, not code" rules.
