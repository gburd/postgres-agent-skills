---
name: review-diff
description: Review a git diff for regressions, style violations, complexity, and security issues. Use for cross-tool monitoring — one agent reviews another's changes.
---

## Workflow

1. Show what changed: `git -P log --oneline main..HEAD` and `git -P diff --stat main..HEAD`
2. Review each file: `git -P diff main..HEAD -- <file>`
3. Check: correctness, regressions, style, complexity, security, tests
4. Run tests: `cargo test && cargo clippy --all-targets --all-features -- -D warnings`
5. Report findings with file:line references and severity (blocker/warning/nit)

## Cross-Tool Usage

Claude makes changes → commit → Kiro runs `/review-diff`
Kiro makes changes → commit → Claude reviews the branch
