---
name: stop-slop
description: >
  Remove the predictable tells of AI-written prose. Use when drafting, editing,
  or reviewing any text that ships under a human's name: commit messages, PR
  descriptions, docs, issue comments, emails, design notes. Produces prose that
  reads as written by a person who knows the subject, not generated.
license: CC0-1.0
metadata:
  author: ddx
  version: "0.1.0"
---

# Stop slop

Strip the patterns that mark text as machine-generated. The goal is prose a
competent human would actually write: direct, specific, varied, and free of the
reflexes a language model falls into.

## The tells, and what to do instead

- **Throat-clearing openers.** Cut "Here's what", "It's worth noting that",
  "In order to", "Let's dive in". Start with the point.
- **The not-X-but-Y contrast.** "This isn't just a cache, it's a..." State Y
  directly and drop the setup.
- **Rule-of-three everywhere.** Not every list wants three items; two is often
  the honest count. Vary it.
- **Inflated register.** Avoid critical, crucial, essential, significant,
  comprehensive, robust, elegant, seamless, powerful, cutting-edge, delve,
  leverage (as a verb), unlock. Say what the thing does.
- **Adverb padding.** "significantly faster", "simply run", "carefully
  consider". Delete the adverb or give a number.
- **Passive voice hiding the actor.** "mistakes were made" -> name who did
  what. Prefer a human subject doing something.
- **Inanimate things performing human verbs.** "the design decides", "the error
  wants" -> name the person or the mechanism.
- **Vague declaratives.** "the implications are significant" -> name the
  specific implication. "the reasons are structural" -> state the reason.
- **Metronomic rhythm.** If three sentences in a row are the same length, break
  one. Mix short and long.
- **Pull-quote sentences.** If a line sounds engineered to be quoted, rewrite
  it plainer.
- **Em dashes.** Replace with a comma, parentheses, a colon, or a new sentence.
- **Filler validation.** "Great question", "You're absolutely right",
  "Fascinating" -> delete.
- **Closing boilerplate.** "Let me know if you need anything else", "I hope
  this helps" -> delete.

## Quick pass before delivering

Read the draft once looking only for: an opener that delays the point; a
"not X, it's Y"; any adverb; a passive sentence whose actor is hidden; an
inanimate subject doing a human verb; a vague "the Xs are Y"; three equal-length
sentences in a row; an em dash. Fix each.

## Scoring (optional)

Rate the draft 1-5 on each; anything below 3 gets another pass:

| Dimension | Ask |
|-----------|-----|
| Directness | does it state, or announce and then state? |
| Specificity | are claims named, or vague? |
| Rhythm | varied sentence length, or metronomic? |
| Trust | does it respect the reader, or over-explain? |
| Density | is anything cuttable without loss? |

Domain prose rules (commit-message shape, docs style) still apply on top; see
`steering/prose-mechanics.md`. The idea of de-slopping prose is widely
discussed; this skill is an original CC0 formulation, not a copy of any
particular checklist.
