# refactor-arch Skill

Esta skill automatiza a análise, auditoria e refatoração de projetos legados para o padrão MVC.

## Objetivo
- Detectar linguagem, framework, arquitetura e domínio do projeto.
- Identificar anti-patterns e code smells com severidade e localização exata.
- Gerar um relatório de auditoria estruturado.
- Refatorar o projeto para uma arquitetura MVC clara.
- Validar que a aplicação inicia e mantém os endpoints originais.

## Como usar
1. Execute a skill no diretório do projeto.
2. A skill faz 3 fases sequenciais.
3. A Fase 2 pausa para confirmação antes de qualquer modificação.
4. A Fase 3 aplica refatorações e validações.

## Fase 1 — Análise
1. Identifique a linguagem principal do projeto.
2. Detecte framework e bibliotecas principais.
3. Liste todos os arquivos de código fonte relevantes.
4. Mapeie a arquitetura atual: monolito, camadas parciais, modelo MVC, etc.
5. Detecte banco de dados e método de persistência.
6. Produza um resumo com:
   - Language
   - Framework
   - Dependencies
   - Domain
   - Architecture
   - Source files analyzed
   - DB tables/entities

Use `project-analysis-guidelines.md` para as heurísticas de identificação.

## Fase 2 — Auditoria
1. Use `antipattern-catalog.md` para detectar anti-patterns, vulnerabilidades e APIs deprecated.
2. Gere um relatório seguindo o template em `audit-report-template.md`.
3. O relatório deve conter:
   - Summary por severidade
   - Findings com:
     - severidade
     - arquivo e linhas exatas
     - descrição
     - impacto
     - recomendação
4. Ordene findings de CRITICAL para LOW.
5. Inclua pelo menos 5 findings, com ao menos 1 HIGH ou CRITICAL.
6. Pare e peça confirmação antes de executar a Fase 3.

A resposta da Fase 2 deve terminar com:

> Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

## Fase 3 — Refatoração
1. Use `mvc-guidelines.md` como base para reestruturar o projeto.
2. Use `refactor-playbook.md` para aplicar transformações concretas por anti-pattern.
3. Gere uma nova estrutura consistente com:
   - config/settings
   - models/
   - controllers/
   - views/routes/
   - middlewares/ (tratamento de erros, validação)
   - entrypoint claro (app.js, server.js, main.py)
4. Extraia configurações hardcoded para arquivos de config.
5. Separe responsabilidades:
   - Models: abstração de dados e persistência
   - Controllers: fluxo de aplicação e orquestração
   - Routes: expor endpoints e delegar ao controller
   - Middlewares: validação, erros e segurança
6. Remova endpoints inseguros ou debug/backdoor quando não fizerem parte do domínio da API.
7. Substitua SQL construído por concatenação por queries parametrizadas ou ORM.
8. Remova APIs deprecated e recomende equivalentes modernos.

## Validação
1. A aplicação deve bootar sem erros.
2. Verifique pelo menos um endpoint original.
3. Confirme a estrutura de diretórios e a ausência de anti-patterns críticos.
4. A skill deve descrever as mudanças realizadas e os arquivos alterados.

## Regras Gerais
- Seja agnóstico de tecnologia. A skill deve funcionar para Python/Flask e Node.js/Express.
- Não modifique nada antes da confirmação da Fase 2.
- Use os arquivos de referência para todas as decisões.
- Priorize segurança, separação de responsabilidades e manutenção.
- Se não for possível validar a aplicação completamente, explique claramente o motivo no final.

## Regra de Ouro (Fase 3 vs Fase 2)
- **TODA** falha ou vulnerabilidade apontada no relatório da Fase 2, incluindo achados em scripts de mock, seeds ou tokens falsos (Fake JWT), **DEVE** ser ativamente corrigida no código durante a Fase 3.
- Não deixe pendências descritas no relatório vazarem para o código final. Verifique duplamente: senhas no banco (seeds inclusive) e tokens (devem ser JWTs assinados de verdade, não placeholders).
