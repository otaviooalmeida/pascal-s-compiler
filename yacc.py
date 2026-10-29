"""Parser LALR(1), resolução de nomes e verificação estática de Pascal-S."""

from dataclasses import dataclass
import sys

import ply.yacc as ply_yacc

import predefined
from lex import PascalLexer, tokens as lexer_tokens
from symbol_table import ArrayType, Environment, Parameter, SymbolTable

LEXICAL_ONLY_TOKENS = {"CASE", "RECORD"}
tokens = [token for token in lexer_tokens if token not in LEXICAL_ONLY_TOKENS]
BOOL = "boolean"
symbols = None
scanner = None
syntax_errors = 0
precedence = (("nonassoc", "IFX"), ("nonassoc", "ELSE"))


@dataclass
class Value:
    type: object
    symbol: object = None
    lvalue: bool = False
    constant: object = None
    is_constant: bool = False
    token: object = None


class CompileError(Exception):
    """Erro semântico impeditivo, já diagnosticado."""


def semantic_error(message, token):
    print(f"Semantic error at {token.lineno}:{token.lexpos + 1}: {message}", file=sys.stderr)
    raise CompileError(message)


def resolve(token, local=False):
    # Corrige também IDs obtidos pelo lookahead antes de uma mudança de ambiente.
    token.value = symbols.reference(token.value.name, token.lineno, local=local)
    if token.lineno > 0:
        token.value.references[(token.lineno, token.lexpos)] = token.lexeme
    return token.value


def define(symbol, kind, var_type, token, parameters=None, value=None):
    if not symbols.define(symbol, kind, var_type, token.lineno, parameters, value):
        semantic_error(f"duplicate declaration of {symbol.name!r}", token)


def numeric_pair(left, right, operator, token):
    if left.type not in ("integer", "real") or right.type not in ("integer", "real"):
        semantic_error(f"operator {operator!r} requires numeric operands", token)
    if left.type != right.type:
        semantic_error(f"operator {operator!r} cannot mix {left.type} and {right.type}", token)
    return left.type


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
        if not arguments and symbol.io_mode != "readln":
            semantic_error(f"procedure {symbol.name!r} requires arguments", token)
        for actual in arguments:
            if isinstance(actual.type, ArrayType):
                semantic_error(f"procedure {symbol.name!r} requires scalar arguments", token)
            if symbol.io_mode in ("read", "readln") and not actual.lvalue:
                semantic_error(f"procedure {symbol.name!r} requires variable arguments", token)
        return Value(None, token=token)
    parameters = symbol.parameters or ()
    if len(arguments) != len(parameters):
        semantic_error(f"{expected_kind} {symbol.name!r} expects {len(parameters)} argument(s), "
                       f"got {len(arguments)}", token)
    for index, (actual, parameter) in enumerate(zip(arguments, parameters), 1):
        expected = parameter.type if isinstance(parameter, Parameter) else parameter
        matches = actual.type in expected if isinstance(expected, tuple) else actual.type == expected
        if not matches:
            description = " or ".join(expected) if isinstance(expected, tuple) else str(expected)
            semantic_error(f"argument {index} of {symbol.name!r}: expected {description}, got {actual.type}", token)
        if isinstance(parameter, Parameter) and parameter.by_ref and not actual.lvalue:
            semantic_error(f"argument {index} of {symbol.name!r} is a var parameter and requires a variable", token)
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


def integer_value(text):
    # Não depende do limite de int(<texto decimal>) do Python 3.11+.
    value = 0
    for start in range(0, len(text), 500):
        chunk = text[start:start + 500]
        value = value * 10 ** len(chunk) + int(chunk)
    return value


def p_program(p):
    "program : program_header uses_section body DOT"


def p_program_header(p):
    "program_header : PROGRAM ID program_files SEMICOLON"
    symbol = resolve(p.slice[2], local=True)
    define(symbol, "program", None, p.slice[2])


def p_program_files(p):
    """program_files : LPAREN id_list RPAREN
                     | empty"""
    if len(p) == 4:
        for symbol, token in p[2]:
            define(symbol, "file", None, token)


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
    conflict = predefined.import_library(symbols, symbol.name)
    if conflict is not None:
        semantic_error(f"library routine {conflict!r} conflicts with declared identifier", p.slice[1])


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


