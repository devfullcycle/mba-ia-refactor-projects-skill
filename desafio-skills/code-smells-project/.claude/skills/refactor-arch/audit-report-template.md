# Template — relatório de auditoria (Fase 2)

Copie a estrutura abaixo. Substitua os placeholders. **Ordene findings: CRITICAL → HIGH → MEDIUM → LOW.**

---

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta ou serviço>
Stack:   <Language + Framework>
Files:   <N> analyzed | ~<linhas> LOC (opcional)

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <título curto>
File: <path>:<start>-<end>
Description: ...
Impact: ...
Recommendation: ...

### [HIGH] <título curto>
File: <path>:<start>-<end>
Description: ...
Impact: ...
Recommendation: ...

### [MEDIUM] ...
### [LOW] ...

================================
Total: <N> findings
================================
```

## Regras

1. Todo finding **deve** ter intervalo de linhas ou linha única (`file.py:42`).
2. **Sem** findings genéricos sem âncora no código.
3. Se “APIs deprecated” não se aplicar, um único finding pode documentar **N/A** com o que foi verificado (grep, docs consultadas).
