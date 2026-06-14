# Desafio 3 — Refatoração Arquitetural Automatizada com Skills

Skill `refactor-arch` para o Claude Code que automatiza a análise, auditoria e refatoração de projetos legados para o padrão MVC, agnóstica de tecnologia.

---

## Análise Manual

Antes de construir a skill, os três projetos foram analisados manualmente para entender os problemas que ela precisaria detectar e corrigir.

---

### Projeto 1 — `code-smells-project` (Python/Flask — API de E-commerce)

**Stack:** Python 3 + Flask | **Arquitetura atual:** Quasi-MVC plano (4 arquivos, ~780 linhas)

| Severidade | Problema | Arquivo | Linha(s) | Por que é relevante |
|---|---|---|---|---|
| CRITICAL | SQL Injection | `models.py` | 28, 47–50, 57–62, 67, 92, 109–111, 127–129, 140, 148–165, 174, 188, 192, 220, 224, 279–281, 290–296 | Entrada do usuário concatenada em 19 queries distintas. Login (`WHERE email = '"+email+"'`) é bypassed com `' OR '1'='1`. |
| CRITICAL | Credencial hardcoded + vazada | `app.py:7` | `controllers.py:289` | `SECRET_KEY` no código-fonte E retornada no corpo da resposta `/health` — qualquer cliente recebe a chave de sessão. |
| CRITICAL | Senhas em texto puro | `models.py` | 109–111, 127–129 | `criar_usuario` armazena `senha` diretamente; `login_usuario` compara texto puro. Banco comprometido = todas as senhas expostas. |
| CRITICAL | Endpoints admin sem autenticação | `app.py` | 47–78 | `/admin/reset-db` apaga todos os dados; `/admin/query` executa SQL arbitrário — abertos para qualquer HTTP request. |
| CRITICAL | God Module — `models.py` | `models.py` | 1–314 | 314 linhas com queries de 4 domínios + lógica de negócio (cálculo de desconto). Impossível testar em isolamento. |
| CRITICAL | Debug mode hardcoded `True` | `app.py` | 8, 88 | `debug=True` em `0.0.0.0`: REPL do Werkzeug acessível remotamente para execução de código arbitrário. |
| HIGH | Senha e `SECRET_KEY` em respostas da API | `models.py` | 82–83, 97–98; `controllers.py:285–292` | `get_todos_usuarios()` serializa o campo `senha`; `/health` expõe `secret_key`, `debug` e `db_path`. |
| HIGH | Sem autenticação em nenhum endpoint | `app.py` | 1–88 | Qualquer cliente não autenticado lista usuários (com senhas), cria pedidos em nome de outros e acessa admin. |
| HIGH | Race condition — pedido sem transação | `models.py` | 133–168 | Verificação de estoque, INSERT em `pedidos`, INSERTs em `itens_pedido` e UPDATE de estoque sem BEGIN/COMMIT. Falha parcial deixa banco inconsistente. |
| HIGH | Conexão global mutável | `database.py` | 4, 7–8 | `db_connection` como singleton de módulo com `check_same_thread=False`: race conditions em deploys multi-thread. |
| MEDIUM | Problema N+1 | `models.py` | 171–233 | `get_pedidos_usuario()` e `get_todos_pedidos()` abrem novo cursor para cada item e novo cursor para o nome do produto — O(pedidos × itens) queries. |
| MEDIUM | Duplicação de código | `models.py` | 171–201 vs 203–233 | Bloco de 30 linhas quase idêntico duplicado nas duas funções de listagem de pedidos. |
| MEDIUM | Validação ausente — cadastro de usuário | `controllers.py` | 146–165 | Email aceito sem validação de formato; senha aceita com qualquer tamanho (inclusive vazia após strip). |
| MEDIUM | Sem paginação nas listagens | `models.py` | 4–22, 72–87, 203–233 | `SELECT * FROM <tabela>` sem LIMIT em três endpoints — esgota memória com volume real de dados. |
| MEDIUM | Tratamento de exceções genérico | `controllers.py` | múltiplos | `except Exception as e` com `str(e)` retornado ao cliente expõe traceback e mascara erros específicos (ex: e-mail duplicado vira 500 em vez de 409). |
| LOW | Magic numbers — limiares de desconto | `models.py` | 257–263 | `10000`, `5000`, `1000`, `0.1`, `0.05`, `0.02` inline sem constantes nomeadas — regras de negócio invisíveis. |

