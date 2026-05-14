-- agora.lua - MCP client plugin for the PostgreSQL Agora server
--
-- Provides access to PostgreSQL mailing list archives, source code intelligence,
-- and git history via the Agora MCP server at https://postgr.esq/l/mcp/
--
-- Usage:
--   local agora = require("agora")
--   local results = agora.search("s:parallel query", { inbox = "pgsql-hackers" })
--   local thread = agora.get_thread("<message-id@example.com>")

local json = require("json")
local http = require("http")

local M = {}

-- Configuration
M.endpoint = "https://postgr.esq/l/mcp/"
M.transport = "streamable-http"

--- Internal: send an MCP tool call to the server.
-- @param tool_name string The MCP tool name to invoke
-- @param params table The parameters for the tool call
-- @return table The parsed response result
-- @return string|nil Error message if the call failed
local function call_tool(tool_name, params)
    local request_body = json.encode({
        jsonrpc = "2.0",
        id = tostring(os.time()) .. tostring(math.random(1000, 9999)),
        method = "tools/call",
        params = {
            name = tool_name,
            arguments = params or {}
        }
    })

    local response, err = http.request({
        method = "POST",
        url = M.endpoint,
        headers = {
            ["Content-Type"] = "application/json",
            ["Accept"] = "application/json"
        },
        body = request_body
    })

    if err then
        return nil, "HTTP request failed: " .. tostring(err)
    end

    if response.status_code ~= 200 then
        return nil, "Server returned status " .. tostring(response.status_code)
    end

    local result, decode_err = json.decode(response.body)
    if decode_err then
        return nil, "JSON decode failed: " .. tostring(decode_err)
    end

    if result.error then
        return nil, "MCP error: " .. tostring(result.error.message or result.error)
    end

    return result.result, nil
end

-- Email Search and Discovery

--- Full-text search across mailing list messages.
-- Supports prefix syntax: s:subject f:from t:to d:2024-01..2025-01 b:body_text
-- @param query string Search query string
-- @param opts table|nil Optional: inbox, limit, offset, collapse_threads
-- @return table Search results
function M.search(query, opts)
    opts = opts or {}
    local params = { query = query }
    if opts.inbox then params.inbox = opts.inbox end
    if opts.limit then params.limit = opts.limit end
    if opts.offset then params.offset = opts.offset end
    if opts.collapse_threads then params.collapse_threads = opts.collapse_threads end
    return call_tool("search", params)
end

--- Combined keyword + semantic search using Reciprocal Rank Fusion.
-- @param query string Search query (supports keywords and natural language)
-- @param opts table|nil Optional: inbox, limit, keyword_weight
-- @return table Search results
function M.hybrid_search(query, opts)
    opts = opts or {}
    local params = { query = query }
    if opts.inbox then params.inbox = opts.inbox end
    if opts.limit then params.limit = opts.limit end
    if opts.keyword_weight then params.keyword_weight = opts.keyword_weight end
    return call_tool("hybrid_search", params)
end

--- Semantic similarity search using vector embeddings.
-- @param query string Natural language query
-- @param opts table|nil Optional: inbox, limit
-- @return table Search results
function M.semantic_search(query, opts)
    opts = opts or {}
    local params = { query = query }
    if opts.inbox then params.inbox = opts.inbox end
    if opts.limit then params.limit = opts.limit end
    return call_tool("semantic_search", params)
end

--- Find messages by a specific author with optional date filtering.
-- @param author string Author name or email
-- @param opts table|nil Optional: inbox, after, before, limit, offset
-- @return table Messages by author
function M.get_author_messages(author, opts)
    opts = opts or {}
    local params = { author = author }
    if opts.inbox then params.inbox = opts.inbox end
    if opts.after then params.after = opts.after end
    if opts.before then params.before = opts.before end
    if opts.limit then params.limit = opts.limit end
    if opts.offset then params.offset = opts.offset end
    return call_tool("get_author_messages", params)
end

--- Find messages related to a commit, topic, or PR.
-- @param query string Commit hash, Message-ID substring, or subject keyword
-- @param opts table|nil Optional: limit
-- @return table Related discussions
function M.find_related_discussions(query, opts)
    opts = opts or {}
    local params = { query = query }
    if opts.limit then params.limit = opts.limit end
    return call_tool("find_related_discussions", params)
end

