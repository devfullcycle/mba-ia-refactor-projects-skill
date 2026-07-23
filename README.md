# Skill de Auditoria e Refatoração Arquitetural — `refactor-arch`

Skill agnóstica de tecnologia que **analisa → audita → refatora** qualquer backend legado
para o padrão **MVC**, validando que a aplicação continua funcionando.

Este repositório contém a skill `refactor-arch` e sua execução nos 3 projetos-alvo:
`code-smells-project` (Python/Flask), `ecommerce-api-legacy` (Node.js/Express) e
`task-manager-api` (Python/Flask + SQLAlchemy).

> **Ferramenta:** Claude Code (convenção `.claude/skills/`). A skill foi criada dentro de
> `code-smells-project/.claude/skills/refactor-arch/` e copiada para os outros dois projetos.
> Cada projeto contém a skill completa + o código refatorado (Fase 3) + o relatório em `reports/`.

---

## A) Análise Manual

Antes de criar a skill, analisei manualmente os três projetos. O mínimo exigido era
5 problemas por projeto (≥1 CRITICAL/HIGH, ≥2 MEDIUM, ≥2 LOW); todos os três entregaram
**20 findings** cada. Resumo dos principais achados (detalhe completo em `reports/`).

### Projeto 1 — `code-smells-project` (Python/Flask — E-commerce)
| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | SQL Injection (string concat) em **toda** query | `models.py:28,110,289-297` | Bypass de auth, exfiltração e destruição remota |
| CRITICAL | `SECRET_KEY` hardcoded **e** vazada pelo `/health` | `app.py:7`, `controllers.py:289` | Permite forjar tokens; segredo exposto a anônimos |
| CRITICAL | `/admin/query` executa SQL arbitrário; `/admin/reset-db` sem auth | `app.py:47-78` | Destruição total do banco por qualquer chamador |
| CRITICAL | Senhas em texto puro + login por SQL plaintext | `models.py:110`, `database.py:75-79` | Vazamento de credenciais |
| CRITICAL | God File (4 arquivos misturam DB+regras+rotas) | `app.py`/`controllers.py`/`models.py` | Intestável, alto blast radius |
| HIGH | Regra de negócio (descontos, status, notificações) nos controllers | `controllers.py:43-54,208-250` | Regras não reutilizáveis/testáveis |
| MEDIUM | Queries N+1 em listagem de pedidos | `models.py:171-233` | Latência O(pedidos×itens) |
| MEDIUM | `except Exception` repetido 17× vaza internals | `controllers.py` (todos handlers) | Info disclosure + esconde bugs |
| LOW | Magic numbers (faixas de desconto, porta) | `models.py:256-262` | Difícil de manter |
| LOW | `print()` como logger; `id` sobia builtin | `controllers.py`, `models.py` | Sem observabilidade; legibilidade |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express — LMS)
| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | God Class `AppManager` (DB+schema+rotas+pagamento) | `AppManager.js:1-141` | Intestável, manutenção impraticável |
| CRITICAL | Segredos `pk_live_` no código **e** `.env` commitado | `utils.js:1-7`, `.env:1-4` | Credenciais de produção no git |
| CRITICAL | `badCrypto` (reversível/colisivo) + seed `'123'` plaintext | `utils.js:17-23`, `AppManager.js:18` | Todas as senhas comprometidas |
| CRITICAL | PAN + gateway key logados no stdout | `AppManager.js:45` | Violação PCI-DSS |
| CRITICAL | Sem auth em `/api/admin/financial-report` e `DELETE /users/:id` | `AppManager.js:80,131` | Acesso total anônimo |
| HIGH | Multi-write sem transação (matrícula+pagamento+auditoria) | `AppManager.js:50-57` | Estado inconsistente em falha |
| HIGH | Callback hell (4-5 níveis) + sem DI | `AppManager.js:37-77` | Fluxo intratável |
| MEDIUM | N+1 no relatório financeiro | `AppManager.js:89-125` | Latência quadrática |
| MEDIUM | Validação só checa truthiness; campos `usr/eml/c_id` | `AppManager.js:29-35` | Dados inválidos aceitos |
| LOW | `let` onde cabe `const`; `sqlite3.verbose()` deprecated | `AppManager.js:1,29-33` | Estilo / ruído em prod |

