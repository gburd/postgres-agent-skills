# Workflow: Fetch a Patch from a Message-ID, Apply, Build, Test, Review

End-to-end reviewer workflow: pull a patch from a -hackers message, set up a
worktree, apply, configure, build, run regression tests, run a high-level
review checklist, and emit a structured report the reviewer can paste back
to the thread. What used to be a 30–60-minute manual ritual becomes a
5–10-minute interactive session.

This is the reviewer-side companion to `submit-patch.md` (author side) and
`pre-review-by-committers.md` (simulated review). Use it whenever you
volunteer to review a CF entry or a -hackers patch attachment.

## Goal

Given a `message_id` (or a postgr.esq URL), produce:

1. A working directory containing the patch applied to a clean worktree.
2. A build + test fingerprint proving the patch compiles and passes
   regression.
3. A structured review report covering doc updates, test coverage,
   coding-standard compliance, commit-message shape (if present), and
   reviewer comments suitable for posting back to the thread.

## Inputs

- `message_id` — a -hackers Message-ID (the canonical anchor). Examples:
  `<CAEze2WgX...@mail.gmail.com>`,
  `<20260520123456.foo@bar.example>`.
- OR `postgresql_url` — `https://postgr.esq/m/<msg-id>` or
  `https://www.postgresql.org/message-id/<msg-id>`. Strip to the bare ID.
- `cf_id` (optional) — if the patch is associated with a CF entry, pass
  this so the report cross-references cfbot status.

Optional:

- `worktree_dir` — defaults to `/scratch/cfreview-<short-id>` or
  `${TMPDIR:-/tmp}/cfreview-<short-id>` if `/scratch` is unavailable.
- `configure_args` — additional flags. Default below is minimal-debug.
- `keep_worktree` — `true` (default) to leave the worktree for further
  digging, `false` to clean up after the report.

## Outputs

A markdown report with:

- **Patch metadata**: subject, author(s), date, thread anchor, attachment
  filename(s), CF entry ID if known.
- **Apply status**: clean / fuzzed / failed-with-conflicts.
- **Build fingerprint**: configure flags, build status, first 20 lines of
  any error.
- **Test fingerprint**: per-suite pass/fail, list of failing tests, link to
  `regression.diffs` if any.
- **Review checklist**: per-item pass/fail with one-line evidence each.
- **Reviewer comments**: a draft block ready to paste into the -hackers
  reply, in the project's review style (concrete, file:line-cited, no
  grades).
- **Cleanup status**: worktree retained at `<path>` or removed.

## Steps

### 1. Resolve the message-id and fetch the message

Strip URL prefixes (`https://postgr.esq/m/`,
`https://www.postgresql.org/message-id/`, etc.) to the bare ID.

```
get_message(message_id: "<id>")
get_message_headers(message_id: "<id>")
```

Capture: subject, From, Date, In-Reply-To, References (for thread anchor),
attachment list. If the message has no attachments AND its body has no
inline diff, walk the thread for the patch:

```
get_thread(message_id: "<id>")
```

Pick the latest message in the thread that has a `.patch` attachment —
v-numbered series convention means the highest `vN-` prefix is the
intended target.

### 2. Fetch the patch attachment(s)

```
get_attachment(message_id: "<patch-bearing-id>", index: 0)
# iterate index for multi-part attachments
```

If the patch is inline in the body (no attachment), pull the raw message
and extract the `diff --git ... ` to end-of-diff section:

```
get_raw_message(message_id: "<id>")
```

For a v-numbered series (e.g. `v7-0001-…patch`,
`v7-0002-…patch`), apply in order. Save attachments to
`$WORKTREE/../patches/`:

```bash
WORKTREE="${worktree_dir:-/scratch/cfreview-$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$(dirname "$WORKTREE")/patches"
# Save each attachment to a numbered file in that dir.
```

If `/scratch` is not present, fall back to `$TMPDIR` (per global workflow
notes — `/tmp` is RAM-backed and a `make check` run can fill it).

### 3. Identify the patch's claimed base

Many recent patches carry a base SHA in the cover letter or the first
patch's commit message ("Rebased onto <sha>" / "Applied on top of
<sha>"). Read the message body for that hint:

```
get_message(message_id: "<id>")
```

