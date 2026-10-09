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

**The specific failure mechanics, by platform:**

- **Windows symlinks are unreliable in a git checkout.** Avoid relying on
  symlinks in build or test scripts; a checkout on a Windows machine may
  silently get a text file containing the link target instead of a real
  link.
- **GNU-specific build traps.** `sed -i` without a backup-suffix argument,
  reliance on `/proc`, and GNU-dialect `sed`/`awk` constructs all fail on
  the BSDs and macOS, whose base-system `sed`/`awk` are not GNU. Write
  scripts to the POSIX-common subset or detect the platform explicitly.
- **MSVC is strict about C dialect.** Designated initializers and variable-
  length arrays (VLAs), both fine on gcc/clang, do not build on MSVC. A
  construct that compiles cleanly on your Linux box can fail the Windows
  buildfarm animal outright.
- **`%zu` vs `%lu` for `Size`.** `Size` (a `size_t`) must be printed with
  `%zu`, not `%lu` — on a 32-bit platform or a platform where `long` and
  `size_t` differ in width, `%lu` either misformats or triggers a compiler
  warning that is an error under `-Werror`.
- **`getaddrinfo`/`strto*`/shared-memory and semaphore APIs diverge by
  platform.** Behavioral differences (not just availability) in these calls
  across Linux, the BSDs, and Windows are a recurring source of "works on
  my machine" bugs; use the project's `src/include/port.h` abstractions
  rather than calling the libc function directly where one exists.
- **A change category is not verified until the full buildfarm/cfbot matrix
  is green — a local run cannot clear it alone.** This applies especially
  to: configure/meson feature detection, locale/collation/encoding/ICU code
  paths, threading/shared-memory/semaphores/atomics/barriers,
  TLS/SSL/SASL/SCRAM/GSSAPI/LDAP/Kerberos (also gated behind
  `PG_TEST_EXTRA` — set it when you touch them), timezone/`clock_gettime`
  behaviour, and any `#ifdef WIN32` / platform `#ifdef` branch (the branch
  you did not compile locally is the one that breaks).

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

### Reporting a Non-Bug (False-Positive Patterns)

Static-analysis instincts from typical C/C++ codebases misfire constantly on
the PostgreSQL backend. Before reporting a "bug" a scanner or a first pass
flagged, check whether it is actually one of these well-known non-bugs:

- **`strcmp` on an identifier or catalog name is correct, not a collation
  bug.** `strcmp` is right for C-locale / byte-exact comparisons; `varstr_cmp`
  (and the collation machinery) is for user string data. Flagging a `strcmp`
  on a relation name or similar as "collation-unaware" is a frequent false
  positive.
- **GUC validation belongs in the `check_hook`, not the `assign_hook`.** The
  assign hook is not allowed to fail — "validation in the wrong hook" is by
  design, not a missed check.
- **A missing overflow check is only a bug where attacker-influenced values
  reach plain arithmetic.** The paths that must be overflow-safe already use
  `pg_add_s32_overflow` and friends; plain arithmetic in paths that cannot
  overflow (bounded internal counters, fixed-size loops) is fine as written.
- **A signal handler that only sets a `volatile sig_atomic_t` flag is
  correct, not incomplete.** Signal handlers and postmaster paths must be
  async-signal-safe; "just take a lock" advice from general C guidance is
  wrong here — taking a lock in a handler is the actual bug.
- **Calling libc `free()` on `palloc`'d memory (or `pfree` on `malloc`'d
  memory) is the real bug — a missing `pfree` on context-allocated memory is
  not.** Most backend allocations live in a `MemoryContext` reset or deleted
  in bulk at a well-defined lifetime boundary; a missing `pfree` there is
  normal and often intentional. Only flag it when the allocation accumulates
  in a long-lived context (`TopMemoryContext`, `CacheMemoryContext`).
- **Build with `--enable-cassert`/`-Dcassert=true` and reproduce before
  reporting anything.** Many genuine backend bugs only manifest under
  assertions, and most of the false-positive patterns above vanish once you
  understand the idiom and see the assertion-enabled build still pass.

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
