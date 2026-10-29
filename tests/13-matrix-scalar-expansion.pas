program ProdutoMatrizesEscalares;
{ A EBNF nao possui arrays. Cada elemento 2x2 e uma variavel escalar.
  Este teste verifica expressoes do produto matricial, nao suporte a arrays. }
var
    a11, a12, a21, a22 : integer;
    b11, b12, b21, b22 : integer;
    c11, c12, c21, c22, determinante : integer;
begin
    a11 := 1; a12 := 2; a21 := 3; a22 := 4;
    b11 := 5; b12 := 6; b21 := 7; b22 := 8;
    c11 := a11 * b11 + a12 * b21;
    c12 := a11 * b12 + a12 * b22;
    c21 := a21 * b11 + a22 * b21;
    c22 := a21 * b12 + a22 * b22;
    determinante := c11 * c22 - c12 * c21;
    if (c11 = 19) and (c12 = 22) and (c21 = 43) and (c22 = 50) then
        writeln(c11, c12, c21, c22, determinante)
    else
        writeln(0)
end.
