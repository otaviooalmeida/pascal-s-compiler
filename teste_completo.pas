program TesteMultiplosErros;

var
  x: integer;
  y: boolean;
  
function somar(a: integer; b: integer): integer;
begin
  somar := a + b;
end;

begin
  x := 10;

  x := x @ 2;
  writeln('Erro lexico de string nao fechada);
  x := 5 # 3;

  if (x > 5) 
    x := 20;

  x := 15
  y := true;
  x := somar(5, );

  x := 3;
  z := 100;
  x := somar(10, 'texto');
end.