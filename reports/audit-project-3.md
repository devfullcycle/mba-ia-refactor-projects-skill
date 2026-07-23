# Architecture Audit Report — task-manager-api

## Phase 1: Project Analysis

### Unidade 1 — API HTTP

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language(s):   Python; 15 fontes .py, requirements.txt e README.md
Runtime(s):    CPython 3.12.11 no ambiente local; versão suportada pelo projeto não declarada
Framework(s):  Flask 3.0.0, Flask-SQLAlchemy 3.1.1, Flask-CORS 4.0.0
Dependencies:  pip/requirements.txt; Marshmallow e Requests declarados sem uso observado
Persistence:   SQLite via Flask-SQLAlchemy; tabelas users, categories e tasks
Domain:        Gestão de tarefas, usuários, categorias, autenticação e relatórios
Architecture:  Monólito parcialmente em camadas; routes acumulam adapter, negócio, queries e apresentação
Entry points:  app.py; comando descoberto: python app.py
Source files:  16 técnicos analisados: 15 Python + requirements.txt
Contracts:     22 operações HTTP declaradas
Tests:         Nenhuma suíte, configuração ou comando encontrado
================================
```

Evidências principais: [app.py](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/app.py:1), [requirements.txt](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/requirements.txt:1), [database.py](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/database.py:1).

### Unidade 2 — Seed CLI

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language(s):   Python
Runtime(s):    Mesmo ambiente da API
Framework(s):  Flask-SQLAlchemy
Dependencies:  Compartilha app, db e models
Persistence:   Apaga e recria dados em users, categories e tasks
Domain:        Carga de dados iniciais
Architecture:  CLI acoplada ao bootstrap HTTP e ao ORM
Entry points:  seed.py; comando descoberto: python seed.py
Source files:  Compartilhados com a unidade principal
Contracts:     1 contrato CLI destrutivo
Tests:         Ausentes
================================
```

Evidência: [seed.py:2–99](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/seed.py:2).

## Metadata

- **Codebase root:** [task-manager-api](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api)
- **Delivery repository root:** `/home/matheussouza/learn/mba-ia-refactor-projects-skill`
- **Version-control snapshot:** `6d1ce6248c3e956801010a89d8bdaab48029bf30`
- **Audited source fingerprint:** tree `028909091b9c8f44b47add85549d1ae4aa1930a3` em `6d1ce6248c3e956801010a89d8bdaab48029bf30`
- **Preexisting changes:** nenhum item no escopo segundo `git status --porcelain -- task-manager-api`
- **Audited at:** `2026-07-22T20:19:19-04:00`
- **Scope:** 15 fontes Python, `requirements.txt` e documentação de suporte
- **Exclusions:** 2.142 arquivos de `.venv/`, 12 `.pyc`, `instance/tasks.db` e README da contagem técnica
- **Source files:** 16 arquivos técnicos; 1.158 linhas Python
- **Files under root:** 2.172
- **Report path:** `reports/audit-project-3.md`
- **Phase 1–2 filesystem changes:** este relatório somente

## Project Analysis

| Attribute | Result | Evidence | Confidence |
|---|---|---|---|
| Language/runtime | Python; CPython local 3.12.11; versão suportada não declarada | `.venv/pyvenv.cfg:1-5` | HIGH local / UNKNOWN projeto |
| Build/dependencies | pip, seis versões fixadas; sem lock transitivo | `requirements.txt:1-6`, `README.md:7-10` | HIGH |
| Framework/interfaces | Flask, 3 blueprints, 22 operações HTTP e 1 CLI | `app.py:1-34` e decorators em `routes/` | HIGH |
| Persistence/integrations | SQLite/SQLAlchemy; SMTP implementado mas desconectado | `app.py:11-16`, `models/`, `services/notification_service.py` | HIGH |
| Domain | Tarefas, responsáveis, categorias, autenticação e relatórios | Models e rotas | HIGH |
| Current architecture | Camadas nominais com Active Record, fat route handlers e bootstrap com efeitos | `app.py:9-34`, `routes/*.py` | HIGH |
| Units/entry points | API: `python app.py`; seed: `python seed.py` | `app.py:33-34`, `seed.py:98-99` | HIGH |
| Tests | Ausentes | Nenhum arquivo, framework ou script de teste | HIGH |

