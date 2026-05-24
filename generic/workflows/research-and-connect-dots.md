# Workflow: Research a Topic and Connect the Dots

Quickly assemble a chronological, cross-source picture of a PostgreSQL topic by traversing the wiki, official docs, mailing-list archives, git history, and the source-code symbol graph in one pass. This is **research mode**: build understanding fast before doing anything.

## Goal

Given a topic name (e.g. "vacuum freeze", "logical replication slot drop", "subxact overflow", "TID store"), produce a single timeline + reference list that pins down where the idea came from, where it lives in the code today, and what's been said about it recently.

## Inputs

- `topic` (required): a short phrase. Two to five words is the sweet spot. Single-word topics ("vacuum") return too much; full sentences confuse search ranking.
- `since` (optional): ISO date for "recent activity" cutoff. Defaults to one year before today.

## Outputs

- A chronological timeline:
  - First mailing-list mention (message-id, date, subject, author)
  - First commit (SHA, date, author, one-line summary)
  - Wiki coverage (page title + URL)
  - Docs coverage (postgresql.org/docs URL, with section anchor if applicable)
  - Major refinements (3–10 commits, oldest to newest, each with sha + date + one-line summary)
  - Recent activity in the last 12 months (mailing-list threads + commits)
- A reference list of 10–20 items with one-line summaries each, grouped by source kind (wiki, docs, hackers, committers, git, code).
- A "what to read first" recommendation: the 3 references most likely to give a person background fast.

## Steps

### 1. Cast a wide net across all sources

Start with `search_all_sources` for a single-shot view; this hits wiki, docs, hackers, code in parallel and returns a ranked merged list:

```
search_all_sources(query: "topic", limit: 30)
```

If that's too noisy, fall back to per-source searches in steps 2–6.

### 2. Wiki coverage

The PostgreSQL wiki is where designs and rationale tend to live as long-form prose:

```
search_wiki(query: "topic")
get_wiki_page(title: "<best hit>")
get_wiki_history(title: "<best hit>")     # who has edited it; staleness signal
```

If the topic has its own wiki page, that page's References section is the single highest-yield jump-off point. If it doesn't, look for a parent-area page (e.g. "VACUUM Internals" for "vacuum freeze").

### 3. Official documentation coverage

```
search_docs(query: "topic")
list_doc_versions()               # confirm coverage exists in current branch
get_doc_page(path: "<best hit>")  # to extract the canonical phrasing
```

Note the section anchor — link the user to it directly, not to the page top.

### 4. Mailing-list archaeology

The first mention is often years before the first commit. To find it, walk forward in time:

```
# Substring + BM25 ranking; restrict to the inbox most likely to discuss design
search(query: "s:topic", inbox: "pgsql-hackers", limit: 20)

# Conceptual / paraphrase matches (different vocabulary than the modern term)
hybrid_search(query: "topic in natural-language form", limit: 20)

# When you find one anchor, fan out to similar
find_similar_messages(message_id: "<anchor-id>", limit: 10)
find_related_discussions(query: "<topic phrasing>")
```

Sort the hits by date ascending to find the earliest. Read the first thread's first message to identify who proposed it and why.

### 5. Git history

```
# Commits whose message text mentions the topic
git_search(query: "topic")

# Filter by file path if you already know where it lives
git_log(path: "src/backend/...", since: "1995-01-01", limit: 50)
```

For long-running areas (e.g. vacuum, planner), use the analytics:

```
git_analyze_hotspots(path: "src/backend/access/heap")
git_analyze_authors(path: "src/backend/access/heap", since: "2023-01-01")
git_analyze_churn(path: "src/backend/access/heap", since: "2023-01-01")
```

These reveal which files / authors are currently most active in the area — high-signal for "who would you talk to about this today?"

### 6. Code-symbol graph

```
# Symbols whose name matches the topic terms
search_symbols(query: "topic_term")
hybrid_search_code(query: "what the topic does in plain English", limit: 15)
semantic_search_code(query: "what the topic does in plain English", limit: 15)

# Pick the central symbol; trace it
get_symbol(qualified_name: "<central function>")
get_callers(qualified_name: "<central function>")
get_callees(qualified_name: "<central function>")
```

The central symbol's `git_blame` gives you the contributor lineage:

```
git_blame(path: "<file from get_symbol>", line_start: <N>, line_end: <M>)
blame_symbol(qualified_name: "<central function>")
```

### 7. Recent activity (last 12 months)

```
search(query: "s:topic", inbox: "pgsql-hackers", limit: 20)   # then sort by date
get_new_messages(inbox: "pgsql-hackers", since: "<one year ago>")
git_log(path: "<area>", since: "<one year ago>", limit: 30)
git_analyze_activity(path: "<area>", since: "<one year ago>")
```

