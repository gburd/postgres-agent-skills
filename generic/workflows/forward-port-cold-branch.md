# Workflow: Forward-Port a Cold Branch

Resurrect a stale branch or patch from N years ago to today's `origin/master`, with conflict triage informed by upstream commit history. Use when reviving an abandoned commitfest entry, an archived feature branch, or a "I had this almost-working in 2022" workspace.

## Goal

Take a stale ref (branch, commit SHA, or message-id with attached patch from years ago), identify the divergence point, classify the upstream changes that may conflict, attempt the rebase, and for each conflict produce a resolution recommendation backed by the upstream commits' rationale.

## Inputs

One of:

- `branch_name` — a local branch (e.g. `archive/incremental-vacuum-2022`).
- `commit_sha` — a SHA in the local clone, on a stale branch.
- `message_id` — a -hackers Message-ID whose attached patch was never merged.
- `patch_file_path` — local `.patch` file produced years ago.

## Outputs

- **Divergence summary**: merge-base SHA, calendar age, number of upstream commits since divergence (overall + restricted to files the stale ref touches).
- **Upstream-change clusters**: 3–10 clusters of upstream commits grouped by area, each with a one-line rationale.
- **Per-conflict resolution plan** (after attempting the rebase):
  - Conflict location (file:line range)
  - 3-line context window before / after
  - Upstream commits that introduced the new code, with one-line summaries from `git_log`
  - Suggested resolution: `apply ours`, `apply theirs`, `hybrid`, or `abandon` — with rationale
- **Final state**: rebased branch ready for compile/test (chain to `rebase-feature-branch.md` and `fetch-patch-test.md`), or a list of manual interventions still needed.

## Steps

### 1. Materialize the stale ref locally

If you have a branch, you're done:

```bash
git checkout <branch_name>
```

If you have a SHA on a stale branch:

```bash
git switch -c forward-port/<short-name> <commit_sha>
```

If you have a message-id:

```
get_message(message_id: "<id>")
get_attachment(message_id: "<id>", index: 0)
```

Save the attachment to a local `.patch` and apply it on top of the merge-base of the patch's claimed era. To estimate the era, read the message's date header:

```
get_message_headers(message_id: "<id>")
```

Then check out the closest origin/master at that date:

```bash
PATCH_DATE="2022-03-01"
git switch -c forward-port/<short-name> $(git rev-list -1 --before="$PATCH_DATE" origin/master)
git apply /tmp/<patch>.patch
git commit -am "Original patch as of $PATCH_DATE (from <message-id>)"
```

This puts the patch on a clean parent that compiled at the time it was sent — gives the rebase a fighting chance.

### 2. Identify the divergence point

```bash
MERGE_BASE=$(git merge-base origin/master HEAD)
echo "Merge base: $MERGE_BASE"
git log --oneline "$MERGE_BASE^..$MERGE_BASE" --pretty=format:'%h %ad %s' --date=short
```

Calendar age:

```bash
git log -1 --format=%ad --date=short "$MERGE_BASE"
```

If the gap is > 2 years, expect heavy conflicts. Plan for at least one full day per 1000 lines of original patch.

### 3. Enumerate upstream changes that affect the same files

```bash
TOUCHED_FILES=$(git diff --name-only "$MERGE_BASE" HEAD)
git log --oneline "$MERGE_BASE..origin/master" -- $TOUCHED_FILES | wc -l
```

For each touched file, get the upstream commit list with rationale via pg.ddx.io (faster than reading 200 messages locally):

```
git_log(repo: "postgres", path: "<touched file>", since: "<merge-base date>", limit: 100)
```

Cluster the upstream commits by intent. Use coupling analysis to find related upstream commits even on files your patch doesn't touch (signal: upstream refactors that moved logic *out* of your file):

```
git_analyze_coupling(repo: "postgres", path: "<touched file>", since: "<merge-base date>")
git_analyze_hotspots(repo: "postgres", path: "<area dir>", since: "<merge-base date>")
git_analyze_authors(repo: "postgres", path: "<area dir>", since: "<merge-base date>")
```

The hotspot list tells you which files were refactored most aggressively; those are where conflicts will cluster. The author list tells you whose commits to read first.

### 4. Read upstream commit rationale before rebasing

