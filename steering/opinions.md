# Opinions

Subjective preferences: how generated output (prose, commits, PRs, docs,
naming) should read. These are taste, not correctness. When a preference here
conflicts with clarity or correctness, clarity wins; absent a reason, follow
these. (This is the file to fork for your own taste.)

## Punctuation and prose

- No em dashes in generated prose. Use a spaced hyphen, a comma, parentheses,
  or a rewrite. Models default to em dashes and it reads as machine output.
  Applies to PR descriptions, commit bodies, docs, comments, and chat alike.
- Plain, factual language. Describe what the code does now, not discarded
  approaches. Avoid the inflated register (critical, crucial, essential,
  significant, comprehensive, robust, elegant, seamless, powerful,
  cutting-edge).
- No filler validation. Do not open with "Great question", "You're absolutely
  right", or "Fascinating". Get to the answer.

## Formatting

- Prefer terse bullets over walls of prose for status and plans; prefer prose
  when the logic between points matters (see `voice.md`).
- Fenced code blocks with a language tag for any code or command.
- No trailing "let me know if you need anything else" boilerplate.
