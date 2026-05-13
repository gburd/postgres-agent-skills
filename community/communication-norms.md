# PostgreSQL Communication Norms

Mailing list etiquette: formatting, quoting, threading, and the implicit social rules of pgsql-hackers.

## Email Formatting

### Plain Text Only
- No HTML email. Ever.
- No rich text, no embedded images, no styled fonts
- Many list subscribers use mutt, Alpine, or text-mode clients
- HTML messages are sometimes silently dropped or mangled

### Line Wrapping
- Wrap prose at 72 characters
- Don't wrap code, diffs, or patches (they should be verbatim)
- Don't use format=flowed

### Quoting Style
**Inline reply only. Never top-post.**

Correct:
```
> Previous person wrote this specific point about
> the buffer management approach.

My response to that specific point goes here,
directly below the relevant quote.

> They then made another point about locking.

And my response to the locking point goes here.
```

Incorrect (top-posting):
```
Here is my response to everything below.

--- Original Message ---
Full text of previous message...
```

### Quote Trimming
- Delete parts of the quoted message you're not responding to
- Leave enough context to understand what you're replying to
- Mark elisions with `[...]` if helpful

### Attribution Lines
```
On 2024-03-15 14:30, Tom Lane wrote:
> quoted text
```

## Thread Discipline

### One Topic Per Thread
- Don't hijack an existing thread to discuss something different
- If discussion drifts to a new topic, start a new thread with a new subject
- Reply to the right message in the thread (for proper threading)

### When to Start a New Thread
- New feature proposal
- Significant design change from original topic
- New version of a patch (sometimes — judgment call)
- Unrelated question triggered by reading a thread

### Subject Line Conventions
| Prefix | Meaning |
|--------|---------|
| `[PATCH v2 3/7]` | Patch submission, version 2, part 3 of 7 |
| `RFC:` | Request for comments, pre-patch stage |
| `Re:` | Reply (added automatically by email) |
| `[BUG]` | Bug report (more common on pgsql-bugs) |
| `WIP:` | Work in progress, not ready for review |

### Updating the Subject
If the conversation has drifted, update the subject:
```
Subject: Re: New topic (was: Original topic)
```

## Tone and Social Norms

### Expected Tone
- Direct and technical. No filler.
- Disagreement is normal and expected — argue the technical point
- Terse is fine. "NAK, this breaks X case." is a valid complete response.
- Politeness is valued but verbosity is not

### Things That Are Normal
- Pointing out flaws in someone's approach without softening
- Saying "no" without extensive justification (especially from committers)
- Silence (means "I don't care about this enough to respond")
- Quick one-line responses
- Asking someone to do more work ("needs tests", "needs docs")
- Disagreeing with someone more senior

### Things That Are Not Acceptable
- Personal attacks or insults
- Dismissing someone's contribution without technical reason
- Ignoring repeated review feedback
- Relitigating settled decisions without new evidence
- Spamming the list with the same proposal after rejection
- Cross-posting the same message to multiple lists without reason

### How to Acknowledge
When someone helps you:
- "Thanks, fixed in v2" is sufficient
- You don't need extensive praise
- Fixing the issue IS the acknowledgment

### How Silence Is Interpreted
Context matters:
- Silence on an RFC = "nobody is interested enough to champion this"
- Silence on a review request = "nobody has time right now" (not rejection)
- Silence after you respond to feedback = reviewer may be busy (wait)
- Silence from a committer after "ready for committer" = they'll get to it
- Prolonged silence (months) on a patch = it's effectively dead unless you revive it

## Response Expectations

### Timing
- Don't expect same-day responses (people have jobs, time zones)
- A week without response is normal
- After 2-3 weeks, a gentle ping ("any thoughts on this?") is acceptable
- During commitfest, responses are faster
- During holiday seasons (December, August), expect delays

### Ping Etiquette
```
Acceptable: "Ping — any thoughts on this patch? Happy to address any concerns."
Not acceptable: "Hello? Anyone? This has been sitting for 3 days."
```

### When to Give Up
If your proposal receives no interest after:
- An RFC with zero responses after 2+ weeks
- A patch registered in commitfest that gets no reviewer for a full commitfest cycle
- Multiple versions with the same feedback and no movement toward "ready for committer"

This doesn't mean you're wrong — it may mean the community has higher priorities right now.

## Attachments

### Patches
- Attach as `.patch` or `.diff` files, or inline in the message body
- For multi-patch series, use git format-patch with cover letter
- Compress large patches (gzip)

### Other Attachments
- Test cases, sample data, benchmark results: attach as text files
- Explain attachments in the body text
- Don't attach binaries unless absolutely necessary

## List-Specific Norms

### pgsql-hackers
- Highest-bandwidth list. Be concise.
- Patches expected to be high quality (build clean, pass tests)
- Design discussion welcome before code
- Committers actively read this list

### pgsql-bugs
- Users report bugs here
- Be patient with reporters who don't know internals
- Help them create reproducible test cases
- Move development discussion to pgsql-hackers

### pgsql-general
- User questions about usage
- No development discussion
- Point people to pgsql-hackers for development topics
- Patience with beginners expected
