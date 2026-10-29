"""Resultados esperados das entradas; independentes da implementação do compilador."""

SUCCESS_CASES = {
    "01-success.pas", "05-lexer-scopes-logic.pas", "11-complex-control-flow.pas",
    "12-euclidean-algorithm.pas", "13-matrix-scalar-expansion.pas", "14-real-bisection.pas",
    "15-boolean-precedence-empty-statements.pas", "17-library-import.pas",
    "18-function-definition.pas", "19-procedure-definition.pas", "21-vector-declaration.pas",
    "22-matrix-declaration.pas", "27-keyword-prefix-identifiers.pas", "28-text-literals.pas",
    "teste_matriz.pas", "teste_onda.pas", "teste_recursao_fibonacci.pas", "teste_completo.pas",
}


def expected_exit(path):
    return 0 if path.name in SUCCESS_CASES else 1