For each cluster (use the top 3 by churn), pull the commits' messages and skim them. Many will be unrelated; some will explain a refactor that broke your patch's assumptions:

```
git_log(repo: "postgres", path: "<cluster file>", since: "<merge-base date>", limit: 30)
git_show_file(repo: "postgres", sha: "<commit>", path: "<cluster file>")
```

Take 5–10 minutes notes on:

- Renames (function / type / file). Your patch will reference old names.
- Refactors that split or merged functions. Your patch's call sites may no longer exist.
- API contract changes (new mandatory parameters, return-type changes).
- New invariants (e.g. "callers must hold X lock"). Your patch may violate them.

### 5. Search the archive for "did upstream replace what my patch was doing?"

This is the highest-value step that makes forward-porting possible: sometimes someone else solved the same problem in a different way, and the right answer is to abandon the stale patch.

```
search(query: "s:<patch's central concept>", inbox: "pgsql-hackers", limit: 20)
search(query: "s:<patch's central concept>", inbox: "pgsql-committers", limit: 20)
find_related_discussions(query: "<patch's central concept>")
git_search(repo: "postgres", query: "<patch's central concept>")
```

If you find that the same problem was solved upstream (different design), the forward-port may be wasted effort. Write that finding into the report and stop. Better to know now than after 8 hours of rebase.

### 6. Attempt the rebase

```bash
git rebase origin/master
```

Track each conflict as it appears. Do not resolve mechanically.

### 7. Per-conflict triage

For each conflict marker:

```bash
# Find the upstream commits that introduced the conflicting code
git log --merges --first-parent "$MERGE_BASE..origin/master" -- <conflicting-file>
git blame -L <line-start>,<line-end> origin/master -- <conflicting-file>
```

Cross-reference via pg.ddx.io (gives commit message in full):

```
git_log(repo: "postgres", path: "<conflicting-file>", since: "<merge-base date>", limit: 30)
git_blame(repo: "postgres", path: "<conflicting-file>", line_start: <N>, line_end: <M>)
```

Resolution decision rule:

