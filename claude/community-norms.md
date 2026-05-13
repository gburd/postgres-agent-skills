# PostgreSQL Community Norms

Use this skill to understand PostgreSQL community methodology and etiquette. This encodes implicit knowledge about how the PostgreSQL community operates — things that are rarely written down but universally understood by long-term participants.

## How Discussions Work

### The Mailing List Is the System of Record

Everything important happens on pgsql-hackers. There is no Slack, no Discord, no Jira that matters for development decisions. If it wasn't discussed on-list, it didn't happen. This is intentional — it creates a permanent, searchable, public record of every decision.

### Thread Lifecycle

1. **RFC/Proposal** — Someone posts an idea. Subject often includes "RFC:" or "proposal:"
2. **Discussion** — Community responds. Silence is not agreement.
3. **Patch** — If the idea has support, code appears as `[PATCH v1 0/N]`
4. **Review** — Others review the code (not just the idea)
5. **Iteration** — Author posts updated versions based on feedback
6. **Commit or Reject** — A committer either commits it or it gets returned/withdrawn

### How to Interpret Responses

- **Quick positive response from a committer** = strong signal of acceptance
- **Silence** = nobody cares enough to champion this; it will likely die
- **"I'm not sure we need this"** from a committer = soft rejection
- **"This would need to..."** = conditional interest; requirements being stated
- **"NAK"** or **"-1"** = strong objection (rare, serious when it happens)
- **Long debate with no resolution** = feature may be too controversial for this cycle
- **"Let's revisit this for PG N+1"** = polite deferral, may or may not happen

### The Role of Committers

PostgreSQL has ~30 committers. They are the only people who can push to the official repository. Their opinions carry outsized weight because:

- They will maintain the code after it's committed
- They have context on long-term project direction
- They've seen many patches fail for the same reasons

Key committers to know (as of 2024-2025):
- Tom Lane — longest-serving, encyclopedic knowledge, often catches subtle issues
- Andres Freund — performance expert, infrastructure, storage
- Robert Haas — parallelism, partitioning, project direction
- Heikki Linnakangas — WAL, replication, storage internals
- Peter Eisentraut — SQL standards, build system, localization
- Michael Paquier — replication, authentication, security
- Alvaro Herrera — catalogs, DDL, partitioning
- Noah Misch — security, portability, edge cases
- Bruce Momjian — documentation, coordination, community building

## Communication Etiquette

### Email Formatting

- **Inline reply, not top-posting.** Quote the relevant part and respond below it.
- **Trim quotes.** Don't include the entire previous message.
- **Plain text only.** No HTML mail. No rich formatting.
- **Patches as attachments or inline,** formatted with `git format-patch`.
- **72-character line wrap** for prose (not for patches).

### Thread Discipline

- **One topic per thread.** Don't hijack existing threads for unrelated topics.
- **Start a new thread for new versions** if the design changed significantly.
- **Subject line prefixes:** `[PATCH v2 3/7]`, `Re:`, `RFC:`, `[BUG]`
- **Update the subject** if the conversation drifts to a new topic.

### Tone and Approach

- Direct, technical, concise. No pleasantries required (but not rude).
- Disagree by providing technical arguments, not appeals to authority.
- Acknowledge when you're wrong. "You're right, I missed that case" is respected.
- Don't take criticism personally — code review is about the code.
- Say "I don't understand" rather than pretending you do.

## Implicit Rules

### Things That Will Get Your Patch Rejected

1. Not reading prior discussions on the same topic
2. Ignoring review feedback and reposting unchanged
3. Breaking backwards compatibility without overwhelming justification
4. Adding user-visible features without documentation
5. Submitting without regression tests
6. Not running pgindent on your code
7. Changing behavior of existing SQL constructs
8. Adding GUCs for things that should just work
9. Over-engineering: "this might be useful someday"
10. Copying code from other projects without license compatibility

### Things That Earn Respect

1. Thorough research of prior art before proposing
2. Clean, well-tested, well-documented patches
3. Responsive to review feedback
4. Helping review other people's patches
5. Finding and fixing bugs in existing code
6. Patience — major features take multiple release cycles
7. Admitting when your approach is wrong and pivoting

### The "Do We Need This?" Test

Every new feature must justify its existence against:
- Maintenance burden (forever, not just today)
- Added complexity for users
- Whether it can be done in an extension instead
- Whether the use case is common enough to warrant core support
- Whether the proposed API is stable enough to commit to

## Using Agora to Understand Norms

```
# See how a topic was discussed
search(query: "s:topic", inbox: "pgsql-hackers")
get_thread(message_id: "<id>")

# See how a committer responds to patches
get_author_messages(author: "committer@email", inbox: "pgsql-hackers")

# Find examples of successful patch submissions
search_patches(query: "committed feature-name")

# Find examples of community pushback
search(query: "s:feature-name NAK OR -1 OR rejected")

# Understand community consensus on a controversial topic
hybrid_search(query: "community position on controversial-topic")
```
