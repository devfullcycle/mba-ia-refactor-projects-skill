# Template do Relatório de Auditoria de Arquitetura

O relatório gerado ao final da **Fase 2 — Auditoria** deve seguir rigorosamente a estrutura textual definida abaixo.

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: [NOME_DO_PROJETO]
Stack:   [LINGUAGEM] + [FRAMEWORK]
Files:   [NUMERO] analyzed | ~[LINHAS] lines of code

## Summary
CRITICAL: [N] | HIGH: [N] | MEDIUM: [N] | LOW: [N]

## Findings

### [[GRAVIDADE]] [Nome do Anti-pattern ou Code Smell]
- **File:** [caminho_do_arquivo]:[linha_inicio]-[linha_fim]
- **Description:** [Descrição sucinta de onde e por que ocorre o problema]
- **Impact:** [O impacto desse problema na segurança, performance, confiabilidade ou legibilidade]
- **Recommendation:** [Recomendação precisa de como refatorar]

[Adicione quantos Findings forem encontrados, sempre ordenados por gravidade decrescente: CRITICAL -> HIGH -> MEDIUM -> LOW]

================================
Total: [TOTAL] findings
================================
```

## Diretrizes de Formatação:
1. O cabeçalho e rodapé decorados com `====` devem ser impressos exatamente como no exemplo.
2. Os Findings devem ser listados em ordem de gravidade: primeiro todos os `CRITICAL`, depois todos os `HIGH`, depois `MEDIUM` e finalmente `LOW`.
3. Os caminhos de arquivos devem ser relativos à raiz do projeto analisado (ex: `src/utils.js` em vez de caminhos absolutos).
4. O total de findings deve corresponder exatamente à soma de todas as severidades do sumário.