---

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express — LMS API)

**Stack:** Node.js + Express | **Arquitetura atual:** Monolítica (3 arquivos, ~193 linhas)

| Severidade | Problema | Arquivo | Linha(s) | Por que é relevante |
|---|---|---|---|---|
| CRITICAL | Credenciais e segredos hardcoded | `src/utils.js` | 1–7 | `dbPass`, `paymentGatewayKey` (`pk_live_…`) e `smtpUser` no código-fonte — qualquer dev com acesso ao repo possui todas as credenciais de produção. |
| CRITICAL | Pseudo-criptografia para senhas | `src/utils.js` | 17–22; `src/AppManager.js` | 18, 68 | `badCrypto()` repete base64 e trunca — não é hash real. Seed insere usuário com senha `'123'` em texto puro. |
| CRITICAL | Endpoint admin sem autenticação | `src/AppManager.js` | 80–128 | `GET /api/admin/financial-report` retorna receita, nomes e e-mails de alunos sem nenhuma verificação de identidade. |
| CRITICAL | Lógica de pagamento por prefixo de cartão | `src/AppManager.js` | 44–47 | `cc.startsWith("4") ? "PAID" : "DENIED"` aprova qualquer cartão Visa automaticamente. |
| CRITICAL | God Class — tudo em `AppManager.js` | `src/AppManager.js` | 1–141 | Inicialização do banco, seeds, rotas, lógica de negócio, pagamento e logs no mesmo arquivo. Nenhuma operação pode ser testada em isolamento. |
| HIGH | Lógica de negócio embutida nas rotas | `src/AppManager.js` | 28–137 | Fluxo completo de checkout (criar usuário, validar curso, processar pagamento, enrolar, auditar) em callbacks de rota inline — impossível reutilizar ou testar unitariamente. |
| HIGH | Race condition no checkout sem transação | `src/AppManager.js` | 50–62 | Enrollment criado em `db.run` separado do pagamento sem `BEGIN/COMMIT/ROLLBACK`. Falha no pagamento deixa enrollment órfão. |
| HIGH | DELETE de usuário sem cascade e sem autenticação | `src/AppManager.js` | 131–137 | Acessível sem auth; remove só `users`, deixando enrollments e payments órfãos — a própria resposta admite: "matrículas e pagamentos ficaram sujos no banco". |
| HIGH | Estado global mutável | `src/utils.js` | 9–10 | `globalCache` e `totalRevenue` mutados durante requests — race conditions em ambientes concorrentes. |
| MEDIUM | Problema N+1 no relatório financeiro | `src/AppManager.js` | 88–127 | Para cada curso, busca enrollments; para cada enrollment, busca usuário e pagamento. 2 cursos × 1 aluno = 7 queries; escala como O(N²). |
| MEDIUM | Callback hell (5 níveis) | `src/AppManager.js` | 28–77 | Callbacks aninhados com tratamento de erros inconsistente (alguns `err` ignorados), fluxo ilegível e padrão obsoleto. |
| MEDIUM | Ausência de validação de entrada | `src/AppManager.js` | 29–35 | Checkout verifica apenas presença de campos, sem validar formato de email, tipo de `courseId` ou comprimento de cartão. |
| LOW | Nomes de variáveis inexpressivos | `src/AppManager.js` | 29–34 | `u`, `e`, `p`, `cid`, `cc` em vez de `username`, `email`, `password`, `courseId`, `cardNumber`. |

---

### Projeto 3 — `task-manager-api` (Python/Flask — API de Task Manager)

**Stack:** Python 3 + Flask + SQLAlchemy | **Arquitetura atual:** Layered parcial (models/, routes/, services/, utils/)

