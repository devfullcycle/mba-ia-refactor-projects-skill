# Planejamento — Skill de Auditoria e Refatoração Arquitetural

## Pré-requisitos
- [x] Claude Code instalado e configurado (ferramenta do desafio)

## Status
- [x] Etapa 1: Análise manual (3 projetos)
- [x] Etapa 2: Criação da skill
- [x] Etapa 3: Execução projeto 1 (code-smells-project)
- [ ] Etapa 4: Execução projeto 2 (ecommerce-api-legacy)
- [x] Etapa 5: Execução projeto 3 (task-manager-api)
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
- [x] cd code-smells-project
- [x] claude "/refactor-arch"

### Validação Fase 1
- [x] Linguagem detectada: Python ✓
- [x] Framework detectado: Flask ✓
- [x] Domínio descrito corretamente (E-commerce) ✓
- [x] Número de arquivos analisados correto ✓

### Validação Fase 2
- [x] Relatório segue template definido ✓
- [x] >= 5 findings encontrados ✓
- [x] >= 1 CRITICAL ou HIGH identificado ✓
- [x] Findings ordenados por severidade (CRITICAL → LOW) ✓
- [x] Cada finding tem arquivo e linhas exatas ✓
- [x] Detecção de APIs deprecated incluída (se aplicável) ✓
- [x] Skill pausa e pede confirmação explícita ✓

### Validação Fase 3
- [x] Estrutura de diretórios segue padrão MVC ✓
- [x] Configuração extraída para módulo de config (sem hardcoded) ✓
- [x] Models criados para abstrair dados ✓
- [x] Views/Routes separadas ✓
- [x] Controllers concentram fluxo da aplicação ✓
- [x] Error handling centralizado ✓
- [x] Entry point claro ✓
- [x] Aplicação inicia sem erros ✓
- [x] Endpoints originais respondem corretamente ✓

### Pós-execução
- [x] Salvar reports/audit-project-1.md
- [x] git commit

## Etapa 4 — Projeto 2 (ecommerce-api-legacy)
### Execução
- [x] Copiar .claude/skills/refactor-arch/ para ecommerce-api-legacy/.claude/skills/
- [x] cd ../ecommerce-api-legacy
- [x] claude "/refactor-arch"

### Validação Fase 1
- [x] Linguagem detectada: Node.js ✓
- [x] Framework detectado: Express ✓
- [x] Domínio descrito corretamente (LMS com checkout) ✓
- [x] Número de arquivos analisados correto ✓

### Validação Fase 2
- [x] Relatório segue template definido ✓
- [x] >= 5 findings encontrados ✓ (17 findings)
- [x] >= 1 CRITICAL ou HIGH identificado ✓ (4 CRITICAL, 5 HIGH)
- [x] Findings ordenados por severidade (CRITICAL → LOW) ✓
- [x] Cada finding tem arquivo e linhas exatas ✓
- [x] Detecção de APIs deprecated incluída (se aplicável) ✓ (sqlite3 callbacks)
- [x] Skill pausa e pede confirmação explícita ✓

### Validação Fase 3
- [x] Estrutura de diretórios segue padrão MVC ✓
- [x] Configuração extraída para módulo de config (sem hardcoded) ✓
- [x] Models criados para abstrair dados ✓
- [x] Views/Routes separadas ✓
- [x] Controllers concentram fluxo da aplicação ✓
- [x] Error handling centralizado ✓
- [x] Entry point claro ✓
- [x] Aplicação inicia sem erros ✓
- [x] Endpoints originais respondem corretamente ✓

### Pós-execução
- [x] Salvar reports/audit-project-2.md
- [x] git commit

## Etapa 5 — Projeto 3 (task-manager-api)
### Execução
- [x] Copiar .claude/skills/refactor-arch/ para task-manager-api/.claude/skills/
- [x] cd ../task-manager-api
- [x] claude "/refactor-arch"

### Validação Fase 1
- [x] Linguagem detectada: Python ✓
- [x] Framework detectado: Flask ✓
- [x] Domínio descrito corretamente (Task Manager) ✓
- [x] Número de arquivos analisados correto ✓
- [x] Arquitetura parcialmente organizada detectada corretamente ✓

### Validação Fase 2
- [x] Relatório segue template definido ✓
- [x] >= 5 findings encontrados (mesmo em código parcialmente organizado) ✓ — 11 findings (2 CRITICAL, 1 HIGH, 4 MEDIUM, 4 LOW)
- [x] >= 1 CRITICAL ou HIGH identificado ✓
- [x] Findings ordenados por severidade (CRITICAL → LOW) ✓
- [x] Cada finding tem arquivo e linhas exatas ✓
- [x] Detecção de APIs deprecated incluída (se aplicável) ✓ — MD5 para senha, datetime.utcnow()
- [x] Skill pausa e pede confirmação explícita ✓

### Validação Fase 3
- [x] Estrutura de diretórios melhorada mantendo organização existente ✓ — models/, routes/, services/, utils/ preservados; adicionados config/ e middlewares/
- [x] Configuração extraída para módulo de config (sem hardcoded) ✓ — config/settings.py
- [x] Models separados e sem lógica de negócio extra ✓
- [x] Routes limpas, sem lógica de negócio ✓ — overdue delegado a Task.is_overdue()
- [x] Controllers consolidam fluxo da aplicação ✓ — handlers dos blueprints atuam como controllers (idiomático em Flask), sem SQL/regra de negócio direto
- [x] Services com responsabilidades bem definidas ✓ — notification_service usa config, sem credenciais hardcoded
- [x] Error handling centralizado ✓ — middlewares/error_handler.py
- [x] Entry point claro ✓ — app.py
- [x] Aplicação inicia sem erros ✓
- [x] Endpoints originais respondem corretamente ✓ — validado com curl (health, /, tasks CRUD+search+stats, users CRUD, login, users/:id/tasks, reports/summary, reports/user/:id, categories CRUD)

### Pós-execução
- [x] Salvar reports/audit-project-3.md
- [x] git commit

## Etapa 6 — README.md final
Seções obrigatórias:
- [x] Análise Manual
- [x] Construção da Skill
- [x] Resultados (antes/depois, checklist, prints/logs)
- [x] Como Executar

## Etapa 7 — Entrega
- [ ] Repositório público no GitHub (fork)
- [ ] git push origin main
