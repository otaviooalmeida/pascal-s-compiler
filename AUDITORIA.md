# Auditoria e validação do Pascal-S ampliado

## Parecer e referências

Foram analisados integralmente `Trabalho_Prático_1.pdf` e `relatorio.pdf`, a lista de palavras e o código da [referência Pascal-S](https://github.com/samiam95124/Pascal-S/blob/1c806460ed31db9baca5e503e5ebc8475dcade1d/source/pascals.pas), e o arquivo local `ONDA (1).PAS`.

A linguagem foi ampliada a pedido do usuário: não está mais limitada à EBNF do PDF. A validação atual tem **122 testes, 1.159 subtestes e 40 entradas Pascal com logs reais**: 18 aceitas e 22 rejeitadas conforme as expectativas independentes de `tests/fixture_cases.py`. A tabela LALR(1) é gerada sem advertências de conflito não resolvido.

**Os arquivos secretos do professor não estão disponíveis.** Os programas `teste_matriz`, `teste_onda`, `teste_recursao_fibonacci`, `teste_completo` e `erro_completo` aqui presentes são exemplos novos, inspirados nos nomes informados. Não são cópias dos testes do professor, nem prova de aprovação em toda entrada desconhecida. O compilador valida programas; não calcula seus resultados nem executa gráficos, E/S ou recursão.

## Regras solicitadas e evidências

| Requisito | Implementação e validação | Situação |
| --- | --- | --- |
| Matrizes/vetores como tipos próprios | `ArrayType` guarda limites, dimensões e elemento; `array[1..3,1..3]` e arrays aninhados; aliases e declarações diretas | Implementado |
| Tipagem dos elementos e indexação | Índices inteiros; excesso de índices, índices literais fora dos limites, indexação de escalar e atribuição de tipo incorreto são erros | Implementado estaticamente |
| Arrays em atribuições, parâmetros e retornos | Compatibilidade estrutural, inclusive limites; subvetores, cópia de arrays e elementos de resultados de funções | Implementado |
| Funções e Fibonacci recursivo | Assinatura registrada antes do corpo; resultado atribuído ao nome da função; chamadas recursivas e aninhadas | Implementado |
| Tipos dos parâmetros | Verificação exata por posição, tanto para funções quanto procedimentos; sem coerção `integer`/`real` | Implementado |
| Texto/real/booleano enviados a `integer` | Matriz de testes cruzados dos cinco tipos básicos; literais textuais de um e de vários caracteres | Rejeitados |
| Literais em parâmetros `var` | Referência exige lvalue: literal, constante, expressão, valor entre parênteses e resultado de chamada não são variáveis | Rejeitados |
| Chamada sem argumentos obrigatórios | `f`, `f()`, `p`, `p()` e aridade excessiva são conferidos contra a assinatura | Implementado |
| Procedimentos sem parênteses | `procedimento;` é uma chamada com zero argumentos; sua categoria é validada | Implementado |
| Procedimento usado como expressão | Tanto `writeln(p)` quanto `writeln(p())` identificam uso indevido do procedimento | Rejeitado |
| Strings não fechadas | Diagnóstico na aspa inicial, descarte até o fim da linha e continuação da análise; EOF e sequências de apóstrofos testados | Implementado |
| Ponto e vírgula | Cabeçalhos, declarações, separação de comandos e fim de subprogramas; recuperação por produções `error SEMICOLON` | Implementado |
| Variável nunca declarada | Atribuição, expressão, índice, condição e argumento; parâmetros e variáveis locais não escapam do escopo | Rejeitado |
| `true` atribuído a `integer` | `true`/`false` são IDs para constantes predefinidas de tipo `boolean`, não números | Rejeitado |
| `round` fora do escopo | Não é palavra reservada e não há assinatura predefinida, mesmo após `uses Math` | Chamada não declarada rejeitada |
| Bibliotecas identificadas por IDs | `uses` é palavra reservada; `crt`, `graph`, `Math`, `System` e nomes de rotinas são identificadores | Implementado |
| `for`, `to`, `downto`, `do`, `step` | Contador, início, limite e passo inteiros; passo constante zero é erro; positivo/negativo e laços aninhados | Implementado |
| `repeat/until` | Corpo vazio ou composto e condição booleana | Implementado |
| E/S e onda | Assinaturas estáticas para E/S, funções matemáticas selecionadas e rotinas de `crt`/`graph` | Implementado para o catálogo documentado |
| Caixa dos nomes | Resolução Pascal case-insensitive, incluindo parâmetros, tipos, bibliotecas e subprogramas | Implementado |

### O significado de “mandar um literal”

Há uma ambiguidade na solicitação. O comportamento adotado é o de Pascal:

- `f(42)` é válido se `f` recebe `integer` **por valor**; isso é necessário para exemplos naturais como `Fibonacci(10)`.
- `f(1.0)`, `f('texto')`, `f('x')` e `f(true)` são erros para esse parâmetro.
- Se o parâmetro é `var n: integer`, até `f(42)` é erro: o argumento deve ser uma variável inteira, como `f(x)` ou um elemento inteiro de vetor.

A proibição de **qualquer** literal, inclusive inteiro, em parâmetro por valor seria uma regra adicional não padrão. Foi pedida confirmação antes de adotá-la; ela não foi presumida nem confundida com incompatibilidade de tipos.

## Casos inspirados nos nomes dos testes

| Arquivo | O que verifica | Resultado |
| --- | --- | --- |
| `tests/teste_matriz.pas` | Matrizes inteiras, dimensões nomeadas por constante, multiplicação com três laços e parâmetros de matriz por valor/`var` | Aceito |
| `tests/teste_onda.pas` | `uses crt,graph`, chamadas sem parênteses, `sin`, cálculo real homogêneo, `for/step`, gráficos e `repeat until keypressed` | Aceito |
| `tests/teste_onda_erro_round.pas` | `w := w / round(w)` com tipos anteriores corretos e importações | Erro semântico em `round` |
| `tests/teste_recursao_fibonacci.pas` | Retorno inteiro, teste de base e duas chamadas recursivas | Aceito |
| `tests/teste_completo.pas` | Tipos básicos, constantes, aliases, vetores/matrizes, recursão, referências, procedimentos, escopos, `div/mod`, `for` e `repeat` | Aceito |
| `tests/erro_completo.pas` | Declarações ruins, string aberta, comandos incompletos e `true` para inteiro | Quatro erros sintáticos, um léxico e um semântico |
| `tests/erro_parametro_ausente.pas` | Função com parâmetro usada sem argumento | Rejeitado |
| `tests/30-invalid-parameter-type.pas` | Texto passado a função que espera inteiro | Rejeitado |
| `tests/31-invalid-parameter-arity.pas` | Argumento excedente | Rejeitado |

Além desses casos, a suíte cobre:

- testes cruzados dos tipos `integer`, `real`, `boolean`, `char`, `string`, por valor e por referência;
- grupos de parâmetros e múltiplos subprogramas com nomes locais iguais, captura de escopo e sombreamento;
- arrays de tipos/dimensões/limites incompatíveis, submatrizes e retornos estruturados;
- literais muito longos, reais, caracteres, strings, escapes por apóstrofo duplicado e os três formatos de comentário;
- EOF durante comentário/string, sincronização e compilação repetida sem vazamento de estado;
- 60 programas numéricos e 40 formas de matrizes gerados com tipos corretos;
- 400 mutações do programa simples e 200 do programa completo, com sementes fixas;
- listas longas, 2.500 comandos e 250 níveis de blocos/parênteses;
- CLI, UTF-8 inválido, argumentos errados, caminhos Unicode e logs comparados com as execuções atuais.

As mutações verificam ausência de exceções não tratadas e consistência entre sucesso/falha e diagnósticos. Não são um oráculo independente de aceitação de todos os programas Pascal.

## `ONDA (1).PAS`: resultado real, sem editar a entrada

O arquivo foi preservado. Seu cabeçalho, `uses crt,graph`, nomes em caixas diferentes, E/S e chamadas iniciais são reconhecidos. Com a tipagem estrita, a primeira inconsistência é:

```pascal
if w > 25 then
```

`w` foi declarado `real`; `25` é `integer`. A execução da CLI retorna 1 e relata `Semantic error at 14:6: operator '>' cannot mix real and integer`. Portanto, não seria correto prometer que o primeiro diagnóstico desse arquivo será em `round`: há uma falha anterior. O exemplo `teste_onda_erro_round.pas` usa `25.0` e demonstra especificamente `undeclared function 'round'` na chamada.

Como no TP1, o primeiro erro semântico encerra a compilação. Erros léxicos/sintáticos anteriores podem ser acumulados; não se promete listar todas as incompatibilidades semânticas de um arquivo após o primeiro aborto.

## Arquitetura e compatibilidade com o TP1

- **`lex.py`:** 32 palavras reservadas e 57 tipos de tokens. Inclui integralmente as 27 palavras da referência, as três do TP1 (`integer`, `real`, `writeln`) e `uses`/`step`. `round`, nomes de bibliotecas, constantes booleanas e rotinas comuns continuam IDs. `case`/`record` ainda não possuem produções sintáticas.
- **`symbol_table.py`:** ambientes hash encadeados, busca sem distinção de caixa, placeholders não declarados, registros compartilhados, aliases, tipos estruturados e assinaturas. `Parameter` diferencia valor e referência. Tipos e rotinas predefinidas não consomem offsets de variáveis.
- **`predefined.py`:** catálogo estático, não um carregador de código. Núcleo: tipos booleano/textuais, `true/false`, `read/readln/write` e funções matemáticas selecionadas. CRT: `clrscr`, `keypressed`, `readkey`, `delay`; Graph: `initgraph`, `line`, `setcolor`, `closegraph`. `round` está intencionalmente ausente.
- **`yacc.py`:** ações semânticas dirigidas pela sintaxe, sem AST nem execução. O parser cria os ambientes de blocos e subprogramas; resolve novamente IDs de lookahead ao consumi-los para não vincular parâmetros ao ambiente errado. A mesma função valida chamadas com e sem parênteses.

O lexer isolado mantém seu modo de eventos `begin/end` para a interface já existente; `compile_file()` utiliza escopos controlados pelo parser. As produções de recuperação reajustam o ambiente conforme os marcadores ainda presentes na pilha. Toda compilação começa com tabela nova e termina com o ambiente raiz restaurado.

Os requisitos originais continuam exercitados: tokens e comentários do PDF, leitura por `readline()` em vez de leitura total, referências diretas dos IDs, atributos/offsets, escopos, duplicidades e omissões, tipos fortes, precedência, dangling else e sincronização em `;`. Mudanças deliberadas em relação à versão inicial são a insensibilidade de caixa dos IDs, a ampliação gramatical e a retirada do cadastro de `round`.

A precedência aritmética é representada por fatores/termos/expressões. `%prec IFX` abaixo de `ELSE` associa `else` ao `if` não encerrado mais próximo. O log do parser comprova a decisão e a ausência de advertências de conflito não resolvido.

Offsets são lógicos por ambiente, sem alinhamento: inteiro 4, real 8, booleano/caractere 1, string 8; arrays multiplicam o tamanho do elemento por suas extensões. Não existe alocação real nem definição de ABI de parâmetros.

### Falhas de robustez já corrigidas

1. **Inteiro com 5.000 dígitos:** não depende mais de `int(texto)` aplicado à entrada inteira, cujo limite padrão gerava `ValueError`. O lexer preserva o lexema; quando um valor inteiro é necessário para limites/constantes, a conversão usa blocos pequenos. Diagnósticos de limites enormes também evitam reconversões decimais ilimitadas.
2. **UTF-8 inválido:** a CLI trata `UnicodeError` junto de `OSError`, informa falha de leitura e sai com código 2, sem traceback.
3. **Colisão na importação:** o catálogo não pode transformar um nome já declarado pelo usuário em predefinido. A regressão `program line; uses graph; var line:integer; ...` agora acusa o conflito, em vez de permitir indevidamente a redeclaração.

## Limitações explícitas

- Não há acesso aos testes secretos, prova formal de correção ou garantia de cobertura exaustiva de toda variante de Pascal-S.
- Não há execução, backend, validação de resultados numéricos, análise de inicialização ou prova de atribuição do retorno em todos os caminhos.
- Não há `case`, `record`, `forward`/recursão mútua, casts ou chamadas qualificadas por unidade.
- `uses` reconhece identificadores e ativa apenas o catálogo conhecido. Não lê unidades externas, não conhece assinaturas arbitrárias e não libera chamadas desconhecidas.
- `/` conserva o tipo numérico homogêneo dos operandos, interpretação mantida do TP1. Não há coerção implícita entre inteiros e reais. Isso difere de alguns dialetos Pascal.
- Arrays têm limites inteiros constantes. Índices constantes podem ser verificados; valores dinâmicos só têm seu tipo validado.
- Strings de um caractere têm tipo `char`; outros textos, `string`. Não há conversão implícita entre esses tipos, strings multilinha ou escape com barra invertida. `''` é rejeitado como na referência Pascal-S.
- Comentários não são aninhados. A memória do buffer depende da maior linha; a tabela de símbolos também cresce com as declarações/ambientes.
- O cabeçalho `program p(input,output)` é reconhecido; isso não implementa E/S explícita de arquivos tipados.

## Reprodução e entregáveis

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tests/run_fixtures.py
.venv/bin/python yacc.py tests/teste_matriz.pas
.venv/bin/python yacc.py tests/teste_onda_erro_round.pas
```

- A suíte esperada termina com **122 testes e 1.159 subtestes**, sem falhas.
- O runner valida os códigos de saída e regenera logs reais das 40 entradas. Expectativas ficam em `tests/fixture_cases.py`, não são inferidas do compilador.
- `tests/output/unittest.log` registra a validação; `tests/output/parser-lalr.log` registra as tabelas/decisões do PLY.
- `relatorio.pdf` existe, mas descreve uma versão antiga. É necessário atualizar gramática, tipos, escopos, catálogo, exclusão de `round`, novos testes e limitações. Não há fonte editável do relatório no repositório; o PDF não foi sobrescrito.
- ZIP e apresentação ao professor permanecem tarefas de entrega. Preservaram-se os arquivos do usuário e a remoção preexistente de `CONTEXT.md`.
