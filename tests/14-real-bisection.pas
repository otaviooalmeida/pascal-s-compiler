program Bissecao;
var
    esquerda, direita, meio, quadrado, tolerancia : real;
    iteracoes : integer;
begin
    esquerda := 0.0;
    direita := 2.0;
    tolerancia := 0.00001;
    iteracoes := 0;
    while (direita - esquerda) > tolerancia do
    begin
        meio := (esquerda + direita) / 2.0;
        quadrado := meio * meio;
        if quadrado < 2.0 then esquerda := meio else direita := meio;
        iteracoes := iteracoes + 1
    end;
    writeln(esquerda, direita, meio, iteracoes)
end.
