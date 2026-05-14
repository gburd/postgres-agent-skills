# PostgreSQL Community Research Agent

This project connects to the Agora MCP server for PostgreSQL community research. Agora provides access to 40+ years of mailing list archives across all PostgreSQL lists, full source code intelligence with call graphs, and git history analysis.

## MCP Configuration

**Endpoint:** `https://postgr.esq/l/mcp/`
**Transport:** Streamable HTTP

Connect using any MCP client that supports Streamable HTTP transport. The server requires no authentication for read access.

## Available Tool Categories

### Email Search and Discovery

| Tool | Purpose |
|------|---------|
| `search` | Full-text search with prefix syntax (s:subject, f:from, d:daterange, b:body, t:to) |
| `hybrid_search` | Combined keyword + semantic search using Reciprocal Rank Fusion |
| `semantic_search` | Pure vector-similarity search for conceptually related messages |
| `get_author_messages` | Find all messages by a specific contributor, with optional date filtering |
| `find_related_discussions` | Find messages related to a commit hash, topic, or Message-ID |
| `search_patches` | Find patch series by parsing [PATCH vN M/N]-style subject prefixes |
| `list_recent` | List the most recent messages in an inbox |
| `list_threads` | Browse recent threads with message counts and date ranges |
| `browse_by_date` | Browse threads within a specific date range |

### Thread Navigation

| Tool | Purpose |
|------|---------|
| `get_thread` | Get all messages in a thread from any Message-ID in it |
| `get_message` | Get a single message with headers, body, and attachment metadata |
| `get_message_references` | Discover cross-references (References/In-Reply-To + body mentions) |
| `get_thread_references` | Cross-references across an entire thread |
| `find_similar_messages` | Find messages semantically similar to a given one |
| `get_raw_message` | Get the raw RFC 822 email bytes |
| `get_message_headers` | Get structured header key/value pairs |
| `get_attachment` | Download attachment content by index or filename |

### Code Intelligence

| Tool | Purpose |
|------|---------|
| `search_symbols` | Search symbols by name, kind (function/class/struct/etc.), or language |
| `get_symbol` | Full source code, signature, documentation, and file location |
| `get_signature` | Function/method signature and doc comment |
| `get_callers` | Reverse call graph: who calls this symbol |
| `get_callees` | Forward call graph: what this symbol calls |
| `get_dependents` | Transitive blast radius if this symbol changes |
| `get_impact` | Risk analysis: blast radius, affected communities and flows |
| `get_type_hierarchy` | Inheritance and implementation chains |
| `get_implementors` | All types implementing an interface or inheriting from a class |
| `find_imports` | Cross-file dependencies for a given file |
| `find_pattern` | Regex search across symbol bodies (trigram-accelerated) |
| `find_dead_code` | Functions with zero incoming call graph edges |
| `symbols_in_file` | List all symbols defined in a file |
| `get_communities` | Louvain community clusters in the call graph |
| `get_community` | Details and member symbols for a specific community |
| `get_execution_flows` | Trace execution flow paths from entry points |
| `hybrid_search_code` | Combined keyword + semantic code search |
| `semantic_search_code` | Pure vector-similarity code search |

### Git History and Analysis

| Tool | Purpose |
|------|---------|
| `git_blame` | Modification history for a file: commits, authors, summaries |
| `git_log` | Commit history with filters by path, author, date range |
| `git_diff` | Unified diff between two commits |
| `git_search` | Search commit messages or file paths by keyword |
| `git_show_file` | File content at a specific commit |
| `git_analyze_churn` | Most frequently modified files (hotspots) |
| `git_analyze_coupling` | Files frequently changed together (hidden dependencies) |
| `git_analyze_hotspots` | Directory-level churn aggregation |
| `git_analyze_bus_factor` | Files with fewest distinct authors (knowledge silos) |
| `git_analyze_authors` | Commit statistics per author |
| `git_analyze_activity` | Commit frequency over time |
| `detect_changes` | Symbols changed between two commits |
| `blame_symbol` | Commit history filtered to a symbol's line range |

### Patch and PR Tracking

| Tool | Purpose |
|------|---------|
| `get_patch_series` | All iterations of a patch submitted to the mailing list |
| `get_patch_branches` | Git branches created from applied email patches |
| `check_upstream_status` | Whether a PR has been merged upstream |

### Inbox and Repository Metadata

| Tool | Purpose |
|------|---------|
| `list_inboxes` | All configured mailing list inboxes |
| `get_inbox_info` | Metadata for an inbox (name, addresses, message count) |
| `get_inbox_stats` | Aggregate statistics: message counts, top authors, trends |
| `list_repositories` | All registered git repositories with stats |
| `repository_stats` | Detailed stats for a repository |
| `code_index_status` | Code indexing statistics |
| `codebase_map` | Directory-level overview of the codebase |
| `list_branches` | Tracked branches with head commit info |
| `embedding_status` | Embedding coverage and model info |

### Documentation and Wiki

