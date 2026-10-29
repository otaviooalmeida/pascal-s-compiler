"""Validação da gramática do TP1 e das palavras reservadas de Pascal-S."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import random
import unittest

import ply.yacc as ply_yacc

import yacc
from fixture_cases import expected_exit


class FrontendAuditTests(unittest.TestCase):
    def compile_source(self, source):
        output, errors = StringIO(), StringIO()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "input.pas"
            path.write_bytes(source.encode("utf-8"))
            with redirect_stdout(output), redirect_stderr(errors):
                result = yacc.compile_file(path)
        return result, output.getvalue(), errors.getvalue()

    def assert_accepts(self, source):
        result, output, errors = self.compile_source(source)
        self.assertTrue(result, errors)
        self.assertEqual(output, "Compilation succeeded.\n")
        self.assertEqual(errors, "")

    def assert_rejects(self, source, diagnostic):
        result, output, errors = self.compile_source(source)
        self.assertFalse(result, source[:200])
        self.assertEqual(output, "")
        self.assertIn(diagnostic, errors)
        self.assertNotIn("Traceback", errors)
        return errors

    def test_integer_literal_has_no_unspecified_python_digit_limit(self):
        # A EBNF não limita a quantidade de dígitos; o front-end não avalia valores.
        self.assert_accepts("program p; begin writeln(" + "9" * 5000 + ") end.")

    def test_all_pascal_fixtures(self):
        for path in sorted(Path(__file__).parent.glob("*.pas")):
            with self.subTest(file=path.name):
                source = path.read_text(encoding="utf-8")
                if expected_exit(path) == 0:
                    self.assert_accepts(source)
                else:
                    self.assert_rejects(source, "error at")

    def test_empty_statements_blocks_and_optional_declarations(self):
        bodies = (
            "", ";", ";;;;", "begin end", "begin ;;; end;", "begin begin end end",
            "writeln(1)", "writeln(1);", "writeln(1);;writeln(2);;",
            "if 1 = 1 then", "if 1 = 1 then else", "while 1 = 2 do",
            "if 1 = 1 then begin end else begin end",
            "if 1 = 1 then if 2 = 2 then writeln(1) else writeln(2)",
            "if 1 = 1 then begin if 2 = 2 then end else writeln(2)",
        )
        for body in bodies:
            with self.subTest(body=body):
                self.assert_accepts(f"program p; begin {body} end.")

    def test_reserved_words_are_case_insensitive(self):
        self.assert_accepts("""PrOgRaM p;
VaR x: InTeGeR; r: ReAl;
BeGiN x := 1; r := 1.0;
  WhIlE x < 3 Do BeGiN x := x + 1 EnD;
  If NoT (x = 1) AnD (x > 0) Or (x = 3)
  ThEn WrItElN(x, r) ElSe WrItElN(0)
