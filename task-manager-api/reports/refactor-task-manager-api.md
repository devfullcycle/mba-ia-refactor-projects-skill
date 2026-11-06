# Refactor Report — task-manager-api

> Gerado pela skill `refactor-arch` (Fase 3 — Refatoração).
> Data: 2026-11-05 | Raiz: `/home/eric-ogata/codes/full_cycle/mba_engenharia_ia/desafios/desafio3/mba-ia-refactor-projects-skill/task-manager-api`
> Baseado em: `reports/analysis-task-manager-api.md` e `reports/audit-task-manager-api.md`

## 1. Resumo

| Métrica | Antes | Depois |
|---|---|---|
| Arquivos `.py` | 15 | 41 |
| Localizações com query no controller/rota | 33 | 0 |
| Segredos literais | 4 | 0 (exceto chave de teste) |
| Tratamento de erro | 11 `except` genéricos | 3 handlers centrais |
| Cobertura de testes | 0 | 8 testes de integração |
| Migrations | ausentes | Alembic (revisão inicial `81c7c4d76ee3`) |
| Endpoints de negócio validados | — | 22/22 (100%) |
| CRITICAL/HIGH fechados | 0/6 | **6/6** |
| Auth de escrita | opt-in (`AUTH_REQUIRED=false`) | **default deny/fail-closed** |
| Gestão de usuários | sem autorização | **`admin` obrigatório** |

**Arquitetura:** Monolítico em camadas parcial → **MVC + Services + Repositories**, com Config, Validators, Middleware, Migrations e autorização por papel.

### Estrutura antes

```
app.py              # config hardcoded (SECRET_KEY) + rotas / e /health + create_all
database.py         # instância SQLAlchemy
models/             # task, user (MD5 + password no to_dict), category
routes/             # rota + validação + regra de negócio + ORM + serialização
services/           # notification_service.py (credenciais SMTP, nunca importado)
utils/helpers.py    # validação duplicada, parcialmente órfã
```

Sem camada de controllers/repositories, sem validators centralizados, sem migrations,
sem testes e com autenticação apenas nominal (`fake-jwt-token-<id>`, não verificada).

### Estrutura depois

```
app.py                  # composition root (create_app)
errors.py               # exceções de domínio
config/settings.py      # config via env (.env.example); AUTH_REQUIRED=True
models/                 # entidades + invariantes (sem segredos no to_dict)
repositories/           # task, user, category — único ponto de ORM
services/               # task, user, category, report, auth — sem HTTP
controllers/            # task, user, category, report — orquestração pura
routes/                 # task, user, category, report — só add_url_rule
validators/schemas.py   # marshmallow por recurso
middleware/             # error_handler central + auth/autorização JWT
migrations/             # Alembic/Flask-Migrate
tests/test_api.py       # integração + gate de segurança 401/403/autorizado
```

Fluxo de dependência: `routes → controllers → services → repositories → models`.

## 2. Anti-patterns corrigidos

### CRITICAL

| Achado | Resolução |
|---|---|
| **SEC-02** `SECRET_KEY` em `app.py:13` | `config/settings.py` lê `SECRET_KEY` do ambiente; sem valor, gera chave aleatória em boot. `.env.example` documenta a variável. |
| **SEC-02** credenciais SMTP em `notification_service.py` | Módulo removido (código morto, nunca importado). |
| **SEC-03** MD5 + hash exposto | `werkzeug.security.generate_password_hash`/`check_password_hash`; `User.to_dict` não inclui `password`; login aceita MD5 legado e **re-hasheia no primeiro login**; seed usa hashes com salt. |

### HIGH

| Achado | Resolução |
|---|---|
| **SEC-04** rotas de escrita sem auth + token falso | JWT real assinado; guard central **fail-closed** em `middleware/auth.py`; `AUTH_REQUIRED` default `True` e middleware não desativa a proteção; `@require_role('admin')` em toda a gestão de usuários; `/login` público; identidade/papel/posse derivados do token. |
| **ARCH-01** lógica de negócio nas rotas | Extraída para `TaskService`, `UserService`, `CategoryService`, `ReportService`; controllers apenas orquestram. |
| **ARCH-02** ORM/`db.session` nas rotas | Centralizado em `repositories/` (um por agregado); rotas/controllers não importam `db` nem models. |

### MEDIUM/LOW