def p_declaration_error(p):
    """decl_group : error SEMICOLON
                  type_group : error SEMICOLON
                  const_group : error SEMICOLON"""
    repair_scopes(p.parser)
    p.parser.errok()


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
    bounds, element = tuple(p[3]), p[6]
    if isinstance(element, ArrayType):
        bounds += element.bounds
        element = element.element
    p[0] = ArrayType(bounds, element)


def p_bounds(p):
    """bounds : bound
              | bounds COMMA bound"""
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]


def p_bound(p):
    "bound : expr RANGE expr"
    if any(value.type != "integer" or not value.is_constant or value.constant is None for value in (p[1], p[3])):
        semantic_error("array bounds must be integer constants", p.slice[2])
    if p[1].constant > p[3].constant:
        semantic_error("array lower bound exceeds upper bound", p.slice[2])
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
    if (symbol.kind == "function") != (p[3] is not None):
        semantic_error(f"invalid return type for {symbol.kind} {symbol.name!r}", p.slice[4])
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
    "parameter_group : parameter_mode id_list COLON type"
    p[0] = []
    for symbol, token in p[2]:
        define(symbol, "variable", p[4], token)
        p[0].append(Parameter(p[4], p[1]))


def p_parameter_mode(p):
    """parameter_mode : VAR
                      | empty"""
    p[0] = p[1] is not None


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
    p[0] = Value(symbol.type, symbol, symbol.declared and (symbol.kind == "variable" or symbols.owns_result(symbol)),
                 symbol.value, symbol.kind == "constant", p.slice[1])


def p_designator_index(p):
    """designator : designator LBRACKET expr_list RBRACKET
                  | call LBRACKET expr_list RBRACKET"""
    base = check_call(*p[1], "function") if isinstance(p[1], tuple) else p[1]
    indices = p[3]
    if base.symbol is not None and not base.symbol.declared:
        semantic_error(f"undeclared variable {base.symbol.name!r}", base.token)
    if base.symbol is not None and base.symbol.kind == "function" and not base.lvalue:
        base = check_call(base, [], "function")
    if not isinstance(base.type, ArrayType):
        semantic_error("cannot index non-array expression", p.slice[2])
    if len(indices) > len(base.type.bounds):
        semantic_error("too many array indices", p.slice[2])
    for index, (low, high) in zip(indices, base.type.bounds):
        if index.type != "integer":
            semantic_error("array index must be integer", p.slice[2])
        if index.is_constant and index.constant is not None and not low <= index.constant <= high:
            semantic_error("constant array index is out of bounds", p.slice[2])
    remaining = base.type.bounds[len(indices):]
    result = ArrayType(remaining, base.type.element) if remaining else base.type.element
    p[0] = Value(result, base.symbol, base.lvalue, token=base.token)


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
    "for_header : FOR designator ASSIGN expr direction expr step_spec DO"
    require_variable(p[2])
    if any(value.type != "integer" for value in (p[2], p[4], p[6])):
        semantic_error("for variable and limits must be integer", p.slice[1])
    if p[7] is not None:
        if p[7].type != "integer":
            semantic_error("for step must be integer", p.slice[1])
        if p[7].constant == 0:
            semantic_error("for step cannot be zero", p.slice[1])


def p_for_stmt(p):
    "for_stmt : for_header stmt"


def p_direction(p):
    """direction : TO
                 | DOWNTO"""


def p_step_spec(p):
    """step_spec : STEP expr
                 | empty"""
    p[0] = p[2] if len(p) == 3 else None


def p_repeat_stmt(p):
    "repeat_stmt : REPEAT stmt_list UNTIL expr"
    if p[4].type != BOOL:
        semantic_error("until condition must be boolean", p.slice[1])


def p_write_stmt(p):
    "write_stmt : WRITELN LPAREN expr_list RPAREN"
    if any(isinstance(value.type, ArrayType) for value in p[3]):
        semantic_error("writeln requires scalar arguments", p.slice[1])


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


def p_expr_simple(p):
    "expr : simple_expr"
    p[0] = p[1]


