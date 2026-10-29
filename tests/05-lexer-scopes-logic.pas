PROGRAM EdgeCases;
VAR A, b: INTEGER;
begin
    { block comment
      spanning physical lines }
    A := 1; b := 2; // line comment
    A := A / 1;
    if not (A <= b) OR (b <> 2) then writeln(A, b) else begin end;
    if A = 1 then if b = 2 then A := 3 else A := 4;
end.
