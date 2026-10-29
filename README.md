# Front-end Pascal-S

Front-end em Python/PLY para análise léxica, sintática e semântica. Parte do TP1 e amplia a linguagem com subprogramas, matrizes/vetores e laços. **Não executa os programas nem gera código.**

## Uso

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python yacc.py arquivo.pas
```

Saídas: `0` = aceito; `1` = erro de compilação; `2` = argumentos inválidos ou falha de leitura/decodificação. Com um arquivo informado, a CLI imprime uma linha por ocorrência de ID, em ordem no arquivo, com escopo global/local, tipo, deslocamento e estado da declaração, mesmo se a análise falhar.

## O que está implementado

- Identificadores e palavras reservadas **case-insensitive**, preservando a grafia para diagnósticos.
- Leitura lazy por linhas; comentários `//`, `{...}` e `(*...*)`; posições físicas de erros.
- Inteiros, reais, caracteres e strings entre aspas simples. Apóstrofo interno duplicado: `'it''s'`. Strings não terminadas são erros léxicos; strings multilinha e o literal vazio `''` são rejeitados.
- Cabeçalho simples ou `program Nome(input,output);`.
- Tipos `integer`, `real`, `boolean`, `char`, `string`, constantes e aliases com `const`/`type`.
- Vetores e matrizes `array[...] of ...`: tipo próprio com limites, dimensões e elemento; indexação, subvetores, atribuições e parâmetros/retornos estruturados.
- Funções, recursão direta, procedimentos e subprogramas aninhados, com escopos locais e sombreamento.
- Parâmetros por valor e `var`, verificando tipos exatos, quantidade de argumentos e passagem por referência.
- Procedimentos sem parênteses: `limpar;`. Se houver parâmetros obrigatórios, essa chamada é erro. Funções sem argumentos também podem aparecer como valores sem parênteses.
- `if/else`, `while`, `for ... to/downto ... [step ...] do`, `repeat ... until`, `div`, `mod`, sinais unários e expressões lógicas.
- `uses`: os nomes de bibliotecas são IDs. Há um catálogo estático de assinaturas conhecidas de `crt`/`graph`; bibliotecas não são carregadas nem executadas.
- Recuperação sintática em `;`, incluindo declarações e blocos aninhados. Erros semânticos encerram a compilação na primeira ocorrência, conforme a política do TP1.

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
| `incrementar(42)`, `incrementar(x + 1)` | Erro: `var` exige variável, não literal/expressão |

Não há coerção numérica implícita em operações, atribuições ou parâmetros de usuário. `true`/`false` são constantes booleanas predefinidas, não inteiros. Um vetor/matriz não é confundido com seu elemento: limites, dimensões e tipo do elemento participam da compatibilidade.

**Interpretação de “literal”:** texto, real e booleano são rejeitados para um parâmetro `integer`. Inteiros literais são permitidos por valor, como em Pascal e em `Fibonacci(10)`; são proibidos para `var`. Proibir também `f(42)` por valor seria uma regra adicional, não adotada sem confirmação.

### `round` está fora do escopo

`round` **não é reservado e não é predefinido**, inclusive após `uses Math`. Assim:

```pascal
w := w / round(w)
```

acusa `undeclared function 'round'`, em vez de assumir uma assinatura ou gerar um erro de tipo decorrente de um retorno inventado. Uma função própria explicitamente declarada com esse nome pode ser usada como qualquer outro ID. Isso substitui o suporte predefinido de uma versão anterior.

### Bibliotecas e rotinas conhecidas

- Núcleo: `write`, `read`, `readln`; `writeln` conserva o token do TP1. `sin`, `cos`, `sqrt`, `exp`, `ln`, `arctan` aceitam um argumento numérico e retornam `real`.
- `uses crt`: `clrscr`, `keypressed`, `readkey`, `delay`.
- `uses graph`: `initgraph`, `line`, `setcolor`, `closegraph`, com parâmetros tipados; `initgraph` exige variáveis inteiras nos dois primeiros argumentos.
- Uma biblioteca desconhecida pode ser registrada como ID, mas suas rotinas não ganham assinaturas fictícias: chamadas desconhecidas são erros. Não há suporte a chamadas qualificadas como `Math.round(...)`.

O lexer reconhece **32 palavras reservadas e 57 tipos de tokens**: as 27 da [referência Pascal-S](https://github.com/samiam95124/Pascal-S/blob/1c806460ed31db9baca5e503e5ebc8475dcade1d/source/pascals.pas#L1808-L1821), `integer`/`real`/`writeln` do TP1 e as extensões `uses`/`step`. `boolean`, `char`, `string` e `true`/`false` são IDs predefinidos, não palavras reservadas. `case` e `record` ainda são apenas reconhecidos lexicalmente, sem produções implementadas.

## Testes

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tests/run_fixtures.py
```

A suíte contém **122 testes, 1.159 subtestes e 40 entradas `.pas`**, com logs reais em `tests/output/`. Inclui:

- `teste_matriz.pas`, `teste_onda.pas`, `teste_recursao_fibonacci.pas`, `teste_completo.pas` e `erro_completo.pas`;
- testes cruzados dos tipos básicos em parâmetros por valor e referência;
- 60 programas numéricos e 40 formas de matrizes gerados deterministicamente;
- 600 mutações com sementes fixas, verificando ausência de exceções e consistência dos diagnósticos;
- erros de aridade, escopo, indexação, strings, separadores, tipos e referências a `round`.

Os exemplos são nossos, inspirados nos nomes informados: **não são os arquivos secretos do professor**. Seus resultados não garantem aprovação em entradas desconhecidas. As expectativas das entradas ficam em `tests/fixture_cases.py`; a suíte compara os logs com os diagnósticos da CLI, ignorando a tabela de símbolos.

`ONDA (1).PAS` foi preservado. Com a tipagem estrita, sua primeira falha é `w > 25` (real versus integer), antes de `round`. O exemplo isolado `teste_onda_erro_round.pas` demonstra especificamente a função não declarada.

## Organização e limitações

- `lex.py`: tokens, leitura incremental e diagnósticos léxicos.
- `symbol_table.py`: registros compartilhados, tipos de arrays, assinaturas e ambientes.
- `predefined.py`: assinaturas estáticas das rotinas conhecidas; não inclui `round`.
- `yacc.py`: gramática LALR(1), escopos, tipos, recuperação e CLI.

Offsets lógicos: `integer` 4 bytes, `real` 8, `boolean`/`char` 1, `string` 8; arrays multiplicam o tamanho do elemento pelos limites, sem alinhamento. Não é um ABI nem uma alocação real de memória.

Não há backend, avaliação de Fibonacci/matrizes, análise de inicialização, prova de retorno em todos os caminhos, importação real, `forward`/recursão mútua, `case`, `record` ou casts. Índices literais fora dos limites são detectados; índices dinâmicos são verificados apenas quanto ao tipo. A divisão `/` conserva o tipo dos operandos, interpretação mantida do TP1.

A auditoria detalhada está em [AUDITORIA.md](AUDITORIA.md). `relatorio.pdf` ainda precisa ser atualizado para refletir esta implementação.
