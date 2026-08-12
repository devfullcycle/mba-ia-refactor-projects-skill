# Desafio Skills — Refatoração Arquitetural Automatizada (MVC)

Repositório de entrega do desafio de **Skills** — uma skill `refactor-arch` agnóstica de tecnologia que analisa, audita e refatora projetos legados para o padrão **MVC**, aplicada a 3 projetos com stacks diferentes.

- **Ferramenta:** Claude Code (Custom Skills)
- **Skill:** `.claude/skills/refactor-arch/` (SKILL.md + 5 arquivos de referência)
- **Projetos-alvo:** `code-smells-project` (Python/Flask), `ecommerce-api-legacy` (Node.js/Express), `task-manager-api` (Python/Flask)

---

## A) Análise Manual

Análise manual dos 3 projetos para entender os problemas antes de construir a skill.

### Projeto 1 — `code-smells-project` (Python/Flask — API de E-commerce)

| # | Severidade | Problema | Onde | Relevância |
|---|---|---|---|---|
| 1 | CRITICAL | `SECRET_KEY` e `DEBUG=True` hardcoded | `app.py:7-8` | Vazamento de segredo; debug em produção |
| 2 | CRITICAL | SQL por concatenação em todas as queries | `models.py` (12 ocorrências) | SQL Injection |
| 3 | CRITICAL | `/admin/query` executa SQL arbitrário sem auth | `app.py:59` | Backdoor total no banco |
| 4 | CRITICAL | `/admin/reset-db` apaga todas as tabelas sem auth | `app.py:47` | Destruição de dados |
| 5 | CRITICAL | God Module — 4 domínios num arquivo | `models.py:1-314` | Impossível testar isoladamente |
| 6 | HIGH | Lógica de negócio nos controllers (email/sms/push via print) | `controllers.py:167-220` | Dificulta testes |
| 7 | HIGH | Cálculo de pedido e estoque no model | `models.py:133-169` | Model não abstrai só dados |
| 8 | HIGH | Estado global mutável (`db_connection`) | `database.py:4` | Comportamento imprevisível |
| 9 | MEDIUM | N+1 nas listagens de pedidos | `models.py:139-192` | Performance |
| 10 | MEDIUM | Senhas em texto puro | `models.py:122-130` | Vulnerabilidade |
| 11 | LOW | Prints de debug espalhados | `controllers.py` | Ruído |
| 12 | LOW | Duplicação `get_pedidos_usuario`/`get_todos_pedidos` | `models.py:171-233` | Manutenção |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express — LMS API com checkout)

| # | Severidade | Problema | Onde | Relevância |
|---|---|---|---|---|
| 1 | CRITICAL | Credenciais de produção hardcoded | `utils.js:1-7` | Vazamento de secrets |
| 2 | CRITICAL | `badCrypto()` — "hash" invertível (base64) | `utils.js:17` | Senhas decifráveis |
| 3 | CRITICAL | `/api/admin/financial-report` sem autenticação | `AppManager.js:80` | Dados financeiros expostos |
| 4 | CRITICAL | Estado global (`globalCache`, `totalRevenue`) | `utils.js:9-10` | Concorrência |
| 5 | HIGH | God Class `AppManager` — rotas+SQL+pagamento+matrícula | `AppManager.js:4` | Acoplamento total |
| 6 | HIGH | Lógica de checkout inteira dentro do handler HTTP | `AppManager.js:28-78` | Impossível testar |
| 7 | MEDIUM | N+1 no relatório financeiro (loops aninhados) | `AppManager.js:89-127` | Performance |
| 8 | MEDIUM | `DELETE /api/users/:id` deixa dados órfãos | `AppManager.js:131` | Integridade |
| 9 | LOW | Nomes enigmáticos (`usr`, `eml`, `c_id`, `cc`) | `AppManager.js:28` | Legibilidade |
| 10 | LOW | Erros como strings HTML soltas | `AppManager.js` | Padronização |