--- Find patch series by parsing [PATCH vN M/N]-style subject prefixes.
-- @param opts table|nil Optional: query, inbox, limit
-- @return table Patch series results
function M.search_patches(opts)
    opts = opts or {}
    local params = {}
    if opts.query then params.query = opts.query end
    if opts.inbox then params.inbox = opts.inbox end
    if opts.limit then params.limit = opts.limit end
    return call_tool("search_patches", params)
end

--- List recent messages from an inbox.
-- @param opts table|nil Optional: inbox, limit
-- @return table Recent messages
function M.list_recent(opts)
    opts = opts or {}
    local params = {}
    if opts.inbox then params.inbox = opts.inbox end
    if opts.limit then params.limit = opts.limit end
    return call_tool("list_recent", params)
end

--- Browse recent threads (topic-level view).
-- @param opts table|nil Optional: inbox, limit, before (unix timestamp)
-- @return table Thread summaries
function M.list_threads(opts)
    opts = opts or {}
    local params = {}
    if opts.inbox then params.inbox = opts.inbox end
    if opts.limit then params.limit = opts.limit end
    if opts.before then params.before = opts.before end
    return call_tool("list_threads", params)
end

--- Browse threads within a specific date range.
-- @param after string Start date (YYYY-MM-DD)
-- @param before string End date (YYYY-MM-DD)
-- @param opts table|nil Optional: inbox, limit
-- @return table Threads in date range
function M.browse_by_date(after, before, opts)
    opts = opts or {}
    local params = { after = after, before = before }
    if opts.inbox then params.inbox = opts.inbox end
    if opts.limit then params.limit = opts.limit end
    return call_tool("browse_by_date", params)
end

-- Thread Navigation

--- Get all messages in a thread by any Message-ID in the thread.
-- @param message_id string Message-ID (with or without angle brackets)
-- @param opts table|nil Optional: inbox, include_bodies
-- @return table Thread messages
function M.get_thread(message_id, opts)
    opts = opts or {}
    local params = { message_id = message_id }
    if opts.inbox then params.inbox = opts.inbox end
    if opts.include_bodies ~= nil then params.include_bodies = opts.include_bodies end
    return call_tool("get_thread", params)
end

--- Get a message by Message-ID, including headers, body, and attachment metadata.
-- @param message_id string Message-ID (with or without angle brackets)
-- @param opts table|nil Optional: inbox, include_body
-- @return table Message details
function M.get_message(message_id, opts)
    opts = opts or {}
    local params = { message_id = message_id }
    if opts.inbox then params.inbox = opts.inbox end
    if opts.include_body ~= nil then params.include_body = opts.include_body end
    return call_tool("get_message", params)
end

--- Discover cross-references in a message.
-- @param message_id string Message-ID
-- @param opts table|nil Optional: inbox
-- @return table References found
function M.get_message_references(message_id, opts)
    opts = opts or {}
    local params = { message_id = message_id }
    if opts.inbox then params.inbox = opts.inbox end
    return call_tool("get_message_references", params)
end

--- Cross-reference graph for an entire thread.
-- @param message_id string Message-ID of any message in the thread
-- @param opts table|nil Optional: inbox
-- @return table Thread cross-references
function M.get_thread_references(message_id, opts)
    opts = opts or {}
    local params = { message_id = message_id }
    if opts.inbox then params.inbox = opts.inbox end
    return call_tool("get_thread_references", params)
end

--- Find messages similar to a given message using embeddings.
-- @param message_id string Message-ID to find similar messages for
-- @param opts table|nil Optional: inbox, limit
-- @return table Similar messages
function M.find_similar_messages(message_id, opts)
    opts = opts or {}
    local params = { message_id = message_id }
    if opts.inbox then params.inbox = opts.inbox end
    if opts.limit then params.limit = opts.limit end
    return call_tool("find_similar_messages", params)
end

-- Code Intelligence

--- Search code symbols by name, kind, or language.
-- @param query string Symbol name or keyword
-- @param opts table|nil Optional: kind, language, repository, limit
-- @return table Symbol search results
function M.search_symbols(query, opts)
    opts = opts or {}
    local params = { query = query }
    if opts.kind then params.kind = opts.kind end
    if opts.language then params.language = opts.language end
    if opts.repository then params.repository = opts.repository end
    if opts.limit then params.limit = opts.limit end
    return call_tool("search_symbols", params)
end

--- Get full details for a code symbol by its qualified name.
-- @param qualified_name string Fully qualified symbol name
-- @param opts table|nil Optional: repository
-- @return table Symbol details with source code
function M.get_symbol(qualified_name, opts)
    opts = opts or {}
    local params = { qualified_name = qualified_name }
    if opts.repository then params.repository = opts.repository end
    return call_tool("get_symbol", params)