| Severidade | Problema | Arquivo | Linha(s) | Por que é relevante |
|---|---|---|---|---|
| CRITICAL | MD5 para armazenar senhas | `models/user.py` | 29, 32 | MD5 não tem salt e é trivialmente quebrado por rainbow tables. Banco comprometido = todas as senhas expostas. |
| CRITICAL | Credenciais SMTP hardcoded | `services/notification_service.py` | 9–10 | `senha123` no código-fonte expõe a conta de e-mail para abuso (spam, phishing). |
| CRITICAL | `SECRET_KEY` hardcoded | `app.py` | 13 | Mesma implicação do Projeto 1: tokens de sessão forjáveis por qualquer pessoa com o código. |
| CRITICAL | Token JWT falso | `routes/user_routes.py` | 210 | `'fake-jwt-token-' + str(user.id)` não é criptograficamente assinado — qualquer usuário pode fabricar tokens de outros usuários. |
| HIGH | Senha incluída na resposta da API | `models/user.py` | 21 | `to_dict()` serializa `self.password` (hash MD5) nas respostas. Expõe o hash para qualquer cliente que liste usuários. |
| HIGH | Sem autenticação nos endpoints | `routes/task_routes.py` | 11–300 | Qualquer request não autenticado lê, cria ou modifica tasks de qualquer usuário. Ausência total de autorização. |
| HIGH | Problema N+1 nas tasks | `routes/task_routes.py` | 14–59 | Para cada task, consulta `User` e `Category` separadamente. 100 tasks = 201 queries. |
| MEDIUM | Lógica de overdue duplicada em 3 lugares | `routes/task_routes.py` | 30–39, 71–80; `routes/report_routes.py` | 33–43 | O mesmo bloco de cálculo de atraso copiado três vezes. Um bugfix precisa ser feito em todos os lugares. |
| MEDIUM | `except:` sem especificidade | `routes/task_routes.py` | 62, 151, 223, 236 | Captura `KeyboardInterrupt`, `SystemExit` e tudo mais. Esconde erros de programação silenciosamente. |
| MEDIUM | Sem paginação nos endpoints de lista | `routes/task_routes.py` | 14 | `Task.query.all()` retorna todas as linhas da tabela. Com milhares de tasks, causa estouro de memória. |
| LOW | Magic numbers de validação | `routes/task_routes.py` | 96–97, 113–114 | `200` (tamanho de título), `1`–`5` (prioridade) hardcoded em múltiplos pontos sem constantes nomeadas. |
| LOW | Imports não utilizados | `routes/task_routes.py` | 7 | `import json, os, sys, time` — nenhum deles usado no arquivo. |

---

## Construção da Skill

### Decisões de design

A skill foi estruturada em **um arquivo de instruções** (`SKILL.md`) e **cinco arquivos de referência**, cada um cobrindo uma área de conhecimento obrigatória:

```
.claude/skills/refactor-arch/
├── SKILL.md                    # Prompt principal — instrui as 3 fases
├── project-analysis.md         # Heurísticas de detecção de stack e arquitetura
├── anti-patterns-catalog.md    # Catálogo com 14 anti-patterns e sinais de detecção
├── report-template.md          # Template padronizado do relatório de auditoria
├── architecture-guidelines.md  # Regras do padrão MVC alvo por camada
└── refactoring-playbook.md     # 10 padrões de transformação com exemplos antes/depois
```

O `SKILL.md` age como um **prompt de sistema especializado**: define o papel do agente, as três fases sequenciais e as regras de comportamento (nunca modificar arquivos antes da confirmação, sempre incluir arquivo e linha nos findings, priorizar segurança). Os arquivos de referência fornecem o **conhecimento de domínio** que o agente consulta em cada fase.

A separação deliberada entre instrução (`SKILL.md`) e conhecimento (arquivos `.md`) permite evoluir o catálogo de anti-patterns ou o playbook sem alterar o fluxo de execução.

### Anti-patterns incluídos no catálogo

O catálogo cobre **14 anti-patterns** organizados por severidade:

