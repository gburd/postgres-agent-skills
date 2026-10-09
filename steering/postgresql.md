# PostgreSQL workflow (domain steering)

Required reading for any PostgreSQL task: a patch, an internals question, a
performance investigation, a design discussion, or extension development. This
is domain steering: load it per project that works on Postgres, not globally.
It extends the universal steering (`must-rules.md`, `coding-standards.md`,
`workflow.md`, `prose-mechanics.md`) and wins where it differs.

## Rule of first resort: research before you code

Before `grep`, `rg`, web search, or asking the human for context, consult a
PostgreSQL community/codebase research tool (the `agora` MCP skill, if
configured, indexes the pgsql-hackers archive plus the upstream git history
with author/date/thread metadata):

1. Design questions ("why does X work this way", "has Y been proposed before")
   -> thread search; read the top few.
2. Symbol lookup (a struct, a function, an executor node) -> symbol + history
   search.
3. Reviewer objections in an area -> thread search filtered by reviewer or
   subject.
4. Commit-to-thread correlation ("what discussion led to this commit").
5. Community conventions for an area.

Half the time someone already proposed the thing; understanding why it stalled
saves the same dead end. Fall back to manual search only when research comes up
short, and note the gap.

## The deliverable is files, never a sent message

Agents never send mail to any list (see `must-rules.md`): no `git send-email`,
no SMTP, not even a test copy, not even after approval. Finish with
`git format-patch` output plus a plain-text cover letter (recipients,
`In-Reply-To`, prior-thread references) and say "ready for you to send". The
human sends. The project's GitHub mirror is read-only; patches go to
pgsql-hackers plus a commitfest entry, never a PR.

## Patch-series discipline (acceptance criteria, not aspirations)

A reviewer will `git rebase --exec 'make'` the series; treat these as the bar:

- Every commit builds clean on its own with warnings-as-errors and
  `--enable-cassert --enable-injection-points`. Any commit that fails is
  disqualifying.
- Every commit passes `make check` on its own, not just the tip. Bundle each
  test with the commit that introduces the feature it exercises.
- Foundational changes precede their consumers and keep every existing consumer
  correct at that commit. If a change is only correct once its new consumer
  exists, put it in the commit with the consumer.
- Minimise churn between commits; do not add code in one and delete it in
  another within the series.
- Typedefs go in `src/tools/pgindent/typedefs.list` in the commit that
  introduces the type. Run `pgindent`.
- Do not ship a `CATALOG_VERSION_NO` bump in a posted patch: bump it locally
  for your tests, note "requires a catversion bump" in the message, and let the
  committer set the real value at push (a concrete bump collides with every
  other catalog-touching commit).
- Each commit stands alone as a defensible idea with a self-contained rationale.
- ASCII only in code, comments, docs, and messages. No internal codename in
  identifiers.
- A local-only dev-setup commit (editor/build env) stays first and is excluded
  from the submitted series.

## Build and verify (mechanics that bite)

- Build with `--enable-cassert --enable-debug --enable-tap-tests`.
  Undefined-behaviour bugs only show under cassert.
- meson caches the initdb template (`tmp_install/initdb-template`); it is not
  regenerated on `git checkout`. A stale template produces false regress diffs
  and false passes. Regenerate (`meson test --suite setup`) before a regress
  run when you changed commits.
- Build-system mtime traps: a just-checked-out file may not trigger a rebuild;
  confirm the object actually recompiled before trusting a delta.
- Distinguish stale-build and stale-template confounds from real regressions
  before concluding anything; each has fabricated both a false green and a
  false red.
- Bisect deterministic failures across the series to find the introducing
  commit; reproduce isolation/TAP failures standalone with a scratch cluster.

## Performance investigation

1. Ask for the workload shape (read/write/mixed, working-set size, isolation);
   do not guess.
2. Reproduce with a minimal `pgbench`/`psql` script; get a baseline.
3. Profile: `perf` for CPU, `bpftrace`/bcc for syscalls and IO,
   `pg_stat_statements` for query-level.
4. Hypothesise, then change one variable at a time.

For A/B against the mainline, compare the feature branch against its merge-base
with `master` (not an arbitrary tip), build both from the same checkout, refuse
to run with a dirty tree, and emit machine-readable results. The generic
methodology, instance choice, and OS tuning are in the `benchmark`,
`choose-instance`, and `tune-os-for-benchmark` tooling skills; `pg-numa-benchmark`
layers the PostgreSQL specifics.

## The security and trust model (the top review lever)

Misreading this wastes the security team's scarce time on non-issues:

- A superuser can already do anything; "a superuser can cause X" is not a
  vulnerability. Trusted versus untrusted input is the line that matters.
- `ereport(ERROR)` does a `longjmp`; palloc memory-context pooling is not a
  leak; `PG_TRY`/`volatile` exist because of the longjmp.
- `SECURITY DEFINER` plus `search_path`, signal-handler safety, and
  locale-aware comparison are the real hazards. Most "injection" reports against
  stock behaviour are not bugs.
- Genuine issues go privately to the security team only; never a public list,
  never a public proof-of-concept.

## House style (what reviewers expect)

- Comments: no comment is the default when patching existing code; a comment
  earns its place only by stating something non-obvious, pitched above the
  code. "Note that ..." is the house connective; "XXX" marks an acknowledged
  hack; never "FIXME". New code is commented more generously.
- Tests: the bar for adding one is high; simple fixes routinely ship without a
  test. When one is warranted it is minimal and blended into the nearest
  existing suite in that suite's style, not new scaffolding.
- Docs (SGML): present tense, one point per `<para>`; caveats become "Note that
  ..." sentences. A missing word is its own `doc:` commit.
- Commit messages: `area: Imperative summary.` (capitalised, ~50 chars,
  trailing period; backend changes take no area prefix). Body hard-wrapped,
  explains why not what, references the prior thread. Trailers (Reported-by,
  Author, Reviewed-by, Discussion, Backpatch-through) one person per line.
- Prose: versions are "v17"; the product is "Postgres" in casual prose;
  "back-patch" is hyphenated; GUCs and file names are bare and unquoted.

## Minimisation

Aim for the smallest patch that does the job well, in code, comments, and
tests. Split a series into a framework commit then one conversion per commit;
re-indent and blame-ignore updates are their own commits. One adjacent cleanup
may ride along if the message flags it ("While at it, ..."); anything more is
deferred and named.

## Empirical discipline

Do not assert "behaviour-preserving" or "fixed" without evidence: compare the
failing artifact before and after, show the test going red to green, show the
standalone repro now returning the right answer. When asked to verify first,
present the evidence before implementing.
