# Pascal-S — Trabalho Prático 1

Source of truth: [`../Trabalho_Prático_1.pdf`](../Trabalho_Prático_1.pdf), all seven pages. FURG/C3, Compiladores, Prof. Dr. Gerson Alberto Leiria Nunes, semester 2026/2. This assignment is worth **30% of the bimonthly grade**, with **at most two students per group**.

The three compiler modules are implemented; `tests/` contains the required sample inputs. This document records the specification, chosen interpretations, and remaining submission work. It is not a replacement for the required technical PDF report.

## Mandatory implementation rule

**ALL CODE MUST BE CONCISE AND DIRECT. THE AMOUNT OF CODE WRITTEN MUST BE THE MINIMUM POSSIBLE. DO NOT OVERENGINEER.**

- Implement only what the assignment requires, using Python, PLY, and the standard library.
- Keep the three modules below; use `yacc.py` as the entry point rather than adding a separate application layer.
- Prefer straightforward functions and dictionaries; add classes only when they simplify symbol records, scope management, or lexer state.
- No frameworks, plugin systems, generic compiler infrastructure, redundant wrappers, speculative features, or unnecessary dependencies.
- Perform semantic checks in parser actions; do not build an AST, interpreter, or backend unless a demonstrated requirement makes one necessary.
- Avoid duplicated logic, boilerplate, and comments that merely restate code. Keep necessary explanations short.
- Minimal code does **not** mean obfuscated code or skipping required validation, diagnostics, recovery, documentation, or tests.

## Files and responsibilities

| File | Responsibility |
| --- | --- |
| `lex.py` | Token definitions, reserved-word lookup, line-buffered lazy `token()` production, comments, positions, and lexical diagnostics. |
| `symbol_table.py` | Symbol records, nested environments, declaration/lookup, direct references, duplicate/undeclared detection. This module's filename is our choice; the PDF does not name it. |
| `yacc.py` | PLY LALR(1) grammar, precedence, semantic checks, semicolon recovery, and the `python3 yacc.py input.pas` entry point. |

PLY is the only required third-party dependency (`requirements.txt`). Set up and run the project with `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`, and `.venv/bin/python yacc.py path/to/input.pas`. The import aliases `ply_lex` and `ply_yacc` avoid confusion with the local module filenames.

The PDF does not prescribe a CLI. Report whether front-end validation succeeded; do **not** execute the Pascal-S program. Do not report success after any compilation error.

## Domain language

- **Pascal-S:** the exact restricted Pascal language below, not general Pascal.
- **Front-end:** lexical analysis, parsing, symbol management, and static semantic validation; no code generation is requested.
- **Symbol:** the shared record for an identifier and its attributes. An ID token carries a reference to this record, not just its spelling.
- **Scope/environment:** a dictionary of symbols linked to its enclosing environment, or an equivalent stack of dictionaries.
- **Declaration:** the operation that gives a variable its declared type in a scope. Merely interning its name must not count as declaring it.
- **Panic-mode recovery:** discard input until `;`, repair parser state, then resume parsing rather than stopping at the first syntax error.

## 1. Lexer requirements — PDF §§1, 2.1, 3.1, 3.5

### Tokens

Reserved words, matched **case-insensitively** through a dictionary:

```text
program var integer real begin end if then else while do writeln not and or
```

| Category | Pattern/lexemes | Suggested token names from the PDF |
| --- | --- | --- |
| Identifier | `[a-zA-Z_][a-zA-Z0-9_]*` | `ID` |
| Integer literal | `\d+` | `NUM_INT` |
| Real literal | `\d+\.\d+` | `NUM_REAL` |
| Assignment | `:=` | `ASSIGN` |
| Separators | `:` `;` `,` `.` `(` `)` | `COLON SEMICOLON COMMA DOT LPAREN RPAREN` |
| Arithmetic | `+` `-` `*` `/` | `PLUS MINUS TIMES DIVIDE` |
| Relations | `=` `<>` `<` `<=` `>` `>=` | `EQ NE LT LE GT GE` |

Reserved-word token names are their uppercase spellings. Recognize an entire identifier before checking whether it is reserved, so `integer_value` remains an ID. Real literals need digits on both sides of the dot: `.5`, `5.`, and exponent notation are not real literals in this specification.

### Required behavior

