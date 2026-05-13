# PostgreSQL Research Methodology

Use this skill when researching PostgreSQL topics using the Agora MCP server. The server provides access to 40+ years of mailing list archives across all PostgreSQL lists (pgsql-hackers, pgsql-general, pgsql-bugs, pgsql-committers, etc.) plus full source code intelligence.

## Research Strategy

### 1. Start Broad, Then Narrow

Begin with keyword search to understand the landscape of a topic, then use semantic search to find conceptually related discussions, then drill into specific threads.

```
search(query: "s:autovacuum freeze") → get overview of thread subjects
hybrid_search(query: "preventing transaction ID wraparound") → find conceptually related
get_thread(message_id: "<specific-id>") → read full discussion
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

## Key Tools and When to Use Them

### Email Discovery
- `search` — Full-text search with prefix syntax (s:subject, f:from, d:daterange, b:body)
- `hybrid_search` — Combined keyword + semantic search; best for natural language queries
- `semantic_search` — Pure meaning-based search; good for finding conceptually similar discussions
- `get_author_messages` — Find all messages by a specific contributor
- `find_related_discussions` — Find messages related to a commit hash or Message-ID

### Thread Navigation
- `get_thread` — Get the complete thread from any Message-ID in it
- `get_message` — Get a single message with full headers and body
- `get_message_references` — Find all cross-references in a message
- `get_thread_references` — Cross-references across an entire thread
- `find_similar_messages` — Find messages semantically similar to a given one

### Code Intelligence
- `search_symbols` — Find symbols by name, kind, or language
- `get_symbol` — Full source code and documentation for a symbol
- `get_callers` — Who calls this function? (reverse call graph)
- `get_callees` — What does this function call? (forward call graph)
- `get_dependents` — Full blast radius if this symbol changes
- `get_type_hierarchy` — Inheritance and implementation chains
- `find_imports` — Cross-file dependencies for a given file

### Git History
- `git_blame` — Who changed each line and when
- `git_log` — Commit history with filters
- `git_diff` — What changed between two commits
- `git_search` — Search commit messages
- `git_analyze_coupling` — Files that change together

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

## Research Patterns

### "What does the community think about X?"

1. `search(query: "s:X", inbox: "pgsql-hackers")` — find threads
2. Read the longest threads (more messages = more discussion)
3. Look for messages from committers (they make final decisions)
4. Check if there's a commitfest entry that tracked it

### "Has anyone tried X before?"

1. `hybrid_search(query: "X approach")` — find prior attempts
2. `search(query: "s:X rejected")` or `search(query: "s:X withdrawn")` — find failed attempts
3. Read rejection reasons — they encode community values

### "How does feature X work internally?"

1. `search_symbols(query: "X", kind: "function")` — find entry points
2. `get_callees(qualified_name: "...")` — trace execution
3. `get_execution_flows()` — see high-level paths through the code
4. `git_blame(path: "...")` — find the commit that added it
5. `git_search(query: "commit message keywords")` — find related commits
6. `find_related_discussions(query: "commit-hash")` — find the mailing list thread

### "What are the active debates on topic X?"

1. `browse_by_date(after: "2024-01-01", before: "today")` — recent threads
2. `search(query: "s:X d:2024-01..")` — recent discussions of X
3. `get_inbox_stats(inbox: "pgsql-hackers")` — who's most active

## Tips

- pgsql-hackers is where development decisions are made
- pgsql-committers shows what was actually committed
- pgsql-bugs reveals real-world problems and edge cases
- pgsql-general shows user-facing concerns and use cases
- Threads with 50+ messages indicate contentious or important topics
- Messages from Tom Lane, Andres Freund, Robert Haas, Heikki Linnakangas, Bruce Momjian carry particular weight as long-term committers
- The PostgreSQL community values backwards compatibility above almost everything
- Silence on a proposal often means "nobody cares enough to push this forward" not "everyone agrees"
