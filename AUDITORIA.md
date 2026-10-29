# Auditoria e validação do Pascal-S ampliado

## Parecer e referências

Esta atualização usa como referência os quatro programas entregues na raiz: `teste_completo.pas`, `teste_matrizes.pas`, `teste_onda.pas` e `teste_recursao.pas`, além do gabarito `erros_completo.txt`.

Os quatro arquivos foram executados pela CLI: matrizes e recursão compilam; `teste_onda.pas` é rejeitado por misturar `real` e `integer`; `teste_completo.pas` apresenta três erros léxicos, três sintáticos e interrompe na primeira falha semântica. O compilador valida os programas; não os executa nem gera código.

Os programas são considerados o escopo de validação solicitado; não se está inferindo requisitos além deles.

## Regras solicitadas e evidências

| Requisito | Implementação e validação | Situação |
| --- | --- | --- |
| Matrizes/vetores como tipos próprios | `ArrayType` guarda limites, dimensões e elemento; `array[1..3,1..3]` e arrays aninhados; aliases e declarações diretas | Implementado |
| Tipagem dos elementos e indexação | Matriz/vetor são indexados nos formatos usados pelos arquivos fornecidos; limites e quantidade de índices não são validados | Escopo reduzido |
| Tipos em comparações | Operandos relacionais precisam ter o mesmo tipo; `integer`/`real` misturados são rejeitados | Implementado |
| Aritmética `integer`/`real` | Operandos de tipos distintos são rejeitados; `/` retorna `real` | Implementado |
| Arrays e vetores | Aliases, declarações e indexações presentes nos arquivos fornecidos | Escopo reduzido |
| Funções e Fibonacci recursivo | Assinatura registrada antes do corpo; resultado atribuído ao nome da função; chamadas recursivas e aninhadas | Implementado |
| Tipos dos parâmetros | Verificação exata por posição, tanto para funções quanto procedimentos; sem coerção `integer`/`real` | Implementado |
| Argumento com tipo errado | A chamada é verificada por tipo e posição; o caso do gabarito fica depois do primeiro erro semântico e não é alcançado | Regra implementada; ocorrência não reportada |
| Parâmetros `var` | O modificador é aceito; os argumentos são verificados pelo tipo, sem validar se são variáveis | Escopo reduzido |
| Chamada sem argumentos obrigatórios | `f`, `f()`, `p`, `p()` e aridade excessiva são conferidos contra a assinatura | Implementado |
| Procedimentos sem parênteses | `procedimento;` é uma chamada com zero argumentos; sua categoria é validada | Implementado |
| Procedimento usado como expressão | Tanto `writeln(p)` quanto `writeln(p())` identificam uso indevido do procedimento | Rejeitado |
| Strings não fechadas | Diagnóstico na aspa inicial, descarte até o fim da linha e continuação da análise; EOF e sequências de apóstrofos testados | Implementado |
| Ponto e vírgula | Cabeçalhos, declarações, separação de comandos e fim de subprogramas; recuperação por produções `error SEMICOLON` | Implementado |
| Variável nunca declarada | Atribuição a `z` fica depois do primeiro erro semântico e não é alcançada | Regra implementada; ocorrência não reportada |
| `true` atribuído a `integer` | `true`/`false` são IDs para constantes predefinidas de tipo `boolean`, não números | Rejeitado |
| `round` | Função predefinida `round(real): integer`, usada por `teste_onda.pas` | Implementado |
| Bibliotecas identificadas por IDs | `uses` é palavra reservada; `crt`, `graph`, `Math`, `System` e nomes de rotinas são identificadores | Implementado |
| `for`, `to`, `downto`, `do` | Contador e limites inteiros; passos com `step` não são suportados | Implementado para os arquivos fornecidos |
| `repeat/until` | Corpo vazio ou composto e condição booleana | Implementado |
| E/S e onda | Assinaturas estáticas para E/S, funções matemáticas selecionadas e rotinas de `crt`/`graph` | Implementado para o catálogo documentado |
| Caixa dos nomes | Resolução Pascal case-insensitive, incluindo parâmetros, tipos, bibliotecas e subprogramas | Implementado |

## Casos fornecidos

| Arquivo | O que verifica | Resultado |
| --- | --- | --- |
| `teste_matrizes.pas` | Tipos de matriz, constantes, aliases, indexação e laços | Aceito |
| `teste_onda.pas` | `crt`/`graph`, `round`, funções matemáticas e laços; comparação `w > 25` mistura tipos | Rejeitado em `w > 25` |
| `teste_recursao.pas` | Funções/procedimentos, recursão, vetores, parâmetros `var` e booleanos | Aceito |
| `teste_completo.pas` | Erros léxicos, sintáticos e semânticos descritos em `erros_completo.txt` | Rejeitado após os 3 erros léxicos, 3 sintáticos e o primeiro semântico |

