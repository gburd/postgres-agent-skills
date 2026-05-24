# Workflow: Gain Perspective Before Committing to an Idea

Before you spend a week on a feature proposal or a refactor, take 30 minutes
to ask the archive whether the idea is fresh, has prior art, has been
rejected, has been superseded, or sits squarely in a committer's "I've said
no to this twice already" zone. The output is a perspective brief — not a
yes/no verdict, but the historical context you'd want a senior contributor
to whisper in your ear before you start typing.

This is the inverse of `pre-review-by-committers.md`: that skill simulates
review *of code you've written*; this skill simulates committer reaction *to
an idea you're considering*, before any code exists.

## Goal

Given an idea ("add a GUC for X", "rewrite planner module Y", "expose
internal API Z"), produce a one-page brief that lists prior proposals on the
same topic, names the committers most likely to weigh in, summarizes likely
objections from their voice files, lists common pitfalls, and recommends
concrete first steps that respect the project's process — typically "post a
design email to -hackers BEFORE writing code", not "open a coding session".

## Inputs

- `idea` (required): a free-form description of what you want to do. One to
  three sentences. Examples:
  - "Add a GUC `enable_seqscan_parallel` to force parallel sequential scans."
  - "Rewrite the planner's join-order search to use simulated annealing
    even at low join counts."
  - "Expose `LWLockAcquire` to extensions via a stable ABI."
- `area_hint` (optional): subsystem name if you already know it. Speeds up
  voice selection.
- `effort_budget` (optional): how much work you're contemplating ("a
  weekend", "a month", "a year"). Calibrates the brief — a weekend's worth
  of work doesn't need the full design-review treatment, but a year's
  worth absolutely does.

## Outputs

- **Idea normalization**: one-paragraph restatement of the idea in
  PostgreSQL-canonical vocabulary. (Drift between user phrasing and
  project terminology is a frequent source of false-negative archive
  searches; the normalization step exposes it.)
- **Prior art**: 3–10 historical proposals on the same or adjacent
  topics, each with:
  - Year + thread anchor message-id
  - One-line outcome (`accepted+committed` / `accepted+different-design`
    / `consensus-no` / `dropped-by-author` / `still-discussing`)
  - One-line takeaway: what the project decided and why
- **Likely committer reactions**: 2–4 voices with their likely framing
  of this idea (drawn from `community/voices/` files), each with one
  concrete prediction of what they'd ask. **Mandatory disclaimer** —
  these are stylistic simulations, not real committer statements.
- **Common pitfalls** specific to this kind of idea (drawn from
  `community/conventions/` and the prior-art outcomes).
- **Suggested first steps**: 3–5 numbered actions, ordered. Almost
  always the first step is "write a design email, not code".
- **Should-you-bother verdict**: one of `proceed-with-design-post`,
  `proceed-with-prototype-and-design-post`, `pause-research-more`,
  `redirect-to-related-effort`, `likely-rejected-on-historical-grounds`.
  This is a recommendation, not a prohibition; the user decides.

## Steps

### 1. Normalize the idea

Restate the idea using project terminology. Drift catches:

- "make X faster" → "reduce contention on the X lock" or "avoid full
  table scan during X"
- "expose Y to plugins" → "extend the hook API for Y" or "publish a
  stable ABI for Y"
- "make Z transactional" → "WAL-log Z" or "give Z proper visibility
  semantics"

When in doubt, search both the user's phrasing AND the project's
phrasing in step 2; if they return wildly different hits, the
normalization needs more work and you should surface both
phrasings to the user.

### 2. Foundation: full multi-source research pass

Run the entire `research-and-connect-dots.md` workflow on the
normalized idea. The output of that skill — a chronological timeline
of mailing-list / git / wiki / docs / code-symbol mentions — is the
**foundation** of this skill. Do not duplicate the research mechanics
here; chain to that skill and consume its result.

In particular, read and capture:

- The wiki + docs landscape (existing coverage of the idea, if any).
- The first mailing-list mention and its outcome.
- Recent activity in the area (last 12 months).
- The central code symbols (`get_symbol`, `get_callers`,
  `get_callees`).

If `research-and-connect-dots.md` produced a "what to read first"
trio, that trio anchors the prior-art section of this brief.

### 3. Search specifically for "this exact proposal, before"

The previous-step research pass is broad. Now run a narrow,
proposal-shaped search:

```
search(query: "s:<normalized phrasing>", inbox: "pgsql-hackers", limit: 30)
search(query: "s:<user's phrasing>", inbox: "pgsql-hackers", limit: 30)
hybrid_search(query: "<idea in plain English>", limit: 30)
find_related_discussions(query: "<idea>")
```

Sort hits by date ascending. For each hit that looks proposal-shaped
(an opening message that says "I propose to add…", "RFC", "PoC",
"$x patch", "WIP"), pull the thread:

```
get_thread(message_id: "<anchor>")
get_message(message_id: "<anchor>")
```

Determine the outcome by skimming the thread tail (last few messages):

- **accepted+committed**: thread ends with "committed as <sha>" or
  the agent finds the commit via `git_search`. Best case for you —
  someone else already did it, you should learn from their patch and
  use it.
- **accepted+different-design**: a different patch landed on the same
  problem. Read the committed approach; your idea may now be moot, or
  may have a new angle.
- **consensus-no**: a committer or a chorus said no with reasons. Read
  the reasons. Most "no"s are surface-rationale ("we tried X, it
  performs worse than Y on Z workload") that the agent can quote
  faithfully back to the user.
- **dropped-by-author**: thread petered out without conclusion.
  Sometimes the author lost interest, sometimes they hit a wall.
  Read the last 3–5 messages — the wall is usually visible.
- **still-discussing**: active commitfest entry now. Note the entry
  ID; the user may want to join the existing thread rather than
  start a new one.

```
find_entries_for_thread(message_id: "<anchor>")
get_entry(entry_id: <id>)
```

### 4. Search for "the previous time someone said no"

This is the highest-value step that this skill adds beyond
`research-and-connect-dots.md`. Run targeted searches for committer-on-idea
collisions:

```
search(query: "<idea> Tom Lane",        inbox: "pgsql-hackers", limit: 10)
search(query: "<idea> Andres Freund",   inbox: "pgsql-hackers", limit: 10)
search(query: "<idea> Robert Haas",     inbox: "pgsql-hackers", limit: 10)
get_author_messages(name_or_email: "tgl@sss.pgh.pa.us", limit: 30)
```

For each prominent committer who has commented on the area before, get
their last 3–5 messages on the topic. Quote one or two lines back to the
user — the difference between "Tom thinks this is a bad idea" (vague,
unprovable) and "Tom said in <message-id>: '\<one line>'" (specific,
verifiable) is the difference between gossip and intelligence.

### 5. Pick voices to surface, then read their files

Use the same voice-selection logic as
`pre-review-by-committers.md` § "Select 3+ voices to simulate":

- Default triplet: `community/voices/tom-lane.md`,
  `community/voices/andres-freund.md`, plus one topic-relevant voice.
- Topic mapping (from that skill's step 3 classification):
  - planner / parser → `tom-lane.md` is the lead voice
  - perf / atomics / async I/O → `andres-freund.md` is the lead voice
  - WAL / MVCC / replication → cross-reference `community/voices/index.md`
    § "Heikki Linnakangas"
  - extended stats / partition pruning → `tomas-vondra.md`
  - parallel query / project process → `robert-haas.md`
  - TAP / tests / back-patching → `michael-paquier.md`
  - build system / locale / SQL standard → `community/voices/index.md`
    § "Peter Eisentraut"
  - release notes / docs / TODO list → `community/voices/index.md`
    § "Bruce Momjian"

Read each selected voice file. Identify its "recurring concerns" /
"common patterns" / "review checklist" section. For this skill, ask:
**how would this committer react to the idea, not the code?**
That's a different question than the code-review question
`pre-review-by-committers.md` answers. Concretely:

- **Tom**: would the idea require touching grammar.y or the type
  system? Is it a planner change with measurable correctness risk?
  Is the user proposing a GUC as a knob to compensate for a
  problem that should be fixed structurally?
- **Andres**: does the idea involve a hot path? Does it propose
  to add atomics, locks, or async I/O? Is the user proposing
  it without measurement, only on intuition?
- **Robert**: does the idea expose internal mechanism (parallel
  worker setup, DSM segments) that should stay private? Is it
  asking for an EXPLAIN extension for something not yet
  measurable?
- **Tomas**: is the idea about extended statistics, partition
  pruning, or parallel-query costing? Has the user shown a
  workload where the *current* design is observably wrong?
- **Michael**: does the idea require a TAP test to verify? Is
  it back-patchable, or master-only? Are there
  injection-points implications?

Each voice gets a 2–4 sentence prediction in the brief. Cite the
voice file. **Disclaim** every prediction — these are stylistic
simulations, not statements of fact about the committer.

### 6. Pull common-pitfalls from the conventions corpus

Skim:

- `community/common-pitfalls.md` (if present)
- The conventions files relevant to the idea's category:
  - GUC additions → `community/conventions/committing-checklist.md`
    § "Sync postgresql.conf.sample"
  - Doc-visible features → `community/conventions/commit-message-format.md`
    + the conventions corpus on doc updates
  - Hooks / extension API → typically Peter / Andres voices on
    ABI stability
  - Back-patchable features → `michael-paquier.md` § "back-patching
    mechanics"

Pull 3–5 specific pitfalls that this idea would land on. "Don't
forget the docs" is generic and unhelpful; "extending pg_stat_*
views needs a catversion bump and pg_proc.dat entries" is
specific and actionable.

### 7. Compose the suggested-first-steps list

The first step is almost always **post a design email to -hackers**.
The reasons:

- The project's culture is design-first. Committers regularly cite
  "post a design before writing code" as the path of least friction.
  Cross-reference: `community/conventions/git-workflow.md`
  § "Branch-per-feature workflow" — the local branch is private; the
  design conversation is the public artifact.
- A 100-line design email costs you 30 minutes; a 500-line patch you
  later have to redesign costs days. The expected-value math favors
  the email even if the design lands first try.

Step list (5 numbered actions, in order):

1. **Post a design email to pgsql-hackers** with the subject
   "Proposal: <one-line>". Body: motivation, prior art (cite the
   threads from step 3), proposed mechanism, alternatives
   considered, open questions. Don't attach code.
2. **Wait at least one week** for responses. Reviewers are slow but
   thorough; the first three replies are usually the ones that
   matter. Resist the urge to write the patch in parallel — if
   the design changes, the patch is wasted.
3. **If response is positive**: write a PoC patch (no docs, no
   tests yet) sufficient to validate the design. Re-post on the
   same thread with the PoC.
4. **If response is mixed**: revise the design email and re-post
   with explicit answers to the objections. The thread is the
   conversation; don't fork it.
5. **If response is "we already did this differently"**: stop.
   Read the existing implementation. Either there's nothing left
   to do, or there's a refinement to propose, but the original
   idea is dead.

For ideas that are clearly small (a one-line GUC default change, a
typo fix) the email-first rule relaxes; for those, suggested action
is a direct patch post per `generic/workflows/submit-patch.md`.

### 8. Pick the should-you-bother verdict

Decision matrix:

- Prior art shows `accepted+committed` matching the idea's intent →
  `redirect-to-related-effort`. Don't redo it.
- Prior art shows `consensus-no` from < 5 years ago AND no significant
  intervening change in the project → `likely-rejected-on-historical-grounds`.
  Surface specific quote(s) so the user can update their thinking.
- Prior art shows `still-discussing` → `redirect-to-related-effort`
  (join the existing thread).
- Prior art shows `consensus-no` from > 5 years ago → context may
  have changed; `proceed-with-design-post` but explicitly cite the
  prior "no" in the email.
- Prior art absent OR shows `dropped-by-author` → `proceed-with-design-post`.
- Idea is small, well-scoped, low-risk → `proceed-with-prototype-and-design-post`.
- Idea spans multiple subsystems and the area is undergoing
  active redesign per the research pass → `pause-research-more`.

State the verdict and the one-sentence rationale. Do not bury
the verdict — put it at the top of the brief.

## MCP tool reference

- (Foundation, via chained skill) the full toolset of
  `research-and-connect-dots.md`.
- Targeted prior-art: `search`, `hybrid_search`,
  `find_related_discussions`, `get_thread`, `get_message`,
  `find_similar_messages`
- Committer-on-topic searches: `get_author_messages`,
  `find_contributions`, `get_contributor_history`,
  `release_contributors`
- Idea-to-CF lookup: `find_entries_for_thread`, `get_entry`,
  `list_entries`
- Code grounding: `search_symbols`, `get_symbol`, `get_callers`,
  `get_callees`, `hybrid_search_code`, `semantic_search_code`,
  `git_log`, `git_blame`, `git_search`
- Wiki / docs: `search_wiki`, `get_wiki_page`, `search_docs`,
  `get_doc_page`

## Failure modes

- **Idea too vague.** "Make Postgres faster" returns nothing
  actionable. Push back: ask the user for the specific bottleneck
  or workload they observed.
- **Idea is in a domain not covered by archived discussion.** Some
  operational features (e.g. cloud-specific or distribution-specific)
  have no -hackers history because the conversation lives elsewhere.
  Note the absence honestly; don't fabricate a verdict.
- **All voices in the area are missing voice files.** Use
  `community/voices/index.md` § "Other committers" to surface the
  committer's email/name for direct archive search, and produce the
  brief without the voice-derived predictions. Disclaim the gap in
  the brief header.
- **Idea has prior art under a totally different name.** Vocabulary
  drift (e.g. "synchronous standby" vs "synchronous replication").
  This is exactly why step 1's normalization matters; if the agent
  finds nothing, retry with a paraphrase via `hybrid_search` before
  declaring "no prior art".
- **Recent active thread on the same idea, but the user is unaware.**
  The `redirect-to-related-effort` verdict is the right call —
  joining the existing thread is much higher value than restarting.
- **User pushes back on the verdict.** That's their right; the brief
  is advice, not a gate. Re-state the rationale, ask whether the
  prior-art quotes were considered, and let them proceed.

## Sources

- `generic/workflows/research-and-connect-dots.md` — foundation;
  this skill chains to it for the broad research pass.
- `generic/workflows/pre-review-by-committers.md` — voice-simulation
  pattern; reuse the voice-selection logic.
- `community/voices/index.md` — voice-file pointers, including the
  in-line cross-references for Heikki, Bruce, Peter.
- `community/voices/tom-lane.md`,
  `community/voices/andres-freund.md`,
  `community/voices/tomas-vondra.md`,
  `community/voices/michael-paquier.md`,
  `community/voices/robert-haas.md` — voice files.
- `community/conventions/commit-message-format.md` — what a design
  email's eventual commit message will look like; a good design
  email anticipates the commit message.
- `community/conventions/committing-checklist.md` — what the patch
  will eventually need to satisfy; design with that list in mind.
- `community/conventions/git-workflow.md` § "Branch-per-feature
  workflow" — the workflow the design email anchors.
- `community/conventions/creating-clean-patches.md` — the standard
  for the eventual PoC.
- Wiki: <https://wiki.postgresql.org/wiki/Submitting_a_Patch>
  § "Discuss your idea on pgsql-hackers" — the project's own
  guidance to design-first.
- Wiki: <https://wiki.postgresql.org/wiki/Todo> — Bruce's curated
  list; check whether your idea is on the TODO list (positive
  signal) or has been explicitly marked not-wanted.

## Example

Input: `idea = "Add a GUC enable_seqscan_parallel to force parallel
sequential scans on small tables."`

```
# 1. Normalize
# Project vocabulary: this is a planner-cost / parallel-query knob.
# Canonical form: "force parallel scan on tables under
# min_parallel_table_scan_size".

# 2. Research foundation
# (chain research-and-connect-dots.md "force parallel scan small table")

# 3. Targeted prior-art
search(query: "s:force parallel scan", inbox: "pgsql-hackers", limit: 30)
hybrid_search(query: "GUC to override min_parallel_table_scan_size")
# → 2017 thread "Forcing parallel scan on small tables" — outcome:
#   consensus-no. Tom: "the cost model is the right place to fix
#   this; a GUC is band-aid." (msgid <…@sss.pgh.pa.us>)
# → 2022 thread "min_parallel_table_scan_size = 0 misbehavior" —
#   outcome: accepted+committed (different design: cost model fix).

# 4. Committer-on-topic
get_author_messages(name_or_email: "tgl@sss.pgh.pa.us", limit: 30)
# → multiple messages saying "GUCs to force planner choice are a
#   dead end; fix the cost model".

# 5. Voices
# Default triplet: tom-lane (planner), andres-freund (perf),
#                  robert-haas (parallel query — topic-relevant).

# 6. Pitfalls
# - GUC additions need postgresql.conf.sample sync (committing-checklist).
# - "Force" GUCs are historically opposed (Tom).
# - Doc must explain when the GUC helps; without that, doc fails review.

# 7. First steps
# 1. Post design email "Proposal: planner cost-model fix for small-table
#    parallel scans" — frame as cost-model fix, not GUC.
# 2. Cite the 2022 thread; explain what it left unresolved.
# 3. Skip the prototype until -hackers buys the framing.

# 8. Verdict
# likely-rejected-on-historical-grounds — for the GUC framing.
# proceed-with-design-post — for the cost-model framing.
```

Output (paste-able):

```
Verdict: likely-rejected-on-historical-grounds (as a GUC).
         proceed-with-design-post (as a cost-model fix).

Prior art:
  - 2017 <msgid> — "Forcing parallel scan on small tables" —
    consensus-no. Tom: "the cost model is the right place to fix
    this; a GUC is band-aid."
  - 2022 <msgid> — "min_parallel_table_scan_size = 0 misbehavior" —
    accepted+committed (sha <…>) as a cost-model fix; left small-
    table small-row-count case open.

Likely committer reactions (SIMULATION — disclaimer applies):
  - Tom Lane (community/voices/tom-lane.md § "GUCs as compensation"):
    "Don't add a knob to override planner judgment; fix the planner."
  - Andres Freund (community/voices/andres-freund.md § "show me
    perf"):  "Workload that benefits? Show pgbench / TPC-H numbers,
    not microbenchmark."
  - Robert Haas (community/voices/robert-haas.md § "what the project
    values"): "Parallel query knobs proliferate; raise the bar for
    new ones."

Common pitfalls:
  - GUC additions require postgresql.conf.sample sync.
  - "force-X" GUCs are historically opposed.
  - Need a workload proving the cost model is wrong.

Suggested first steps:
  1. Reframe as a cost-model bug, not a GUC.
  2. Find a workload where the planner picks seqscan but parallel
     would be measurably better.
  3. Post design email to -hackers; cite 2017 + 2022 threads.
  4. Wait one week.
  5. If the framing lands, write a PoC; otherwise drop.
```

## Tips

- The brief is calibration, not a verdict. A `likely-rejected` brief
  doesn't stop the user; it tells them what they're walking into.
- Always run step 4 (committer-on-topic search). The single most
  common failure mode of new contributors is proposing something a
  committer has explicitly rejected on the same list within the
  past 3 years. A 30-second search prevents the embarrassment.
- Quote sparingly. One line per committer is enough; longer quotes
  drift into argument-by-authority and irritate the very people
  whose words you're quoting.
- This skill is short-circuit-eligible: if the user's idea is in a
  category the brief always answers with "post a design email
  first" (e.g. any planner change, any GUC addition, any new hook
  API), produce the brief but cap effort at ~10 minutes. The
  expensive research pass is overkill for ideas where the verdict
  is foregone.
- Re-run the brief after every significant change to the idea. A
  reframing from "GUC" to "cost-model fix" can flip the verdict;
  the brief's value is *in the framing*, not just the keywords.
