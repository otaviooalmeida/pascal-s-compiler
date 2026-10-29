program Euclides;
var a, b, resto, passos : integer;
begin
    a := 1071;
    b := 462;
    passos := 0;
    while b <> 0 do
    begin
        resto := a;
        while resto >= b do resto := resto - b;
        a := b;
        b := resto;
        passos := passos + 1
    end;
    if (a > 0) and not (passos = 0) then
        writeln(a, passos)
    else
        writeln(0)
end.
