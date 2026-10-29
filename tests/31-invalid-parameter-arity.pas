program ParametroAridadeInvalida;
var n: integer;
function identidade(valor: integer): integer;
begin
    identidade := valor
end;
begin
    n := identidade(1, 2);
    writeln(n)
end.
