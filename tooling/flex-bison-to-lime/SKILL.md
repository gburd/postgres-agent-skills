---
name: flex-bison-to-lime
description: Port flex+bison parser/scanner pairs to the Lime parser generator. Covers mechanical bison-to-Lime conversion, hand-rolled scanners replacing flex, push-parser drivers, and reverse converters for tools that still consume bison output. Distilled from porting 12 PostgreSQL grammar/scanner pairs (~36k lines).
---

## What Lime Is and Why It's Different

Lime is a push-parser generator (descendant of Lemon/SQLite) with explicit modification semantics for runtime grammar extension. The mental model differences from yacc/bison matter:

- **Push, not pull.** The parser does not call your scanner. *You* call the parser, feeding it one token at a time. The driver loop is yours to write.
- **Symbolic tokens only.** No raw character literals like `'+'` in rules — every token has a name. ASCII-bearing tokens get aliased (`PLUS`, `LBRACE`, `COMMA`).
- **First-character symbol class.** `Foo` is a terminal; `foo` is a non-terminal. Bison's PascalCase non-terminals (`SelectStmt`, `OptRoleList`) must be lowercased.
- **Letter labels, not numbers.** `lhs(A) ::= a(B) b(C). { A = expr_using(B, C); }`. No `$$`, `$1`, `$2`.
- **Per-symbol types, not union members.** Bison's `%type <ival> foo bar` becomes `%type foo {int}` and `%type bar {int}`. The C type is the type, not a member name.
- **One alternative per rule.** No `lhs : alt1 | alt2 | alt3 ;` grouping. Each alternative is its own `lhs ::= ... .` declaration.
- **Period-terminated declarations.** `%token NAME.` not `%token NAME`. Rule heads end in `.`. Rule alternatives end in `.` (or `. { action }`).
- **No lookahead in actions** (as of upstream `1d2ac61`). Bison's `yychar`/`yyclearin` have no direct equivalent inside actions; needs driver-side workaround.
- **`%first_token N`** sets the starting numeric ID for tokens (default 1). Set to 257 for Bison parity if your scanner emits raw ASCII for self-chars.
- **Static and dynamic grammar mods.** Lime's `lime_modifications_to_grammar_text()` lets extensions splice rules at runtime — a feature bison cannot match.

Read `/home/gburd/ws/lime/docs/MIGRATION_FROM_BISON.md` for the upstream directive map. Read `/home/gburd/ws/lime/docs/CONCEPTS.md` for the parser's runtime model.

## Per-Component Recipe (proven across 12 PG ports)

For every flex+bison pair, follow this order:

1. **Scanner first** — convert the `.l` to hand-rolled C. Do not try to keep flex.
2. **Driver shape** — sketch the push loop and ASCII-to-token translator before touching the grammar.
3. **Mechanical grammar conversion** — write/adapt a converter (`lime_convert_gram.py`-style); do not hand-translate 20k-line grammars.
4. **Build flip wiring** — meson `custom_target` + Makefile rule, with `lime_kw` and relaxed `c_args` for the generated file.
5. **Test gate** — `meson test --suite setup` MUST pass before any other test. After every backend rebuild, re-run setup.
6. **Differential test** — feed malformed inputs through old and new parsers; diff stderr byte-for-byte.

If you skip step 5 you will burn hours debugging "regression failures" that are stale tmp_install artefacts.

## Hand-Rolling a Scanner (replacing flex)

Flex scanners aren't generally portable to Lime — flex's regex engine, exclusive-state machinery, and yytext management have no Lime counterpart. The path that works:

1. **List exclusive states.** Each `<STATE>` block in the .l becomes a state ID in an enum.
2. **Identify token-emitting rules.** Each terminal action (`return TOKEN;`) becomes a case in the new scanner.
3. **Write a `next_token(state)` function.** Single switch on state, single switch on current char. No regex; explicit char-by-char advance.
4. **Preserve the public API.** If consumers of the scanner include `scanner.h`, keep the same symbol names (`yylex`, `yyalloc`, `yyfree`, `yylval`, `yylloc`).
5. **Buffer management.** Track `scanbuf`, `scanbufpos`, `scanbuflen` explicitly. Use `memchr` to find newlines for location tracking — never walk the whole buffer.

Common scanner bugs:

- **Infinite recursion in `yyerror_more`.** Advance the cursor *before* calling yyerror, not after. Otherwise yyerror calls back into the scanner which re-reports the same error.
- **`<state><<EOF>>` rules.** Reset `yytext` to a sentinel before calling yyerror; otherwise stale yytext bleeds into error messages.
- **Self-char tokens.** Decide once whether the scanner returns raw ASCII (`'+'` returns 43) or symbolic tokens (`PLUS`). Raw ASCII is simpler if the driver translates; symbolic requires CHAR_TOKEN_MAP everywhere.

## The Push-Parser Driver

Every Lime parser needs a driver that owns the lex loop:

