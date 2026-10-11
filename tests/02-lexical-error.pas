program TesteErroLexico;
var
    cont : integer;
begin
    cont := 10 @ 5; // '@' is illegal
    writeln(cont)
end.
