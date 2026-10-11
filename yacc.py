"""Pascal-S LALR(1) parser and front-end command-line entry point."""

import sys

import ply.yacc as ply_yacc

from lex import PascalLexer, tokens
from symbol_table import SymbolTable

BOOL = "boolean"
symbols = None
scanner = None
syntax_errors = 0
precedence = (("nonassoc", "IFX"), ("nonassoc", "ELSE"))


class CompileError(Exception):
    pass


def location(token):
    return token.lineno, token.lexpos + 1


def semantic_error(message, token):
    line, column = location(token)
    print(f"Semantic error at {line}:{column}: {message}", file=sys.stderr)
    raise CompileError(message)


def variable_type(symbol, token):
    if symbol.kind != "variable" or not symbol.declared:
        semantic_error(f"undeclared variable {symbol.name!r}", token)
    return symbol.type


def numeric_pair(left, right, operator, token):
    if left not in ("integer", "real") or right not in ("integer", "real"):
        semantic_error(f"operator {operator!r} requires numeric operands", token)
    if left != right:
        semantic_error(f"operator {operator!r} cannot mix {left} and {right}", token)
    return left


def boolean_pair(left, right, operator, token):
    if left != BOOL or right != BOOL:
        semantic_error(f"operator {operator!r} requires boolean operands", token)
    return BOOL


def p_program(p):
    "program : program_header decl_list block DOT"


def p_program_header(p):
    "program_header : PROGRAM ID SEMICOLON"
    symbols.declare_program(p[2])


def p_decl_list(p):
    """decl_list : VAR decl_group_list
                 | empty"""


def p_decl_group_list(p):
    """decl_group_list : decl_group
                        | decl_group_list decl_group"""


def p_decl_group(p):
    "decl_group : id_list COLON type SEMICOLON"
    for symbol, token in p[1]:
        if not symbols.declare(symbol, p[3], token.lineno):
            semantic_error(f"duplicate declaration of {symbol.name!r}", token)


def p_id_list_one(p):
    "id_list : ID"
    p[0] = [(p[1], p.slice[1])]


def p_id_list_more(p):
    "id_list : id_list COMMA ID"
    p[0] = p[1] + [(p[3], p.slice[3])]


def p_type(p):
    """type : INTEGER
             | REAL"""
    p[0] = p[1].lower()


def p_block(p):
    "block : BEGIN stmt_list END"


def p_stmt_list(p):
    """stmt_list : stmt
                  | stmt_list SEMICOLON stmt
                  | error SEMICOLON stmt
                  | stmt_list SEMICOLON error SEMICOLON stmt"""


def p_stmt(p):
    """stmt : assign_stmt
             | if_stmt
             | while_stmt
             | write_stmt
             | block
             | empty"""


def p_empty(p):
    "empty :"
    p[0] = None


def p_assign_stmt(p):
    "assign_stmt : ID ASSIGN expr"
    target_type = variable_type(p[1], p.slice[1])
    if target_type != p[3]:
        semantic_error(f"cannot assign {p[3]} to {target_type} variable {p[1].name!r}", p.slice[1])


def p_if_stmt(p):
    """if_stmt : IF expr THEN stmt %prec IFX
                | IF expr THEN stmt ELSE stmt"""
    if p[2] != BOOL:
        semantic_error("if condition must be boolean", p.slice[1])


def p_while_stmt(p):
    "while_stmt : WHILE expr DO stmt"
    if p[2] != BOOL:
        semantic_error("while condition must be boolean", p.slice[1])


def p_write_stmt(p):
    "write_stmt : WRITELN LPAREN expr_list RPAREN"


def p_expr_list(p):
    """expr_list : expr
                  | expr_list COMMA expr"""


def p_expr_simple(p):
    "expr : simple_expr"
    p[0] = p[1]


def p_expr_relation(p):
    "expr : simple_expr relop simple_expr"
    numeric_pair(p[1], p[3], p[2][0], p[2][1])
    p[0] = BOOL


def p_simple_expr_term(p):
    "simple_expr : term"
    p[0] = p[1]


def p_simple_expr_more(p):
    "simple_expr : simple_expr addop term"
    operator, token = p[2]
    if operator == "or":
        p[0] = boolean_pair(p[1], p[3], operator, token)
    else:
        p[0] = numeric_pair(p[1], p[3], operator, token)


def p_term_factor(p):
    "term : factor"
    p[0] = p[1]


def p_term_more(p):
    "term : term mulop factor"
    operator, token = p[2]
    if operator == "and":
        p[0] = boolean_pair(p[1], p[3], operator, token)
    else:
        p[0] = numeric_pair(p[1], p[3], operator, token)


def p_factor_id(p):
    "factor : ID"
    p[0] = variable_type(p[1], p.slice[1])


def p_factor_number(p):
    """factor : NUM_INT
              | NUM_REAL"""
    p[0] = "integer" if p.slice[1].type == "NUM_INT" else "real"


def p_factor_group(p):
    "factor : LPAREN expr RPAREN"
    p[0] = p[2]


def p_factor_not(p):
    "factor : NOT factor"
    if p[2] != BOOL:
        semantic_error("not requires a boolean operand", p.slice[1])
    p[0] = BOOL


def p_relop(p):
    """relop : EQ
              | NE
              | LT
              | LE
              | GT
              | GE"""
    p[0] = (p[1], p.slice[1])


def p_addop(p):
    """addop : PLUS
              | MINUS
              | OR"""
    p[0] = (p[1].lower(), p.slice[1])


def p_mulop(p):
    """mulop : TIMES
              | DIVIDE
              | AND"""
    p[0] = (p[1].lower(), p.slice[1])


def p_error(token):
    global syntax_errors
    syntax_errors += 1
    if token is None:
        line, column = scanner.position()
        print(f"Syntax error at {line}:{column}: unexpected end of file", file=sys.stderr)
    else:
        value = getattr(token.value, "name", token.value)
        print(f"Syntax error at {token.lineno}:{token.column}: unexpected {value!r} ({token.type})", file=sys.stderr)
    # The stmt_list error productions make PLY discard through the next semicolon.
    symbols.current = symbols.root


parser = ply_yacc.yacc(start="program", write_tables=False, debug=False)


def compile_file(path):
    global symbols, scanner, syntax_errors
    symbols = SymbolTable()
    syntax_errors = 0
    try:
        with open(path, encoding="utf-8") as source:
            scanner = PascalLexer(source, symbols)
            parser.parse(lexer=scanner)
    except CompileError:
        return False
    if scanner.errors or syntax_errors:
        return False
    print("Compilation succeeded.")
    return True


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} source.pas", file=sys.stderr)
        return 2
    try:
        return 0 if compile_file(sys.argv[1]) else 1
    except OSError as error:
        print(f"Cannot read source: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
