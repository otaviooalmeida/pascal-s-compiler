program TesteRecursao;
function Fibonacci(n: integer): integer;
begin
    if n <= 1 then
        Fibonacci := n
    else
        Fibonacci := Fibonacci(n - 1) + Fibonacci(n - 2)
end;
begin
    writeln(Fibonacci(0), Fibonacci(1), Fibonacci(10))
end.
