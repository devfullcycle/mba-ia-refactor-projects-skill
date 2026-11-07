# Audit Report Template (Fase 2)

Gere o relatório **exatamente** nesta estrutura. Os findings devem vir
**ordenados por severidade (CRITICAL → HIGH → MEDIUM → LOW)** e todo finding
precisa de **arquivo e linha(s)**. Imprima no chat e salve em
`reports/audit-project-<N>.md`.

---

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome-do-projeto>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<linhas> lines of code
Date:    <YYYY-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Nome do anti-pattern> (<código AP>)
File: <arquivo>:<linha(s)>
Description: <o que foi encontrado concretamente no código>
Impact: <por que importa — manutenção, segurança, performance>
Recommendation: <ação concreta de correção>

### [CRITICAL] <...>
File: <...>:<...>
Description: ...
Impact: ...
Recommendation: ...

### [HIGH] <...>
File: <...>:<...>
...

### [MEDIUM] <...>
...

### [LOW] <...>
...

================================
Total: <N> findings
================================
```

---

## Regras de preenchimento

- **Um bloco por finding.** Se o mesmo anti-pattern aparece em vários lugares,
  liste as linhas de todas as ocorrências no campo `File:` (ex.:
  `models.py:28, 110, 140`).
- `Description` descreve o **código real** observado, não a teoria. Cite o
  trecho quando ajudar.
- `Recommendation` é acionável e aponta para o padrão do playbook.
- O bloco `Summary` deve bater com a contagem real dos findings.
- Inclua o código do anti-pattern (`AP-0X`) entre parênteses no título para
  rastrear até o catálogo e o playbook.
- Mantenha os delimitadores `====` e os cabeçalhos `##`/`###` como no modelo —
  é o que torna o relatório comparável entre projetos.

## Rodapé opcional

Após o `Total`, pode-se incluir uma linha indicando o plano de refatoração e a
pergunta de confirmação (fora do arquivo salvo, no chat):

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
