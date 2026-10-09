# PostgreSQL Patch Submission

How to submit patches to PostgreSQL: the commitfest process, formatting expectations, versioning, and rebasing.

## Before Submitting

### Research First
- Search the mailing list archives for prior discussion of your topic
- Check if someone else is already working on it
- Read the commitfest for similar entries
- If the feature is non-trivial, post an RFC first and wait for feedback

### RFC Process (for New Features)
1. Send email to pgsql-hackers with subject starting "RFC:" or "proposal:"
2. Describe the problem you're solving (not just the solution)
3. Explain your proposed approach
4. Ask for feedback on direction before writing code
5. Wait for responses — give it at least a week

## Patch Format

### Creating Patches
```bash
# Generate patches from commits
git format-patch origin/main..HEAD

# Single commit
git format-patch -1 HEAD

# With a cover letter (for multi-patch series)
git format-patch --cover-letter origin/main..HEAD
```

### Subject Line Format
```
[PATCH v1 0/3] Short description of patch series (cover letter)
[PATCH v1 1/3] First logical change
[PATCH v1 2/3] Second logical change
[PATCH v1 3/3] Third logical change
```

Components:
- `[PATCH]` — indicates this is a patch submission
- `v1`, `v2`, etc. — version number (increment with each resubmission)
- `1/3` — patch number / total patches in series
- `0/N` — cover letter (describes the series as a whole)

### Cover Letter Contents
- Problem statement: what's wrong or missing
- Solution overview: your approach
- Changes since last version (for v2+)
- Open questions (if any)
- Testing done

### Patch Content Requirements
- Must apply cleanly on current HEAD of master
- Must pass `make check` (all regression tests)
- Must be pgindent-clean (`src/tools/pgindent/pgindent`)
- Should include regression tests
- Should include documentation updates for user-visible changes
- Must compile without warnings on all supported platforms (test via buildfarm)

## Submitting to the Commitfest

### Registration
1. Ensure your patch is posted to pgsql-hackers
2. Register at https://commitfest.postgresql.org/
3. Fill in: title, author(s), mailing list link, wiki link (if applicable)
4. Select the appropriate commitfest (current or next)

### Timing
- Don't submit during the last few days of a commitfest
- The last commitfest before feature freeze is the deadline for new features
- Bug fixes can be submitted at any time

## Responding to Review

### When You Get Feedback

1. **Acknowledge promptly** — even if just "thanks, I'll look at this"
2. **Address every point** — reviewers track whether their concerns were handled
3. **Explain disagreements** — if you disagree with feedback, explain why (with technical reasoning)
4. **Submit a new version** — don't just discuss, produce updated code

### Submitting Updated Versions

```bash
# Rebase on current master
git fetch origin
git rebase origin/main

# Generate new version
git format-patch --cover-letter -v2 origin/main..HEAD
```

In the v2 cover letter:
- List all changes from v1
- Reference the reviewer's points
- Note any unresolved questions

### Version Discipline
- v1: Initial submission
- v2: After first round of review feedback
- v3: After second round
- Continue incrementing until committed or withdrawn

## Common Mistakes in Patch Submission

### Process Mistakes
1. **Not searching for prior art** — your idea was discussed in 2007 and rejected for good reasons
2. **Submitting before RFC** — for anything non-trivial, get buy-in first
3. **Ignoring review feedback** — posting unchanged v2 will annoy reviewers
4. **Not updating commitfest entry** — keep the status current
5. **Submitting to wrong list** — development patches go to pgsql-hackers
6. **Top-posting in responses** — use inline reply style

### Technical Mistakes
1. **Not rebasing** — patches must apply to current master
2. **Mixing concerns** — one logical change per commit
3. **Missing tests** — patches without tests won't be committed
4. **Missing docs** — user-visible changes need documentation
5. **Not running pgindent** — formatting must be clean
6. **Breaking other tests** — run the full test suite, not just your new tests
7. **Platform-specific code** — must work on Windows, macOS, Linux, *BSD, AIX...

### Social Mistakes
1. **Being impatient** — reviews take time; don't ping after 2 days
2. **Taking criticism personally** — it's about the code, not about you
3. **Arguing without evidence** — back up disagreements with data or references
4. **Not helping others** — review other patches to build goodwill
5. **Submitting huge patches** — break large features into reviewable chunks

## Rebasing Expectations

- **You are expected to keep your patch rebased on current master**
- If your patch no longer applies, reviewers will move on to other patches
- Rebase when master conflicts with your changes (don't merge)
- After rebasing, re-run all tests to ensure nothing broke
- If rebasing requires design changes, post a new version with explanation

## Attribution

The commit message will credit:
- **Author**: The person who wrote the patch
- **Reviewed-by**: People who reviewed it substantially
- **Discussion**: Link to the mailing list thread

If multiple people contributed code, additional authors can be listed. This attribution is permanent — it's how the community recognizes contributions.
