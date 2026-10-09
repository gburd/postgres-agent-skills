# AI life skills

Agent-agnostic, domain-agnostic skills: the small habits that make an AI
coding session work regardless of what you are building. These are **not**
PostgreSQL-specific; they are offered as a standalone set.

| Skill | Use for |
|-------|---------|
| [`persistent-memory/`](persistent-memory/SKILL.md) | choose and use a cross-session memory store (memelord, an MCP memory server, or a notes file) so lessons survive between sessions |
| [`btw/`](btw/SKILL.md) | handle a quick aside without losing the thread of the current task |
| [`checkpoint/`](checkpoint/SKILL.md) | summarise progress — done, remaining, blockers — between tasks or when context grows long |
| [`dream/`](dream/SKILL.md) | brainstorm an idea or approach freely, without writing code |
| [`maintain-docs/`](maintain-docs/SKILL.md) | audit and update AGENTS.md / CLAUDE.md against the project's actual state |
| [`think-hard/`](think-hard/SKILL.md) | deliberate step-by-step reasoning for a hard bug or design decision before acting |
| [`watchdog/`](watchdog/SKILL.md) | periodic project health check — build, tests, lint, format, architecture drift |

`persistent-memory` is the keystone: start a task by recalling, finish by
recording, and never make the user tell you the same thing twice.

CC0-1.0 (public domain). See the repo root `LICENSE`.