- Ignore spaces/tabs and discard `//` comments through the end of the line and `{ ... }` block comments, including multiline comments.
- Track physical lines across all input, including comments. Report accurate line and column positions, not buffer-relative positions.
- Resolve overlapping patterns correctly: reals before integers, `:=` before `:`, and two-character relations before their one-character prefixes. Distinguish `/` from `//`.
- On an illegal character, report its position and spelling, skip it, and continue. An invalid input remains a failed compilation even if recovery reaches EOF.
- Handle EOF and incomplete constructs without hanging; an unterminated block comment must not disappear silently.
- Let the parser request tokens lazily through the lexer object's `token()` method, equivalent to `getNextToken()`. Do not precompute a list of tokens.
- **Do not read the whole source file into memory.** PLY's usual `lexer.input(file.read())` would violate the explicit requirement. Use buffered/refillable input, preserving positions and lexical state across refills. A small line-buffered approach may suffice, but multiline comments must survive refills and token boundaries must not be split incorrectly.
- Each `ID` token's value must reference its symbol-table entry. Reserved words are not variable entries. Preserve token occurrence positions separately from the symbol's declaration line.

The PDF's boilerplate is incomplete: it lacks comment handling, buffered streaming, symbol references, the parser, and several required diagnostics. It is a starting point, not a compliant solution.

## 2. Symbol-table requirements — PDF §§1, 3.2

- Use hash-based environments with parent links, or a stack of environments.
- Record **name, basic type, scope, displacement/offset, and physical declaration line**. The objectives mention displacement even though the example class omits it; its units/layout are unspecified.
- Return the actual symbol record from lookup, not a copied record. All occurrences of a declared ID must resolve to that shared object.
- Enter a child environment at each `begin` block and restore its parent at `end`. Lookup searches from the current environment outward.
- Reject a second declaration in the same scope. Resolve enclosing declarations when a name is absent locally; distinguish this from an undeclared use.
- Reject undeclared variable uses, including assignment targets and expressions.
- Handle the program's name as a program identifier, not an undeclared variable.
- Do not mistake a lexically interned but untyped placeholder for a declared variable. A declaration list may contain several IDs before its type is known.
- Coordinate lexer lookahead with scope changes so references are not permanently bound to the wrong environment. Reset symbols, scope state, positions, and error state between separate compilations.

The grammar permits variable declarations **only before the outer block**. Nested block environments are still required, but adding local `var` sections, functions, or procedures would extend the language and is not requested. Environments change as the lazy lexer yields `begin`/`end`, so every ID token carries the entry for its source scope.

## 3. Parser requirements — PDF §§1, 2.2, 3.3

Use PLY's `yacc` LALR(1) generator. Translate the following EBNF faithfully; `[...]` means optional and `{...}` means repetition. Prefer left recursion for list and operator productions to keep the parser stack small.

```ebnf
program         ::= "program" identifier ";" decl_list block "."
decl_list       ::= [ "var" decl_group_list ]
decl_group_list ::= decl_group { decl_group }
decl_group      ::= id_list ":" type ";"
id_list         ::= identifier { "," identifier }
type            ::= "integer" | "real"
block           ::= "begin" stmt_list "end"
stmt_list       ::= stmt { ";" stmt }
stmt            ::= assign_stmt | if_stmt | while_stmt | write_stmt | block | empty
empty           ::=
assign_stmt     ::= identifier ":=" expr
if_stmt         ::= "if" expr "then" stmt [ "else" stmt ]
while_stmt      ::= "while" expr "do" stmt
write_stmt      ::= "writeln" "(" expr_list ")"
expr_list       ::= expr { "," expr }
expr            ::= simple_expr [ relop simple_expr ]
simple_expr     ::= term { addop term }
term            ::= factor { mulop factor }
factor          ::= identifier | number | "(" expr ")" | "not" factor
relop           ::= "=" | "<>" | "<" | "<=" | ">" | ">="
addop           ::= "+" | "-" | "or"
mulop           ::= "*" | "/" | "and"
```

`identifier` corresponds to `ID`; `number` corresponds to `NUM_INT | NUM_REAL`. The PDF uses these two names without separate productions.

### Grammar consequences

