---
name: refactor-arch-validate
description: Fase 4 - Validação Pós-Refatoração. Verifica regressão total, estrutura alvo, cruzamento com auditoria e contrato original sem modificar código-fonte.
---

# refactor-arch-validate — Fase 4 (Validação Pós-Refatoração)

Objetivo: realizar uma **validação de aceitação** após a Fase 3. Garantir que a aplicação continua funcionando em relação ao contrato original, que a estrutura alvo foi aplicada e que os achados CRITICAL/HIGH foram efetivamente corrigidos. **Somente verificação, nunca correção.**

## Pré-requisitos OBRIGATÓRIOS
1. `reports/analysis-<nome-do-projeto>.md` existente (contrato original: rotas, verbos, entrypoint, stack)
2. `reports/audit-<nome-do-projeto>.md` existente (achados e severidade)
3. `reports/refactor-<nome-do-projeto>.md` existente (mudanças realizadas)

**Se algum pré-requisito não for atendido → NÃO iniciar.** Solicitar ao orquestrador que complete as fases anteriores.

## Referências a ler
Leia integralmente antes de aplicar:
- `../refactor-arch/references/mvc-guidelines.md` (seção 6 - checklist de validação)
- `../refactor-arch/references/report-template.md` (estilo de relatório)

## Passo 1 — Preparar
1. Ler os 3 relatórios acima.
2. Extrair: inventário de rotas/verbos do `analysis-*.md`, lista de achados CRITICAL/HIGH do `audit-*.md`, resumo de mudanças e arquivos antes/depois do `refactor-*.md`.
3. Identificar comando de boot e entrypoint a partir do `analysis-*.md`.

## Passo 2 — Verificação estática
Validar:
- [ ] **Estrutura alvo** - Presença das camadas esperadas conforme arquitetura definida (routes/controllers/services/repositories/models/middleware/config conforme mapeamento por ecossistema)
- [ ] **Rotas separadas** - Registro de rotas isolado do entrypoint (não centralizado com boot/config inline)
- [ ] **Responsabilidades** - Controllers orquestram (sem SQL direto / regra de negócio pesada). Services com regras de negócio. Repositories com acesso a dados.
- [ ] **Queries parametrizadas** - Ausência de concatenação/f-string/interpolação em chamadas SQL
- [ ] **Segredos** - Ausência de credenciais/tokens/chaves hardcoded
- [ ] **Arquivos órfãos** - Verificar se arquivos antigos removidos não possuem imports remanescentes
- [ ] **Configuração** - Config centralizada via ambiente quando aplicável

## Passo 3 — Verificação dinâmica (Smoke Test)
1. **Subir/verificar** a aplicação com o comando de boot identificado.
2. **Exercitar TODAS** as rotas inventariadas em `analysis-*.md` (método + path).
3. **Validar contrato** - Manter path, verbo e formato de resposta o mais próximo possível do original. 
4. **Observar erros** - Registrar status codes, erros 500 inesperados, falhas de inicialização.
5. **Seguir princípio**: Validar que **continua funcionando como antes**. Melhorias arquiteturais não devem ser tratadas como falhas se o contrato for preservado.

## Passo 4 — Cruzamento com auditoria
Para **todos** os achados CRITICAL e HIGH do `audit-*.md`:
- Verificar efetiva resolução com evidência (arquivo:linha ou comportamento)
- Classificar: `RESOLVIDO` / `PARCIAL` / `NÃO RESOLVIDO`
- Justificar com evidência concreta

Achados MEDIUM/LOW podem ser avaliados, mas **não bloqueiam** a aprovação, devendo ser reportados.

## Passo 5 — Emitir relatório
Gerar `reports/validation-<nome-do-projeto>.md` com:

### Estrutura obrigatória
1. **Resumo** - Status geral (`PASS` / `PARTIAL` / `FAIL`), rotas OK/FAIL, críticos resolvidos/não resolvidos
2. **Contrato original vs atual** - Comparação com inventário de rotas do `analysis-*.md`
3. **Smoke test por endpoint** - Tabela com: Método, Path, Status obtido, Resultado (PASS/FAIL/WARN), Observação, Evidência
4. **Verificação estática** - Checklist com evidências
5. **Cruzamento com auditoria (CRITICAL/HIGH)** - Tabela detalhada por achado
6. **Riscos e ressalvas** - Falhas não bloqueantes, dependências, limitações
7. **Recomendação final** - `APROVADO` | `APROVADO COM RESSALVAS` | `REPROVADO - AÇÃO NECESSÁRIA` com lista objetiva de ações
8. **Notas e evidências** - Comandos executados, logs relevantes

**Bloco de resumo no terminal:**
```
================================
PHASE 4: VALIDATION
================================
Project:            <projeto>
Routes tested:      N/N
Routes passed:      X (Y%)
Critical resolved:  A/B
High resolved:      C/D
Static checks:      OK/PARTIAL/FAIL
Status:             VALIDATED / VALIDATION FAILED / VALIDATED WITH RESERVES
Recommendation:     APPROVED / APPROVED WITH RESERVES / REJECTED
================================
```

## Regras
- **Somente verificação**. **NUNCA** editar, mover, deletar ou criar arquivos de código-fonte.
- **Baseado no contrato original**. Comparar com `analysis-*.md`, não com suposições.
- **Evidência obrigatória** para toda falha.
- **Foco em regressão**. Priorizar boot, rotas existentes e resolução de CRITICAL/HIGH.
- **Não inflar severidade**. Distinguir quebra funcional (`FAIL`) de sugestão (`WARN`).
- **Não auto-corrigir**. Caso haja falhas críticas, reportar e sugerir retorno pontual à Fase 3.
- **Agnóstico de tecnologia**.
- **Gateway de conclusão**. Só considerar fluxo concluído com este relatório e recomendação coerente.
