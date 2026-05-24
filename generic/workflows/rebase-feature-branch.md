# Workflow: Rebase a Feature Branch and Verify

Rebase a local feature branch onto fresh `origin/master`, classify and resolve
conflicts with archive-grounded context, then run the project's standard build
and regression tests. Use after `git fetch origin` reveals upstream movement,
before posting `vN+1` of a patch series, or as the final step of
`forward-port-cold-branch.md`.

This skill is short and mechanical; its value is the **conflict-triage policy**
in step 3 — when to keep going vs. when to stop and ask a human — and the
**build-verification fingerprint** that proves the rebase is real.

## Goal

Take a local feature branch, rebase it onto current `origin/master`, resolve
trivial conflicts with awareness of *why* upstream changed, surface non-trivial
conflicts as a clearly-framed user question with three options, and finish with
a build + `make check` pass. Output is a one-page summary the patch author can
paste into the cover-letter for `v(N+1)`.

## Inputs

- `branch_name` — local branch to rebase (default: current `HEAD` if
  detached-OK or `git rev-parse --abbrev-ref HEAD`).
- `target_ref` — base to rebase onto (default: `origin/master`).
- `configure_args` — optional additional `./configure` flags. Defaults below.
- `test_target` — `check`, `check-world`, or `installcheck`. Default: `check`.
- `meson_or_autoconf` — explicit choice; default: detect from `meson.build`
  presence + existing `build/` or `Makefile.global`.

## Outputs

- **Pre-rebase summary**: branch SHA, merge-base SHA, count of upstream
  commits since divergence, count of upstream commits touching the branch's
  files.
- **Conflict log**:
  - Per-conflict: file:line range, classification (`trivial` /
    `non-trivial` / `semantic`), upstream commits cited via `git_log` /
    `git_blame`, resolution taken or three suggested resolutions.
- **Build fingerprint**:
  - Build flags used (`./configure …` or `meson setup …`).
  - Build status: `OK` / `FAIL` with first 20 lines of the failure.
  - Test status: per-suite pass/fail, list of failing tests, link to
    `regression.diffs` if any.
- **One-paragraph cover-letter snippet** the author can paste into the
  `v(N+1)` cover.

## Steps

### 1. Verify and snapshot the starting state

```bash
# Confirm branch and clean tree.
git status --porcelain   # must be empty before rebase
BRANCH=$(git rev-parse --abbrev-ref HEAD)
START_SHA=$(git rev-parse HEAD)
echo "Rebasing $BRANCH ($START_SHA) onto $TARGET_REF"

# Fetch fresh upstream
git fetch origin --prune
git fetch origin master:refs/remotes/origin/master   # explicit if upstream is non-default
```

If the working tree is not clean, abort with a clear message. Never `git stash`
silently before a rebase; the author may have intentional WIP.

### 2. Compute divergence + upstream-change profile

```bash
MERGE_BASE=$(git merge-base "$TARGET_REF" HEAD)
echo "merge-base: $MERGE_BASE  ($(git log -1 --format=%ad --date=short "$MERGE_BASE"))"

# Total upstream commits since divergence
git log --oneline "$MERGE_BASE..$TARGET_REF" | wc -l

# Upstream commits restricted to files this branch touches
TOUCHED=$(git diff --name-only "$MERGE_BASE" HEAD)
git log --oneline "$MERGE_BASE..$TARGET_REF" -- $TOUCHED | wc -l
```

If the touched-file commit count is `> 30`, the rebase is high-risk and the
agent should warn the user **before** invoking `git rebase` — many small fixes
and a lot of upstream churn means the rebase will likely require human
judgment and the cheaper move may be to chain into
`forward-port-cold-branch.md` instead.

### 3. Run the rebase

```bash
git rebase "$TARGET_REF"
```

If it succeeds with no conflict, jump to step 5.

If it stops on a conflict, do **not** mass-resolve. Triage each conflict
through this decision tree:

#### Triage decision tree

For each conflicted hunk:

