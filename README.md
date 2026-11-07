# Refatoração Arquitetural Automatizada — Skill `refactor-arch`

Skill agnóstica de tecnologia que **analisa, audita e refatora** qualquer
codebase para o padrão **MVC**, em 3 fases sequenciais (Análise → Auditoria com
confirmação humana → Refatoração validada).

A skill foi criada em `code-smells-project/.claude/skills/refactor-arch/` e
**copiada** para os outros dois projetos. Foi executada nos três projetos
fornecidos — dois Python/Flask e um Node.js/Express — provando que funciona
tanto em monolitos completamente desestruturados quanto em projetos já
parcialmente organizados.

```
.claude/skills/refactor-arch/
├── SKILL.md                              # orquestra as 3 fases (o "prompt")
└── references/
    ├── project-analysis.md               # heurísticas de detecção (Fase 1)
    ├── antipattern-catalog.md            # 18 anti-patterns + APIs deprecated (Fase 2)
    ├── report-template.md                # formato padrão do relatório (Fase 2)
    ├── architecture-guidelines.md        # regras do alvo MVC (Fase 3)
    └── refactoring-playbook.md           # 14 transformações antes/depois (Fase 3)
```

Relatórios de auditoria gerados: [`reports/audit-project-1.md`](reports/audit-project-1.md),
[`reports/audit-project-2.md`](reports/audit-project-2.md),
[`reports/audit-project-3.md`](reports/audit-project-3.md).

---

## A) Análise Manual

Antes de criar a skill, os três projetos foram lidos manualmente. Abaixo os
problemas mais relevantes de cada um (a auditoria completa gerada pela skill
está em `reports/`).

### Projeto 1 — `code-smells-project` (Python/Flask, E-commerce)

| # | Problema | Severidade | Local | Por que é relevante |
|---|----------|------------|-------|---------------------|
| 1 | SQL Injection por concatenação de string | CRITICAL | `models.py` (quase todas as queries) | Input do usuário entra direto no SQL — permite ler/alterar/apagar o banco e burlar o login |
| 2 | Credenciais hardcoded + segredo exposto em `/health` | CRITICAL | `app.py:7`, `controllers.py:289` | `SECRET_KEY` fixa no código e devolvida pela API |
| 3 | Senhas em texto puro e expostas nas respostas | CRITICAL | `database.py:76`, `models.py:83,99` | Vazamento direto de credenciais de todos os usuários |
| 4 | Endpoints admin perigosos (`/admin/reset-db`, `/admin/query`) | CRITICAL | `app.py:47-78` | Reset do banco e execução de SQL arbitrário sem autenticação |
| 5 | God File: `models.py` concentra tudo | CRITICAL | `models.py:1-315` | Dados + regra + SQL + formatação de 4 domínios juntos |
| 6 | Regra de negócio e efeitos colaterais no controller | HIGH | `controllers.py:208-210` | E-mail/SMS/push via `print` dentro do handler |
| 7 | Estado global mutável de conexão | HIGH | `database.py:4` | Conexão global compartilhada entre requisições |
| 8 | DEBUG ligado em produção | HIGH | `app.py:8,88` | Execução remota de código via debugger |
| 9 | Queries N+1 na listagem de pedidos | MEDIUM | `models.py:187-199,219-231` | 1 query por item/produto |
| 10 | Validação e serialização duplicadas | MEDIUM | `controllers.py`, `models.py` | Divergência silenciosa |
| 11 | Error handling genérico vazando `str(e)` | MEDIUM | `controllers.py` (todos os handlers) | Vaza detalhes internos |
| 12 | Prints de debug / magic numbers | LOW | `controllers.py`, `models.py:256-262` | Ruído e intenção obscura |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, LMS com checkout)

