program ControleComplexo;
var
    linha, coluna, limite, soma, produto : integer;
    taxa, acumulado : real;
begin
    limite := 8;
    linha := 0;
    soma := 0;
    produto := 1;
    taxa := 0.25;
    acumulado := 0.0;
    while linha < limite do
    begin
        coluna := 0;
        while coluna <= linha do
        begin
            soma := soma + (linha * coluna + 1);
            if not (coluna = 0) and ((linha <> coluna) or (linha >= limite)) then
                produto := produto * (coluna + 1)
            else if linha > 0 then
                produto := produto / (linha + 1)
            else
                begin ; end;
            acumulado := acumulado + taxa * (1.0 + taxa);
            coluna := coluna + 1
        end;
        linha := linha + 1
    end;
    writeln(linha, coluna, soma, produto, acumulado, (soma >= produto))
end.
