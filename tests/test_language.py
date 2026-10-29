"""Cenários da linguagem ampliada, observados pela compilação de arquivos reais."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import random
from tempfile import TemporaryDirectory
import unittest

import yacc


class ExtendedLanguageTests(unittest.TestCase):
    def compile_source(self, source):
        output, errors = StringIO(), StringIO()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "program.pas"
            path.write_text(source, encoding="utf-8")
            with redirect_stdout(output), redirect_stderr(errors):
                accepted = yacc.compile_file(path)
        return accepted, output.getvalue(), errors.getvalue()

    def assert_accepts(self, source):
        accepted, output, errors = self.compile_source(source)
        self.assertTrue(accepted, errors)
        self.assertEqual(output, "Compilation succeeded.\n")
        self.assertEqual(errors, "")

    def assert_rejects(self, source, message):
        accepted, output, errors = self.compile_source(source)
        self.assertFalse(accepted, source)
        self.assertEqual(output, "")
        self.assertIn(message, errors)
        self.assertNotIn("Traceback", errors)
        return errors

    def test_round_is_an_ordinary_undeclared_function(self):
        self.assert_rejects("program p; var w: real; begin w:=1.0; w:=w/round(w) end.",
                            "undeclared function 'round'")

    def test_recursive_fibonacci_and_value_parameters(self):
        self.assert_accepts("""program Fibonacci;
function Fib(n: integer): integer;
begin
  if n <= 1 then Fib := n
  else Fib := Fib(n-1) + Fib(n-2)
end;
begin writeln(Fib(10)) end.""")

    def test_value_parameters_enforce_exact_declared_types(self):
        header = "program p; function f(n: integer): integer; begin f:=n end; begin "
        self.assert_accepts(header + "writeln(f(42)) end.")
        for argument, actual in (("1.0", "real"), ("'texto'", "string"), ("'x'", "char"), ("true", "boolean")):
            with self.subTest(argument=argument):
                self.assert_rejects(header + f"writeln(f({argument})) end.", f"expected integer, got {actual}")
        for call, count in (("f()", 0), ("f", 0), ("f(1,2)", 2)):
            with self.subTest(call=call):
                self.assert_rejects(header + f"writeln({call}) end.", f"expects 1 argument(s), got {count}")

    def test_var_parameters_require_variables_not_literals_or_expressions(self):
        prefix = "program p; var x: integer; procedure inc(var n: integer); begin n:=n+1 end; begin "
        self.assert_accepts(prefix + "x:=0; inc(x); writeln(x) end.")
        for argument in ("1", "x+1", "(x)"):
            with self.subTest(argument=argument):
                self.assert_rejects(prefix + f"inc({argument}) end.", "var parameter and requires a variable")

    def test_procedures_can_be_called_without_parentheses_but_not_without_required_arguments(self):
        self.assert_accepts("program p; procedure ping; begin end; begin ping; ping() end.")
        self.assert_rejects("program p; procedure ping(n: integer); begin end; begin ping end.",
                            "procedure 'ping' expects 1 argument(s), got 0")
        self.assert_rejects("program p; procedure ping; begin end; begin writeln(ping()) end.", "is not a function")

    def test_nested_functions_shadow_parameters_without_leaking_them(self):
        self.assert_accepts("""program p;
var n: real;
function outer(n: integer): integer;
  function inner(k: integer): integer;
  begin inner:=n+k end;
begin outer:=inner(n) end;
begin n:=1.5; writeln(outer(2), n) end.""")
        self.assert_rejects("program p; function f(n: integer): integer; begin f:=n end; begin n:=1 end.",
                            "undeclared variable 'n'")

    def test_identifiers_follow_pascal_case_insensitivity(self):
        self.assert_accepts("program p; var Count: integer; begin COUNT:=1; writeln(count) end.")
        self.assert_rejects("program p; var A, a: integer; begin end.", "duplicate declaration")

    def test_matrix_is_a_structural_type_and_elements_have_the_declared_type(self):
        self.assert_accepts("""program ProdutoMatrizes;
const N = 2;
type Matriz = array[1..N,1..N] of integer;
var a,b,c: Matriz; i,j,k: integer;
procedure produto(var result: Matriz; left,right: Matriz);
var i,j,k: integer;
begin
  result[1,1]:=left[1,1]*right[1,1]+left[1,2]*right[2,1];
  result[2,2]:=left[2,1]*right[1,2]+left[2,2]*right[2,2]
end;
begin produto(c,a,b); writeln(c[1,1]) end.""")

    def test_for_to_downto_step_and_repeat_until(self):
        self.assert_accepts("""program Loops;
