program TesteOndaRoundForaDoEscopo;
uses crt, graph, Math;
var w: real;
begin
    clrscr;
    w := 50.5;
    if w > 25.0 then
        w := w / round(w);
    closegraph
end.
