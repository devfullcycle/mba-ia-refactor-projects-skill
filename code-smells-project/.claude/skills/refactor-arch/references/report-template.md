# Template do Relatório de Auditoria (Fase 2)

Imprima o relatório **exatamente** neste formato. Os findings são ordenados por severidade: CRITICAL → HIGH → MEDIUM → LOW. Dentro da mesma severidade, ordene por arquivo/linha.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do projeto>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<M> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [SEVERITY] <Nome do anti-pattern> (<código AP-xx>)
File: <arquivo>:<linha(s)>
Description: <o que é o problema neste projeto, concreto>
Impact: <consequência prática>
Recommendation: <como corrigir; se for API deprecated, citar o substituto moderno>

### [SEVERITY] <Nome do anti-pattern> (<código AP-xx>)
File: <arquivo>:<linha(s)>
Description: ...
Impact: ...
Recommendation: ...

<... um bloco por finding ...>

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Regras de preenchimento

- **`[SEVERITY]`**: exatamente `CRITICAL`, `HIGH`, `MEDIUM` ou `LOW`, em maiúsculas, entre colchetes.
- **`File`**: caminho relativo à raiz do projeto + linha(s). Use intervalo quando o problema abrange um bloco (`models.py:171-233`) e lista quando são pontos discretos (`app.py:7,8`). **Confirme os números de linha no arquivo real.**
- **`Description`**: específica ao projeto (cite o nome da função/rota/variável), não genérica. "Query SQL montada por concatenação em `login_usuario`" é bom; "código ruim" não.
- **`Recommendation`**: acionável. Para APIs deprecated, nomear o equivalente moderno.
- **`Summary`**: contagens devem bater com o número de findings listados.
- **Mínimo**: o relatório deve conter pelo menos 5 findings, com pelo menos 1 CRITICAL ou HIGH. Se o projeto tiver menos, revise — provavelmente há detecções faltando.
- A linha final `Phase 2 complete. Proceed...` é obrigatória e deve ser seguida de uma pausa real, aguardando resposta do usuário.
