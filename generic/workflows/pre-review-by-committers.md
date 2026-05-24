# Workflow: Pre-Review a Patch By Simulating Canonical Committers

Have the LLM role-play 3 or more PostgreSQL committers and produce each one's likely review of a patch, commit, or branch. Output is structured so the author can address obvious objections before posting to -hackers, where real reviewers are slow and finite.

## Goal

Produce a pre-flight review report that approximates the kinds of concerns three or more well-known committers tend to raise on patches in their area, citing each insight back to the voice file that informed it.

## Inputs

One of:

- `patch_file_path` — local path to a unified-diff `.patch` file.
- `commit_sha` — a SHA in the local clone of postgres.git or accessible via agora's `git_show_file`.
- `branch_name` — a local branch (the diff is `git merge-base origin/master <branch>..` to `<branch>`).
- `message_id` — a -hackers Message-ID whose attached patch should be fetched via agora.

## Outputs

A markdown report with:

- **Patch summary** (3–6 lines): files touched, lines added/removed, primary subsystem.
- **Reviewer simulations** (one section per voice, 3+ voices):
  - Likely concerns (drawn from the voice file's "common patterns" or "recurring advice" section)
  - Questions they typically ask
  - Suggestions in their style
  - Each insight cites the voice file path AND a specific section anchor or message-id.
- **Synthesis section**:
  - Areas all reviewers agree on (high-confidence issues)
  - Areas where the reviewers diverge (judgment calls; surface them)
  - Top 3 things to fix before sending the patch to -hackers
- **Disclaimer** (mandatory, top of file): this is a stylistic simulation, not real review. Real committer reviews routinely surface things this skill won't catch (architectural objections, prior-art collisions, deadlock with another in-flight patch). Treat the output as a checklist, not a verdict.

## Steps

### 1. Decide whether this skill is appropriate

Skip this skill — output a one-line note instead — if any of:

- Patch is < 20 lines AND touches no header or `.sgml` or `pg_proc.dat` file (mechanical typo / comment fix).
- Patch is a translation update (`*.po`).
- Patch is a `.gitignore` / `.editorconfig` / Meson build-file-only change (review is purely mechanical).

These cases waste the simulation budget and produce no useful output.

### 2. Fetch the diff

For a commit SHA in the local clone:

```bash
git show <sha>
```

For a SHA on the indexed remote:

```
git_show_file(repo: "postgres", sha: "<sha>", path: "<file>")   # per file
git_diff(repo: "postgres", from_commit: "<sha>^", to_commit: "<sha>")
```

For a branch:

```bash
git diff $(git merge-base origin/master <branch>)..<branch>
```

For a message-id:

```
get_message(message_id: "<id>")
get_message_headers(message_id: "<id>")
get_attachment(message_id: "<id>", index: 0)   # iterate indices for multi-part patches
```

If the patch is inline in the message body (no attachment), extract the unified-diff section between `diff --git` and the message footer. If multiple patches are attached (a series), process each separately and produce one report per patch.

### 3. Classify the patch's primary subsystem

Look at the file paths touched. Map to subsystem:

- `src/backend/optimizer/`, `src/backend/parser/`, `src/include/optimizer/` → planner / parser
- `src/backend/access/transam/`, `src/backend/access/heap/`, WAL files → MVCC / WAL
- `src/backend/storage/buffer/`, `src/backend/storage/lmgr/`, atomics, lwlocks → concurrency / perf
- `src/backend/replication/`, `src/backend/access/transam/xlog*` → replication / WAL
- `src/backend/statistics/`, partition pruning, parallel-query planning → statistics / partitioning
- `src/backend/postmaster/`, `meson.build`, `configure.ac`, `src/include/port/` → build / portability
- `src/backend/access/nbtree/`, `src/backend/access/gin/`, `src/backend/access/spgist/` → indexes

Classification picks the **topic-relevant** voice in step 4.

### 4. Select 3+ voices to simulate

**Default triplet** (always present):

- `community/voices/tom-lane.md` — planner correctness, type-system invariants, code-review philosophy ("don't reformat unrelated code", "preserve git history"). Always relevant; Tom reviews everything.
- `community/voices/andres-freund.md` — performance, lock-free / atomics, async I/O, NUMA. Relevant for any change touching hot paths.
- One **topic-relevant** voice from the list below.

**Topic-relevant additions** (pick at least one; pick more if the patch spans subsystems):

- `community/voices/tomas-vondra.md` — extended statistics, partition pruning, parallel-query costing.
- `community/voices/heikki-linnakangas.md` (or `voices/index.md#heikki-linnakangas` if folded) — WAL, MVCC, recovery, replication.
- `community/voices/peter-eisentraut.md` (or `voices/index.md#peter-eisentraut` if folded) — build system, locale, ICU, libpq, SQL standard conformance.
- `community/voices/robert-haas.md` — parallel query, project-process commentary, "what the project values".
- `community/voices/michael-paquier.md` — TAP test discipline, regression isolation, build-system, back-patching mechanics.
- `community/voices/bruce-momjian.md` (or `voices/index.md#bruce-momjian` if folded) — release management, design overview, doc / commit-message authorship.

If the voice file you want isn't on disk yet (the content-distillation work may not have committed it), substitute the closest relative or fall back to `community/voices/index.md` with the named anchor and note the substitution in the report header.

### 5. Per-voice simulation procedure

For each selected voice file:

1. Read it. Identify its "recurring concerns" / "common patterns" / "review checklist" section.
2. For each concern that is testable against this patch, ask: does the patch trigger it? If yes, write a short paragraph in the voice's style (not parody — distilled, with one concrete suggestion). If no, skip it; do not pad.
3. Cite the voice-file section and, where the voice file itself cites a message-id, cite that too. Pattern:
   ```
   > _Insight derived from `community/voices/tom-lane.md` § "Don't touch unrelated code" — citing pgsql-hackers <12345.1234567890@sss.pgh.pa.us>_
   ```
4. End the section with the single highest-priority question this voice would ask. Frame as a question, not an assertion.

### 6. Cross-reference against archive — does this patch already have history?

```
search(query: "<patch's central concept>", inbox: "pgsql-hackers", limit: 10)
find_related_discussions(query: "<patch's central concept>")
```

If there is prior art (someone has proposed something similar before), surface it in the report. A common reason real reviewers reject a patch is "we already discussed this in 2019; here's why we didn't do it." Pre-empting that is high-value.

```
get_thread(message_id: "<earlier-thread-anchor>")
```

### 7. Cross-reference against the live commitfest

If the patch is an in-flight CF entry, check whether the same author has other entries currently failing — sometimes a reviewer will redirect attention if a previous version of the same idea is still red:

```
find_entries_for_author(name_or_email: "<author>")
get_entry(entry_id: <N>)
get_patch_build_history(entry_id: <N>)
```

### 8. Synthesize

The synthesis section answers three questions:

1. **What do all 3+ reviewers agree is a problem?** These are high-confidence; fix before submitting.
2. **What does one reviewer flag that another doesn't?** Judgment calls. Document the disagreement; let the author decide.
3. **What did none of the reviewers think to ask?** This is the honest part: list 1–3 things you (the agent) noticed that don't fit any voice's pattern. Flag them as "agent observations, not voice-derived."

### 9. Compose the report

Top of report (mandatory):

```
> SIMULATION DISCLAIMER. This is a pattern-matched approximation of canonical
> committers' review styles. It is not a substitute for real review on
> -hackers. Do not cite this report on the mailing list as if a committer
> said it. Treat it as a checklist of likely objections to address
> proactively.
```

Then patch summary, then per-voice sections, then synthesis, then disclaimer footer with voice-file paths cited.

## MCP tool reference

- Patch fetch: `get_message`, `get_message_headers`, `get_attachment`, `git_show_file`, `git_diff`
- Prior-art search: `search`, `find_related_discussions`, `get_thread`, `find_similar_messages`
- CF context: `find_entries_for_author`, `get_entry`, `get_patch_build_history`

## Failure modes

- **Mechanical patch.** Skip per step 1.
- **Voice file missing.** Note substitution; do not fabricate the voice. If no relevant voice file exists at all, output the report with only the default triplet plus an "agent-observations" section, and flag in the report header that topic-relevant simulation was skipped.
- **Patch touches everything.** A 5000-line patch across 50 files defeats voice-by-voice review; chunk the patch into per-subsystem hunks first and run this skill once per chunk.
- **No prior art found.** Don't say "this is novel" — say "no prior discussion located in agora's index" and note that pre-2010 mail might not be reachable.
- **Disclaimer absence.** If you forgot the disclaimer, the report is unusable. Always include it.

## Sources

- `community/voices/*.md` (per-committer distillations)
- `community/voices/index.md` (umbrella file for voices not given a separate file)
- `community/review-standards.md` (project-wide review norms — supplements the voice-specific patterns)
- `community/common-pitfalls.md` (patterns that any reviewer would flag)
- Existing skill: `generic/workflows/review-thread-context.md` (chain to it when reviewing a patch that already has -hackers replies)

## Example

Input: a commit SHA on a feature branch that adds a new GUC controlling buffer-eviction batch size.

```
# 1. Classify
git show <sha> --stat
# Files: src/backend/storage/buffer/freelist.c, src/include/storage/buf_internals.h,
#        src/backend/utils/misc/guc_tables.c, doc/src/sgml/config.sgml
# Subsystem: concurrency / perf + GUC + docs

# 2. Voices
# Default triplet: tom-lane (always), andres-freund (perf), heikki-linnakangas
#                  (buffer manager / WAL adjacency)
# Topic-relevant addition: peter-eisentraut (GUC + doc patterns)

# 3. Per-voice
# Tom Lane (community/voices/tom-lane.md):
#   - Concern: GUC name discoverability ("the GUC name doesn't say what it does")
#   - Concern: "make sure pg_settings shows the right unit"
#   - Question: "does this need a postgresql.conf.sample sync? did you bump it?"
#
# Andres Freund (community/voices/andres-freund.md):
#   - Concern: "show me a perf number, not a benchmark; what was the contention before?"
#   - Concern: "is the eviction batch size a hot constant? consider USE_PREFETCH gating"
#   - Question: "did you measure on a NUMA box with > 32 cores?"
#
# Heikki (community/voices/heikki-linnakangas.md or voices/index.md#heikki-linnakangas):
#   - Concern: "what happens if BgBufferSync is in the middle of a sweep?"
#   - Concern: "interaction with bgwriter_lru_maxpages — is that GUC now redundant?"
#   - Question: "did you run pgbench with checkpoint_timeout=30s to trigger sync hard?"
#
# Peter Eisentraut (community/voices/peter-eisentraut.md or voices/index.md#peter-eisentraut):
#   - Concern: "the doc patch describes the *what* but not when to tune"
#   - Concern: "is the GUC unit annotated? check src/backend/utils/misc/guc_tables.c"
#   - Question: "did you add a regression test that exercises non-default values?"

# 4. Prior art
search(query: "s:buffer eviction batch", inbox: "pgsql-hackers", limit: 10)
# Found one thread from 2022: "Buffer eviction throughput on NUMA hardware."
# Result was inconclusive; surface in the report so author can either cite or
# distinguish.

# 5. CF check
find_entries_for_author(name_or_email: "<author>")
# Author has 2 other CF entries; 1 is currently failing on cfbot. Note in report.

# 6. Synthesis
# Agreement: needs perf numbers (Andres + Heikki agree); needs doc tuning guidance
#            (Peter); needs postgresql.conf.sample sync (Tom).
# Divergence: Tom is fine with GUC name; Peter would rename to bear the unit.
# Agent observation: there is no test covering the GUC-equals-zero edge case.
```

Output: a 200-300 line markdown report. The author reads it in 5 minutes and fixes 4 of the 8 issues before sending to -hackers, where the next round of review now hits architecture (which this skill cannot simulate) instead of style (which it can).

## Tips

- Don't include voice quotations longer than 2 lines. The voice files cite exact message-ids; link to the message-id rather than reproducing prose.
- Resist the urge to score the patch (e.g. "B+"). Real review doesn't grade; it surfaces specific issues.
- Run this skill before, not after, you write tests. The simulated reviews often demand specific tests; writing those tests first wastes effort.
- The synthesis section is where the value is. If you only have time to read one section, read that.