| # | Problema | Severidade | Local | Por que é relevante |
|---|----------|------------|-------|---------------------|
| 1 | Credenciais/chaves hardcoded | CRITICAL | `utils.js:1-7` | Chave `pk_live_...` de gateway e senha de banco no código |
| 2 | Log de cartão + chave do gateway | CRITICAL | `AppManager.js:45` | Número de cartão completo e segredo em texto puro no log |
| 3 | Hash de senha caseiro (`badCrypto`) | CRITICAL | `utils.js:17-23` | Loop de base64 — não é criptografia |
| 4 | God Class `AppManager` | CRITICAL | `AppManager.js:1-141` | Init de banco + rotas + regra + pagamento numa classe |
| 5 | Regra de negócio na rota + callback hell | HIGH | `AppManager.js:28-128` | 4+ níveis de callbacks e contadores manuais |
| 6 | Estado global mutável | HIGH | `utils.js:9-10` | `globalCache` e `totalRevenue` de módulo |
| 7 | Query N+1 no relatório financeiro | MEDIUM | `AppManager.js:83-128` | Queries por curso × matrícula |
| 8 | API legada do sqlite3 (callbacks) — **deprecated** | MEDIUM | `AppManager.js` inteiro | Estilo que gera o callback hell |
| 9 | Deleção deixa dados órfãos | MEDIUM | `AppManager.js:131-137` | A própria resposta admite "ficaram sujos" |
| 10 | Nomes crípticos / `console.log` | LOW | `AppManager.js:29-33,45` | `u,e,p,cid,cc`; log improvisado |

### Projeto 3 — `task-manager-api` (Python/Flask, Task Manager — já parcialmente organizado)

| # | Problema | Severidade | Local | Por que é relevante |
|---|----------|------------|-------|---------------------|
| 1 | Hash de senha MD5 sem salt | CRITICAL | `models/user.py:29,32` | MD5 é quebrado e sem salt |
| 2 | Hash de senha exposto na serialização | CRITICAL | `models/user.py:16-25` | `to_dict()` devolve `password` em 3 endpoints |
| 3 | `SECRET_KEY` e credenciais SMTP hardcoded | CRITICAL | `app.py:13`, `services/notification_service.py:9-10` | Segredos versionados |
| 4 | Regra de negócio pesada nas rotas | HIGH | `routes/report_routes.py`, `routes/task_routes.py` | `summary_report`/`get_tasks` fazem tudo inline |
| 5 | Serialização e lógica `overdue` duplicadas | HIGH | 3 rotas + model | Mesmo cálculo reimplementado |
| 6 | Service morto + validação duplicada | HIGH | `notification_service.py`, `utils/helpers.py` | Código morto e 3 fontes de validação |
| 7 | Query N+1 em listagem e relatórios | MEDIUM | `task_routes.py:41-57` | `User.query.get()`/`Category.query.get()` por task |
| 8 | APIs **deprecated** (`datetime.utcnow()`, `Model.query.get()`) | MEDIUM | vários | `utcnow` deprecated no 3.12+, `query.get` legado no SQLAlchemy 2.x |
| 9 | Imports mortos / prints de debug | LOW | `app.py:7`, `routes/*` | Ruído |
| 10 | Retornos booleanos verbosos | LOW | `models/*` | `if/else` onde a condição bastaria |

---

## B) Construção da Skill

### Decisões de design

- **`SKILL.md` é o orquestrador (o "prompt")**: contém apenas o passo a passo
  das 3 fases, os princípios invioláveis (confirmação humana, sem regressão de
  comportamento, segredos fora do código) e uma **tabela que mapeia cada fase
  ao arquivo de referência** a ser lido sob demanda. Isso mantém o SKILL.md
  curto e empurra o conhecimento de domínio para os arquivos de referência,
  carregados só quando necessários (progressive disclosure).
- **5 arquivos de referência**, cobrindo exatamente as 5 áreas exigidas:
  detecção/análise, catálogo de anti-patterns, template de relatório,
  guidelines de arquitetura e playbook de transformações.
