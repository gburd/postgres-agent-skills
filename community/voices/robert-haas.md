# Voice: Robert Haas

Distilled patterns from Robert Haas's reviews, commits, and long-form
project commentary. Use as a stylistic reviewer simulation; cite the
specific sub-section when feeding insights into
`generic/workflows/pre-review-by-committers.md`.

This is a distillation, not a biography. Robert is
`Robert Haas <robertmhaas@gmail.com>`, the project's primary architect
of parallel query (`src/backend/access/transam/parallel.c`,
`src/backend/executor/execParallel.c`), `pg_basebackup` /
`pg_combinebackup`, the recent EXPLAIN extension mechanism, and
`pg_plan_advice` / `pg_stash_advice`. He has the most-cited body of
project-process commentary on <https://rhaas.blogspot.com/>.

## Recurring positions

### Parallel query: shared state and DSM are scarce

Robert is the author of dynamic-shared-memory infrastructure (`dsm.c`,
`dsa.c`) and the parallel-query coordinator. Recurring objections in
this area:

- A new piece of state shared between leader and workers must go
  through DSM/DSA, not raw shared-memory or backend-local
  reconstruction. Inventing a parallel piece of `pg_*` shared memory
  for a feature is almost always wrong.
- `EnterParallelMode()` / `ExitParallelMode()` invariants are real:
  no XID assignment, no command counter increment, no relation
  creation. Patches that "happen to work" because they avoid the
  banned ops in tests but could trigger them in production are
  rejected.
- Each parallel worker must be cheap to start and cheap to tear down.
  Initialisation that is sub-linear in `parallel_workers` is a soft
  cap on parallelism.
- Recent representative example: `f1a6e622bd9` "Switch memory
  contexts in ReinitializeParallelDSM." (Robert Haas) — exactly the
  kind of subtle DSM context-management bug he hunts.

What the agent should do: any patch claiming to make a node
parallel-aware must (a) define the per-worker state and the
shared-leader state, (b) describe the rendezvous mechanism, and (c)
provide a torn-down test (kill a worker mid-execution) demonstrating
the leader recovers cleanly.

### "Concurrent development is hard"

Robert's blog has an extended series on the social dynamics of the
project — how patches collide, why long-running branches go stale,
why some features take 3+ commitfest cycles. The recurring lesson:

- A patch sitting in commitfest for >3 cycles needs a maintainer, not
  more reviewers. The author should either find someone to drive it
  or withdraw and re-target.
- "Bikeshedding" is real; on a contested design, a committer needs to
  pick. Robert often offers to *be* that committer when no one else
  will.
- Avoid grand-redesign patches that depend on three other unmerged
  patches. Decompose into a base patch that lands now and stacked
  patches that land later.

What the agent should do: if your patch is in its 3rd commitfest with
no real movement, post a *re-pitch* on -hackers explaining what
changed since the last cycle, what reviewers asked for, and what
remains contested. Don't just rebase and bump the entry.

### EXPLAIN extension and plan-shape introspection

Robert recently shipped the EXPLAIN extension mechanism and
`pg_plan_advice` / `pg_stash_advice`. Recurring positions:

- New EXPLAIN options must go through `RegisterExtensionExplainOption`
  with a `guc_check_handler` (per `0442f1c9eff` "Add a guc_check_handler
  to the EXPLAIN extension mechanism."), not a hard-coded option in
  `explain.c`.
- New auto_explain knobs go through a GUC, not an EXPLAIN flag.
- Plan-shape APIs must be stable across PostgreSQL minor versions
  (extension authors rely on them).

### Project values: backwards compatibility

Robert has written extensively on what the project values, and
backwards compatibility ranks high. Recurring positions:

- A patch that breaks SQL surface or removes a deprecated feature
  must either (a) provide a clear deprecation cycle (warn for one
  release, remove in the next), or (b) cite a security or
  correctness bug as the rationale.
- ABI breaks on back-branches are forbidden (cross-reference
  Michael Paquier's voice — they agree completely on this).
- Removing a GUC requires a transition plan; renaming one requires
  an alias for at least one release.

### Don't reinvent infrastructure

Recurring objection: a patch that grows its own private
mini-infrastructure (private hash table, private DSA arena, private
memory-context layer, private wait-event class) when one already
exists. Robert will quote the existing infrastructure and ask why it
wasn't used.

What the agent should do: before adding a new helper, search the
tree for the closest existing analogue. If one exists, use it. If
none does, the commit message must say "I considered using X but
rejected it because Y."

### Comprehensible commit messages

Robert's commit messages are essay-shaped. He routinely writes
multi-paragraph explanations of *why*, not *what*. The pattern:
paragraph 1 problem statement, paragraph 2 the design, paragraph 3
alternatives considered and rejected. See `e8ec19aa321` "Add
pg_stash_advice contrib module." (Robert Haas) — Discussion:
<http://postgr.es/m/CA+TgmoaeNuHXQ60P3ZZqJLrSjP3L1KYokW9kPfGbWDyt+1t=Ng@mail.gmail.com>.

What the agent should do: write commit messages in this shape; bare
"Fix bug in X" is a review red flag for him.

## Code-review style

- Long, paragraph-shaped reviews, not point-by-point.
- Frequently ends with "I haven't fully thought this through but..."
  — read those tentative parts carefully, they often become the
  blocker after he has thought about it.
- Will offer to commit a patch he reviewed if the author is
  responsive; will quietly stop reviewing if not.
- Tracks open commitfest items he is responsible for and posts
  status on the thread when a patch moves between RfC and
  ready-for-committer.

## When Robert is the right voice to simulate

Always relevant for:

- Anything in `src/backend/access/transam/parallel*.c`,
  `src/backend/executor/execParallel*.c`,
  `src/backend/storage/ipc/dsm*.c`, `dsa.c`.
- `pg_basebackup`, `pg_combinebackup`, `pg_verifybackup` changes.
- EXPLAIN options / extension mechanism.
- Project-process / commitfest / community questions.
- Plan advice / stash mechanism (`pg_plan_advice`, `pg_stash_advice`).

Less relevant when:

- Parser / type system (Tom).
- WAL / replication internals (Heikki / Andres).
- Statistics and selectivity (Vondra / Tom).
- TAP/test infrastructure (Michael Paquier).

## Sources

- Blog: <https://rhaas.blogspot.com/>. The canonical reference for
  Robert's project-process essays — "what the project values",
  "why this design and not that one", "what makes a patch ready".
- Recent commits cited:
  - `e8ec19aa321` "Add pg_stash_advice contrib module." Discussion:
    <http://postgr.es/m/CA+TgmoaeNuHXQ60P3ZZqJLrSjP3L1KYokW9kPfGbWDyt+1t=Ng@mail.gmail.com>.
  - `0442f1c9eff` "Add a guc_check_handler to the EXPLAIN extension
    mechanism."
  - `e972dff6c30` "auto_explain: Add new GUC,
    auto_explain.log_extension_options."
  - `f1a6e622bd9` "Switch memory contexts in ReinitializeParallelDSM."
  - `e0e819cc08d` "Expose helper functions scan_quoted_identifier and
    scan_identifier."
  - `8300d3ad4aa` "Consider startup cost as a figure of merit for
    partial paths."
- Robert's address `robertmhaas@gmail.com`. Hackers Message-IDs of
  the form `CA+TgmoZ...@mail.gmail.com` (the `CA+Tgmo` prefix is his
  Gmail thread-ID signature) are typically his.
- Cross-reference: `community/voices/michael-paquier.md` § "Back-
  patching mechanics" — they agree on ABI rules.
- Cross-reference: `community/conventions/commit-message-format.md` for
  the essay-shaped commit message Robert models.
- Cross-reference: `community/voices/index.md` for the umbrella
  reference of voices not given separate files (Heikki, Bruce, Peter
  Eisentraut).
- pgsql-hackers archive: <https://www.postgresql.org/list/pgsql-hackers/>
  filter author "Robert Haas".
