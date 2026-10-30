---
name: pg-patch-upkeep
description: >
  Upkeep of a PostgreSQL patch branch that is out for review: read the
  pgsql-hackers thread, the cfbot results and the branch's PR CI for anything
  that needs an answer or a fix, address it, rebase on origin/master, pass
  test-world, and force-push the branch. Use when asked to check a patch's
  thread, cfbot or CI for activity, to rebase a commitfest branch and push
  it, or to bring a patch series current before a new version.
license: CC0-1.0
metadata:
  author: ddx
  version: "0.1.0"
  persona: developer
---

# Patch upkeep

One pass over a patch branch in flight: **review** every channel, **address**
what needs it, **rebase**, **test-world**, **push**. In that order: the
activity can change the code, and the rebase and test run must cover those
changes. Every step ends on the criterion under it; a step is not done until
the criterion holds.

## 1. Identify the patch

From the branch (its name, its commits' trailers, the PR title, e.g.
`[cf-7392]`), find the commitfest entry and the thread:
`find_entries_for_thread`, `search_commitfest`, `get_entry` (pg.ddx.io), and
the PR (`gh pr list --head <branch>`). Note the date and version of your last
posted patch: activity is everything after it.

*Done when:* you hold the CF id, the thread's Message-ID, the PR number (or
"no PR"), and the cut-off date.

## 2. Review the activity

Read all three channels from the cut-off forward.

- **Thread:** `get_thread(<message-id>)` with bodies. Every message after your
  last post, including replies in sub-threads and on a re-titled thread.
- **cfbot:** `get_patch_build_history(<cf-id>)` (last three runs per
  platform), `find_rebase_needed_patches`, and `build_status_freshness` first,
  so stale green is never read as current green. The workflow
  `generic/workflows/commitfest-health-watch.md` classifies red cells (flake /
  rebase-needed / platform-specific / genuine regression / infra).
- **PR CI:** `gh pr checks <n>` and `gh pr view <n> --comments`, plus review
  comments on lines (`gh api repos/<owner>/<repo>/pulls/<n>/comments`). For a
  failed job, read the failing step's log (`gh run view <run> --log-failed`).
- **Entry status:** `entry_history(<cf-id>)`. A flip to *Waiting on Author* is
  activity even with no message.

List each item as an **activity** row: who, when, what they asked or what
failed, and a link or Message-ID. Activity is anything that asks the author to
change, explain or decide: a review point, a question, a failure, a competing
or overlapping patch, a committer's design note, a status change. Thanks and
+1s are not activity.

*Done when:* every message, cfbot run and CI run after the cut-off is either a
row or was read and judged not activity.

## 3. Address it

Give every row one **disposition**:

- **fixed**: a code change, made in the commit of the series it belongs to
  (`git commit --fixup` + `git rebase -i --autosquash`), never as a trailing
  "address review" commit;
- **reply**: an answer drafted to a file for the human to send, quoting the
  point it answers (agents never send mail; see `postgres/developer`
  § Submission);
- **decision**: a design choice for the human, framed with the options and
  their cost;
- **no action**: with the reason (already fixed upstream, a cfbot flake shown
  in its run history, a misreading answered in a reply).

A failure called "not ours" needs a control: the same failure on origin/master
without the patch, or in cfbot's history for unrelated entries.

*Done when:* every row has a disposition and every **fixed** row names its
commit.

## 4. Rebase

```bash
git fetch origin
lease=$(git rev-parse origin/<branch>)   # what the push may replace (step 6)
git rebase origin/master
```

Follow `generic/workflows/rebase-feature-branch.md` for conflicts: resolve the
trivial ones citing the upstream commit that caused each, and stop and ask on
any semantic conflict. Then build every commit of the series on its own
(`git rebase --exec 'ninja -C build' origin/master`, or `make -s`), as
`postgres/developer` requires.

*Done when:* the branch sits on the fetched origin/master, the tree is clean,
and every commit builds without warnings.

## 5. Test-world

Run the whole suite CI calls *Test world*, on a cassert build with TAP tests:

- meson: `meson test -C build --num-processes $(nproc) --print-errorlogs`
  (all suites; the `running` setup is a separate run);
- autoconf: `make -s check-world -j$(nproc)` after
  `./configure --enable-debug --enable-cassert --enable-tap-tests`.

A failing test blocks the push. Fix it in the series and go back to step 4's
per-commit build. A failure dismissed as pre-existing needs the same test
failing on origin/master at the same SHA (step 3's control rule).

*Done when:* test-world reports zero failures, or every failure has a
recorded failing control on origin/master.

## 6. Push

Force-push the branch only, leased on the SHA recorded in step 4, so a push
made from anywhere else since then is refused instead of overwritten:

```bash
git push --force-with-lease=<branch>:"$lease" origin <branch>
```

A refused lease means someone else pushed: fetch, look at what they pushed,
and ask before going further.

Then confirm the PR's CI started on the new head (`gh pr checks <n>`).

*Done when:* `git ls-remote origin <branch>` returns your local HEAD and CI is
running on it.

## Report

End with: the activity table and each row's disposition; drafted replies
(paths); decisions waiting on the human; the rebase summary (old and new base,
conflicts and the upstream commits behind them); the test-world command and
result; the pushed SHA and the CI run. If the series is ready for a new
version, say so and leave `git format-patch` output and a cover-letter draft
for the human to send.