- **Fases com fronteiras rígidas**: a Fase 2 é somente leitura e termina
  **pausando para confirmação humana** (`[y/n]`); nada é escrito antes disso.
  A Fase 3 só é considerada concluída após **validação real** (boot + endpoints).

### Anti-patterns incluídos no catálogo e por quê

O catálogo tem **18 anti-patterns** (AP-01 a AP-18) com severidade distribuída,
escolhidos a partir dos problemas reais encontrados na análise manual para que a
skill detectasse exatamente aquilo que os projetos continham:

- **CRITICAL** — God Class, segredos hardcoded, SQL Injection, senha em texto
  puro/hash fraco, endpoints admin perigosos.
- **HIGH** — fat controller, estado global mutável, falta de DI, callback hell,
  DEBUG em produção.
- **MEDIUM** — N+1, validação ausente/duplicada, código duplicado, **APIs
  deprecated (AP-13)**, error handling espalhado, lógica em `utils`.
- **LOW** — prints de debug, magic numbers.

A entrada **AP-13 (APIs deprecated)** é obrigatória e traz uma tabela
"deprecated → equivalente moderno" (`datetime.utcnow()` → `datetime.now(UTC)`,
`Model.query.get()` → `db.session.get()`, `new Buffer()` → `Buffer.from()`,
MD5 → bcrypt/werkzeug, callbacks sqlite3 → Promises, etc.).

### Como garanti que a skill é agnóstica de tecnologia

- As heurísticas de detecção partem **sempre de evidências** (manifesto de
  dependências, imports, extensões) — nunca de uma stack assumida.
- O catálogo e as guidelines falam em **conceitos** (God Class, N+1, DI,
  camadas), não em APIs específicas.
- O **playbook traz exemplos tanto em Python/Flask quanto em Node/Express** para
  o mesmo padrão, reforçando que a transformação é conceitual.
- A mesma skill, copiada sem alteração, rodou nos 3 projetos e em 2 stacks.

### Desafios encontrados e como resolvi

- **Não quebrar contratos de API**: preservei paths, métodos, formatos de
  resposta e status codes. Mudanças de segurança deliberadas (parar de devolver
  `senha`/`secret_key`) foram tratadas como correção e registradas no relatório.
- **Trap do `datetime.utcnow()`**: trocar por `datetime.now(timezone.utc)`
  (aware) quebraria comparações com as colunas `DateTime` naive existentes.
  Resolvi com um helper `now_utc()` que retorna UTC **naive**
  (`datetime.now(timezone.utc).replace(tzinfo=None)`) — remove a deprecação sem
  quebrar comparações.
- **Hash de senha sem dependências nativas no Node**: em vez de `bcrypt`
  (precisa compilar), usei `crypto.scrypt` nativo com salt.
- **Porta 5000 ocupada pelo AirPlay no macOS**: a config lê `PORT` do ambiente,
  então validei nas portas 5055/3030/5066 sem tocar no código.
- **Projeto parcialmente organizado (nº 3)**: a guideline instrui a skill a
  **adaptar-se** — preservar o que já era bom (blueprints, models) e focar em
  segurança, extração de regra para services, N+1 e deprecações, em vez de
  reescrever tudo.

---

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---------|-------|:--------:|:----:|:------:|:---:|:-----:|
| 1 — code-smells-project | Python/Flask | 5 | 4 | 3 | 2 | **14** |
| 2 — ecommerce-api-legacy | Node/Express | 4 | 4 | 4 | 2 | **14** |
| 3 — task-manager-api | Python/Flask | 3 | 3 | 4 | 3 | **13** |

Todos atingem os critérios de aceite: ≥ 5 findings e ≥ 1 CRITICAL/HIGH.

### Comparação antes/depois da estrutura

**Projeto 1 — de monolito plano para MVC completo**

