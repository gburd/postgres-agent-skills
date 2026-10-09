# Workflow: Investigate a Bug Using Archives and Code Intelligence

Use the pg.ddx.io MCP server to investigate a PostgreSQL bug by combining mailing list archives (where bugs are reported and discussed) with code intelligence (to understand the affected code paths).

## Inputs

- `bug_description`: What the bug is (e.g., "crash during parallel index build", "wrong results with CTE")
- `affected_version`: (optional) PostgreSQL version where the bug appears
- `error_message`: (optional) Exact error text or error code

## Steps

### 1. Search for Known Reports

Check if this bug (or similar) has been reported before:

```
# Search by error message
search(query: "b:exact error text", inbox: "pgsql-bugs")

# Search by topic
search(query: "s:bug-keywords", inbox: "pgsql-bugs")
hybrid_search(query: "natural language description of the bug")

# Also check pgsql-hackers for discussion of the fix
search(query: "s:Fix bug-keywords", inbox: "pgsql-hackers")
```

### 2. Find Related Bug Reports

```
# Semantic search finds conceptually similar bugs
semantic_search(query: "description of buggy behavior")

# Find similar messages to a known bug report
find_similar_messages(message_id: "<known-bug-report-id>")
```

### 3. Identify Affected Code

```
# Find the function mentioned in stack traces or error messages
search_symbols(query: "function_from_backtrace")
get_symbol(qualified_name: "crashing_function")

# Find the error-raising code
find_pattern(pattern: "ereport.*ERROR.*specific_error")

# If you know the file
symbols_in_file(path: "src/backend/relevant/file.c")
```

### 4. Understand the Code Path

```
# Who calls the crashing function?
get_callers(qualified_name: "crashing_function")

# What does it call? (where might it fail internally?)
get_callees(qualified_name: "crashing_function")

# What's the full execution flow?
get_execution_flows()
```

### 5. Check Commit History

```
# When was this code last changed?
git_blame(path: "src/backend/relevant/file.c")

# Find recent changes to the affected area
git_log(path: "src/backend/relevant/file.c", since: "one-year-ago")

# Look for related fixes
git_search(query: "Fix crash in relevant-area")
```

### 6. Find If It Was Already Fixed

```
# Check pgsql-committers for fix commits
search(query: "s:Fix bug-keywords", inbox: "pgsql-committers")

# Search git for fix commits
git_search(query: "Fix bug-keywords")

# Check if there's a newer version of the affected code
git_diff(from_commit: "version-tag", to_commit: "HEAD", path: "affected/file.c")
```

### 7. Find the Original Discussion About the Fix

```
find_related_discussions(query: "fix-commit-hash")
get_thread(message_id: "<fix-discussion-id>")
```

## Outputs

- Whether the bug is known and has been reported before
- The affected code path and what triggers the bug
- Whether a fix exists (and in which versions)
- The discussion thread explaining the root cause
- Related bugs that might share the same root cause

## Example

Bug: "Server crashes with SIGABRT when running VACUUM FULL on a table with expression indexes"

```
# 1. Search for existing reports
search(query: "s:vacuum full crash expression index", inbox: "pgsql-bugs")
search(query: "b:SIGABRT vacuum full", inbox: "pgsql-bugs")

# 2. Find the code
search_symbols(query: "lazy_vacuum_heap")
search_symbols(query: "reindex_relation")
find_pattern(pattern: "SIGABRT.*vacuum")

# 3. Check history
git_search(query: "Fix crash vacuum full expression index")
git_log(path: "src/backend/commands/vacuumlazy.c", since: "2023-01-01")

# 4. Understand what's happening
get_callers(qualified_name: "lazy_vacuum_heap_rel")
get_callees(qualified_name: "lazy_vacuum_heap_rel")
```

## Tips

- pgsql-bugs is where users report bugs; pgsql-hackers is where developers discuss fixes
- pgsql-committers shows when fixes are committed
- Stack traces in bug reports often name the exact function — search for it in code
- PostgreSQL error codes (ERRCODE_*) are searchable in the source
- Back-patched fixes appear in multiple stable branches — check git log for the fix commit being cherry-picked
- If the bug is in a recent release, check if it was introduced by a new feature (find commits since the branch point)