> **Nota:** neste projeto o SQL **já era** parametrizado (`?`) — então SQL Injection (C1)
> **não se aplica**. Isso provou que a skill não detecta falsos positivos: o catálogo
> distingue placeholders seguros de concatenação.

### Projeto 3 — `task-manager-api` (Python/Flask + SQLAlchemy)
| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | Senhas com **MD5** sem salt | `models/user.py:29` | Quebra trivial via rainbow table |
| CRITICAL | Hash de senha exposto em `to_dict()` | `models/user.py:21` | Vazamento em `GET/POST/PUT /users` e `/login` |
| CRITICAL | Credenciais SMTP hardcoded + `.env` commitado | `notification_service.py:7-10`, `.env` | Conta de email comprometida |
| CRITICAL | `SECRET_KEY` hardcoded | `app.py:13` | Forja de tokens |
| HIGH | JWT **fake** nunca verificado; sem authz (role bypass) | `user_routes.py:210` | Qualquer um vira admin |
| HIGH | N+1 em tasks/users/reports | `task_routes.py:42,51`, `report_routes.py:56` | Latência O(N) |
| HIGH | Regra "overdue" duplicada 6× (helper canonical morto) | vários | Bugs se escondem na divergência |
| MEDIUM | CRUD de Categoria no blueprint errado (`report_bp`) | `report_routes.py:157-223` | Coesão ruim |
| MEDIUM | `datetime.utcnow()` e `Model.query.get()` deprecated | vários | Incompatível forward |
| LOW | Dead code (`NotificationService`, helpers, ~80% morto) | `services/`, `utils/helpers.py` | Confunde auditores |

---

## B) Construção da Skill

### Estrutura
```
.claude/skills/refactor-arch/
├── SKILL.md                              # prompt em 3 fases (Analysis → Audit → Refactor)
└── references/
    ├── 01-project-analysis.md            # heurísticas de detecção de stack/domínio/arquitetura
    ├── 02-anti-pattern-catalog.md        # 17 anti-patterns + seção dedicada de APIs deprecated
    ├── 03-report-template.md             # formato exato do relatório da Fase 2
    ├── 04-mvc-guidelines.md              # regras das camadas MVC (Python e JS)
    └── 05-refactor-playbook.md           # 13 transformações antes/depois (Python e JS)
```

### Decisões de design
- **SKILL.md é um prompt, as referências são conhecimento.** O `SKILL.md` orquestra as 3 fases
  e aponta **quando** ler cada referência (Phase 1 lê `01`, Phase 2 lê `02`+`03`, Phase 3 lê
  `04`+`05`). Isso mantém o prompt curto e o contexto focado por fase.
- **Catálogo com 17 anti-patterns** (exigido ≥8) cobrindo as 4 severidades, **mais uma seção
  dedicada de detecção de APIs deprecated** (exigido pelo enunciado). Cada pattern tem
  **sinais de detecção concretos e grep-áveis** (ex.: *"query SQL dentro de loop for"* em vez
  de *"código ruim"*).
- **Playbook com 13 transformações antes/depois** (exigido ≥8), cada uma em **Python e JS**,
  para a skill se aplicar à stack detectada na Fase 1.
- **Gate obrigatório na Fase 2:** o `SKILL.md` tem uma regra `HARD STOP` — nenhum arquivo é
  tocado antes de um `y/n` explícito do humano.

### Por que cada anti-pattern entrou no catálogo
Os 8+ patterns foram escolhidos a partir dos problemas reais dos 3 projetos:
**SQL Injection**, **Hardcoded Secrets**, **God Class**, **Insecure Password Storage**,
**Destructive/Unauthenticated endpoints** e **Sensitive Data Leakage** (CRITICAL) cobrem os
riscos de segurança; **Business Logic in Routes**, **Global Mutable State**, **Missing Auth**,
**Callback Hell/no-DI** e **Non-atomic writes** (HIGH) cobrem SOLID/MVC; **N+1**, **Bare
Exception/Error leak**, **Missing Validation** e **Code Duplication** (MEDIUM) cobrem
qualidade/performance; e **Magic Numbers**, **print-as-logger**, **Dead Code/Poor Naming** e
**Repo Hygiene** (LOW) cobrem legibilidade. A seção deprecated cobre `datetime.utcnow()`,
`Model.query.get()`, `flask.__version__`, `sqlite3.verbose()`, `body-parser` standalone, etc.

