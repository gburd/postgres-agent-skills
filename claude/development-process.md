# PostgreSQL Development Process

Use this skill to understand how PostgreSQL development is organized: the release cycle, commitfest process, and how patches flow from idea to release.

## Release Cycle

PostgreSQL follows a roughly annual release cycle:

### Timeline (approximate, varies by year)

| Phase | Timing | What Happens |
|-------|--------|--------------|
| Development opens | After prior release branch | New features accepted |
| Commitfest 1 | ~November | First batch of patches reviewed |
| Commitfest 2 | ~January | Second batch |
| Commitfest 3 | ~March | Third batch |
| Commitfest 4 (last) | ~May | Final chance for new features |
| Feature freeze | ~April/May | No new features after this |
| Beta 1 | ~May/June | Public testing begins |
| Beta 2-N | Monthly | Bug fixes only |
| RC 1 | ~September | Release candidate |
| Release | ~September/October | GA release |

### What Each Phase Means for Patches

- **Before feature freeze:** New features accepted if they pass review
- **After feature freeze:** Only bug fixes, documentation, and performance improvements
- **During beta:** Bugs found in new features can still be fixed
- **After RC:** Only critical/security bugs
- **After release:** Only back-patchable bug fixes to stable branches

## The Commitfest Process

A commitfest is a coordinated review period. The community focuses on reviewing submitted patches.

### Commitfest Lifecycle

1. Patches are registered at https://commitfest.postgresql.org/
2. During the commitfest, reviewers pick up patches
3. Patches move through states: Needs Review → Waiting on Author → Ready for Committer
4. At the end of the commitfest, unfinished patches are moved to the next one or returned

### Patch States

- **Needs Review** — Nobody has reviewed it yet
- **Waiting on Author** — Reviewer found issues; author must respond
- **Ready for Committer** — Reviewed and approved; committer should look
- **Committed** — Done, in the tree
- **Moved to next CF** — Didn't get reviewed in time
- **Returned with Feedback** — Not ready, come back later
- **Withdrawn** — Author pulled it
- **Rejected** — Community decided against it (rare, usually just "returned")

### How Patches Flow

```
Idea → RFC email → Discussion → [PATCH v1] → Review → [PATCH v2] → ...
                                                          ↓
                                              Ready for Committer
                                                          ↓
                                                    Committed
                                                          ↓
                                              pgsql-committers notification
```

## Finding Process Information via Agora

### Track a Patch Through the Process

```
# Find initial proposal
search(query: "s:RFC feature-name OR s:proposal feature-name", inbox: "pgsql-hackers")

# Find patch submissions (all versions)
search_patches(query: "feature-name")

# Find review discussion
search(query: "s:Re: [PATCH feature-name", inbox: "pgsql-hackers")

# Find the commit
search(query: "s:feature-name", inbox: "pgsql-committers")
git_search(query: "feature-name")

# Check if a PR-style submission was merged
check_upstream_status(pr_url: "https://github.com/...")
```

### Understand Current Development Focus

```
# What's being discussed now?
list_threads(inbox: "pgsql-hackers")

# What patches are active?
search_patches(inbox: "pgsql-hackers")

# What's a specific author working on?
get_author_messages(author: "developer@email", after: "2024-01-01")

# What was committed recently?
list_recent(inbox: "pgsql-committers")
```

### Understand Historical Development

```
# What happened in a specific commitfest period?
browse_by_date(after: "2024-03-01", before: "2024-03-31", inbox: "pgsql-hackers")

# Track development activity over time
git_analyze_activity(period: "month")

# Who are the most active developers?
git_analyze_authors()
get_inbox_stats(inbox: "pgsql-hackers")
```

## Branch and Release Management

### Branch Naming
- `main` (or `master` historically) — development branch
- `REL_17_STABLE` — stable branch for version 17
- `REL_16_STABLE` — stable branch for version 16
- Older: `REL9_6_STABLE` (underscore instead of dot)

### Back-Patching Rules
- Bug fixes are back-patched to all supported branches (usually 5 years)
- Security fixes get immediate back-patching
- New features never go to stable branches
- Performance improvements sometimes back-patched if low-risk

### The "catversion bump" Rule
Any change to system catalogs requires incrementing `CATALOG_VERSION_NO` in `src/include/catalog/catversion.h`. This means:
- All existing databases must be dumped and reloaded (or pg_upgraded)
- It can only happen before feature freeze
- It signals a "this changes the on-disk format" level of impact

## Development Infrastructure

- **Git repository:** https://git.postgresql.org/gitweb/?p=postgresql.git
- **Mailing lists:** https://www.postgresql.org/list/ (archives at Agora)
- **Commitfest:** https://commitfest.postgresql.org/
- **Bug tracker:** https://www.postgresql.org/account/submitbug/
- **Build farm:** https://buildfarm.postgresql.org/ (multi-platform CI)
- **Documentation:** https://www.postgresql.org/docs/

## Key Concepts

### The "Extension vs Core" Debate
Features that CAN be extensions SHOULD be extensions. Core additions carry eternal maintenance burden. The community is increasingly pushing things toward extensions (e.g., pg_stat_statements, pg_trgm, etc. are extensions, not core).

### The "Committer Discretion" Principle
There is no voting. Committers exercise judgment. A patch needs:
- At least one committer willing to review and commit it
- No strong objections from other committers
- Consensus that it belongs in core

### The "One Feature, One Commit" Rule
Each commit should be atomic — one logical change. Large features are split into preparatory refactoring commits followed by the feature commit. This makes bisection and back-patching possible.