```c
int prefix_yyparse(...) {
    void *parser = prefix_yyAlloc(palloc);
    YYSTYPE lval;
    YYLTYPE lloc;
    int tok;
    while ((tok = prefix_yylex(&lval, &lloc, yyscanner)) > 0) {
        prefix_yyLoc(parser, ascii_to_lime_token(tok), lval, lloc, &extra);
    }
    prefix_yyLoc(parser, 0, lval, lloc, &extra);  /* EOF */
    prefix_yyFree(parser, pfree);
    return extra.error_count > 0 ? 1 : 0;
}
```

`ascii_to_lime_token` translates raw ASCII codes (43 for `+`, 40 for `(`, etc.) to the symbolic token IDs Lime assigns. Generate this function from the grammar's char-token table.

Lookahead-in-actions workaround (until upstream P0-NEW-5 lands):

```c
struct LookaheadBuf { int has; int tok; YYSTYPE lval; YYLTYPE lloc; };
/* In driver loop: maintain 1-token buffer in extra->lookahead.
   Push the BUFFERED token; lex new one to refill. Actions can
   read extra->lookahead.tok and call extra->driver_consume_lookahead()
   to drop it. */
```

## Mechanical Conversion (bison → lime)

For grammars over 1k lines, write a converter. The PG converter (`src/tools/lime_convert_gram.py`, ~1650 lines) handles:

- **Directive translation.** `%token`/`%left`/`%right`/`%nonassoc`/`%type`/`%start`/`%expect` map directly. `%union` becomes `%token_type`. `%parse-param` folds into a `struct GramParseExtra`.
- **First-character flip.** PascalCase non-terminals (`SelectStmt`) become `selectStmt`. Record the rename in a sidecar map for the reverse direction.
- **Char-literal → symbolic.** `'+'` → `PLUS`; emit a `%token PLUS.` and an `ascii_to_lime_token` table.
- **Action rewriting.** `$$` → `A` (LHS letter); `$1`, `$2`, `$N` → letters by position; `$<member>$` → `A.member`; explicit `$<member>N` → labeled letters with member access.
- **Mid-rule action lifting.** Bison's inline `{ ... }` actions in the middle of a rule become standalone non-terminals (`midactN`) with explicit type and action. Detect via `$<member>$ = expr` pattern; type the helper from the union member's C type.
- **Per-rule precedence.** Bison's `%prec TOKEN` becomes Lime's `[TOKEN]` after the rule body's period.
- **Empty alternatives.** Bison's `lhs : | alt ;` (leading bar = empty alt first) requires careful state tracking; track `just_consumed_pipe` to detect trailing-empty.
- **Multi-alternative emission.** `lhs : alt1 | alt2 | alt3 ;` becomes three separate `lhs ::= ... .` declarations.
- **Action-body bison-isms.** Rewrite `yyerror`, `yylex`, `yychar`, `yyclearin` to grammar-prefixed equivalents. Inject `yyscan_t yyscanner = extra->yyscanner;` locals at action-block scope so prologue macros expand.
- **Multiple `%parse-param` fold.** Bison allows `%parse-param {Foo *foo}{Bar *bar}`; Lime takes one `%extra_argument`. Fold into a struct and rewrite action references from `foo` to `extra->foo`.

Don't try to do this by hand for any grammar over a few hundred lines.

## Reverse Converter (lime → bison-format)

