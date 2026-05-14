# Maki Plugin: Agora PostgreSQL Community Server

A Lua plugin for the [tontinton/maki](https://github.com/tontinton/maki) agent framework that provides access to PostgreSQL community resources via the Agora MCP server.

## Installation

1. Copy the plugin into your maki plugins directory:

```bash
cp plugins/agora.lua ~/.config/maki/plugins/
```

Or symlink it:

```bash
ln -s "$(pwd)/plugins/agora.lua" ~/.config/maki/plugins/agora.lua
```

2. Ensure your maki installation has `json` and `http` modules available (these are standard maki built-ins).

## Configuration

The plugin connects to the Agora MCP server at `https://postgr.esq/l/mcp/` using Streamable HTTP transport. No authentication is required.

To change the endpoint (e.g., for a local development server):

```lua
local agora = require("agora")
agora.endpoint = "http://localhost:8080/mcp/"
```

## Usage

```lua
local agora = require("agora")

-- Search mailing list archives
local results = agora.search("s:parallel query", { inbox = "pgsql-hackers" })

-- Semantic search for conceptually related discussions
local related = agora.hybrid_search("preventing transaction ID wraparound")

-- Read a complete thread
local thread = agora.get_thread("<CAF4Au4w@mail.gmail.com>")

-- Find code symbols
local symbols = agora.search_symbols("ExecParallelHashJoin", { kind = "function" })

-- Get call graph
local callers = agora.get_callers("ExecParallelHashJoin")

-- Search git history
local commits = agora.git_search("parallel hash join")

-- Browse recent threads
local threads = agora.list_threads({ inbox = "pgsql-hackers", limit = 10 })
```

## Available Functions

### Email Search
- `search(query, opts)` -- Full-text search with prefix syntax
- `hybrid_search(query, opts)` -- Combined keyword + semantic search
- `semantic_search(query, opts)` -- Pure vector similarity search
- `get_author_messages(author, opts)` -- Messages by a specific author
- `find_related_discussions(query, opts)` -- Messages related to a commit or topic
- `search_patches(opts)` -- Find patch series by subject prefix
- `list_recent(opts)` -- Recent messages in an inbox
- `list_threads(opts)` -- Recent threads with metadata
- `browse_by_date(after, before, opts)` -- Threads in a date range

### Thread Navigation
- `get_thread(message_id, opts)` -- Complete thread from any Message-ID
- `get_message(message_id, opts)` -- Single message with headers and body
- `get_message_references(message_id, opts)` -- Cross-references in a message
- `get_thread_references(message_id, opts)` -- Cross-references across a thread
- `find_similar_messages(message_id, opts)` -- Semantically similar messages

### Code Intelligence
- `search_symbols(query, opts)` -- Search by name, kind, or language
- `get_symbol(qualified_name, opts)` -- Full source, signature, docs
- `get_signature(qualified_name, opts)` -- Signature and doc comment
- `get_callers(qualified_name, opts)` -- Reverse call graph
- `get_callees(qualified_name, opts)` -- Forward call graph
- `get_dependents(qualified_name, opts)` -- Transitive blast radius
- `get_impact(qualified_name, opts)` -- Risk analysis
- `get_type_hierarchy(qualified_name, opts)` -- Inheritance chains
- `get_implementors(qualified_name, opts)` -- Interface implementors
- `find_pattern(pattern, opts)` -- Regex search in symbol bodies
- `find_imports(path, opts)` -- Cross-file dependencies
- `symbols_in_file(path, opts)` -- All symbols in a file

### Git History
- `git_blame(path, opts)` -- File modification history
- `git_log(opts)` -- Commit history with filters
- `git_diff(from_commit, opts)` -- Diff between commits
- `git_search(query, opts)` -- Search commit messages
- `git_show_file(path, opts)` -- File content at a commit
- `git_analyze_churn(opts)` -- Frequently modified files
- `git_analyze_coupling(opts)` -- Files changed together

### Metadata
- `list_inboxes()` -- All configured inboxes
- `get_inbox_info(opts)` -- Inbox metadata
- `get_inbox_stats(opts)` -- Aggregate statistics
- `list_repositories()` -- Registered git repositories
- `check_upstream_status(pr_url)` -- PR merge status
- `search_all_sources(query, opts)` -- Unified cross-source search

## Search Syntax

The `search` function supports prefix queries:

| Prefix | Meaning | Example |
|--------|---------|---------|
| `s:` | Subject | `s:vacuum freeze` |
| `f:` | From | `f:tom.lane` |
| `t:` | To | `t:pgsql-hackers` |
| `d:` | Date range | `d:2023-01..2023-06` |
| `b:` | Body text | `b:ereport ERROR` |

Combine them: `s:autovacuum f:andres.freund d:2022-01..2023-12`

## MCP Server

- **Endpoint:** `https://postgr.esq/l/mcp/`
- **Transport:** Streamable HTTP
- **Authentication:** None required (read-only public access)
