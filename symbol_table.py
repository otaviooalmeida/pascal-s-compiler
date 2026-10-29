"""Registros compartilhados, assinaturas e ambientes léxicos de Pascal-S."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Parameter:
    type: object
    by_ref: bool = False


@dataclass(frozen=True)
class ArrayType:
    bounds: tuple
    element: object

    def __str__(self):
        def label(number):
            return str(number) if number.bit_length() < 1024 else "<large integer>"
        bounds = ",".join(f"{label(low)}..{label(high)}" for low, high in self.bounds)
        return f"array[{bounds}] of {self.element}"


class Symbol:
    def __init__(self, name, scope, lineno):
        self.name = name
        self.scope = scope
        self.lineno = lineno
        self.references = {}
        self.type = None
        self.offset = None
        self.kind = "variable"
        self.declared = False
        self.parameters = None
        self.builtin = False
        self.value = None
        self.io_mode = None


class Environment:
    def __init__(self, parent, number, owner=None):
        self.parent = parent
        self.number = number
        self.owner = owner
        self.symbols = {}
        self.next_offset = 0


def storage_size(var_type):
    if isinstance(var_type, ArrayType):
        size = storage_size(var_type.element)
        for low, high in var_type.bounds:
            size *= high - low + 1
        return size
    return {"integer": 4, "real": 8, "boolean": 1, "char": 1, "string": 8}[var_type]


class SymbolTable:
    """Busca nomes sem distinção de caixa e mantém declarações locais separadas."""

    def __init__(self):
        self.root = Environment(None, 0)
        self.current = self.root
        self.next_scope = 1
        self.environments = {0: self.root}

    def push(self, owner=None):
        self.current = Environment(self.current, self.next_scope, owner)
        self.environments[self.next_scope] = self.current
        self.next_scope += 1
        return self.current

    def pop(self):
        if self.current.parent is not None:
            self.current = self.current.parent

    def lookup(self, name):
        env = self.current
        while env is not None:
            if name.lower() in env.symbols:
                return env.symbols[name.lower()]
            env = env.parent
        return None

    def reference(self, name, lineno, local=False):
        symbol = self.current.symbols.get(name.lower()) if local else self.lookup(name)
        if symbol is None:
            symbol = Symbol(name, self.current.number, lineno)
            self.current.symbols[name.lower()] = symbol
        return symbol

    def define(self, symbol, kind, var_type, lineno, parameters=None, value=None):
        if symbol.declared and not symbol.builtin:
            return False
        symbol.kind = kind
        symbol.type = var_type
        symbol.lineno = lineno
        symbol.parameters = parameters
        symbol.value = value
        symbol.io_mode = None
        symbol.builtin = False
        symbol.declared = True
        if kind == "variable":
            env = self.environments[symbol.scope]
            symbol.offset = env.next_offset
            env.next_offset += storage_size(var_type)
        return True

    def declare(self, symbol, var_type, lineno):
        return self.define(symbol, "variable", var_type, lineno)

    def declare_builtin(self, name, parameters, result_type, io_mode=None):
        symbol = self.reference(name, 0)
        if not self.define(symbol, "function" if result_type is not None else "procedure",
                           result_type, 0, parameters):
            return None
        symbol.builtin = True
        symbol.io_mode = io_mode
        return symbol

    def owns_result(self, symbol):
        env = self.current
        while env is not None:
            if env.owner is symbol and symbol.kind == "function":
                return True
            env = env.parent
        return False
