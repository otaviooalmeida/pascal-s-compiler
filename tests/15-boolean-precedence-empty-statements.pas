PrOgRaM Logica;
VaR x, y: InTeGeR; r, s: ReAl;
BeGiN
    ;;;
    x := 8; y := 2; r := 8.0; s := 2.0;
    x := x - y - 1 + y * 2 / 1;
    r := r - s - 1.0 + s * 2.0 / 1.0;
    If NoT (x < y) AnD (r >= s) Or (x = y) ThEn
        If x <> 0 ThEn WrItElN(x) ElSe WrItElN(y);
    while (x > 0) and (x <= 20) do begin x := x - 1 end;
    writeln((r = s), (r <> s), (r < s), (r <= s), (r > s), (r >= s));
    begin begin end; ; end;;
EnD.