- The `var` section is optional, but when present it contains at least one declaration group.
- Comma-separated declarations and `writeln` arguments must be supported. `writeln()` is not valid: `expr_list` is nonempty.
- Empty statements/blocks, repeated statement separators, and an optional trailing `;` before `end` follow from the empty production.
- A semicolon separates statements; it is not a mandatory terminator before `end` or `else`.
- Blocks may nest and may appear wherever a statement is allowed.
- The program ends in `end.`; reject unexpected trailing input.
- At most one relational operator is allowed per `expr`: unparenthesized chained comparisons are invalid.
- Highest to lowest expression precedence: parentheses/`not`, then `* / and`, then `+ - or`, then relations. Binary arithmetic/logical operators associate left; `not` nests recursively.
- Unary `+`/`-`, strings, arrays, booleans as declared types, procedures/functions, `for`, `readln`, casts, and extra Pascal operators are not in this grammar.

### Conflicts

The PDF calls its grammar unambiguous, but the optional `else` creates the classic **dangling-else ambiguity**. Explicitly resolve it so `else` binds to the nearest unmatched `if` (e.g. suitable `THEN`/`ELSE` precedence or matched/unmatched productions), and explain the decision in the report.

Inspect PLY's parser diagnostics/state output during development. The current generated table has no unresolved conflicts; `%prec IFX` below `ELSE` resolves dangling else by shifting `ELSE` to the nearest unmatched `if`. The grammar's separate `expr`/`simple_expr`/`term` levels encode operator grouping without additional precedence declarations. Explain these choices and the conflict analysis in the technical report.

## 4. Static semantic requirements — PDF §§1, 3.3

- Declared numeric types are exactly `integer` and `real`; propagate literal, identifier, and expression types through parser actions.
- **No implicit conversion or coercion between `integer` and `real`.**
- For `+`, `-`, `*`, `/`, and each relational operator, operands of different numeric types are a semantic error, even if a conversion would be mathematically safe.
- Assignment requires the target type to match the expression type exactly. Reject both real-to-integer and integer-to-real assignments.
- Abort compilation immediately and in a controlled manner on type incompatibility. Report a useful position and the incompatible types; do not continue as if validation succeeded or produce an unhandled traceback.
- Integrate duplicate/undeclared detection with these checks. No definite-assignment analysis or evaluation of program expressions is requested.

### Specification gaps and implementation interpretations

The PDF leaves these points open. This implementation uses the following narrow, explicit rules; confirm them with the professor if a different interpretation is expected:

1. **Logical expressions:** comparisons produce an internal `boolean`; `not`, `and`, and `or` require boolean operands; `if` and `while` require boolean conditions. Relational operators compare same-typed numeric operands only. Boolean variables and literals are not added.
2. **Division result:** `integer / integer` has type `integer`, matching the operand type and avoiding implicit conversion. Real division remains `real / real`.
3. **Identifier casing:** reserved words are case-insensitive; identifiers are case-sensitive.
4. **Displacement:** every symbol has an `offset` attribute, currently `None`, because the PDF gives no storage sizes or allocation rules. No memory-layout subsystem is added.

## 5. Diagnostics and panic-mode recovery — PDF §§3.4, 4

- Implement `p_error(p)` in `yacc.py`.
- Report a syntax error's **physical line, column, and offending token**. Handle `p is None` (unexpected EOF) explicitly.
- Synchronize on **semicolon `;`**, as required: discard bad tokens until the next semicolon, coordinate parser-stack recovery, and resume parsing the remaining input.
- Handle the case where the current offending token is already `;`, and terminate safely when EOF arrives before another separator.
- Preserve or repair scope state during recovery; discarded input must not leave stale environments or invalidate later diagnostics.
- Demonstrate multiple distinct syntax errors in one run and successful analysis of later statements where possible. A simple whole-parser restart is insufficient if it prevents the remaining block from being analyzed.
- Keep behaviors distinct: lexical errors skip illegal characters and continue; syntax errors recover; type incompatibilities stop compilation immediately.

In the illegal-character example below, removing `@` leaves `10 5`, which is also syntactically invalid. A lexical diagnostic followed by a syntax diagnostic/recovery is therefore expected, not evidence that lexical recovery failed.

## 6. Required validation — PDF §4

`tests/01-success.pas` through `tests/09-unterminated-comment.pas` cover the three required scenarios plus recovery, comments, case sensitivity, nested blocks, logical operations, integer division, dangling else, duplicate/undeclared identifiers, reverse assignment coercion, and unterminated comments. Actual command output and exit codes are saved under `tests/output/`. The following are the three mandatory scenarios; comments and formatting aside, these reproduce the PDF inputs.