| Tool | Purpose |
|------|---------|
| `search_docs` | Full-text search across documentation pages |
| `get_doc_page` | Get a specific documentation page by path and version |
| `list_doc_versions` | Available documentation versions |
| `search_wiki` | Full-text search across wiki pages |
| `get_wiki_page` | Get a wiki page with latest revision |
| `get_wiki_history` | Revision history for a wiki page |

### Discord

| Tool | Purpose |
|------|---------|
| `list_discord_channels` | Monitored Discord channels with message counts |
| `get_discord_thread` | Get a Discord conversation by channel |
| `search_discord` | Full-text search across Discord messages |

### Cross-Source Search

| Tool | Purpose |
|------|---------|
| `search_all_sources` | Unified search across docs, wiki, discord, and email |

## Search Syntax

The `search` tool supports prefix-based queries:

| Prefix | Meaning | Example |
|--------|---------|---------|
| `s:` | Subject line | `s:parallel query` |
| `f:` | From (author) | `f:tom.lane` |
| `t:` | To (recipient) | `t:pgsql-hackers` |
| `d:` | Date range | `d:2023-01..2023-06` |
| `b:` | Body text | `b:ereport ERROR` |

Combine prefixes: `s:vacuum f:andres.freund d:2022-01..2023-12`

## Research Strategy

### 1. Start Broad, Then Narrow

Begin with keyword search to understand the landscape, then use semantic search for conceptually related discussions, then drill into specific threads.

```
search(query: "s:autovacuum freeze") -> overview of thread subjects
hybrid_search(query: "preventing transaction ID wraparound") -> conceptually related
get_thread(message_id: "<specific-id>") -> read full discussion
```

### 2. Combine Email and Code Intelligence

PostgreSQL decisions are made on-list and implemented in code. Bridge both:

```
# Find the discussion
search(query: "s:Add support for MERGE")

# Find the implementation
search_symbols(query: "ExecMerge", kind: "function")
get_callers(qualified_name: "ExecMerge")

# Find what changed
git_search(query: "MERGE")
git_blame(path: "src/backend/executor/execMerge.c")
```

### 3. Trace Decisions Through Time

Major features evolve over years. Follow the trail:

```
# Find early RFCs
search(query: "s:RFC MERGE d:2018-01..2019-12", inbox: "pgsql-hackers")

# Find review threads
search(query: "s:MERGE d:2020-01..2022-12", inbox: "pgsql-hackers")

# Find the commit announcement
search(query: "s:MERGE", inbox: "pgsql-committers")
```

## Research Patterns

### "What does the community think about X?"

1. `search(query: "s:X", inbox: "pgsql-hackers")` -- find threads
2. Read the longest threads (more messages = more discussion)
3. Look for messages from committers (they make final decisions)
4. Check if there's a commitfest entry that tracked it

### "Has anyone tried X before?"

1. `hybrid_search(query: "X approach")` -- find prior attempts
2. `search(query: "s:X rejected")` or `search(query: "s:X withdrawn")` -- find failed attempts
3. Read rejection reasons -- they encode community values

### "How does feature X work internally?"

1. `search_symbols(query: "X", kind: "function")` -- find entry points
2. `get_callees(qualified_name: "...")` -- trace execution
3. `get_execution_flows()` -- see high-level paths through the code
4. `git_blame(path: "...")` -- find the commit that added it
5. `git_search(query: "commit message keywords")` -- find related commits
6. `find_related_discussions(query: "commit-hash")` -- find the mailing list thread

### "What are the active debates on topic X?"

1. `browse_by_date(after: "2024-01-01", before: "today")` -- recent threads
2. `search(query: "s:X d:2024-01..", inbox: "pgsql-hackers")` -- recent discussions
3. `get_inbox_stats(inbox: "pgsql-hackers")` -- who's most active

### "How was this code originally designed?"

1. `git_blame(path: "src/backend/...")` -- find the introducing commit
2. `git_search(query: "keywords from commit message")` -- find the commit
3. `find_related_discussions(query: "commit-sha")` -- find the thread
4. `get_thread(message_id: "<id>")` -- read the full discussion
5. `get_thread_references(message_id: "<id>")` -- find cross-referenced threads

### "What's the impact of changing symbol X?"

1. `get_symbol(qualified_name: "X")` -- understand current implementation
2. `get_callers(qualified_name: "X")` -- direct callers
3. `get_dependents(qualified_name: "X")` -- full transitive blast radius
4. `get_impact(qualified_name: "X")` -- risk level and affected communities
5. `blame_symbol(qualified_name: "X")` -- who has modified it and when

## Patch Review Workflow

### Reviewing a Patch Submission

1. Find the patch series and all versions:
   ```
   search_patches(query: "feature-name")
   search(query: "s:[PATCH v feature-name", inbox: "pgsql-hackers")
   ```

2. Read the cover letter (the 0/N message) for each version to understand changes.