If found, use it. Otherwise default to `origin/master` and fetch fresh:

```bash
( cd "$POSTGRES_GIT" && git fetch origin )
BASE_REF="origin/master"
```

### 4. Create a worktree

```bash
git -C "$POSTGRES_GIT" worktree add "$WORKTREE" "$BASE_REF"
cd "$WORKTREE"
```

`git worktree add` is non-destructive — it doesn't touch your main
clone's HEAD. The worktree is disposable and can be removed at the end
without affecting the source repo.

### 5. Apply the patch series

For a single `.patch` from `git format-patch`:

```bash
git am --keep-cr "$WORKTREE/../patches/v7-0001-foo.patch"
git am --keep-cr "$WORKTREE/../patches/v7-0002-foo.patch"
```

For a plain `.patch` (unified diff, no `From … Subject:` envelope):

```bash
git apply --check "$WORKTREE/../patches/foo.patch"
git apply           "$WORKTREE/../patches/foo.patch"
git -c commit.gpgsign=false commit -am "Applied foo.patch from <message-id>"
```

If `git am` fails:

- Capture the conflict list (file + hunk).
- Try `git am --3way` for a smarter merge.
- If still failing: stop and surface the failure with the affected
  files. The patch is unappliable; the report's `Apply status =
  failed-with-conflicts` is the load-bearing finding. Do not invent
  a resolution; the reviewer should see what the author posted, not
  what the agent guessed.

For a `git apply --reject`-needed series, refuse silently re-applying with
`--reject`; that produces `*.rej` files and a half-broken tree. Instead
surface the conflict and stop.

### 6. Configure with the project's standard reviewer flags

```bash
./configure --enable-debug --enable-cassert --enable-tap-tests \
            --without-icu \
            --prefix="$WORKTREE/install"
```

Notes:

- `--without-icu` is a *minimum* configuration; if the patch touches
  collation / locale, drop it and use the full `--with-icu` build to
  exercise that path.
- `--enable-injection-points` is not always needed but is increasingly
  expected for tests authored by Michael Paquier and similar
  committers; turn it on if the patch adds `.spec` files under
  `src/test/modules/injection_points/`.
- See `generic/workflows/build-and-test.md` for the full reviewer build
  matrix, including Meson, valgrind, and `CLOBBER_CACHE_ALWAYS`.

For Meson:

```bash
meson setup build --buildtype=debug -Dcassert=true -Dtap_tests=enabled \
    -Dprefix="$WORKTREE/install"
```

Capture the configure output (last 30 lines) — projects sometimes fail
configure rather than build, and the failure-message is the diagnostic.

### 7. Build

```bash
make -s -j"$(nproc)" 2>&1 | tee "$WORKTREE/build.log"
echo "build status: ${PIPESTATUS[0]}"
```

Meson:

```bash
ninja -C build 2>&1 | tee "$WORKTREE/build.log"
```

If build fails: capture the first error with ±10 lines context. Do not
proceed to step 8. The report's `Build = FAIL` is the load-bearing
finding.

### 8. Run the regression suite

Default scope is `make check`; for patches that touch `contrib/`,
`src/test/`, `src/bin/`, `src/pl/`, expand to `make check-world`:

```bash
make -s check 2>&1 | tee "$WORKTREE/check.log"
# or
make -s check-world 2>&1 | tee "$WORKTREE/check.log"
```

Meson:

```bash
meson test -C build --print-errorlogs --suite regress
# or all suites:
meson test -C build --print-errorlogs
```

If tests fail, capture `regression.diffs`
(`src/test/regress/regression.diffs` for autoconf, or
`build/testrun/regress/regress/regression.diffs` for Meson) and the
TAP `*.log` for any failing TAP suites. Keep them; the report links
to them.

### 9. High-level review checklist

For each item below, check `git diff --stat` and the patch contents.
Each item is `pass` / `fail` / `n/a` with one-line evidence.

#### 9.1 Doc updates

```bash
git -P log -p HEAD~..HEAD -- 'doc/src/sgml/*' | wc -l
```

Patch is `pass` if it touches `doc/src/sgml/` AND the user-visible
behavior change demands a doc update. Patch is `fail` if it adds a
GUC / catalog / SQL function / `EXPLAIN` keyword without doc. Patch
is `n/a` for purely internal refactors.

Cross-reference: `community/conventions/committing-checklist.md`
§ "Sync postgresql.conf.sample" for the GUC-specific obligation.

#### 9.2 Test coverage

```bash
git -P log -p HEAD~..HEAD -- 'src/test/regress/*' \
                             'src/test/isolation/*' \
                             'src/test/modules/*' \
                             'src/test/recovery/*' \
                             '**/t/*.pl'
