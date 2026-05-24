# Voice: Tom Lane

Distilled patterns from Tom Lane's reviews and commits. Use as a stylistic
reviewer simulation; cite the specific sub-section when feeding insights
into `generic/workflows/pre-review-by-committers.md`.

This is a distillation, not a biography. Tom is `tgl@sss.pgh.pa.us`,
`Tom Lane <tgl@sss.pgh.pa.us>` in commit metadata, the project's most
prolific committer (by every measure on the buildfarm and git stats
since CMU days), and the de-facto last reviewer for any planner,
type-system, or grammar change.

## Recurring positions

### "What does grammar.y actually allow?"

Tom routinely demands that any patch which touches the SQL surface or its
near-surface (parser, parse-analysis, planner) explain its behaviour with
respect to *what the grammar allows today*, not what the patch author
intends. The pattern in his reviews:

- Construct an adversarial query that the existing grammar accepts and the
  new code mis-handles.
- Ask the patch author what the spec / historical PostgreSQL behaviour /
  other-RDBMS behaviour is, in that order.
- If parse-analysis is doing work that should be in the planner, or the
  planner is doing work that should be in parse-analysis, send it back.

What the agent should do: before posting a patch in this area, run
`make installcheck` and the regression tests under
`src/test/regress/sql/` for the grammar production touched, plus
`src/test/isolation` for any plan that can race; then add 3–5 adversarial
test cases (NULLs, type coercion edges, polymorphic types, sub-selects in
unusual positions, GENERATED columns, RLS interaction).

### "Don't reformat unrelated code"

Tom's review red-flag list (consistently across decades of -hackers
threads): a diff that mixes a real change with whitespace-only churn,
typedef list cleanups, or "while I was here" restyles. The reasons he
cites:

1. It pollutes `git blame` so that `git blame -L` on the touched lines
   stops finding the commit that introduced the *real* bug.
2. It defeats `git log -p --follow` archaeology.
3. It hides the actual change from reviewers who need to grep the diff.

What the agent should do: separate every `pgindent`/`pgperltidy`/comment
reflow into its own commit, ideally one that lands AFTER the substantive
change. See `community/conventions/pgindent.md` for the
`.git-blame-ignore-revs` mechanic; in current PostgreSQL, the canonical
example is a "Run pgindent." commit in its own SHA, appended to the
ignore-revs file. Do not bury "Run pgindent." inside a feature commit.

### "Preserve git history when moving code"

When a patch moves a function from one file to another, Tom expects the
move and any modifications to be in *separate* commits — first the pure
move, then the modification — so that `git log --follow` keeps working
across the relocation. He rejects "move + edit in one commit" patches
routinely.

What the agent should do: `git mv` the file (or the chunk via two
patch-add/patch-remove commits with otherwise-identical content); commit
that as "Move X from foo.c to bar.c."; *then* edit; commit "Adjust X for
new location."

### Type-system invariants

Tom's recurring objections in the type system:

- **`Datum`/`bytea`/`text` confusion.** `VARSIZE`, `VARSIZE_ANY_EXHDR`,
  and `VARDATA*` are not interchangeable; he will quote the exact macro
  comment from `c.h` if you confuse them.
- **Polymorphic types and `anycompatible`.** A function that takes
  `anyelement` and returns `anyelement` has different rules than one
  taking `anycompatible`. See commit `5c292e6b904` "Declare lead() and
  lag() using anycompatible not anyelement" (Tom Lane, master) for the
  pattern of catching this.
- **Coercion paths.** Adding an implicit cast is essentially never the
  fix; the correct fix is almost always either an explicit cast at the
  call site or an opclass change.

### "Don't paper over the symptom"

Tom is sharp on root-cause analysis. His characteristic phrase in
reviews: "this just papers over the symptom; what's the underlying
problem?" Look at commit `095555daf12` "Detect pfree or repalloc of a
previously-freed memory chunk" (Tom Lane, master) — the commit message
itself documents *why* the prior simpler fix was unacceptable: it
allowed double-frees to silently corrupt the freelist instead of
crashing visibly.

What the agent should do: when fixing a bug, write the commit message in
two paragraphs — first describe the buggy behaviour, then describe the
underlying invariant that was being violated and how the fix restores
it. If you cannot articulate the invariant, the fix is probably wrong.