### Como a skill é agnóstica de tecnologia
1. A **Fase 1 detecta a stack** via manifests (`requirements.txt` vs `package.json`) e imports,
   sem assumir nada — a stack detectada dirige o resto.
2. O **catálogo e o playbook carregam exemplos em Python e JS**; a skill usa o da stack
   detectada.
3. As **heurísticas de arquitetura** são descritas por forma (monolítico vs God class vs
   layered cosmético), não por nome de arquivo.
4. A validação final **adapta-se à stack**: `test_client()` para Flask, boot HTTP + kill para
   Express.

### Desafios encontrados (e como resolvi)
- **Falsos positivos de SQL Injection:** o projeto 2 usa placeholders `?`. O catálogo
  explicitamente diz *"placeholders são SEGUROS — não flague"*, evitando falso positivo.
- **Processo órfão do reloader Werkzeug:** ao validar com `debug=True`, o filho do reloader
  ficou vivo na porta 5000 e gerou 404s falsos no teste do projeto 3. Solução: validar apps
  Flask **em-processo com `test_client()`** (sem porta/reloader).
- **Transações SQLite + Python sqlite3:** o modo padrão conflita com `BEGIN` explícito
  (*"cannot commit - no transaction is active"*). Solução: abrir a conexão com
  `isolation_level=None` e o **service** ser dono do `BEGIN/COMMIT/ROLLBACK`.
- **Datetimes naive vs aware:** SQLite armazena datetimes *sem tz*, então comparar com
  `datetime.now(timezone.utc)` (aware) levanta `TypeError`. Solução: comparar com
  `now(timezone.utc).replace(tzinfo=None)` — evita o `utcnow()` deprecated sem quebrar.
- **marshmallow:** `fields.Number` é abstrato nesta versão; trocado por `fields.Float`.

---

## C) Resultados

### Resumo dos relatórios de auditoria
| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---:|---:|---:|---:|---:|
| code-smells-project | Python/Flask | 7 | 5 | 5 | 4 | **20** |
| ecommerce-api-legacy | Node/Express | 5 | 5 | 6 | 4 | **20** |
| task-manager-api | Python/Flask+SQLA | 4 | 7 | 5 | 4 | **20** |

Todos os projetos cumpriram os critérios de aceite: ≥5 findings, ≥1 CRITICAL/HIGH.

### Antes × Depois (estrutura)

**Projeto 1 — code-smells-project**
- Antes: 4 arquivos raiz (`app.py`, `controllers.py`, `models.py`, `database.py`) misturando tudo.
- Depois: app factory + `config/`, `core/`, `models/`, `services/`, `controllers/`, `routes/`,
  `middlewares/`, `schemas/`. SQL parametrizado, bcrypt, secret em env, error handler central,
  validação marshmallow, pedido transacional.

**Projeto 2 — ecommerce-api-legacy**
- Antes: God Class `AppManager.js` (141 linhas) + `utils.js`.
- Depois: `src/{app,server}.js` (factory separada do listen) + `config/`, `db/`, `models/`,
  `services/`, `controllers/`, `routes/`, `middlewares/`, `utils/`. async/await, sqlite3
  promisificado, bcrypt (fim do `badCrypto`), config por env, checkout transacional,
  delete em cascata, PAN redacted, error middleware.

**Projeto 3 — task-manager-api**
- Antes: pastas `models/routes/services/utils` mas services mortos; rotas gordas batendo direto
  no DB.
- Depois: `config/`, `core/`, `middlewares/`, **`controllers/`** + `services/` reais, rotas
  finas, `category_routes` separado, bcrypt (fim do MD5), sem leak de senha, env-driven,
  APIs deprecated removidas (`now(timezone.utc)`, `db.session.get`/`select`).

### Checklist de validação
**Projeto 1 (code-smells-project)** — app factory ✓ · config extraído ✓ · models ✓ ·
routes ✓ · controllers concentram o fluxo ✓ · error handling centralizado ✓ · entry point
claro ✓ · **boot OK** ✓ · 18 endpoints respondem (0× 500) ✓ · SQL injection→401, sem leak
de senha/secret, admin write→403 ✓

