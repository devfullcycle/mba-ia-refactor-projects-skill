# Criação de Skills — Refatoração Arquitetural Automatizada

Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## Objetivo

Você deve entregar uma Skill capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

## Contexto

### Definição de Severidades

Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

### Exemplo de Uso no CLI

```bash
# Executar a skill no projeto com problemas
cd code-smells-project
claude "/refactor-arch"
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
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

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

## Tecnologias obrigatórias

- **Ferramenta:** uma das três opções abaixo (não são aceitas outras ferramentas):
  - Claude Code
  - Gemini CLI
  - OpenAI Codex
- **Recurso:** Custom Skills (ou o equivalente na ferramenta escolhida)
- **Formato dos arquivos de referência:** Markdown
- **Projetos-alvo:** Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)

> **Nota sobre a ferramenta:** Os exemplos deste documento usam o Claude Code (`.claude/skills/`) como referência, pois é a ferramenta utilizada no curso. Se você optar por Gemini CLI ou Codex, adapte o nome da pasta e o comando de invocação conforme a convenção dela — o conceito de skill e a estrutura interna (SKILL.md + arquivos de referência) permanecem os mesmos.

## Requisitos

### 1. Análise Manual dos Projetos

Antes de criar a skill, você deve entender os problemas que ela vai resolver.

**Tarefas:**

- Analisar o projeto `code-smells-project/` (Python/Flask — API de E-commerce)
- Analisar o projeto `ecommerce-api-legacy/` (Node.js/Express — LMS API com fluxo de checkout)
- Analisar o projeto `task-manager-api/` (Python/Flask — API de Task Manager)

Para cada projeto, identificar e documentar no mínimo 5 problemas, incluindo pelo menos:

- 1 de severidade CRITICAL ou HIGH
- 2 de severidade MEDIUM
- 2 de severidade LOW

Documentar os achados na seção "Análise Manual" do seu `README.md`

> **Dica:** Não precisa encontrar todos os problemas — foque nos que têm maior impacto arquitetural. Use os projetos como insumo para entender quais padrões sua skill precisa detectar.

> **Por que 3 projetos?** Dois são Python/Flask (com níveis de organização diferentes) e um é Node.js/Express. Sua skill precisa funcionar nos 3 para provar que é verdadeiramente agnóstica de tecnologia — lidando tanto com código completamente desestruturado quanto com projetos que já possuem alguma separação de camadas.

### 2. Criação da Skill

Agora que você conhece os problemas, crie uma skill que os detecte, gere um relatório de auditoria e corrija automaticamente.

**Tarefas:**

Criar a skill dentro do projeto `code-smells-project/` e implementar o SKILL.md com 3 fases sequenciais:

- **Fase 1 — Análise:** Detectar stack, mapear arquitetura atual, imprimir resumo
- **Fase 2 — Auditoria:** Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
- **Fase 3 — Refatoração:** Reestruturar para o padrão MVC, validar que funciona

Criar arquivos de referência em Markdown que forneçam à skill o conhecimento necessário para executar as 3 fases. Os arquivos devem cobrir **obrigatoriamente** as seguintes áreas de conhecimento:

| Área de conhecimento | O que deve conter |
|---|---|
| Análise de projeto | Heurísticas para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura |
| Catálogo de anti-patterns | Anti-patterns com sinais de detecção e classificação de severidade |
| Template de relatório | Formato padronizado do relatório de auditoria (Fase 2) |
| Guidelines de arquitetura | Regras do padrão MVC alvo (camadas Models, Views/Routes e Controllers, responsabilidades de cada uma) |
| Playbook de refatoração | Padrões concretos de transformação para cada anti-pattern (com exemplos de código) |

> **Nota:** Você tem liberdade para organizar os arquivos de referência como preferir — pode usar os nomes e a quantidade de arquivos que fizer sentido para sua skill. O importante é que todas as 5 áreas de conhecimento estejam cobertas. O nome da skill (`refactor-arch`) e o arquivo `SKILL.md` são obrigatórios e não devem ser alterados. O path da skill segue a convenção da ferramenta escolhida (no Claude Code, por exemplo, é `.claude/skills/refactor-arch/`).

**Requisitos da skill:**

- Deve ser agnóstica de tecnologia — deve funcionar corretamente nos 3 projetos fornecidos, independente da stack ou nível de organização
- O catálogo de anti-patterns deve conter no mínimo 8 anti-patterns com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW)
- O catálogo deve incluir detecção de APIs deprecated — identificar uso de APIs obsoletas e recomendar o equivalente moderno
- O playbook deve ter no mínimo 8 padrões de transformação com exemplos de código antes/depois
- A Fase 2 deve pausar e pedir confirmação antes de modificar qualquer arquivo
- A Fase 3 deve validar o resultado (boot da aplicação + endpoints funcionando)

### 3. Execução da Skill

Execute sua skill nos 3 projetos e valide que ela funciona em todas as stacks.

#### Projeto 1 — code-smells-project (Python/Flask)

Invocar a skill no Claude Code:

```bash
claude "/refactor-arch"
```

> **Nota:** O comando acima é o exemplo com Claude Code. Se você estiver usando Gemini CLI ou Codex, utilize o comando equivalente para invocar uma skill na sua ferramenta.

- Verificar que a Fase 1 detecta corretamente a stack e imprime o resumo
- Verificar que a Fase 2 encontra no mínimo 5 dos problemas documentados na sua análise manual
- Confirmar a execução da Fase 3
- Verificar que a Fase 3:
  - Cria a estrutura de diretórios baseada em MVC
  - A aplicação inicia sem erros
  - Os endpoints originais continuam respondendo
- Salvar o relatório de auditoria (output da Fase 2) em `reports/audit-project-1.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