```
ANTES                          DEPOIS
app.py (rotas + admin)         app.py                      (composition root)
controllers.py (293 l.)        config/{settings,database}.py
models.py (315 l., SQL cru)    models/{produto,usuario,pedido}_model.py
database.py (global)           services/{pedido,relatorio}_service.py, notifier.py
                               controllers/{produto,usuario,pedido,sistema}_controller.py
                               views/routes.py
                               middlewares/error_handler.py
                               .env.example
```

**Projeto 2 — de God Class para camadas (Express)**

```
ANTES                          DEPOIS
src/app.js                     src/app.js                  (composition root async)
src/AppManager.js (God Class)  src/config/{index,database}.js
src/utils.js (segredos+global) src/models/{user,course,enrollment,payment,auditLog}Model.js
                               src/services/{checkout,report,password,paymentGateway,cache}.js
                               src/controllers/{checkout,report,user}Controller.js
                               src/routes/index.js
                               src/middlewares/{errorHandler,httpError}.js
                               src/logger.js, .env.example
```

**Projeto 3 — de camadas parciais para MVC coeso (Flask)**

```
ANTES                          DEPOIS (preserva o bom, adiciona o que faltava)
app.py (create_all no import)  app.py                      (application factory)
models/ (MD5, senha exposta)   config/settings.py          (novo)
routes/ (regra inline, N+1)    models/ (werkzeug, to_dict sem senha, is_overdue)
services/ (notification morto) services/{task,report,validators,notification}_service.py
utils/helpers.py (dead code)   routes/ (finos, delegam aos services)
                               middlewares/error_handler.py (novo)
                               utils/helpers.py (limpo, now_utc), .env.example
```

### Checklist de validação (preenchido para os 3 projetos)

Legenda: ✅ atende · ⚠️ adaptado (ver nota)

| Item | P1 | P2 | P3 |
|------|:--:|:--:|:--:|
| **Fase 1** — Linguagem detectada | ✅ Python | ✅ Node.js | ✅ Python |
| Framework detectado | ✅ Flask 3.1 | ✅ Express 4.18 | ✅ Flask 3.0 + SQLAlchemy |
| Domínio descrito | ✅ E-commerce | ✅ LMS/checkout | ✅ Task Manager |
| Nº de arquivos condiz | ✅ 4 | ✅ 3 | ✅ 11 |
| **Fase 2** — Segue o template | ✅ | ✅ | ✅ |
| Cada finding com arquivo:linha | ✅ | ✅ | ✅ |
| Ordenado por severidade | ✅ | ✅ | ✅ |
| ≥ 5 findings | ✅ 14 | ✅ 14 | ✅ 13 |
| Detecção de APIs deprecated | ⚠️ não aplicável¹ | ✅ sqlite3 callbacks | ✅ utcnow/query.get |
| Pausa e pede confirmação | ✅ | ✅ | ✅ |
| **Fase 3** — Estrutura MVC | ✅ | ✅ | ✅ |
| Config sem hardcoded | ✅ | ✅ | ✅ |
| Models abstraem dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ | ✅ | ✅ |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ routes+services² |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ | ✅ | ✅ factory |
| App inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem | ✅ | ✅ | ✅ |

¹ Projeto 1 não usa APIs deprecated relevantes; a categoria foi verificada.
² Em Flask com Blueprints, a rota atua como controller (fluxo) e delega a
  regra de negócio aos services — adaptação prevista nas guidelines.

### Logs das aplicações rodando após a refatoração

**Projeto 1** (`PORT=5055`):
```
$ curl /health  → {"status":"ok","database":"connected","counts":{"produtos":10,"usuarios":3,"pedidos":0},"versao":"1.0.0"}
$ curl /usuarios → keys: [criado_em, email, id, nome, tipo]          # sem "senha"
$ POST /login admin/admin123 → {"sucesso":true,"mensagem":"Login OK"} # hash werkzeug
$ POST /pedidos → {"pedido_id":1,"total":12089.88}                    # JOIN, sem N+1
$ /produtos/busca?categoria=geral' OR '1'='1 → total: 0               # SQLi bloqueado
$ POST /admin/reset-db → 403 (desabilitado por padrão)
```