**Projeto 2 (ecommerce-api-legacy)** — `app.js`/`server.js` ✓ · config ✓ · models ✓ ·
routes ✓ · controllers ✓ · error middleware ✓ · **boot OK** ✓ · 3 endpoints respondem
(checkout 200, denied 400, report 200, delete 200) ✓ · PAN redacted ✓

**Projeto 3 (task-manager-api)** — MVC completo ✓ · config ✓ · models ✓ · routes finas ✓ ·
controllers ✓ · error handler ✓ · **boot OK** ✓ · 23 endpoints respondem (0× 500) ✓ · sem
leak de senha, 401/409/400/404 corretos ✓

### Logs de boot (após refatoração)
```
# Projeto 1 (test_client em-processo)
=== BOOT: OK (create_app imported without error) ===
GET / 200 · GET /health 200 · GET /produtos 200 · GET /usuarios 200
POST /login admin@loja.com/admin123 -> 200 · POST /pedidos -> 201

# Projeto 2 (npm start)
[app] Banco inicializado e populado.
[app] LMS API rodando na porta 3000 (development)
[app] Processando cartao (ultimos 4: 4444)
POST /api/checkout -> 200 · GET /api/admin/financial-report -> 200

# Projeto 3 (test_client em-processo)
=== BOOT: OK ===
GET /tasks 200 · GET /reports/summary 200 · GET /users/1 200
POST /login joao@email.com/1234 -> 200 · password leak /users/1? False
```

### Observações entre stacks
- A skill aplicou o **mesmo** catálogo/playbook nas duas stacks sem mudanças — provando
  agnosticidade real.
- O projeto 2 (Node) precisou de `async/await` + promisificação do sqlite3; o Python usou
  app factory + transações explícitas — transformações diferentes do **mesmo** playbook.
- O projeto 3, por já ter pastas, exigiu **menos** reestruturação e **mais** correção de
  segurança/APIs deprecated — confirmando a recomendação do enunciado ("projetos diferentes
  exigem adaptação").

---

## D) Como Executar

### Pré-requisitos
- **Claude Code** instalado e autenticado (ou uma ferramenta compatível que leia
  `.claude/skills/`). A skill também pode ser executada por qualquer agente que leia o
  `SKILL.md` (foi assim que esta entrega foi produzida).
- **Python 3.12+** e **Node.js 20+** instalados.
- Python: crie um venv por projeto e instale as deps:
  ```bash
  cd code-smells-project && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
  cd ../task-manager-api  && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
  ```
- Node:
  ```bash
  cd ecommerce-api-legacy && npm install
  ```

### Executar a skill
```bash
# Projeto 1 — Python/Flask E-commerce
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — Node/Express LMS
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — Python/Flask Task Manager
cd ../task-manager-api
claude "/refactor-arch"
```
A cada execução: **Fase 1** imprime o resumo da stack · **Fase 2** gera o relatório (e
**pausa** pedindo `y/n`) · **Fase 3** refatora para MVC e valida.

### Validar que a refatoração funcionou
```bash
# Projeto 1 — boot + endpoints (test_client)
cd code-smells-project
python -c "from app import app; c=app.test_client(); print(c.get('/health').status_code, c.get('/produtos').status_code)"

# Projeto 2 — boot HTTP
cd ../ecommerce-api-legacy
npm start   # em outro terminal:
curl -X POST http://localhost:3000/api/checkout -H "Content-Type: application/json" \
  -d '{"usr":"T","eml":"t@x.com","pwd":"1","c_id":1,"card":"4111222233334444"}'

# Projeto 3 — popular e testar
cd ../task-manager-api
python seed.py
python -c "from app import app; c=app.test_client(); print(c.get('/tasks').status_code, c.post('/login', json={'email':'joao@email.com','password':'1234'}).status_code)"
```
Espera-se **status 2xx** (ou 4xx controlado para entradas inválidas) e **nenhum 500** em todos
os endpoints originais. Os relatórios completos estão em `reports/audit-project-{1,2,3}.md`.
