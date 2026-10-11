# Front-end Pascal-S

Projeto do Trabalho Prático 1 de Compiladores: um front-end para um subconjunto de Pascal-S, implementado em Python com PLY. Analisa o código-fonte, verifica tipos e reporta erros; não executa os programas.

## Arquivos principais

- `lex.py`: análise léxica sob demanda.
- `yacc.py`: análise sintática, verificações semânticas e recuperação de erros.
- `symbol_table.py`: tabela de símbolos e escopos.

## Instalação e uso

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python yacc.py caminho/para/arquivo.pas
```

O compilador retorna código de saída `0` quando a análise é bem-sucedida e `1` quando encontra erros.

## Testes

Os arquivos de entrada estão em `tests/`; as saídas correspondentes estão em `tests/output/`.
