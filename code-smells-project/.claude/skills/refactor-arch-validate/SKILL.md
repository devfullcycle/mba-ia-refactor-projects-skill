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
- [ ] **Auth default deny** - Rotas de escrita exigem credencial por padrão; a proteção não depende de flag opt-in
- [ ] **Autorização por papel** - Rotas administrativas exigem `admin`; identidade, papel e posse vêm do token, nunca do body
- [ ] **Hash em repouso** - Seed/banco usam hash com salt; login sem fallback de comparação em texto puro

## Passo 3 — Verificação dinâmica (Smoke Test)
1. **Subir/verificar** a aplicação com o comando de boot identificado, usando a **configuração padrão** do projeto (`.env.example` ou default de `Config`). Não habilite flags especiais para provar uma correção.
2. **Exercitar TODAS** as rotas inventariadas em `analysis-*.md` (método + path).
3. **Validar contrato** - Manter path, verbo e formato de resposta o mais próximo possível do original.
4. **Observar erros** - Registrar status codes, erros 500 inesperados, falhas de inicialização.
5. **Seguir princípio**: Validar que **continua funcionando como antes**. Melhorias arquiteturais não devem ser tratadas como falhas se o contrato for preservado.

## Passo 4 — Cruzamento com auditoria (gate bloqueante)
Para **todos** os achados CRITICAL e HIGH do `audit-*.md`, valide com a **configuração padrão do projeto** e classifique estritamente:
- `RESOLVIDO` — somente com evidência estática **e** dinâmica (arquivo:linha + teste/comando/HTTP).
- `PARCIAL` — **falha** (não é aprovação).
- `NÃO RESOLVIDO` — **falha**.
- Justificar com evidência concreta.

Verificações específicas obrigatórias:
- **SEC-04:** `401` sem token, `403` com papel insuficiente, `200/201` com papel correto; gestão de usuários só com `admin`.
- **SEC-03:** consultar banco/seed e provar que não há senha em texto puro; testar login; provar que não existe fallback de comparação plaintext.
- **SEC-02:** grep por segredos + boot com a configuração padrão.
- **SEC-06:** logs sem dados sensíveis (sem senha, token ou PII).

**Gate bloqueante:** se **qualquer** CRITICAL/HIGH estiver `PARCIAL` ou `NÃO RESOLVIDO`:
- status geral = `FAIL`;
- recomendação = `REPROVADO - AÇÃO NECESSÁRIA`;
- fluxo **não concluído**;
- listar ações objetivas para retornar à Fase 3.

`APROVADO COM RESSALVAS` só pode existir para achados MEDIUM/LOW; **nunca** para CRITICAL/HIGH.

Achados MEDIUM/LOW podem ser avaliados, mas **não bloqueiam** a aprovação, devendo ser reportados.

## Passo 5 — Emitir relatório
Gerar `reports/validation-<nome-do-projeto>.md` com:

### Estrutura obrigatória
1. **Resumo** - Status geral (`PASS`/`VALIDATED` ou `FAIL`/`VALIDATION FAILED`), rotas OK/FAIL, críticos/altos resolvidos e `Partial critical/high: N` (deve ser `0`)
2. **Contrato original vs atual** - Comparação com inventário de rotas do `analysis-*.md`
3. **Smoke test por endpoint** - Tabela com: Método, Path, Status obtido, Resultado (PASS/FAIL/WARN), Observação, Evidência
4. **Verificação estática** - Checklist com evidências
5. **Cruzamento com auditoria (CRITICAL/HIGH)** - Tabela detalhada por achado, com evidência estática e dinâmica
6. **Riscos e ressalvas** - Falhas não bloqueantes, dependências, limitações (apenas MEDIUM/LOW)
7. **Recomendação final** - `APROVADO` | `APROVADO COM RESSALVAS` (somente MEDIUM/LOW) | `REPROVADO - AÇÃO NECESSÁRIA`, com lista objetiva de ações
8. **Ações para retorno à Fase 3** - Obrigatório quando houver CRITICAL/HIGH `PARCIAL`/`NÃO RESOLVIDO`; lista objetiva por achado
9. **Notas e evidências** - Comandos executados, logs relevantes

**Bloco de resumo no terminal:**
```
================================
PHASE 4: VALIDATION
================================
Project:               <projeto>
Routes tested:         N/N
Routes passed:         X (Y%)
Critical resolved:     A/B
High resolved:         C/D
Partial critical/high: N
Static checks:         OK/PARTIAL/FAIL
Status:                VALIDATED / VALIDATED WITH RESERVES / VALIDATION FAILED
Recommendation:        APROVADO / APROVADO COM RESSALVAS / REPROVADO - AÇÃO NECESSÁRIA
================================
```

Se `Partial critical/high > 0`, o status **deve** ser `VALIDATION FAILED` e a recomendação **deve** ser `REPROVADO - AÇÃO NECESSÁRIA`. Nunca `VALIDATED`.

## Regras
- **Somente verificação**. **NUNCA** editar, mover, deletar ou criar arquivos de código-fonte.
- **Baseado no contrato original**. Comparar com `analysis-*.md`, não com suposições.
- **Evidência obrigatória** para toda falha.
- **Foco em regressão**. Priorizar boot, rotas existentes e resolução de CRITICAL/HIGH.
- **Não inflar severidade**. Distinguir quebra funcional (`FAIL`) de sugestão (`WARN`).
- **Não auto-corrigir**. Caso haja falhas críticas, reportar e sugerir retorno pontual à Fase 3.
- **Agnóstico de tecnologia**.
- **Gate bloqueante**. `PARCIAL` ou `NÃO RESOLVIDO` em CRITICAL/HIGH reprova automaticamente o fluxo.
- **Validação com configuração padrão**. Provar a correção com o default do projeto/`.env.example`, não com flag especial.
- **Conclusão**. Só considerar fluxo concluído com este relatório em `PASS`/`VALIDATED`, recomendação `APROVADO` e `Partial critical/high: 0`.
