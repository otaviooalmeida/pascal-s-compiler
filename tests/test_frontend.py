"""Testes de regressão para recuperação de erros e deslocamentos por escopo."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import unittest

import yacc
from symbol_table import SymbolTable

TESTS = Path(__file__).parent


class FrontendTests(unittest.TestCase):
    def test_declaration_recovery_reaches_later_statements(self):
        errors = StringIO()
        with redirect_stderr(errors):
            self.assertFalse(yacc.compile_file(TESTS / "10-declaration-recovery.pas"))
        self.assertEqual(yacc.syntax_errors, 5)
        self.assertEqual(
            [line.split(": unexpected")[0] for line in errors.getvalue().splitlines()],
            [f"Syntax error at {position}" for position in
             ("3:12", "4:20", "11:19", "12:19", "14:15")],
        )
        self.assertIs(yacc.symbols.current, yacc.symbols.root)
        self.assertEqual(yacc.symbols.lookup("count").offset, 0)
        self.assertEqual(yacc.symbols.lookup("value").offset, 4)
        self.assertIsNone(yacc.symbols.lookup("broken").offset)

    def test_compiled_declarations_have_offsets(self):
        with redirect_stdout(StringIO()):
            self.assertTrue(yacc.compile_file(TESTS / "01-success.pas"))
        self.assertEqual(
            [yacc.symbols.lookup(name).offset for name in
             ("cont", "limite", "taxa", "acumulador")],
            [0, 4, 8, 16],
        )

    def test_offsets_are_local_and_duplicates_allocate_nothing(self):
        symbols = SymbolTable()
        first = symbols.reference("first", 1)
        self.assertTrue(symbols.declare(first, "integer", 1))
        self.assertFalse(symbols.declare(first, "real", 2))
        symbols.push()
        local = symbols.reference("local", 3)
        self.assertTrue(symbols.declare(local, "real", 3))
        symbols.pop()
        last = symbols.reference("last", 4)
        self.assertTrue(symbols.declare(last, "real", 4))
        self.assertEqual([first.offset, local.offset, last.offset], [0, 0, 4])
