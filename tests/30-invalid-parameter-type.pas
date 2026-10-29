program ParametroTipoInvalido;
var n: integer;
function identidade(valor: integer): integer;
begin
    identidade := valor
end;
begin
    n := identidade('texto');
    writeln(n)
end.