### Projeto 3 — `task-manager-api` (Python/Flask — API de Task Manager)

| # | Severidade | Problema | Onde | Relevância |
|---|---|---|---|---|
| 1 | CRITICAL | `SECRET_KEY` e credenciais SMTP hardcoded | `app.py:13`, `notification_service.py:7-10` | Vazamento de segredos |
| 2 | CRITICAL | `hashlib.md5` para senhas | `models/user.py:29,32` | Quebrável |
| 3 | CRITICAL | `to_dict()` expõe senha nas respostas | `models/user.py:16-25` | Exposição de credenciais |
| 4 | CRITICAL | Estado global de notificações em memória | `notification_service.py:6` | Vazamento de memória |
| 5 | HIGH | Lógica de negócio dentro das rotas | `routes/*` | Rotas grossas |
| 6 | HIGH | N+1 em relatórios (tasks por usuário em loop) | `report_routes.py:55-68` | Performance |
| 7 | HIGH | Token JWT falso (`'fake-jwt-token-...'`) | `user_routes.py:210` | Segurança falsa |
| 8 | HIGH | Lógica de "overdue" duplicada em 5 lugares | `routes/*` | Inconsistência |
| 9 | MEDIUM | `except:` bare sem padronização | `report_routes.py` | Erros difíceis de debugar |
| 10 | MEDIUM | Config implicita (URI, debug, porta) | `app.py:11,34` | Ambiente fixo |
| 11 | LOW | Imports e dependências mortas | vários | Manutenção |
| 12 | LOW | Magic values repetidos (`'pending'`, `'#000000'`) | `routes/*` | Legibilidade |

---

## B) Construção da Skill

### Decisões de design

A skill está em `.claude/skills/refactor-arch/` com **SKILL.md** (prompt orquestrador) + **5 arquivos de referência** (conhecimento de domínio), conforme as áreas obrigatórias do desafio:

| Arquivo | Área de conhecimento |
|---|---|
| `SKILL.md` | Orquestra as 3 fases sequenciais |
| `project-analysis-guidelines.md` | Heurísticas de detecção (linguagem, framework, banco, arquitetura) |
| `antipattern-catalog.md` | Catálogo com 13 anti-patterns classificados por severidade + APIs deprecated |
| `audit-report-template.md` | Template padronizado do relatório (Fase 2) |
| `mvc-guidelines.md` | Regras do MVC alvo (models, controllers, routes, config, middlewares) |
| `refactor-playbook.md` | 8+ padrões de transformação com exemplos antes/depois |

### Anti-patterns no catálogo (13, severidades distribuídas)

- **CRITICAL (4):** God Class/Module, Hardcoded Secrets, SQL Injection, Backdoor/Unsafe Admin Query
- **HIGH (3):** Business Logic in Controller/Route, Global Mutable State, Deprecated/Vulnerable API
- **MEDIUM (3):** N+1 Query, Mixed Responsibilities, Missing Input Validation
- **LOW (3):** Magic Values, Duplicate Code, Implicit Configuration

**APIs deprecated cobertas:** `badCrypto`/hash MD5 → `bcrypt`/`werkzeug`; `body-parser` → `express.json()`; `DEBUG=True` no código → env; SQL concatenação → parametrização.

### Como garanti o agnosticismo

- **Fase 1** identifica a stack por sinais (imports, package.json, requirements) em vez de assumir uma tecnologia.
- **Fase 2** cruza contra um catálogo de padrões (não de arquivos específicos), usando heurísticas genéricas.
- **Fase 3** segue guidelines de camadas (models/controllers/routes/config/middlewares) que mapeiam 1:1 entre Flask (Blueprints) e Express (Router).
- Testei a mesma skill (com cópia literal) nos 3 projetos — dois Python/Flask em estágios diferentes e um Node/Express.

### Desafios encontrados e soluções

