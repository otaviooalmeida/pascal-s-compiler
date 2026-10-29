"""Analisador léxico com buffer e leitura sob demanda para Pascal-S."""

import sys

import ply.lex as ply_lex

# Pascal-S da referência + integer/real/writeln do TP1 + step/uses solicitados.
reserved = {word: word.upper() for word in (
    "and array begin case const div do downto else end for function if mod not "
    "of or procedure program record repeat then to type until var while "
    "integer real writeln step uses"
).split()}

tokens = [
    "ID", "NUM_INT", "NUM_REAL", "ASSIGN", "COLON", "SEMICOLON", "COMMA", "DOT",
    "LPAREN", "RPAREN", "PLUS", "MINUS", "TIMES", "DIVIDE", "EQ", "NE", "LT",
    "LE", "GT", "GE", "LBRACKET", "RBRACKET", "RANGE", "CHAR_LITERAL", "STRING_LITERAL",
] + list(reserved.values())
states = (("comment", "exclusive"), ("starcomment", "exclusive"))


class PascalLexer:
    """Tokeniza Pascal-S sob demanda e mantém os escopos sincronizados."""

    tokens = tokens
    states = states
    t_ignore = " \t"
    t_comment_ignore = ""
    t_starcomment_ignore = ""

    t_ASSIGN = r":="
    t_COLON = r":"
    t_SEMICOLON = r";"
    t_COMMA = r","
    t_DOT = r"\."
    t_RANGE = r"\.\."
    t_LBRACKET = r"\["
    t_RBRACKET = r"\]"
    t_LPAREN = r"\("
    t_RPAREN = r"\)"
    t_PLUS = r"\+"
    t_MINUS = r"-"
    t_TIMES = r"\*"
    t_DIVIDE = r"/"
    t_EQ = r"="
    t_NE = r"<>"
    t_LT = r"<"
    t_LE = r"<="
    t_GT = r">"
    t_GE = r">="

    def __init__(self, source, symbols, manage_scopes=True):
        self.source = source
        self.symbols = symbols
        self.manage_scopes = manage_scopes
        self.errors = 0
        self.error_lines = set()
        self.comment_start = None
        self.buffer = ""
        self.lexer = ply_lex.lex(object=self)
        self.lexer.owner = self
        self.lexer.input("")

    def t_LINE_COMMENT(self, token):
        r"//[^\n]*"

    def t_BLOCK_START(self, token):
        r"\{"
        token.lexer.owner.comment_start = (token.lineno, token.lexpos + 1)
        token.lexer.begin("comment")

    def t_STAR_START(self, token):
        r"\(\*"
        self.comment_start = (token.lineno, token.lexpos + 1)
        token.lexer.begin("starcomment")

    def t_STRING_LITERAL(self, token):
        r"'(?:[^'\r\n]|'')*'(?!')"
        token.value = token.value[1:-1].replace("''", "'")
        if not token.value:
            self.lexical_error(token, "empty string literal")
            return
        if len(token.value) == 1:
            token.type = "CHAR_LITERAL"
        return token

    def t_UNTERMINATED_STRING(self, token):
        r"'[^\r\n]*"
        self.lexical_error(token, "unterminated string literal")

    def t_ID(self, token):
        r"[a-zA-Z_][a-zA-Z0-9_]*"
        word = token.value.lower()
        if word in reserved:
            token.type = reserved[word]
            if self.manage_scopes:
                if token.type == "BEGIN":
                    self.symbols.push()
                elif token.type == "END":
                    self.symbols.pop()
        else:
            token.lexeme = token.value
            token.value = token.lexer.owner.symbols.reference(token.value, token.lineno)
        return token

    def t_NUM_REAL(self, token):
        r"\d+\.\d+"
        return token

    def t_NUM_INT(self, token):
        r"\d+"
        return token

    def t_newline(self, token):
        r"\n+"
        token.lexer.lineno += len(token.value)

    def t_comment_end(self, token):
        r"\}"
        token.lexer.begin("INITIAL")
        token.lexer.owner.comment_start = None

    def t_comment_newline(self, token):
        r"\n+"
        token.lexer.lineno += len(token.value)

    def t_comment_content(self, token):
        r"[^}\n]+"

    def t_starcomment_end(self, token):
        r"\*\)"
        token.lexer.begin("INITIAL")
        self.comment_start = None

    def t_starcomment_newline(self, token):
        r"\n+"
        token.lexer.lineno += len(token.value)

    def t_starcomment_content(self, token):
        r"[^*\n]+|\*(?!\))"

    def t_starcomment_error(self, token):
        token.lexer.skip(1)

    def lexical_error(self, token, message):
        print(f"Lexical error at {token.lineno}:{token.lexpos + 1}: {message}", file=sys.stderr)
        self.errors += 1
        self.error_lines.add(token.lineno)

    def t_error(self, token):
        self.lexical_error(token, f"illegal character {token.value[0]!r}")
        token.lexer.skip(1)

    def t_comment_error(self, token):
        token.lexer.skip(1)

    def position(self):

        if self.buffer.endswith("\n"):
            return self.lexer.lineno, 1
        return self.lexer.lineno, len(self.buffer.rstrip("\r\n")) + 1

    def token(self):

        while True:
            token = self.lexer.token()
            if token is not None:
                token.column = token.lexpos + 1
                return token
            line = self.source.readline()
            if line == "":
                if self.lexer.current_state() in ("comment", "starcomment"):
                    row, column = self.comment_start
                    print(f"Lexical error at {row}:{column}: unterminated block comment", file=sys.stderr)
                    self.errors += 1
                    self.error_lines.add(row)
                    self.lexer.begin("INITIAL")
                return None
            self.buffer = line
            self.lexer.input(line)