```

`pass` if the patch adds tests covering the new behavior. `fail` if
the patch adds new SQL surface or new code paths without tests.
`n/a` for trivial typo / comment fixes.

#### 9.3 pgindent compliance

Run `src/tools/pgindent/pgindent` on the patch's touched C/H files
and compare:

```bash
TOUCHED_C=$(git diff --name-only HEAD~..HEAD -- '*.c' '*.h')
if [ -n "$TOUCHED_C" ]; then
    src/tools/pgindent/pgindent --check $TOUCHED_C
fi
```

`pass` if pgindent reports no diff. `fail` with the unified diff
attached otherwise. Cross-reference:
`community/conventions/pgindent.md`.

#### 9.4 Whitespace and encoding

```bash
git -P diff --check HEAD~..HEAD
LC_ALL=C grep -RnP '[^\x00-\x7F]' --include='*.[ch]' --include='*.sgml' \
                                    --include='*.pl' --include='*.pm' \
                                    --include='Makefile*' .
```

`pass` if `--check` clean and no non-ASCII in source. `fail` with
file:line offenders. Cross-reference:
`community/conventions/whitespace-and-encoding.md`.

#### 9.5 Code-comment style

Search for forbidden markers in newly added lines:

```bash
git -P diff HEAD~..HEAD -U0 | grep -E '^\+.*(//[^/]| HACK:| BUG:)' || \
    echo "no forbidden comment markers"
```

`pass` if absent. `fail` with offenders. Cross-reference:
`community/conventions/code-comments.md`.

#### 9.6 Commit-message shape

If the patch is a `git format-patch` series, each patch has a
commit message. Inspect:

```bash
git -P log --format='%H%n%s%n%n%b%n---%n' HEAD~..HEAD
```

Per `community/conventions/commit-message-format.md`:

- Subject ≤ ~70 chars, imperative mood.
- Body wrapped at ~76 chars.
- Trailers (`Author:`, `Reviewed-by:`, `Discussion:`,
  `Backpatch-through:`) where applicable.
- No `Co-Authored-By:`, no AI-tool footers.

`pass` / `fail` per patch.

#### 9.7 catversion / postgresql.conf.sample (if applicable)

```bash
git -P diff HEAD~..HEAD -- 'src/include/catalog/catversion.h'
git -P diff HEAD~..HEAD -- 'src/backend/utils/misc/postgresql.conf.sample'
```

If the patch adds catalog entries, `catversion.h` should bump (master
only; back-branches don't bump). If the patch adds a GUC,
`postgresql.conf.sample` should reflect it.
Cross-reference: `community/conventions/committing-checklist.md`.

#### 9.8 ABI considerations (back-branch only)

If the patch is targeted at a back-branch (rare for reviewer
fetch — it's usually master), check:

- No struct field reordering / addition.
- No exported function signature change.
- No `#define` value change for things in `src/include/`.

Cross-reference: `community/conventions/committing-checklist.md`
§ "ABI on back-branches".

### 10. Cross-reference cfbot if `cf_id` provided

```
get_patch_build_history(entry_id: <cf_id>, limit: 10)
build_status_freshness()
```

If cfbot disagrees with our local result (cfbot green, local red, or
vice-versa), surface the disagreement explicitly — that's a
high-value finding. Common reasons:

- cfbot uses different platforms (you tested Linux, cfbot tested
  Windows).
- cfbot rebased the patch onto a newer master; you didn't.
- The patch's claimed base SHA differs from cfbot's auto-rebase.

When in doubt, chain to `commitfest-health-watch.md` for the full
matrix.

### 11. Compose reviewer comments (paste-ready)

Draft a short block in the project's review style. Be concrete; cite
file:line. Don't grade. Frame as questions or suggestions, not
verdicts.