var i,total: integer;
begin
  total:=0;
  for i:=1 to 10 step 2 do total:=total+i;
  for i:=10 downto 1 do total:=total+i;
  for i:=10 to 1 step -1 do total:=total+i;
  repeat total:=total-1; i:=i+1 until (total=0) or (i>100);
  repeat until true;
  writeln(total)
end.""")

    def test_boolean_constants_are_typed_and_cannot_be_assigned_to_integer(self):
        self.assert_accepts("program p; var b:boolean; begin b:=true; if not b then b:=false end.")
        self.assert_rejects("program p; var x:integer; begin x:=true end.", "cannot assign boolean to integer")

    def test_div_and_mod_require_integer_operands(self):
        self.assert_accepts("program p; var x:integer; begin x:=10 div 3 + 10 mod 3 end.")
        for operator in ("div", "mod"):
            with self.subTest(operator=operator):
                self.assert_rejects(f"program p; begin writeln(2.0 {operator} 1.0) end.",
                                    "requires integer operands")

    def test_library_names_are_identifiers_and_common_library_procedures_are_typed(self):
        self.assert_accepts(r"""program OndaSemRound;
uses crt, graph;
var c,d,t:integer; w:real;
begin
  clrscr;
  write('W: '); read(w);
  initgraph(c,d,'c:\\bgi');
  for t:=0 to 10 step 2 do line(t,0,t,10);
  w:=sin(w);
  repeat until keypressed;
  closegraph
end.""")
        self.assert_rejects("program p; uses math; var w:real; begin w:=1.0; w:=w/round(w) end.",
                            "undeclared function 'round'")
        self.assert_rejects("program p; uses graph; begin line('texto',0,1,2) end.",
                            "expected integer, got string")

    def test_vectors_submatrices_aliases_and_array_value_assignments(self):
        self.assert_accepts("""program p;
