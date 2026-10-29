Program Tragetoria;
uses crt,graph;

var t,C,D:integer;
   Y1,Y2,A,W,fi : real;
begin
clrscr;
write('Digite o valor da Amplitude: ');
read(A);
write('Digite o valor do Angulo: ');
read(fi);
write('Digite a velocidade angular W: ');
read(w);
if w > 25 then
   w:= w/(round(w) div 25);
clrscr;
INITGRAPH(C,D,'c:\arquiv~1\tp\bgi');
line(0,200,640,200);
line(10,0,10,600);
For T:=0 to 639 do
begin
Y1:=(A*sin(W*t+fi));
Y2:=(A*sin(W*(t+1)+fi));
{onda1}
line(t,round(y1+200),(t+1),round(y2+200));
end;
For T:=0 to 639 do
begin
{fi = 0}
Y1:=(A*sin(W*t));
Y2:=(A*sin(W*(t+1)));
{onda2}
setcolor(2);
line(t,round(y1+200),(t+1),round(y2+200));
end;
repeat until keypressed;
CLOSEGRAPH;
end.