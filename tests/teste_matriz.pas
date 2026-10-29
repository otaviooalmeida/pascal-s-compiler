program TesteMatriz;
const N = 3;
type Matriz = array[1..N, 1..N] of integer;
var a, b, c: Matriz; i, j: integer;
procedure Multiplicar(var resultado: Matriz; esquerda, direita: Matriz);
var i, j, k: integer;
begin
    for i := 1 to N do
        for j := 1 to N do
        begin
            resultado[i,j] := 0;
            for k := 1 to N do
                resultado[i,j] := resultado[i,j] + esquerda[i,k] * direita[k,j]
        end
end;
begin
    for i := 1 to N do
        for j := 1 to N do
        begin
            a[i,j] := i + j;
            b[i,j] := i * j
        end;
    Multiplicar(c, a, b);
    writeln(c[1,1], c[2,2], c[3,3])
end.