### Scenario 1 — valid syntax and homogeneous types

```pascal
program SucessoSemantico;
var
    cont, limite : integer;
    taxa, acumulador : real;
begin
    cont := 0;
    limite := 100;
    taxa := 1.25;
    acumulador := 0.0;
    while cont < limite do
    begin
        cont := cont + 1;
        acumulador := acumulador + taxa
    end;
    writeln(cont, acumulador)
end.
```

Expected: successful front-end validation, no lexical/syntax/semantic errors. `writeln` is parsed and checked, not executed by this project.

### Scenario 2 — illegal character with recovery

```pascal
program TesteErroLexico;
var
    cont : integer;
begin
    cont := 10 @ 5; // '@' is illegal
    writeln(cont)
end.
```

Expected: report the exact line/column of `@`, skip it, recover from the resulting syntax error at `;`, and continue through the remaining block. Compilation must still be marked failed.

### Scenario 3 — immediate type failure

```pascal
program IncompatibilidadeDeTipos;
var
    cont : integer;
    acumulador, taxa : real;
begin
    acumulador := 5.5;
    taxa := 1.1;
    cont := acumulador + taxa; // real expression assigned to integer
    writeln(cont)
end.
```

Expected: immediate, controlled semantic failure at the assignment to `cont`.

### Additional test coverage

The PDF explicitly asks for a substantial error-focused test battery because the professor will probe edge cases. Include:

- All tokens/operators, mixed-case reserved words, identifier boundaries, and malformed numeric input.
- Both comment forms, multiline/unterminated comments, `/` versus `//`, blank lines, line endings, and correct positions after buffer refills.
- Lazy token consumption and a large source file without whole-file reading or pretokenization.
- No declarations, grouped declarations, repeated declarations, undeclared reads/writes, shared symbol references, and nested-scope lookup/restoration.
- Empty/nested blocks, repeated/trailing semicolons, lists, dangling `else`, precedence, parentheses, `not`, `and`, and `or` under the documented type policy.
- Rejection of missing delimiters, chained relations, unsupported syntax, and input after the final dot.
- Same-type numeric operations; mixed-type failures for every arithmetic/relational operator; incompatible assignments in both directions.
- Multiple syntax errors in one input, recovery at an already-present semicolon, continued parsing after recovery, unexpected EOF, and EOF during synchronization.
- Independent compiler runs with no leaked symbols, line counters, or error state.

Keep test tooling small; input files plus a direct runner/output capture are sufficient. Do not fabricate expected logs as actual compiler output.

## 7. Submission, report, and grading — PDF §5

Submit **one ZIP**, named `TP1_NomeCompleto1_NomeCompleto2.zip` for a two-person group; confirm the naming convention for a solo submission. No deadline is stated in the PDF.

Required work/deliverables:

1. Complete, documented Python source: `lex.py`, `yacc.py`, and the symbol-table module.
2. Present and explain the code to the professor.
3. An **academic-format technical PDF report** covering design decisions, the Pascal-S grammar, and a detailed analysis of parser conflicts and their resolutions. Explain streaming, symbol references/scopes, typing, and error recovery as part of the design.
4. Test scripts/input files for success, lexical failure, and type failure, together with the corresponding output logs. Include the broader test battery as well.

| Evaluation item | Weight | Main criteria |
| --- | --- | --- |
| Lexer | 25% | Correct token patterns, whitespace/comments, physical lines, lazy tokenization. |
| Symbol table and types | 20% | Static scopes, mandatory ID references, early duplicate/undeclared detection. |
| Parser | 35% | Exact grammar, correct precedence/associativity, elimination of unresolved conflicts. |
| Error recovery | 10% | Semicolon panic-mode synchronization and multiple syntax diagnostics. |
| Technical report and organization | 10% | Academic PDF, documented decisions, detailed shift/reduce conflict analysis. |

## Completion checklist

- [x] Document narrow interpretations of the specification gaps without extending the language.
- [x] Implement the three modules with the **minimum necessary concise, direct code**.
- [x] Verify streaming, symbol references/attributes, nested scopes, grammar, and strong typing.
- [x] Verify precise diagnostics, syntax recovery, and immediate type-error termination.
- [x] Save compiler output logs for the required and additional test inputs.
- [ ] Inspect/document parser conflicts in the technical PDF report.
- [ ] Prepare the code explanation, verify ZIP contents/naming, and submit.
