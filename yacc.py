"""Parser LALR(1), resolução de nomes e verificação estática de Pascal-S."""

from dataclasses import dataclass
import sys

import ply.yacc as ply_yacc

import predefined
from lex import PascalLexer, tokens as lexer_tokens
from symbol_table import ArrayType, Environment, SymbolTable

LEXICAL_ONLY_TOKENS = {"CASE", "RECORD", "STEP"}
tokens = [token for token in lexer_tokens if token not in LEXICAL_ONLY_TOKENS]
BOOL = "boolean"
symbols = None
scanner = None
syntax_errors = 0
precedence = (
    ("nonassoc", "IFX"), ("nonassoc", "ELSE"),
    ("left", "OR"), ("left", "AND"),
    ("nonassoc", "EQ", "NE", "LT", "LE", "GT", "GE"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE", "DIV", "MOD"),
    ("right", "UPLUS", "UMINUS", "NOT"),
)


@dataclass
class Value:
    type: object
    symbol: object = None
    constant: object = None
    is_constant: bool = False
    token: object = None


class CompileError(Exception):
    """Erro semântico impeditivo, já diagnosticado."""


def semantic_error(message, token):
    print(f"Semantic error at {token.lineno}:{token.lexpos + 1}: {message}", file=sys.stderr)
    raise CompileError(message)


def resolve(token, local=False):
    token.value = symbols.reference(token.value.name, token.lineno, local=local)
    if token.lineno:
        token.value.references[(token.lineno, token.lexpos)] = token.lexeme
    return token.value


def define(symbol, kind, var_type, token, parameters=None, value=None):
    if not symbols.define(symbol, kind, var_type, token.lineno, parameters, value):
        semantic_error(f"duplicate declaration of {symbol.name!r}", token)


def numeric_pair(left, right, operator, token):
    if left.type != right.type:
        semantic_error(f"operator {operator!r} cannot mix {left.type} and {right.type}", token)
    if left.type not in ("integer", "real") or right.type not in ("integer", "real"):
        semantic_error(f"operator {operator!r} requires numeric operands", token)
    return "real" if operator == "/" else left.type


def boolean_pair(left, right, operator, token):
    if left.type != BOOL or right.type != BOOL:
        semantic_error(f"operator {operator!r} requires boolean operands", token)
    return BOOL


def require_variable(value):
    symbol, token = value.symbol, value.token
    if symbol is None:
        semantic_error("expression is not an assignable variable", token)
    if not symbol.declared:
        semantic_error(f"undeclared variable {symbol.name!r}", token)
    if symbol.kind == "function" and symbols.owns_result(symbol):
        return
    if symbol.kind != "variable":
        semantic_error(f"{symbol.name!r} is not an assignable variable", token)


def check_call(value, arguments, expected_kind):
    symbol, token = value.symbol, value.token
    if symbol is None:
        semantic_error(f"expression is not a {expected_kind}", token)
    if not symbol.declared:
        semantic_error(f"undeclared {expected_kind} {symbol.name!r}", token)
    if symbol.kind != expected_kind:
        semantic_error(f"{symbol.name!r} is not a {expected_kind}", token)
    if symbol.io_mode:
        return Value(None, token=token)
    parameters = symbol.parameters or ()
    if len(arguments) != len(parameters):
        semantic_error(f"{expected_kind} {symbol.name!r} expects {len(parameters)} argument(s), "
                       f"got {len(arguments)}", token)
    for index, (actual, parameter) in enumerate(zip(arguments, parameters), 1):
        expected = getattr(parameter, "type", parameter)
        if actual.type not in (expected if isinstance(expected, tuple) else (expected,)):
            description = " or ".join(expected) if isinstance(expected, tuple) else expected
            semantic_error(f"argument {index} of {symbol.name!r}: expected {description}, got {actual.type}", token)
    return Value(symbol.type, token=token)


def read_value(value):
    symbol, token = value.symbol, value.token
    if symbol is None or (symbol.kind == "function" and symbols.owns_result(symbol)):
        return value
    if symbol.kind == "function" and symbol.declared:
        return check_call(value, [], "function")
    if symbol.kind == "procedure" and symbol.declared:
        semantic_error(f"procedure {symbol.name!r} cannot be used as an expression", token)
    if not symbol.declared or symbol.kind not in ("variable", "constant"):
        semantic_error(f"undeclared variable {symbol.name!r}", token)
    return value


def repair_scopes(parser):
    for item in reversed(parser.symstack):
        if isinstance(getattr(item, "value", None), Environment):
            symbols.current = item.value
            return
    symbols.current = symbols.root


def p_program(p):
    "program : program_header uses_section body DOT"


def p_program_header(p):
    "program_header : PROGRAM ID SEMICOLON"
    symbol = resolve(p.slice[2], local=True)
    define(symbol, "program", None, p.slice[2])


def p_uses_section(p):
    """uses_section : USES library_list SEMICOLON
                    | empty"""


def p_library_list(p):
    """library_list : library_name
                    | library_list COMMA library_name"""


def p_library_name(p):
    "library_name : ID"
    symbol = resolve(p.slice[1], local=True)
    define(symbol, "library", None, p.slice[1])
    predefined.import_library(symbols, symbol.name)


def p_body(p):
    "body : const_section type_section var_section callable_list block"


def p_const_section(p):
    """const_section : CONST const_groups
                     | empty"""


def p_const_groups(p):
    """const_groups : const_group
                    | const_groups const_group"""


def p_const_group(p):
    "const_group : ID EQ expr SEMICOLON"
    if not p[3].is_constant:
        semantic_error("constant declaration requires a constant expression", p.slice[1])
    define(resolve(p.slice[1], local=True), "constant", p[3].type, p.slice[1], value=p[3].constant)


def p_type_section(p):
    """type_section : TYPE type_groups
                    | empty"""


def p_type_groups(p):
    """type_groups : type_group
                   | type_groups type_group"""


def p_type_group(p):
    "type_group : ID EQ type SEMICOLON"
    define(resolve(p.slice[1], local=True), "type", p[3], p.slice[1])


def p_var_section(p):
    """var_section : VAR decl_group_list
                   | empty"""


def p_decl_group_list(p):
    """decl_group_list : decl_group
                       | decl_group_list decl_group"""


def p_decl_group(p):
    "decl_group : id_list COLON type SEMICOLON"
    for symbol, token in p[1]:
        define(symbol, "variable", p[3], token)


def p_id_list_one(p):
    "id_list : ID"
    p[0] = [(resolve(p.slice[1], local=True), p.slice[1])]


def p_id_list_more(p):
    "id_list : id_list COMMA ID"
    p[1].append((resolve(p.slice[3], local=True), p.slice[3]))
    p[0] = p[1]


def p_type(p):
    """type : INTEGER
            | REAL
            | ID"""
    if p.slice[1].type == "ID":
        symbol = resolve(p.slice[1])
        if not symbol.declared or symbol.kind != "type":
            semantic_error(f"undeclared type {symbol.name!r}", p.slice[1])
        p[0] = symbol.type
    else:
        p[0] = p[1].lower()


def p_type_array(p):
    "type : ARRAY LBRACKET bounds RBRACKET OF type"
    p[0] = ArrayType(tuple(p[3]), p[6])


def p_bounds(p):
    """bounds : bound
              | bounds COMMA bound"""
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]