1. **Projeto 2 tinha o SQL já parametrizado** — a skill precisava não "inventar" SQL injection. Resolvi auditando com honestidade (finding HIGH de "N+1 + lógica no handler" em vez de fabricar CRITICAL de injeção).
2. **Projeto 3 já era parcialmente organizado** — a refatoração focou em extrair lógica das rotas para `services/`, padronizar erros e centralizar config, sem reescrever o que já estava bom.
3. **Validação funcional** — cada projeto teve que **bootar e responder os endpoints originais** após a Fase 3 (não basta "compilar").
4. **Consistência de segredos/senhas** — ao trocar hash de senha (MD5→pbkdf2/bcrypt), o seed precisou ser atualizado junto para o login continuar funcionando (ex: projeto 3).

---

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---|---|---|---|---|---|
| 1. code-smells-project | 5 | 4 | 4 | 3 | 16 | `reports/audit-project-1.md` |
| 2. ecommerce-api-legacy | 5 | 3 | 3 | 2 | 13 | `reports/audit-project-2.md` |
| 3. task-manager-api | 4 | 4 | 4 | 2 | 14 | `reports/audit-project-3.md` |

Todos os projetos atingiram os critérios de aceite: **>= 5 findings**, **>= 1 CRITICAL/HIGH**, **Fase 1 correta**, **aplicação funcionando pós-refatoração**.

### Antes × Depois — Estrutura

**Projeto 1 — code-smells-project**

```
ANTES (monolítico)                    DEPOIS (MVC)
app.py  (rotas + admin)               app.py  (composition root, blueprints)
controllers.py (handlers grossos)     config/settings.py
models.py    (God module)             models/  → produto_model, usuario_model, pedido_model
database.py (global db)               services/ → produto_service, pedido_service, usuario_service
                                      controllers/ → produto, usuario, pedido
                                      routes/ → produto_routes, usuario_routes, pedido_routes, system_routes
                                      middlewares/error_handler.py
                                      database.py (getter lazy, schema/seed centralizados)
```

**Projeto 2 — ecommerce-api-legacy**

```
ANTES                                DEPOIS (MVC)
src/app.js  (Express + listen)       src/app.js (composition root, middleware de erro)
src/AppManager.js (God class)        src/config/index.js
src/utils.js   (secrets + badCrypto) src/models/ → db, userModel, courseModel
                                      src/services/ → checkoutService, reportService
                                      src/controllers/ → checkout, report, user
                                      src/routes/index.js (checkout + admin auth)
                                      src/middlewares/ → authMiddleware, errorHandler
                                      src/utils/security.js (bcrypt + cache scoped)
```

**Projeto 3 — task-manager-api**

```
ANTES (parcial)                      DEPOIS (MVC completo)
routes/* com toda lógica             routes/* finas (só delegam)
models/user.py MD5 + senha exposta   models/user.py (werkzeug, to_dict sem password)
app.py com secrets                   config/settings.py (env)
notification com credenciais         services/ → task, user, report, notification
                                     middlewares/error_handler.py (ApiError + decorator)
                                     app.py (create_app + register handlers)
```

### Checklist de Validação

#### Projeto 1 — code-smells-project
**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.1.1)
- [x] Domínio descrito corretamente (E-commerce API)
- [x] Nº de arquivos condiz com a realidade (4 arquivos / ~780 LOC)

**Fase 2 — Auditoria**
- [x] Relatório segue o template
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] 16 findings (>= 5)
- [x] Detecção de APIs deprecated (DEBUG no código, SQL concatenação)
- [x] Pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura MVC (`models/`, `controllers/`, `routes/`, `services/`, `middlewares/`, `config/`)
- [x] Config extraída para `config/settings.py` (sem hardcoded)
- [x] Models abstraem dados (`models/*_model.py` com parametrização)
- [x] Views/Routes separadas (Blueprints)
- [x] Controllers concentram o fluxo
- [x] Error handling centralizado (`middlewares/error_handler.py`)
- [x] Entry point claro (`app.py` = create_app + boot)
- [x] Aplicação inicia sem erros (boot verificado)
- [x] Endpoints originais respondem (health, produtos CRUD, busca, pedidos, login, relatório — todos 200/201)