type TVec=array[-1..1] of integer; TMat=array[1..2] of TVec;
var a:TMat; rowvalue:TVec;
procedure init(var row:TVec); begin row[-1]:=1; row[0]:=2; row[1]:=3 end;
begin init(a[1]); a[2][-1]:=a[1,-1]; rowvalue:=a[1]; a[2]:=rowvalue end.""")

    def test_array_parameters_require_matching_dimensions_bounds_and_elements(self):
        for actual_type in ("integer", "real", "array[0..2] of integer", "array[1..3] of real",
                            "array[1..3,1..2] of integer"):
            with self.subTest(actual_type=actual_type):
                errors = self.assert_rejects(f"program p; type TVec=array[1..3] of integer; var x:{actual_type}; "
                                             "procedure use(v:TVec); begin end; begin use(x) end.", "expected array")
                if actual_type == "array[0..2] of integer":
                    self.assertIn("1..3", errors)
                    self.assertIn("0..2", errors)
        self.assert_rejects("program p; type TVec=array[1..3] of integer; "
                            "procedure use(v:TVec); begin end; begin use('texto') end.", "expected array")

    def test_array_indices_and_bounds_are_checked(self):
        prefix = "program p; var a:array[1..2,1..3] of integer; begin "
        for statement, message in (
            ("a[1.0,1]:=0", "array index must be integer"),
            ("a[true,1]:=0", "array index must be integer"),
            ("a['x',1]:=0", "array index must be integer"),
            ("a[0,1]:=0", "out of bounds"),
            ("a[1,4]:=0", "out of bounds"),
            ("a[1,1,1]:=0", "too many array indices"),
            ("a[1]:=0", "cannot assign integer to array"),
            ("a[]:=0", "Syntax error"),
            ("a[1,1]:=true", "cannot assign boolean to integer"),
        ):
            with self.subTest(statement=statement):
                self.assert_rejects(prefix + statement + " end.", message)
        self.assert_rejects("program p; var x:integer; begin x[1]:=0 end.", "cannot index non-array")
        self.assert_rejects("program p; begin a[1]:=0 end.", "undeclared variable 'a'")
        for bounds, message in (("3..1", "lower bound exceeds upper"),
                                ("1.0..3.0", "bounds must be integer constants"),
                                ("true..false", "bounds must be integer constants")):
            with self.subTest(bounds=bounds):
                self.assert_rejects(f"program p; var a:array[{bounds}] of integer; begin end.", message)
        self.assert_rejects("program p; var n:integer; a:array[1..n] of integer; begin end.",
                            "bounds must be integer constants")
        self.assert_accepts("program p; const N=2*3; type TV=array[0..N-1] of real; "
                            "var a:TV; begin a[5]:=1.0 end.")
        errors = self.assert_rejects("program p; var a:array[1.." + "9" * 5000 + "] of integer; "
                                    "procedure use(v:array[1..2] of integer); begin end; begin use(a) end.",
                                    "expected array[1..2]")
        self.assertIn("<large integer>", errors)

    def test_for_headers_and_repeat_conditions_enforce_types(self):
        for declaration, loop, message in (
            ("i:real", "for i:=0 to 2 do", "variable and limits must be integer"),
            ("i:integer", "for i:=0.0 to 2 do", "variable and limits must be integer"),
            ("i:integer", "for i:=0 to true do", "variable and limits must be integer"),
            ("i:integer", "for i:=0 to 2 step 0.5 do", "step must be integer"),
            ("i:integer", "for i:=0 to 2 step 0 do", "step cannot be zero"),
            ("i:integer", "for i:=0 to 2 step 2-2 do", "step cannot be zero"),
            ("i:integer", "repeat until 1", "until condition must be boolean"),
        ):
            with self.subTest(loop=loop):
                self.assert_rejects(f"program p; var {declaration}; begin {loop} end.", message)
        self.assert_rejects("program p; begin for i:=0 to 2 do begin end end.", "undeclared variable 'i'")

    def test_missing_semicolons_and_loop_delimiters_are_rejected(self):
        sources = (
            "program p; var x:integer begin end.",
            "program p; function f(n:integer):integer begin f:=n end; begin end.",
            "program p; procedure ping; begin end begin ping end.",
            "program p; procedure ping; begin end; begin ping ping end.",
            "program p; var i:integer; begin i:=1 i:=2 end.",
            "program p; var i:integer; begin for i:=1 to 3 i:=i+1 end.",
            "program p; var i:integer; begin for i:=1 3 do i:=i+1 end.",
            "program p; begin repeat writeln(1) until end.",
            "program p; begin repeat writeln(1) true end.",
        )
        for source in sources:
            with self.subTest(source=source):
                self.assert_rejects(source, "Syntax error")

    def test_io_requires_declared_writable_arguments_and_scalars(self):
        self.assert_accepts("program p; var x:integer; s:string; begin read(x,s); readln; readln(); "
                            "write(x,s,true); writeln(x) end.")
        for statement, message in (("read(1)", "requires variable arguments"),
                                   ("read(true)", "requires variable arguments"),
                                   ("read()", "requires arguments"), ("write()", "requires arguments"),
                                   ("read(missing)", "undeclared variable 'missing'")):
            with self.subTest(statement=statement):
                self.assert_rejects(f"program p; begin {statement} end.", message)
        self.assert_rejects("program p; var a:array[1..2] of integer; begin writeln(a) end.",
                            "requires scalar arguments")

    def test_function_results_and_parameter_declarations_are_checked(self):
        self.assert_rejects("program p; function f(n:integer):integer; begin f:='texto' end; begin end.",
                            "cannot assign string to integer")
        self.assert_rejects("program p; function f(n,n:integer):integer; begin f:=1 end; begin end.",
                            "duplicate declaration")
        self.assert_rejects("program p; function f(n:integer;n:real):integer; begin f:=1 end; begin end.",
                            "duplicate declaration")
        self.assert_rejects("program p; function f(n:integer); begin end; begin end.", "invalid return type")
        self.assert_accepts("program p; function zero:integer; begin zero:=0 end; begin writeln(zero,zero()) end.")
        self.assert_rejects("program p; function zero:integer; begin zero:=0 end; begin zero end.",
                            "is not a procedure")

    def test_local_declarations_do_not_leak_and_predefined_signatures_can_be_shadowed(self):
        self.assert_rejects("program p; procedure p1; var local:integer; begin local:=1 end; "
                            "begin local:=1 end.", "undeclared variable 'local'")
        self.assert_accepts("program p; function write(n:integer):integer; begin write:=n end; "
                            "begin writeln(write(1)) end.")
        self.assert_accepts("program p; function outer:integer; "
                            "procedure setresult; begin outer:=1 end; begin setresult end; "
                            "begin writeln(outer) end.")
        self.assert_rejects("program p; function f:integer; begin f:=1 end; begin f:=2 end.",
                            "not an assignable variable")

    def test_lexical_and_syntax_recovery_reach_a_later_undeclared_assignment(self):
        errors = self.assert_rejects("program p;\nvar x:integer;\nbegin\n  writeln('open);\n"
                                    "  x:=;\n  writeln(1 2);\n  missing:=1\nend.",
                                    "undeclared variable 'missing'")
        self.assertIn("Lexical error at 4:11: unterminated string literal", errors)
        self.assertGreaterEqual(errors.count("Syntax error"), 2)

    def test_library_parameters_and_unknown_library_functions_are_not_silently_accepted(self):
        self.assert_rejects("program p; uses graph; begin initgraph(0,0,'path') end.", "var parameter")
        self.assert_rejects("program p; uses crt; begin clrscr(1) end.", "expects 0 argument(s), got 1")
        self.assert_rejects("program p; uses unknown_library; begin mystery end.", "undeclared procedure")
        self.assert_accepts("program p; uses Math; begin writeln(sin(1.0)) end.")
        self.assert_rejects("program p; uses CRT,GRAPH,Math; begin writeln(ROUND(1.0)) end.",
                            "undeclared function")

    def test_array_function_results_keep_element_types_and_reference_rules(self):
        self.assert_accepts("""program p;