```
Thanks for v7.

Quick reviewer notes from local apply + check-world (no surprises in
build/test):

* doc/src/sgml/ref/foo.sgml — the new GUC `bar` is documented in
  config.sgml but doesn't appear in the SGML index for "Server
  Configuration"; would you mind adding the `<indexterm>`?

* src/backend/utils/baz.c:317 — wondering about the locking
  discipline here; we hold `XidGenLock` while calling out to
  `qux()`. Is there a reason this can't be released earlier?

* src/test/regress/sql/foo.sql adds coverage for the new behavior;
  is there a case for `SET bar = 0` to exercise the fall-back
  path?

* pgindent on baz.c reports no diff; commit-message shape per the
  project's conventions; trailing whitespace clean; no non-ASCII.

I'll plan to retest after v8.
```

Tone notes:

- Open with thanks and a short build/test status summary.
- Cite file:line, not "you should".
- Frame as questions where the reviewer might be wrong; frame as
  suggestions where the reviewer is sure.
- Sign off with what you plan to do next ("retest after v8" or
  "I think this is committable; passing to a committer").

### 12. Cleanup

Default: leave the worktree. Print:

```
Worktree retained at: <WORKTREE>
To clean up: git -C <POSTGRES_GIT> worktree remove <WORKTREE>
```

If `keep_worktree=false`:

```bash
cd "$POSTGRES_GIT"
git worktree remove --force "$WORKTREE"
git worktree prune
# Patches dir was outside the worktree; clean separately:
find "$(dirname "$WORKTREE")/patches" -mindepth 1 -delete \
  && rmdir "$(dirname "$WORKTREE")/patches" 2>/dev/null
```

Per the project workflow notes, prefer `find … -delete` over `rm -rf`
on agent-managed scratch directories.

## MCP tool reference

- Mail: `get_message`, `get_message_headers`, `get_attachment`,
  `get_thread`, `get_raw_message`, `get_message_references`,
  `get_thread_references`, `find_similar_messages`,
  `find_related_discussions`
- Patches/CF: `get_entry`, `find_entries_for_thread`,
  `get_patch_build_history`, `build_status_freshness`,
  `find_failing_patches`, `find_rebase_needed_patches`
- Git context (when investigating apply failures or upstream
  drift): `git_log`, `git_show_file`, `git_diff`, `git_blame`,
  `git_search`

## Failure modes

- **Message-id resolves but has no patch**: walk the thread (step 1
  fallback) for the latest `.patch` attachment. If still none,
  surface "no patch found in thread" and stop.
- **Patch is from > 12 months ago**: high probability of unappliable.
  Chain to `forward-port-cold-branch.md` instead.
- **Patch applies but build fails on a subsystem the reviewer
  doesn't know**: keep going through the report up to the
  build-fail line; do not attempt to fix. The report's job is to
  surface "v7 doesn't build with the project's standard reviewer
  flags" — that's actionable feedback for the author.
- **`make check` flake**: rerun once. If second run is green, note
  the flake; if red again, report failure.
- **Inline diff in message body, not attached**: extract via
  `get_raw_message`. Fence on the unified-diff format; don't parse
  HTML.
- **Multi-author / Co-author thread**: cite the original-message
  author in the report's "patch author" field; cite reviewers
  separately when known.
- **Thread is too long to read in full**: `get_thread` returns
  metadata; pull just the messages with attachments and the most
  recent 5 messages. Don't read 80 messages to write a 20-line
  report.
- **Worktree creation fails because the destination exists**:
  `git worktree add` refuses to clobber. Either pick a fresh
  `worktree_dir` or remove the stale one first via
  `git worktree remove --force`.

## Sources

- agora MCP tool definitions:
  `agora/pkg/mcp/tools.go` (mailing-list verbs),
  `agora/pkg/mcp/tools_commitfest.go`,
  `agora/pkg/mcp/tools_build_status.go` —
  authoritative names + parameters.
- `community/conventions/git-workflow.md` — `git format-patch`
  conventions, `git am` mechanics, `apply.whitespace = error`.
- `community/conventions/creating-clean-patches.md` — the standard
  the patch you're reviewing was supposed to meet.
- `community/conventions/committing-checklist.md` — what a
  committer's first-pass-after-accept will hit, the same list this
  skill folds into the review checklist.