| Código | Anti-pattern | Por que foi incluído |
|---|---|---|
| AP-C1 | SQL Injection | Presente nos Projetos 1 e 2; risco mais crítico de segurança web |
| AP-C2 | Hardcoded Credentials | Presente nos 3 projetos; comprometimento silencioso de credenciais |
| AP-C3 | Plain Text / Weak Password Storage | Projetos 1 (texto puro), 2 (pseudo-hash), 3 (MD5) — 3 variantes diferentes |
| AP-C4 | Unauthenticated Dangerous Endpoints | Projeto 1: reset-db e query SQL abertos ao público |
| AP-C5 | God Class / God Module | Projetos 1 e 2: arquivos monolíticos com 4+ domínios misturados |
| AP-C6 | Insecure Payment Processing | Projeto 2: aprovação de pagamento por prefixo de cartão |
| AP-H1 | Business Logic in Controllers | Presente nos 3 projetos em graus diferentes |
| AP-H2 | Global Mutable State | Projeto 2: `globalCache` e `totalRevenue` globais |
| AP-H3 | No Dependency Injection | Padrão cross-project: dependências instanciadas dentro de classes |
| AP-H4 | Sensitive Data in API Responses | Projeto 3: hash de senha exposto na serialização |
| AP-H5 | Missing Authentication / Broken Authorization | Projeto 3: todos os endpoints sem auth |
| AP-M1 | N+1 Query Problem | Presente nos 3 projetos |
| AP-M2 | Code Duplication (DRY) | Projetos 1 e 3: lógica duplicada em múltiplos arquivos |
| AP-M5 | Deprecated Callback Pattern | Projeto 2: callback hell de 5 níveis no Node.js |

Foram escolhidos anti-patterns com **sinal de detecção preciso e acionável** — não "código ruim" genérico, mas padrões que o agente consegue localizar com arquivo e linha exatos (ex: "query SQL dentro de string concatenada", "campo `password` em `to_dict()`").

### Como a skill é agnóstica de tecnologia

Cada arquivo de referência cobre explicitamente **Python e Node.js** em paralelo:

- `project-analysis.md`: tabelas de detecção separadas para frameworks Python (Flask, Django, FastAPI) e Node.js (Express, Fastify, NestJS, Koa), além de ORM para ambos
- `anti-patterns-catalog.md`: exemplos de código antes/depois em Python e JavaScript para cada anti-pattern
- `refactoring-playbook.md`: cada transformação mostra a versão Python (`werkzeug`, `sqlalchemy`) e Node.js (`bcrypt`, `async/await`, `promisify`)
- `architecture-guidelines.md`: estrutura MVC target documentada para Python/Flask (Blueprints) e Node.js/Express (Routers)

O `SKILL.md` instrui o agente a usar as heurísticas do `project-analysis.md` antes de qualquer auditoria, garantindo que detecte a stack correta e aplique os exemplos relevantes.

### Desafios encontrados e como foram resolvidos

**Desafio 1 — Granularidade dos sinais de detecção**
Anti-patterns genéricos ("God Class") são difíceis de detectar automaticamente. A solução foi definir **critérios quantitativos**: "arquivo > 300 linhas com 3+ domínios misturados" e "funções de domínios diferentes no mesmo escopo".

**Desafio 2 — Projetos com níveis de organização diferentes**
O Projeto 3 já tem `models/`, `routes/`, `services/` — uma skill que simplesmente "cria estrutura MVC" quebraria o que já funciona. A solução foi documentar em `architecture-guidelines.md` a regra: "se o projeto já tem estrutura parcial, mova código mal posicionado em vez de recriar tudo do zero".

**Desafio 3 — Garantir a pausa antes da Fase 3**
A instrução no `SKILL.md` é explícita: aguardar "y" do usuário antes de modificar qualquer arquivo. O template de relatório termina com a mensagem de confirmação padronizada, reforçando que a Fase 2 encerra com uma pergunta, não com uma ação.

---

## Resultados

### Resumo dos findings por projeto

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| `code-smells-project` (Python/Flask) | 6 | 4 | 5 | 1 | **16** |
| `ecommerce-api-legacy` (Node.js/Express) | 5 | 4 | 3 | 1 | **13** |
| `task-manager-api` (Python/Flask) | 4 | 3 | 3 | 2 | **12** |

### Comparação antes/depois — Estrutura dos projetos

#### Projeto 1 — `code-smells-project`

**Antes:**
```
code-smells-project/
├── app.py          # rotas + configuração + admin endpoints perigosos
├── models.py       # 350 linhas: 4 domínios misturados + SQL injection
├── controllers.py  # lógica de negócio + health com vazamento de secrets
└── database.py     # conexão com banco
```

