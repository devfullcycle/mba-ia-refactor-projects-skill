# Planejamento — Skill de Auditoria e Refatoração Arquitetural

## Status
- [ ] Etapa 1: Análise manual (3 projetos)
- [ ] Etapa 2: Criação da skill
- [ ] Etapa 3: Execução projeto 1 (code-smells-project)
- [ ] Etapa 4: Execução projeto 2 (ecommerce-api-legacy)
- [ ] Etapa 5: Execução projeto 3 (task-manager-api)
- [ ] Etapa 6: README final
- [ ] Etapa 7: Push no fork

## Etapa 1 — Análise Manual
Para cada projeto, mínimo 5 problemas:
- 1 CRITICAL ou HIGH
- 2 MEDIUM
- 2 LOW

Projetos:
- [ ] code-smells-project (Python/Flask)
- [ ] ecommerce-api-legacy (Node.js/Express)
- [ ] task-manager-api (Python/Flask)

## Etapa 2 — Skill (dentro de code-smells-project/.claude/skills/refactor-arch/)
Arquivos obrigatórios:
- [ ] SKILL.md (3 fases: análise, auditoria, refatoração)
- [ ] project-analysis.md (heurísticas de detecção de linguagem/framework/DB)
- [ ] anti-patterns-catalog.md (mínimo 8, com severidade + APIs deprecated)
- [ ] report-template.md
- [ ] architecture-guidelines.md (regras MVC)
- [ ] refactoring-playbook.md (mínimo 8 transformações, com exemplo antes/depois)

## Etapa 3 — Projeto 1
- [ ] claude "/refactor-arch"
- [ ] Fase 1 detecta stack corretamente
- [ ] Fase 2 encontra >= 5 findings, com pelo menos 1 CRITICAL/HIGH
- [ ] Fase 2 pausa pedindo confirmação
- [ ] Fase 3 gera estrutura MVC e app sobe sem erro
- [ ] Salvar reports/audit-project-1.md
- [ ] git commit

## Etapa 4 — Projeto 2
- [ ] Copiar .claude/skills/refactor-arch/ para ecommerce-api-legacy/
- [ ] claude "/refactor-arch"
- [ ] Salvar reports/audit-project-2.md
- [ ] git commit

## Etapa 5 — Projeto 3
- [ ] Copiar .claude/skills/refactor-arch/ para task-manager-api/
- [ ] claude "/refactor-arch"
- [ ] Salvar reports/audit-project-3.md
- [ ] git commit

## Etapa 6 — README.md final
Seções obrigatórias:
- [ ] Análise Manual
- [ ] Construção da Skill
- [ ] Resultados (antes/depois, checklist, prints/logs)
- [ ] Como Executar

## Etapa 7 — Entrega
- [ ] Repositório público no GitHub (fork)
- [ ] git push origin main
