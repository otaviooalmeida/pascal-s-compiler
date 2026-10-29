"""Contratos públicos do lexer sob demanda e da tabela de símbolos."""

from contextlib import redirect_stderr
from io import StringIO
import unittest

from lex import PascalLexer
from symbol_table import Symbol, SymbolTable


class ReadlineOnlySource:
    """Fonte que detecta leitura em lote e permite observar o avanço do buffer."""

    def __init__(self, text):
        self.stream = StringIO(text)
        self.lines_read = 0

    def read(self, *args):
        raise AssertionError("O scanner não pode ler o arquivo inteiro")

    def readline(self):
        self.lines_read += 1
        return self.stream.readline()


class LexerTests(unittest.TestCase):
    def scan(self, source, symbols=None):
        scanner = PascalLexer(StringIO(source), symbols or SymbolTable())
        errors = StringIO()
        with redirect_stderr(errors):
            tokens = list(iter(scanner.token, None))
        return scanner, tokens, errors.getvalue()

    def test_all_reserved_words_and_their_mixed_case_spellings(self):
        # key[1..27] de samiam95124/Pascal-S, mais os três tokens do TP1.
        words = ("and", "array", "begin", "case", "const", "div", "do", "downto",
                 "else", "end", "for", "function", "if", "mod", "not", "of", "or",
                 "procedure", "program", "record", "repeat", "then", "to", "type",
                 "until", "var", "while", "integer", "real", "writeln", "step", "uses")
        for spelling in (str.lower, str.upper, str.title):
            with self.subTest(spelling=spelling.__name__):
                source = " ".join(spelling(word) for word in words)
                scanner, tokens, errors = self.scan(source)
                self.assertEqual([token.type for token in tokens], [word.upper() for word in words])
                self.assertEqual(scanner.symbols.root.symbols, {})
                self.assertEqual(errors, "")

    def test_every_punctuation_operator_and_longest_match(self):
        source = ":= : ; , . ( ) + - * / = <> < <= > >= :== <=> <>="
        _, tokens, errors = self.scan(source)
        self.assertEqual([token.type for token in tokens], [
            "ASSIGN", "COLON", "SEMICOLON", "COMMA", "DOT", "LPAREN", "RPAREN",
            "PLUS", "MINUS", "TIMES", "DIVIDE", "EQ", "NE", "LT", "LE", "GT", "GE",
            "ASSIGN", "EQ", "LE", "GT", "NE", "EQ",
        ])
        self.assertEqual(errors, "")

    def test_array_delimiters_and_ranges_do_not_consume_real_decimal_points(self):
        scanner, tokens, errors = self.scan("a[1..10,2..3] 1.5..2.5 ... . ..")
        self.assertEqual([(token.type, token.value if token.type != "ID" else token.value.name)
                          for token in tokens], [
            ("ID", "a"), ("LBRACKET", "["), ("NUM_INT", "1"), ("RANGE", ".."),
            ("NUM_INT", "10"), ("COMMA", ","), ("NUM_INT", "2"), ("RANGE", ".."),
            ("NUM_INT", "3"), ("RBRACKET", "]"), ("NUM_REAL", "1.5"), ("RANGE", ".."),
            ("NUM_REAL", "2.5"), ("RANGE", ".."), ("DOT", "."), ("DOT", "."), ("RANGE", ".."),
        ])
        self.assertEqual(scanner.errors, 0)
        self.assertEqual(errors, "")

    def test_literal_kinds_and_lexemes_without_host_numeric_conversion(self):
        _, tokens, errors = self.scan("0 001 9999 3.1415 0.5 120.0")
        self.assertEqual([(token.type, token.value) for token in tokens], [
            ("NUM_INT", "0"), ("NUM_INT", "001"), ("NUM_INT", "9999"),
            ("NUM_REAL", "3.1415"), ("NUM_REAL", "0.5"), ("NUM_REAL", "120.0"),
        ])
        self.assertEqual(errors, "")

    def test_invalid_real_forms_are_not_single_real_tokens(self):
        _, tokens, errors = self.scan(".5 5. 1e3 1..2")
        self.assertEqual([token.type for token in tokens], [
            "DOT", "NUM_INT", "NUM_INT", "DOT", "NUM_INT", "ID",
            "NUM_INT", "RANGE", "NUM_INT",
        ])
        self.assertEqual(errors, "")

    def test_quoted_literals_decode_doubled_apostrophes(self):
        cases = (
            ("'a'", "CHAR_LITERAL", "a"),
            ("'texto'", "STRING_LITERAL", "texto"),
            ("'it''s'", "STRING_LITERAL", "it's"),
            ("''''", "CHAR_LITERAL", "'"),
            ("'a'''", "STRING_LITERAL", "a'"),
            ("'''abc'''", "STRING_LITERAL", "'abc'"),
            ("'\\n'", "STRING_LITERAL", "\\n"),
            ("'ação'", "STRING_LITERAL", "ação"),
            ("'ç'", "CHAR_LITERAL", "ç"),
        )
        for source, token_type, value in cases:
            with self.subTest(source=source):
                scanner, tokens, errors = self.scan(source)
                self.assertEqual([(token.type, token.value) for token in tokens], [(token_type, value)])
                self.assertEqual(scanner.errors, 0)
                self.assertEqual(errors, "")

    def test_unterminated_literals_report_the_opening_quote_and_resume_next_line(self):
        for literal in ("'", "'''", "'abc", "'abc''"):
            for suffix in ("", "\nnext_name"):
                with self.subTest(literal=literal, suffix=suffix):
                    scanner, tokens, errors = self.scan("  " + literal + suffix)
                    self.assertEqual(scanner.errors, 1)
                    self.assertEqual(errors, "Lexical error at 1:3: unterminated string literal\n")
                    self.assertEqual([token.value.name for token in tokens],
                                     ["next_name"] if suffix else [])
                    if suffix:
                        self.assertEqual((tokens[0].lineno, tokens[0].column), (2, 1))

    def test_empty_literal_is_rejected_like_the_pascal_s_reference(self):
        scanner, tokens, errors = self.scan("  ''")
        self.assertEqual(tokens, [])
        self.assertEqual(scanner.errors, 1)
        self.assertEqual(errors, "Lexical error at 1:3: empty string literal\n")

    def test_comment_markers_and_keywords_inside_literals_are_plain_text(self):
        scanner, tokens, errors = self.scan("'begin end { // @ } [1..2]'\n  'x'")
        self.assertEqual([(token.type, token.value, token.lineno, token.column) for token in tokens],
                         [("STRING_LITERAL", "begin end { // @ } [1..2]", 1, 1),
                          ("CHAR_LITERAL", "x", 2, 3)])
        self.assertIs(scanner.symbols.current, scanner.symbols.root)
        self.assertEqual(scanner.symbols.root.symbols, {})
        self.assertEqual(errors, "")

    def test_quote_runs_have_unambiguous_escaped_quote_boundaries(self):
        for length in range(1, 17):
            with self.subTest(length=length):
                scanner, tokens, errors = self.scan("'" * length)
                if length == 2 or length % 2:
                    self.assertEqual(scanner.errors, 1)
                    self.assertEqual(tokens, [])
                    self.assertIn("string literal", errors)
                else:
                    self.assertEqual(scanner.errors, 0)
                    self.assertEqual(len(tokens), 1)
                    self.assertEqual(tokens[0].value, "'" * (length // 2 - 1))

    def test_literals_are_lazy_and_large_literals_do_not_split(self):
        source = ReadlineOnlySource("'primeira'\n'" + "a" * 20000 + "'\n")
        scanner = PascalLexer(source, SymbolTable())
        self.assertEqual(scanner.token().value, "primeira")
        self.assertEqual(source.lines_read, 1)
        token = scanner.token()
        self.assertEqual((token.type, len(token.value), token.lineno), ("STRING_LITERAL", 20000, 2))
        self.assertEqual(source.lines_read, 2)
        self.assertEqual(scanner.errors, 0)

    def test_identifier_pattern_and_reserved_prefix_boundaries(self):
        names = ["_", "_x", "x2", "valor_calculado", "programa", "begin2", "and_", "integer_value",
                 "array2", "case_value", "const2", "div2", "downto2", "for2", "function_value",
                 "mod2", "of2", "procedure_value", "record_type", "repeat2", "to2", "type2", "until2", "step2", "uses_value"]
        _, tokens, errors = self.scan(" ".join(names))
        self.assertEqual([token.type for token in tokens], ["ID"] * len(names))
        self.assertEqual([token.value.name for token in tokens], names)
        self.assertTrue(all(isinstance(token.value, Symbol) for token in tokens))
        self.assertEqual(errors, "")

    def test_predefined_names_and_library_names_are_not_reserved_words(self):
        # enter(...) do Pascal-S cadastra estes nomes como IDs, não em key[1..27].
        names = ["round", "trunc", "abs", "sqr", "sqrt", "sin", "cos", "boolean", "char",
                 "true", "false", "read", "readln", "write", "crt", "graph", "Math", "System"]
        _, tokens, errors = self.scan(" ".join(names))
        self.assertEqual([token.type for token in tokens], ["ID"] * len(names))
        self.assertEqual([token.value.name for token in tokens], names)
        self.assertEqual(errors, "")

    def test_ids_point_to_shared_records_without_declaring_them(self):
        symbols = SymbolTable()
        _, tokens, errors = self.scan("total total", symbols)
        self.assertIs(tokens[0].value, tokens[1].value)
        self.assertIs(tokens[0].value, symbols.lookup("total"))
        self.assertFalse(tokens[0].value.declared)
        self.assertIsNone(tokens[0].value.type)
        self.assertEqual(errors, "")

    def test_declared_records_are_reused_in_nested_blocks(self):
        symbols = SymbolTable()
        original = symbols.reference("total", 1)
        symbols.declare(original, "integer", 1)
        _, tokens, errors = self.scan("begin total begin total end total end", symbols)
        self.assertTrue(all(token.value is original for token in tokens if token.type == "ID"))
        self.assertIs(symbols.current, symbols.root)
        self.assertEqual(errors, "")

    def test_scope_entry_exit_and_parent_lookup_follow_source_tokens(self):
        symbols = SymbolTable()
        parent = symbols.reference("outer", 1)
        symbols.declare(parent, "real", 1)
        scanner = PascalLexer(StringIO("begin outer begin inner end outer end"), symbols)
        self.assertEqual(scanner.token().type, "BEGIN")
        child = symbols.current
        self.assertIs(child.parent, symbols.root)
        self.assertIs(scanner.token().value, parent)
        self.assertEqual(scanner.token().type, "BEGIN")
        grandchild = symbols.current
        self.assertIs(grandchild.parent, child)
        local = scanner.token().value
        self.assertEqual(local.scope, grandchild.number)
        self.assertEqual(scanner.token().type, "END")
        self.assertIs(symbols.current, child)
        self.assertIsNone(symbols.lookup("inner"))
        self.assertIs(scanner.token().value, parent)
        self.assertEqual(scanner.token().type, "END")
        self.assertIs(symbols.current, symbols.root)
        self.assertIsNone(scanner.token())

    def test_token_occurrence_position_is_not_the_declaration_position(self):
        symbols = SymbolTable()
        original = symbols.reference("x", 10)
        symbols.declare(original, "integer", 10)
        _, tokens, errors = self.scan("x\n  x", symbols)
        self.assertEqual([(token.lineno, token.column) for token in tokens], [(1, 1), (2, 3)])
        self.assertEqual(original.lineno, 10)
        self.assertIs(tokens[1].value, original)
        self.assertEqual(errors, "")

    def test_multiline_and_line_comments_preserve_positions_and_state(self):
        scanner, tokens, errors = self.scan("// begin fake @\n{ while\nend // @ }\n  value // ignored\n+ 1")
        self.assertEqual([(token.type, token.lineno, token.column) for token in tokens],
                         [("ID", 4, 3), ("PLUS", 5, 1), ("NUM_INT", 5, 3)])
        self.assertIs(scanner.symbols.current, scanner.symbols.root)
        self.assertIsNone(scanner.symbols.lookup("fake"))
        self.assertEqual(errors, "")

    def test_pascal_star_comments_ignore_tokens_and_preserve_physical_lines(self):
        scanner, tokens, errors = self.scan("(* begin ' { @\n // end ***)\n  value (* text *) / 2")
        self.assertEqual([(token.type, token.lineno, token.column) for token in tokens],
                         [("ID", 3, 3), ("DIVIDE", 3, 20), ("NUM_INT", 3, 22)])
        self.assertIs(scanner.symbols.current, scanner.symbols.root)
        self.assertEqual(errors, "")

    def test_unterminated_star_comment_reports_its_opening_once(self):
        scanner, tokens, errors = self.scan("\n  (* unclosed\ntext")
        self.assertEqual(tokens, [])
        self.assertEqual(scanner.errors, 1)
        self.assertEqual(errors, "Lexical error at 2:3: unterminated block comment\n")
        with redirect_stderr(StringIO()) as later:
            self.assertIsNone(scanner.token())
        self.assertEqual(later.getvalue(), "")

    def test_division_is_not_confused_with_comments(self):
        _, tokens, errors = self.scan("8/2 // 100/0\n{ / // } 6/3")
        self.assertEqual([token.type for token in tokens],
                         ["NUM_INT", "DIVIDE", "NUM_INT", "NUM_INT", "DIVIDE", "NUM_INT"])
        self.assertEqual(errors, "")

    def test_comment_boundaries_may_adjoin_tokens(self):
        _, tokens, errors = self.scan("a{}+{comment}b// comment at EOF")
        self.assertEqual([token.type for token in tokens], ["ID", "PLUS", "ID"])
        self.assertEqual(errors, "")

    def test_each_illegal_character_is_reported_and_skipped(self):
        scanner, tokens, errors = self.scan(" \t@ #\n  $x")
        self.assertEqual(scanner.errors, 3)
        self.assertEqual(errors.splitlines(), [
            "Lexical error at 1:3: illegal character '@'",
            "Lexical error at 1:5: illegal character '#'",
            "Lexical error at 2:3: illegal character '$'",
        ])
        self.assertEqual([(token.type, token.column) for token in tokens], [("ID", 4)])

    def test_unterminated_block_comment_is_reported_once(self):
        scanner, tokens, errors = self.scan("\n  { open\nno close")
        self.assertEqual(tokens, [])
        self.assertEqual(scanner.errors, 1)
        self.assertEqual(errors, "Lexical error at 2:3: unterminated block comment\n")
        with redirect_stderr(StringIO()) as later_errors:
            self.assertIsNone(scanner.token())
        self.assertEqual(later_errors.getvalue(), "")

    def test_reading_is_lazy_and_does_not_precompute_tokens(self):
        source = ReadlineOnlySource("first second\nthird\n")
        symbols = SymbolTable()
        scanner = PascalLexer(source, symbols)
        self.assertEqual(source.lines_read, 0)
        self.assertEqual(scanner.token().value.name, "first")
        self.assertEqual(source.lines_read, 1)
        self.assertIsNone(symbols.lookup("second"))
        self.assertEqual(scanner.token().value.name, "second")
        self.assertEqual(source.lines_read, 1)
        self.assertEqual(scanner.token().value.name, "third")
        self.assertEqual(source.lines_read, 2)
        self.assertIsNone(scanner.token())
        self.assertEqual(source.lines_read, 3)

    def test_comment_state_survives_buffer_refills(self):
        source = ReadlineOnlySource("{ open\n" + "still comment\n" * 1000 + "} x\n")
        scanner = PascalLexer(source, SymbolTable())
        token = scanner.token()
        self.assertEqual((token.value.name, token.lineno, token.column), ("x", 1002, 3))
        self.assertEqual(source.lines_read, 1002)
        self.assertEqual(scanner.errors, 0)

    def test_empty_source_and_no_final_newline(self):
        scanner, tokens, errors = self.scan("")
        self.assertEqual(tokens, [])
        self.assertEqual(scanner.position(), (1, 1))
        scanner, tokens, errors = self.scan("\n  123")
        self.assertEqual([(token.lineno, token.column) for token in tokens], [(2, 3)])
        self.assertEqual(scanner.position(), (2, 6))
        self.assertEqual(errors, "")


class SymbolTableTests(unittest.TestCase):
    def test_declaration_completes_the_existing_symbol_record(self):
        symbols = SymbolTable()
        symbol = symbols.reference("x", 1)
        self.assertTrue(symbols.declare(symbol, "integer", 7))
        self.assertIs(symbols.lookup("x"), symbol)
        self.assertEqual((symbol.name, symbol.type, symbol.scope, symbol.offset, symbol.lineno),
                         ("x", "integer", 0, 0, 7))
        self.assertTrue(symbol.declared)

    def test_lookup_searches_parents_but_child_names_do_not_escape(self):
        symbols = SymbolTable()
        outer = symbols.reference("outer", 1)
        symbols.declare(outer, "integer", 1)
        symbols.push()
        local = symbols.reference("local", 2)
        symbols.declare(local, "real", 2)
        symbols.push()
        self.assertIs(symbols.lookup("outer"), outer)
        self.assertIs(symbols.lookup("local"), local)
        symbols.pop()
        symbols.pop()
        self.assertIs(symbols.lookup("outer"), outer)
        self.assertIsNone(symbols.lookup("local"))
        self.assertIsNone(symbols.lookup("unknown"))

    def test_duplicate_declarations_do_not_change_attributes_or_allocate_space(self):
        symbols = SymbolTable()
        first = symbols.reference("x", 1)
        symbols.declare(first, "integer", 1)
        self.assertFalse(symbols.declare(first, "real", 99))
        second = symbols.reference("y", 2)
        symbols.declare(second, "real", 2)
        self.assertEqual((first.type, first.lineno, first.offset, second.offset), ("integer", 1, 0, 4))

    def test_scope_numbers_are_unique_and_root_cannot_be_popped(self):
        symbols = SymbolTable()
        symbols.pop()
        self.assertIs(symbols.current, symbols.root)
        symbols.push()
        first_scope = symbols.current.number
        symbols.pop()
        symbols.push()
        self.assertNotEqual(symbols.current.number, first_scope)
        self.assertIs(symbols.current.parent, symbols.root)

    def test_predefined_function_has_a_shared_signature_without_variable_storage(self):
        symbols = SymbolTable()
        builtin = symbols.declare_builtin("round", (("integer", "real"),), "integer")
        self.assertIs(symbols.reference("round", 10), builtin)
        self.assertIs(symbols.lookup("round"), builtin)
        self.assertEqual((builtin.kind, builtin.type, builtin.parameters),
                         ("function", "integer", (("integer", "real"),)))
        self.assertTrue(builtin.builtin)
        self.assertTrue(builtin.declared)
        self.assertIsNone(builtin.offset)
        self.assertEqual(symbols.root.next_offset, 0)

    def test_variable_declaration_can_shadow_a_predefined_function_once(self):
        symbols = SymbolTable()
        builtin = symbols.declare_builtin("round", (("integer", "real"),), "integer")
        self.assertTrue(symbols.declare(builtin, "real", 3))
        self.assertEqual((builtin.kind, builtin.type, builtin.lineno, builtin.offset), ("variable", "real", 3, 0))
        self.assertFalse(builtin.builtin)
        self.assertIsNone(builtin.parameters)
        self.assertFalse(symbols.declare(builtin, "integer", 4))
        self.assertEqual(symbols.root.next_offset, 8)

    def test_program_identifier_is_distinguished_from_variables(self):
        symbols = SymbolTable()
        program = symbols.reference("p", 1)
        symbols.define(program, "program", None, program.lineno)
        self.assertIs(symbols.reference("p", 2), program)
        self.assertTrue(program.declared)
        self.assertEqual(program.kind, "program")
        self.assertIsNone(program.type)
        self.assertIsNone(program.offset)


if __name__ == "__main__":
    unittest.main()
