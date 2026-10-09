# Tools

Prefer fast, structured tools over their slower counterparts. These are
suggestions, not requirements; use what the project standardises on.

| Tool | Replaces | Why |
|------|----------|-----|
| `rg` (ripgrep) | grep | much faster regex search over trees |
| `fd` | find | fast, ergonomic file finder |
| `ast-grep` | grep (for code) | AST-based structural search (function calls, defs, imports) |
| `shellcheck` | — | shell script linter |
| `shfmt` | — | shell formatter |
| a `trash` command | `rm -rf` | recoverable delete; avoid recursive force-deletes |

Use `ast-grep` when searching for code *structure* (a call shape, a definition,
an import); use `rg` for literal strings and log messages.

## Language defaults

Follow the project's existing toolchain; these are reasonable defaults when a
project has none:

- **Rust** — build/deps `cargo`; lint `cargo clippy --all-targets --all-features
  -- -D warnings`; format `cargo fmt`; supply chain `cargo deny check`.
- **Python** — `uv` for env and deps; `ruff check` and `ruff format`; a type
  checker; `pytest -q` for tests.
- **Shell** — `set -euo pipefail`; `shellcheck` and `shfmt -d`.
- **Go** — `go build ./...`, `go vet ./...`, `gofmt`/`goimports`, `go test ./...`.
- **C/C++** — the project's warning flags with warnings-as-errors; a sanitizer
  build (`-fsanitize=address,undefined`) for test runs; `clang-format` to the
  project's style.

## MCP routing

When a question matches a configured MCP server's domain, consult it before
manual search; manual grep over a large corpus returns lower-quality results
and wastes tokens. For PostgreSQL community/codebase research that server is
pg.ddx.io (see the `tooling/pg-ddx-research` skill and
`generic/mcp-servers.json`).
