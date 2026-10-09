# PostgreSQL Decision Making

How consensus is reached, the role of committers, and how things get done in the PostgreSQL project.

## The Consensus Model

### No Formal Voting

PostgreSQL has never used formal voting for technical decisions. There is no:
- +1/-1 voting system
- Formal RFC process with numbered documents
- Technical steering committee (for day-to-day decisions)
- Benevolent Dictator For Life

### What Consensus Means in Practice

A proposal has consensus when:
- At least one committer is willing to champion it (review and commit)
- No committer has a sustained, unresolved objection
- The author has addressed all substantive review feedback
- The implementation is technically sound

A proposal lacks consensus when:
- A committer objects and the objection is not addressed
- The community is split with strong feelings on both sides
- The design keeps changing without stabilizing
- Nobody cares enough to review it (consensus by indifference = no)

### The "Lazy Consensus" Pattern

Most decisions are made through lazy consensus:
1. Someone proposes a change
2. Nobody objects within a reasonable time
3. It goes in

This works because:
- The community trusts committers to exercise good judgment
- Bad decisions can be reverted
- Most changes are uncontroversial

## Committer Authority

### Who Are Committers?

Committers are developers who have been granted push access to the PostgreSQL repository. As of 2024-2025, there are approximately 30 active committers. They are the only people who can make changes to the official source.

### How Committers Are Chosen

- Demonstrated sustained contribution over years (not months)
- Technical excellence in a specific area
- Good judgment about what belongs in core
- Trusted by existing committers
- Formally: existing committers agree to grant access

### Committer Discretion

Each committer exercises individual judgment:
- They can commit patches they believe are ready
- They can reject patches they believe are not ready
- They typically specialize in certain subsystems
- They can (and do) overrule reviewer recommendations

### The Champion Model

For a patch to be committed:
1. It must have at least one committer willing to take responsibility for it
2. That committer reviews it themselves (even if others already reviewed)
3. They commit it, which means they're accountable for any problems

This is why patches with zero committer interest die — nobody will take the risk.

## How Disagreements Are Resolved

### Technical Disagreements

1. Discussion on pgsql-hackers with technical arguments
2. If unresolved, more senior/experienced voices often break ties
3. Sometimes prototypes or benchmarks are requested to prove a point
4. Rarely: the "let's sleep on it" approach (wait a commitfest or two)

### Design Disagreements

1. RFC thread explores alternatives
2. Community gravitates toward one approach
3. If still split: the person writing the code usually wins (within reason)
4. Committers have final say on what enters the tree

### Process Disagreements

Handled at the community level:
- PostgreSQL Core Team (mostly administrative/legal, not technical)
- Release Management Team (decides release schedule)
- Commitfest managers (coordinate review efforts)
- These are not dictatorial roles — they facilitate, not decide

## The "Committed" vs "Pushed" Distinction

Technically, committing = pushing to the official repo. But there's an implicit progression:

1. **Patch exists**: Code is written
2. **Reviewed**: Someone checked it
3. **Ready for Committer**: Reviewer approves
4. **Committed**: A committer pushes it to master
5. **Released**: It ships in a GA release

After (4), the change can still be reverted if problems emerge. The release in (5) is the true point of no return for backwards compatibility.

## Decision Documentation

### Where Decisions Are Recorded

- **Mailing list archive**: The primary record. The thread IS the decision.
- **Commit messages**: Summarize the decision and link to the thread
- **Source code comments**: Explain non-obvious decisions in the code
- **Documentation**: User-facing explanation of features
- **TODO files**: Known issues and future work (in the source tree)

### There Is No Design Document Repository

Unlike some projects, PostgreSQL does not maintain:
- Architecture documents (beyond the source code itself)
- Design decision records (ADRs)
- Technical specification documents

The mailing list archive serves this purpose. If you want to understand why PostgreSQL does something a particular way, search the archives for when it was introduced.

## The Release Team

### Composition
- Small group of long-standing committers
- Makes decisions about:
  - When to branch for a release
  - When to call feature freeze
  - When to ship beta/RC/GA
  - When to end-of-life old versions

### Release Authority
- Can delay release for critical bugs
- Cannot force features in or out (that's committer discretion)
- Sets the timeline that development works against

## Power Dynamics (Implicit)

### Influence Hierarchy (roughly)
1. Long-serving committers with deep expertise (Tom Lane, Andres Freund, etc.)
2. Active committers who review and commit regularly
3. Less active committers (still have commit authority)
4. Regular contributors without commit access but strong reputation
5. Occasional contributors
6. First-time contributors

### How Influence Is Earned
- Years of sustained, high-quality contribution
- Reviewing others' patches (very highly valued)
- Maintaining existing code (not just adding new features)
- Being right often and admitting when wrong
- Helping new contributors

### How Influence Is Lost
- Committing broken code repeatedly
- Ignoring review feedback from others
- Pushing personal agendas over project benefit
- Going silent for extended periods (influence is perishable)

## The "Extension First" Doctrine

An increasingly important decision principle:
- If a feature CAN reasonably be an extension, it SHOULD be
- Core is for features that fundamentally require server internals
- Extensions can iterate faster and break compatibility freely
- This reduces the maintenance burden on the core team

Debates about "core vs extension" are among the most common and most important in the project.

## Reading the Signals (a cheat sheet)

An agent that treats a PostgreSQL thread like a GitHub PR — silence as
approval, a merge as the goal, a reply as a decision — will consistently
misread the project. The signals committers give are subtle and conversational,
not a status field:

- **A quick positive reply from a committer** is a strong signal of acceptance.
- **Silence is not agreement.** It usually means nobody cares enough to
  champion the idea, and it will quietly die. Do not treat an unanswered
  proposal as approved — "consensus by indifference" is a no, not a yes.
- **"I'm not sure we need this"** from a committer is a soft rejection, not an
  open question.
- **"This would need to…"** is conditional interest — a requirement being
  stated, not a rejection; address it and the thread may move forward.
- **"NAK" / "-1"** is a strong, rare, and serious objection.
- **"Let's revisit for the next release"** is a polite deferral that may or
  may not actually happen — track it, don't assume it will resurface on its
  own.
- **A long debate with no resolution** means the feature may be too
  controversial for this cycle, not that it is close to landing.

## For an Agent Specifically

- **Do not infer approval from silence** or from a single reply. The absence
  of an objection is not the presence of consensus.
- **Do not treat "merged" as the objective.** The point of a thread is to
  reach the right design; surface the trade-off and the open questions, and
  let the humans decide whether and when to commit.
- **Never post to a mailing list to force a decision.** A human owns and
  sends all list traffic; an agent prompting a thread for a ruling is not how
  this project reaches consensus and will be read as impatience, which costs
  credibility (see "How Influence Is Lost" above).
