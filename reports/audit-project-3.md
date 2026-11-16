================================
FASE 1: ANÁLISE DO PROJETO
================================
Linguagem:      Python 3
Framework:      Flask (3.0.0 pinado; 3.1.1 instalado) + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.0.x)
Dependências:   flask-cors 4.0.0, marshmallow 3.20.1 (não usado), requests 2.31.0 (não usado), python-dotenv 1.0.0 (não usado)
Domínio:        Task, User, Category (tasks pertencem a um usuário e a uma categoria)
Arquitetura:    Parcial — já existem models/, routes/, services/, utils/, mas as rotas concentram queries, regras de negócio e serialização; sem controllers/config
Arquivos:       15 arquivos analisados
Banco de dados: SQLite (tasks.db) via ORM (Flask-SQLAlchemy)
Endpoints:      21 (ver lista abaixo)
Como executar:  pip install -r requirements.txt && python seed.py && python app.py  (http://localhost:5000)
================================

Endpoints (contrato a preservar na Fase 3):
- GET `/`, GET `/health`                                   (app.py:22-28)
- GET `/tasks`, POST `/tasks`                              (task_routes.py:11, 85)
- GET/PUT/DELETE `/tasks/<id>`                             (task_routes.py:65, 156, 225)
- GET `/tasks/search`, GET `/tasks/stats`                  (task_routes.py:240, 273)
- GET/POST `/users`, GET/PUT/DELETE `/users/<id>`         (user_routes.py:10, 42, 27, 92, 134)
- GET `/users/<id>/tasks`, POST `/login`                   (user_routes.py:153, 185)
- GET `/reports/summary`, GET `/reports/user/<id>`         (report_routes.py:12, 103)
- GET/POST `/categories`, PUT/DELETE `/categories/<id>`   (report_routes.py:157, 167, 190, 211)

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask (3.0.0) + Flask-SQLAlchemy (3.1.1) / SQLAlchemy 2.0
Files:   15 analisados | ~1158 linhas de código
Database: SQLite (tasks.db) / ORM Flask-SQLAlchemy (queries via `Model.query`)

## Summary
| Severidade | Qtde |
|---|---|
| CRITICAL | 2 |
| HIGH     | 4 |
| MEDIUM   | 4 |
| LOW      | 2 |
| **Total** | **12** |

## Current Architecture
Nível **parcial**. Há pastas por responsabilidade (`models/`, `routes/`, `services/`, `utils/`), mas as rotas funcionam como controllers gordos: executam queries ORM, calculam regras (atraso, estatísticas, validações), serializam manualmente e tratam erros. `report_routes.py` mistura relatórios e CRUD de categorias. Não existem camadas de controllers, config, serializers nem tratador de erros central; `services/` e `utils/helpers.py` estão praticamente mortos (nenhuma rota os usa). Configuração e segredos estão hardcoded em `app.py` e no serviço de notificação.

## Findings

### [CRITICAL] AP-02 — Credenciais e segredos hardcoded
- **File**: `app.py:13`, `app.py:34`, `services/notification_service.py:7-10`
- **Description**: `SECRET_KEY = 'super-secret-key-123'` literal no código; `app.run(debug=True, host='0.0.0.0')` fixo (debugger Werkzeug interativo exposto na rede); credenciais SMTP (`taskmanager@gmail.com` / `senha123`) literais em `NotificationService.__init__`. A URI do banco também é fixa (`app.py:11`). `python-dotenv` está nas dependências mas nunca é usado.
- **Impact**: vazamento de acesso pelo repositório; `debug=True` em `0.0.0.0` permite execução remota de código via console do debugger.
- **Recommendation**: criar `config/settings.py` que lê `SECRET_KEY`, `DATABASE_URL`, `DEBUG`, `HOST`, `PORT` e credenciais SMTP de variáveis de ambiente (com `python-dotenv` e `.env.example`), com `DEBUG` desligado por padrão (Playbook P2).

### [CRITICAL] AP-03 — Exposição de dados sensíveis / autenticação fraca
- **File**: `models/user.py:21`, `models/user.py:29`, `models/user.py:32`, `routes/user_routes.py:33`, `routes/user_routes.py:85-86`, `routes/user_routes.py:129`, `routes/user_routes.py:207-211`, `routes/user_routes.py:52,71-78`, `routes/user_routes.py:134-151`, `routes/task_routes.py:225-238`, `routes/report_routes.py:211-223`, `app.py:15`
- **Description**: (1) senhas armazenadas com **MD5 sem salt** (`hashlib.md5`); (2) `User.to_dict()` inclui o campo `password` (hash) e é devolvido por `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`; (3) `/login` devolve token falso `'fake-jwt-token-' + str(user.id)` — previsível e nunca validado; (4) **nenhum endpoint exige autenticação**, inclusive `DELETE /users/<id>` (apaga também todas as tasks do usuário), `DELETE /tasks/<id>` e `DELETE /categories/<id>`; (5) `POST /users` aceita `role` livre, permitindo a qualquer cliente criar um `admin`; (6) `CORS(app)` libera todas as origens.
- **Impact**: comprometimento de contas (hashes MD5 quebráveis são vazados pela API), escalada de privilégio trivial e destruição de dados por qualquer cliente anônimo.
- **Recommendation**: hash com `werkzeug.security.generate_password_hash/check_password_hash`; serializer de usuário que nunca expõe `password`; emitir token assinado (ex.: `itsdangerous`/JWT) e proteger mutações com middleware/decorator de autenticação e checagem de role; restringir CORS por config (Playbook P2, P8).

### [HIGH] AP-05 — Lógica de negócio e acesso a dados nas rotas
- **File**: `routes/task_routes.py:11-299`, `routes/user_routes.py:10-211`, `routes/report_routes.py:12-223`
- **Description**: todos os handlers fazem `Model.query...`, `db.session.add/commit/delete`, cálculo de atraso, estatísticas, taxa de conclusão, validações e montagem do JSON no mesmo bloco (ex.: `get_tasks` em `task_routes.py:11-63`, `summary_report` em `report_routes.py:12-101`, `delete_user` apaga tasks manualmente em `user_routes.py:140-142`). As rotas importam `db` e os models diretamente.
- **Impact**: viola MVC; regra duplicada, sem reuso e impossível de testar sem HTTP.
- **Recommendation**: criar `controllers/` (orquestração: extrair request, chamar service/model, escolher status) e mover regras/queries para `models/` e `services/`; rotas apenas mapeiam URL → controller (Playbook P3, P4, P5).

### [HIGH] AP-04 — God File / responsabilidades misturadas
- **File**: `routes/task_routes.py:1-299`, `routes/report_routes.py:157-223`, `app.py:9-34`
- **Description**: `task_routes.py` (299 linhas) concentra CRUD, busca, estatísticas, validação, serialização e erros; `report_routes.py` (223 linhas) mistura relatórios com o CRUD completo de `Category` (blueprint `reports` expondo `/categories`); `app.py` acumula config, criação do app, registro de rotas, handlers `/health` e `/`, e `create_all()` no import.
- **Impact**: arquivos com 3+ responsabilidades, difíceis de evoluir e de testar isoladamente.
- **Recommendation**: separar `category_routes.py`/`category_controller.py`, `report_controller.py`, `task_controller.py`; app factory enxuto como composition root (Playbook P3, P4).

### [HIGH] AP-06 — Estado global mutável e efeitos colaterais no import
- **File**: `app.py:9`, `app.py:30-31`, `seed.py:2`, `services/notification_service.py:6`
- **Description**: o `app` Flask é um objeto global de módulo e `db.create_all()` roda no momento do import de `app.py`; `seed.py` importa `app` apenas para obter o contexto, disparando criação de schema como efeito colateral. `NotificationService` mantém `self.notifications` em memória (lista mutável sem ciclo de vida/limite, perdida a cada restart).
- **Impact**: testes frágeis (não é possível criar app com outra config/banco), efeitos colaterais ao importar, estado perdido/crescente.
- **Recommendation**: adotar `create_app(config)` (application factory) com `db.create_all()` explícito no boot; persistir ou remover o histórico em memória (Playbook P6).

### [HIGH] AP-07 — Tratamento de erros ausente ou inadequado
- **File**: `routes/task_routes.py:62-63`, `137`, `204`, `236`; `routes/user_routes.py:130`, `149`; `routes/report_routes.py:186`, `207`, `221`; `utils/helpers.py:47`, `49`, `88`; `routes/task_routes.py:151-154`, `221-223`; `routes/user_routes.py:87-90`
- **Description**: `except:` vazio (captura até `KeyboardInterrupt`) engole a causa — ex.: `get_tasks` devolve apenas "Erro interno" sem log; falhas registradas só com `print`; ausência de try/except onde há risco real: `int(priority)`/`int(user_id)` em `task_routes.py:261,264`, `data = request.get_json()` seguido de `'name' in data` com `data=None` em `report_routes.py:196-197`, `len(data['title'])` com tipo inválido em `task_routes.py:167`. Não há error handler central; o formato de erro é montado à mão em cada rota.
- **Impact**: falhas silenciosas, 500 HTML do Flask em entradas inválidas, diagnóstico impossível.
- **Recommendation**: error handlers centrais (`@app.errorhandler`) com formato único `{ "error": ... }`, exceções de domínio nos services e `logging` no lugar de `print`; remover `except:` nus (Playbook P7).

### [MEDIUM] AP-08 — N+1 e queries ineficientes
- **File**: `routes/task_routes.py:41-57`, `routes/user_routes.py:22`, `routes/report_routes.py:53-68`, `routes/report_routes.py:161-164`, `routes/task_routes.py:281-287`, `routes/report_routes.py:30-43`, `routes/report_routes.py:15-28`
- **Description**: `get_tasks` faz `User.query.get`/`Category.query.get` por task; `get_users` dispara lazy-load `len(u.tasks)` por usuário; `summary_report` consulta as tasks de cada usuário em loop (`report_routes.py:56`); `get_categories` faz um `COUNT` por categoria; atraso é calculado carregando **todas** as tasks em memória (`Task.query.all()`) em `task_stats` e `summary_report`; o resumo executa ~15 `COUNT` separados (um por status/prioridade). Nenhuma listagem tem paginação (`task_routes.py:14`, `user_routes.py:12`, `report_routes.py:159`).
- **Impact**: latência e carga no banco crescem linearmente (ou pior) com o volume.
- **Recommendation**: `joinedload`/`selectinload`, agregações com `GROUP BY` e `func.count`, filtro de atraso no SQL, paginação opcional por `limit/offset` mantendo o formato atual (Playbook P9).

### [MEDIUM] AP-09 — Validação de entrada ausente, frágil ou duplicada
- **File**: `routes/task_routes.py:87,104,113`, `routes/task_routes.py:166-184`, `routes/task_routes.py:261,264`, `routes/user_routes.py:103`, `routes/user_routes.py:124-125`, `routes/report_routes.py:173-180`, `routes/report_routes.py:196-203`
- **Description**: `priority < 1` com valor não numérico gera `TypeError` → 500; `len(data['title'])` com não-string; `int(priority)`/`int(user_id)` sem try na busca; `name` de usuário e `active` aceitos sem validação (`user_routes.py:103,125`); `color` de categoria sem validar (existe `is_valid_color` não utilizado); `update_category` quebra com corpo vazio; `marshmallow` está nas dependências, mas não é usado. Validações de status/e-mail/título copiadas entre create e update e em `helpers.py`.
- **Impact**: respostas 500 por entrada do cliente, dados inválidos persistidos.
- **Recommendation**: camada única de validação (schemas marshmallow já disponíveis ou validators no controller) reutilizada por create/update, retornando 400 com mensagem uniforme (Playbook P5).

### [MEDIUM] AP-10 — Duplicação de código (DRY)
- **File**: `routes/task_routes.py:30-39`, `71-80`, `283-287`; `routes/user_routes.py:171-180`; `routes/report_routes.py:33-43`, `132-135`; `routes/task_routes.py:17-28` vs `models/task.py:23-36`; `routes/user_routes.py:162-169`; `routes/task_routes.py:110,177`, `models/task.py:39`, `utils/helpers.py:75,110`; `routes/user_routes.py:61,106`, `utils/helpers.py:21`; `routes/task_routes.py:273-299` vs `routes/report_routes.py:103-155`
- **Description**: a regra de "atrasada" é reescrita 6 vezes em rotas apesar de existir `Task.is_overdue()` (`models/task.py:50-60`, nunca chamado); a serialização de task é copiada em `get_tasks` e `get_user_tasks` apesar de `to_dict()`; lista de status válidos repetida em 4 lugares; regex de e-mail em 3; contagem de status repetida em `task_stats`, `summary_report` e `user_report`.
- **Impact**: qualquer correção de regra precisa ser replicada; risco de divergência.
- **Recommendation**: usar `Task.is_overdue()` (com timezone correto), serializers únicos e constantes/validators compartilhados (Playbook P4, P5).

### [MEDIUM] AP-13 — APIs deprecated (agrupado)
- **File**: ver tabela "Deprecated APIs" (`datetime.utcnow()` em 20+ locais; `Model.query.get()` em 16 locais; MD5 para senha)
- **Description**: uso de `datetime.utcnow()` (deprecated desde Python 3.12) e `Query.get()` (legado no SQLAlchemy 2.0), além de `Model.query` (interface legada segundo a documentação do Flask-SQLAlchemy).
- **Impact**: warnings hoje, remoção futura; `utcnow()` ainda cria datetimes "naive" ambíguos.
- **Recommendation**: `datetime.now(timezone.utc)` e `db.session.get(Model, id)` (Playbook P8, P11). Cuidado: ao migrar para datetimes aware, manter o formato de saída `str(...)` das datas para preservar o contrato.

### [LOW] AP-11 — Magic numbers e strings
- **File**: `routes/task_routes.py:96,99,110,113,177,182`, `routes/user_routes.py:64,71,115,120`, `routes/report_routes.py:84-88`, `routes/report_routes.py:180`, `models/task.py:11-12,39`, `models/category.py:10`
- **Description**: status (`'pending'`, `'in_progress'`, `'done'`, `'cancelled'`), roles, limites de título (3/200), prioridade (1-5), senha mínima (4) e cor padrão `'#000000'` como literais repetidos. Constantes já existem em `utils/helpers.py:110-116` mas ninguém as usa.
- **Impact**: alterações exigem caça manual de literais; risco de inconsistência.
- **Recommendation**: centralizar em módulo de constantes/enums do domínio e importá-lo (Playbook P10).

### [LOW] AP-12 — Nomenclatura, código morto e debug com `print`
- **File**: `app.py:7`, `routes/task_routes.py:7`, `routes/user_routes.py:5-6`, `routes/report_routes.py:7-8`, `utils/helpers.py:1-7`, `utils/helpers.py:9-108`, `services/notification_service.py:4-48`, `models/task.py:38-48`, `routes/task_routes.py:149,153,219,234`, `routes/user_routes.py:83,89,147`, `services/notification_service.py:21,24`, `utils/helpers.py:39-41`, `models/task.py:50-60`, `models/user.py:34-38`
- **Description**: imports não usados (`os, sys, json, hashlib, time, timedelta`, `format_date`, `calculate_percentage`...); `helpers.py` quase inteiro e `NotificationService` nunca são chamados; `validate_status`/`validate_priority` sem uso; `print` como log; `if/else` retornando `True/False` redundante; `type(x) == list` em vez de `isinstance`; nomes curtos (`p1..p5`, `t`, `cat`, `d`); blueprint `reports` contendo categorias.
- **Impact**: ruído, confusão sobre o que é código ativo.
- **Recommendation**: remover código morto e imports, trocar `print` por `logging`, simplificar booleanos e renomear (Playbook P10).

## Deprecated APIs
| API obsoleta | Local | Equivalente moderno | Severidade |
|---|---|---|---|
| `datetime.utcnow()` | `models/category.py:11`; `models/task.py:15,16,52`; `models/user.py:14`; `routes/task_routes.py:31,72,215,285`; `routes/user_routes.py:172`; `routes/report_routes.py:35,42,45,71,133`; `services/notification_service.py:35`; `utils/helpers.py:38`; `seed.py:66,67,69,70,74` | `datetime.now(timezone.utc)` | MEDIUM |
| `Model.query.get(id)` (`Query.get`, legado no SQLAlchemy 2.0) | `routes/task_routes.py:42,51,67,117,122,158,188,195,227`; `routes/user_routes.py:29,94,136,155`; `routes/report_routes.py:105,192,213` | `db.session.get(Model, id)` | MEDIUM |
| `Model.query` (interface legada Flask-SQLAlchemy) | todas as rotas, `seed.py:11-13,94-96` | `db.session.execute(db.select(Model))` / `db.session.scalars(...)` | LOW |
| MD5 para hash de senha | `models/user.py:29,32` | `werkzeug.security.generate_password_hash` / bcrypt / argon2 | HIGH (segurança — tratado em AP-03) |

## Target Architecture (proposta)
```
task-manager-api/
├── app.py                      # entry point: create_app() + run (composition root)
├── config/
│   └── settings.py             # lê env vars (SECRET_KEY, DATABASE_URL, DEBUG, SMTP...)
├── database.py                 # instância db (SQLAlchemy)
├── models/                     # entidades + regras de domínio (is_overdue, set/check_password)
│   ├── task.py
│   ├── user.py
│   └── category.py
├── services/                   # regras de negócio e queries agregadas
│   ├── task_service.py
│   ├── user_service.py
│   ├── category_service.py
│   ├── report_service.py
│   └── notification_service.py
├── controllers/                # orquestração por recurso (request -> service -> view)
│   ├── task_controller.py
│   ├── user_controller.py
│   ├── category_controller.py
│   └── report_controller.py
├── routes/                     # só mapeamento URL -> controller (blueprints)
│   ├── task_routes.py
│   ├── user_routes.py
│   ├── category_routes.py
│   └── report_routes.py
├── views/                      # serializers (nunca expõem password)
│   └── serializers.py
├── middlewares/
│   ├── auth.py                 # autenticação/role
│   └── error_handler.py        # tratamento central de erros
├── utils/
│   └── constants.py            # status, roles, limites
└── seed.py
```

================================
Total: 12 achados (2 critical, 4 high, 4 medium, 2 low)
================================

Fase 2 concluída. Deseja prosseguir com a refatoração (Fase 3)? [s/n]