O fluxo atual é `HTTP route → validação/regra/query/transação/serialização no próprio handler → SQLAlchemy → JSON`. O seed importa o bootstrap HTTP, que cria o schema durante o carregamento em [app.py:30–31](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/app.py:30).

## Public Contract Baseline

Aliases de payload:

- `TaskDTO`: `id`, `title`, `description`, `status`, `priority`, `user_id`, `category_id`, `created_at`, `updated_at`, `due_date`, `tags`.
- `UserDTO`: `id`, `name`, `email`, `password` (hash), `role`, `active`, `created_at`.
- `CategoryDTO`: `id`, `name`, `description`, `color`, `created_at`.
- Erros explícitos usam `{error: string}`; deleções usam `{message: string}`.
- Não existe autenticação aplicada a nenhuma rota.

| Type | Identity | Handler/location | Input/auth | Expected output/error/effect |
|---|---|---|---|---|
| HTTP | `GET /` | `index`, `app.py:26-28` | sem entrada; sem auth | 200 `{message, version}` |
| HTTP | `GET /health` | `health`, `app.py:22-24` | sem entrada; sem auth | 200 `{status, timestamp}` |
| HTTP | `GET /tasks` | `get_tasks`, `task_routes.py:11-63` | sem auth | 200 `TaskDTO[]` acrescido de `overdue`, `user_name`, `category_name`; 500 |
| HTTP | `GET /tasks/<task_id>` | `get_task`, `task_routes.py:65-83` | inteiro no path; sem auth | 200 `TaskDTO + overdue`; 404 |
| HTTP | `POST /tasks` | `create_task`, `task_routes.py:85-154` | JSON; `title` obrigatório; demais campos opcionais; sem auth | 201 `TaskDTO`; 400/404/500; insere task |
| HTTP | `PUT /tasks/<task_id>` | `update_task`, `task_routes.py:156-223` | JSON parcial; sem auth | 200 `TaskDTO`; 400/404/500; atualiza task |
| HTTP | `DELETE /tasks/<task_id>` | `delete_task`, `task_routes.py:225-238` | inteiro no path; sem auth | 200 `{message}`; 404/500; apaga task |
| HTTP | `GET /tasks/search` | `search_tasks`, `task_routes.py:240-271` | query `q`, `status`, `priority`, `user_id`; sem auth | 200 `TaskDTO[]` |
| HTTP | `GET /tasks/stats` | `task_stats`, `task_routes.py:273-299` | sem auth | 200 `{total,pending,in_progress,done,cancelled,overdue,completion_rate}` |
| HTTP | `GET /users` | `get_users`, `user_routes.py:10-25` | sem auth | 200 array de `{id,name,email,role,active,created_at,task_count}` |
| HTTP | `GET /users/<user_id>` | `get_user`, `user_routes.py:27-40` | inteiro no path; sem auth | 200 `UserDTO + tasks: TaskDTO[]`; 404 |
| HTTP | `POST /users` | `create_user`, `user_routes.py:42-90` | JSON com `name`, `email`, `password`; `role` opcional; sem auth | 201 `UserDTO`; 400/409/500; cria usuário |
| HTTP | `PUT /users/<user_id>` | `update_user`, `user_routes.py:92-132` | JSON parcial; sem auth | 200 `UserDTO`; 400/404/409/500 |
| HTTP | `DELETE /users/<user_id>` | `delete_user`, `user_routes.py:134-151` | inteiro no path; sem auth | 200 `{message}`; 404/500; apaga usuário e suas tasks |
| HTTP | `GET /users/<user_id>/tasks` | `get_user_tasks`, `user_routes.py:153-183` | inteiro no path; sem auth | 200 array de `{id,title,description,status,priority,created_at,due_date,overdue}`; 404 |
| HTTP | `POST /login` | `login`, `user_routes.py:185-211` | JSON `{email,password}`; público | 200 `{message,user:UserDTO,token}`; 400/401/403 |
| HTTP | `GET /reports/summary` | `summary_report`, `report_routes.py:12-101` | sem auth | 200 com `generated_at`, `overview`, status/prioridades, atrasos, atividade e produtividade |
| HTTP | `GET /reports/user/<user_id>` | `user_report`, `report_routes.py:103-155` | inteiro no path; sem auth | 200 `{user,statistics}`; 404 |
| HTTP | `GET /categories` | `get_categories`, `report_routes.py:157-165` | sem auth | 200 `CategoryDTO[] + task_count` |
| HTTP | `POST /categories` | `create_category`, `report_routes.py:167-188` | JSON; `name` obrigatório; sem auth | 201 `CategoryDTO`; 400/500 |
| HTTP | `PUT /categories/<cat_id>` | `update_category`, `report_routes.py:190-209` | JSON parcial; sem auth | 200 `CategoryDTO`; 404/500 |
| HTTP | `DELETE /categories/<cat_id>` | `delete_category`, `report_routes.py:211-223` | inteiro no path; sem auth | 200 `{message}`; 404/500; apaga categoria |
| CLI | `python seed.py` | `seed_data`, `seed.py:8-99` | sem argumentos | apaga todos os dados, cria 3 usuários, 4 categorias e 10 tasks; imprime contagens |

