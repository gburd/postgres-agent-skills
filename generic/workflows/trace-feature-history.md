# Workflow: Trace a Feature from RFC to Merge

Follow the complete lifecycle of a PostgreSQL feature from initial proposal through design, implementation, review, and final commit.

## Inputs

- `feature`: The feature name or description (e.g., "table partitioning", "JSON path queries")
- `approximate_version`: (optional) The PostgreSQL version where the feature appeared

## Steps

### 1. Find the Original Proposal

```
search(query: "s:RFC feature OR s:proposal feature", inbox: "pgsql-hackers")
```

If you know the approximate version, use date filtering:
```
search(query: "s:feature d:start-year..end-year", inbox: "pgsql-hackers")
```

### 2. Read the Initial Discussion

```
get_thread(message_id: "<rfc-thread-id>")
```

Look for:
- Who proposed it
- Initial community reaction
- Design alternatives discussed
- Requirements established

### 3. Find the Design Evolution

Many features go through multiple design iterations:

```
# Find follow-up threads
get_thread_references(message_id: "<rfc-thread-id>")
find_similar_messages(message_id: "<rfc-message-id>")

# Search for design-phase discussions
search(query: "s:feature design OR s:feature approach", inbox: "pgsql-hackers")
```

### 4. Find the Implementation Patches

```
search_patches(query: "feature")
search(query: "s:[PATCH feature", inbox: "pgsql-hackers")
```

### 5. Track Review Iterations

For each patch version, read the review thread:

```
get_thread(message_id: "<patch-v1-id>")
get_thread(message_id: "<patch-v2-id>")
# ... etc
```

Look for:
- Reviewer concerns
- What changed between versions
- When it reached "Ready for Committer"

### 6. Find the Commit

```
search(query: "s:feature", inbox: "pgsql-committers")
git_search(query: "feature")
```

### 7. Find Post-Commit Activity

Features often get follow-up fixes:

```
git_log(path: "relevant/file/path.c", since: "commit-date")
search(query: "s:Fix feature OR s:feature bug", inbox: "pgsql-hackers")
```

## Outputs

- Complete timeline from RFC to commit
- Key design decisions and alternatives rejected
- List of all people involved (proposer, reviewers, committer)
- Commit hash(es) of the final implementation
- Any known follow-up issues or improvements

## Example

Feature: "Parallel Hash Join" (PostgreSQL 11)

```
# 1. Find the RFC (around 2016-2017)
search(query: "s:parallel hash d:2016-01..2017-12", inbox: "pgsql-hackers")

# 2. Find patches
search_patches(query: "parallel hash join")

# 3. Find the commit
search(query: "s:parallel hash", inbox: "pgsql-committers")
git_search(query: "parallel hash join")

# 4. Trace the full implementation
git_log(path: "src/backend/executor/nodeHashjoin.c")
```
