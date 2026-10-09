# Coding standards

How to write code in this project. Correctness and clarity first; these are
rules, not taste (taste lives in `opinions.md`).

## Philosophy

- No speculative features. Do not add a flag, option, or configuration until it
  is actively needed.
- No premature abstraction. Do not extract a utility until you have written the
  same code three times.
- Clarity over cleverness. Prefer explicit, readable code to dense one-liners;
  the next reader predicts the line.
- Justify new dependencies. Each one is attack surface and maintenance burden.
- No phantom features. Do not document or validate what is not implemented.
- Replace, do not deprecate. When a new implementation supersedes an old one,
  remove the old one.
- Verify at every level. Linters, type checkers, and tests are the first thing
  you set up, not the last.
- Bias toward action on reversible choices; ask before committing to
  interfaces, data models, and architecture.
- Finish the job. Handle the edge cases you can see, clean up what you touched,
  and flag adjacent breakage without inventing new scope.
- Do not over-weight development cost. An agent builds far faster than human
  effort-estimates assume, so discount build cost and favour the
  higher-quality, more maintainable design.

## Never commit PII or private data

This overrides convenience. Personally identifiable information and private
data must never enter a commit, patch, branch, or tracked file:

- names, emails, phone/postal addresses, locations tied to real people;
- account identifiers, customer/order/invoice data;
- credentials: passwords, API keys, tokens, cookies, private keys, certs;
- raw logs, database dumps, captures, or support bundles that embed any of the
  above;
- the contents of any file shared privately for debugging.

Rules that follow from it: files shared for debugging are read-only scratch,
never repurposed as fixtures; fixtures and examples use obviously fake data
(`jane.doe@example.com`, `192.0.2.1`); audit every file before staging and read
the staged diff; secrets live in a secrets manager, never in the tree; when in
doubt, leave it out and ask. Assume anything committed is public forever.

## Hard limits

- Functions stay small (roughly <=100 lines, low cyclomatic complexity).
- Few positional parameters (roughly <=5); past that, take a struct/object.
- A consistent line length (100 is a reasonable default).
- Absolute imports; no deep relative paths.
- Document non-trivial public APIs.

## Zero-warnings policy

Fix every warning from every tool: linters, type checkers, compilers, tests.
If one genuinely cannot be fixed, suppress it inline with a one-line
justification.

## Comments

Code is self-documenting by default; delete commented-out code. If a comment is
needed to explain *what* the code does, refactor instead. The bar differs:

- Patching existing code: no comment is the default. A comment earns its place
  only by stating something non-obvious (the why, a constraint, a case the code
  cannot show), pitched a level above the code.
- Writing new code: comment generously. A header on each new function (summary,
  then the caller contract), a short full-sentence comment above each phase of
  a non-trivial function, and multi-sentence blocks for the why and the
  constraints.

Many ecosystems have their own house comment style; where a project or a domain
steering file (for example PostgreSQL) specifies one, it wins.
