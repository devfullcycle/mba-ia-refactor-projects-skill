# Audit Report Template

Use EXATAMENTE este formato para gerar o relatorio da Fase 2.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do projeto>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<M> lines of code

## Summary
CRITICAL: <count> | HIGH: <count> | MEDIUM: <count> | LOW: <count>

## Findings

### [CRITICAL] <Nome do Anti-Pattern>
File: <caminho/do/arquivo>:<linha-inicio>-<linha-fim>
Description: <descricao especifica do problema, citando o codigo real>
Impact: <impacto pratico no sistema>
Recommendation: <recomendacao concreta para resolver>

### [CRITICAL] <Nome do Anti-Pattern>
File: <arquivo>:<linha>
Description: <descricao>
Impact: <impacto>
Recommendation: <recomendacao>

### [HIGH] <Nome do Anti-Pattern>
File: <arquivo>:<linha>
Description: <descricao>
Impact: <impacto>
Recommendation: <recomendacao>

### [MEDIUM] <Nome do Anti-Pattern>
File: <arquivo>:<linha>
Description: <descricao>
Impact: <impacto>
Recommendation: <recomendacao>

### [LOW] <Nome do Anti-Pattern>
File: <arquivo>:<linha>
Description: <descricao>
Impact: <impacto>
Recommendation: <recomendacao>

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Regras do Relatorio

1. **Ordem por severidade:** CRITICAL primeiro, depois HIGH, MEDIUM, LOW
2. **Dentro da mesma severidade:** ordenar por impacto (mais impactante primeiro)
3. **Todo finding DEVE ter:** caminho exato do arquivo e numero(s) da linha
4. **Descricao especifica:** cite o codigo real encontrado, nao use descricoes genericas
5. **Impacto concreto:** explique consequencias reais, nao teoricas
6. **Recomendacao acionavel:** aponte a solucao especifica
7. **Incluir deprecated APIs** quando detectado
8. **Counts devem bater:** os totais no Summary devem corresponder aos findings listados
9. **Sempre terminar com o prompt de confirmacao** antes da Fase 3
