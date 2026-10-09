# Workflow: Watch Commitfest Entry Health

Detect when a commitfest (CF) entry's cfbot status drifts from green so the
author can react before the next CF cycle bites them. Turns an open question
("are my CF entries still green?") into a one-screen status table that names
which animal failed on which branch, with a cited log excerpt and a suggested
next step.

## Goal

For one CF entry, a list of entry IDs, or all entries owned by an author email,
produce a per-entry × per-branch health matrix from cfbot + buildfarm data,
flag the regressions, and propose a triage action (resubmit / investigate /
ignore) for each red cell.

This is a polling skill: re-run it before each push to confirm nothing else
went red while you were focused on one patch series.

## Inputs

One of:

- `cf_id` — single commitfest entry ID (an integer; visible in the URL on
  commitfest.postgresql.org/.../<id>).
- `cf_ids` — explicit list of entry IDs.
- `author_email` or `author_name` — fan out to every entry owned by this
  author across the active and most-recent commitfest.
- `thread_message_id` — a -hackers Message-ID from the patch thread; resolves
  to its CF entry via `find_entries_for_thread`.

Optional:

- `branches` — restrict the matrix to a subset (e.g. just `master`, or
  `master + REL_18_STABLE`). Default: all tracked branches in
  `entry_branches`.
- `since` — RFC3339 cutoff for "recent failures" (default: 14 days).

## Outputs

- **Per-entry status table** with columns: master / 18 / 17 / 16 / 15 (or
  whatever `entry_branches` returns). Each cell = `Green` / `Yellow` (build
  pending / freshness stale) / `Red` (failure).
- **Per-red-cell drill-down**:
  - Branch + animal (if buildfarm) or platform (if cfbot)
  - First-failure timestamp
  - 5–15 lines of the failure log
  - Suspected cause: `flake` / `rebase-needed` / `genuine-regression` /
    `infra` (cfbot-side issue, e.g. archive fetch broken) / `unknown`
  - Suggested action: per-row, one-liner.
- **Aggregate verdict**: counts of Green / Yellow / Red across the matrix +
  a one-paragraph summary the author can paste into an email reply when a
  reviewer asks "what's the cfbot saying?"
- **Freshness warning** if cfbot data is older than 24h: surface it; do not
  pretend stale-green is current-green.

## Steps

### 1. Resolve the input to a list of CF entries

For `cf_id` / `cf_ids`: pass through.

For an author:

```
find_entries_for_author(name_or_email: "<author>", limit: 50)
```

This returns CF entries authored or co-authored by them across the live
commitfest cycles. Filter to entries with status not in `{Committed,
Withdrawn, Rejected, Returned with Feedback}`; those are terminal and
status-watch is moot.

For a thread-id:

```
find_entries_for_thread(message_id: "<msgid>")
```

For each entry returned, capture:

```
get_entry(entry_id: <id>)
```

This gives the entry's `name`, `status`, `latest_attachment` (the most
recent patch series filename, e.g. `v7-…`), and the assigned commitfest
number.

### 2. Discover which branches this entry tracks

```
entry_branches(cf_id: <id>)
```

Returns rows like `{repo, branch_name, is_authoritative}`. Typically one
row for each `cf/<id>` cfbot branch that maps to a master + one back-branch
target. Many entries are master-only; some patches with back-branch
intent track multiple. Use the returned `branch_name` set as the
column-headers of the per-entry status table.

### 3. Pull cfbot's per-branch build history

```
get_patch_build_history(entry_id: <id>, limit: 30)
```

Returns recent run rows for each branch with `{branch, platform, status,
finished_at, log_url}`. Group by `(branch, platform)`; for each group,
take the *most recent* run as the current cell. Status values to expect:

- `success` → Green
- `failure` → Red — capture `log_url`, fetch a tail snippet
- `aborted` / `errored` / `infra` / `pending` → Yellow with a sub-label
- absent for > 24h → Yellow with `stale` sub-label

For a global view across many entries, the convenience verbs are
faster:

