---
name: subagent-teams
description: >
  Run coordinated teams of sub-agents to parallelize work and raise quality
  through independent review. Use when a task is big enough to split across
  sub-agents, when independent review of a change would catch what the
  implementer cannot see, or when fanning out genuinely independent work.
  Covers the worker/reviewer/re-reviewer pattern, when to parallelize vs. stay
  serial, how to brief a sub-agent, and the harness constraints that make a
  sub-agent die instantly.
license: CC0-1.0
metadata:
  author: ddx
  version: "0.1.0"
---

# Sub-agent teams

A single agent is a bottleneck and its own blind spot. Teams of sub-agents
parallelize independent work and add the independent eyes that catch an
implementer's mistakes. Use them deliberately, not reflexively; the ceremony
of dispatch and hand-off is a cost that only pays off above a certain task
size.

## The review pattern (worker -> reviewer -> re-reviewer)

For a change that matters:

1. **Worker** implements the change and reports what it did plus the evidence
   (tests run, output).
2. **Reviewer** (a separate sub-agent, fresh context) reads the diff and the
   worker's evidence, and finds issues: correctness, architecture, missed edge
   cases, convention violations. It works from the diff and the reported
   evidence; it does not re-run the whole suite.
3. **Re-reviewer** verifies the fix for any issue the reviewer raised, catching
   the lead-level error where a "fix" introduces a new problem.

Independent context is the point: a reviewer sharing the worker's context
shares its blind spots.

## When to parallelize vs. stay serial

- **Parallelize** genuinely independent work: tasks that touch disjoint files
  with no shared state and no ordering dependency. Fan them out, each in its
  own workspace/branch, and integrate as they finish.
- **Stay serial** when tasks share state, must happen in order, or are small
  enough that dispatch overhead exceeds the work. Prefer fewer, larger,
  independently-reviewable tasks over many micro-tasks that spend their
  wallclock on hand-off.
- **Never block on a background run.** A sub-agent must not hand control back
  while stalled on a long build/test it launched in the background; run the
  targeted check in the foreground, or leave the slow whole-suite run for a
  single final verification.

## Briefing a sub-agent well

A sub-agent starts cold. Give it: the goal in one or two sentences, the exact
files or area, the constraints (conventions, what not to touch), what "done"
looks like, and whether it may write or is read-only. A vague brief produces a
vague result. For a reviewer, hand it the diff and the acceptance criteria, not
"take a look".

## Harness dispatch constraints (why a sub-agent dies in <2s)

A sub-agent that finishes in a second or two with zero tool uses almost always
failed to dispatch, not finished the work. The usual causes, across harnesses:

- **A model the sub-agent cannot actually call.** Some model IDs require
  provisioned capacity or a specific regional/inference-profile form; a bare or
  wrong-form ID fails immediately. The safe default is to **omit the model
  override** and inherit the parent's model: the parent already proved it is
  dispatchable.
- **Missing capability or tool grant** the sub-agent needs but was not given.
- **A prompt that points at a path or resource that does not exist.**

When a sub-agent dies instantly: drop any model override so it inherits the
parent's, confirm the brief references real paths, and re-dispatch. Learn your
specific harness's dispatch rules once and record them in persistent memory so
the next session does not rediscover them.