def p_bound(p):
    "bound : expr RANGE expr"
    p[0] = (p[1].constant, p[3].constant)


def p_callable_list(p):
    """callable_list : callable_list callable_decl
                     | empty"""


def p_callable_start(p):
    """callable_start : FUNCTION ID
                      | PROCEDURE ID"""
    symbol = resolve(p.slice[2], local=True)
    define(symbol, p[1].lower(), None, p.slice[2])
    p[0] = symbols.push(owner=symbol)


def p_callable_header(p):
    "callable_header : callable_start formal_parameters result_spec SEMICOLON"
    symbol = p[1].owner
    symbol.parameters = tuple(p[2])
    symbol.type = p[3]
    p[0] = p[1]


def p_result_spec(p):
    """result_spec : COLON type
                   | empty"""
    p[0] = p[2] if len(p) == 3 else None


def p_formal_parameters(p):
    """formal_parameters : LPAREN parameter_groups RPAREN
                         | LPAREN RPAREN
                         | empty"""
    p[0] = p[2] if len(p) == 4 else []


def p_parameter_groups(p):
    """parameter_groups : parameter_group
                        | parameter_groups SEMICOLON parameter_group"""
    p[0] = p[1] if len(p) == 2 else p[1] + p[3]


def p_parameter_group(p):
    """parameter_group : VAR id_list COLON type
                       | id_list COLON type"""
    names, var_type = (p[2], p[4]) if len(p) == 5 else (p[1], p[3])
    p[0] = []
    for symbol, token in names:
        define(symbol, "variable", var_type, token)
        p[0].append(var_type)


