Skill de Auditoria e Refatoração Arquitetural
Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

Objetivo
Você deve entregar uma Skill capaz de:

Analisar uma codebase detectando linguagem, framework e arquitetura atual
Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
Gerar um relatório de auditoria estruturado com todos os achados
Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
Validar o resultado garantindo que a aplicação continua funcionando após as mudanças
A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

Contexto
Definição de Severidades
Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

CRITICAL: Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
HIGH: Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
MEDIUM: Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
LOW: Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.
Exemplo de Uso no CLI
# Executar a skill no projeto com problemas
cd code-smells-project
claude "/refactor-arch"
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

Findings

[CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL,
             validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

[CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
Tecnologias Obrigatórias
Ferramenta — uma das três opções abaixo (não são aceitas outras ferramentas):

Claude Code
Gemini CLI
OpenAI Codex
Recurso: Custom Skills (ou o equivalente na ferramenta escolhida)
Formato dos arquivos de referência: Markdown
Projetos-alvo: Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)
Nota: Os exemplos deste documento usam o Claude Code (.claude/skills/) como referência. Se você optar por Gemini CLI ou Codex, adapte o nome da pasta e o comando de invocação conforme a convenção dela — o conceito de skill e a estrutura interna (SKILL.md + arquivos de referência) permanecem os mesmos.

Requisitos
1. Análise Manual dos Projetos
Antes de criar a skill, você deve entender os problemas que ela vai resolver.

Tarefas:

Analisar o projeto code-smells-project/ (Python/Flask — API de E-commerce)
Analisar o projeto ecommerce-api-legacy/ (Node.js/Express — LMS API com fluxo de checkout)
Analisar o projeto task-manager-api/ (Python/Flask — API de Task Manager)
Para cada projeto, identificar e documentar no mínimo 5 problemas, incluindo pelo menos:

1 de severidade CRITICAL ou HIGH
2 de severidade MEDIUM
2 de severidade LOW
Documentar os achados na seção "Análise Manual" do seu README.md.

Dica: Não precisa encontrar todos os problemas — foque nos que têm maior impacto arquitetural.

Por que 3 projetos? Dois são Python/Flask (com níveis de organização diferentes) e um é Node.js/Express. Sua skill precisa funcionar nos 3 para provar que é verdadeiramente agnóstica de tecnologia.

2. Criação da Skill
Agora que você conhece os problemas, crie uma skill que os detecte, gere um relatório de auditoria e corrija automaticamente.

Criar a skill dentro do projeto code-smells-project/ e implementar o SKILL.md com 3 fases sequenciais:

Fase 1 — Análise: Detectar stack, mapear arquitetura atual, imprimir resumo
Fase 2 — Auditoria: Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
Fase 3 — Refatoração: Reestruturar para o padrão MVC, validar que funciona
Os arquivos de referência devem cobrir obrigatoriamente as seguintes áreas de conhecimento:

Análise de projeto: Heurísticas para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura
Catálogo de anti-patterns: Anti-patterns com sinais de detecção e classificação de severidade
Template de relatório: Formato padronizado do relatório de auditoria (Fase 2)
Guidelines de arquitetura: Regras do padrão MVC alvo (camadas Models, Views/Routes e Controllers)
Playbook de refatoração: Padrões concretos de transformação para cada anti-pattern (com exemplos de código)
Requisitos da skill:

Deve ser agnóstica de tecnologia — deve funcionar corretamente nos 3 projetos fornecidos
O catálogo de anti-patterns deve conter no mínimo 8 anti-patterns com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW)
O catálogo deve incluir detecção de APIs deprecated
O playbook deve ter no mínimo 8 padrões de transformação com exemplos de código antes/depois
A Fase 2 deve pausar e pedir confirmação antes de modificar qualquer arquivo
A Fase 3 deve validar o resultado (boot da aplicação + endpoints funcionando)
3. Execução da Skill
Projeto 1 — code-smells-project (Python/Flask)
claude "/refactor-arch"
Verificar que a Fase 1 detecta corretamente a stack e imprime o resumo
Verificar que a Fase 2 encontra no mínimo 5 dos problemas documentados na sua análise manual
Confirmar a execução da Fase 3
Verificar que a Fase 3 cria a estrutura MVC, a aplicação inicia sem erros e os endpoints originais continuam respondendo
Salvar o relatório de auditoria em reports/audit-project-1.md
Commitar o código refatorado no repositório
Projeto 2 — ecommerce-api-legacy (Node.js/Express)
cd ../ecommerce-api-legacy
claude "/refactor-arch"
Copiar a pasta .claude/skills/refactor-arch/ para dentro de ecommerce-api-legacy/
Verificar que as 3 fases executam corretamente neste projeto
Salvar o relatório em reports/audit-project-2.md
Commitar o código refatorado no repositório
Projeto 3 — task-manager-api (Python/Flask)
cd ../task-manager-api
claude "/refactor-arch"
Copiar a pasta .claude/skills/refactor-arch/ para dentro de task-manager-api/
Verificar que a Fase 1 detecta Python/Flask e o domínio de Task Manager
Verificar que a Fase 2 identifica problemas mesmo em um projeto parcialmente organizado
Verificar que a Fase 3 melhora a estrutura sem quebrar a aplicação
Salvar o relatório em reports/audit-project-3.md
Commitar o código refatorado no repositório
Checklist de Validação
Fase 1 — Análise