EnD.""")

    def test_identifier_boundaries_and_legal_nonreserved_names(self):
        # round continua ID; palavras reservadas com sufixos também são IDs.
        names = "_x, x2, valor_calculado, begin2, integer_value, round, function_value, uses_value"
        self.assert_accepts(f"program p; var {names}: integer; begin "
                            "_x := 1; x2 := _x; round := x2; function_value := round; "
                            "uses_value := function_value; writeln(uses_value) end.")

    def test_extended_reserved_words_cannot_be_identifiers(self):
        words = ("array", "case", "const", "div", "downto", "for", "function", "mod",
                 "of", "procedure", "record", "repeat", "to", "type", "until")
        for word in words:
            for spelling in (word, word.upper()):
                for source in (
                    f"program {spelling}; begin end.",
                    f"program p; var {spelling}: integer; begin end.",
                    f"program p; begin writeln({spelling}) end.",
                ):
                    with self.subTest(word=spelling, source=source):
                        errors = self.assert_rejects(source, "Syntax error")
                        self.assertIn(f"({word.upper()})", errors)
                        self.assertNotIn("undeclared variable", errors)

    def test_identifier_case_policy_is_explicit(self):
        self.assert_rejects("program p; var A, a: integer; begin end.", "duplicate declaration")
        self.assert_accepts("program p; var Count: integer; begin count := 1; writeln(COUNT) end.")

    def test_all_homogeneous_arithmetic_operators(self):
        for var_type, value in (("integer", "8"), ("real", "8.0")):
            for operator in ("+", "-", "*", "/"):
                with self.subTest(type=var_type, operator=operator):
                    self.assert_accepts(f"program p; var x: {var_type}; begin "
                                        f"x := ({value} {operator} {value}); writeln(x) end.")

    def test_all_relational_operators_for_both_numeric_types(self):
        for value in ("2", "2.0"):
            for operator in ("=", "<>", "<", "<=", ">", ">="):
                with self.subTest(value=value, operator=operator):
                    self.assert_accepts(f"program p; begin if {value} {operator} {value} "
                                        "then writeln(1) else writeln(0) end.")

    def test_mixed_types_fail_for_every_numeric_operator_in_both_directions(self):
        for operator in ("+", "-", "*", "/", "=", "<>", "<", "<=", ">", ">="):
            for left, right in (("1", "1.0"), ("1.0", "1")):
                with self.subTest(operator=operator, left=left):
                    self.assert_rejects(f"program p; begin writeln({left} {operator} {right}) end.",
                                        "cannot mix")

    def test_assignment_requires_exact_type_in_both_directions(self):
        for var_type, expression in (("integer", "1.0"), ("real", "1"),
                                     ("integer", "1 < 2"), ("real", "1 < 2")):
            with self.subTest(type=var_type, expression=expression):
                self.assert_rejects(f"program p; var x: {var_type}; begin x := {expression} end.",
                                    "cannot assign")

    def test_boolean_and_arithmetic_operands_are_not_interchangeable(self):
        cases = (
            ("not 1", "not requires a boolean operand"),
            ("1 and 2", "requires boolean operands"),
            ("1 or 2", "requires boolean operands"),
            ("(1 < 2) and 3", "requires boolean operands"),
            ("1.0 or (1 = 1)", "requires boolean operands"),
            ("(1 < 2) + 1", "requires numeric operands"),
            ("1 * (1 < 2)", "requires numeric operands"),
            ("(1 < 2) = 3", "requires numeric operands"),
        )
        for expression, diagnostic in cases:
            with self.subTest(expression=expression):
                self.assert_rejects(f"program p; begin writeln({expression}) end.", diagnostic)

    def test_conditions_require_boolean_expressions(self):
        for statement in ("if 1 then writeln(1)", "while 1.0 do writeln(1)"):
            with self.subTest(statement=statement):
                self.assert_rejects(f"program p; begin {statement} end.", "condition must be boolean")

    def test_grammar_precedence_for_not_and_or_and_relations(self):
        self.assert_accepts("program p; begin "
                            "writeln(not (1 < 2) and (2 = 2) or (3 > 4)); "
                            "writeln(not not (1 = 1)); "
                            "writeln((1 < 2) or (2 < 3) and (3 < 4)) end.")
        # not liga ao fator; and liga mais fortemente que os relacionais.
        self.assert_rejects("program p; begin writeln(not 1 = 2) end.",
                            "not requires a boolean operand")
        self.assert_rejects("program p; begin writeln(1 < 2 and 3 < 4) end.",
                            "requires boolean operands")

    def test_arithmetic_parentheses_and_left_recursive_operator_chains(self):
        self.assert_accepts("program p; var x: integer; begin "
                            "x := 20 - 6 - 2 + 8 / 4 / 2 * 3; "
                            "x := (20 - (6 - 2)) + ((8 / 4) * 3); writeln(x) end.")

    def test_invalid_programs_and_unsupported_constructs(self):
        sources = (
            "", "program p begin end.", "program ; begin end.", "begin end.",
            "program p; var begin end.", "program p; var x integer; begin end.",
            "program p; var x:; begin end.", "program p; var x,: integer; begin end.",
            "program p; begin var x: integer; end.",
            "program p; begin writeln() end.", "program p; begin writeln(1,) end.",
            "program p; begin writeln(,1) end.", "program p; begin writeln(1 2) end.",
            "program p; begin writeln(1; end.", "program p; begin writeln(1) end",
            "program p; begin end;", "program p; begin end. writeln(1)",
            "program p; begin end..", "program p; begin else end.",
            "program p; begin if 1=1 writeln(1) end.",
            "program p; begin while 1=1 writeln(1) end.",
            "program p; begin if 1=1 then writeln(1); else writeln(2) end.",
            "program p; begin writeln(1 < 2 < 3) end.",
            "program p; begin writeln(.5) end.", "program p; begin writeln(5.) end.",
            "program p; begin writeln(1e3) end.", "program p; begin writeln(123abc) end.",
            "program p; begin readln(1) end.",
            "program p; begin writeln(1:2) end.",
            "program p; var writeln: integer; begin end.",
            "program p; var 1x: integer; begin end.",
        )
        for source in sources:
            with self.subTest(source=source):
                self.assert_rejects(source, "error at")

    def test_user_function_returns_declared_integer(self):
        self.assert_accepts("program p; var n: integer; function f(v:integer):integer; "
                            "begin f:=v end; begin n:=f(3); writeln(n, f(2), f(f(2))) end.")

    def test_user_function_checks_argument_count_and_types(self):
        cases = (
            ("f()", "expects 1 argument(s), got 0"),
            ("f(1,2)", "expects 1 argument(s), got 2"),
            ("f(1 < 2)", "expected integer, got boolean"),
            ("f('a')", "expected integer, got char"),
            ("f('abc')", "expected integer, got string"),
        )
        for expression, diagnostic in cases:
            with self.subTest(expression=expression):
                self.assert_rejects("program p; function f(v:integer):integer; begin f:=v end; "
                                    f"begin writeln({expression}) end.", diagnostic)

    def test_function_results_obey_strong_typing(self):
        function = "function f(v:integer):integer; begin f:=v end; "
        self.assert_accepts("program p; var n:integer; " + function + "begin n:=2*f(3); writeln(n) end.")
        self.assert_rejects("program p; var r:real; " + function + "begin r:=f(2) end.",
                            "cannot assign integer to real")
        self.assert_rejects("program p; " + function + "begin writeln(f(2) + 1.0) end.", "cannot mix")

    def test_function_calls_require_a_declared_function_not_a_variable_or_program(self):
        self.assert_rejects("program p; begin writeln(unknown(1.0)) end.",
                            "undeclared function 'unknown'")
        self.assert_rejects("program p; var f: integer; begin f:=1; writeln(f(1.0)) end.",
                            "'f' is not a function")
        self.assert_rejects("program p; begin writeln(p(1.0)) end.", "'p' is not a function")
        self.assert_rejects("program p; begin writeln(round) end.", "undeclared variable 'round'")
        self.assert_rejects("program p; begin round:=1 end.", "undeclared variable 'round'")

    def test_round_can_be_shadowed_without_becoming_reserved(self):
        self.assert_accepts("program p; var round: integer; begin round:=3; writeln(round) end.")
        self.assert_rejects("program p; var round: integer; begin writeln(round(1.0)) end.",
                            "'round' is not a function")
        self.assert_rejects("program p; var round, round: integer; begin end.",
                            "duplicate declaration of 'round'")
        self.assert_accepts("program round; begin writeln(1) end.")
        self.assertEqual(yacc.symbols.lookup("round").lineno, 1)
        self.assert_rejects("program round; begin writeln(round(1.0)) end.",
                            "'round' is not a function")
        # Nem compilação anterior nem uses Math deve introduzir round implicitamente.
        self.assert_rejects("program p; uses Math; begin writeln(round(1.5)) end.",
                            "undeclared function 'round'")
        self.assert_accepts("program p; function round(n:integer):integer; begin round:=n end; "
                            "begin writeln(round(2)) end.")

    def test_malformed_function_calls_recover_and_report_later_errors(self):
        errors = self.assert_rejects("program p; function f(v:real):real; begin f:=v end; "
                                    "begin writeln(f(1.0,)); writeln(1 2); writeln(f(2.5)) end.", "Syntax error")
        self.assertEqual(errors.count("Syntax error"), 2)
        self.assertNotIn("Semantic error", errors)
        self.assert_rejects("program p; begin writeln(round(1.0", "unexpected end of file")

    def test_text_literals_cannot_be_used_as_numbers_or_numeric_variables(self):
        for expression in ("'x' + 1", "1 * 'ab'", "'a' = 1"):
            with self.subTest(expression=expression):
                self.assert_rejects(f"program p; begin writeln({expression}) end.", "requires numeric operands")
        for expression in ("'x'", "'abc'"):
            with self.subTest(expression=expression):
                self.assert_rejects(f"program p; var x: integer; begin x:={expression} end.", "cannot assign")

    def test_writeln_accepts_character_and_string_literals(self):
        self.assert_accepts("program p; begin writeln('texto', 'a', 'it''s', '''', 42) end.")

    def test_undeclared_identifiers_in_all_expression_contexts(self):
        for statement in ("missing := 1", "writeln(missing)", "writeln(1 + missing)",
                          "if missing = 1 then", "while missing = 1 do"):
            with self.subTest(statement=statement):
                self.assert_rejects(f"program p; begin {statement} end.",
                                    "undeclared variable 'missing'")

    def test_program_name_is_not_a_variable(self):
        for body, message in (("p := 1", "not an assignable variable"), ("writeln(p)", "undeclared variable 'p'")):
            with self.subTest(body=body):
                self.assert_rejects(f"program p; begin {body} end.", message)
        self.assert_rejects("program p; var p: integer; begin end.", "duplicate declaration")

    def test_duplicate_declarations_in_group_or_later_group(self):
        for declarations in ("x,x: integer;", "x: integer; x: real;"):
            with self.subTest(declarations=declarations):
                self.assert_rejects(f"program p; var {declarations} begin end.",
                                    "duplicate declaration of 'x'")

    def test_declaration_lookahead_into_first_block(self):
        self.assert_accepts("program p; var x: integer; begin x:=1; begin "
                            "begin x:=x+1 end; writeln(x) end; x:=2 end.")
        symbol = yacc.symbols.lookup("x")
        self.assertEqual((symbol.type, symbol.scope, symbol.offset, symbol.lineno),
                         ("integer", 0, 0, 1))
        self.assertIs(yacc.symbols.current, yacc.symbols.root)

    def test_multiple_adjacent_errors_synchronize_on_semicolon(self):
        source = ("program p; var x: integer; begin\n"
                  "x := ;\nx := ;\nx := ;\nwriteln(x)\nend.")
        errors = self.assert_rejects(source, "Syntax error")
        self.assertEqual(errors.splitlines(), [
            f"Syntax error at {line}:6: unexpected ';' (SEMICOLON)" for line in (2, 3, 4)
        ])
        self.assertIs(yacc.symbols.current, yacc.symbols.root)

    def test_recovery_resumes_and_checks_later_semantics(self):
        errors = self.assert_rejects("program p; var x: integer; begin "
                                    "x := ; writeln(1 2); missing := 1 end.",
                                    "undeclared variable 'missing'")
        self.assertEqual(errors.count("Syntax error"), 2)
        self.assertEqual(errors.count("Semantic error"), 1)

    def test_recovery_in_nested_blocks_preserves_later_lookups(self):
        errors = self.assert_rejects("program p; var x: integer; begin begin "
                                    "writeln(1 2); x:=1; writeln(3 4); end; "
                                    "x:=2; writeln(5 6); writeln(x) end.", "Syntax error")
        self.assertEqual(errors.count("Syntax error"), 3)
        self.assertNotIn("Semantic error", errors)
        self.assertIs(yacc.symbols.current, yacc.symbols.root)

    def test_skipped_tokens_do_not_cause_undeclared_semantic_errors(self):
        errors = self.assert_rejects("program p; begin writeln(1 2 missing); writeln(3 4) end.",
                                    "Syntax error")
        self.assertEqual(errors.count("Syntax error"), 2)
        self.assertNotIn("undeclared", errors)

    def test_eof_positions_with_and_without_newline(self):
        for source, position in (("", "1:1"), ("\n", "2:1"),
                                 ("program p;\nbegin", "2:6"),
                                 ("program p;\nbegin\n", "3:1")):
            with self.subTest(source=source):
                errors = self.assert_rejects(source, "unexpected end of file")
                self.assertIn(f"Syntax error at {position}:", errors)

    def test_eof_during_error_synchronization_terminates(self):
        for tail in ("writeln(1 2", "writeln(1 2);", "begin writeln(1 2); end",
                     "writeln(1 2) {unterminated"):
            with self.subTest(tail=tail):
                self.assert_rejects("program p; begin " + tail, "Syntax error")

    def test_lexical_errors_are_not_hidden_by_an_otherwise_valid_parse(self):
        errors = self.assert_rejects("program p; begin writeln(1) end. @ #", "Lexical error")
        self.assertIn("1:34: illegal character '@'", errors)
        self.assertIn("1:36: illegal character '#'", errors)
        self.assertNotIn("Syntax error", errors)

    def test_lexical_error_positions_after_multiline_comments(self):
        errors = self.assert_rejects("program p;\nbegin\n{ first\nsecond }\n  @ writeln(1)\nend.",
                                    "Lexical error at 5:3: illegal character '@'")
        self.assertNotIn("Syntax error", errors)

    def test_unterminated_comments_report_opening_position(self):
        errors = self.assert_rejects("program p;\nbegin end.\n  { no\nclose\n",
                                    "Lexical error at 3:3: unterminated block comment")
        self.assertEqual(len(errors.splitlines()), 1)

    def test_crlf_and_cr_line_endings_in_real_files(self):
        source = "program p;\nvar x: integer;\nbegin\n x:=1;\n writeln(x)\nend.\n"
        for newline in ("\n", "\r\n", "\r"):
            with self.subTest(newline=repr(newline)):
                self.assert_accepts(source.replace("\n", newline))
                errors = self.assert_rejects(source.replace("x:=1", "x:=1.0").replace("\n", newline),
                                            "Semantic error at 4:2")
                self.assertNotIn("Lexical error", errors)

    def test_semantic_errors_abort_without_scanning_the_rest_of_the_file(self):
        errors = self.assert_rejects("program p; var x: integer; begin x:=1.0;\n"
                                    "writeln(1);\n@ missing:=2\nend.", "cannot assign")
        self.assertEqual(len(errors.splitlines()), 1)
        self.assertNotIn("Lexical", errors)
        self.assertNotIn("undeclared", errors)

    def test_compilations_reset_symbols_lines_errors_and_comment_state(self):
        self.assert_rejects("program p;\nbegin { open", "unterminated block comment")
        self.assert_accepts("program p; var previous: integer; begin previous:=1 end.")
        errors = self.assert_rejects("program p; begin previous:=1 end.",
                                    "Semantic error at 1:18: undeclared variable 'previous'")
        self.assertEqual(len(errors.splitlines()), 1)
        self.assert_accepts("program q; begin writeln(1) end.")

    def test_runtime_execution_is_not_part_of_frontend_validation(self):
        # Divisão por zero e laço infinito não são avaliados por este trabalho.
        self.assert_accepts("program p; begin writeln(1 / 0); while 1=1 do begin end end.")

    def test_long_real_literals_are_recognized_without_float_overflow(self):
        self.assert_accepts("program p; var x: real; begin x := " + "9" * 5000 + ".5 end.")

    def test_large_lists_and_statement_sequences(self):
        names = ",".join(f"x{index}" for index in range(1500))
        statements = ";\n".join("x0 := x0 + 1" for _ in range(2500))
        arguments = ",".join("x0" for _ in range(1500))
        self.assert_accepts(f"program p; var {names}: integer; begin x0:=0;\n"
                            f"{statements}; writeln({arguments}) end.")

    def test_deep_blocks_and_parentheses_use_the_lalr_stack(self):
        self.assert_accepts("program p; begin " + "begin " * 250 +
                            "writeln(" + "(" * 250 + "1" + ")" * 250 + ")" +
                            " end" * 250 + " end.")

    def test_generated_well_typed_programs(self):
        rng = random.Random(202602)

        def expression(var_type, depth):
            if not depth or rng.randrange(3) == 0:
                return rng.choice(("i", "0", "7")) if var_type == "integer" else rng.choice(("r", "0.0", "7.5"))
            left = expression(var_type, depth - 1)
            right = expression(var_type, depth - 1)
            return f"({left} {rng.choice(('+', '-', '*', '/'))} {right})"

        for case in range(60):
            integer = expression("integer", 4)
            real = expression("real", 4)
            with self.subTest(case=case):
                self.assert_accepts(f"program p; var i: integer; r: real; begin i:=0; r:=0.0; "
                                    f"i:={integer}; r:={real}; "
                                    f"if not ({integer} < i) or ({real} >= r) then "
                                    f"begin writeln(i,r) end else while i<10 do i:=i+1 end.")

    def test_seeded_token_mutations_never_crash_and_keep_diagnostics_consistent(self):
        rng = random.Random(1729)
        base = ("program p ; var x , y : integer ; r : real ; begin x := 1 ; "
                "while x < 10 do begin x := x + 1 end ; writeln ( x , r ) end .").split()
        alphabet = base + ["@", "#", "[", "]", "..", "function", "uses", "round", "0.5", "else",
                           "'x'", "'texto'", "'unterminated", "'it''s'"]
        for case in range(400):
            words = base.copy()
            for _ in range(rng.randint(1, 5)):
                position = rng.randrange(len(words))
                operation = rng.randrange(3)
                if operation == 0:
                    del words[position]
                elif operation == 1:
                    words[position] = rng.choice(alphabet)
                else:
                    words.insert(position, rng.choice(alphabet))
            with self.subTest(case=case, source=" ".join(words)):
                result, output, errors = self.compile_source(" ".join(words))
                self.assertIsInstance(result, bool)
                self.assertNotIn("Traceback", errors)
                if result:
                    self.assertEqual(errors, "")
                    self.assertEqual(output, "Compilation succeeded.\n")
                else:
                    self.assertIn("error at", errors)
                    self.assertEqual(output, "")

    def test_lalr_table_has_no_unresolved_conflicts(self):
        warnings, states = StringIO(), StringIO()
        ply_yacc.yacc(module=yacc, start="program", write_tables=False, debug=True,
                      errorlog=ply_yacc.PlyLogger(warnings), debuglog=ply_yacc.PlyLogger(states))
        self.assertNotIn("WARNING", warnings.getvalue())
        self.assertNotIn("conflict", warnings.getvalue().lower())
        self.assertIn("! ELSE", states.getvalue())
        self.assertNotIn("reduce/reduce conflict", states.getvalue())


if __name__ == "__main__":
    unittest.main()