```
find_failing_patches(limit: 50)
find_rebase_needed_patches(limit: 50)
find_passing_long_pending(limit: 50)
build_status_freshness()
find_patches_by_platform_status(platform: "<plat>", status: "failure",
                                limit: 50)
```

`build_status_freshness` is the single check that warns if cfbot itself
is lagging (e.g. queue backed up after a force-push of master). If the
freshness reports > 24h lag, prepend a freshness warning to every entry's
output — do not bury it.

### 4. Cross-correlate with the buildfarm

cfbot tests `cf/<id>` branches; the buildfarm tests `master`. They're
distinct CI systems. If cfbot is green but a buildfarm animal is red on
master, an entry that *will* land on master may regress an animal that
the cfbot's runners don't cover (cfbot platforms are limited; buildfarm
covers exotic OSes and architectures).

For master-tracking entries, also query:

```
commit_buildfarm_status(commit_sha: "<latest origin/master sha>")
buildfarm_overview()
find_breaks(since: "<since cutoff>", limit: 30)
```

If `buildfarm_overview` shows any animal red and the entry's diff would
plausibly hit that animal's specialty (e.g. patch touches WAL → red
animal is `dragonet` on s390x → cross-mention), surface it. This is a
soft signal: don't claim causation, just flag the adjacency.

For animal-specific drill-downs:

```
list_animals(limit: 200)
get_animal(name: "<animal>")
animal_history(name: "<animal>", limit: 50)
find_failing_runs(animal: "<animal>", limit: 20)
```

Cross-reference with `find_entries_with_failures_on(animal_name:
"<animal>")` to invert: "which CF entries have failed on this animal?"
Useful if an animal goes red and the question is whose patch likely
caused it (handed off to `buildfarm-blame.md` for the full diagnosis).

### 5. Classify each red cell

Apply this decision tree per red cell, in order:

1. **`find_rebase_needed_patches`** lists this entry → cause = `rebase-needed`.
   Action: `git fetch origin && git rebase origin/master` (chain
   `rebase-feature-branch.md`).
2. **Failure log mentions `apply` / `does not apply`** → cause =
   `apply-failure`. Action: regenerate the patch series with `git
   format-patch` from a freshly rebased branch (chain
   `rebase-feature-branch.md` then resubmit).
3. **Failure log mentions `regression.diffs`** but only on one platform →
   cause = `platform-specific`. Action: investigate that platform; chain
   `buildfarm-blame.md` if a buildfarm animal is in the picture.
4. **Failure log mentions `regression.diffs` on every platform** → cause
   = `genuine-regression`. Action: pull the patch locally, run `make check`,
   diagnose. Chain `fetch-patch-test.md` if the patch is the latest in the
   thread.
5. **Failure log is empty / 500 / network** → cause = `infra`. Action: wait
   for next cfbot cycle; surface but don't burn cycles.
6. **Same failure has appeared and disappeared in the last 5 runs** → cause
   = `flake`. Action: file a -hackers note if reproducible; otherwise
   ignore and watch.
7. Otherwise → cause = `unknown`. Action: read the full log; surface to
   user as "needs human eyes".

To get the log excerpt, follow the `log_url` from
`get_patch_build_history`. Most cfbot logs are large; grep for the first
`FAIL`, `ERROR`, `regression.diffs`, or `error:` line and capture ±5 lines
of context.

### 6. Cross-reference recent CF activity

If the user is comparing "before" and "after" on a re-submission, anchor
the report against the last 7 days:

```
recent_commitfest_activity(since: "<7 days ago>", limit: 100)
```

This shows what *else* moved on the commitfest in the last week —
sometimes the answer to "why did my entry suddenly go red?" is "another
entry landed that conflicts with yours and the rebase exposed it". The
entry-history call surfaces status changes:

```
entry_history(cf_id: <id>)
```

Use this to detect status flips (e.g. `Needs Review → Waiting on Author`)
that the author may not have noticed yet; reviewers sometimes set
`Waiting on Author` without sending an email if cfbot fails repeatedly.