Linguagem detectada corretamente
Framework detectado corretamente
Domínio da aplicação descrito corretamente
Número de arquivos analisados condiz com a realidade
Fase 2 — Auditoria

Relatório segue o template definido nos arquivos de referência
Cada finding tem arquivo e linhas exatos
Findings ordenados por severidade (CRITICAL → LOW)
Mínimo de 5 findings identificados
Detecção de APIs deprecated incluída (se aplicável)
Skill pausa e pede confirmação antes da Fase 3
Fase 3 — Refatoração

Estrutura de diretórios segue padrão MVC
Configuração extraída para módulo de config (sem hardcoded)
Models criados para abstrair dados
Views/Routes separadas para roteamento
Controllers concentram o fluxo da aplicação
Error handling centralizado
Entry point claro
Aplicação inicia sem erros
Endpoints originais respondem corretamente
Entregável
Este projeto.
Skill completa em .claude/skills/refactor-arch/ (dentro dos 3 projetos)
Código refatorado dos 3 projetos (resultado da execução da Fase 3, commitado no repositório)
Relatórios de auditoria em reports/ (3 arquivos)
README.md atualizado
Estrutura do repositório
desafio-skills/
├── README.md
│
├── code-smells-project/
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/
│   │           ├── SKILL.md
│   │           └── (arquivos de referência)
│   ├── app.py
│   ├── controllers.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── ecommerce-api-legacy/
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/
│   ├── src/
│   │   ├── app.js
│   │   ├── GodManager.js
│   │   └── utils.js
│   ├── api.http
│   └── package.json
│
├── task-manager-api/
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/
│   ├── app.py
│   ├── database.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
│
└── reports/
    ├── audit-project-1.md
    ├── audit-project-2.md
    └── audit-project-3.md
README.md deve conter
A) Seção "Análise Manual": lista dos problemas identificados, classificação por severidade e justificativa de por que cada problema é relevante.

B) Seção "Construção da Skill": decisões de design, quais anti-patterns incluiu e por quê, como garantiu que a skill é agnóstica de tecnologia e desafios encontrados.

C) Seção "Resultados": resumo dos relatórios de auditoria, comparação antes/depois, checklist de validação preenchido, screenshots ou logs das aplicações rodando após refatoração.

D) Seção "Como Executar": pré-requisitos, comandos para executar a skill em cada projeto e como validar que a refatoração funcionou.

Ordem de execução sugerida
1. Analisar os projetos manualmente — leia o código dos três projetos e documente os problemas encontrados.

2. Criar a skill — escreva o SKILL.md e os arquivos de referência.

3. Executar nos 3 projetos:

# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
4. Iterar — se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

Critérios de Aceite
A skill deve atingir os seguintes mínimos em todos os 3 projetos:

Fase 1 detecta stack corretamente — OBRIGATÓRIO (3/3 projetos)
Fase 2 encontra ≥ 5 findings — OBRIGATÓRIO (3/3 projetos)
Fase 2 inclui pelo menos 1 CRITICAL ou HIGH — OBRIGATÓRIO (3/3 projetos)
Fase 3 aplicação funciona após refatoração — OBRIGATÓRIO (3/3 projetos)
Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!

Referências
https://code.claude.com/docs/en/skills - Claude Code: Skills — Documentação oficial sobre como criar e estruturar Skills
 https://code.claude.com/docs/en/overview - Claude Code: Overview — Visão geral do Claude Code e suas capacidades
The Complete Guide to Building Skills for Claude (PDF) — Guia completo da Anthropic sobre construção de Skills
Equipping Agents for the Real World with Agent Skills — Blog oficial da Anthropic sobre Agent Skills
Dicas Finais
Comece pela análise manual — entender os problemas profundamente é essencial para criar uma skill que os detecte.
O SKILL.md é um prompt — ele instrui o agente sobre o que fazer, enquanto os arquivos de referência fornecem o conhecimento de domínio.
Seja específico nos sinais de detecção — "código ruim" não ajuda; "query SQL dentro de loop for" é acionável.
Teste incrementalmente — não tente criar a skill perfeita de primeira.
A skill deve ser copiável — se ela só funciona em um projeto específico, está acoplada demais. Teste nos 3 projetos para validar.
Pedir confirmação na Fase 2 é obrigatório — o humano deve revisar o relatório antes de qualquer modificação.
Consulte as referências do curso — revise a documentação oficial da ferramenta escolhida e os materiais das aulas.