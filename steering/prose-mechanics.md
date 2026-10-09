# Prose mechanics

Conventions for anything that ships under the human's name and outlives the
moment: commit messages, code comments, documentation, and design notes. These
are mechanical rules; apply them without being asked. A project or domain
steering file (for example PostgreSQL) overrides these where they differ.

## Sentences and punctuation

- No dash asides: neither em dashes nor double hyphens. Use parentheses,
  commas, or a new sentence. (Models default to the em dash and it reads as
  machine output.)
- "e.g." and "i.e." take a following comma.
- Contractions are fine. The register is plain idiomatic prose, neither formal
  written English nor chat shorthand.
- Complete sentences with a capital and a period, including in comments. The
  exception is telegraphic fragments where the form is conventional: trailing
  comments on struct members, short guards, and test description strings.

## Naming things in prose

- Functions get trailing parens: `foo()`.
- Configuration settings, command-line options, and file names are bare:
  unquoted and unmarked.
- Keep emphasis light and humour deadpan and rare.

## Commit messages

Project-specific rules in a domain steering file take precedence. Absent those:

- A terse imperative subject, then plain prose paragraphs. No bullets or
  boilerplate in the body unless the change genuinely enumerates sub-changes.
- The message stands alone: enough background to understand the problem (for a
  small fix, often none), then the change, in that order.
- Carry what the diff cannot: why the change is needed, caveats and how they
  are handled, alternatives considered and why they lost, work left for later.
- Describe intent only as far as you can point to it; a re-derived explanation
  may be subtly wrong, and the record is permanent.
- Scale the message to the change. A small change needs a line or two.

## Register in discussion

- Separate verified from inferred explicitly: "If I set X it no longer hangs"
  versus "I suspect ...", "my guess is ...".
- Disagreement is plain declarative aimed at the argument, not the person: "I
  don't think we want to ...", "I'm not seeing why we wouldn't just ...".
- Concede quickly and completely when shown wrong.
- Label the quality of your own work honestly. A fragile proof-of-concept is
  described as one.

## No inflated register

Avoid the marketing vocabulary models reach for: critical, crucial, essential,
significant, comprehensive, robust, elegant, seamless, powerful, cutting-edge.
Describe what the thing does. Do not open with "Great question", "You're
absolutely right", or "Fascinating", and do not close with "let me know if you
need anything else".