### 7. Compose the output

Per-entry table, in this canonical shape:

```
CF #4521 — "Event trigger for sequence change" (Author: …, status: Needs Review)
Latest patch: v7-0001-event-trigger-seq-change.patch  (posted 2026-05-21)

Branch matrix (last cfbot run per platform):
                    master        REL_18      REL_17
Linux/x86_64       Green         (n/a)        (n/a)
FreeBSD/x86_64     Red ←         (n/a)        (n/a)
macOS/arm64        Yellow stale  (n/a)        (n/a)
Windows MSVC       Green         (n/a)        (n/a)

Red cells:
  - master/FreeBSD/x86_64 — failure at 2026-05-23T08:14Z
    Log excerpt:
        regression.diffs: event_trigger_sequence ... FAILED
        --- expected/event_trigger_sequence.out  ...
        +++ results/event_trigger_sequence.out   ...
        @@ -42,7 +42,7 @@
        -NOTICE:  trigger fired (sequence: my_seq)
        +NOTICE:  trigger fired (sequence: public.my_seq)
    Cause: genuine-regression (FreeBSD-only schema-qual regression)
    Suggested action: investigate qualified-name handling on FreeBSD;
                      reproduce via `--with-includes=…` on a FreeBSD VM
                      or chain `fetch-patch-test.md` and run on local box.

Buildfarm cross-check (master): all green at <sha>.
Freshness: cfbot last ran 4h ago. OK.
```

Aggregate verdict:

```
Summary: 1 entry, 4 cells, 1 Red, 1 Yellow, 2 Green. The Red cell is
FreeBSD-specific; not a global regression. Action before next push:
investigate FreeBSD/x86_64 schema-qualification path.
```

## MCP tool reference

- CF entry: `get_entry`, `list_entries`, `find_entries_for_author`,
  `find_entries_for_thread`, `entry_history`, `entry_branches`,
  `recent_commitfest_activity`, `commitfest_stats`
- cfbot / build status: `get_patch_build_history`, `find_failing_patches`,
  `find_rebase_needed_patches`, `find_passing_long_pending`,
  `find_patches_by_platform_status`, `build_status_freshness`
- Buildfarm cross-check: `commit_buildfarm_status`, `buildfarm_overview`,
  `find_breaks`, `list_animals`, `get_animal`, `animal_history`,
  `find_failing_runs`, `find_entries_with_failures_on`,
  `animal_owner_contributions`

## Failure modes

