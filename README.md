# Front-end Pascal-S

Front-end em Python/PLY para análise léxica, sintática e semântica. Parte do TP1 e amplia a linguagem com subprogramas, matrizes/vetores e laços. **Não executa os programas nem gera código.**

## Uso

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python yacc.py arquivo.pas
```

Saídas: `0` = aceito; `1` = erro de compilação; `2` = argumentos inválidos ou falha de leitura/decodificação. Com um arquivo, a CLI imprime os diagnósticos e a tabela de símbolos com uma linha por ocorrência de ID, mesmo se a análise falhar.

## O que está implementado

- Identificadores e palavras reservadas **case-insensitive**, preservando a grafia para diagnósticos.
- Leitura lazy por linhas; comentários `//`, `{...}` e `(*...*)`; posições físicas de erros.
- Inteiros, reais, caracteres e strings entre aspas simples. Apóstrofo interno duplicado: `'it''s'`. Strings não terminadas são erros léxicos; strings multilinha e o literal vazio `''` são rejeitados.
- Cabeçalho simples `program Nome;`.
- Tipos `integer`, `real`, `boolean`, `char`, `string`, constantes e aliases com `const`/`type`.
- Vetores e matrizes `array[...] of ...`: aliases e indexação usados nos arquivos de validação.
- Funções, recursão direta, procedimentos e subprogramas aninhados, com escopos locais e sombreamento.
- Parâmetros por valor e `var`, verificando tipo e quantidade; o modificador `var` não exige um argumento variável.
- Procedimentos sem parênteses: `limpar;`. Se houver parâmetros obrigatórios, essa chamada é erro. Funções sem argumentos também podem aparecer como valores sem parênteses.
- `if/else`, `while`, `for ... to/downto ... do`, `repeat ... until`, `div`, `mod`, sinais unários e expressões lógicas.
- `uses`: os nomes de bibliotecas são IDs. Há um catálogo estático de assinaturas conhecidas de `crt`/`graph`; bibliotecas não são carregadas nem executadas.
- Recuperação sintática em `;` para reportar vários erros. O primeiro erro semântico interrompe a compilação.

### Parâmetros e tipagem

```pascal
function dobro(n: integer): integer;
begin dobro := n * 2 end;

procedure incrementar(var n: integer);
begin n := n + 1 end;
```

| Chamada | Resultado |
| --- | --- |
| `dobro(42)` | Válida: literal inteiro para parâmetro inteiro por valor |
| `dobro(1.5)`, `dobro('texto')`, `dobro(true)` | Erro de tipo |
| `dobro`, `dobro()` | Erro: argumento obrigatório ausente |
| `incrementar(x)` com `x: integer` | Válida |
| `incrementar(x + 1)` | Aceita se a expressão tiver o tipo esperado; o parser não verifica se `var` recebe uma variável |

Operações aritméticas binárias e comparações relacionais exigem operandos do mesmo tipo; misturas de `integer` e `real` são erros semânticos. A atribuição também exige tipos iguais. `/` retorna `real`. `true`/`false` são constantes booleanas predefinidas, não inteiros.

Para chamadas de usuário, o parser confere quantidade e tipo dos argumentos. Não distingue se o argumento de um parâmetro `var` é uma variável ou uma expressão; assim, aceita `incrementar(x + 1)` quando o tipo corresponde.

### Função `round`

`round` é uma função predefinida, recebe um argumento `real` e retorna `integer`. Não é palavra reservada:

```pascal
i := round(w)
```

O uso aparece em `teste_onda.pas`; chamadas qualificadas como `Math.round(...)` não são suportadas.

### Bibliotecas e rotinas conhecidas

- Núcleo: `write`, `read`, `readln`; `writeln` conserva o token do TP1. `sin`, `cos`, `sqrt`, `exp`, `ln`, `arctan` aceitam um argumento numérico e retornam `real`; `round(real)` retorna `integer`.
- `uses crt`: `clrscr`, `keypressed`, `readkey`, `delay`.
- `uses graph`: `initgraph`, `line`, `setcolor`, `closegraph`, com tipos de argumentos verificados.
- Uma biblioteca desconhecida pode ser registrada como ID, mas suas rotinas não ganham assinaturas fictícias: chamadas desconhecidas são erros. Não há suporte a chamadas qualificadas como `Math.round(...)`.

O lexer reconhece **32 palavras reservadas e 57 tipos de tokens**: as 27 da [referência Pascal-S](https://github.com/samiam95124/Pascal-S/blob/1c806460ed31db9baca5e503e5ebc8475dcade1d/source/pascals.pas#L1808-L1821), `integer`/`real`/`writeln` do TP1 e as extensões `uses`/`step`. `step`, `case` e `record` são reconhecidos lexicalmente, mas não têm produções no parser.

## Casos do professor

```bash
.venv/bin/python yacc.py teste_matrizes.pas
.venv/bin/python yacc.py teste_onda.pas
.venv/bin/python yacc.py teste_recursao.pas
.venv/bin/python yacc.py teste_completo.pas
```

`teste_matrizes.pas` e `teste_recursao.pas` compilam com código `0`. `teste_onda.pas` retorna `1` em `w > 25` (`real` versus `integer`). `teste_completo.pas` reporta os três erros léxicos e três sintáticos anteriores, depois interrompe em `x := true`, o primeiro erro semântico.

O gabarito `erros_completo.txt` também lista os erros semânticos de `z` e do argumento de `somar`; eles não são alcançados porque o PDF exige aborto imediato no primeiro erro semântico. A recuperação por `;` é aplicada aos erros sintáticos. O parser não valida se os argumentos `var` são variáveis, as dimensões e os limites de índices, nem chamadas inválidas de E/S. Erros sintáticos em linhas com erro léxico são suprimidos para evitar cascatas.

## Organização e limitações

- `lex.py`: tokens, leitura incremental e diagnósticos léxicos.
- `symbol_table.py`: registros compartilhados, tipos de arrays, assinaturas e ambientes.
- `predefined.py`: assinaturas estáticas das rotinas conhecidas, incluindo `round`.
- `yacc.py`: gramática LALR(1), escopos, tipos, recuperação e CLI.

Offsets lógicos: `integer` 4 bytes, `real` 8, `boolean`/`char` 1, `string` 8; arrays multiplicam o tamanho do elemento pelos limites, sem alinhamento. Não é um ABI nem uma alocação real de memória.

Não há backend, avaliação de Fibonacci/matrizes, análise de inicialização, prova de retorno em todos os caminhos, importação real, `forward`/recursão mútua, `case`, `record`, `step`, cabeçalhos com arquivos ou casts. A checagem de matrizes se limita aos usos nos arquivos fornecidos.

A auditoria detalhada está em [AUDITORIA.md](AUDITORIA.md). `relatorio.pdf` ainda precisa ser atualizado para refletir esta implementação.
