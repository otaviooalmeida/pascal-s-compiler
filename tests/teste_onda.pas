program TesteOnda;
uses crt, graph;
var driver, modo, t: integer;
    amplitude, velocidade, fase, tempo, y: real;
begin
    clrscr;
    amplitude := 2.0;
    velocidade := 1.5;
    fase := 0.0;
    tempo := 0.0;
    initgraph(driver, modo, 'c:\bgi');
    for t := 0 to 100 step 2 do
    begin
        y := amplitude * sin(velocidade * tempo + fase);
        writeln(t, y);
        line(t, 200, t + 1, 200);
        tempo := tempo + 0.1
    end;
    repeat until keypressed;
    closegraph
end.
