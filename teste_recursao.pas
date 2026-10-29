program AnalisadorCompletoTest;
uses crt;
const
  MaxTamanho = 50;
  FatorLimite = 10;
  MensagemFim = 'Processamento concluido com sucesso.';

type
  VetorInteiros = array [1..MaxTamanho] of integer;
  EstadoLogico = boolean;

var
  globalContador: integer;
  globalFator: real;
  globalAtivo: EstadoLogico;
  dados: VetorInteiros;


function mdc(a: integer; b: integer): integer;
begin
  if b = 0 then
    mdc := a
  else
    mdc := mdc(b, a mod b);
end;


procedure inicializarVetor(var arr: VetorInteiros; tam: integer);
var
  i: integer;
begin
  for i := 1 to tam do
  begin
    arr[i] := i * 3;
  end;
end;


function ehPrimo(num: integer): EstadoLogico;
var
  i: integer;
  primo: EstadoLogico;
begin
  if num <= 1 then
    ehPrimo := false
  else
  begin
    primo := true;
    i := 2;
    while (i * i <= num) and primo do
    begin
      if (num mod i) = 0 then
        primo := false;
      i := i + 1;
    end;
    ehPrimo := primo;
  end;
end;


procedure processarDados(var arr: VetorInteiros; limite: integer);
var
  j, soma, tempMdc: integer;
  fatorLocal: real;
begin
  soma := 0;
  fatorLocal := 1.5;
  
  for j := 1 to limite do
  begin
    soma := soma + arr[j];
    if ehPrimo(arr[j]) then
    begin
      writeln('Elemento primo encontrado: ', arr[j]);
    end;
  end;
  
  tempMdc := mdc(soma, limite);
  writeln('Soma total: ', soma);
  writeln('MDC da soma com o limite: ', tempMdc);
end;


begin
  globalContador := 20;
  globalFator := 2.718;
  globalAtivo := true;

  if globalAtivo and (globalContador > 5) then
  begin
    inicializarVetor(dados, globalContador);
    processarDados(dados, globalContador);
    writeln(MensagemFim);
  end
  else
  begin
    writeln('Condicao global nao atendida.');
  end;
end.