def p_expr_relation(p):
    "expr : simple_expr relop simple_expr"
    operator, token = p[2]
    if isinstance(p[1].type, ArrayType) or isinstance(p[3].type, ArrayType):
        semantic_error(f"operator {operator!r} requires scalar operands", token)
    if p[1].type in ("integer", "real") or p[3].type in ("integer", "real"):
        numeric_pair(p[1], p[3], operator, token)
    elif p[1].type != p[3].type:
        semantic_error(f"operator {operator!r} cannot mix {p[1].type} and {p[3].type}", token)
    p[0] = Value(BOOL, is_constant=p[1].is_constant and p[3].is_constant)


def p_simple_expr_term(p):
    "simple_expr : term"
    p[0] = p[1]


def p_simple_expr_more(p):
    "simple_expr : simple_expr addop term"
    operator, token = p[2]
    result = boolean_pair(p[1], p[3], operator, token) if operator == "or" else numeric_pair(p[1], p[3], operator, token)
    constant = None
    if result == "integer" and p[1].constant is not None and p[3].constant is not None:
        constant = p[1].constant + p[3].constant if operator == "+" else p[1].constant - p[3].constant
    p[0] = Value(result, constant=constant, is_constant=p[1].is_constant and p[3].is_constant)


def p_term_factor(p):
    "term : factor"
    p[0] = p[1]


def p_term_more(p):
    "term : term mulop factor"
    operator, token = p[2]
    result = boolean_pair(p[1], p[3], operator, token) if operator == "and" else numeric_pair(p[1], p[3], operator, token)
    if operator in ("div", "mod") and result != "integer":
        semantic_error(f"operator {operator!r} requires integer operands", token)
    if operator in ("div", "mod") and p[3].is_constant and p[3].constant == 0:
        semantic_error(f"operator {operator!r} cannot divide by zero", token)
    constant = None
    if result == "integer" and p[1].constant is not None and p[3].constant is not None:
        left, right = p[1].constant, p[3].constant
        if operator == "*":
            constant = left * right
        elif operator in ("div", "mod"):
            quotient = abs(left) // abs(right) * (-1 if (left < 0) != (right < 0) else 1)
            constant = quotient if operator == "div" else left - quotient * right
    p[0] = Value(result, constant=constant, is_constant=p[1].is_constant and p[3].is_constant)


def p_factor_designator(p):
    "factor : designator"
    p[0] = read_value(p[1])


def p_factor_call(p):
    "factor : call"
    p[0] = check_call(*p[1], "function")


def p_factor_literal(p):
    """factor : NUM_INT
              | NUM_REAL
              | CHAR_LITERAL
              | STRING_LITERAL"""
    kind = p.slice[1].type
    var_type = {"NUM_INT": "integer", "NUM_REAL": "real", "CHAR_LITERAL": "char", "STRING_LITERAL": "string"}[kind]
    constant = integer_value(p[1]) if kind == "NUM_INT" else (p[1] if kind != "NUM_REAL" else None)
    p[0] = Value(var_type, constant=constant, is_constant=True, token=p.slice[1])


def p_factor_group(p):
    "factor : LPAREN expr RPAREN"
    p[0] = Value(p[2].type, constant=p[2].constant, is_constant=p[2].is_constant)


def p_factor_sign(p):
    """factor : PLUS factor
              | MINUS factor"""
    if p[2].type not in ("integer", "real"):
        semantic_error("unary sign requires a numeric operand", p.slice[1])
    constant = p[2].constant
    if constant is not None and p[1] == "-":
        constant = -constant
    p[0] = Value(p[2].type, constant=constant, is_constant=p[2].is_constant)


def p_factor_not(p):
    "factor : NOT factor"
    if p[2].type != BOOL:
        semantic_error("not requires a boolean operand", p.slice[1])
    p[0] = Value(BOOL, is_constant=p[2].is_constant)


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
             | DIV
             | MOD
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
    occurrences = sorted(
        ((line, column, name, symbol)
         for env in symbols.environments.values()
         for symbol in env.symbols.values()
         for (line, column), name in symbol.references.items()),
        key=lambda item: item[:2],
    )
    for line, _, name, symbol in occurrences:
        offset = symbol.offset
        if offset is None:
            offset = "-"
        elif offset.bit_length() >= 1024:
            offset = "<large integer>"
        scope = "global" if symbol.scope == 0 else "local"
        print(f"{scope}\t{name}\t{symbol.kind}\t{symbol.type or '-'}\t"
              f"{offset}\t{line}\t{symbol.declared}")


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