- `community/conventions/commit-message-format.md` — what to score
  in step 9.6.
- `community/conventions/whitespace-and-encoding.md` — what to
  score in step 9.4.
- `community/conventions/code-comments.md` — what to score in
  step 9.5.
- `community/conventions/pgindent.md` — what to score in step 9.3.
- `generic/workflows/build-and-test.md` — fuller build matrix; this
  skill uses the standard reviewer subset.
- `generic/workflows/pre-review-by-committers.md` — chain *after*
  this skill if the local checks pass and you want the
  voice-simulation pass.
- `generic/workflows/rebase-feature-branch.md` — chain to it if
  apply fails because the patch's claimed base is older than
  `origin/master`.
- `generic/workflows/forward-port-cold-branch.md` — chain to it
  if the patch is > 12 months old.
- `generic/workflows/commitfest-health-watch.md` — chain to it
  for the cf-bot cross-check in step 10.
- Wiki: <https://wiki.postgresql.org/wiki/Reviewing_a_Patch> —
  the reviewer's project-norm checklist; this skill operationalizes
  it.
- Wiki: <https://wiki.postgresql.org/wiki/Submitting_a_Patch>
  § "Producing the patch" — what the patch you're applying was
  supposed to look like.
- Pre-commit hook template in
  `community/conventions/git-workflow.md` § "`.git/hooks/pre-commit`
  template" — the same checks, applied at the reviewer side.

## Example

Input: `message_id = <CAEze2Wgu...@mail.gmail.com>`,
`cf_id = 4521`.

```
get_message(message_id: "<CAEze2Wgu...>")
# → subject "[PATCH v7] event trigger for sequence change"
# → 2 attachments: v7-0001-foo.patch, v7-0002-bar.patch.

get_attachment(message_id: "<…>", index: 0)
get_attachment(message_id: "<…>", index: 1)
# Saved to /scratch/cfreview-event-trigger-seq-change/patches/

# Worktree
$ git -C "$HOME/postgres" worktree add /scratch/cfreview-… origin/master
$ cd /scratch/cfreview-…

# Apply
$ git am --keep-cr ../patches/v7-0001-foo.patch
$ git am --keep-cr ../patches/v7-0002-bar.patch
# clean

# Configure + build
$ ./configure --enable-debug --enable-cassert --enable-tap-tests \
              --without-icu --prefix="$PWD/install"
$ make -s -j$(nproc)
# OK

# Test
$ make -s check
# All 215 tests pass.

# Checklist
# 9.1 Docs:        pass — config.sgml updated for new GUC
# 9.2 Tests:       pass — src/test/regress/sql/event_trigger.sql expanded
# 9.3 pgindent:    pass
# 9.4 Whitespace:  pass
# 9.5 Comments:    pass
# 9.6 Commit-msg:  pass on both patches
# 9.7 catversion:  pass — bumped
# 9.8 ABI:         n/a (master-only patch)

# CF cross-check
get_patch_build_history(entry_id: 4521, limit: 5)
# → cfbot all green except FreeBSD/x86_64 — flagged but not reproduced
#   locally; surface in report.

# Reviewer comments drafted from the synthesis. Worktree retained.
```

## Tips

- Run this skill **before** `pre-review-by-committers.md`; the local
  build/test fingerprint informs the voice-simulation. If the build
  fails locally, the voice-simulation is moot — the patch isn't
  ready for that level of review yet.
- Save `build.log` and `check.log` even on success. If a committer
  later applies the patch and it fails on their box, the logs are
  the diff between "worked here" and "broke there".
- Don't auto-clean the worktree by default. The most common reviewer
  follow-up is "let me poke at this in `psql`" — needing the
  worktree gone is rarer than needing it present.
- If apply succeeds but the patch is mechanically suspect (e.g.
  files at unexpected paths, unusual line endings), surface those
  observations in the report. They often correlate with a
  development environment the author hasn't reset to project norms.
- Prefer `make check` over `make check-world` for the *first* pass.
  If `check` fails, `check-world` adds noise. Once `check` is
  green, expand scope before posting.
- The reviewer comments block is the deliverable; everything else
  is scaffolding. Spend the most editorial care there.
