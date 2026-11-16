# Template do Relatório de Auditoria (Fase 2)

Use **exatamente** esta estrutura. Exiba no chat e salve em `reports/audit-project-<nome-do-projeto>.md`. Substitua tudo entre `<>`. Linhas devem ser reais (verifique no arquivo).

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome>
Stack:   <linguagem> + <framework> (<versão>)
Files:   <N> analisados | ~<LOC> linhas de código
Database: <banco / forma de acesso>

## Summary
| Severidade | Qtde |
|---|---|
| CRITICAL | <n> |
| HIGH     | <n> |
| MEDIUM   | <n> |
| LOW      | <n> |
| **Total** | **<n>** |

## Current Architecture
<2–5 linhas: como o código está organizado hoje, que camadas estão misturadas, nível (monolítico/parcial/em camadas).>

## Findings
(ordenados por severidade: CRITICAL → HIGH → MEDIUM → LOW)

### [CRITICAL] AP-01 — <Nome do anti-pattern>
- **File**: `<caminho>:<linha-início>-<linha-fim>`
- **Description**: <o que foi encontrado, com trecho curto se útil>
- **Impact**: <consequência concreta>
- **Recommendation**: <o que fazer> (Playbook P<n>)

### [HIGH] AP-04 — <...>
...

(Repita para cada achado. Agrupe ocorrências repetidas do mesmo padrão em um achado, listando todos os arquivos/linhas.)

## Deprecated APIs
| API obsoleta | Local | Equivalente moderno | Severidade |
|---|---|---|---|
| `<api>` | `<arquivo>:<linha>` | `<api nova>` | <nível> |
(Se não houver: "Nenhuma API deprecated detectada.")

## Target Architecture (proposta)
```
<árvore de pastas MVC proposta para a stack>
```

================================
Total: <n> achados (<C> critical, <H> high, <M> medium, <L> low)
================================

Fase 2 concluída. Deseja prosseguir com a refatoração (Fase 3)? [s/n]
````

## Regras de preenchimento

- Todo achado tem arquivo + intervalo de linhas; nunca "vários arquivos" sem listar.
- Severidade segue `anti-patterns-catalog.md`.
- Recomendações são específicas ao código observado, não genéricas.
- O relatório deve conter pelo menos um achado por nível presente no código; se um nível não tiver ocorrências, mostre `0` na tabela de resumo.
- Termine **sempre** com a pergunta de confirmação e pare.
