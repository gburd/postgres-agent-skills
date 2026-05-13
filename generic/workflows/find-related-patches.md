# Workflow: Find All Related Patch Submissions

Given a topic, find all related patch submissions across the PostgreSQL mailing lists.

## Inputs

- `topic`: The feature, subsystem, or concept to search for (e.g., "parallel hash join", "MERGE statement", "logical replication")

## Steps

### 1. Search for Patch Series

Use `search_patches` to find structured patch submissions with version/sequence metadata:

```
search_patches(query: "topic")
```

This parses `[PATCH vN M/K]` subject prefixes and groups patches into series.

### 2. Search for RFC/Proposal Threads

Find the original proposals that preceded the patches:

```
search(query: "s:RFC topic OR s:proposal topic", inbox: "pgsql-hackers")
```

### 3. Search for All Patch Versions

Find every version submitted:

```
search(query: "s:[PATCH topic", inbox: "pgsql-hackers")
```

### 4. Get Patch Series Details (if forge PR exists)

If the patch is tracked via a forge pull request:

```
get_patch_series(pr_url: "https://github.com/postgresql/postgresql/pull/NNN")
```

### 5. Read Cover Letters

Cover letters (`[PATCH vN 0/M]`) explain what changed between versions:

```
search(query: "s:[PATCH v2 0/ topic", inbox: "pgsql-hackers")
get_message(message_id: "<cover-letter-id>")
```

### 6. Check Upstream Status

Determine if a patch was merged:

```
check_upstream_status(pr_url: "https://...")
```

### 7. Find Review Discussion

```
get_thread(message_id: "<patch-message-id>")
```

## Outputs

- List of all patch versions with dates and authors
- Current status (committed, withdrawn, under review, returned)
- Key review comments and objections
- Link to the final committed version (if applicable)

## Example

Topic: "incremental backup"

```
search_patches(query: "incremental backup")
search(query: "s:RFC incremental backup", inbox: "pgsql-hackers")
search(query: "s:[PATCH incremental backup", inbox: "pgsql-hackers")
# Read the threads of the most recent versions
```