- **Apply ours** (keep the stale patch's version): only if the stale patch is the more correct of the two AND upstream's change can be cleanly redone on top.
- **Apply theirs** (drop the patch's hunk): when upstream already solves what the patch was solving (compare intents). Note this in the report; the patch may be partially obsolete.
- **Hybrid**: rewrite the hunk by combining both — the most common outcome for non-trivial patches. Show the synthesized version in the report.
- **Abandon**: if conflicts saturate (every other hunk needs hybrid), the right answer is to redesign on top of master from scratch using the original patch as a *spec*, not as code. Mark the entire forward-port as `redesign-required` and stop.

### 8. Build & test

After resolution, hand off to `rebase-feature-branch.md` for the build-and-test verification loop. Do not declare the forward-port "done" until `make check` passes — many subtle conflicts hide as test failures rather than compile errors.

## MCP tool reference

- Mail: `get_message`, `get_message_headers`, `get_attachment`, `search`, `find_related_discussions`
- Git history: `git_log`, `git_show_file`, `git_diff`, `git_blame`, `git_search`
- Git analytics: `git_analyze_coupling`, `git_analyze_hotspots`, `git_analyze_authors`, `git_analyze_churn`, `git_analyze_activity`

## Failure modes

- **Stale ref doesn't compile at its merge-base.** Sometimes the original author had local environment quirks. Try the patch against the *next* commit on master after their last working state. If that fails, the original was never green; treat as `redesign-required`.
- **Original patch is in flex/bison files that have been replaced.** PostgreSQL has been migrating grammar files; old patches against `gram.y` may need full re-application against the current grammar. See `flex-bison-to-lime/SKILL.md` for the porting recipe.
- **Original patch depends on infrastructure that was reverted.** E.g. a 2018 patch built on a parallel-aggregate framework that was redesigned. The patch is salvageable only as a design document; mark it as such.
- **catversion / xlog-records have changed.** Forward-port replaces all `CATALOG_VERSION_NO` values and may need new XLOG record numbers. Don't blindly accept upstream's catversion — bump to one beyond `origin/master`'s.
- **ABI breakage on backbranches.** If the patch was originally targeted at a back-branch, ABI rules apply. See `community/conventions/committing-checklist.md` for the back-branch ABI rules.
- **Upstream has already merged a different solution.** Stop — see step 5. Write the finding; do not finish the rebase.

## Sources

- Existing skill: `generic/workflows/rebase-feature-branch.md` — chain after step 8 for the build-and-test loop.
- Existing skill: `generic/workflows/fetch-patch-test.md` — chain to it if your input is a message-id.
- `community/conventions/committing-checklist.md` — back-branch ABI rules, catversion bump rules.
- `community/conventions/git-workflow.md` — rebase mechanics that match the project's expectations.

## Example

Input: branch `archive/parallel-vacuum-2021` last touched 2021-09, 47 commits ahead of its merge-base.

```bash
# 1. Materialize
git checkout archive/parallel-vacuum-2021

# 2. Divergence
MERGE_BASE=$(git merge-base origin/master HEAD)
git log -1 --format=%ad --date=short "$MERGE_BASE"
# 2021-09-15.  Four years of upstream change.

# 3. Touched files
TOUCHED=$(git diff --name-only "$MERGE_BASE" HEAD)
echo "$TOUCHED"
# src/backend/access/heap/vacuumlazy.c
# src/backend/access/heap/heapam.c
# src/backend/commands/vacuum.c
# src/include/access/heapam.h

# 4. Upstream churn on those files
for f in $TOUCHED; do
  echo "=== $f ==="
  git log --oneline "$MERGE_BASE..origin/master" -- "$f" | wc -l
done
# vacuumlazy.c: 138 commits. Heavy.

# 5. Hotspots
```
```
git_analyze_hotspots(repo: "postgres", path: "src/backend/access/heap", since: "2021-09-15")
git_analyze_coupling(repo: "postgres", path: "src/backend/access/heap/vacuumlazy.c", since: "2021-09-15")
```
```bash
# 6. Has anyone solved parallel vacuum upstream?
```
```
search(query: "s:parallel vacuum", inbox: "pgsql-hackers", limit: 20)
search(query: "s:parallel vacuum", inbox: "pgsql-committers", limit: 20)
git_search(repo: "postgres", query: "parallel vacuum")
```
```
# Found: parallel index vacuum landed in PG13 (different design). The
# stale branch's "parallel heap-pruning" angle was never merged. Forward-port
# is still novel work, but rebase will conflict with the parallel-index
# vacuum infrastructure.

# 7. Rebase
git rebase origin/master
# CONFLICT: vacuumlazy.c — lazy_scan_heap was split into lazy_scan_prune and
#                          lazy_scan_noprune in d36d70e (2024-11-15).
# CONFLICT: heapam.h — heap_page_prune signature changed.

# 8. Triage
```
```
git_log(repo: "postgres", path: "src/backend/access/heap/vacuumlazy.c", since: "2024-09-01", limit: 30)
git_blame(repo: "postgres", path: "src/backend/access/heap/vacuumlazy.c", line_start: 1100, line_end: 1200)
```

The output report would recommend:
- `lazy_scan_heap` conflict → **hybrid**: re-implement the parallel hook against the new `lazy_scan_prune` entry-point.
- `heap_page_prune` signature → **apply theirs**: take upstream's signature, port the patch's parallel-context argument as a separate function.
- catversion → bump to `origin/master + 1`.
- Estimated remaining work: 2 days. The patch's design is still relevant; the implementation is 60% rewrite.

## Tips

- Don't `git rebase` a 4-year-old branch in one shot. Split into eras: rebase first onto each major upstream tag along the way (PG14 → PG15 → PG16 → PG17 → master). Each era's conflicts are smaller and more comprehensible. This trades total time (slower) for cognitive load (much lower).
- Keep a running notes file (`.git/forward-port-NOTES.md`) of every decision. Reviewers will ask "why did you take theirs here?" — having the upstream commit SHA and rationale already noted answers it instantly.
- If the original author is reachable, ask them. A 5-minute email exchange ("does the design still apply?") can save days of forward-port effort. Find their email via `get_author_messages` or `find_contributions`.
- After the rebase, run `pre-review-by-committers.md` on the result before posting. The simulation will surface "you forgot to update the docs / regression tests" issues that always accompany a forward-port.