**Depois (pós-refatoração):**
```
code-smells-project/
├── app.py                        # composition root (create_app factory)
├── database.py                   # conexão por request via Flask g
├── .env                          # secrets (gitignored)
├── .env.example                  # template de variáveis
├── requirements.txt              # adicionado python-dotenv
├── config/
│   └── settings.py               # SECRET_KEY e DEBUG via env vars
├── models/
│   ├── product_model.py          # queries parametrizadas, domínio isolado
│   ├── user_model.py             # bcrypt via werkzeug, senha fora do to_dict()
│   └── order_model.py            # JOIN elimina N+1; BEGIN/COMMIT/ROLLBACK
├── controllers/
│   ├── product_controller.py     # validação com exceções específicas
│   ├── user_controller.py        # regex email + tamanho mínimo de senha
│   └── order_controller.py       # lógica de desconto com constantes nomeadas
├── views/
│   ├── product_routes.py         # Blueprint /produtos
│   ├── user_routes.py            # Blueprint /usuarios + /login
│   └── order_routes.py           # Blueprint /pedidos + /relatorios
└── middlewares/
    └── error_handler.py          # handlers 400/404/405/500 centralizados
```

#### Projeto 2 — `ecommerce-api-legacy`

**Antes:**
```
ecommerce-api-legacy/src/
├── app.js          # entry point
├── AppManager.js   # 140 linhas: tudo misturado + callback hell
└── utils.js        # credenciais hardcoded + badCrypto()
```

**Depois (pós-refatoração):**
```
ecommerce-api-legacy/
├── .env                               # secrets (gitignored)
├── .env.example                       # template de variáveis (commitável)
├── .gitignore
└── src/
    ├── app.js                         # composition root
    ├── config/
    │   └── settings.js                # dotenv, sem hardcoded secrets
    ├── database/
    │   └── index.js                   # singleton DB + wrappers Promise (getAsync/allAsync/runAsync)
    ├── models/
    │   ├── UserModel.js               # bcryptjs, sem pass nas respostas
    │   ├── CourseModel.js
    │   ├── EnrollmentModel.js
    │   └── PaymentModel.js
    ├── services/
    │   └── CheckoutService.js         # checkout com BEGIN/COMMIT/ROLLBACK
    ├── controllers/
    │   ├── CheckoutController.js      # validação + async/await
    │   ├── ReportController.js        # JOIN único elimina N+1
    │   └── UserController.js          # deleção com cascade
    ├── routes/
    │   ├── checkoutRoutes.js
    │   ├── reportRoutes.js
    │   └── userRoutes.js
    └── middlewares/
        ├── auth.js                    # guarda x-admin-api-key nas rotas admin
        └── errorHandler.js
```

#### Projeto 3 — `task-manager-api`

**Antes:**
```
task-manager-api/
├── app.py               # SECRET_KEY hardcoded, debug=True
├── models/
│   └── user.py          # MD5 password + senha exposta no to_dict()
├── routes/
│   ├── task_routes.py   # sem auth + N+1 + except: genérico
│   └── user_routes.py   # fake JWT token
├── services/
│   └── notification_service.py  # credenciais SMTP hardcoded
└── utils/
```

**Depois (pós-refatoração):**
```
task-manager-api/
├── config/
│   └── settings.py           # env vars para tudo
├── models/
│   ├── user.py               # bcrypt, sem password no to_dict()
│   └── task.py               # overdue logic centralizada no model
├── controllers/
│   ├── task_controller.py    # auth + validação
│   └── user_controller.py    # JWT real
├── routes/
│   ├── task_routes.py        # só roteamento
│   └── user_routes.py
├── services/
│   └── notification_service.py  # credenciais via env
├── middlewares/
│   └── error_handler.py      # except específicos
├── utils/
│   └── task_helpers.py       # overdue sem duplicação
├── app.py
└── .env.example
```

### Checklist de validação

