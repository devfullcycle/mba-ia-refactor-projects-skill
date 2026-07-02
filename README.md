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

Levantamento feito por leitura direta do código-fonte dos 3 projetos, antes da criação da skill. Cada achado indica arquivo(s) e linha(s) exatos.

### code-smells-project (Python/Flask)

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | SQL Injection generalizada (concatenação de string em todas as queries) | `models.py:28,47-50,57-61,68,109-111,126-129,140,174,279-280,289-297` | Nenhuma query usa parâmetros. O caso do login (`109-111`) permite bypass de autenticação e extração de dados só manipulando os campos `email`/`senha`. |
| CRITICAL | Endpoint que executa SQL arbitrário sem autenticação | `app.py:59-78` | `/admin/query` recebe SQL bruto no corpo da requisição e executa via `cursor.execute()` sem validação, allowlist ou auth — controle total do banco por HTTP. |
| CRITICAL | Senhas em texto plano, expostas via API | `database.py:27-34`, `models.py:105-120`, `controllers.py:128-134` | Não há hashing; `GET /usuarios` devolve a senha de todos os usuários em texto plano. |
| HIGH | Segredos hardcoded expostos publicamente | `app.py:7-8`, `controllers.py:285-290` | `SECRET_KEY` e `debug` ficam visíveis no JSON de resposta de `/health`, acessível sem autenticação. |
| HIGH | Endpoint destrutivo sem autenticação | `app.py:47-57` | `/admin/reset-db` apaga produtos, usuários e pedidos via POST simples, sem token nem confirmação. |
| MEDIUM | Queries N+1 ao montar pedidos | `models.py:171-233` | `get_pedidos_usuario`/`get_todos_pedidos` abrem um cursor novo por item e por produto dentro de loops aninhados, em vez de um JOIN. |
| MEDIUM | Duplicação de validação entre criar e atualizar produto | `controllers.py:24-96` | As mesmas ~15 linhas de validação estão copiadas entre `criar_produto` e `atualizar_produto`. |
| LOW | Uso de `print()` para logging | `controllers.py:8,11,57,61,106,161,179,182,208-210,248,250` | Não há logging estruturado; erros e auditoria vão para stdout sem nível ou timestamp. |
| LOW | Listas de valores válidos hardcoded e duplicadas | `controllers.py:52,242` | Categorias e status são listas literais dentro da função; alterar um valor exige editar múltiplos pontos. |

### ecommerce-api-legacy (Node.js/Express)

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | Segredos hardcoded no código-fonte | `src/utils.js:1-7` | Senha de banco, chave de gateway de pagamento (`pk_live_...`) e credencial SMTP versionadas em texto plano. |
| CRITICAL | Hash de senha customizado e inseguro | `src/utils.js:17-23`, usado em `src/AppManager.js:68` | `badCrypto()` não é um hash criptográfico real (repete base64 do valor original 10.000x e trunca) — reversível e sem salt. |
| HIGH | God Class concentrando DB, seed, rotas e regras de negócio | `src/AppManager.js:1-141` | Uma única classe cria conexão, schema, dados de seed e implementa todos os handlers HTTP — impossível testar em isolamento. |
| HIGH | Pirâmide de callbacks com tratamento de erro incompleto | `src/AppManager.js:28-129` | `/api/checkout` e `/api/admin/financial-report` aninham até 5 níveis de callback; vários `err` são ignorados (ex: linhas 92, 104-106). |
| HIGH | Estado global mutável compartilhado entre requisições | `src/utils.js:9-10` | `globalCache` e `totalRevenue` são variáveis de módulo mutáveis, sem encapsulamento nem escopo por requisição. |
| MEDIUM | Queries N+1 no relatório financeiro | `src/AppManager.js:83-127` | Uma query por curso, outra por matrícula e outra por pagamento dentro de loops aninhados, em vez de um JOIN. |
| MEDIUM | Exclusão de usuário deixa dados órfãos | `src/AppManager.js:131-137` | `DELETE /api/users/:id` remove o usuário mas não as matrículas/pagamentos associados — o próprio comentário no código admite isso. |
| LOW | Nomes de variáveis não descritivos | `src/AppManager.js:29-33` | `u, e, p, cid, cc` dificultam entender o payload do checkout sem ler a lógica inteira. |
| LOW | Respostas de erro inconsistentes | `src/AppManager.js` (várias linhas) | Mistura `res.send()` com texto puro e `res.status().json()`, sem contrato de API único. |