type TVec=array[1..2] of integer;
var data:TVec;
function make(seed:integer):TVec;
begin make[1]:=seed; make[2]:=make[1]+1 end;
begin data:=make(2); writeln(data[2], make(2)[1]) end.""")
        self.assert_rejects("program p; type TVec=array[1..2] of integer; var data:TVec; "
                            "function make:TVec; begin make:=data end; "
                            "procedure change(var a:TVec); begin end; begin change(make()) end.", "var parameter")

    def test_basic_parameter_type_cross_product_by_value_and_reference(self):
        arguments = {"integer": "1", "real": "1.0", "boolean": "true", "char": "'x'", "string": "'texto'"}
        declarations = "; ".join(f"v_{kind}:{kind}" for kind in arguments)
        for expected in arguments:
            for actual, literal in arguments.items():
                for by_ref in (False, True):
                    mode = "var " if by_ref else ""
                    argument = f"v_{actual}" if by_ref else literal
                    source = (f"program p; var {declarations}; function f({mode}n:{expected}):integer; "
                              f"begin f:=0 end; begin writeln(f({argument})) end.")
                    with self.subTest(expected=expected, actual=actual, by_ref=by_ref):
                        if expected == actual:
                            self.assert_accepts(source)
                        else:
                            self.assert_rejects(source, f"expected {expected}, got {actual}")
            source = (f"program p; function f(var n:{expected}):integer; begin f:=0 end; "
                      f"begin writeln(f({arguments[expected]})) end.")
            with self.subTest(expected=expected, literal_to_reference=True):
                self.assert_rejects(source, "var parameter and requires a variable")

    def test_bare_procedure_in_an_expression_is_identified_as_a_procedure(self):
        self.assert_rejects("program p; procedure ping; begin end; begin writeln(ping) end.",
                            "procedure 'ping' cannot be used as an expression")

    def test_generated_matrix_shapes_preserve_scalar_and_parameter_types(self):
        for rows in range(1, 6):
            for columns in range(1, 5):
                for element, literal in (("integer", "1"), ("real", "1.0")):
                    with self.subTest(rows=rows, columns=columns, element=element):
                        self.assert_accepts(f"program p; type TMat=array[1..{rows},1..{columns}] of {element}; "
                                            f"var data:TMat; function first(m:TMat):{element}; "
                                            "begin first:=m[1,1] end; procedure init(var m:TMat); "
                                            f"begin m[1,1]:={literal} end; begin init(data); writeln(first(data)) end.")

    def test_seeded_mutations_of_complete_program_never_crash(self):
        rng = random.Random(8264)
        source = (Path(__file__).parent / "teste_completo.pas").read_text(encoding="utf-8")
        base = source.replace(";", " ; ").replace("(", " ( ").replace(")", " ) ").split()
        alphabet = ["function", "procedure", "var", "for", "to", "step", "do", "repeat", "until",
                    "[", "]", "..", "'bad", "true", "1.5", ":=", "integer", ";"]
        for case in range(200):
            words = base.copy()
            for _ in range(rng.randint(1, 8)):
                position = rng.randrange(len(words))
                operation = rng.randrange(3)
                if operation == 0:
                    words.pop(position)
                elif operation == 1:
                    words[position] = rng.choice(alphabet)
                else:
                    words.insert(position, rng.choice(alphabet))
            with self.subTest(case=case):
                accepted, output, errors = self.compile_source(" ".join(words))
                self.assertIsInstance(accepted, bool)
                self.assertIs(yacc.symbols.current, yacc.symbols.root)
                self.assertNotIn("Traceback", errors)
                if accepted:
                    self.assertEqual(errors, "")
                    self.assertEqual(output, "Compilation succeeded.\n")
                else:
                    self.assertIn("error at", errors)
                    self.assertEqual(output, "")

    def test_classic_program_heading_with_input_and_output(self):
        self.assert_accepts("program p(input,output); begin writeln(1) end.")
        self.assert_rejects("program p(input output); begin end.", "Syntax error")
        self.assert_rejects("program p(); begin end.", "Syntax error")

    def test_library_catalog_does_not_turn_user_declarations_into_builtins(self):
        self.assert_rejects("program line; uses graph; var line:integer; begin end.",
                            "conflicts with declared identifier")
        self.assert_accepts("program p; uses graph; begin line(0,0,1,1) end.")


if __name__ == "__main__":
    unittest.main()