When other tools consume bison-format grammar output (PG's ecpg `parse.pl`, for example), generate a Bison scaffold from the Lime source at build time. The scaffold doesn't need to compile via bison — it just needs to be parseable by the consuming tool.

Strategy:

1. Parse Lime tokens, precedence directives, and rules.
2. Emit `%token NAME` per token (drop period; convert char-token aliases back to `'X'`).
3. Emit precedence directives (`%left`, `%right`, `%nonassoc`).
4. Emit rules as `lhs : alt1 | alt2 ;` blocks (group by LHS).
5. **Recover non-terminal case.** The first-character flip is lossy at the symbol level. Have the *forward* converter emit the rename map as a magic comment block at the top of the .lime file:
   ```
   /* lime_to_bison_gram nt_rename map -- DO NOT EDIT BY HAND.
    * Each line: <bison-name> -> <lime-name>.
    * SelectStmt -> selectStmt
    * OptRoleList -> optRoleList
    */
   ```
   The reverse converter parses this block and uses it to recover original names.
6. **Reverse char-token aliases.** `LPAREN` → `'('`, `COMMA` → `','`, etc. Maintain the same map both directions.
7. **Per-rule precedence.** Lime's `[TOKEN]` becomes `%prec TOKEN` in the bison body.
8. **Strip mid-rule helpers.** `midactN` non-terminals are an artefact of conversion; consumers expect inline mid-rule actions or no mid-rule action at all. Skip them.
9. **Skip Lime-specific directives.** `%first_token`, `%locations`, `%location_type`, `%name`, `%token_type`, `%extra_argument`, `%syntax_error`, `%parse_failure` have no bison meaning.

The PG implementation: `src/tools/lime_to_bison_gram.py` (~330 lines).

## Build Wiring

### meson

```meson
gram = custom_target('gram.c',
  input: 'gram.lime',
  output: ['gram.c', 'gram.h'],
  kwargs: lime_kw,
)
parser_lib = static_library('parser',
  gram, scan,
  c_args: ['-Wno-missing-prototypes', '-Wno-unused-variable']
        + cflags_no_decl_after_statement,
  ...
)
```

### Makefile

```make
gram.c gram.h: gram.lime
	$(LIME) -d. $<
```

### Distros

Distros without the Lime binary (Debian, RPM, Homebrew, source tarballs) need both:

1. `find_program('lime', required: false)` — pre-generated `.c`/`.h` shipped in the source tarball, regenerated only if `lime` is found.
2. Static `liblime_parser.a` link if your output uses runtime APIs.

## Testing Methodology

### The mandatory setup gate

Every PG test run MUST start with:

```bash
meson test -C build --suite setup
```

This rebuilds tmp_install. Skip it once and you'll spend an afternoon "debugging" stale-binary regressions.

### Differential testing

Feed identical malformed inputs to old and new parsers; diff stderr:

```bash
diff <(echo 'malformed input' | psql -f - 2>&1) \
     <(echo 'malformed input' | new_psql -f - 2>&1)
```

Acceptable deltas: error-message wording (Lime's LALR errors are stricter and earlier than Bison's). Document each delta in the commit message; update `expected/*.out` files as needed.

### Conflict accounting

Lime's `%expect 0` is unforgiving. Real conflicts must be resolved (precedence directives, rule restructuring); spurious conflicts from converter bugs (empty-alt drops, missing precedence) need converter fixes.

## Gotchas (PG-tested)

- **Token numbering vs ASCII.** Lime numbers tokens from 1 by default. Scanners that emit raw ASCII (43 for `+`) collide with Lime's first ~127 token IDs. Use `%first_token 257` (Bison parity) so ASCII 0-127 stays reserved.
- **Location tracking.** Set `%locations` and `%location_type {YYLTYPE}`. Use `@N` in actions for the Nth RHS symbol's location. `&yyloc` accesses the current rule's location in `%syntax_error`.
- **YYSTYPE union placement.** Lime emits the union body in the .c file, not the .h. Consumers (other .c files including the parser's .h) won't see the typedef. Solution: declare the YYSTYPE union typedef in a separate header (e.g., `gramparse.h`) and `#include` that wherever YYSTYPE is needed. Use `#define YYSTYPE_IS_DECLARED 1` to guard against re-declaration if a bison-emitted header coexists during transition.
- **Multiple `%parse-param`** must fold into a single `struct GramParseExtra` referenced via `extra->`. Bison-style parameter shadows in macros collide with function-declaration parameter names.
- **Empty alternatives drop on bare-pipe.** Bison's `lhs : | alt ;` (leading pipe = empty alt first) is easy to mis-track. The converter must detect "just consumed pipe" and emit an explicit empty alternative if a `;` follows immediately.
- **Action mutation of `$$`.** Bison's `$$ = ...` reassigns the LHS value. Lime's `A = ...` does the same — but the default action `A = B;` (copy first RHS to LHS) is suppressed for pointer types when a typed mid-rule helper is detected. Don't fight this; it's correct.
- **`%syntax_error` recipe.** Lime's `%syntax_error` block runs on syntax errors. The canonical PG shape:
  ```lime
  %syntax_error {
      prefix_yyerror(extra->result, extra->escontext, extra->scanner,
                     yymajor, &yyloc, "syntax error");
  }
  %parse_failure {
      prefix_yyerror_token(extra, 0, "syntax error");  /* yymajor not exposed here */
  }
  ```
- **`%parse_failure` does NOT expose `yymajor`.** Only `%syntax_error` does. If you need the failing token in `%parse_failure`, save it from `%syntax_error` into your extra struct.

## When NOT to Port

- **Tiny grammars (<100 lines).** Hand-rewrite directly in Lime; the converter is overkill.
- **Hand-tuned scanners with no flex regex.** Already C; no work to do beyond renaming `yylex` callers.
- **Tools you can't modify.** If a downstream consumer needs bison output and you can't change it, write a reverse converter and keep gram.lime authoritative.

## Verification Checklist

Before declaring a port done:

- [ ] `meson test --suite setup` passes
- [ ] Full test suite ok-count matches pre-port count
- [ ] Differential test on at least 100 representative inputs (sample from regress test corpus)
- [ ] Error-message deltas documented in commit message
- [ ] No new warnings (`-Wall -Wextra -Wno-unused-variable` for generated code)
- [ ] `expected/*.out` updates explained, not blanket-accepted
- [ ] Build works without Lime binary present (pre-generated artefacts in tarball)

## Reference Implementation

`/home/gburd/ws/postgres/lime` — 12 components ported, including the 20k-line backend SQL parser. See `AGENTS.md` for the operator manual; `Lime-Requests.txt` for upstream dialog; `src/tools/lime_convert_gram.py` for the converter; `src/tools/lime_to_bison_gram.py` for the reverse converter.