def p_callable_decl(p):
    "callable_decl : callable_header body SEMICOLON"
    symbols.current = p[1].parent


def p_block_open(p):
    "block_open : BEGIN"
    p[0] = symbols.push()


def p_block(p):
    "block : block_open stmt_list END"
    symbols.pop()


def p_stmt_list(p):
    """stmt_list : stmt
                 | stmt_list SEMICOLON stmt
                 | error SEMICOLON stmt
                 | stmt_list SEMICOLON error SEMICOLON stmt"""
    if any(item.type == "error" for item in p.slice):
        repair_scopes(p.parser)
        p.parser.errok()


def p_stmt(p):
    """stmt : assign_stmt
            | call_stmt
            | if_stmt
            | while_stmt
            | for_stmt
            | repeat_stmt
            | write_stmt
            | block
            | empty"""


def p_empty(p):
    "empty :"
    p[0] = None


def p_designator(p):
    "designator : ID"
    symbol = resolve(p.slice[1])
    p[0] = Value(symbol.type, symbol=symbol, constant=symbol.value,
                 is_constant=symbol.kind == "constant", token=p.slice[1])


def p_designator_index(p):
    "designator : designator LBRACKET expr_list RBRACKET"
    base = p[1]
    p[0] = Value(base.type.element, symbol=base.symbol, token=base.token)


def p_assign_stmt(p):
    "assign_stmt : designator ASSIGN expr"
    require_variable(p[1])
    if p[1].type != p[3].type:
        semantic_error(f"cannot assign {p[3].type} to {p[1].type} variable {p[1].symbol.name!r}", p[1].token)


def p_call(p):
    "call : designator LPAREN arguments RPAREN"
    p[0] = (p[1], p[3])


def p_call_stmt(p):
    """call_stmt : call
                 | designator"""
    value, arguments = p[1] if isinstance(p[1], tuple) else (p[1], [])
    check_call(value, arguments, "procedure")


def p_if_stmt(p):
    """if_stmt : IF expr THEN stmt %prec IFX
               | IF expr THEN stmt ELSE stmt"""
    if p[2].type != BOOL:
        semantic_error("if condition must be boolean", p.slice[1])


def p_while_stmt(p):
    "while_stmt : WHILE expr DO stmt"
    if p[2].type != BOOL:
        semantic_error("while condition must be boolean", p.slice[1])


def p_for_header(p):
    "for_header : FOR designator ASSIGN expr direction expr DO"
    require_variable(p[2])
    if any(value.type != "integer" for value in (p[2], p[4], p[6])):
        semantic_error("for variable and limits must be integer", p.slice[1])


def p_for_stmt(p):
    "for_stmt : for_header stmt"


def p_direction(p):
    """direction : TO
                 | DOWNTO"""


def p_repeat_stmt(p):
    "repeat_stmt : REPEAT stmt_list UNTIL expr"
    if p[4].type != BOOL:
        semantic_error("until condition must be boolean", p.slice[1])


def p_write_stmt(p):
    "write_stmt : WRITELN LPAREN expr_list RPAREN"


def p_expr_list(p):
    """expr_list : expr
                 | expr_list COMMA expr"""
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[1].append(p[3])
        p[0] = p[1]


def p_arguments(p):
    """arguments : expr_list
                 | empty"""
    p[0] = p[1] if p[1] is not None else []


def p_expr_factor(p):
    "expr : factor"
    p[0] = p[1]


def p_expr_binary(p):
    """expr : expr OR expr
            | expr AND expr
            | expr EQ expr
            | expr NE expr
            | expr LT expr
            | expr LE expr
            | expr GT expr
            | expr GE expr
            | expr PLUS expr
            | expr MINUS expr
            | expr TIMES expr
            | expr DIVIDE expr
            | expr DIV expr
            | expr MOD expr"""
    left, right, operator = p[1], p[3], p[2].lower()
    if operator in ("and", "or"):
        result = boolean_pair(left, right, operator, p.slice[2])
    elif operator in ("=", "<>", "<", "<=", ">", ">="):
        if left.type != right.type:
            semantic_error(f"operator {operator!r} cannot mix {left.type} and {right.type}", p.slice[2])
        if left.type in ("integer", "real"):
            numeric_pair(left, right, operator, p.slice[2])
        result = BOOL
    else:
        result = numeric_pair(left, right, operator, p.slice[2])
        if operator in ("div", "mod") and result != "integer":
            semantic_error(f"operator {operator!r} requires integer operands", p.slice[2])
    constant = None
    if result == "integer" and left.constant is not None and right.constant is not None:
        if operator == "+":
            constant = left.constant + right.constant
        elif operator == "-":
            constant = left.constant - right.constant
        elif operator == "*":
            constant = left.constant * right.constant
    p[0] = Value(result, constant=constant, is_constant=left.is_constant and right.is_constant)


