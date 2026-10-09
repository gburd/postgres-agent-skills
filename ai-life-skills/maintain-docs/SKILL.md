---
name: maintain-docs
description: Audit and update CLAUDE.md/AGENTS.md files. Compares documented state against actual project state and suggests updates.
---

## Workflow

1. Read CLAUDE.md and AGENTS.md for this project
2. Check actual state: Cargo.toml, `ls src/`, `cargo test | tail -5`, `git log --oneline -5`
3. Compare documented vs actual
4. Report stale entries, missing entries, incorrect architecture
5. Suggest specific updates

## What to Check

- Build/test commands still work
- Directory structure matches description
- Architecture reflects current code
- Feature flags are up to date
- Known issues still relevant
