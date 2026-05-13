# Commit Archaeology

Use this skill to trace PostgreSQL code back to its original mailing list discussion. Every significant change in PostgreSQL was discussed on-list before being committed. This skill bridges git history to the email archive.

## The Archaeology Process

### Step 1: Find the Commit

Start from a line of code or a function and find when it was introduced:

```
# Find the commit that last touched a file/line
git_blame(path: "src/backend/executor/execMain.c")

# Or search for commits about a topic
git_search(query: "add parallel query support")

# Or look at a specific file's history
git_log(path: "src/backend/optimizer/path/costsize.c")
```

### Step 2: Extract the Message-ID

PostgreSQL commit messages almost always contain a reference to the mailing list discussion. Look for:

- A Message-ID in angle brackets: `<CAF...@mail.gmail.com>`
- A URL to the archives
- Author attribution with an email address
- A discussion reference

```
# Get the full commit details
git_diff(from_commit: "parent-sha", to_commit: "commit-sha")

# Search for the discussion using commit info
find_related_discussions(query: "commit-sha-prefix")
```

### Step 3: Find the Discussion Thread

```
# If you have a Message-ID
get_thread(message_id: "<CAF...@mail.gmail.com>")

# If you have the committer notification
search(query: "s:commit-subject", inbox: "pgsql-committers")

# If you just have keywords from the commit message
search(query: "s:keywords from commit d:approximate-date-range", inbox: "pgsql-hackers")

# Semantic search for the concept
hybrid_search(query: "description of what the commit does")
```

### Step 4: Read the Full Context

Once you have the thread:

```
# Get all messages in the discussion
get_thread(message_id: "<id>")

# Find cross-referenced threads (often design evolved across multiple threads)
get_thread_references(message_id: "<id>")

# Find similar discussions from the same era
find_similar_messages(message_id: "<id>")
```

## Common Patterns

### Tracing a Function's Origin

```
# 1. Find the function
search_symbols(query: "ExecParallelHashJoin", kind: "function")
get_symbol(qualified_name: "ExecParallelHashJoin")

# 2. Find when it was added
git_blame(path: "src/backend/executor/nodeHashjoin.c")

# 3. Find the commit
git_log(path: "src/backend/executor/nodeHashjoin.c", author: "...")

# 4. Find the discussion
find_related_discussions(query: "parallel hash join")
# or
git_search(query: "parallel hash join")
```

### Tracing a GUC's History

```
# 1. Find where it's defined
search_symbols(query: "work_mem")
find_pattern(pattern: "DefineCustom.*work_mem")

# 2. Find commits that changed it
git_log(path: "src/backend/utils/misc/guc_tables.c")
git_search(query: "work_mem")

# 3. Find discussions about changing defaults or behavior
search(query: "s:work_mem default", inbox: "pgsql-hackers")
```

### Tracing a Bug Fix

```
# 1. Find the fix commit
git_search(query: "Fix crash in...")

# 2. Find the bug report
search(query: "keywords from bug", inbox: "pgsql-bugs")

# 3. Find if there was hackers discussion about the fix approach
search(query: "s:keywords d:around-fix-date", inbox: "pgsql-hackers")

# 4. Check if it was backported
git_log(author: "committer", since: "fix-date", until: "fix-date+7d")
```

### Tracing Why Something Was NOT Done

Sometimes the most valuable archaeology is finding why an obvious change was never made:

```
# Find proposals that were rejected
search(query: "s:proposed-change rejected OR withdrawn")

# Find discussions where the idea came up and was shot down
hybrid_search(query: "why not do proposed-change")

# Look for Tom Lane or other committer explaining why
search(query: "b:proposed-change f:tgl@sss.pทech.com")
```

## Tips for Effective Archaeology

1. **Commit messages are your Rosetta Stone.** PostgreSQL has excellent commit message discipline. The message almost always names the discussion thread.

2. **Date ranges narrow the search.** If you know a feature appeared in PG 14, search in the 14 development window (roughly 2020-2021).

3. **Check pgsql-committers.** Every commit generates a notification there with the full commit message, making it searchable.

4. **Cross-reference multiple threads.** Major features span many threads: RFC, design, implementation review, post-commit fixes. Use `get_thread_references` to find them all.

5. **Author tracking helps.** If you know who committed something, `get_author_messages` can find their discussion of it before the commit.

6. **PostgreSQL version timeline:**
   - PG 16: 2023 development cycle
   - PG 15: 2022
   - PG 14: 2021
   - PG 13: 2020
   - PG 12: 2019
   - PG 11: 2018
   - PG 10: 2017
   - PG 9.6: 2016
   - Earlier versions: subtract 1 year per version back to ~2005

7. **The mailing list predates git.** For code older than ~2010, CVS-era commits may reference `pgsql-committers` posts rather than git hashes.