O seed e os endpoints `DELETE` são contratos destrutivos e deverão ser validados somente contra SQLite temporário.

## Summary

| Severity | Count |
|---|---:|
| CRITICAL | 3 |
| HIGH | 4 |
| MEDIUM | 5 |
| LOW | 2 |
| **Total** | **14** |

**Acceptance check:** `>= 5 verified findings: PASS`; `>= 1 CRITICAL or HIGH: PASS`.

Cobertura do catálogo: AP-01 não teve ocorrência confirmada; AP-04 não produziu finding independente porque a causa foi deduplicada em AP-05; AP-06 não foi confirmado — o objeto SQLAlchemy global usa ciclo de vida gerenciado pelo framework. AP-02, AP-03, AP-05 e AP-07–AP-14 têm ocorrências abaixo.

## Deprecated API Check

- **Status:** dois findings confirmados.
- **Versions inspected:** CPython 3.12.11, Flask 3.0.0, Flask-SQLAlchemy 3.1.1 e SQLAlchemy 2.0.51.
- **Sources locais:** `.venv/pyvenv.cfg:1-5`; metadados instalados; decorator `became_legacy_20` em `sqlalchemy/orm/query.py:1042-1046`.
- **Sources primárias:** a interface `Query` é legada e `Query.get()` foi substituído por `Session.get()` segundo [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/orm/queryguide/query.html) e [Flask-SQLAlchemy 3.1](https://flask-sqlalchemy.palletsprojects.com/en/stable/legacy-query/). `datetime.utcnow()` está deprecated desde Python 3.12, com `datetime.now(UTC)` como substituto, segundo a [documentação oficial do Python 3.12](https://docs.python.org/3.12/library/datetime.html?highlight=utcnow).
- **Candidates not counted:** nenhum.

## Findings

### F-001 — [CRITICAL] Ausência de autenticação e autorização nas fronteiras de dados

- **Catalog rule:** AP-03 — autenticação insegura.
- **Location:** [app.py:15–20](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/app.py:15), [task_routes.py:225–238](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/task_routes.py:225), [user_routes.py:134–151](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/user_routes.py:134), [report_routes.py:211–223](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/report_routes.py:211).
- **Evidence:** blueprints são registrados sem middleware de autenticação; inclusive operações de criação, alteração, exclusão e relatórios não verificam identidade ou papel.
- **Impact:** qualquer cliente pode ler, modificar ou apagar dados.
- **Recommendation:** autenticação real e política explícita de autorização por operação.
- **Transformation:** T09.
- **Validation:** matriz de testes anônimos/autenticados por rota e papel, incluindo 401/403.
- **Confidence:** HIGH.

### F-002 — [CRITICAL] Credenciais e token usam primitivas inseguras

- **Catalog rule:** AP-03 — autenticação ou criptografia insegura.
- **Location:** [models/user.py:27–32](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/models/user.py:27), [user_routes.py:185–211](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/user_routes.py:185), [seed.py:16–35](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/seed.py:16).
- **Evidence:** senhas usam MD5 sem salt; login devolve token determinístico/falso; seed cria contas, inclusive privilegiada, com senhas literais curtas.
- **Impact:** hashes são quebráveis, tokens podem ser forjados e contas iniciais são previsíveis.
- **Recommendation:** hasher adaptativo, tokens assinados/verificados e credenciais de seed somente para ambiente isolado.
- **Transformation:** T09.
- **Validation:** testes de hash com salt, rejeição de token adulterado/expirado e ausência de credenciais default em configuração normal.
- **Confidence:** HIGH.

### F-003 — [CRITICAL] Hash de senha é exposto nas respostas HTTP

- **Catalog rule:** AP-02 — dado sensível exposto.
- **Location:** [models/user.py:16–24](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/models/user.py:16), [user_routes.py:27–40](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/user_routes.py:27), [user_routes.py:74–86](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/user_routes.py:74), [user_routes.py:207–211](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/user_routes.py:207).
- **Evidence:** `User.to_dict()` inclui o campo de senha e é usado em consulta individual, criação, atualização e login.
- **Impact:** clientes anônimos podem coletar hashes e realizar cracking offline.
- **Recommendation:** DTO público sem qualquer campo de credencial.
- **Transformation:** T09/T08.
- **Validation:** contract tests garantindo que `password` nunca aparece em respostas ou logs.
- **Confidence:** HIGH.

### F-004 — [HIGH] Segredos operacionais estão embutidos no código

- **Catalog rule:** AP-02 — segredo exposto.
- **Location:** [app.py:11–13](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/app.py:11), [notification_service.py:7–10](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/services/notification_service.py:7).
- **Evidence:** chave da aplicação e credenciais SMTP são literais no fonte; valores omitidos deste relatório.
- **Impact:** distribuição do código distribui as credenciais e impede rotação segura.
- **Recommendation:** configuração externa com validação obrigatória e rotação das credenciais reais, se utilizadas.
- **Transformation:** T01.
- **Validation:** busca por segredos, boot com ambiente temporário e falha clara quando configuração obrigatória faltar.
- **Confidence:** HIGH; SMTP está desconectado, por isso não foi elevado a CRITICAL.

### F-005 — [HIGH] Bootstrap documentado expõe debugger e configuração insegura

- **Catalog rule:** AP-13 — configuração dispersa.
- **Location:** [app.py:11–15](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/app.py:11), [app.py:30–34](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/app.py:30), [README.md:7–13](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/README.md:7).
- **Evidence:** URI fixa, CORS sem política explícita, criação de schema no import e servidor de desenvolvimento com debug ligado em todas as interfaces.
- **Impact:** o único boot documentado expõe uma superfície que o próprio Flask classifica como grande risco de segurança; o debugger permite execução de Python pelo navegador. [Documentação oficial do Flask](https://flask.palletsprojects.com/en/stable/debugging/).
- **Recommendation:** application factory, perfis de configuração, debug desligado por padrão e servidor WSGI para uso não local.
- **Transformation:** T01/T03.
- **Validation:** import sem side effects, configuração de produção com debug falso e teste de allowlist CORS.
- **Confidence:** HIGH.

### F-006 — [HIGH] Route handlers acumulam adapter, negócio, persistência e apresentação

- **Catalog rule:** AP-05 — fat adapter/controller.
- **Location:** [task_routes.py:11–299](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/task_routes.py:11), [user_routes.py:10–211](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/user_routes.py:10), [report_routes.py:12–223](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/report_routes.py:12).
- **Evidence:** handlers fazem parsing, validação, cálculos de domínio, queries, transações, serialização e logging.
- **Impact:** regras ficam acopladas a Flask e SQLAlchemy, dificultando testes e ampliando regressões.
- **Recommendation:** routes como adapters finos; controllers/use cases, validators, presenters e acesso a dados separados.
- **Transformation:** T03/T04/T08.
- **Validation:** testes unitários dos casos de uso sem contexto Flask e contract tests das routes.
- **Confidence:** HIGH.

### F-007 — [HIGH] Seed destrutivo não é atômico

- **Catalog rule:** AP-07 — operação não atômica.
- **Location:** [seed.py:8–14](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/seed.py:8), [seed.py:16–63](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/seed.py:16), [seed.py:78–92](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/seed.py:78).
- **Evidence:** a exclusão total é commitada antes da criação de usuários, categorias e tasks, com novos commits intermediários.
- **Impact:** uma falha posterior deixa o banco vazio ou parcialmente populado.
- **Recommendation:** uma fronteira transacional com rollback integral.
- **Transformation:** T06.
- **Validation:** injetar falha após cada etapa e confirmar restauração integral do estado anterior.
- **Confidence:** HIGH.

### F-008 — [MEDIUM] Endpoints de coleção executam N+1 queries

- **Catalog rule:** AP-08 — acesso repetitivo.
- **Location:** [task_routes.py:13–57](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/task_routes.py:13), [user_routes.py:10–23](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/user_routes.py:10), [report_routes.py:53–68](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/report_routes.py:53), [report_routes.py:157–165](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/report_routes.py:157).
- **Evidence:** `GET /tasks` executa uma consulta inicial e até duas buscas por task (`1 + 2N`); usuários, produtividade e categorias também consultam relações dentro de loops.
- **Impact:** latência e carga de banco crescem linearmente com o volume.
- **Recommendation:** eager loading, agregação e consultas em lote.
- **Transformation:** T07.
- **Validation:** contador de SQL com limite constante por endpoint.
- **Confidence:** HIGH.

### F-009 — [MEDIUM] Validação e serialização duplicadas produzem respostas inconsistentes

- **Catalog rule:** AP-09 — regra/validação/serialização duplicada.
- **Location:** [task_routes.py:85–145](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/task_routes.py:85), [task_routes.py:156–213](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/task_routes.py:156), [helpers.py:57–108](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/utils/helpers.py:57), [user_routes.py:42–78](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/user_routes.py:42), [user_routes.py:92–125](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/user_routes.py:92).
- **Evidence:** create/update repetem regras e ignoram helper existente; DTOs de tasks variam por endpoint. Tipos inválidos em `priority` ou nos filtros passam por comparações/conversões sem tratamento.
- **Impact:** mudanças precisam ser replicadas e entradas malformadas podem resultar em 500 em vez de 400.
- **Recommendation:** schemas/validators e presenters únicos por recurso.
- **Transformation:** T08.
- **Validation:** testes parametrizados de entradas válidas/ inválidas e snapshots dos DTOs.
- **Confidence:** HIGH.

### F-010 — [MEDIUM] Erros são silenciados e traduzidos de forma dispersa

- **Catalog rule:** AP-10 — tratamento de erro inadequado.
- **Location:** [task_routes.py:61–63](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/task_routes.py:61), [task_routes.py:146–154](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/task_routes.py:146), [user_routes.py:80–90](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/user_routes.py:80), [report_routes.py:182–223](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/report_routes.py:182), [helpers.py:43–50](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/utils/helpers.py:43).
- **Evidence:** vários `except:` capturam tudo, descartam causa ou usam `print`; não existe error mapper central.
- **Impact:** falhas de programação parecem erros operacionais genéricos e incidentes ficam difíceis de diagnosticar.
- **Recommendation:** exceções tipadas, rollback centralizado, envelopes estáveis e logging estruturado.
- **Transformation:** T10.
- **Validation:** testes de falhas conhecidas e captura estruturada sem dados sensíveis.
- **Confidence:** HIGH.

### F-011 — [MEDIUM] Interface legada `Model.query`/`Query.get()` em SQLAlchemy 2

- **Catalog rule:** AP-11 — API deprecated/legada.
- **Location:** `task_routes.py:42,51,67,117,122,158,188,195,227`; `user_routes.py:29,94,136,155`; `report_routes.py:105,192,213`.
- **Evidence:** 16 chamadas `Query.get()`; ambiente efetivo usa Flask-SQLAlchemy 3.1.1 e SQLAlchemy 2.0.51.
- **Impact:** warnings e dívida de compatibilidade em upgrades.
- **Recommendation:** `db.session.get(Model, id)` para PK e `select()`/`session.execute()` para consultas.
- **Transformation:** T11.
- **Validation:** varredura sem `Model.query` e suíte de contratos de persistência.
- **Confidence:** HIGH.
- **Deprecated API proof:** [SQLAlchemy Legacy Query API](https://docs.sqlalchemy.org/en/20/orm/queryguide/query.html) e [Flask-SQLAlchemy Legacy Query Interface](https://flask-sqlalchemy.palletsprojects.com/en/stable/legacy-query/).

### F-012 — [MEDIUM] `datetime.utcnow()` está deprecated no runtime efetivo

- **Catalog rule:** AP-11 — API deprecated.
- **Location:** `models/category.py:11`; `models/task.py:15-16,52`; `models/user.py:14`; `task_routes.py:31,72,215,285`; `user_routes.py:172`; `report_routes.py:35,42,45,71,133`; `seed.py:66-75`; `notification_service.py:35`; `helpers.py:38`.
- **Evidence:** 23 ocorrências; CPython efetivo 3.12.11.
- **Impact:** futura incompatibilidade e mistura de timestamps UTC sem timezone.
- **Recommendation:** relógio injetável baseado em `datetime.now(UTC)` e política consistente de persistência/serialização.
- **Transformation:** T11/custom clock.
- **Validation:** testes timezone-aware, comparações de vencimento e preservação da forma textual aprovada.
- **Confidence:** HIGH.
- **Deprecated API proof:** [Python 3.12 datetime](https://docs.python.org/3.12/library/datetime.html?highlight=utcnow); substituto oficial `datetime.now(UTC)`.

### F-013 — [LOW] Cliente SMTP não possui timeout nem fechamento garantido

- **Catalog rule:** AP-12 — I/O externo bloqueante/frágil.
- **Location:** [notification_service.py:12–25](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/services/notification_service.py:12).
- **Evidence:** conexão SMTP é aberta sem timeout e `quit()` não está protegido por `finally`/context manager.
- **Impact:** se o serviço for conectado ao fluxo, chamadas podem bloquear e conexões podem ficar abertas.
- **Recommendation:** adapter injetável, timeout, context manager e execução assíncrona quando necessária.
- **Transformation:** T04/T10.
- **Validation:** SMTP falso simulando timeout, falha de autenticação e fechamento.
- **Confidence:** HIGH no código; severidade reduzida porque o serviço está desconectado.

### F-014 — [LOW] Código e dependências sem consumidores obscurecem a arquitetura

- **Catalog rule:** AP-14 — higiene/legibilidade.
- **Location:** [requirements.txt:4–6](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/requirements.txt:4), [task_routes.py:7](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/task_routes.py:7), [report_routes.py:7–8](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/routes/report_routes.py:7), [helpers.py:1–7](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/utils/helpers.py:1), [notification_service.py:1–48](/home/matheussouza/learn/mba-ia-refactor-projects-skill/task-manager-api/services/notification_service.py:1).
- **Evidence:** imports não usados, helpers sem consumidores, Marshmallow/Requests sem uso observado e serviço de notificação não ligado ao bootstrap.
- **Impact:** dependências e responsabilidades aparentes divergem do comportamento real.
- **Recommendation:** remover o que for realmente morto ou integrar explicitamente sob interfaces testáveis.
- **Transformation:** T08/T10.
- **Validation:** análise estática e busca de referências após a mudança.
- **Confidence:** HIGH.

## Proposed Refactoring Plan

| Order | Finding IDs | Transformation | Files/roles affected | Risk | Validation |
|---:|---|---|---|---|---|
| 1 | F-004, F-005 | T01/T03: application factory e configuração externa | `app.py`, novo `config.py`, `database.py`, notification adapter | boot e localização do SQLite | import sem escrita; boot em diretório temporário |
| 2 | F-002, F-003 | T09/T08: hashing adaptativo, token real e DTO público | `models/user.py`, auth service/controller, user presenter/routes | hashes existentes e remoção do campo `password` | testes de login, hash e payload |
| 3 | F-001 | T09: middleware e autorização | auth adapter, controllers e routes | mudança pública para 401/403; matriz de papéis não definida | matriz contratual por rota/papel |
| 4 | F-007 | T06: seed como caso de uso atômico | `seed.py`, seed controller/service | operação destrutiva | SQLite temporário e falhas injetadas |
| 5 | F-006, F-009 | T03/T04/T08: controllers, validators e presenters | `routes/`, novos `controllers/`, `schemas/` | regressão de payload/status | contract tests das 22 rotas |
| 6 | F-008, F-011 | T07/T11: repositories, eager loading e SQLAlchemy 2 | models, novos repositories/controllers | ordem/resultados das consultas | contagem de SQL e testes de respostas |
| 7 | F-010 | T10: error mapper e logging central | novo `errors.py`, bootstrap, adapters | envelope/status divergente | testes de 400/404/409/500 |
| 8 | F-012 | T11: relógio UTC central | models, reports, task/user services, seed | timestamps antigos são naive | testes de timezone e serialização |
| 9 | F-013 | T04/T10: adapter SMTP resiliente | `services/notification_service.py` | chamada externa involuntária | test double; nenhuma rede real |
| 10 | F-014 | T08: higiene e dependências | imports, helpers, `requirements.txt`, README | remover integração implícita | análise estática e smoke/load |
| 11 | Todos | suíte de regressão e documentação | novo `tests/`, README, relatório | ausência de baseline automatizado | lint/sintaxe, testes, boot, 23 contratos e nova auditoria |

A remoção de `password` das respostas é uma alteração pública intencional de segurança. A exigência de autenticação também alterará respostas para 401/403; antes de aplicá-la será necessário definir a matriz de permissões para `user`, `manager` e `admin`, que não pode ser inferida com segurança do código atual.

## Expected MVC Target

```text
task-manager-api/
├── app.py                         # composition root/bootstrap
├── config.py                      # configuração por ambiente
├── database.py                    # extensão e infraestrutura SQLAlchemy
├── models/                        # entidades, estado e invariantes
├── repositories/                  # consultas e persistência
├── controllers/                   # casos de uso e orquestração
│   ├── task_controller.py
│   ├── user_controller.py
│   ├── category_controller.py
│   ├── report_controller.py
│   └── seed_controller.py
├── routes/                        # Views/adapters HTTP finos
├── schemas/                       # validação e presenters/DTOs
├── services/                      # auth, clock e notification ports/adapters
├── errors.py                      # erros e tradução HTTP central
├── seed.py                        # adapter CLI
└── tests/                         # unidade, integração e contratos
```

Direção pretendida: bootstrap compõe dependências; routes traduzem HTTP e chamam controllers; controllers orquestram domínio e repositories; models mantêm estado e invariantes; presenters definem os payloads; infraestrutura não invade adapters ou regras.

Para o seed, a View é o adapter CLI, o Controller é o caso de uso transacional e os Models/repositories representam dados e persistência.

## Risks and Preconditions

- Não há testes existentes; o baseline inicial dependerá de contratos estáticos e smoke tests isolados.
- `instance/tasks.db` contém dados reais do workspace e não poderá ser usado pelo seed ou pelos testes.
- Importar `app.py` cria schema; o baseline deverá ser executado numa cópia/diretório temporário.
- Senhas existentes usam MD5; a transição exige estratégia compatível de rehash ou migração.
- Remover `password` dos payloads e adicionar 401/403 são mudanças contratuais de segurança.
- A matriz de autorização por papel precisa de decisão humana antes de proteger as rotas.
- Migrar timestamps naive para UTC aware pode alterar serialização e comparações.
- SMTP deverá ser substituído por test double durante toda a validação.
- Dependências transitivas não estão travadas por lockfile.
- O relatório foi persistido antes do checkpoint; alterações de código ficaram condicionadas à autorização posterior.

## Human Gate

Phase 2 foi concluída com a codebase em modo somente-leitura e este relatório foi salvo em `reports/audit-project-3.md` antes do checkpoint. A Fase 3 foi autorizada e executada em um turno posterior.

**Checkpoint apresentado:** `Phase 2 complete. Autoriza executar a Fase 3 e modificar os arquivos conforme o plano apresentado? [y/n]`

**Checkpoint status:** `APPROVED`

## Phase 3 Results

**Status:** `COMPLETE`

### Changes

- **Report saved at:** `reports/audit-project-3.md`
- **Changed files:** `.env.example`, `README.md`, `app.py`, `config.py`, `controllers/**`, `errors.py`, `models/**`, `repositories/**`, `routes/**`, `schemas/**`, `seed.py`, `services/**`, `tests/**` e `requirements.txt`; helpers legados removidos.
- **New architecture:** routes/adapters finos, controllers, repositories, schemas, models, services, error mapper central e application factory; seed separado como adapter CLI.
- **Resolved findings:** F-001 a F-014.
- **Residual findings/risks:** compatibilidade MD5 existe apenas para rehash imediato de credenciais legadas; rotação de segredos históricos é uma ação operacional externa.

### Validation Evidence

| Check | Command/method | Result | Evidence |
|---|---|---|---|
| Restore/build/load | `.venv/bin/python -m pip check` e load isolado | PASS | dependências íntegras; import sem criação de schema |
| Static analysis/types/lint | compilação em memória de 39 fontes | PASS | sintaxe válida; não há linter dedicado instalado |
| Automated tests | `.venv/bin/python -m unittest discover -s tests -v` | PASS | 16/16 testes |
| Unit boot/readiness | servidor TCP temporário | PASS | readiness HTTP e encerramento limpo |
| Public contracts | suíte de contratos HTTP | PASS | 22/22 operações preservam status/shapes quando autorizadas; matriz 401/403 coberta |
| Seed CLI | seed em SQLite temporário | PASS | exit 0; 3 usuários, 4 categorias e 10 tasks |
| Regression audit | varredura dirigida F-001–F-014 | PASS | 19 operações protegidas, 3 públicas; deprecated APIs removidas |
| Scope/diff | `git diff --check -- task-manager-api` | PASS | `instance/tasks.db` preservado e nenhum resíduo temporário |

### Contract Comparison

| Type | Identity | Before | After | Result |
|---|---|---|---|---|
| HTTP | 22 operações inventariadas | sem autenticação; shapes originais | métodos/paths/shapes preservados quando autorizados; 19 operações com matriz de papéis | PASS — segurança aprovada |
| CLI | `python seed.py` | seed destrutivo não atômico | mesmo entry point com transação e rollback | PASS |

### Final Status

`COMPLETE`
