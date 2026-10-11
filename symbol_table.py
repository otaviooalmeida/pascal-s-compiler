"""Minimal symbol records and nested Pascal-S environments."""


class Symbol:
    def __init__(self, name, scope, lineno):
        self.name = name
        self.scope = scope
        self.lineno = lineno
        self.type = None
        self.offset = None
        self.kind = "variable"
        self.declared = False


class Environment:
    def __init__(self, parent, number):
        self.parent = parent
        self.number = number
        self.symbols = {}


class SymbolTable:
    def __init__(self):
        self.root = Environment(None, 0)
        self.current = self.root
        self.next_scope = 1

    def push(self):
        self.current = Environment(self.current, self.next_scope)
        self.next_scope += 1

    def pop(self):
        if self.current.parent is not None:
            self.current = self.current.parent

    def lookup(self, name):
        env = self.current
        while env is not None:
            if name in env.symbols:
                return env.symbols[name]
            env = env.parent
        return None

    def reference(self, name, lineno):
        symbol = self.lookup(name)
        if symbol is None:
            symbol = Symbol(name, self.current.number, lineno)
            self.current.symbols[name] = symbol
        return symbol

    def declare_program(self, symbol):
        symbol.kind = "program"
        symbol.declared = True

    def declare(self, symbol, var_type, lineno):
        if symbol.declared:
            return False
        symbol.type = var_type
        symbol.lineno = lineno
        symbol.declared = True
        return True