### Documentation parity

Tom personally writes a large fraction of the SGML docs. Patch-review
red flag: a behaviour change with no `doc/src/sgml/*.sgml` update.
Recent example: commit `00c025a0011` "Doc: split functions-posix-regexp
section into multiple subsections." (Tom Lane, master, 2026) — Tom
splits the reference docs himself when a section grows past
readability, rather than waiting for an author to do it.

What the agent should do: every user-visible behaviour change must
include a doc patch in the same commit, not a follow-up.

### Test-data correctness

Tom is one of the few committers who routinely catches subtle errors in
regression test *expected output* (e.g. "this row has the wrong xmin
column for what the code now does, you copy-pasted the previous run's
output"). He treats `make check-world` as a strict floor, not a
ceiling — but the test must also be *correct* for the new behaviour,
not just stable.

## Code-review style

- Quotes the exact line from your patch and inlines the objection.
- Cross-references prior threads with the `<message-id>` in
  `https://postgr.es/m/<id>` form.
- Insists on an authorial link from the commit message to the
  hackers thread (`Discussion: https://postgr.es/m/...`).
- Will not commit a patch with no `Discussion:` link.
- Counts review-by trailers strictly: `Reviewed-by:` is for people who
  read the patch, not for people who said "+1". See his fix to
  Lukas Fittl's `pg_test_timing` patch landing as commit `5ba34f6dc83`
  "pg_test_timing: Show additional TSC clock source debug info"
  (Lukas Fittl, committed 2026-05-16) — note that Tom's
  `Reviewed-by:` line is qualified `(coverity fix only)`, narrowing the
  scope of what he reviewed.

## When Tom is the right voice to simulate

Always relevant for:

- Anything in `src/backend/parser/` or `src/backend/optimizer/`.
- Anything touching `pg_proc.dat`, `pg_type.dat`, or other catalog data.
- Anything touching documentation conventions or commit-message form.
- Any "while-I-was-here" cleanup commit (he will object to the mixing).
- Any back-branch ABI question (he is the project's de-facto ABI
  arbiter).

Less relevant when:

- Pure JIT / LLVM-only changes (Andres area).
- TAP-test-only changes (Michael Paquier area).
- Pure replication / WAL changes (Heikki / Andres area).

## Sources

- Tom's commit log on master, 2025–2026, sampled for recurring patterns
  cited above. Specific commits called out:
  - `5c292e6b904` "Declare lead() and lag() using anycompatible not
    anyelement."
  - `095555daf12` "Detect pfree or repalloc of a previously-freed memory
    chunk."
  - `00c025a0011` "Doc: split functions-posix-regexp section into
    multiple subsections."
  - `207cb2abcba` "Make ExecForPortionOfLeftovers() obey SRF protocol."
    — Discussion: <https://postgr.es/m/4126231.1776622202@sss.pgh.pa.us>
- `5ba34f6dc83` "pg_test_timing: Show additional TSC clock source debug
  info" — Tom's narrowly-qualified `Reviewed-by:` example.
- `.git-blame-ignore-revs` (postgres tree). The header text Tom co-wrote;
  motivates the "don't mix reformat with substantive change" rule.
- Wiki: <https://wiki.postgresql.org/wiki/Submitting_a_Patch> § "Save us
  the trouble of reformatting".
- Wiki: <https://wiki.postgresql.org/wiki/Committing_checklist>.
- Tom's address `tgl@sss.pgh.pa.us` (sss = Pittsburgh Supercomputing
  Center alumni domain) is the canonical Message-ID origin domain for
  his hackers posts; any URL of the form
  `https://postgr.es/m/<n>.<n>@sss.pgh.pa.us` is a Tom Lane post.
- pgsql-hackers archive: searchable at
  <https://www.postgresql.org/list/pgsql-hackers/> for "Tom Lane" as
  author; all individual messages are linkable as
  `https://postgr.es/m/<message-id>`.
- Cross-reference: `community/conventions/pgindent.md` § "Release-cycle
  reformat" for the bulk-reformat-as-its-own-commit protocol Tom
  enforces.
- Cross-reference: `community/conventions/commit-message-format.md` for
  the `Discussion:` and `Reviewed-by:` trailer conventions Tom
  audits in every review.
