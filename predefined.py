from symbol_table import Parameter


LIBRARIES = {
    "crt": (
        ("clrscr", (), None),
        ("keypressed", (), "boolean"),
        ("readkey", (), "char"),
        ("delay", (Parameter("milliseconds", "integer"),), None),
    ),
    "graph": (
        ("initgraph", (Parameter("driver", "integer", True), Parameter("mode", "integer", True),
                       Parameter("path", "string")), None),
        ("line", tuple(Parameter(name, "integer") for name in ("x1", "y1", "x2", "y2")), None),
        ("setcolor", (Parameter("color", "integer"),), None),
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


def import_library(symbols, name):
    for routine, parameters, result in LIBRARIES.get(name.lower(), ()):
        if symbols.declare_builtin(routine, parameters, result) is None:
            return routine
