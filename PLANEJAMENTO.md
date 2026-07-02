# Planejamento — Skill de Auditoria e Refatoração Arquitetural

## Pré-requisitos
- [x] Claude Code instalado e configurado (ferramenta do desafio)

## Status
- [x] Etapa 1: Análise manual (3 projetos)
- [x] Etapa 2: Criação da skill
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
- [x] code-smells-project (Python/Flask) — 9 achados (3 CRITICAL, 2 HIGH, 2 MEDIUM, 2 LOW)
- [x] ecommerce-api-legacy (Node.js/Express) — 9 achados (2 CRITICAL, 3 HIGH, 2 MEDIUM, 2 LOW)
- [x] task-manager-api (Python/Flask) — 9 achados (3 CRITICAL, 2 HIGH, 2 MEDIUM, 2 LOW)

Achados documentados em [README.md](README.md#análise-manual).

## Etapa 2 — Skill (dentro de code-smells-project/.claude/skills/refactor-arch/)
Arquivos obrigatórios:
- [x] SKILL.md (3 fases: análise, auditoria, refatoração)
- [x] references/project-analysis.md (heurísticas de detecção de linguagem/framework/DB)
- [x] references/anti-patterns-catalog.md (19 anti-patterns + seção de APIs deprecated)
- [x] references/report-template.md
- [x] references/architecture-guidelines.md (regras MVC)
- [x] references/refactoring-playbook.md (14 transformações, com exemplo antes/depois)

## Etapa 3 — Projeto 1 (code-smells-project)
### Execução
- [ ] cd code-smells-project
- [ ] claude "/refactor-arch"

### Validação Fase 1
- [ ] Linguagem detectada: Python ✓
- [ ] Framework detectado: Flask ✓
- [ ] Domínio descrito corretamente (E-commerce) ✓
- [ ] Número de arquivos analisados correto ✓

### Validação Fase 2
- [ ] Relatório segue template definido ✓
- [ ] >= 5 findings encontrados ✓
- [ ] >= 1 CRITICAL ou HIGH identificado ✓
- [ ] Findings ordenados por severidade (CRITICAL → LOW) ✓
- [ ] Cada finding tem arquivo e linhas exatas ✓
- [ ] Detecção de APIs deprecated incluída (se aplicável) ✓
- [ ] Skill pausa e pede confirmação explícita ✓

### Validação Fase 3
- [ ] Estrutura de diretórios segue padrão MVC ✓
- [ ] Configuração extraída para módulo de config (sem hardcoded) ✓
- [ ] Models criados para abstrair dados ✓
- [ ] Views/Routes separadas ✓
- [ ] Controllers concentram fluxo da aplicação ✓
- [ ] Error handling centralizado ✓
- [ ] Entry point claro ✓
- [ ] Aplicação inicia sem erros ✓
- [ ] Endpoints originais respondem corretamente ✓

### Pós-execução
- [ ] Salvar reports/audit-project-1.md
- [ ] git commit

## Etapa 4 — Projeto 2 (ecommerce-api-legacy)
### Execução
- [ ] Copiar .claude/skills/refactor-arch/ para ecommerce-api-legacy/.claude/skills/
- [ ] cd ../ecommerce-api-legacy
- [ ] claude "/refactor-arch"

### Validação Fase 1
- [ ] Linguagem detectada: Node.js ✓
- [ ] Framework detectado: Express ✓
- [ ] Domínio descrito corretamente (LMS com checkout) ✓
- [ ] Número de arquivos analisados correto ✓

### Validação Fase 2
- [ ] Relatório segue template definido ✓
- [ ] >= 5 findings encontrados ✓
- [ ] >= 1 CRITICAL ou HIGH identificado ✓
- [ ] Findings ordenados por severidade (CRITICAL → LOW) ✓
- [ ] Cada finding tem arquivo e linhas exatas ✓
- [ ] Detecção de APIs deprecated incluída (se aplicável) ✓
- [ ] Skill pausa e pede confirmação explícita ✓

### Validação Fase 3
- [ ] Estrutura de diretórios segue padrão MVC ✓
- [ ] Configuração extraída para módulo de config (sem hardcoded) ✓
- [ ] Models criados para abstrair dados ✓
- [ ] Views/Routes separadas ✓
- [ ] Controllers concentram fluxo da aplicação ✓
- [ ] Error handling centralizado ✓
- [ ] Entry point claro ✓
- [ ] Aplicação inicia sem erros ✓
- [ ] Endpoints originais respondem corretamente ✓

### Pós-execução
- [ ] Salvar reports/audit-project-2.md
- [ ] git commit

## Etapa 5 — Projeto 3 (task-manager-api)
### Execução
- [ ] Copiar .claude/skills/refactor-arch/ para task-manager-api/.claude/skills/
- [ ] cd ../task-manager-api
- [ ] claude "/refactor-arch"

### Validação Fase 1
- [ ] Linguagem detectada: Python ✓
- [ ] Framework detectado: Flask ✓
- [ ] Domínio descrito corretamente (Task Manager) ✓
- [ ] Número de arquivos analisados correto ✓
- [ ] Arquitetura parcialmente organizada detectada corretamente ✓

### Validação Fase 2
- [ ] Relatório segue template definido ✓
- [ ] >= 5 findings encontrados (mesmo em código parcialmente organizado) ✓
- [ ] >= 1 CRITICAL ou HIGH identificado ✓
- [ ] Findings ordenados por severidade (CRITICAL → LOW) ✓
- [ ] Cada finding tem arquivo e linhas exatas ✓
- [ ] Detecção de APIs deprecated incluída (se aplicável) ✓
- [ ] Skill pausa e pede confirmação explícita ✓

### Validação Fase 3
- [ ] Estrutura de diretórios melhorada mantendo organização existente ✓
- [ ] Configuração extraída para módulo de config (sem hardcoded) ✓
- [ ] Models separados e sem lógica de negócio extra ✓
- [ ] Routes limpas, sem lógica de negócio ✓
- [ ] Controllers consolidam fluxo da aplicação ✓
- [ ] Services com responsabilidades bem definidas ✓
- [ ] Error handling centralizado ✓
- [ ] Entry point claro ✓
- [ ] Aplicação inicia sem erros ✓
- [ ] Endpoints originais respondem corretamente ✓

### Pós-execução
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