#### Projeto 2 — ecommerce-api-legacy
**Fase 1 — Análise**
- [x] Linguagem (JavaScript/Node)
- [x] Framework (Express 4.18.2)
- [x] Domínio (LMS API com checkout)
- [x] Nº de arquivos (3 arquivos / ~278 LOC)

**Fase 2 — Auditoria**
- [x] Template do relatório
- [x] Arquivo + linhas exatos
- [x] Ordenação por severidade
- [x] 13 findings (>= 5)
- [x] Deprecated APIs (badCrypto)
- [x] Confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura MVC (`models/`, `services/`, `controllers/`, `routes/`, `middlewares/`, `config/`)
- [x] Config extraída (`src/config/index.js` via env)
- [x] Models abstraem dados (`userModel`, `courseModel`)
- [x] Routes finas (`src/routes/index.js`)
- [x] Controllers concentram fluxo
- [x] Error handling centralizado (`errorHandler.js` + 404/500)
- [x] Entry point claro (`src/app.js`)
- [x] App inicia sem erros
- [x] Endpoints originais respondem (checkout sucesso 200, pagamento recusado 400, relatório 401 sem token / 200 com token, delete user)
- [x] Admin protegido por auth (novo)

#### Projeto 3 — task-manager-api
**Fase 1 — Análise**
- [x] Linguagem (Python)
- [x] Framework (Flask 3.0.0 + SQLAlchemy)
- [x] Domínio (Task Manager)
- [x] Nº de arquivos (15 arquivos / ~1600 LOC)

**Fase 2 — Auditoria**
- [x] Template
- [x] Arquivo + linhas exatos
- [x] Ordenação por severidade
- [x] 14 findings (>= 5)
- [x] Deprecated APIs (MD5, debug config)
- [x] Confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura MVC com `config/`, `services/`, `middlewares/`
- [x] Config extraída (`config/settings.py` via env)
- [x] Models abstraem dados (werkzeug hash, `is_overdue` centralizada)
- [x] Routes finas (delegam a services)
- [x] Controllers/serviços concentram o fluxo
- [x] Error handling centralizado (`middlewares/error_handler.py`)
- [x] Entry point claro (`create_app()`)
- [x] App inicia sem erros
- [x] Endpoints originais respondem (tasks list/get/stats, reports summary, users, login, categories — todos 200/201)
- [x] Senha não mais exposta nas respostas (fix do CRITICAL)

### Logs de validação

**Projeto 1 — boots + endpoints:**
```
APP BOOT OK → 17 rotas registradas
GET  /health            → 200 {"status":"ok","database":"connected"}
GET  /produtos          → 200 (lista 10 produtos)
GET  /produtos/1        → 200 {"dados":{...},"sucesso":true}
POST /produtos          → 201 {"dados":{"id":11},"mensagem":"Produto criado"}
POST /login             → 200 {"dados":{...},"mensagem":"Login OK"}
POST /pedidos           → 201 {"pedido_id":1,"total":179.8}
PUT  /pedidos/1/status  → 200 {"mensagem":"Status atualizado"}
POST /admin/query       → 404 (backdoor removido)
```

**Projeto 2 — boots + endpoints:**
```
LMS rodando na porta 3000...
POST /api/checkout                    → 200 {"msg":"Sucesso","enrollment_id":2}
POST /api/checkout (card 5...)        → 400 {"error":"Pagamento recusado"}
POST /api/checkout (senha fraca)      → 400
GET  /api/admin/financial-report      → 401 (sem token) / 200 (com ADMIN_TOKEN)
DELETE /api/users/2                   → 200 {"msg":"Usuário removido ..."}
```