### task-manager-api (Python/Flask, parcialmente organizado)

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | Ausência total de autenticação/autorização nas rotas | `routes/task_routes.py` (todas), `routes/user_routes.py` (exceto `/login`), `routes/report_routes.py` (todas) | Existe um endpoint de login, mas nenhuma rota valida o token gerado — qualquer requisição HTTP acessa e altera dados de qualquer usuário. |
| CRITICAL | Hash de senha com MD5 sem salt (API/prática criptográfica obsoleta) | `models/user.py:27-32` | MD5 é quebrado para uso em senhas (rainbow tables); deveria usar `werkzeug.security.generate_password_hash` ou bcrypt. |
| CRITICAL | Credenciais hardcoded no código-fonte | `app.py:13`, `services/notification_service.py:9-10` | `SECRET_KEY` e credenciais SMTP completas (usuário/senha) versionadas em texto plano. |
| HIGH | Token de sessão falso e previsível | `routes/user_routes.py:210` | `'fake-jwt-token-' + user.id` não é assinado nem expira — mesmo que fosse validado, é trivialmente forjável. |
| HIGH | Lógica de negócio duplicada nas rotas em vez de reaproveitar o model | `task_routes.py:30-39,71-80`, `user_routes.py:171-180`, `report_routes.py:33-43,132-135` | O cálculo de "overdue" é copiado manualmente 5 vezes, ignorando `Task.is_overdue()` já existente em `models/task.py:50-60`. |
| MEDIUM | Queries N+1 nos relatórios | `routes/report_routes.py:53-68,161-164` | Uma query de tasks por usuário e uma contagem por categoria dentro de loops, em vez de agregação única. |
| MEDIUM | Hash de senha exposto nas respostas da API | `models/user.py:16-25`, retornado em `routes/user_routes.py:85-86,129` | `to_dict()` inclui o campo `password`; mesmo hasheado, não deveria ser serializado. |
| LOW | `except` genéricos escondem erros | `routes/task_routes.py:62`, `routes/user_routes.py:130,149,207` | `except:` bare captura qualquer exceção sem log detalhado, dificultando debugging. |
| LOW | Imports não utilizados | `routes/task_routes.py:7`, `routes/report_routes.py:8` | `os, sys, time` e `json` importados e nunca usados. |

## Construção da Skill

A skill `refactor-arch` foi estruturada como um prompt com 5 arquivos de referência em Markdown, permitindo agnóstica de tecnologia e reutilização em diferentes stacks.

### Arquitetura da Skill

```
.claude/skills/refactor-arch/
├── SKILL.md                              # Prompt principal (3 fases)
└── references/
    ├── project-analysis.md               # Heurísticas de detecção
    ├── anti-patterns-catalog.md          # Catálogo de 19 anti-patterns
    ├── report-template.md                # Formato de relatório
    ├── architecture-guidelines.md        # Regras MVC
    └── refactoring-playbook.md          # 14 padrões de transformação
```

**SKILL.md** é o prompt que orquestra as 3 fases sequenciais:
1. **Fase 1** — Análise: detecta linguagem, framework, dependências, domínio e arquitetura atual (sem modificar arquivos)
2. **Fase 2** — Auditoria: cruza código contra catálogo de anti-patterns, gera relatório detalhado com arquivo/linha exatos, pede confirmação explícita antes de prosseguir
3. **Fase 3** — Refatoração: reestrutura para MVC conforme playbook, valida que aplicação sobe e endpoints funcionam

### Agnósticismo de Tecnologia

A skill não faz suposições sobre estrutura de pastas, linguagem ou framework:

- **Fase 1** inventaria todos os arquivos-fonte detectando linguagem por extensão (`.py`, `.js`, `.go`) e framework lendo manifesto (`requirements.txt`, `package.json`) e imports do código
- **Fase 2** não assume estrutura de diretórios — aplica cada anti-pattern do catálogo linha por linha em todos os arquivos encontrados
- **Fase 3** adapta a refatoração ao contexto: projeto monolítico completo (cria MVC do zero) ou parcialmente organizado (preserva o que funciona, corrige só o que viola guidelines)

### Catálogo de Anti-Patterns (19 padrões)

