# Patch Review Context

Use this skill when reviewing PostgreSQL patches or helping users understand patch review processes. Provides methods to find prior art, understand reviewer concerns, and navigate the commitfest process.

## Finding Prior Art

Before reviewing or proposing any patch, check what has been tried before:

```
# Search for previous attempts at the same feature
search(query: "s:feature-name", inbox: "pgsql-hackers")

# Find rejected patches on the same topic
search(query: "s:feature-name withdrawn OR rejected OR abandoned")

# Check if there's existing commitfest activity
search_patches(query: "feature-name")

# Find the original RFC/proposal
search(query: "s:RFC feature-name OR s:proposal feature-name", inbox: "pgsql-hackers")
```

## Understanding Reviewer Concerns

PostgreSQL reviewers have consistent concerns. Find what they typically push back on:

```
# Find review threads for similar features
search(query: "s:Re: feature-name review")

# Look at a specific reviewer's feedback patterns
get_author_messages(author: "reviewer@email", inbox: "pgsql-hackers")

# Find discussions about design patterns used in the patch
hybrid_search(query: "design concern about approach-X in PostgreSQL")
```

## Review Checklist (What Committers Look For)

### Correctness
- Does it handle all edge cases? (NULL, empty, concurrent access, OOM)
- Is it safe under concurrent execution?
- Does it handle errors properly (no leaked resources on error paths)?
- Are all code paths tested?

### Backwards Compatibility
- Does it break existing queries or behavior?
- Does it require a catversion bump? (any catalog change does)
- Does it need pg_upgrade support?
- Are dump/restore semantics preserved?

### Code Quality
- Does it follow PostgreSQL coding conventions? (pgindent clean)
- Are variable names consistent with surrounding code?
- Are comments clear and accurate?
- Is the commit message well-structured?

### Performance
- Does it add overhead to common paths?
- Are there unnecessary allocations?
- Is the algorithm appropriate for the data sizes involved?
- Has it been benchmarked?

### Documentation
- Are docs updated for user-visible changes?
- Do docs explain the feature clearly for end users?
- Are there examples in the docs?

### Testing
- Are there regression tests?
- Do tests cover edge cases?
- Do tests exercise error paths?
- Are tests deterministic (no race conditions in expected output)?

## Navigating the Commitfest

The commitfest is PostgreSQL's patch tracking system. Patches go through states:

1. **Needs Review** — Waiting for someone to look at it
2. **Waiting on Author** — Reviewer found issues, author needs to respond
3. **Ready for Committer** — Reviewed and approved, waiting for commit
4. **Committed** — Done
5. **Returned with Feedback** — Not ready for this release, try again
6. **Withdrawn** — Author gave up or decided against it
7. **Rejected** — Community decided against it

### Finding Commitfest Context

```
# Find the patch series submissions
search_patches(query: "feature-name", inbox: "pgsql-hackers")

# Get the full patch series with all versions
get_patch_series(pr_url: "https://github.com/postgresql/postgresql/pull/NNN")

# Check if a patch was merged
check_upstream_status(pr_url: "https://...")
```

## Multi-Version Patch Review

Patches often go through many versions. Track the evolution:

```
# Find all versions
search(query: "s:[PATCH v feature-name", inbox: "pgsql-hackers")

# Read the cover letter for each version to understand changes
# Cover letters are [PATCH vN 0/M] messages
search(query: "s:[PATCH v2 0/ feature-name", inbox: "pgsql-hackers")

# Find what changed between versions by reading inter-version discussion
get_thread(message_id: "<v1-thread-id>")
get_thread(message_id: "<v2-thread-id>")
```

## Common Rejection Reasons

Understanding why patches get rejected helps avoid the same mistakes:

1. **"This can be done in an extension"** — Core should be minimal; if it can reasonably live outside, it should
2. **"Not enough use cases"** — Feature must justify its maintenance burden
3. **"Breaks backwards compatibility"** — Almost never acceptable without very strong justification
4. **"Performance regression on common workloads"** — Even if the new feature is faster for its case
5. **"Too complex for the benefit"** — Complexity has ongoing maintenance cost
6. **"Design not settled"** — Go back to RFC stage
7. **"Needs more testing"** — Insufficient test coverage
8. **"Doesn't handle concurrent access correctly"** — Very common issue

## Providing Review Context

When helping someone understand a patch's context:

```
# Who proposed it and when?
search(query: "s:[PATCH v1 feature-name", inbox: "pgsql-hackers")

# What problem does it solve?
# (read the cover letter / first message)

# Who reviewed it?
get_thread(message_id: "<thread-id>")

# Were there objections?
# (look for messages from committers with concerns)

# What's the current status?
search_patches(query: "feature-name")

# Is there related work in progress?
search(query: "s:feature-name d:2024-01..", inbox: "pgsql-hackers")
```
