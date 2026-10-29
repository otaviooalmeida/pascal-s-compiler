"""Assinaturas conhecidas: não carrega bibliotecas nem executa rotinas externas."""

from symbol_table import Parameter


LIBRARIES = {
    "crt": (
        ("clrscr", (), None),
        ("keypressed", (), "boolean"),
        ("readkey", (), "char"),
        ("delay", (Parameter("integer"),), None),
    ),
    "graph": (
        ("initgraph", (Parameter("integer", True), Parameter("integer", True), Parameter("string")), None),
        ("line", (Parameter("integer"),) * 4, None),
        ("setcolor", (Parameter("integer"),), None),
        ("closegraph", (), None),
    ),
}


def install(symbols):
    for name in ("boolean", "char", "string"):
        symbol = symbols.reference(name, 0)
        symbols.define(symbol, "type", name, 0)
        symbol.builtin = True
    for name, value in (("true", True), ("false", False)):
        symbol = symbols.reference(name, 0)
        symbols.define(symbol, "constant", "boolean", 0, value=value)
        symbol.builtin = True
    for name in ("write", "read", "readln"):
        symbols.declare_builtin(name, (), None, io_mode=name)
    for name in ("sin", "cos", "sqrt", "exp", "ln", "arctan"):
        symbols.declare_builtin(name, (("integer", "real"),), "real")
    # round é intencionalmente externo ao escopo solicitado, inclusive com uses Math.


def import_library(symbols, name):
    for routine, parameters, result in LIBRARIES.get(name.lower(), ()):
        if symbols.declare_builtin(routine, parameters, result) is None:
            return routine
