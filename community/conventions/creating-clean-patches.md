# Creating clean patches

Greg Smith's wiki article "Creating Clean Patches" is the canonical
project guide on what a posted-to-hackers patch should look like. This
skill distills its review-your-own-diff-like-a-reviewer methodology
into an actionable checklist for the agent.

## TL;DR — what the agent must do

Before posting any patch:

```sh
git rebase -i origin/master            # collapse WIP into logical commits
src/tools/pgindent/pgindent <files>    # pgindent
git diff --color origin/master..       # eyeball the diff in colour
git diff --check origin/master..       # whitespace
make -s check-world                    # full test suite
git format-patch --cover-letter -v1 -B -M origin/master..HEAD
```

Read each generated `.patch` file in your terminal. If you see anything
you wouldn't accept as a reviewer, fix it.

## The core idea: review your own diff

Most patches rejected on aesthetic / style grounds were never read
*by their author* in the form a reviewer will see. The fix is to make
the author do that reading first.

Methodology, in the order Greg recommends:

1. **Look at the diff in colour.** `git diff --color
   origin/master..`. Colours surface unintended whitespace adds /
   removes, blank-line churn, and tab/space mixes that are invisible
   in plain output.
2. **Run `git diff --check`** to catch whitespace issues mechanically.
3. **Read the diff sequentially**, top to bottom, as if you were
   reviewing it. Ask at every hunk: *do I understand why this hunk
   exists?* If you can't articulate the reason, neither can the
   reviewer.
4. **Look for unrelated changes**: a stray reformat in a function you
   touched but didn't actually modify; a "while-I-was-here" rename;
   a comment fix in a different subsystem. Move them to a separate
   commit (or revert them).
5. **Run the test suite**, including `make check-world`, the
   isolation tester, and the TAP tests for any subsystem touched.
   See `generic/workflows/build-and-test.md`.
6. **Run pgindent**. See `community/conventions/pgindent.md`. If
   pgindent moves any line you did not touch, you have a missing
   `typedefs.list` entry.
7. **Look for accidentally-included files**: editor backup files
   (`*~`), pgindent leftovers (`*.BAK`), pgperltidy leftovers
   (`*.LOG`), profiling outputs, `.DS_Store`, `Thumbs.db`. `git
   status` should be clean except for the files your patch
   intentionally touches.

## Squashing with `git rebase -i`

A patch series posted to -hackers should consist of *logical* commits,
not the chronological "fix typo, fix bug, address review, fix typo
again" history of a private development branch.

```sh
git rebase -i origin/master
```

In the editor:

- `pick` the first commit of each logical change.
- `fixup` (or `squash`) subsequent commits that are corrections,
  typo-fixes, or pgindent-pass-fixups belonging to that logical
  change.
- `reword` to fix the commit message.
- `drop` to discard a commit entirely.
- Reorder lines to put logical commits in the order they should be
  reviewed (preparation patches first, headline change last).

After the rebase, run the full test suite again — `git rebase -i`
can change the order of commits in ways that produce a clean final
state but a broken intermediate state. Each commit should
independently build and pass `make check`.

The bisectability test:

```sh
git rebase -x 'make -s -j$(nproc) check' origin/master
```

This re-applies each commit and runs `make check` after each one. If
any intermediate commit fails, the series is not bisectable; fix
before posting.

## Splitting a too-large patch

If your single patch:

- Exceeds ~500 lines of substantive change, or
- Touches more than one subsystem, or
- Mixes refactor + new behaviour + tests + docs, or
- Has more than one independent rationale,

then split it into a series. The conventional split:

```
0001-Refactor-X-to-prepare-for-Y.patch
0002-Add-Y.patch
0003-Tests-for-Y.patch
0004-Doc-for-Y.patch
```

Each numbered patch is independent: `git apply 0001-...; make check`
must pass before applying 0002.

Posting hint: when a series has 3+ patches, write a cover letter
explaining the layering and what should be reviewed first. See
`community/conventions/git-workflow.md` § "git format-patch for
posting".

## What "clean" means line-by-line

