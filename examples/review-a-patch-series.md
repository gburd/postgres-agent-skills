# Example: Review a Multi-Version Patch Series

This example demonstrates using the pg.ddx.io MCP server to understand the full context of a patch series that went through multiple review cycles before being committed (or rejected).

## Scenario

You want to review (or understand the history of) a significant patch series — something like "Add MERGE statement support" which went through many versions over several years.

## Step 1: Find All Versions of the Patch

```
# Find the patch series
search_patches(query: "MERGE statement")

# Find all versions by subject pattern
search(query: "s:[PATCH MERGE statement", inbox: "pgsql-hackers")

# Narrow to specific version patterns
search(query: "s:[PATCH v1 MERGE", inbox: "pgsql-hackers")
search(query: "s:[PATCH v2 MERGE", inbox: "pgsql-hackers")
# ... continue for each version
```

## Step 2: Read the Cover Letters

Cover letters (`[PATCH vN 0/M]`) describe the series and what changed:

```
# Find cover letters for each version
search(query: "s:[PATCH v1 0/ MERGE", inbox: "pgsql-hackers")
search(query: "s:[PATCH v2 0/ MERGE", inbox: "pgsql-hackers")

# Read the full cover letter
get_message(message_id: "<cover-letter-message-id>")
```

Each cover letter should explain:
- What the patch does
- Changes since the previous version
- Outstanding issues or questions
- How to test it

## Step 3: Read the Review Discussion for Each Version

```
# Get the full thread for v1
get_thread(message_id: "<v1-cover-letter-id>")

# Get the full thread for v2
get_thread(message_id: "<v2-cover-letter-id>")
```

For each version, identify:
- Who reviewed it
- What concerns were raised
- What was approved
- What needed to change for the next version

## Step 4: Identify the Key Reviewers and Their Concerns

```
# Find the main reviewers
# (read threads and note who provides substantial feedback)

# Get more context on a specific reviewer's perspective
get_author_messages(author: "reviewer@email", after: "relevant-period-start")

# Find if the reviewer has reviewed similar patches
search(query: "f:reviewer@email s:similar-topic", inbox: "pgsql-hackers")
```

### Common Reviewer Patterns to Watch For

- **Tom Lane** often catches subtle backwards-compatibility issues and syntax ambiguities
- **Andres Freund** focuses on performance implications and concurrency correctness
- **Robert Haas** evaluates whether the feature belongs in core and its design simplicity
- **Heikki Linnakangas** catches low-level implementation bugs and WAL-safety issues

## Step 5: Find the Original RFC/Design Discussion

Major features start with design discussion before any code:

```
# Find the initial proposal (often months or years before the patch)
search(query: "s:RFC MERGE OR s:proposal MERGE", inbox: "pgsql-hackers")
search(query: "s:MERGE statement design", inbox: "pgsql-hackers")

# Use semantic search for conceptual discussions
hybrid_search(query: "SQL MERGE statement design discussion PostgreSQL")
```

## Step 6: Understand the Code Being Changed

```
# Find what functions the MERGE patch adds/modifies
search_symbols(query: "ExecMerge")
search_symbols(query: "MERGE", kind: "function")

# Understand the execution path
get_symbol(qualified_name: "ExecMerge")
get_callees(qualified_name: "ExecMerge")
get_callers(qualified_name: "ExecMerge")

# See what existing code it integrates with
get_impact(qualified_name: "ExecModifyTable")
find_imports(path: "src/backend/executor/nodeModifyTable.c")
```

## Step 7: Check if It Was Committed

```
# Find the commit notification
search(query: "s:MERGE", inbox: "pgsql-committers")
git_search(query: "MERGE statement")

# Or check upstream status if it was submitted via forge
check_upstream_status(pr_url: "https://github.com/...")

# Find the final commit
git_log(path: "src/backend/executor/nodeModifyTable.c")
```

## Step 8: Find Post-Commit Issues

After a feature is committed, bugs and follow-up improvements often appear:

```
# Bug reports
search(query: "s:MERGE bug OR crash OR wrong result", inbox: "pgsql-bugs")
search(query: "s:MERGE", inbox: "pgsql-bugs")

# Follow-up fixes
git_search(query: "Fix MERGE")
search(query: "s:Fix MERGE", inbox: "pgsql-committers")

# Enhancement proposals
search(query: "s:MERGE enhancement OR improvement d:post-commit-date..", inbox: "pgsql-hackers")
```

## Step 9: Build the Complete Timeline

Assemble everything into a chronological narrative:

```
# Use date-bounded searches to build the timeline
search(query: "s:MERGE d:2017-01..2017-12", inbox: "pgsql-hackers")  # Early discussion
search(query: "s:MERGE d:2018-01..2018-12", inbox: "pgsql-hackers")  # Design phase
search(query: "s:MERGE d:2019-01..2019-12", inbox: "pgsql-hackers")  # Implementation
search(query: "s:MERGE d:2020-01..2020-12", inbox: "pgsql-hackers")  # Review cycles
search(query: "s:MERGE d:2021-01..2022-12", inbox: "pgsql-hackers")  # Final push
```

## Analysis Template

After gathering all the data, structure your analysis:

### 1. Timeline
- When was it first proposed?
- How many versions were submitted?
- How long from RFC to commit?
- Were there breaks/restarts?

### 2. Design Evolution
- What was the original design?
- What changed and why?
- Were there competing implementations?
- What design decisions were made and why?

### 3. Review Summary
- Who reviewed it?
- What were the main concerns?
- Which concerns recurred across versions?
- What was the blocking issue(s)?

### 4. Community Dynamics
- Was there consensus or controversy?
- Did any committer champion it?
- Did any committer oppose it?
- How was disagreement resolved?

### 5. Technical Assessment
- Is the final implementation sound?
- Were the reviewer concerns adequately addressed?
- Are there known limitations or follow-up work needed?
- What test coverage does it have?

### 6. Lessons Learned
- What could the author have done differently?
- What patterns from this review apply to other patches?
- What community norms are demonstrated?