Recent activity is what tells you whether the topic is alive, dormant, or undergoing a redesign right now.

### 8. Synthesize the timeline

Construct the timeline structure described in **Outputs**. For each timeline event, cite the source (message-id, sha, wiki page, docs URL). Do not paraphrase without citing.

Pick the "what to read first" trio by this rule of thumb:
- 1 wiki page or docs section (overview)
- 1 message-id (rationale: why we did it this way)
- 1 commit (the central change, ideally not the very first — pick one that landed the design as currently shipped)

## MCP tool reference

- Aggregate: `search_all_sources`
- Wiki: `search_wiki`, `get_wiki_page`, `get_wiki_history`
- Docs: `search_docs`, `list_doc_versions`, `get_doc_page`
- Mail: `search`, `hybrid_search`, `find_similar_messages`, `find_related_discussions`, `get_thread`, `get_message`, `get_new_messages`
- Git: `git_search`, `git_log`, `git_blame`, `git_analyze_hotspots`, `git_analyze_authors`, `git_analyze_churn`, `git_analyze_activity`
- Code: `search_symbols`, `hybrid_search_code`, `semantic_search_code`, `get_symbol`, `get_callers`, `get_callees`, `blame_symbol`

## Failure modes

- **Topic too generic.** "Locks" or "buffer" returns thousands of hits and no signal. Refine to a sub-topic ("buffer eviction clock-sweep", "tuple-level lock upgrade").
- **Topic too new.** If a feature landed in the last 6 months, wiki and docs may not have caught up — rely on git + hackers archive + the patch's own commit message.
- **Topic renamed over time.** "Synchronous standby" was discussed for years as "synchronous replication". Use `hybrid_search` to bridge vocabulary gaps; check the first hit's date and search for what the same idea was called before.
- **No code symbol matches.** Some topics are operational, not source-level (e.g. "WAL archiving setup"). Skip step 6; lean harder on docs + wiki.
- **Embeddings not available.** `hybrid_search` falls back to plain BM25 if the embedding provider is offline. Check `embedding_status` if hybrid results look identical to keyword results.

## Sources

- Existing skill: `generic/workflows/trace-feature-history.md` — overlaps on RFC-to-commit walkthrough; this skill is wider (wiki + docs + symbols) but shallower per dimension.
- Existing skill: `generic/workflows/find-related-patches.md` — chain to it when the topic is patch-centric (a specific patch series).
- Existing skill: `generic/workflows/semantic-code-search.md` — chain to it for code-only deep dives.
- Cross-reference: this is the foundation for `gain-perspective.md` and the search-prep step of `pre-review-by-committers.md`.

## Example

Topic: "subxact overflow"

```
# 1. Wide net
search_all_sources(query: "subxact overflow", limit: 30)

# 2. Wiki
search_wiki(query: "subtransaction overflow")
get_wiki_page(title: "Hint Bits")               # mentions subxact suboverflow logic

# 3. Docs
search_docs(query: "subtransaction overflow snapshot")

# 4. Mail
search(query: "s:subxact overflow", inbox: "pgsql-hackers", limit: 20)
hybrid_search(query: "performance cliff with many subtransactions per backend")

# 5. Git
git_search(query: "subtrans overflow")
git_log(path: "src/backend/access/transam/subtrans.c", limit: 50)
git_analyze_hotspots(path: "src/backend/access/transam")

# 6. Code
search_symbols(query: "SubTransGetTopmostTransaction")
get_callers(qualified_name: "SubTransGetTopmostTransaction")
hybrid_search_code(query: "snapshot subxact overflow flag")

# 7. Recent
search(query: "s:subtransaction", inbox: "pgsql-hackers", limit: 20)  # filter to last year
git_log(path: "src/backend/access/transam/subtrans.c", since: "2025-05-24")
```

The expected output is a one-page synthesis: where SubTransSLRU lives, who has worked on its scaling problems (`git_analyze_authors` will name them), the canonical hackers thread on the performance cliff, the 64-subxact PGPROC cache constant, and the docs page that tells users to avoid >64 savepoints per transaction.

## Tips

- Save intermediate hits as you go. Most users abandon a research session before completing it; the timeline is mostly useful in retrospect, not realtime.
- Don't trust the first hit's framing of the problem. Read the first **thread** (multiple replies), not just the first message — early framings get corrected.
- When two sources disagree (e.g. docs say one thing, an old hackers thread says another), trust the most recent commit's message text — that's what's actually shipped.
- When `search` and `hybrid_search` return wildly different top hits, the topic has vocabulary drift. Note both phrasings in your output.
