---
name: refactor-arch
description: Orquestra análise, auditoria, refatoração e validação pós-refatoração. Decide o próximo passo com base em relatórios existentes em reports/, impõe ordem e exige confirmação explícita para refatorações.
---

# refactor-arch — Orquestrador

Este skill **não executa diretamente** as fases. Ele roteia para sub-skills especializadas, valida pré-requisitos, garante a ordem correta e impõe os gates de segurança.

## Sub-skills disponíveis

| Sub-skill | Finalidade | Leitura/Escrita | Saída |
|---|---|---|---|
| `refactor-arch-analyze` | Fase 1 - Análise | Somente leitura + escrita de relatório | `reports/analysis-<projeto>.md` |
| `refactor-arch-audit` | Fase 2 - Auditoria | Somente leitura + escrita de relatório | `reports/audit-<projeto>.md` (pausa para confirmação) |
| `refactor-arch-refactor` | Fase 3 - Refatoração | Leitura + escrita de código (após confirmação) | `reports/refactor-<projeto>.md` + modificações no código |
| `refactor-arch-validate` | Fase 4 - Validação Pós-Refatoração | Leitura + verificação/smoke test (sem modificar código) | `reports/validation-<projeto>.md` (gate de conclusão) |

## Arquivos de referência compartilhados

Os templates e catálogos ficam centralizados aqui e são lidos pelos sub-skills:

| Arquivo | Uso |
|---|---|
| `references/stack-detection.md` | Detecção de stack (análise) |
| `references/architecture-detection.md` | Detecção de arquitetura (análise) |
| `references/report-template.md` | Template do relatório de análise |
| `references/anti-patterns.md` | Catálogo de anti-patterns (auditoria) |
| `references/audit-report-template.md` | Template do relatório de auditoria |
| `references/mvc-guidelines.md` | Diretrizes MVC (refatoração/validação) |
| `references/refactor-playbook.md` | Playbook de refatoração (refatoração) |

## Máquina de estados

1. **Sem análise** - Não existe `reports/analysis-*.md`. → Sugerir/carregar `refactor-arch-analyze`.
2. **Análise pronta, sem auditoria** - Existe `reports/analysis-*.md` mas não existe `reports/audit-*.md`. → Sugerir/carregar `refactor-arch-audit`.
3. **Análise + auditoria prontas, sem confirmação** - Existem ambos os relatórios. **Não iniciar refatoração.** Apresentar resumo da auditoria (lendo `reports/audit-<projeto>.md`) e perguntar explicitamente: *"Prosseguir com a refatoração (Fase 3)? Responda 'sim' para confirmar."* Só prossiga após confirmação inequívoca.
4. **Pronto para refatoração** - Existe análise + auditoria + confirmação explícita do usuário. → Carregar `refactor-arch-refactor`.
5. **Refatoração concluída, sem validação** - Existe `analysis-*.md`, `audit-*.md` e `refactor-*.md`, mas **não existe** `reports/validation-*.md`. → **Obrigatoriamente** sugerir/carregar `refactor-arch-validate`.
6. **Validado** - Existe `reports/validation-*.md`. Fluxo considerado **concluído**. Se a validação indicar falhas **CRÍTICAS** ou recomendação `REPROVADO - AÇÃO NECESSÁRIA`, o orquestrador **não** dará como finalizado e deverá propor um retorno pontual à Fase 3 ou correção manual. **Não auto-refatorar**.

## Regras do orquestrador

- **Ordem obrigatória**: Nunca pule fases. Sempre validate os pré-requisitos lendo a pasta `reports/`.
- **Separação de responsabilidades**: Fases 1 e 2 são read-only (apenas leitura e geração de relatórios). Fase 3 modifica código e só roda após confirmação. Fase 4 é **somente verificação** (leitura, boot, smoke test) sem modificação de código.
- **Gates rígidos**: A sub-skill `refactor-arch-refactor` deve ser carregada apenas quando os pré-requisitos forem atendidos e a confirmação estiver clara. A `refactor-arch-validate` só deve ser carregada após existência de `refactor-*.md`.
- **Validação como gate de conclusão**: O projeto só será considerado "refatorado e validado" após existir `validation-*.md` com análise coerente. Falhas críticas impedem a finalização.
- **Contexto limpo**: Ao iniciar uma fase, carregar a sub-skill correspondente via `skill` tool ao invés de embutir todas as instruções.
- **Evidência e agnosticismo**: Seguir as mesmas regras gerais de evidência e agnosticismo definidas nos sub-skills.
- **Baseado no contrato original**: A validação deve sempre partir do inventário de rotas presente em `analysis-*.md`.

## Fluxo de execução

1. Identificar o projeto (diretório de trabalho atual) e listar `reports/` existentes.
2. Determinar o estado conforme a máquina acima.
3. Se necessário, perguntar ao usuário qual fase deseja executar ou seguir a rota sugerida.
4. Carregar a sub-skill apropriada com `skill(id: "<sub-skill>")` passando o contexto necessário (caminho do projeto, relatórios existentes).
5. Após cada fase, reavaliar o estado e sugerir o próximo passo.
6. **Nunca** executar a Fase 3 sem confirmação explícita registrada no contexto da conversa.
7. **Obriga-se** a avançar para a Fase 4 assim que a Fase 3 for concluída e não existir `reports/validation-*.md`.
8. Só considerar o fluxo concluído após a Fase 4 com `reports/validation-*.md` gerado e avaliação coerente.