| Código | Nome | Severidade |
|---|---|---|
| AP-01 | SQL Injection / Query por concatenação | CRITICAL |
| AP-02 | Credenciais / segredos hardcoded | CRITICAL |
| AP-03 | Senha em texto plano ou hash inseguro | CRITICAL |
| AP-04 | Endpoint perigoso sem autenticação | CRITICAL |
| AP-05 | God Class / God File | CRITICAL |
| AP-06 | Lógica de negócio na camada errada | HIGH |
| AP-07 | Estado global mutável | HIGH |
| AP-08 | Ausência de autenticação/autorização | HIGH |
| AP-09 | Callback hell / tratamento de erro incompleto | HIGH |
| AP-10 | Acoplamento forte / falta de injeção de dependência | HIGH |
| AP-11 | Query N+1 | MEDIUM |
| AP-12 | Validação ausente ou duplicada | MEDIUM |
| AP-13 | Código duplicado | MEDIUM |
| AP-14 | Uso inadequado de middleware / configuração | MEDIUM |
| AP-15 | Logging por print/console | LOW |
| AP-16 | Magic numbers e valores hardcoded | LOW |
| AP-17 | Nomenclatura ruim | LOW |
| AP-18 | Imports não utilizados / dead code | LOW |
| AP-19 | Tratamento de exceção genérico | LOW |

Seção adicional: **APIs Deprecated** — MD5 para senhas, `datetime.utcnow()`, callbacks SQLite, etc., com equivalente moderno recomendado.

### Playbook de Refatoração (14 padrões)

Cada padrão mapeia um ou mais anti-patterns para uma transformação concreta:

| Padrão | Descrição | Corrige |
|---|---|---|
| RF-01 | Parametrizar queries | AP-01 |
| RF-02 | Externalizar configuração e segredos | AP-02 |
| RF-03 | Hash de senha seguro | AP-03 |
| RF-04 | Remover/proteger endpoint perigoso | AP-04 |
| RF-05 | Quebrar God Class em camadas | AP-05 |
| RF-06 | Mover lógica de negócio para model/service | AP-06, AP-13 |
| RF-07 | Encapsular estado global mutável | AP-07, AP-10 |
| RF-08 | Achatar callback hell e tratar erros | AP-09 |
| RF-09 | Adicionar autenticação e tokens reais | AP-08 |
| RF-10 | Eliminar query N+1 | AP-11 |
| RF-11 | Centralizar e reutilizar validação | AP-12 |
| RF-12 | Tratamento de erro centralizado + logging | AP-14, AP-15, AP-19 |
| RF-13 | Constantes nomeadas e limpeza | AP-16, AP-17, AP-18 |
| RF-14 | Substituir APIs deprecated | (seção própria) |

### Validação em 3 Stacks Diferentes

A skill foi testada e validada em:

1. **code-smells-project** (Python/Flask) — projeto monolítico em 4-5 arquivos, desorganizado
2. **ecommerce-api-legacy** (Node.js/Express) — God Class em 3 arquivos, callbacks aninhados
3. **task-manager-api** (Python/Flask) — projeto parcialmente organizado (models/, routes/, services/) mas com violações arquiteturais

Em cada execução, a skill:
- Detectou a stack e domínio corretamente (Fase 1 ✓)
- Encontrou >= 5 findings com >= 1 CRITICAL/HIGH (Fase 2 ✓)
- Reestruturou para MVC sem quebrar a aplicação (Fase 3 ✓)

### Decisões de Design

1. **Prompt + Referências separadas**: SKILL.md é o orquestrador; cada arquivo de referência é um corpo de conhecimento específico (análise, catálogo, guidelines, playbook) que pode ser atualizado independentemente sem afetar a lógica de execução.

2. **Fase 2 para e pede confirmação**: Requisito obrigatório do desafio. O usuário revisa o relatório antes de qualquer mudança de arquivo — abordagem conservadora apropriada para código de produção.

3. **Contexto adaptativo na Fase 3**: Não há reescrita desnecessária. Um projeto já bem organizado (task-manager-api) preserva sua estrutura de diretórios e adiciona apenas o que falta (config/, middlewares/). Um monolito é refatorado do zero (code-smells-project).

4. **Validação obrigatória**: Fase 3 sempre valida boot da aplicação e endpoints respondendo. Se falhar, a skill para antes de reportar conclusão, forçando correção do erro.

## Resultados

Execução da skill nos 3 projetos:

### Projeto 1 — code-smells-project (Python/Flask, monolito)

**Audit Summary:**
- CRITICAL: 5 | HIGH: 3 | MEDIUM: 4 | LOW: 4
- **Total: 16 findings**

**Antes da refatoração:**
```
code-smells-project/
├── app.py (88 linhas) — rotas + config + segredos hardcoded
├── controllers.py (300 linhas) — handlers HTTP + lógica de negócio
├── models.py (350 linhas) — SQL bruto + queries N+1 + cálculos
├── database.py (35 linhas) — conexão global mutável
└── requirements.txt
```