A clean diff (Greg's checklist, condensed):

- No trailing whitespace (`git diff --check`).
- No mixed tabs/spaces in indentation (pgindent enforces).
- No spurious blank-line additions or removals.
- No re-flowed comments outside the area being changed.
- No "while-I-was-here" reformats.
- No commented-out code.
- No `printf` / `fprintf(stderr, ...)` / `puts` debugging artifacts —
  use `elog(DEBUG1)` or remove.
- No `Assert(false)` placeholders that aren't actually unreachable
  (see `community/voices/michael-paquier.md` § "Why `assert(false)`
  is not a fix").
- No editor-added BOM in `.sgml` files.
- No DOS line endings (`^M`).
- Trailing newline on every text file (`pgindent` enforces on `*.c`
  via commit `79ac82125ef`; for `*.h`, check manually).

## Per-file pre-flight grep

```sh
# C++-style comments (not allowed in C source)
git diff origin/master.. -- '*.c' '*.h' | grep -E '^\+.*//[^/]'

# Forbidden markers
git diff origin/master.. -- '*.c' '*.h' | \
    grep -E '^\+.*/\*\s*(HACK|BUG)\s*[: ]'

# Author/date attribution in comments
git diff origin/master.. -- '*.c' '*.h' | \
    grep -E '^\+.*\*.*\b(added|modified|updated)\s+(by|on)\b'

# printf debugging
git diff origin/master.. -- '*.c' | grep -E '^\+\s*(printf|fprintf|puts)\b'

# stray non-ASCII
git diff origin/master.. -- '*.c' '*.h' '*.sgml' | \
    LC_ALL=C grep -P '^\+.*[^\x00-\x7F]'
```

Each of these should produce zero output. Anything they catch is
something a reviewer will catch first.

## The cover letter

`git format-patch --cover-letter` creates a `0000-cover-letter.patch`
template. The author edits it before sending. It should contain:

1. **Subject** (one line): the high-level subject of the *series*,
   not of any individual patch. E.g. "Add I/O instrumentation to
   EXPLAIN" — even though the series has 5 patches.
2. **Motivation paragraph(s)**: why this matters, what problem it
   solves, what the user-visible impact is.
3. **Series layout**: a one-line description of each patch and why
   it belongs in this series. If the series is split for a specific
   reason ("0001 is a refactor that should land independently of
   the rest"), say so.
4. **Outstanding questions**: things you want a reviewer's
   judgement on. Not "do you like this?" but specifically "should
   the new GUC default to X or Y, and why?".
5. **Test summary**: what testing you ran, what platforms, what new
   tests you added.
6. **Discussion link** to prior threads if the patch is a follow-up
   or has been previously posted (with the v-bump rationale).
7. **Performance numbers** if performance is the rationale, with
   the caveats from `community/voices/tomas-vondra.md` § "Benchmarking
   is hard" and `community/voices/andres-freund.md` § "Measure first,
   hack second".

Avoid:

- Marketing language ("revolutionary", "game-changing"). Stick to
  technical vocabulary.
- Apologies for the patch ("I know this is rough but..."). Polish
  before posting; if it's not ready, don't post.
- Long stack traces or paste of the full bug history. Link to a
  -hackers thread or a wiki page if there is context that would
  exceed a paragraph.

## Resubmits: the v2/v3 discipline

When you respond to review feedback, your v2 series should:

- Address every concrete review point from v1, or explicitly say
  why you didn't.
- Carry over `Reviewed-by:` lines from v1 only for reviewers who
  re-reviewed v2 (or whose review concerns survived intact).
- Note the changes between versions in the cover letter, in a
  "Changes since v<N-1>:" section. Bullet form, terse.

Example cover-letter "Changes since v1:" section:

```
Changes since v1:
- Address Tom's concern about polymorphic-type interaction (added
  test in expr_polytype.sql).
- Move the new GUC out of the AUTOVACUUM section into PLANNER (per
  Vondra).
- Fix pgindent regression on src/backend/optimizer/path/costsize.c.
```

## Patch-rejection postmortem

When a committer or reviewer rejects on aesthetic grounds, the
recurring causes are:

1. Did not run pgindent.
2. Did not run `git diff --check`.
3. Posted from a branch that included unrelated commits.
4. Did not regenerate `gen_node_support.pl` output after touching
   `parsenodes.h` etc.
5. Forgot to update `meson.build` to match a `Makefile` change (or
   vice versa). See `community/voices/michael-paquier.md` § "Build
   system".
6. Forgot to update `doc/src/sgml/` for a user-visible change.
7. Bundled a "while-I-was-here" cleanup with the substantive change.
   See `community/voices/tom-lane.md` § "Don't reformat unrelated
   code".

The pre-flight checklist in this skill catches all of these.

## Sources

- Wiki: <https://wiki.postgresql.org/wiki/Creating_Clean_Patches>
  (Greg Smith). The canonical reference; this skill is its
  agent-targeted operationalisation.
- Wiki: <https://wiki.postgresql.org/wiki/Submitting_a_Patch>
  § "Save us the trouble of reformatting", § "Producing the patch".
- `git-rebase(1)` § interactive mode.
- `git-format-patch(1)` for the `-v` and `--cover-letter` flags.
- `git-diff(1)` § `--check`, § `--color`.
- `src/tools/pgindent/pgindent` and `src/tools/pgindent/typedefs.list`.
- Commit `79ac82125ef` "pgindent: ensure all C files end with a
  newline." (Tom Lane).
- Cross-reference: `community/conventions/pgindent.md`.
- Cross-reference: `community/conventions/whitespace-and-encoding.md`.
- Cross-reference: `community/conventions/git-workflow.md`.
- Cross-reference: `community/conventions/commit-message-format.md`.
- Cross-reference: `community/conventions/committing-checklist.md` for
  the parallel checklist a *committer* runs (some overlap, distinct
  audiences).
- Cross-reference: `generic/workflows/submit-patch.md` for the full
  end-to-end author flow that this skill is one step of.
- Cross-reference: `community/voices/{tom-lane,michael-paquier,
  robert-haas,tomas-vondra,andres-freund}.md` for the reviewer
  perspectives this skill anticipates.
