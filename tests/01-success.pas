program SucessoSemantico;
var
    cont, limite : integer;
    taxa, acumulador : real;
begin
    cont := 0;
    limite := 100;
    taxa := 1.25;
    acumulador := 0.0;
    while cont < limite do
    begin
        cont := cont + 1;
        acumulador := acumulador + taxa
    end;
    writeln(cont, acumulador)
end.