**Depois da refatoração:**
```
code-smells-project/
├── config/
│   ├── settings.py — variáveis de ambiente + defaults de dev
│   └── database.py — pool de conexões por requisição
├── models/ — abstrações de dados (produtos, usuários, pedidos)
├── controllers/ — handlers orquestram models + services
├── services/ — notificação, validação
├── middlewares/ — erro centralizado, logging estruturado
├── app.py — entry point limpo
└── requirements.txt (+ dependências de segurança)
```

**Checklist:**
- ✓ Fase 1 detectou Python + Flask corretamente
- ✓ Fase 2 encontrou 16 findings (5 CRITICAL)
- ✓ Fase 3 aplicação inicia sem erros
- ✓ Endpoints originais respondem: GET /produtos, POST /criar_produto, POST /login, etc.

**Relatório:** `reports/audit-project-1.md` (16 achados detalhados)

---

### Projeto 2 — ecommerce-api-legacy (Node.js/Express, God Class)

**Audit Summary:**
- CRITICAL: 4 | HIGH: 5 | MEDIUM: 4 | LOW: 4
- **Total: 17 findings**

**Antes da refatoração:**
```
ecommerce-api-legacy/
├── src/
│   ├── app.js (15 linhas) — bootstrap mínimo
│   ├── AppManager.js (142 linhas) — DB + schema + seed + todas as rotas
│   ├── utils.js (30 linhas) — segredos + badCrypto + globalCache mutável
│   └── test.http
└── package.json
```

**Depois da refatoração:**
```
ecommerce-api-legacy/
├── src/
│   ├── app.js — composition root com DI
│   ├── config/ — env + database promisificado + logger estruturado
│   ├── models/ — userModel, courseModel, enrollmentModel, paymentModel, reportModel
│   ├── services/ — passwordService (bcryptjs), paymentGatewayService, cacheService
│   ├── controllers/ — checkoutController, financialReportController, userController
│   ├── routes/ — checkoutRoutes, adminRoutes, userRoutes
│   ├── middlewares/ — errorHandler, asyncHandler, adminAuth
│   ├── seed.js — dados iniciais, fora do bootstrap
│   ├── .env.example
│   └── package.json (+ bcryptjs)
```

**Checklist:**
- ✓ Fase 1 detectou Node.js + Express corretamente
- ✓ Fase 2 encontrou 17 findings (4 CRITICAL)
- ✓ Fase 3 aplicação inicia sem erros
- ✓ Endpoints originais respondem: POST /api/checkout, GET /api/admin/financial-report (com auth), DELETE /api/users/:id, etc.

**Relatório:** `reports/audit-project-2.md` (17 achados detalhados)

---

### Projeto 3 — task-manager-api (Python/Flask, parcialmente organizado)

**Audit Summary:**
- CRITICAL: 2 | HIGH: 1 | MEDIUM: 4 | LOW: 4
- **Total: 11 findings**

**Antes da refatoração:**
```
task-manager-api/
├── app.py — Flask app com CORS aberto, debug=True, SECRET_KEY hardcoded
├── database.py — conexão global
├── seed.py — dados iniciais
├── models/ — task.py, user.py, category.py (com métodos como is_overdue())
├── routes/ — task_routes.py, user_routes.py, report_routes.py (handlers com lógica)
├── services/ — notification_service.py (com credenciais hardcoded)
├── utils/ — helpers.py (validação morta, constantes não reutilizadas)
└── requirements.txt
```

**Depois da refatoração:**
```
task-manager-api/
├── config/ — settings.py (variáveis de ambiente), database.py (acesso organizado)
├── middlewares/ — error_handler.py, auth.py (login_required decorator)
├── models/ — task.py, user.py, category.py (com hash seguro, métodos isolados)
├── routes/ — task_routes.py, user_routes.py, report_routes.py (limpos, sem lógica)
├── services/ — notification_service.py (credenciais via env), task_service.py (queries eficientes)
├── utils/ — helpers.py (constantes reutilizadas em rotas)
├── app.py — entry point, CORS restrito, debug por env
├── database.py — organizado, conexão por requisição
├── seed.py — dados iniciais
├── .env.example — PORT, SECRET_KEY, EMAIL_*, FLASK_DEBUG
└── requirements.txt
```

