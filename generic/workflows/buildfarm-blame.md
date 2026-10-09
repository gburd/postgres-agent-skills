# Workflow: Blame the Buildfarm

Detect whether a specific commit (yours or anyone's) caused buildfarm animals
to flip from green to red, and produce a per-animal blame report with
likelihood ratings and confounding-commit lists. Use right after pushing,
right after a committer you know pushes, or when an animal owner pings the
list with "anyone want to claim this red?".

## Goal

Given a commit SHA (or a window of recent commits), identify which buildfarm
animals went `green → red` while that SHA was on master, distinguish "my
commit definitely broke this" from "my commit happened to be one of three in
the window", and surface the relevant log excerpts so the user can decide
whether to write a fix, ask the animal's owner, or revert.

This skill is the post-push complement to `commitfest-health-watch.md`
(pre-push) — same data sources, opposite vantage.

## Inputs

One of:

- `commit_sha` — the SHA you suspect or want to vet. The default lens.
- `commit_range` — `<from>..<to>`, e.g. `origin/master@{yesterday}..origin/master`.
- `animal_name` — flip the question: "since when did this animal go red, and
  who's the suspect?".
- `since` — RFC3339 cutoff for "recent regressions" (default: 48 hours).

Optional:

- `branches` — restrict to `master`, `REL_18_STABLE`, etc. Default: all
  branches the buildfarm tracks for that animal.
- `confounders_window` — how many commits before/after the suspect SHA to
  treat as potential confounders (default: 5 each side).

## Outputs

- **Suspect commit summary**: SHA, author, date, files touched, one-line
  log subject (from `git_log`).
- **Animal-by-animal blame table**:
  - Animal name + arch + OS (e.g. `dragonet / s390x / Debian sid`)
  - Last green run on this branch: SHA + timestamp
  - First red run on this branch: SHA + timestamp
  - Failing stage (`configure` / `make` / `check` / `recovery-check` /
    `tap-tests` / `pl-check`)
  - Log excerpt (5–15 lines around the first error)
  - **Blame likelihood**: `high` / `medium` / `low` / `cleared`
  - Confounder commits (other commits in `[last-green, first-red]` window)
- **Aggregate verdict**: per-suspect commit, count of animals high-blame,
  medium, low, cleared; one-paragraph paste-able summary.
- **Suggested action**: revert / write-and-post-fix / ping animal owner /
  investigate locally / ignore (clearly not us).

## Steps

### 1. Resolve the suspect to a commit context

For a SHA:

```
git_log(repo: "postgres", limit: 1, since: "2020-01-01")
git_show_file(repo: "postgres", sha: "<sha>", path: "<each touched file>")
git_diff(repo: "postgres", from_commit: "<sha>^", to_commit: "<sha>")
```

Local equivalent if you have a clone:

```bash
SHA="<sha>"
git -P show --stat "$SHA"
git -P log -1 --format='%H%n%an <%ae>%n%ad%n%s' --date=iso "$SHA"
TOUCHED=$(git diff-tree --no-commit-id --name-only -r "$SHA")
```

For a range, walk it:

```bash
git -P log --oneline "$RANGE"
```

For an `animal_name` input (the "since when?" angle), defer to step 3 and
work backwards from the animal's history.

### 2. Pull the buildfarm context for that commit

```
commit_buildfarm_status(commit_sha: "<sha>")
```

Returns the per-animal results for runs that included this SHA (animals
test specific master tips; some runs picked up your SHA, some didn't).
Each row gives `{animal, branch, status, stage, snapshot}`.

For a global picture:

```
buildfarm_overview()
find_breaks(since: "<since>", limit: 50)
```

`find_breaks` is the highest-yield single call: it returns
animal-and-branch pairs that flipped from green to red recently, with
the SHA each was running at the time of break. Match that SHA against
your suspect SHA (or the SHA window).

### 3. Walk each red animal's history backward

For each animal that `find_breaks` flagged, or each animal listed red in
`commit_buildfarm_status`:

```
animal_history(name: "<animal>", limit: 50)
find_failing_runs(animal: "<animal>", limit: 30)
get_animal(name: "<animal>")
```

`animal_history` lists the animal's runs in reverse chronological order
with `{snapshot_sha, branch, status, stage, finished_at}`. Walk back
until you find the most-recent `success` row for the same branch — that
SHA is the **last-known-green commit**. The first failing row after it
is the **first-red commit**.

The window of suspect commits is therefore:

```
git -P log --oneline "<last-green-sha>..<first-red-sha>"
```

Anywhere from 1 to a few dozen commits, depending on how often the
animal runs.

### 4. Score the blame likelihood

For your suspect SHA in that window, score:

- **high**: window contains exactly 1 commit (your SHA), AND the failure
  stage maps plausibly to files your commit touched. E.g. red on
  `make` and your commit edited the file with the build error; or red
  on `pg_upgrade` and your commit touched `src/bin/pg_upgrade/`.
- **medium**: window contains 2–3 commits but yours is the most
  plausible match by file overlap.
- **low**: window contains > 3 commits, OR your commit's files don't
  overlap the failure area, OR the animal's history shows the same
  failure pattern intermittently (likely flake or pre-existing).
- **cleared**: the last-green-sha is *after* your SHA. You're not in
  the window. Surface this affirmatively — "your SHA was already past;
  not you" is a load-bearing finding.

Use these tools to support the scoring:

```
git_blame(repo: "postgres", path: "<file in error>",
          line_start: <N>, line_end: <M>)
```

If `git_blame` on the failing area returns your SHA, blame is `high`
even if the window had multiple commits — your line is the one tripping.

```
animal_owner_contributions(animal_name: "<animal>")
```

This tells you whether the animal's owner has personal contributions
recently — sometimes an animal goes red because the owner upgraded
their host's compiler / OS / glibc and broke before any specific
upstream commit landed. Surface that as a confounder.

### 5. Pull the failing log excerpt

`animal_history` and `find_failing_runs` rows include a `log_url` /
`stage_log` field pointing at the buildfarm log. Fetch it (HTTP) and
extract:

- The first line containing `error:`, `Error:`, `FAIL`, or
  `regression.diffs`
- ±5 lines of context

If multiple stages failed, pick the *earliest* failing stage; later
failures are usually consequences. Stage order: `configure` → `make` →
`check` → `recovery-check` → `tap-tests` → `pl-check`.

### 6. Surface confounders honestly

If your blame scored `medium` or `low`, list the other commits in the
window so the user can argue with the score. Each confounder gets:

```
- <sha-short>  <author>  <date>  <subject>
  Files: <touched files>
  Likelihood relative to suspect: <higher | similar | lower>
```

Honesty here matters — silently scoring yourself "low" without listing
the alternatives lets a real culprit hide. Equally, if the confounder
list is *empty* (window contained only your SHA), say so. That's the
strongest signal blame.

### 7. Search the archive for prior context

Often someone has already noticed:

```
search(query: "<animal-name> <stage> failure", inbox: "pgsql-hackers",
       limit: 10)
search(query: "<animal-name>", inbox: "pgsql-committers", limit: 10)
get_new_messages(inbox: "pgsql-hackers", since: "<48h ago>")
```

If a -hackers thread already names the SHA or the animal, surface the
message-id; the user may want to reply rather than start a new thread.

### 8. Compose the report

```
Suspect: <sha-short> "<subject>" (<author>, <date>)
Files touched: <count>; <top-3-files>

dragonet / s390x / Debian sid
  Last green: <sha-A> @ <date>
  First red:  <sha-B> @ <date>  (failing at: make, src/backend/utils/foo.c:142)
  Log:
        utils/foo.c:142:9: error: invalid storage class for function 'bar'
        ...
  Window (4 commits): <sha-A>..<sha-B>
    <sha-1> Tom Lane:    Refactor X (touches optimizer/)
    <sha-2> YOU:         Add bar() helper (touches utils/foo.c)  ←
    <sha-3> Author Q:    Doc fix (touches sgml/)
    <sha-4> Author R:    Test addition (touches regress/)
  Blame: high. utils/foo.c:142 directly on your commit per git_blame.
  Suggested action: write fix; reply on -hackers (no existing thread found).
```

For `cleared` rows:

```
copperhead / amd64 / FreeBSD 14
  Last green: <sha-X> @ <date>  (after your suspect)
  First red:  <sha-Y> @ <date>
  Blame: cleared. Not you.
```

Aggregate verdict, paste-able:

```
1 animal high-blame (dragonet/s390x), 0 medium, 1 low (calliphoridae —
broken pre-existing per archive thread <message-id>), 8 cleared.
Action: prepare s390x fix for dragonet; nothing else owed.
```

## MCP tool reference

- Buildfarm: `list_animals`, `get_animal`, `animal_history`,
  `find_failing_runs`, `find_breaks`, `commit_buildfarm_status`,
  `animal_owner_contributions`, `buildfarm_overview`
- Cross-reference with cfbot: `find_entries_with_failures_on`,
  `find_failing_patches`, `get_patch_build_history`
- Git: `git_log`, `git_show_file`, `git_diff`, `git_blame`, `git_search`
- Archive: `search`, `get_new_messages`, `get_thread`, `get_message`,
  `find_related_discussions`

## Failure modes

- **Animal hasn't run since suspect SHA**: blame is `unknown`, not
  `cleared`. Surface as "no run yet"; don't infer green.
- **Animal flapping**: green / red / green / red within the window.
  Likely flake or hardware issue; downgrade blame to `low` and surface
  the flap pattern.
- **Branch-specific break**: a commit might break `REL_17_STABLE` but
  not `master` because the back-branch lacks an upstream fix. Always
  check per-branch; don't collapse.
- **Archive lag**: `find_breaks` indexes from buildfarm posts; if the
  buildfarm itself is delayed, recent breaks may not be indexed yet.
  Cross-check `buildfarm_overview` for animals currently red and
  compare counts.
- **Owner-induced break**: animal owners sometimes upgrade their host
  OS or compiler; a pre-existing pattern of `configure` failures or
  weird linker errors on a single animal often points to host drift,
  not commit drift. `animal_owner_contributions` and `get_animal`
  give the host-side fingerprint.
- **Pre-existing red animal**: if `find_breaks`'s `last-green` for an
  animal is from > 14 days ago, that animal is chronically red; don't
  attribute new commits' redness to them. Surface as "long-pending
  red, not commit-induced".
- **Confounder is hidden behind a merge / squash**: PostgreSQL's master
  is linear (no merge commits — see
  `community/conventions/git-workflow.md` § "Rebase-and-squash, not
  merge"), so this is rare. But a single linear commit can carry
  many logical changes; a `git_blame` on the failing line is the
  decisive disambiguator.

## Sources

- pg.ddx.io MCP tool reference: <https://pg.ddx.io/mcp-tools> —
  authoritative names + parameters for every verb cited above.
- buildfarm.postgresql.org — the per-animal status grid; failure logs
  here back the `log_url` field returned by `animal_history` and
  `find_failing_runs`.
- Andrew Dunstan, "Pluggable buildfarm client" (the buildfarm
  framework owners and host-OS configuration are documented at
  <https://buildfarm.postgresql.org/cgi-bin/show_status.pl>; per-animal
  config visible in `get_animal` response).
- Cross-reference: `community/conventions/committing-checklist.md`
  § "Watch the buildfarm" — the committer-side norm. This skill is
  the agent's automation of that step.
- Cross-reference: `community/conventions/commit-message-format.md`
  — the `Reported-by:` and `Reviewed-by:` trailers used in the
  follow-up fix commit you may need to write.
- Cross-reference: `generic/workflows/commitfest-health-watch.md` —
  the pre-push complement; this skill is invoked after the push, that
  one before.
- Cross-reference: `generic/workflows/rebase-feature-branch.md` —
  invoked when the buildfarm break is "your branch fell behind master
  and the merge skew bit you" rather than "your commit caused this".
- Cross-reference: `generic/workflows/research-and-connect-dots.md` —
  invoked when blame requires understanding the area's recent design
  history (e.g. "this animal has been red since a 2024 atomics
  refactor"), not just commit-level diffs.
- Cross-reference: `community/voices/andres-freund.md` § "performance
  methodology" — relevant when the failing stage is a performance /
  recovery test, not a unit test.
- Wiki: <https://wiki.postgresql.org/wiki/PostgreSQL_Buildfarm_Howto>
  — what the animals are, what they test, how to interpret the grid.

## Example A: did my commit break anything?

Input: `commit_sha = b1f14c96720`, the SHA you just pushed.

```
commit_buildfarm_status(commit_sha: "b1f14c96720")
# → dragonet/master red, calliphoridae/master red, others green.

find_breaks(since: "48h", limit: 30)
# → dragonet flipped green→red between <a>..<b1f…> on master.
#   calliphoridae flipped at <c>..<d>, BEFORE b1f14c96720.

# dragonet:
animal_history(name: "dragonet", limit: 30)
# Window: 1 commit.  Window content: just b1f14c96720.

git_blame(repo: "postgres",
          path: "src/backend/utils/foo.c",
          line_start: 142, line_end: 142)
# → returns b1f14c96720.  Blame: high.

# calliphoridae:
animal_history(name: "calliphoridae", limit: 30)
# Last green: <c>; first red: <d>.  b1f14c96720 came AFTER <d>.
# Blame: cleared.

search(query: "calliphoridae make check failure",
       inbox: "pgsql-hackers", limit: 5)
# → existing thread <msgid>; owner is investigating.
```

Output: 1 high (dragonet), 1 cleared (calliphoridae), 0 medium/low.
Action: write s390x fix for dragonet's `utils/foo.c:142`. Don't worry
about calliphoridae; not you, owner is on it.

## Example B: when did this animal go red?

Input: `animal_name = pademelon`.

```
animal_history(name: "pademelon", limit: 100)
# Walk: green..green..green..RED at <sha-X>.  Last-green: <sha-W>.

git -P log --oneline "<sha-W>..<sha-X>"
# 7 commits. Pull each:

git_show_file(repo: "postgres", sha: "<each>", path: "<files>")
# 1 of the 7 touches src/backend/storage/lmgr/lwlock.c — area pademelon
# (HP-UX/IA64) is historically sensitive to.

git_blame(repo: "postgres", path: "src/backend/storage/lmgr/lwlock.c",
          line_start: <area>, line_end: <area>)
# → returns one of the 7 SHAs.

search(query: "pademelon lwlock", inbox: "pgsql-hackers", limit: 10)
# → no existing thread.
```

Output: medium-blame on commit <sha-Y>; suggested action: ping the
animal owner with the log excerpt and the candidate SHA, invite
confirmation before reverting. Owner contact via `get_animal` →
`owner` field.

## Tips

- Run within 30 minutes of pushing. Buildfarm runs are spaced (each
  animal runs every ~2-4 hours); you don't get fast feedback, but you
  also can't catch a break that hasn't happened yet. The earlier you
  notice a `high`-blame, the cheaper the fix-or-revert.
- The first failing **stage** is the diagnostic anchor. A `make` failure
  is fundamentally different from a `check` failure; don't mix them in
  the report.
- Don't trust auto-blame on platform-specific failures unless the
  failure stage is platform-relevant. A `regression.diffs` on s390x
  that names a function your patch added is high blame; a generic
  `tap-tests` timeout on the same animal is more often a host issue.
- If multiple animals red on the same SHA, group them by failure
  signature — a portability bug typically reproduces on N similar
  animals (BE / 32-bit / non-glibc), not on a random sample.
- This skill *suggests* but does not write the fix. The follow-up is
  the user's call: a one-line cast addition, a `#ifdef` guard, a
  revert request to the committer. Note the suggested action in the
  report and let the user decide.