3. Find prior art on the same topic:
   ```
   search(query: "s:feature-name", inbox: "pgsql-hackers")
   hybrid_search(query: "alternative approaches to feature-name")
   ```

4. Check the implementation against existing code:
   ```
   search_symbols(query: "related-function", kind: "function")
   get_callers(qualified_name: "affected-function")
   ```

5. Look for potential issues flagged in similar past reviews:
   ```
   search(query: "s:Re: [PATCH similar-feature")
   ```

### What Reviewers Look For

- **Correctness**: Edge cases (NULL, empty, concurrent access, OOM), error path resource cleanup
- **Backwards compatibility**: Catalog changes, pg_upgrade, dump/restore
- **Code quality**: pgindent clean, naming consistency, clear comments
- **Performance**: No overhead on common paths, appropriate algorithms
- **Documentation**: Updated docs for user-visible changes, with examples
- **Testing**: Regression tests covering edge cases and error paths, deterministic output

## Commit Archaeology

Every significant PostgreSQL change was discussed on-list before being committed. Trace code back to its discussion:

1. Find when code was introduced: `git_blame(path: "...")`
2. Get the commit details: `git_log(path: "...", author: "...")`
3. PostgreSQL commit messages contain `Discussion:` links -- follow them
4. If no direct link: `find_related_discussions(query: "commit-sha-prefix")`
5. Or search by keywords: `search(query: "s:keywords d:date-range", inbox: "pgsql-hackers")`

## PostgreSQL Development Process

### Release Cycle (Annual)

| Phase | Timing | What Happens |
|-------|--------|--------------|
| Development opens | After prior release branch | New features accepted |
| Commitfests 1-4 | Nov, Jan, Mar, May | Coordinated review periods |
| Feature freeze | ~April/May | No new features after this |
| Beta | ~May-September | Public testing, bug fixes only |
| Release | ~September/October | GA release |

### Commitfest States

- **Needs Review** -- Waiting for someone to look at it
- **Waiting on Author** -- Reviewer found issues
- **Ready for Committer** -- Reviewed and approved
- **Committed** -- Done
- **Returned with Feedback** -- Not ready for this release
- **Withdrawn** -- Author gave up
- **Rejected** -- Community decided against it

### How Proposals Die

Most proposals die from inaction, not rejection:
1. No champion willing to write the code
2. No reviewer willing to review it
3. Author stops responding to feedback
4. Returned from commitfest too many times
5. Scope creep makes it intractable

## Community Norms

### The Mailing List Is the System of Record

Everything important happens on pgsql-hackers. There is no Slack, no Discord, no Jira that matters for development decisions. If it wasn't discussed on-list, it didn't happen.

### Key Mailing Lists

| List | Purpose |
|------|---------|
| pgsql-hackers | Development discussion, patches, design (50-100 msgs/day) |
| pgsql-committers | Commit notifications |
| pgsql-bugs | Bug reports from users |
| pgsql-general | User questions, general discussion |
| pgsql-announce | Release announcements |

### How to Interpret Responses

- **Quick positive from a committer** = strong signal of acceptance
- **Silence** = nobody cares enough to champion this; it will likely die
- **"I'm not sure we need this"** from a committer = soft rejection
- **"This would need to..."** = conditional interest; requirements stated
- **Long debate with no resolution** = too controversial for this cycle

### Key Committers (2024-2025)

- Tom Lane -- longest-serving, encyclopedic knowledge, catches subtle issues
- Andres Freund -- performance, infrastructure, storage
- Robert Haas -- parallelism, partitioning, project direction
- Heikki Linnakangas -- WAL, replication, storage internals
- Peter Eisentraut -- SQL standards, build system, localization
- Michael Paquier -- replication, authentication, security
- Alvaro Herrera -- catalogs, DDL, partitioning
- Noah Misch -- security, portability, edge cases

### Things That Get Patches Rejected

1. Not reading prior discussions on the same topic
2. Ignoring review feedback and reposting unchanged
3. Breaking backwards compatibility without overwhelming justification
4. Adding user-visible features without documentation
5. Submitting without regression tests
6. Not running pgindent
7. Over-engineering: "this might be useful someday"
8. Adding GUCs for things that should just work

### The Extension vs Core Debate

Features that CAN be extensions SHOULD be extensions. Core additions carry eternal maintenance burden. The community increasingly pushes things toward extensions.

## Tips

- pgsql-hackers is where development decisions are made
- pgsql-committers shows what was actually committed
- pgsql-bugs reveals real-world problems and edge cases
- pgsql-general shows user-facing concerns and use cases
- Threads with 50+ messages indicate contentious or important topics
- The PostgreSQL community values backwards compatibility above almost everything
- Silence on a proposal often means "nobody cares enough to push this forward"
- PostgreSQL commit messages almost always contain a `Discussion:` URL linking to the mailing list thread
- The mailing list archive predates git -- for code older than ~2010, CVS-era commits reference pgsql-committers posts
- Before proposing anything, search for prior discussions -- it has almost certainly been discussed before