#### Projeto 1 — `code-smells-project`

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python 3)
- [x] Framework detectado corretamente (Flask 3.1.1)
- [x] Domínio da aplicação descrito corretamente (E-commerce: produtos, pedidos, usuários)
- [x] Número de arquivos analisados condiz com a realidade (4 arquivos, ~780 linhas)

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (16 encontrados: 6 CRITICAL, 4 HIGH, 5 MEDIUM, 1 LOW)
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue padrão MVC (config / models / controllers / views / middlewares)
- [x] Configuração extraída para `config/settings.py` via `python-dotenv` (sem hardcode)
- [x] `.env` criado e adicionado ao `.gitignore`; `.env.example` commitável
- [x] Models separados por domínio com queries 100% parametrizadas
- [x] `UserModel` usa `werkzeug.security` bcrypt; seed re-hasheado
- [x] `OrderModel.create()` envolto em `BEGIN / COMMIT / ROLLBACK`
- [x] `OrderModel._fetch_orders()` usa JOIN — N+1 eliminado, duplicação removida
- [x] Desconto movido para `OrderController._calculate_discount()` com constantes nomeadas
- [x] Views usam Blueprint por domínio
- [x] `middlewares/error_handler.py` registra handlers 400/404/405/500
- [x] `app.py` é composition root puro (factory `create_app()`)
- [x] `/admin/reset-db` e `/admin/query` removidos
- [x] Senha fora de todas as respostas da API; `/health` retorna só `status`/`counts`
- [x] Validação de email (regex) e tamanho mínimo de senha no `UserController`
- [x] Conexão por request via Flask `g` (global mutável eliminado)
- [x] Aplicação inicia sem erros
- [x] Todos os endpoints originais respondem corretamente (validado com `test_client`)

#### Projeto 2 — `ecommerce-api-legacy`

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (JavaScript/Node.js)
- [x] Framework detectado corretamente (Express 4.18.2)
- [x] Domínio da aplicação descrito corretamente (LMS: cursos, usuários, enrollments, pagamentos)
- [x] Número de arquivos analisados condiz com a realidade (4 arquivos, ~193 linhas)
- [x] Tabelas do banco identificadas (users, courses, enrollments, payments, audit_logs)

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] 13 findings identificados (5 CRITICAL, 4 HIGH, 3 MEDIUM, 1 LOW)
- [x] Detecção de APIs deprecated incluída (callback hell identificado como MEDIUM)
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue padrão MVC (config / database / models / services / controllers / routes / middlewares)
- [x] Configuração extraída para `config/settings.js` via `dotenv` (sem hardcoded secrets)
- [x] `.env` criado e adicionado ao `.gitignore`; `.env.example` commitável
- [x] `database/index.js` expõe singleton DB com métodos promisificados (`getAsync`, `allAsync`, `runAsync`)
- [x] Models separados por domínio (`UserModel`, `CourseModel`, `EnrollmentModel`, `PaymentModel`)
- [x] `UserModel.create()` usa `bcryptjs` (10 rounds); seed re-hasheado
- [x] `CheckoutService.processCheckout()` envolto em `BEGIN TRANSACTION / COMMIT / ROLLBACK`
- [x] `ReportController` usa JOIN único — N+1 eliminado (de O(N²) queries para 1 query)
- [x] `UserController.deleteUser()` faz cascade: payments → enrollments → users
- [x] Callback hell de 5 níveis convertido para `async/await` em todos os controllers e service
- [x] `middlewares/auth.js` protege `GET /api/admin/financial-report` e `DELETE /api/users/:id` com header `x-admin-api-key`
- [x] `middlewares/errorHandler.js` centraliza tratamento de erros
- [x] Lógica de aprovação por prefixo de cartão substituída por validação de comprimento mínimo
- [x] Variáveis renomeadas (`u`→`username`, `e`→`email`, `p`→`password`, `cid`→`courseId`, `cc`→`cardNumber`)
- [x] `AppManager.js` e `utils.js` removidos (substituídos pela estrutura MVC)
- [x] Aplicação inicia sem erros
- [x] Todos os endpoints originais respondem corretamente (validado com `curl`)

#### Projeto 3 — `task-manager-api`

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python 3)
- [x] Framework detectado corretamente (Flask + SQLAlchemy)
- [x] Domínio da aplicação descrito corretamente (Task Manager: tasks, usuários, categorias)
- [x] Número de arquivos analisados condiz com a realidade (~15 arquivos)

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (12 encontrados)
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models atualizados (bcrypt, sem senha no to_dict)
- [x] Routes simplificadas (só roteamento)
- [x] Controllers com validação e auth
- [x] Error handling centralizado com exceptions específicas
- [x] Entry point limpo
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

