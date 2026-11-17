# Template Padronizado de Relatório de Auditoria (Fase 2)

Este documento estabelece a estrutura rigorosa que a Fase 2 (Auditoria) da skill `refactor-arch` deve gerar e exibir para o usuário, bem como salvar no arquivo correspondente em `reports/audit-project-<ID>.md`.

---

## Formato do Relatório

Todo relatório de auditoria gerado deve seguir fielmente o seguinte padrão Markdown:

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome-do-projeto>
Stack:   <Linguagem> + <Framework>
Files:   <X> analyzed | ~<Y> lines of code

## Summary
CRITICAL: <C> | HIGH: <H> | MEDIUM: <M> | LOW: <L>

## Findings

### [<SEVERITY>] <Nome do Anti-Pattern>
File: <caminho_do_arquivo>:<linha_inicio>-<linha_fim>
Description: <Descrição clara e objetiva do problema encontrado no código.>
Impact: <Impacto arquitetural, de segurança, de desempenho ou manutenibilidade.>
Recommendation: <Ação corretiva concreta a ser executada na Fase 3.>

[... repetir para cada finding ordenado obrigatoriamente por severidade: CRITICAL -> HIGH -> MEDIUM -> LOW ...]

================================
Total: <Total> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

---

## Regras de Preenchimento Obrigatórias

1. **Ordenação Decrescente de Severidade**:
   - Primeiro todos os findings **CRITICAL**
   - Depois todos os findings **HIGH**
   - Depois todos os findings **MEDIUM**
   - Por fim todos os findings **LOW**

2. **Precisão de Arquivo e Linhas**:
   - O campo `File:` deve apontar para o arquivo real e o intervalo de linhas exato onde a anomalia reside (ex.: `models.py:48-52` ou `src/utils.js:1-7`).

3. **Mínimo de Findings**:
   - O relatório deve conter **no mínimo 5 findings**, garantindo pelo menos 1 de severidade `CRITICAL` ou `HIGH`.

4. **Pausa para Confirmação Humana**:
   - A skill **NUNCA** deve iniciar a Fase 3 automaticamente. Ela deve imprimir a pergunta final:
     `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`
     e aguardar a resposta explícita do usuário antes de criar ou modificar qualquer arquivo.
