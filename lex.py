"""Buffered, on-demand lexer for the Pascal-S subset."""

import sys

import ply.lex as ply_lex

reserved = {word: word.upper() for word in (
    "program var integer real begin end if then else while do writeln not and or"
).split()}

tokens = [
    "ID", "NUM_INT", "NUM_REAL", "ASSIGN", "COLON", "SEMICOLON", "COMMA", "DOT",
    "LPAREN", "RPAREN", "PLUS", "MINUS", "TIMES", "DIVIDE", "EQ", "NE", "LT",
    "LE", "GT", "GE",
] + list(reserved.values())
states = (("comment", "exclusive"),)


class PascalLexer:
    tokens = tokens
    states = states
    t_ignore = " \t"
    t_comment_ignore = ""

    t_ASSIGN = r":="
    t_COLON = r":"
    t_SEMICOLON = r";"
    t_COMMA = r","
    t_DOT = r"\."
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

    def __init__(self, source, symbols):
        self.source = source
        self.symbols = symbols
        self.errors = 0
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

    def t_ID(self, token):
        r"[a-zA-Z_][a-zA-Z0-9_]*"
        word = token.value.lower()
        if word in reserved:
            token.type = reserved[word]
            if token.type == "BEGIN":
                token.lexer.owner.symbols.push()
            elif token.type == "END":
                token.lexer.owner.symbols.pop()
        else:
            token.value = token.lexer.owner.symbols.reference(token.value, token.lineno)
        return token

    def t_NUM_REAL(self, token):
        r"\d+\.\d+"
        token.value = float(token.value)
        return token

    def t_NUM_INT(self, token):
        r"\d+"
        token.value = int(token.value)
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

    def t_error(self, token):
        owner = token.lexer.owner
        column = token.lexpos + 1
        print(f"Lexical error at {token.lineno}:{column}: illegal character {token.value[0]!r}", file=sys.stderr)
        owner.errors += 1
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
                if self.lexer.current_state() == "comment":
                    row, column = self.comment_start
                    print(f"Lexical error at {row}:{column}: unterminated block comment", file=sys.stderr)
                    self.errors += 1
                    self.lexer.begin("INITIAL")
                return None
            self.buffer = line
            self.lexer.input(line)