Prove que sua skill é reutilizável em outro projeto de backend, mas com stack diferente.

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `ecommerce-api-legacy/`
- Invocar a skill:

```bash
cd ../ecommerce-api-legacy
claude "/refactor-arch"
```

- Verificar que as 3 fases executam corretamente neste projeto
- Salvar o relatório em `reports/audit-project-2.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 3 — task-manager-api (Python/Flask)

Agora o teste com um projeto Python/Flask que já possui alguma organização de camadas (models, routes, services, utils).

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `task-manager-api/`
- Invocar a skill:

```bash
cd ../task-manager-api
claude "/refactor-arch"
```

- Verificar que:
  - A Fase 1 detecta corretamente Python/Flask como stack e identifica o domínio de Task Manager
  - A Fase 2 identifica problemas mesmo em um projeto parcialmente organizado
  - A Fase 3 melhora a estrutura sem quebrar a aplicação (todos os endpoints devem continuar respondendo)
- Salvar o relatório em `reports/audit-project-3.md`
- Commitar o código refatorado do projeto no repositório

> **Nota:** Este projeto já possui alguma separação de camadas, mas isso não significa que a arquitetura está adequada. A skill deve identificar tanto problemas de código (segurança, performance, qualidade) quanto oportunidades de melhoria arquitetural. Se houver mudanças estruturais necessárias, a skill deve propô-las e executá-las.

#### Validação

Para cada projeto refatorado, valide o seguinte checklist:

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

> **Dica:** Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Entregável

Repositório público no GitHub (fork do repositório base) contendo:

- Skill completa em `.claude/skills/refactor-arch/` (dentro dos 3 projetos)
- Código refatorado dos 3 projetos (resultado da execução da Fase 3, commitado no repositório)
- Relatórios de auditoria em `reports/` (3 arquivos)
- `README.md` atualizado

### Estrutura do repositório

Faça um fork do repositório base contendo os três projetos com code smells.

> **Nota:** A estrutura abaixo usa Claude Code como exemplo (`.claude/skills/`). Se estiver usando outra ferramenta, adapte os caminhos conforme a convenção dela.

```
desafio-skills/
├── README.md                              # Sua documentação
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (API de E-commerce)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← SUA SKILL AQUI
│   │           ├── SKILL.md
│   │           └── (arquivos de referência)
│   ├── app.py
│   ├── controllers.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS API com checkout)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── src/
│   │   ├── app.js
│   │   ├── AppManager.js
│   │   └── utils.js
│   ├── api.http
│   └── package.json
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (API de Task Manager)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── app.py
│   ├── database.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
│
└── reports/                               # Relatórios gerados
    ├── audit-project-1.md                 # Saída da Fase 2 no projeto 1
    ├── audit-project-2.md                 # Saída da Fase 2 no projeto 2
    └── audit-project-3.md                 # Saída da Fase 2 no projeto 3
