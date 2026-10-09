# PostgreSQL Community Methodology

How email-driven development works, the role of archives, and how decisions are documented in threads.

## Email as the System of Record

PostgreSQL development happens entirely on mailing lists. This is not an accident or legacy — it is a deliberate architectural decision about how to run a project:

- **Permanence**: Every discussion is archived forever and publicly searchable
- **Asynchronous**: Contributors across all time zones participate equally
- **Accountable**: Every statement is attributed and timestamped
- **Transparent**: No private channels where decisions are made (with rare security exceptions)
- **Searchable**: Future developers can find why any decision was made

There is no Slack, no Discord, no Jira, no Confluence that matters for development decisions. If it wasn't discussed on the mailing list, it didn't happen.

## The Mailing Lists

### Primary Lists

| List | Purpose | Volume |
|------|---------|--------|
| pgsql-hackers | Development discussion, patches, design | Very high (~50-100 msgs/day) |
| pgsql-committers | Commit notifications | Moderate |
| pgsql-bugs | Bug reports from users | Moderate |
| pgsql-general | User questions, general discussion | Moderate |
| pgsql-announce | Release announcements | Low |
| pgsql-docs | Documentation discussion | Low |

### How Lists Interact

1. User reports bug on pgsql-bugs
2. Developer moves discussion to pgsql-hackers for fix design
3. Patch is submitted and reviewed on pgsql-hackers
4. Commit notification appears on pgsql-committers
5. If the bug exists in stable branches, back-patch is discussed

## How Decisions Are Made

### The Non-Process Process

PostgreSQL has no formal decision-making process. No voting, no RFCs with numbers, no governance board for technical decisions. Instead:

1. Someone proposes something on pgsql-hackers
2. People respond (or don't)
3. If there's interest, a patch appears
4. The patch is reviewed
5. A committer decides to commit it (or not)

### What "Consensus" Means

- **Not unanimity** — not everyone has to agree
- **No strong objections from committers** — one committer's sustained objection can block
- **At least one champion** — somebody must care enough to push it through
- **Rough agreement on design** — implementation details can be iterated

### The Weight of Silence

Silence on pgsql-hackers is ambiguous:
- It might mean "nobody objects" (for obvious fixes)
- It usually means "nobody cares enough to invest time reviewing this"
- It never means "everyone agrees this is great"
- A patch with no reviews will not get committed no matter how long it waits

### How Proposals Die

Most proposals die not from active rejection but from:
1. **No champion**: Nobody cares enough to write the code
2. **No reviewer**: Code exists but nobody reviews it
3. **Lost momentum**: Author stops responding to feedback
4. **Commitfest timeout**: Returned with feedback too many times
5. **Scope creep**: Discussion expands until it's too complex to tackle

## The Role of Archives

### Archives as Institutional Memory

The mailing list archive IS the documentation of why PostgreSQL is the way it is. When you ask "why does PostgreSQL do X this way?" the answer is almost always in a thread from when X was implemented.

### How to Use Archives Effectively

- **Before proposing anything**: Search for prior discussions. It has almost certainly been discussed before.
- **Before reviewing patches**: Find the original RFC to understand the design intent.
- **When debugging**: Search for similar bug reports — someone may have hit the same issue.
- **When maintaining code**: Find the original commit and its discussion to understand why it's done that way.

### The 40-Year Archive

PostgreSQL's mailing lists go back to the mid-1990s. This means:
- Design rationale for even ancient features is findable
- The evolution of thinking on any topic can be traced
- Community norms are demonstrated by decades of consistent behavior
- Mistakes and their corrections are documented

## Email-Driven Development vs. Modern Tools

### What PostgreSQL Doesn't Use (and Why)

| Modern Tool | Why PostgreSQL Doesn't Use It |
|-------------|-------------------------------|
| GitHub PRs | Not permanent enough, owned by a company, doesn't support the review style |
| Slack/Discord | Ephemeral, not searchable long-term, excludes timezone-disadvantaged |
| Jira/Linear | Overhead for what git + email already provides |
| Wiki for decisions | Editable means not authoritative; email is immutable record |
| CI/CD platforms | Build farm serves this purpose, email integration preferred |

### What This Means for Contributors

- You must be comfortable with email-based workflow
- Your contributions will be public and permanent
- You cannot hide behind a PR review queue — you must actively participate in discussion
- Your commit messages matter because they're the bridge from code to discussion

## The Commit Message as Documentation

PostgreSQL commit messages follow a pattern:

```
Short summary of the change

Longer description of what and why. May reference the discussion
thread by Message-ID or describe the design decisions.

Author: Patch Author <email@example.com>
Reviewed-by: Reviewer Name <reviewer@example.com>
Discussion: https://postgr.es/m/Message-ID@example.com
```

The `Discussion:` link is critical — it connects code to its full context in the archives.
