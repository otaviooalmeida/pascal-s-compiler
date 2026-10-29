program DefinicaoProcedimento;
var x: integer;
procedure Incrementar;
begin
    x := x + 1
end;
begin
    x := 0;
    Incrementar;
    writeln(x)
end.