## `teste_onda.pas`

O programa compara `w: real` com `25: integer`. A checagem estrita retorna erro semântico nessa comparação; as operações aritméticas mistas também são rejeitadas.

No arquivo de erros, o PDF exige que a primeira falha semântica interrompa a análise. Assim, as falhas de `z` e do argumento de `somar` listadas no gabarito não são alcançadas.

## Arquitetura e compatibilidade com o TP1

- **`lex.py`:** 32 palavras reservadas e 57 tipos de tokens. Inclui integralmente as 27 palavras da referência, as três do TP1 (`integer`, `real`, `writeln`) e `uses`/`step`. `round`, nomes de bibliotecas, constantes booleanas e rotinas comuns continuam IDs. `case`/`record` ainda não possuem produções sintáticas.
- **`symbol_table.py`:** ambientes hash encadeados, busca sem distinção de caixa, placeholders não declarados, aliases, tipos estruturados e assinaturas.
- **`predefined.py`:** catálogo estático, não um carregador de código. Núcleo: tipos booleano/textuais, `true/false`, `read/readln/write`, funções matemáticas selecionadas e `round(real): integer`. CRT: `clrscr`, `keypressed`, `readkey`, `delay`; Graph: `initgraph`, `line`, `setcolor`, `closegraph`.
- **`yacc.py`:** ações semânticas dirigidas pela sintaxe, sem AST nem execução. O parser cria ambientes de blocos e subprogramas e valida chamadas com e sem parênteses.

O lexer isolado mantém seu modo de eventos `begin/end` para a interface já existente; `compile_file()` utiliza escopos controlados pelo parser. As produções de recuperação reajustam o ambiente conforme os marcadores ainda presentes na pilha. Toda compilação começa com tabela nova e termina com o ambiente raiz restaurado.

Os requisitos incluem tokens e comentários, leitura por `readline()`, escopos, tipos, precedência e sincronização em `;`. Os arquivos fornecidos são a validação funcional deste trabalho.

A precedência aritmética é representada por fatores/termos/expressões. `%prec IFX` abaixo de `ELSE` associa `else` ao `if` não encerrado mais próximo. O log do parser comprova a decisão e a ausência de advertências de conflito não resolvido.

Offsets são calculados por ambiente, sem alinhamento; a CLI imprime a tabela de símbolos com uma linha por ocorrência de ID.

### Comportamento reduzido

- A verificação de argumentos `var`, dimensões/limites de matrizes e chamadas de E/S é limitada aos usos válidos dos quatro arquivos.
- A recuperação léxica suprime o diagnóstico sintático na mesma linha ou na linha seguinte, para evitar cascatas no gabarito.

## Limitações explícitas

- Não há prova formal de correção ou garantia de cobertura exaustiva de toda variante de Pascal-S.
- Não há execução, backend, validação de resultados numéricos, análise de inicialização ou prova de atribuição do retorno em todos os caminhos.
- Não há `case`, `record`, `forward`/recursão mútua, casts ou chamadas qualificadas por unidade.
- `uses` reconhece identificadores e ativa apenas o catálogo conhecido. Não lê unidades externas, não conhece assinaturas arbitrárias e não libera chamadas desconhecidas.
- Atribuições, parâmetros, operações aritméticas binárias e comparações relacionais rejeitam tipos incompatíveis; o primeiro erro semântico interrompe a análise.
- Matrizes e vetores são aceitos nos formatos fornecidos; a checagem não valida limites nem número/tipo dos índices.
- Strings de um caractere têm tipo `char`; outros textos, `string`. Não há conversão implícita entre esses tipos, strings multilinha ou escape com barra invertida. `''` é rejeitado como na referência Pascal-S.
- Comentários não são aninhados. A memória do buffer depende da maior linha; a tabela de símbolos também cresce com as declarações/ambientes.
- Só o cabeçalho simples `program Nome;` é aceito.

## Reprodução

```bash
.venv/bin/python yacc.py teste_matrizes.pas
.venv/bin/python yacc.py teste_onda.pas
.venv/bin/python yacc.py teste_recursao.pas
.venv/bin/python yacc.py teste_completo.pas
```

- `teste_matrizes.pas` e `teste_recursao.pas` retornam `0`; `teste_onda.pas` retorna `1` em `w > 25`; `teste_completo.pas` retorna `1` após os erros léxicos/sintáticos e a primeira falha semântica.
- `relatorio.pdf` descreve uma versão anterior e não foi alterado.
