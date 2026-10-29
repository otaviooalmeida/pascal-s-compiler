program TesteCompleto;
uses crt;
const N = 4;
      Mensagem = 'Teste completo';
type Vetor = array[0..N-1] of integer;
     Matriz = array[1..2] of array[0..N-1] of integer;
var dados: Vetor; tabela: Matriz;
    i, resultado: integer;
    taxa: real; ativo: boolean; letra: char; texto: string;
function Fibonacci(n: integer): integer;
begin
    if n < 2 then Fibonacci := n
    else Fibonacci := Fibonacci(n-1) + Fibonacci(n-2)
end;
function Somar(valores: Vetor): integer;
var i, soma: integer;
begin
    soma := 0;
    for i := 0 to N-1 do soma := soma + valores[i];
    Somar := soma
end;
procedure Zerar(var valores: Vetor);
var i: integer;
begin
    for i := 0 to N-1 do valores[i] := 0
end;
procedure Banner(msg: string);
begin write(msg) end;
procedure SemParametros;
var resultado: real;
begin resultado := 1.0; writeln(resultado) end;
begin
    clrscr;
    Zerar(dados);
    for i := 0 to N-1 do dados[i] := Fibonacci(i);
    tabela[1] := dados;
    tabela[2] := tabela[1];
    resultado := Somar(tabela[2]);
    resultado := resultado + (10 div 3) + (10 mod 3);
    taxa := 1.5;
    ativo := true;
    letra := '!'; texto := 'Pascal-S';
    if ativo and not (resultado = 0) then Banner(Mensagem);
    SemParametros; SemParametros();
    for i := N-1 downto 0 step -1 do writeln(dados[i]);
    repeat resultado := resultado - 1 until resultado <= 0;
    writeln(texto, letra, taxa, ativo, resultado)
end.
