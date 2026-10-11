PROGRAM EdgeCases;
VAR A, a: INTEGER;
begin
    { block comment
      spanning physical lines }
    A := 1; a := 2; // line comment
    A := A / 1;
    if not (A <= a) OR (a <> 2) then writeln(A, a) else begin end;
    if A = 1 then if a = 2 then A := 3 else A := 4;
end.