```

**O que você vai criar:**

- `.claude/skills/refactor-arch/` — A skill completa (SKILL.md + arquivos de referência)
- Código refatorado dos 3 projetos — resultado da execução da Fase 3, commitado no repositório
- `reports/audit-project-{1,2,3}.md` — Relatório de auditoria de cada projeto
- `README.md` — Documentação do seu processo

**O que já vem pronto:**

- `code-smells-project/` — API de E-commerce Python/Flask com code smells intencionais
- `ecommerce-api-legacy/` — LMS API Node.js/Express (com fluxo de checkout) e problemas de implementação
- `task-manager-api/` — API de Task Manager Python/Flask com organização parcial e problemas de segurança/qualidade

> **Dica:** Cada projeto contém problemas intencionais de diferentes severidades (CRITICAL, HIGH, MEDIUM, LOW), incluindo falhas de segurança, violações arquiteturais e problemas de qualidade de código. Parte do desafio é identificá-los por conta própria através da análise manual do código.

### README.md deve conter

**A) Seção "Análise Manual":**

- Lista dos problemas identificados manualmente em cada projeto
- Classificação por severidade
- Justificativa de por que cada problema é relevante

**B) Seção "Construção da Skill":**

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou

### Ordem de execução sugerida

**1. Analisar os projetos manualmente**

Leia o código dos três projetos e documente os problemas encontrados.

**2. Criar a skill**

Escreva o SKILL.md e os arquivos de referência.

**3. Executar nos 3 projetos**

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Salve a saída da Fase 2 de cada projeto em `reports/audit-project-{1,2,3}.md`.

**4. Iterar**

Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Critérios de Aceite

A skill deve atingir os seguintes mínimos em **todos os 3 projetos**:

| Critério | Requisito |
|---|---|
| Fase 1 detecta stack corretamente | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 encontra >= 5 findings | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | OBRIGATÓRIO (3/3 projetos) |
| Fase 3 aplicação funciona após refatoração | OBRIGATÓRIO (3/3 projetos) |

**IMPORTANTE:** Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!

> **Sobre o projeto 3 (task-manager-api):** Este projeto já possui alguma organização. "aplicação funciona" significa que a API inicia sem erros e todos os endpoints continuam respondendo corretamente.

## Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) — Documentação oficial sobre como criar e estruturar Skills
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) — Visão geral do Claude Code e suas capacidades
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Guia completo da Anthropic sobre construção de Skills
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) — Blog oficial da Anthropic sobre Agent Skills

---

## Dicas Finais

- **Comece pela análise manual** — entender os problemas profundamente é essencial para criar uma skill que os detecte.
- **O SKILL.md é um prompt** — ele instrui o agente sobre o que fazer, enquanto os arquivos de referência fornecem o conhecimento de domínio.
- **Seja específico nos sinais de detecção** — "código ruim" não ajuda; "query SQL dentro de loop for" é acionável.
- **Teste incrementalmente** — não tente criar a skill perfeita de primeira.
- **A skill deve ser copiável** — se ela só funciona em um projeto específico, está acoplada demais. Teste nos 3 projetos para validar.
- **Projetos diferentes exigem adaptação** — a Fase 3 de um projeto já parcialmente organizado não vai ter as mesmas transformações de um monolito. Sua skill deve se adaptar ao contexto.
- **Pedir confirmação na Fase 2 é obrigatório** — o humano deve revisar o relatório antes de qualquer modificação.
- **Consulte as referências do curso** — revise a documentação oficial da ferramenta escolhida e os materiais das aulas para relembrar a estrutura e anatomia de uma skill.

---

## Análise Manual

Abaixo estão os problemas identificados manualmente em cada um dos três projetos, organizados em formato de tabela para facilitar a leitura.

### 1. code-smells-project (Python/Flask)

| Severidade | Problema | Arquivo / Linhas | Justificativa / Impacto |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | Vulnerabilidade de SQL Injection | `models.py` (várias funções) | Concatenação direta de strings nas consultas SQL (`"SELECT * FROM produtos WHERE id = " + str(id)`), permitindo que um invasor execute comandos arbitrários no banco de dados. |
| **CRITICAL** | God Class / God Module | `models.py` e `app.py` | `models.py` agrupa toda a persistência, lógica de negócio e manipulação de múltiplos domínios (Produtos, Usuários, Pedidos). Isso viola diretamente o Princípio de Responsabilidade Única (SRP). |
| **HIGH** | Credenciais Hardcoded | `app.py` (Linha 8) | Armazenamento de segredo sensível (`SECRET_KEY = "minha-chave-super-secreta-123"`) diretamente no código de inicialização. |
| **HIGH** | Vazamento de Criptografia no Endpoint de Saúde | `controllers.py` (Função `status_sistema`) | O endpoint de monitoração `/health` expunha publicamente a `SECRET_KEY` ativa do servidor Flask em texto claro, permitindo a falsificação de sessões por atacantes externos. |
| **MEDIUM** | Endpoints Inseguros (Raw SQL) | `app.py` (`/admin/query` e `/admin/reset-db`) | Exposição de endpoints perigosos que realizam ações destrutivas (reset) e executam queries SQL livres enviadas pelo usuário sem autenticação. |
| **MEDIUM** | Manipulação Direta de Model no Controller | `controllers/pedido_controller.py` (Linhas 15-26) | O controller de pedidos manipula diretamente a classe `PedidoModel` em vez de delegar as transações e lógica de negócio para a camada de serviço (`PedidoService`), violando o acoplamento correto e o padrão MVC. |
| **LOW** | Ausência de Logging Estruturado | `controllers.py` | Uso indiscriminado de instruções `print()` para auditoria e erros ao invés de usar o módulo nativo de `logging` do Python. |
| **LOW** | Uso de Números Mágicos para Regras de Negócio | `models/pedido.py` (Linhas 120-130) | Limiares de descontos e taxas estão escritos como valores literais no meio das funções de cálculo de pedidos, tornando a manutenção difícil e o código propenso a falhas durante atualizações de regras. |

### 2. ecommerce-api-legacy (Node.js/Express)

| Severidade | Problema | Arquivo / Linhas | Justificativa / Impacto |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | Callback Hell / Pyramid of Doom | `src/AppManager.js` (Rota `/api/checkout`) | Lógica altamente aninhada acoplando tratamento HTTP, banco de dados e regras de checkout. Dificulta muito a manutenção e testes. |
| **CRITICAL** | Algoritmo Criptográfico Falso | `src/utils.js` (Função `badCrypto`) | Uso de base64 repetitivo em um loop para "criptografar" a senha do usuário. Base64 é uma codificação reversível e não um algoritmo seguro de hashing de senha. |
| **HIGH** | Credenciais Hardcoded | `src/utils.js` | Armazena chaves privadas de pagamento (`paymentGatewayKey`) e senhas do banco de dados no objeto global de configuração. |
| **MEDIUM** | Query N+1 no Banco de Dados | `src/AppManager.js` (Rota `/api/admin/financial-report`) | Loops aninhados realizam chamadas sucessivas ao banco de dados para buscar registros de cada matrícula e aluno, em vez de consolidar em um único `JOIN`. |
| **MEDIUM** | Violação de Atomicidade no Banco de Dados | `controllers/userController.js` (Linhas 4-10) | O método `deleteUser` exclui o registro do usuário mas deixa registros órfãos nas tabelas de matrículas (`enrollments`) e pagamentos (`payments`), corrompendo a integridade referencial por falta de transação. |
| **LOW** | Nomenclatura Pobre de Variáveis | `src/AppManager.js` (Rota `/api/checkout`) | Declaração de variáveis curtas e confusas (`let u`, `let e`, `let p`), violando boas práticas de clean code. |
| **LOW** | Ausência de Sanitização e Validação de Entradas | `routes/routes.js` | Roteador encaminha dados e parâmetros do `req.body` diretamente para as camadas lógicas sem passar por middlewares de sanitização ou validação de esquema (como Joi), aumentando o risco de dados inconsistentes ou ataques simples. |

### 3. task-manager-api (Python/Flask)

| Severidade | Problema | Arquivo / Linhas | Justificativa / Impacto |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | Credenciais Hardcoded no Serviço de Email | `services/notification_service.py` (Linhas 8-9) | Senha de login (`senha123`) do Gmail SMTP em texto claro no arquivo de serviço. |
| **HIGH** | Lógica de Negócio no Controller (Fat Controller) | `routes/task_routes.py` | A rota `/tasks` gerencia a verificação de atraso (`overdue`) de tasks e formatação manual de dados complexos que pertencem à camada Model ou Service. |
| **HIGH** | Credenciais Hardcoded (Secret Key) | `app.py` (Linha 14) | Exposição direta do segredo (`SECRET_KEY = 'super-secret-key-123'`) no arquivo principal do servidor. |
| **MEDIUM** | Tratamento de Erros Genérico | `routes/task_routes.py` (Rota `/tasks` [GET]) | Uso de bloco `try-except` genérico (bare except) capturando todas as falhas e retornando `Erro interno`, mascarando erros úteis para desenvolvimento. |
| **MEDIUM** | Ausência de Validação Declarativa de Inputs | `controllers/task_controller.py` | Validação de dados de entrada na criação/atualização de tarefas é feita de forma imperativa e pulverizada no controller, ao invés de usar validação declarativa estruturada. |
| **LOW** | Uso Inconsistente de Dates / Timezones | `routes/task_routes.py` | Uso de `datetime.utcnow()` bruto que pode causar disparidade de fusos horários ao se comunicar com sistemas de frontend em outras localizações. |
| **LOW** | Manipulação Direta de Model na Camada de Roteamento | `routes/task_routes.py` | Rotas acessam diretamente a classe Model do SQLAlchemy para executar queries complexas de busca e ordenação, vazando regras de persistência para as rotas. |

## Construção da Skill

A skill `refactor-arch` foi estruturada para ser modular, eficiente no consumo de contexto e totalmente agnóstica de tecnologia. 

### 1. Decisões de Design e Estruturação
Adotamos o princípio de **Progressive Disclosure** (Divulgação Progressiva) recomendado no desenvolvimento de Skills para a Gemini CLI. O arquivo principal `SKILL.md` foi mantido limpo e focado no fluxo sequencial das 3 fases do desafio, enquanto os detalhes densos e as especificações de domínio foram movidos para a pasta `references/` em arquivos markdown dedicados:
- `references/project_analysis.md`: Heurísticas para autodetecção da stack.
- `references/anti_patterns.md`: Definição e classificação dos problemas e code smells.
- `references/report_template.md`: Template estruturado do relatório.
- `references/architecture_guidelines.md`: Regras do padrão MVC alvo.
- `references/refactoring_playbook.md`: Exemplos concretos de transformações antes/depois.

Esta abordagem economiza tokens valiosos, pois a IA só carrega os arquivos de referência necessários sob demanda em cada fase específica.

### 2. Catálogo de Anti-patterns Escolhidos
O catálogo engloba 9 problemas de severidades distribuídas:
1. **SQL Injection (CRITICAL)**: Segurança extrema; as aplicações não parametrizavam dados em Flask e SQLite.
2. **Pyramid of Doom / Callback Hell (CRITICAL)**: Problema severo em Node.js com SQLite nativo; corrigido para Promises limpas.
3. **Falsa Criptografia (CRITICAL)**: Senhas mascaradas com Base64 sequencial em vez de algoritmo de hash de via única com salt.
4. **God Class / God Module (CRITICAL)**: Arquivos monolíticos acoplando rotas, regras de negócio e persistência de múltiplos domínios.
5. **Hardcoded Credentials (HIGH)**: Chaves de API, senhas SMTP e secrets expostos diretamente no repositório.
6. **Fat Controllers (HIGH)**: Roteadores engolindo regras de negócio complexas.
7. **Query N+1 Problem (MEDIUM)**: Consultas consecutivas ao banco feitas de dentro de loops, gerando gargalo de performance.
8. **Tratamento de Erros Genérico (MEDIUM)**: Capturas sem log real (bare except) escondendo exceções originais.
9. **APIs Deprecated (MEDIUM/LOW)**: Uso de funções obsoletas como `datetime.utcnow()` do Python 3.12 ou `before_first_request` no Flask.

### 3. Independência de Tecnologia (Agnosticismo)
Para garantir que a skill funcione de forma agnóstica de linguagem ou framework (Python/Flask, Node.js/Express, etc.):
- As fases usam **heurísticas genéricas de mapeamento** baseadas na árvore de arquivos e dependências (`package.json`, `requirements.txt`).
- O playbook de refatoração possui padrões paralelos para ambas as stacks (ex: correção de SQL Injection no Python com `sqlite3` e no Node.js com o driver `sqlite3` assíncrono).
- O padrão MVC foi definido a nível arquitetural e conceitual (responsabilidades de cada camada), permitindo que a IA aplique as mesmas regras abstratas adaptadas às convenções idiomáticas de cada linguagem.

### 4. Desafios Encontrados e Resolução
- **Sincronismo no SQLite Node.js**: O sqlite3 nativo de Node.js usa callbacks pesados. O playbook orienta a envelopar as chamadas do driver em Promises nativas para que a IA possa usar `async/await`, eliminando o callback hell sem requerer pacotes de terceiros pesados.
- **Isolamento de Camadas no MVC**: Garantir que os Models gerados ficassem 100% "cegos" para as requisições HTTP do Flask/Express. Definimos regras rigorosas impedindo o import de objetos globais HTTP (como `request` ou `req`) dentro dos models.

---

## Resultados

A execução automatizada da skill `refactor-arch` obteve resultados excelentes ao mapear, auditar e refatorar os três projetos legados simultaneamente. Os relatórios gerados na pasta `/reports` detalham as vulnerabilidades identificadas de forma exaustiva. Abaixo estão os principais resultados da refatoração realizada:

1. **code-smells-project (Python + Flask)**:
   - **Vulnerabilidades Corrigidas**: Injeção de SQL resolvida por parametrização completa das consultas.
   - **Arquitetura Alvo**: Migrado de um monolito sem camadas (onde o arquivo `models.py` era um God Module) para o padrão MVC rigoroso com camadas isoladas (`controllers`, `services`, `models`).
   - **Melhorias de Qualidade**: Adicionado suporte a variáveis de ambiente (`dotenv`), tratamento global de erros unificado, eliminação de números mágicos e logging estruturado.

2. **ecommerce-api-legacy (Node.js + Express)**:
   - **Vulnerabilidades Corrigidas**: Corrigido o algoritmo de criptografia falsa de Base64 para o padrão seguro de mercado **bcrypt** com salt dinâmico através do módulo `bcrypt`, resolvendo a vulnerabilidade CRITICAL em aberto de forma definitiva.
   - **Callback Hell**: Refatorado para `async/await` com Promises nativas sobre o SQLite, estruturando o fluxo de forma legível e sem aninhamento.
   - **Performance**: O gargalo de Query N+1 na listagem de relatórios financeiros foi resolvido agrupando as chamadas em um `LEFT JOIN` unificado de alta performance.

3. **task-manager-api (Python + Flask)**:
   - **Vulnerabilidades Corrigidas**: Removidas chaves e senhas hardcoded de SMTP/Flask para arquivo `.env` seguro. Resolvida injeção de SQL em filtros de busca.
   - **Isolamento de Camadas**: Lógicas de negócio pesadas (Fat Controller) foram extraídas da camada de roteamento e alocadas em `services/task_service.py`, deixando os controllers limpos e focados apenas na interface HTTP.

## Como Executar

A execução e validação da skill `refactor-arch` e dos projetos resultantes seguem as diretrizes abaixo.

### 1. Requisitos Prévios

- **Runtime**: Node.js v18+ e Python 3.10+ instalados no sistema de desenvolvimento.
- **Banco de Dados**: SQLite3 (gerenciado em arquivos ou em memória no código).
- **Gemini CLI** ou **Claude CLI** instalado e configurado globalmente.

### 2. Configuração e Instalação de Dependências

Para cada um dos projetos sob a raiz, certifique-se de instalar as dependências necessárias:

```bash
# Para os projetos Python (code-smells-project e task-manager-api)
cd code-smells-project && pip install -r requirements.txt
cd ../task-manager-api && pip install -r requirements.txt

# Para o projeto Node.js (ecommerce-api-legacy)
cd ../ecommerce-api-legacy && npm install
```

### 3. Execução da Skill `refactor-arch`

A skill pode ser invocada via terminal para rodar as fases sequenciais (Análise, Auditoria e Refatoração).

```bash
# Carregar e rodar a skill refactor-arch a partir do CLI da Gemini / Claude:
gemini-cli run refactor-arch
```

### 4. Execução Manual e Teste das Aplicações

Para rodar localmente e testar os endpoints refatorados de cada projeto:

- **code-smells-project**:
  ```bash
  cd code-smells-project
  python app.py
  ```
  Acesse `http://localhost:5000/` para interagir com o app.

- **ecommerce-api-legacy**:
  ```bash
  cd ecommerce-api-legacy
  npm start
  ```
  O servidor subirá na porta `3000`. Use o arquivo `api.http` para realizar requisições de checkout, exclusão de usuários e relatório financeiro com as chaves e rotas seguras.

- **task-manager-api**:
  ```bash
  cd task-manager-api
  python app.py
  ```
  O painel de tarefas rodará em `http://localhost:5000/`. Você pode validar o funcionamento dos endpoints usando os testes automatizados já fornecidos (`test_endpoints.py`).