**Checklist:**
- ✓ Fase 1 detectou Python + Flask + domínio Task Manager corretamente
- ✓ Fase 2 encontrou 11 findings (2 CRITICAL, detectou API deprecated)
- ✓ Fase 3 aplicação inicia sem erros, arquitetura existente preservada
- ✓ Endpoints originais respondem: GET/POST /tasks, /users, /categories, /reports, /login, etc.

**Relatório:** `reports/audit-project-3.md` (11 achados detalhados)

---

### Resumo Comparativo

| Métrica | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| **Stack** | Python/Flask | Node.js/Express | Python/Flask |
| **Arquitetura** | Monolítica (4 arquivos) | God Class (3 arquivos) | Parcialmente organizada (modular) |
| **Findings totais** | 16 | 17 | 11 |
| **CRITICAL** | 5 | 4 | 2 |
| **HIGH** | 3 | 5 | 1 |
| **Refatoração** | Reestrutura completa | Separação em MVC | Melhoria incremental |
| **Validação Fase 3** | ✓ Todos endpoints funcionam | ✓ Todos endpoints funcionam | ✓ Todos endpoints funcionam |

**Comportamento da Skill em 3 contextos:**

1. **Monolito desestruturado** (projeto 1): Skill criou estrutura MVC completa, moveu segredos para config, parametrizou todas as queries, centralizou logging.

2. **God Class com callbacks** (projeto 2): Skill quebrou a classe única em models/services/controllers/routes, promisificou callbacks para async/await, protegeu rotas admin, substituiu hash inseguro por bcryptjs.

3. **Projeto modular com violações** (projeto 3): Skill preservou models/, routes/, services/, utils/ existentes, adicionou config/ e middlewares/, extraiu duplicação, implementou autenticação via decorator, migrou para hash seguro e `datetime.now(datetime.UTC)`.

## Como Executar

### Pré-requisitos

- **Claude Code** instalado ([claude.ai/code](https://claude.ai/code)) ou CLI local (`claude` disponível no $PATH)
- **Python 3.7+** (para code-smells-project e task-manager-api)
- **Node.js 16+** (para ecommerce-api-legacy)
- `pip` e `npm` disponíveis

### Executar a Skill em cada Projeto

#### Projeto 1 — code-smells-project

```bash
cd code-smells-project
pip install -r requirements.txt
claude "/refactor-arch"
```

Ao final da Fase 2, responda `y` para confirmar refatoração.

Para validar manualmente após Fase 3:
```bash
python app.py
# Em outro terminal:
curl http://localhost:5000/health
curl -X GET http://localhost:5000/produtos
curl -X POST http://localhost:5000/criar_produto \
  -H "Content-Type: application/json" \
  -d '{"nome":"Notebook","preco":2000,"estoque":5,"categoria":"Eletrônicos"}'
```

#### Projeto 2 — ecommerce-api-legacy

```bash
cd ../ecommerce-api-legacy
npm install
claude "/refactor-arch"
```

Ao final da Fase 2, responda `y` para confirmar refatoração.

Para validar manualmente após Fase 3:
```bash
npm start
# Em outro terminal (exemplos em ecommerce-api-legacy/api.http):
curl -X POST http://localhost:3000/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"u":"Alice","e":"alice@example.com","p":"senha123","cid":1,"cc":"4111111111111111"}'

curl -X GET "http://localhost:3000/api/admin/financial-report" \
  -H "x-admin-key: admin-key-123"
```

#### Projeto 3 — task-manager-api

```bash
cd ../task-manager-api
pip install -r requirements.txt
python seed.py
claude "/refactor-arch"
```

Ao final da Fase 2, responda `y` para confirmar refatoração.

Para validar manualmente após Fase 3:
```bash
python app.py
# Em outro terminal:
curl http://localhost:5000/health
curl -X GET http://localhost:5000/tasks
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
curl -X GET http://localhost:5000/reports/summary
```

### Onde Encontrar os Resultados

- **Código refatorado:** Cada projeto (após executar a skill, os arquivos são modificados in-place)
- **Relatórios de auditoria:** `reports/audit-project-{1,2,3}.md`
- **Logs de execução:** Serão impressos no console durante a Fase 1, 2 e 3

### Iteração (se necessário)

Se a skill não detectou problemas suficientes ou a refatoração falhou em algum projeto:

1. Revise os arquivos de referência em `.claude/skills/refactor-arch/references/`
2. Ajuste o catálogo de anti-patterns ou playbook conforme necessário
3. Limpe os arquivos modificados ou reverta com `git restore`
4. Execute novamente: `claude "/refactor-arch"`
5. Repita até que todas as fases sejam validadas