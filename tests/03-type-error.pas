program IncompatibilidadeDeTipos;
var
    cont : integer;
    acumulador, taxa : real;
begin
    acumulador := 5.5;
    taxa := 1.1;
    cont := acumulador + taxa; // real expression assigned to integer
    writeln(cont)
end.