### Observações sobre comportamento em stacks diferentes

A skill demonstrou comportamento consistente nas três stacks:

- **Python/Flask (Projetos 1 e 3):** Detectou corretamente `@app.route`, `Flask()`, e arquivos `requirements.txt`. A diferença entre o Projeto 1 (monolito) e Projeto 3 (parcialmente organizado) foi tratada adequadamente — no Projeto 3 a skill melhorou as camadas existentes em vez de recriar do zero.

- **Node.js/Express (Projeto 2):** Detectou `require('express')`, `app.get(`, e `package.json`. O anti-pattern de callback hell (específico ao ecossistema Node.js) foi identificado corretamente e a transformação para `async/await` com `promisify` foi aplicada.

- **SQLAlchemy ORM vs. SQLite raw:** O catálogo cobre ambos — queries parametrizadas com `?` para SQLite direto e `joinedload()` para N+1 com SQLAlchemy. A skill selecionou o padrão correto para cada projeto.

---

## Como Executar

### Pré-requisitos

- **Claude Code** instalado e configurado (`npm install -g @anthropic-ai/claude-code`)
- Chave de API Anthropic configurada (`ANTHROPIC_API_KEY` no ambiente)
- Python 3.10+ (para Projetos 1 e 3)
- Node.js 18+ (para Projeto 2)

### Executar a skill em cada projeto

```bash
# Projeto 1 — code-smells-project (Python/Flask)
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — ecommerce-api-legacy (Node.js/Express)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — task-manager-api (Python/Flask)
cd ../task-manager-api
claude "/refactor-arch"
```

Durante a execução, a skill:
1. Imprime o resumo da análise (Fase 1) automaticamente
2. Gera e exibe o relatório completo de auditoria (Fase 2)
3. **Aguarda confirmação** `[y/n]` antes de modificar qualquer arquivo
4. Executa a refatoração e valida a aplicação (Fase 3)

### Salvar os relatórios de auditoria

Quando a Fase 2 imprimir o relatório, copie o output para o arquivo correspondente:

```bash
# Criar diretório de relatórios
mkdir -p reports

# Os relatórios são gerados pela skill durante a execução da Fase 2
# Salve o output em:
# reports/audit-project-1.md  (code-smells-project)
# reports/audit-project-2.md  (ecommerce-api-legacy)
# reports/audit-project-3.md  (task-manager-api)
```

### Validar que a refatoração funcionou

Após a Fase 3 de cada projeto, execute manualmente:

```bash
# Projeto 1 e 3 (Python/Flask)
pip install -r requirements.txt
python app.py &
curl http://localhost:5000/api/health
# Espera: {"status": "ok"} — sem SECRET_KEY nem debug na resposta

# Projeto 2 (Node.js/Express)
npm install
node src/app.js &
curl http://localhost:3000/api/health
# Espera: {"status": "ok"}
```

Confirme que os endpoints originais documentados em cada projeto ainda respondem com os mesmos contratos de resposta.

---

## Estrutura do Repositório

```
desafio3/
├── README.md                              # Este arquivo
│
├── code-smells-project/                   # Projeto 1 — Python/Flask E-commerce
│   ├── .claude/skills/refactor-arch/      # Skill
│   ├── reports/
│   │   └── audit-project-1.md
│   └── src/                               # Código refatorado
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express LMS
│   ├── .claude/skills/refactor-arch/      # Skill (cópia)
│   ├── reports/
│   │   └── audit-project-2.md
│   └── src/                               # Código refatorado
│
├── task-manager-api/                      # Projeto 3 — Python/Flask Task Manager
│   ├── .claude/skills/refactor-arch/      # Skill (cópia)
│   ├── reports/
│   │   └── audit-project-3.md
│   └── src/                               # Código refatorado
│
└── reports/                               # Relatórios consolidados
    ├── audit-project-1.md
    ├── audit-project-2.md
    └── audit-project-3.md
```
