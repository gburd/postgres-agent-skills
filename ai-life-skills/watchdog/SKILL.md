---
name: watchdog
description: Comprehensive project health check. Run periodically to catch drift, regressions, and quality issues. Checks build, tests, lint, format, and architecture constraints.
---

## Checks

1. **Build:** `cargo build 2>&1 | tail -5`
2. **Tests:** `cargo test 2>&1 | tail -20`
3. **Lint:** `cargo clippy --all-targets --all-features -- -D warnings 2>&1 | tail -10`
4. **Format:** `cargo fmt -- --check`
5. **Uncommitted changes:** `git status --short`
6. **Architecture:** Read AGENTS.md, verify constraints still hold

## Report

```
## Watchdog — <project> — <date>
- Build: ✅/❌
- Tests: ✅/❌ (N passed, M failed)
- Lint: ✅/❌
- Format: ✅/❌
- Uncommitted: <list>
- Architecture: <any drift>
```
