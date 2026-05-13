# Spec: Research pgsql-hackers Discussions

## Context

The pgsql-hackers mailing list is PostgreSQL's primary development list with 77,000+ archived messages spanning decades. Researching it effectively requires combining keyword search, semantic search, thread navigation, and temporal filtering.

## Requirements

### Functional Requirements

1. **Topic Discovery** — Given a topic keyword or natural language description, find all relevant threads across the pgsql-hackers archive.

2. **Temporal Filtering** — Narrow results to specific PostgreSQL development cycles or date ranges.

3. **Thread Reading** — Retrieve and present complete discussion threads with all messages in order.

4. **Author Tracking** — Find all contributions from a specific developer on a topic.

5. **Cross-Reference Resolution** — Follow references between threads to build complete picture of a discussion that spans multiple threads.

### Non-Functional Requirements

- Results should be ranked by relevance, with most recent and most active threads prioritized.
- Thread summaries should identify key participants and whether consensus was reached.
- Should handle topics that evolved in terminology over time (e.g., "parallel query" vs "parallel execution" vs "parallel scan").

## MCP Tools to Use

| Tool | Purpose |
|------|---------|
| `search` | Full-text keyword search with date/author/subject filters |
| `hybrid_search` | Combined keyword + semantic for natural language queries |
| `semantic_search` | Pure meaning-based search for conceptual similarity |
| `get_thread` | Retrieve complete thread from any Message-ID |
| `get_message` | Get individual message details |
| `get_author_messages` | Find all posts by a specific person |
| `find_similar_messages` | Find semantically related discussions |
| `get_thread_references` | Discover cross-thread references |
| `browse_by_date` | Explore threads in a time window |
| `get_inbox_stats` | Understand activity patterns |

## Workflow

### Step 1: Broad Discovery
```
search(query: "s:topic-keyword", inbox: "pgsql-hackers")
hybrid_search(query: "natural language description of topic")
```

### Step 2: Identify Key Threads
Sort results by message count (longer threads = more important discussions). Identify threads from different time periods to see how thinking evolved.

### Step 3: Deep Reading
```
get_thread(message_id: "<id-of-important-thread>")
get_thread_references(message_id: "<id>")
```

### Step 4: Follow the Trail
```
find_similar_messages(message_id: "<key-message-id>")
get_author_messages(author: "key-contributor", after: "relevant-start", before: "relevant-end")
```

### Step 5: Synthesize
Identify: consensus position, open questions, key objections, and current status.

## Acceptance Criteria

- [ ] Can find threads on any PostgreSQL development topic
- [ ] Can follow discussion evolution across multiple threads
- [ ] Can identify community consensus or lack thereof
- [ ] Can distinguish active/ongoing discussions from resolved ones
- [ ] Handles terminology changes over time via semantic search
