"""Testes de caixa-preta da CLI: códigos de saída, diagnósticos e falhas de leitura."""

from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parent.parent


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run([sys.executable, str(ROOT / "yacc.py"), *map(str, arguments)],
                              capture_output=True, text=True, timeout=5, cwd=ROOT)

    def test_invalid_utf8_is_reported_without_traceback(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.pas"
            path.write_bytes(b"program p; begin \xff end.")
            result = self.run_cli(path)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Cannot read source:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("Symbol table for:", result.stdout)

    def test_valid_file_returns_zero_and_does_not_execute_writeln(self):
        result = self.run_cli(ROOT / "tests/01-success.pas")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.startswith("Compilation succeeded.\nSymbol table for:"))
        self.assertIn("scope\tname\tkind\ttype\toffset\tline\tdeclared\n", result.stdout)
        self.assertEqual(result.stdout.count("global\tcont\tvariable\tinteger\t"), 6)
        self.assertEqual(result.stderr, "")

    def test_lexical_syntax_semantic_and_unsupported_inputs_return_one(self):
        for filename, diagnostic in (
            ("02-lexical-error.pas", "Lexical error at 5:16"),
            ("03-type-error.pas", "Semantic error at 8:5"),
            ("04-syntax-recovery.pas", "Syntax error"),
            ("20-undeclared-round-call.pas", "undeclared function 'round'"),
            ("30-invalid-parameter-type.pas", "expected integer, got string"),
            ("31-invalid-parameter-arity.pas", "expects 1 argument(s), got 2"),
            ("29-unterminated-string.pas", "unterminated string literal"),
            ("32-empty-string.pas", "empty string literal"),
            ("23-invalid-matrix-indexing.pas", "cannot index non-array"),
        ):
            with self.subTest(filename=filename):
                result = self.run_cli(ROOT / "tests" / filename)
                self.assertEqual(result.returncode, 1)
                self.assertIn("Symbol table for:", result.stdout)
                self.assertIn(diagnostic, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_functions_matrices_and_text_compile_without_execution(self):
        for filename in ("18-function-definition.pas", "19-procedure-definition.pas",
                         "21-vector-declaration.pas", "22-matrix-declaration.pas", "28-text-literals.pas"):
            with self.subTest(filename=filename):
                result = self.run_cli(ROOT / "tests" / filename)
                self.assertEqual(result.returncode, 0)
                self.assertTrue(result.stdout.startswith("Compilation succeeded.\nSymbol table for:"))
                self.assertEqual(result.stderr, "")

    def test_missing_or_extra_arguments_return_two(self):
        for arguments in ((), ("one.pas", "two.pas")):
            with self.subTest(arguments=arguments):
                result = self.run_cli(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("Usage:", result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("Traceback", result.stderr)

    def test_missing_file_or_directory_return_two(self):
        with TemporaryDirectory() as directory:
            for path in (Path(directory) / "absent.pas", Path(directory)):
                with self.subTest(path=path.name):
                    result = self.run_cli(path)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("Cannot read source:", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertIn("Symbol table for:", result.stdout)

    def test_saved_fixture_logs_match_the_current_cli(self):
        for source in sorted((ROOT / "tests").glob("*.pas")):
            with self.subTest(source=source.name):
                result = self.run_cli(source)
                relative = source.relative_to(ROOT)
                output = result.stdout.split("Symbol table for:", 1)[0] + result.stderr
                expected = (f"$ .venv/bin/python yacc.py {relative}\n"
                            f"{output}[exit code: {result.returncode}]\n")
                saved = ROOT / "tests/output" / f"{source.stem}.log"
                self.assertEqual(saved.read_text(encoding="utf-8").split("Symbol table for:", 1)[0], expected)

    def test_paths_with_spaces_and_unicode(self):
        with TemporaryDirectory(prefix="fonte pascal ") as directory:
            path = Path(directory) / "funções e matrizes.pas"
            path.write_text("program p; begin writeln(1) end.", encoding="utf-8")
            result = self.run_cli(path)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertIn("Symbol table for:", result.stdout)

    def test_embedded_zero_byte_is_a_lexical_error_not_a_crash(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "zero.pas"
            path.write_bytes(b"program p; begin \x00 writeln(1) end.")
            result = self.run_cli(path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("illegal character '\\x00'", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("Symbol table for:", result.stdout)


if __name__ == "__main__":
    unittest.main()