**Projeto 3 — boots + endpoints:**
```
APP BOOT OK → 22 rotas registradas
GET  /health          → 200 {"status":"ok",...}
GET  /tasks           → 200 (10 tasks, com overdue derivado)
GET  /tasks/stats     → 200 {"total":10,"done":1,"overdue":2,...}
POST /tasks           → 201 (nova task)
PUT  /tasks/1         → 200 (status done)
GET  /reports/summary → 200 (agregado sem N+1 pesado)
POST /login           → 200 {"message":"Login realizado com sucesso",...}
POST /login (errada)  → 401
POST /users (senha fraca) → 400
GET  /users           → 200 (sem password nos payloads)
```

### Observações: comportamento da skill em stacks diferentes

- **Flask (Python)** — a skill produziu **Blueprints** por domínio e `create_app()` (application factory). A validação usou `app.url_map` para confirmar as rotas.
- **Express (Node)** — a skill produziu **`express.Router()`** + middleware de auth e erro. O padrão `async/await` + `next(err)` substituiu callbacks aninhados.
- A skill se adaptou ao nível de organização: no monolito (P1) fez split completo; no parcial (P3) fez extração de services + padronização, sem destruir a estrutura existente.
- A mesma cópia da skill (`.claude/skills/refactor-arch/`) foi usada nos 3 projetos — prova de agnosticismo.

---

## D) Como Executar

### Pré-requisitos

- **Claude Code** instalado e autenticado (`claude --version`)
- Para Python: `python3` + `pip` + venv com `requirements.txt` de cada projeto
- Para Node: `node >= 18` + `npm install`

### Executar a skill em cada projeto

```bash
# Projeto 1 — Python/Flask (E-commerce)
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — Node.js/Express (LMS/checkout)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — Python/Flask (Task Manager)
cd ../task-manager-api
claude "/refactor-arch"
```

A skill executa 3 fases:
1. **Fase 1** — análise de stack/arquitetura/domínio (sem modificar arquivos).
2. **Fase 2** — auditoria e relatório no template, com arquivo:linha e severidades.
3. **Fase 3** — confirmação (`y`) → refatoração MVC + validação.

### Como validar que a refatoração funcionou

**Projeto 1:**
```bash
cd code-smells-project
.venv/bin/python app.py          # sobe em http://localhost:5000
curl localhost:5000/health        # {"status":"ok",...}
curl localhost:5000/produtos      # lista produtos
```

**Projeto 2:**
```bash
cd ecommerce-api-legacy
npm install
npm start                          # sobe em http://localhost:3000
curl -X POST localhost:3000/api/checkout -H 'Content-Type: application/json' \
  -d '{"usr":"Guilherme","eml":"g@e.com","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
ADMIN_TOKEN=secret node src/app.js  # define token para o relatório admin
```

**Projeto 3:**
```bash
cd task-manager-api
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py           # popula o banco (opcional, mas recomendado)
.venv/bin/python app.py            # sobe em http://localhost:5000
curl localhost:5000/tasks
curl localhost:5000/reports/summary
```

---

## Estrutura do repositório

```
mba-ia-refactor-projects-skill/
├── README.md                                # ← este documento
├── reports/
│   ├── audit-project-1.md                   # Auditoria Projeto 1 (16 findings)
│   ├── audit-project-2.md                   # Auditoria Projeto 2 (13 findings)
│   └── audit-project-3.md                   # Auditoria Projeto 3 (14 findings)
├── code-smells-project/                     # Projeto 1 — Python/Flask (E-commerce)
│   ├── .claude/skills/refactor-arch/        # Skill (original)
│   ├── app.py  config/  models/  services/
│   ├── controllers/  routes/  middlewares/
│   └── database.py
├── ecommerce-api-legacy/                    # Projeto 2 — Node.js/Express (LMS)
│   ├── .claude/skills/refactor-arch/        # Skill (cópia)
│   └── src/  config/  models/  services/  controllers/  routes/  middlewares/  utils/
└── task-manager-api/                        # Projeto 3 — Python/Flask (Task Manager)
    ├── .claude/skills/refactor-arch/        # Skill (cópia)
    └── app.py  config/  models/  services/  routes/  middlewares/  seed.py
```
