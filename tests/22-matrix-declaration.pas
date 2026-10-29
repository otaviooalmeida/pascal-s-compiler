program Matriz;
var
    a, b, c: array[1..3, 1..3] of real;
    i, j, k: integer;
begin
    i := 1;
    while i <= 3 do
    begin
        j := 1;
        while j <= 3 do
        begin
            c[i,j] := 0.0;
            k := 1;
            while k <= 3 do
            begin
                c[i,j] := c[i,j] + a[i,k] * b[k,j];
                k := k + 1
            end;
            j := j + 1
        end;
        i := i + 1
    end;
    writeln(c[1,1])
end.