1. **`git diff --check`-only**: pure whitespace conflict, no semantic
   collision. Resolve mechanically (project-style is `tab-in-indent`,
   `trailing-space`, `cr-at-eol` per `community/conventions/git-workflow.md`
   § "Local config the project expects" — match upstream's whitespace).
   Classification: `trivial`. Continue.

2. **Adjacent edit** (your patch and upstream both edited near each other but
   not the same statement): take both, with awareness of which goes first.
   Classification: `trivial`. Continue.

3. **Same-line edit**: now you need to know *why* upstream changed it. Pull
   the upstream rationale before deciding.

   ```
   git_log(repo: "postgres", path: "<conflicted-file>",
           since: "<merge-base date>", limit: 30)
   git_blame(repo: "postgres", path: "<conflicted-file>",
             line_start: <conflict-line-start>,
             line_end: <conflict-line-end>)
   git_show_file(repo: "postgres", sha: "<upstream commit SHA from blame>",
                 path: "<conflicted-file>")
   git_diff(repo: "postgres", from_commit: "<sha>^", to_commit: "<sha>")
   ```

   Read the upstream commit message — that *is* the rationale. Decision
   matrix:

   - **Upstream's change is a refactor that does not touch your patch's
     intent**: rewrite your hunk against the new shape. Classification:
     `trivial` if the rewrite is < 10 lines; `non-trivial` otherwise.
   - **Upstream's change subsumes your patch's intent** (someone else solved
     the same problem differently): drop your hunk; note the upstream commit
     in the cover-letter snippet so reviewers know the patch lost scope.
     Classification: `semantic` — STOP, surface to user.
   - **Upstream's change conflicts with your patch's intent** (different
     designs trying to do the same thing): STOP. Classification:
     `non-trivial`. Surface three resolution options to the user (next).

4. **Non-trivial / semantic**: do not invent a resolution. Surface to the
   user as:

   ```
   CONFLICT in <file>:<line-range>  [non-trivial]
   Your hunk:
     <ours, abbreviated>
   Upstream's hunk (introduced in <sha> by <author> on <date>):
     <theirs, abbreviated>
   Upstream rationale (one paragraph from commit message):
     <quote>

   Three plausible resolutions:
   (A) Take upstream's design; rewrite our patch's idea on top.
       Cost: ~<N> lines rewrite. Risk: <low|medium|high>.
   (B) Take ours; reapply upstream's improvement on top of our hunk.
       Cost: <…>. Risk: upstream may regress.
   (C) Hybrid — combine: <one-sentence sketch>.
       Cost: <…>. Risk: <…>.

   Which (A/B/C/other)?
   ```

   Do **not** pick one for the user. The whole point of stopping is that the
   choice is design-level. While waiting, leave the rebase paused (`git
   status` still shows the rebase in progress); the user resolves and runs
   `git rebase --continue` themselves.

For trivial / non-trivial-but-mechanical conflicts the agent does resolve, run
`git diff --check` after each `git add` to catch whitespace drift before
continuing.

### 4. Loop

Repeat step 3 until `git rebase` completes (no more conflicts) or until you
have surfaced a non-trivial conflict to the user. After every batch of
resolutions, run the build (step 5) early — semantic conflicts often compile
but break tests, and an early build tells you whether your "trivial"
classifications were honest.

### 5. Build with the project's diagnostic flags

The project's standard development build for testing patches uses
`--enable-debug --enable-cassert`; some workflows add
`--enable-tap-tests`, `--enable-injection-points`,
`-DCLOBBER_CACHE_ALWAYS`, or `-DRELCACHE_FORCE_RELEASE`. See
`generic/workflows/build-and-test.md` for the long form. The minimum:

```bash
./configure --enable-debug --enable-cassert --enable-tap-tests \
            --prefix="$HOME/pg-rebase-check"
make -s -j"$(nproc)" 2>&1 | tee /tmp/rebase-build.log
echo "build status: ${PIPESTATUS[0]}"
```

For a Meson tree:

```bash
meson setup build --buildtype=debug -Dcassert=true -Dtap_tests=enabled \
    --prefix="$HOME/pg-rebase-check"
ninja -C build 2>&1 | tee /tmp/rebase-build.log
```

If the build fails, **stop**. Do not run `make check` against a partial
build; it produces noise. Surface the first 20 lines of the build error and
ask the user to direct repair.

### 6. Run the regression suite

```bash
make -s check 2>&1 | tee /tmp/rebase-check.log
# or for a wider sweep
make -s check-world 2>&1 | tee /tmp/rebase-check.log
```

Meson:

```bash
meson test -C build --print-errorlogs --suite regress
# or
meson test -C build --print-errorlogs   # all suites
```

If any suite fails, capture `regression.diffs` (autoconf:
`src/test/regress/regression.diffs`; Meson: under
`build/testrun/regress/regress/regression.diffs`). The rebase is
**not done** until tests pass.

A failing test after a rebase that previously passed almost always means a
silent semantic conflict — re-read the diff, particularly hunks classified
`trivial`. Common culprits: an upstream commit changed the call signature of
a function you didn't conflict on, or a type changed underneath you.

### 7. Compose the cover-letter snippet

The author will paste this into `v(N+1)`'s cover-letter:

```
Rebased onto <target_ref>@<sha> (was <merge-base sha>, <N> upstream
commits since divergence, <M> touching files this patch modifies).

Conflicts resolved:
- <file>:<lines> — <one-line description, citing upstream <sha>>
- <file>:<lines> — <…>

Build: --enable-debug --enable-cassert. OK.
Tests: make check. OK.
```

Honesty matters here: if a conflict was non-trivial and the user picked the
hybrid, *say so* in the cover letter. Reviewers are vastly more forgiving of
a clearly-disclosed design tension than they are of an undisclosed one
silently sneaking through.

## MCP tool reference

- Git history: `git_log`, `git_show_file`, `git_diff`, `git_blame`,
  `git_search`
- Coupling / churn: `git_analyze_coupling`, `git_analyze_hotspots`,
  `git_analyze_authors`, `git_analyze_churn`, `git_analyze_activity`
- (When chained into) `forward-port-cold-branch.md`: that skill itself uses
  `get_message`, `get_attachment` for message-id inputs.

## Failure modes

- **Repo dirty.** Abort. Never auto-stash.
- **Detached HEAD.** Abort or surface a `git switch -c rebase-tmp` proposal;
  do not silently rebase a detached HEAD onto master and lose the SHA.
- **Rebase aborts on the first commit.** Often the merge-base is older than
  the agent assumes. Recompute `git merge-base`; if the date is > 1 year
  back, redirect to `forward-port-cold-branch.md`.
- **Build fails after "trivial" conflicts only.** Re-classify; one of them
  was secretly semantic. Re-read each conflicted hunk with `git diff
  HEAD@{1} HEAD -- <file>`.
- **Tests fail in `regress/` you didn't touch.** A common signal is a
  changed default in `postgresql.conf.sample` upstream — `make check`
  expects the new default. See
  `community/conventions/committing-checklist.md` § "Sync
  postgresql.conf.sample".
- **Buildfarm-only failures the local box doesn't reproduce.** Out of
  scope here; chain to `buildfarm-blame.md` to investigate which animal +
  arch first regressed.
- **Patch series has a known squash issue.** Resolve mid-rebase by editing
  the rebase todo list (`git rebase -i`) — see
  `community/conventions/git-workflow.md` § "Rebase-and-squash, not merge".

## Sources

- `community/conventions/git-workflow.md` — canonical commands, never-merge
  rule, `apply.whitespace = error`, `.git-blame-ignore-revs`.
- `community/conventions/creating-clean-patches.md` — pre-post polish
  (re-run pgindent and `git diff --check` after the rebase).
- `community/conventions/committing-checklist.md` § "Apply the patch
  cleanly", § "Sync postgresql.conf.sample" — what a committer's
  first-pass-after-accept will hit.
- `community/conventions/whitespace-and-encoding.md` — what the whitespace
  conflicts mean and how to resolve consistently.
- `generic/workflows/build-and-test.md` — full build matrix; this skill
  uses the minimal subset.
- `generic/workflows/forward-port-cold-branch.md` — escalation path when
  divergence is too large.
- `generic/workflows/fetch-patch-test.md` — chain *to* this skill after a
  successful patch apply, when the user wants the same compile + test
  fingerprint.
- `generic/workflows/pre-review-by-committers.md` — re-run after rebase if
  the conflict resolutions touched committer-attention areas.
- Wiki: <https://wiki.postgresql.org/wiki/Working_with_Git> § "Updating
  your branch" — rebase-not-merge norm.
- Wiki: <https://wiki.postgresql.org/wiki/Submitting_a_Patch> § "Producing
  the patch" — what the cover-letter snippet feeds into.

## Example

A patch series `cf/4521-event-trigger-fix` with 6 commits, last touched 11
days ago. Branch tip is `b1f14c96720`. `origin/master` has moved 142
commits.

```bash
$ BRANCH=cf/4521-event-trigger-fix
$ git checkout $BRANCH
$ git fetch origin --prune
$ MERGE_BASE=$(git merge-base origin/master HEAD)
$ git log --oneline "$MERGE_BASE..origin/master" | wc -l
142
$ TOUCHED=$(git diff --name-only "$MERGE_BASE" HEAD)
$ git log --oneline "$MERGE_BASE..origin/master" -- $TOUCHED | wc -l
4

# 4 upstream commits touching our files; safe to attempt rebase.

$ git rebase origin/master
Auto-merging src/backend/commands/event_trigger.c
CONFLICT (content): Merge conflict in src/backend/commands/event_trigger.c
```

Triage:

```
git_log(repo: "postgres", path: "src/backend/commands/event_trigger.c",
        since: "2026-05-13", limit: 10)
# → finds upstream <sha> "Refactor EventTriggerInvoke to take EventTriggerData
#    by reference" by <committer>, 4 days ago.

git_blame(repo: "postgres", path: "src/backend/commands/event_trigger.c",
          line_start: 1240, line_end: 1280)
# → confirms the conflict line range was rewritten by <sha>.
```

Classification: refactor that doesn't change intent → `trivial-but-rewrite`.
Resolve by adapting our patch's call to the new by-reference signature.

```bash
$ git add src/backend/commands/event_trigger.c
$ git diff --cached --check
$ git rebase --continue
# Rebase completes.

$ ./configure --enable-debug --enable-cassert --enable-tap-tests \
              --prefix="$HOME/pg-rebase-check"
$ make -s -j$(nproc)
$ make -s check
# All 215 tests pass.
```

Cover-letter snippet:

```
Rebased onto origin/master@<sha> (was <merge-base sha>, 142 upstream
commits since divergence, 4 touching event_trigger.c).

Conflicts resolved:
- src/backend/commands/event_trigger.c:1240-1280 — adapted callsite to
  upstream <sha> "Refactor EventTriggerInvoke to take EventTriggerData by
  reference".

Build: --enable-debug --enable-cassert --enable-tap-tests. OK.
Tests: make check. OK.
```

## Tips

- Rebase **before** running `pgindent`; pgindent diffs after a rebase get
  conflated with conflict-resolution diffs and confuse reviewers. After
  this skill finishes, run `src/tools/pgindent/pgindent` on the touched
  files (per `community/conventions/pgindent.md`) and amend in a separate
  commit if needed.
- If the rebase chain involves more than one non-trivial conflict, stop
  after the first one and ask. Compounding speculative resolutions across
  multiple conflicts hides which ones actually caused the eventual test
  failure.
- The "upstream commits touching files this patch modifies" metric is a
  better risk predictor than total commits-since-divergence. A 500-commit
  gap with zero file overlap is safer than a 10-commit gap that all
  touched the same file.
- Keep `/tmp/rebase-build.log` and `/tmp/rebase-check.log` until the patch
  is committed by a committer. They're useful for diagnosing buildfarm
  divergence; chain to `buildfarm-blame.md` if the patch lands on master
  and an animal goes red.