def p_factor_literal(p):
    """factor : NUM_INT
              | NUM_REAL
              | CHAR_LITERAL
              | STRING_LITERAL"""
    kind = p.slice[1].type
    var_type = {"NUM_INT": "integer", "NUM_REAL": "real", "CHAR_LITERAL": "char", "STRING_LITERAL": "string"}[kind]
    constant = int(p[1]) if kind == "NUM_INT" else (p[1] if kind != "NUM_REAL" else None)
    p[0] = Value(var_type, constant=constant, is_constant=True, token=p.slice[1])


def p_factor_group(p):
    "factor : LPAREN expr RPAREN"
    p[0] = Value(p[2].type, constant=p[2].constant, is_constant=p[2].is_constant)


def p_factor_value(p):
    """factor : designator
              | call"""
    p[0] = check_call(*p[1], "function") if isinstance(p[1], tuple) else read_value(p[1])


def p_factor_sign(p):
    """factor : PLUS factor %prec UPLUS
              | MINUS factor %prec UMINUS
              | NOT factor"""
    if p.slice[1].type == "NOT":
        if p[2].type != BOOL:
            semantic_error("not requires a boolean operand", p.slice[1])
        p[0] = Value(BOOL, is_constant=p[2].is_constant)
        return
    if p[2].type not in ("integer", "real"):
        semantic_error("unary sign requires a numeric operand", p.slice[1])
    constant = p[2].constant
    if constant is not None and p.slice[1].type == "MINUS":
        constant = -constant
    p[0] = Value(p[2].type, constant=constant, is_constant=p[2].is_constant)


def p_error(token):
    global syntax_errors
    # shortcut: ignore adjacent lexical cascades; use error tokens if recovery expands.
    if (token is not None and scanner is not None
            and any(token.lineno - 1 <= line <= token.lineno for line in scanner.error_lines)):
        return
    syntax_errors += 1
    if token is None:
        line, column = scanner.position()
        print(f"Syntax error at {line}:{column}: unexpected end of file", file=sys.stderr)
    else:
        value = getattr(token.value, "name", token.value)
        print(f"Syntax error at {token.lineno}:{token.column}: unexpected {value!r} ({token.type})", file=sys.stderr)


parser = ply_yacc.yacc(start="program", write_tables=False, debug=False)


def compile_file(path):
    global symbols, scanner, syntax_errors
    symbols = SymbolTable()
    syntax_errors = 0
    predefined.install(symbols)
    try:
        with open(path, encoding="utf-8") as source:
            scanner = PascalLexer(source, symbols, manage_scopes=False)
            parser.parse(lexer=scanner)
    except CompileError:
        return False
    finally:
        symbols.current = symbols.root
    if scanner.errors or syntax_errors:
        return False
    print("Compilation succeeded.")
    return True


def print_symbol_table(path):
    print(f"Symbol table for: {path}")
    print("scope\tname\tkind\ttype\toffset\tline\tdeclared")
    entries = sorted(
        (line, column, name, symbol)
        for env in symbols.environments.values()
        for symbol in env.symbols.values()
        for (line, column), name in symbol.references.items()
    )
    for line, _, name, symbol in entries:
        scope = "global" if symbol.scope == 0 else "local"
        print(f"{scope}\t{name}\t{symbol.kind}\t{symbol.type or '-'}\t"
              f"{symbol.offset if symbol.offset is not None else '-'}\t{line}\t{symbol.declared}")


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} source.pas", file=sys.stderr)
        return 2
    try:
        return 0 if compile_file(sys.argv[1]) else 1
    except (OSError, UnicodeError) as error:
        print(f"Cannot read source: {error}", file=sys.stderr)
        return 2
    finally:
        print_symbol_table(sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())
