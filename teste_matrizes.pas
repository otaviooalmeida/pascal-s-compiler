program GeradorMatrizesAleatorias;

const
  MaxMatrizes = 100;
  DimL = 3;
  DimC = 3;

type
  TMatriz = array [1..DimL, 1..DimC] of integer;

var
  k, i, j: integer;
  seed: integer;
  mat: TMatriz;

{ Funcao manual para gerar numeros pseudo-aleatorios (0 ate maxVal - 1) }
function meuRandom(maxVal: integer): integer;
begin
  { Algoritmo gerador linear congruencial simples }
  seed := (seed * 21 + 1);
  if seed < 0 then
    seed := -seed;
  meuRandom := seed mod maxVal;
end;

begin
  { Inicializa a semente inicial do gerador }
  seed := 1234;

  writeln('Iniciando geracao de 100 matrizes (3x3)...');
  writeln('------------------------------------------');

  for k := 1 to MaxMatrizes do
  begin
    { Preenche a matriz atual com valores aleatorios de 0 a 9 }
    for i := 1 to DimL do
    begin
      for j := 1 to DimC do
      begin
        mat[i, j] := meuRandom(10);
      end;
    end;

    { Para evitar poluir excessivamente a tela com 100 matrizes completas, 
      exibimos apenas as 3 primeiras e a ultima, mostrando que o loop funciona. }
    if (k <= 3) or (k = MaxMatrizes) then
    begin
      writeln('Matriz numero: ', k);
      for i := 1 to DimL do
      begin
        writeln(mat[i, 1], '   ', mat[i, 2], '   ', mat[i, 3]);
      end;
      writeln('------------------------------------------');
    end;
  end;

  writeln('Sucesso! As 100 matrizes foram geradas e processadas.');
end.