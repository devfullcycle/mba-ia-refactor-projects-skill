# Template do Relatório de Auditoria (Fase 2)

## Regras de formato

1. **Ordem:** CRITICAL → HIGH → MEDIUM → LOW. Dentro da mesma severidade, ordene pelo arquivo
   com maior impacto arquitetural.
2. **Numeração contínua** dos findings (1..N), atravessando as severidades.
3. **`File:` é obrigatório** e sempre com linha ou faixa de linhas: `models.py:28`,
   `models.py:133-169`, `src/utils.js:1-7`. Múltiplas linhas do mesmo arquivo e do mesmo
   anti-pattern no mesmo finding: `models.py:28, 92, 110-111, 140`.
4. **Description:** o que existe no código, em fato verificável. Cite o identificador ou o
   valor real encontrado (ex.: `SECRET_KEY = 'minha-chave-super-secreta-123'`).
5. **Impact:** a consequência concreta. Não repita a descrição em outras palavras.
6. **Recommendation:** ação, no imperativo, alinhada ao padrão do `refactor-playbook.md`.
7. **Anti-pattern:** cite o ID do catálogo (AP-XX) — é o que liga auditoria e refatoração.
8. Sem finding sem evidência. Sem adjetivo vazio ("código ruim", "mal escrito").
9. Salve em `reports/audit-<nome-do-projeto>.md` e imprima o mesmo conteúdo no terminal.

## Template

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome-do-projeto>
Stack:   <linguagem> + <framework versão>
Files:   <N> analyzed | ~<N> lines of code
Date:    <YYYY-MM-DD>

## Summary

CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

| Camada MVC | Situação |
|---|---|
| Config | <ausente / parcial / ok — evidência> |
| Models | <...> |
| Views/Routes | <...> |
| Controllers | <...> |
| Middlewares | <...> |
| Entry point | <...> |

## Findings

### 1. [CRITICAL] <Nome do anti-pattern> (AP-XX)
File: <arquivo:linha(s)>
Description: <o que está no código, com o identificador/valor real>
Impact: <consequência concreta>
Recommendation: <ação — padrão RP-XX>

### 2. [CRITICAL] <...>
...

### <n>. [LOW] <...>
...

## Deprecated APIs

| API | Arquivo:linha | Substituto | Removida em |
|---|---|---|---|
| <api> | <arquivo:linha> | <substituto> | <versão / "ainda suportada"> |

<Se não houver nenhuma: "Nenhuma API deprecated detectada nesta stack/versão.">

## Endpoints inventariados (baseline da Fase 3)

| Método | Rota | Handler | Observação |
|---|---|---|---|
| GET | /exemplo | <arquivo:linha> | <ex.: sem auth, N+1> |

================================
Total: <N> findings
================================
```

## Exemplo preenchido

```markdown
### 1. [CRITICAL] SQL Injection por Concatenação (AP-04)
File: models.py:28, 92, 110-111, 140, 174, 280-281, 289-299
Description: Queries montadas com concatenação de string a partir de entrada do usuário.
             Em `login_usuario` (models.py:109-111) e-mail e senha entram direto no WHERE;
             em `buscar_produtos` (models.py:289-299) os filtros `q`, `categoria`,
             `preco_min` e `preco_max` vêm da querystring.
Impact: `senha' OR '1'='1` autentica como qualquer usuário; a mesma via permite ler e
        destruir qualquer tabela. O próprio projeto já usa placeholders em database.py:70-72,
        então a correção é local.
Recommendation: Substituir toda concatenação por queries parametrizadas (`?`) e isolar o
                acesso a dados em repository por agregado — padrão RP-03.

### 7. [HIGH] Estado Global Mutável (AP-09)
File: database.py:4-11
Description: `db_connection` é variável global inicializada por efeito colateral do primeiro
             `get_db()`, com `check_same_thread=False`, e o mesmo getter cria schema e faz seed.
Impact: uma conexão compartilhada por todas as requisições, sem proteção de thread — corrida
        em escrita concorrente; impossível injetar conexão de teste.
Recommendation: Application factory + conexão por request (ou pool) injetada nos
                repositories; mover DDL/seed para script de inicialização — padrão RP-06.
```

## Cálculo do sumário

O contador por severidade é o número de **findings**, não de ocorrências: um finding que lista
8 linhas do mesmo arquivo conta 1. `Total` no rodapé = soma das quatro severidades e tem que
bater com o número do último finding.