end

--- Get function/method signature and doc comment.
-- @param qualified_name string Fully qualified symbol name
-- @param opts table|nil Optional: repository
-- @return table Signature details
function M.get_signature(qualified_name, opts)
    opts = opts or {}
    local params = { qualified_name = qualified_name }
    if opts.repository then params.repository = opts.repository end
    return call_tool("get_signature", params)
end

--- Find all symbols that call/reference the given symbol (reverse call graph).
-- @param qualified_name string Fully qualified symbol name
-- @param opts table|nil Optional: repository, limit
-- @return table Callers
function M.get_callers(qualified_name, opts)
    opts = opts or {}
    local params = { qualified_name = qualified_name }
    if opts.repository then params.repository = opts.repository end
    if opts.limit then params.limit = opts.limit end
    return call_tool("get_callers", params)
end

--- Find all symbols that the given symbol calls/references (forward call graph).
-- @param qualified_name string Fully qualified symbol name
-- @param opts table|nil Optional: repository, limit
-- @return table Callees
function M.get_callees(qualified_name, opts)
    opts = opts or {}
    local params = { qualified_name = qualified_name }
    if opts.repository then params.repository = opts.repository end
    if opts.limit then params.limit = opts.limit end
    return call_tool("get_callees", params)
end

--- Get transitive dependents (blast radius) if this symbol changes.
-- @param qualified_name string Fully qualified symbol name
-- @param opts table|nil Optional: repository, limit, max_depth
-- @return table Dependents
function M.get_dependents(qualified_name, opts)
    opts = opts or {}
    local params = { qualified_name = qualified_name }
    if opts.repository then params.repository = opts.repository end
    if opts.limit then params.limit = opts.limit end
    if opts.max_depth then params.max_depth = opts.max_depth end
    return call_tool("get_dependents", params)
end

--- Analyze impact of modifying a symbol.
-- @param qualified_name string Fully qualified symbol name
-- @param opts table|nil Optional: repository
-- @return table Impact analysis
function M.get_impact(qualified_name, opts)
    opts = opts or {}
    local params = { qualified_name = qualified_name }
    if opts.repository then params.repository = opts.repository end
    return call_tool("get_impact", params)
end

--- Get inheritance and implementation hierarchy for a type.
-- @param qualified_name string Fully qualified type name
-- @param opts table|nil Optional: repository
-- @return table Type hierarchy
function M.get_type_hierarchy(qualified_name, opts)
    opts = opts or {}
    local params = { qualified_name = qualified_name }
    if opts.repository then params.repository = opts.repository end
    return call_tool("get_type_hierarchy", params)
end

--- Find all types implementing an interface or inheriting from a class.
-- @param qualified_name string Fully qualified interface/class name
-- @param opts table|nil Optional: repository
-- @return table Implementors
function M.get_implementors(qualified_name, opts)
    opts = opts or {}
    local params = { qualified_name = qualified_name }
    if opts.repository then params.repository = opts.repository end
    return call_tool("get_implementors", params)
end

--- Search for a regex pattern in code symbol bodies.
-- @param pattern string Regular expression pattern
-- @param opts table|nil Optional: repository, limit
-- @return table Pattern matches
function M.find_pattern(pattern, opts)
    opts = opts or {}
    local params = { pattern = pattern }
    if opts.repository then params.repository = opts.repository end
    if opts.limit then params.limit = opts.limit end
    return call_tool("find_pattern", params)
end

--- Find cross-file dependencies for a given file.
-- @param path string File path within the repository
-- @param opts table|nil Optional: repository
-- @return table Import dependencies
function M.find_imports(path, opts)
    opts = opts or {}
    local params = { path = path }
    if opts.repository then params.repository = opts.repository end
    return call_tool("find_imports", params)
end

--- List all symbols defined in a file.
-- @param path string File path within the repository
-- @param opts table|nil Optional: repository
-- @return table Symbols in file
function M.symbols_in_file(path, opts)
    opts = opts or {}
    local params = { path = path }
    if opts.repository then params.repository = opts.repository end
    return call_tool("symbols_in_file", params)
end

-- Git History and Analysis

--- Show modification history for a file.
-- @param path string File path within the repository
-- @param opts table|nil Optional: repository, commit
-- @return table Blame results
function M.git_blame(path, opts)
    opts = opts or {}
    local params = { path = path }
    if opts.repository then params.repository = opts.repository end
    if opts.commit then params.commit = opts.commit end
    return call_tool("git_blame", params)
