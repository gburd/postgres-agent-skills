# Common Pitfalls for PostgreSQL Contributors

Mistakes newcomers (and sometimes experienced contributors) make when interacting with the PostgreSQL community. Learning these saves months of frustration.

## Research Failures

### Not Reading Prior Discussions

**The most common mistake.** Your idea has almost certainly been discussed before. Often multiple times.

Before proposing anything:
1. Search the mailing list archives (via the pg.ddx.io MCP server: `search`, `hybrid_search`)
2. Look for rejected proposals on the same topic
3. Read WHY previous attempts failed — the reasons are usually still valid
4. Reference what you found: "I saw the 2019 thread about X. My approach differs because..."

### Not Understanding the Codebase

Submitting a patch without understanding the surrounding code:
- Missing existing helper functions that do what you reimplemented
- Not following the patterns established in that subsystem
- Breaking invariants you didn't know existed
- Not understanding the locking protocol for that data structure

Use the pg.ddx.io code intelligence tools: `get_callers`, `get_callees`, `get_dependents`, `get_impact`

### Not Understanding the Problem Space

Solving a problem you defined, not the problem users actually have:
- Over-specifying solutions to narrow use cases
- Not talking to actual users about what they need
- Solving the easy part and hand-waving the hard part

## Technical Pitfalls

### Ignoring Backwards Compatibility

**This is the number one technical reason patches are rejected.**

Things that break backwards compatibility (all require extraordinary justification):
- Changing behavior of existing SQL statements
- Changing output format of existing functions
- Changing default GUC values that affect behavior
- Removing or renaming public APIs
- Changing catalog structures without pg_upgrade support
- Breaking dump/restore from older versions

### Over-Engineering

Building for hypothetical future requirements:
- "We might want to support X someday, so let's add an abstraction layer"
- "This could be extended to handle Y, so let's make it configurable"
- "I added a GUC in case someone wants to tune this"

The community prefers:
- Simple code that solves today's problem
- Refactoring later when the actual need arises
- No GUCs for things that should just work correctly

### Not Testing on All Platforms

PostgreSQL supports Windows, macOS, Linux, FreeBSD, OpenBSD, NetBSD, Solaris/illumos, and AIX. Your patch must work on all of them.

Common portability failures:
- Using Linux-specific system calls
- Assuming POSIX behavior that Windows doesn't have
- Assuming 64-bit pointers
- Assuming specific endianness
- Using C99/C11 features not available on all compilers

### Missing catversion Bumps

If you change system catalogs (pg_proc entries, new catalog columns, new catalog tables, etc.), you must increment `CATALOG_VERSION_NO`. Forgetting this means databases from before and after your change are incompatible without anyone knowing.

### Incorrect Concurrency Handling

PostgreSQL is highly concurrent. Common concurrency mistakes:
- Reading shared data without appropriate locks
- Holding locks too long (causing contention)
- Deadlock potential from inconsistent lock ordering
- MVCC-unsafe operations
- Not handling race conditions in catalog access
- Assuming operations are atomic when they're not

### Memory Leaks on Error Paths

Because PostgreSQL uses longjmp for error handling (ereport/elog ERROR), you can't rely on cleanup code after the function call:

```c
/* BAD: if step_2() throws ERROR, ptr leaks */
ptr = palloc(size);
step_2();  /* might throw */
pfree(ptr);

/* GOOD: use memory contexts or PG_TRY */
```

## Social Pitfalls

### Being Impatient

- Pinging after 2 days: "Anyone? Hello?"
- Resubmitting the same patch unchanged to "bump" it
- Complaining on social media about slow reviews
- Demanding attention from committers

Reality: Reviewers are volunteers. They have jobs. Response time of 1-2 weeks is normal.

### Ignoring Review Feedback

Resubmitting a patch without addressing feedback:
- Posting v2 that's identical to v1 (hoping for a different reviewer)
- Addressing surface issues but ignoring fundamental design feedback
- Saying "I disagree" without technical argument

### Arguing from Authority

"I've been doing database development for 20 years, so my approach is correct."

The community respects technical arguments backed by evidence:
- Benchmarks
- Standards references
- Analysis of edge cases
- Demonstration of correctness

### Not Helping Others

The community values reciprocity. Contributors who only submit their own patches without reviewing others' patches are viewed less favorably. Reviewing is how you build credibility and relationships.

### Scope Creep in Discussions

Starting with "add feature X" and gradually expanding to redesigning the entire subsystem. This causes:
- The original patch becomes impossible to commit in isolation
- Discussion becomes unfocused
- Reviewers lose interest
- Nothing gets committed

Better: Submit the minimal useful change. Follow up with enhancements in separate patches.

## Process Pitfalls

### Not Using the Commitfest

Posting a patch to the list but not registering it in commitfest means:
- No reviewer will be assigned
- It won't be tracked
- It will be forgotten

### Submitting at Bad Times

- Last day of a commitfest: nobody will review it
- December/January: many contributors on holiday
- Right before feature freeze: rushed reviews, likely returned

### Not Keeping Patches Rebased

If your patch no longer applies to current master:
- Reviewers won't test it
- The commitfest manager may mark it "Waiting on Author"
- You lose momentum

### Not Splitting Large Changes

A 5000-line patch is very unlikely to be reviewed. Break it into:
1. Preparatory refactoring (minimal behavior change)
2. Infrastructure additions
3. The actual feature
4. Documentation
5. Tests (if not included with each step)

Each piece should be independently committable and reviewable.

## Recovery Strategies

### Your Patch Was Rejected — Now What?

1. Read the rejection reason carefully
2. If it's "not needed": accept it or gather evidence of real-world need
3. If it's "wrong approach": ask what the right approach would be
4. If it's "too complex": simplify aggressively
5. If it's "can be an extension": write an extension

### Your Patch Has No Reviewers — Now What?

1. Review other people's patches (reciprocity)
2. Make your patch smaller (easier to review)
3. Post a clear summary of what the patch does and why
4. Ask specific people who work in that area (politely)
5. Wait for the next commitfest (fresh round of reviews)

### You Disagree with a Committer — Now What?

1. Present your technical argument clearly with evidence
2. If they still disagree, ask for their alternative proposal
3. If neither side budges, a third committer's opinion may help
4. Know when to concede — sometimes you're wrong, sometimes it's not worth the fight
5. Never escalate outside the technical discussion