| Achado | Resolução |
|---|---|
| **PERF-01** N+1 | `joinedload` em `TaskRepository.get_all`; `group_by`/`count` para contagens e produtividade. |
| **QUAL-02** validação ausente | `validators/schemas.py` (marshmallow) por recurso; payload inválido → 400. |
| **QUAL-03** `except` genérico | `middleware/error_handler.py` com handlers para `DomainError`, `HTTPException` e `Exception` (com log e rollback). |
| **QUAL-04** estado global mutável | `NotificationService` removido; nenhum estado de módulo mutável restante. |
| **ARCH-03** Model com responsabilidades duplas | Models mantêm entidade/invariantes; hashing no Model com API segura, validação em schemas, persistência em repositórios. |
| **QUAL-05** dependências/código mortos | `requests` removido; `marshmallow` e `python-dotenv` passaram a ser usados; `NotificationService` excluído. |
| **QUAL-06** sem migrations | Flask-Migrate/Alembic inicializado; revisão `81c7c4d76ee3` aplicada; `db.create_all()` removido do import do app. |
| **QUAL-07** config hardcoded | Host, porta, debug, URI e segredos externalizados; `debug` default `False`, bind default `127.0.0.1`. |
| **QUAL-08** sem testes | `tests/test_api.py` — 8 testes de integração, incluindo 401/403/caminho autorizado. |
| **DEP-01** APIs deprecated | `datetime.utcnow()` → `utils.helpers.utcnow()`; `Query.get()` → `db.session.get()`. |

## 3. Matriz de Fechamento CRITICAL/HIGH

| ID | Severidade | Impacto descrito na auditoria | Correção aplicada | Evidência estática (arquivo:linha) | Evidência dinâmica (teste/comando/HTTP) | Status |
|---|---|---|---|---|---|---|
| SEC-02 | CRITICAL | `SECRET_KEY` hardcoded permitia forjar tokens | Config via ambiente; fallback aleatório em boot | `config/settings.py:25-29`; `.env.example:3-5` | `grep` sem `super-secret-key-123`; boot com config padrão OK | `RESOLVIDO` |
| SEC-02 | CRITICAL | Credenciais SMTP em texto puro no repositório | Módulo `notification_service.py` removido | `services/` sem o módulo; `grep` sem `smtp.gmail.com`/`senha123` | `grep` de segredos sem ocorrências no código de produção | `RESOLVIDO` |
| SEC-03 | CRITICAL | MD5 sem salt e hash devolvido pela API | `generate_password_hash`/`check_password_hash`; `to_dict` sem `password`; re-hash de legado | `models/user.py:20-41`; `services/user_service.py:46-54,78-92` | Senhas do banco iniciam em `scrypt:`; login 200; respostas sem `password`; teste de re-hash passa | `RESOLVIDO` |
| SEC-04 | HIGH | Rotas de escrita abertas, token falso e sem autorização | JWT real + guard central fail-closed + `@require_role('admin')` + posse derivada do token | `middleware/auth.py:22-96`; `controllers/user_controller.py:10-34`; `services/task_service.py:56-127`; `config/settings.py:31-34` | Sem token: `POST /tasks` 401, `POST /users` 401; não-admin: `POST/PUT/DELETE /users` 403; admin: 201/200; `/login` 200 | `RESOLVIDO` |
| ARCH-01 | HIGH | Regra de negócio nas rotas | Casos de uso extraídos para services | `services/task_service.py`, `user_service.py`, `category_service.py`, `report_service.py`; controllers com 1-8 linhas | Testes de integração exercitam as regras via HTTP | `RESOLVIDO` |
| ARCH-02 | HIGH | ORM/`db.session` na camada de transporte | Repositórios por agregado; rotas/controllers sem ORM | `repositories/task_repository.py`, `user_repository.py`, `category_repository.py` | `grep` de `db`/`.query` em `controllers/` e `routes/` sem resultados | `RESOLVIDO` |

**Resumo:** CRITICAL 3/3 `RESOLVIDO`; HIGH 3/3 `RESOLVIDO`; `BLOQUEADO` = 0.

## 4. Resultado dos testes de validação

### Boot com configuração padrão

```
$ DATABASE_URL=sqlite:////tmp/opencode/tm-etapa5.db .venv/bin/python seed.py
Seed concluído com sucesso! (3 usuários, 4 categorias, 10 tasks)
$ DATABASE_URL=sqlite:////tmp/opencode/tm-etapa5.db PORT=5055 .venv/bin/python app.py
 * Running on http://127.0.0.1:5055
```

`AUTH_REQUIRED` não foi definido no ambiente: `Config.AUTH_REQUIRED = True`.

### Smoke test HTTP (22/22)

| Método | Rota | Status | Contrato |
|---|---|---|---|
| GET | `/` | 200 | `{message, version}` |
| GET | `/health` | 200 | `{status, timestamp}` |
| GET | `/tasks` | 200 | lista com `user_name`, `category_name`, `overdue`, `tags` |
| GET | `/tasks/<id>` | 200 | objeto + `overdue` |
| POST | `/tasks` | 201 | objeto criado com dono derivado do JWT |
| PUT | `/tasks/<id>` | 200 | objeto atualizado pelo dono/admin |
| DELETE | `/tasks/<id>` | 200 | `{message}` |
| GET | `/tasks/search` | 200 | lista filtrada |
| GET | `/tasks/stats` | 200 | `{total,pending,in_progress,done,cancelled,overdue,completion_rate}` |
| GET | `/users` | 200 | listagem admin com `task_count`, **sem** `password` |
| GET | `/users/<id>` | 200 | usuário + `tasks` |
| POST | `/users` | 201 | usuário criado, **sem** `password` |
| PUT | `/users/<id>` | 200 | usuário atualizado |
| DELETE | `/users/<id>` | 200 | `{message}` + tasks do usuário removidas |
| GET | `/users/<id>/tasks` | 200 | lista com `overdue` |
| POST | `/login` | 200 | `{message, user, token}` com **JWT real** (3 partes) |
| GET | `/reports/summary` | 200 | overview, status, prioridade, overdue, atividade, produtividade |
| GET | `/reports/user/<id>` | 200 | user + statistics |
| GET | `/categories` | 200 | lista com `task_count` |
| POST | `/categories` | 201 | categoria criada |
| PUT | `/categories/<id>` | 200 | categoria atualizada |
| DELETE | `/categories/<id>` | 200 | `{message}` |