end

--- Browse commit history with optional filters.
-- @param opts table|nil Optional: path, author, since, until, repository, limit, offset
-- @return table Commit log
function M.git_log(opts)
    opts = opts or {}
    local params = {}
    if opts.path then params.path = opts.path end
    if opts.author then params.author = opts.author end
    if opts.since then params.since = opts.since end
    if opts["until"] then params["until"] = opts["until"] end
    if opts.repository then params.repository = opts.repository end
    if opts.limit then params.limit = opts.limit end
    if opts.offset then params.offset = opts.offset end
    return call_tool("git_log", params)
end

--- Show diff between two commits.
-- @param from_commit string Base commit ID
-- @param opts table|nil Optional: to_commit, path, repository
-- @return table Diff result
function M.git_diff(from_commit, opts)
    opts = opts or {}
    local params = { from_commit = from_commit }
    if opts.to_commit then params.to_commit = opts.to_commit end
    if opts.path then params.path = opts.path end
    if opts.repository then params.repository = opts.repository end
    return call_tool("git_diff", params)
end

--- Search git commit messages or file paths by keyword.
-- @param query string Search query string
-- @param opts table|nil Optional: search_in ("messages" or "paths"), repository, limit
-- @return table Search results
function M.git_search(query, opts)
    opts = opts or {}
    local params = { query = query }
    if opts.search_in then params.search_in = opts.search_in end
    if opts.repository then params.repository = opts.repository end
    if opts.limit then params.limit = opts.limit end
    return call_tool("git_search", params)
end

--- Show file content at a specific commit.
-- @param path string File path within the repository
-- @param opts table|nil Optional: commit, repository
-- @return table File content
function M.git_show_file(path, opts)
    opts = opts or {}
    local params = { path = path }
    if opts.commit then params.commit = opts.commit end
    if opts.repository then params.repository = opts.repository end
    return call_tool("git_show_file", params)
end

--- Identify most frequently modified files.
-- @param opts table|nil Optional: repository, limit
-- @return table Churn analysis
function M.git_analyze_churn(opts)
    opts = opts or {}
    local params = {}
    if opts.repository then params.repository = opts.repository end
    if opts.limit then params.limit = opts.limit end
    return call_tool("git_analyze_churn", params)
end

--- Find files frequently changed together.
-- @param opts table|nil Optional: repository, limit, min_count
-- @return table Coupling analysis
function M.git_analyze_coupling(opts)
    opts = opts or {}
    local params = {}
    if opts.repository then params.repository = opts.repository end
    if opts.limit then params.limit = opts.limit end
    if opts.min_count then params.min_count = opts.min_count end
    return call_tool("git_analyze_coupling", params)
end

-- Inbox and Repository Metadata

--- List all configured mailing list inboxes.
-- @return table Inbox list
function M.list_inboxes()
    return call_tool("list_inboxes", {})
end

--- Get metadata for an inbox.
-- @param opts table|nil Optional: inbox
-- @return table Inbox info
function M.get_inbox_info(opts)
    opts = opts or {}
    local params = {}
    if opts.inbox then params.inbox = opts.inbox end
    return call_tool("get_inbox_info", params)
end

--- Get aggregate statistics for an inbox.
-- @param opts table|nil Optional: inbox, period, top_authors
-- @return table Inbox statistics
function M.get_inbox_stats(opts)
    opts = opts or {}
    local params = {}
    if opts.inbox then params.inbox = opts.inbox end
    if opts.period then params.period = opts.period end
    if opts.top_authors then params.top_authors = opts.top_authors end
    return call_tool("get_inbox_stats", params)
end

--- List all registered git repositories.
-- @return table Repository list
function M.list_repositories()
    return call_tool("list_repositories", {})
end

--- Check if a pull request has been merged upstream.
-- @param pr_url string Forge pull request URL
-- @return table Upstream status
function M.check_upstream_status(pr_url)
    return call_tool("check_upstream_status", { pr_url = pr_url })
end

--- Unified search across all document sources.
-- @param query string Search query
-- @param opts table|nil Optional: limit
-- @return table Search results from all sources
function M.search_all_sources(query, opts)
    opts = opts or {}
    local params = { query = query }
    if opts.limit then params.limit = opts.limit end
    return call_tool("search_all_sources", params)
end

return M