- **CF entry recently moved to next CF**: the `cf_id` you have may now
  reference an entry whose history is split. Use `entry_history(cf_id:
  <id>)` to find the lineage and report on all linked entries (the
  `entry_history` call walks the join across commitfests; see the
  `entry_history` entry at <https://pg.ddx.io/mcp-tools>).
- **cfbot offline / lagging**: `build_status_freshness` flags this. Don't
  produce a confident matrix in that case; report `Unknown (cfbot lag
  Xh)` for every cell and stop.
- **Author with > 20 entries**: the matrix becomes unreadable. Default
  cap at 10 entries and surface "N more truncated; pass `cf_ids` to
  filter".
- **Patch that's master-only but the entry's `entry_branches` lists
  back-branches**: `(n/a)` rather than Green for those columns. Don't
  fabricate runs that don't exist.
- **Mixed-success runs on the same `(branch, platform)` pair within the
  freshness window**: classify as `flake` and surface both runs. Do not
  discard the older one to make the matrix look cleaner.
- **Buildfarm-only red, cfbot all green**: this is the high-value find.
  Surface emphatically — a patch can pass cfbot and still break a
  buildfarm animal because cfbot's platform coverage is narrower. Chain
  to `buildfarm-blame.md` for the post-commit diagnosis path.
- **Patches with cfbot in `errored` for > 3 cycles**: usually a cfbot
  driver bug, not a patch bug. Note as `infra`; do not pester the
  author.

## Sources

- pg.ddx.io MCP tool reference: <https://pg.ddx.io/mcp-tools> —
  authoritative names + parameters for every verb cited above.
- commitfest.postgresql.org — surface UI; the "Cfbot status" column shown
  per entry is the data this skill consumes.
- cirrus.ci.postgresql.org — cfbot's CI runner; failure logs live there
  and are linked from `get_patch_build_history`'s `log_url` field.
- buildfarm.postgresql.org — the master-branch CI grid; complementary to
  cfbot. Each animal has `animal_history` and `find_failing_runs`.
- Cross-reference: `community/conventions/git-workflow.md` § "Tracking
  what's on master" — useful when correlating a buildfarm break with a
  recent merge.
- Cross-reference: `community/conventions/committing-checklist.md`
  § "Watch the buildfarm" — what a committer monitors after pushing
  (this skill is the author-side equivalent before pushing).
- Cross-reference: `generic/workflows/rebase-feature-branch.md` —
  invoked when classification yields `rebase-needed`.
- Cross-reference: `generic/workflows/buildfarm-blame.md` — invoked
  when a buildfarm animal goes red and the question shifts from "is my
  patch healthy?" to "did my patch (or someone else's) break X?".
- Cross-reference: `generic/workflows/fetch-patch-test.md` — invoked
  when classification yields `genuine-regression` and the next step is
  to reproduce locally.
- Wiki: <https://wiki.postgresql.org/wiki/Cfbot> — what cfbot tests, how
  often, on which platforms.

## Example

Input: `author_email = greg.burd@example.org`.

```
find_entries_for_author(name_or_email: "greg.burd@example.org", limit: 50)
# → 3 entries: #4521 (Needs Review), #4612 (Needs Review),
#              #4488 (Waiting on Author).

# Skip #4488 (Waiting on Author = author-side block, not cfbot drift).

# For each remaining entry:
get_entry(entry_id: 4521)
entry_branches(cf_id: 4521)
get_patch_build_history(entry_id: 4521, limit: 30)
# → master/Linux green, master/FreeBSD red (regression.diffs)

get_entry(entry_id: 4612)
entry_branches(cf_id: 4612)
get_patch_build_history(entry_id: 4612, limit: 30)
# → all platforms green, last ran 2h ago.

build_status_freshness()
# → cfbot 2h lag. OK.

commit_buildfarm_status(commit_sha: "<current origin/master>")
# → 1 animal red: dragonet (s390x).
find_breaks(since: "<7 days ago>", limit: 10)
# → dragonet broke at <unrelated sha>; not author's.

recent_commitfest_activity(since: "<7 days ago>", limit: 100)
# → 14 entries updated. None overlap with author's patches.
```

Output:

```
2 active entries; 1 Red cell, 1 Yellow lag flag, 7 Green.

CF #4521 — "Event trigger for sequence change"
  master/FreeBSD: Red — schema-qual regression. Action: chain
  fetch-patch-test.md to reproduce locally.

CF #4612 — "Hash partitioning for foreign tables"
  All Green. No action.

Buildfarm: dragonet (s390x) red on master, but unrelated to either
entry's diff (broke at upstream sha <X>). No action for author.

Aggregate: push v8 of #4521 only after fixing FreeBSD case; #4612 is
fine to leave.
```

## Tips

- Run before every push. Two-minute cost; saves a re-roll if a sister
  entry just went red.
- Watch for **Yellow stale** as much as Red. A platform that hasn't
  reported in 48h often means cfbot's runner for that platform is down;
  a green-stale cell is not the same as a green-fresh cell.
- The `find_entries_for_author` lookup matches on email substring; a
  contributor with multiple email addresses (work + personal) needs two
  queries, one per address. Aggregate the results in the output.
- Don't trust a single run. cfbot has known flakes (e.g. `pg_basebackup`
  occasionally times out on overloaded runners). Look at the **last
  three** runs for a `(branch, platform)` pair before classifying; the
  decision tree's `flake` rule depends on this.
- The output is meant to be paste-able into an email reply. Keep it tight;
  if the matrix grows past 50 cells, attach as a file and summarize in
  prose.