**22/22 rotas de negócio validadas (100%).**

### Casos de erro e segurança

| Cenário | Resultado |
|---|---|
| `POST /tasks` sem token | 401 |
| `POST /tasks` com JWT de usuário comum | 201 |
| `POST /tasks` com `user_id` de terceiro (não-admin) | 403 |
| `POST /users` sem token | 401 |
| `POST /users` com JWT não-admin | 403 |
| `POST /users` com JWT `admin` | 201 |
| `PUT /users/<id>` não-admin / admin | 403 / 200 |
| `DELETE /users/<id>` não-admin / admin | 403 / 200 |
| `GET /users` sem token / não-admin / admin | 401 / 403 / 200 |
| `POST /login` | 200 (público) |
| `POST /tasks` com `{}` | 400 |
| `POST /tasks` com `priority: 9` | 400 |
| `POST /tasks` com `due_date` inválida | 400 |
| `POST /users` com e-mail inválido | 400 |
| `PUT /categories/<id>` com body `null` | 400 |
| `POST /tasks` sem JSON | 400 |
| `GET /tasks/9999` | 404 |

### Testes automatizados

```
$ .venv/bin/python -m pytest -q
........                                                                 [100%]
8 passed
```

Cobrem CRUD de usuários/tasks/categorias, login JWT, relatórios, validação (400), 404, a matriz 401/403/200-201 com auth default, posse de tarefas e re-hash de senha MD5 legada.

## 5. Checklist de validação (mvc-guidelines §6)

- [x] Aplicação sobe sem erros (`python app.py`)
- [x] Todas as 22 rotas de negócio respondem no mesmo path/verbo
- [x] Rotas de escrita rejeitam payload malformado com 400
- [x] Nenhuma query interpolada (ORM com parâmetros vinculados; sem SQL cru)
- [x] Nenhum segredo literal no código (exceto `TestConfig.SECRET_KEY`, restrito a testes)
- [x] Responses não expõem campos sensíveis (`password` removido)
- [x] Rotas de escrita rejeitam anônimo por padrão (`401`)
- [x] Rotas administrativas rejeitam não-admin (`403`)
- [x] Identidade, papel e posse derivados do token, nunca do body
- [x] Nenhuma senha em texto puro em seed/banco — hash com salt em todo armazenamento
- [x] Testes de segurança por finding executados (SEC-02, SEC-03, SEC-04, SEC-06)
- [x] Sem try/except genérico engolindo erro sem log
- [x] Arquivos antigos removidos
- [x] `git status` sem sobras de refatoração (caches/DB cobertos por `.gitignore`)

## 6. Pendências (apenas MEDIUM/LOW)

- Testes unitários de services/repositories e testes de concorrência continuam ausentes (QUAL-08 parcial em profundidade, sem impacto de segurança).
- `/` e `/health` permanecem registrados inline em `app.py`; são rotas de infraestrutura.
- `services/auth_service.py` usa `current_app` apenas para `SECRET_KEY`/expiração; não usa `request`/`response`.
- CI/CD, containerização e logging estruturado seguem fora de escopo.

**Nenhuma pendência CRITICAL/HIGH.**

## 7. Limitações e trabalho futuro

- **Mudanças de contrato intencionais:** gestão de usuários exige `admin`; rotas de escrita exigem JWT por padrão; não-admin só opera nas próprias tarefas; `password` não é retornado; `/login` emite JWT real; SQLite na raiz do projeto. Documentadas no `README.md`.
- **Migrations:** a revisão inicial cobre o schema atual. Bancos criados com o `create_all()` original precisam de baseline (`flask db stamp head`).
- **Evolução:** avaliar logging estruturado, métricas e testes unitários adicionais.

## Bloco de resumo

```
================================
PHASE 3: REFACTORING
================================
Project:       task-manager-api
Files before:  15 files
Files after:   41 files
Architecture:  Monolítico parcial → MVC + Services + Repositories
Critical resolved: 3/3
High resolved:     3/3
Anti-patterns corrected: 16 (3 CRITICAL, 3 HIGH, 5 MEDIUM, 5 LOW)
Endpoints validated: 22/22
Status:        Complete
================================
```