**Projeto 2** (`PORT=3030`):
```
$ POST /api/checkout (card 4111...) → {"msg":"Sucesso","enrollment_id":2}
$ POST /api/checkout (card 5111...) → {"error":"Pagamento recusado"}   # 400
$ GET  /api/admin/financial-report → [{"course":"Clean Architecture","revenue":997,...}]  # JOIN único
$ DELETE /api/users/1 → cascata; report passa a mostrar revenue 0, students []  # sem órfãos
[INFO] Processando pagamento de 497 (cartão ****4444)                  # cartão mascarado, sem chave
```

**Projeto 3** (`PORT=5066`):
```
$ GET /tasks → 10 tasks com user_name/category_name/overdue           # joinedload, sem N+1
$ GET /tasks/stats → {"total":10,"done":1,"overdue":2,"completion_rate":10.0}
$ POST /login joao/1234 → token ok; user sem "password"               # werkzeug
$ GET /reports/summary → overview+overdue+user_productivity           # agregado em memória
$ GET /users → keys sem "password"
```

### Observações sobre o comportamento em stacks diferentes

- A **mesma skill, sem edição**, detectou corretamente Python/Flask e
  Node/Express e adaptou a Fase 3 a cada idioma (Blueprints vs. `Router`,
  `werkzeug` vs. `crypto.scrypt`, DI por parâmetro vs. por construtor).
- O **nível de organização inicial** mudou o esforço da Fase 3, como esperado:
  nos projetos 1 e 2 (monolitos) a árvore MVC foi criada do zero; no projeto 3
  a skill preservou a estrutura existente e corrigiu segurança, performance e
  acoplamento — exatamente a adaptação descrita nas guidelines.
- O requisito de **não regredir comportamento** foi o fio condutor: toda
  mudança de resposta observável foi deliberada (remoção de segredos/senha) e
  documentada.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.claude.com/en/docs/claude-code) instalado e autenticado.
- Python 3.11+ (projetos 1 e 3) e Node.js 18+ (projeto 2).

### Invocando a skill

A skill vive em `.claude/skills/refactor-arch/` dentro de cada projeto. Entre na
pasta do projeto e invoque:

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

A skill roda a Fase 1 (análise) → Fase 2 (auditoria, salva em `reports/` e
**pede confirmação `[y/n]`**) → Fase 3 (refatoração + validação) após o `y`.

### Como validar que a refatoração funcionou

**Projeto 1 (Flask):**
```bash
cd code-smells-project
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PORT=5055 .venv/bin/python app.py          # PORT evita o AirPlay na 5000 (macOS)
curl http://localhost:5055/health
curl http://localhost:5055/produtos
```

**Projeto 2 (Express):**
```bash
cd ecommerce-api-legacy
npm install
PORT=3030 node src/app.js
curl -X POST http://localhost:3030/api/checkout -H 'Content-Type: application/json' \
  -d '{"usr":"Gui","eml":"gui@x.com","pwd":"s","c_id":2,"card":"4111222233334444"}'
curl http://localhost:3030/api/admin/financial-report
```

**Projeto 3 (Flask + SQLAlchemy):**
```bash
cd task-manager-api
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py                   # popula o banco (senhas com hash)
PORT=5066 .venv/bin/python app.py
curl http://localhost:5066/tasks
curl http://localhost:5066/reports/summary
```

Cada projeto traz um `.env.example` — copie para `.env` para customizar segredos
e porta.

### Ordem de execução sugerida

1. **Análise manual** dos 3 projetos (seção A).
2. **Criar a skill** em `code-smells-project/.claude/skills/refactor-arch/`.
3. **Executar no Projeto 1** (monolito Flask) e salvar `reports/audit-project-1.md`.
4. **Copiar a skill** para os projetos 2 e 3 e executar, salvando os respectivos
   relatórios.
5. **Validar** cada projeto (boot + endpoints) e commitar o código refatorado.
