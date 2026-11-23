================================
FASE 1: ANÁLISE DO PROJETO
================================
Linguagem:      Python 3 (3.13 no ambiente)
Framework:      Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.0.36), Werkzeug 3.1
Dependências:   flask-cors 4.0.0, python-dotenv 1.0.0, itsdangerous (transitiva, usada em middlewares/auth.py), marshmallow 3.20.1 e requests 2.31.0 (declaradas, não usadas)
Domínio:        Task, User, Category (task pertence a um usuário e a uma categoria)
Arquitetura:    Em camadas — app.py (composition root), config/, routes/ (blueprints), controllers/, services/, models/, validators/, views/ (serializers), middlewares/ (auth + erros), utils/
Arquivos:       44 arquivos .py analisados (~1041 linhas não vazias) + requirements.txt, .env.example
Banco de dados: SQLite (instance/tasks.db) via ORM (Flask-SQLAlchemy, API 2.0: select()/Session.get)
Endpoints:      22 — GET / e /health; GET/POST /tasks, GET /tasks/search, GET /tasks/stats, GET/PUT/DELETE /tasks/<id>;
                GET/POST /users, GET/PUT/DELETE /users/<id>, GET /users/<id>/tasks, POST /login;
                GET /reports/summary, GET /reports/user/<id>; GET/POST /categories, PUT/DELETE /categories/<id>
Como executar:  pip install -r requirements.txt && python seed.py && python app.py  (http://127.0.0.1:5000)
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask (3.0.0) / Flask-SQLAlchemy 3.1.1 / SQLAlchemy 2.0.36
Files:   44 analisados | ~1041 linhas de código
Database: SQLite via ORM (Flask-SQLAlchemy)

## Summary
| Severidade | Qtde |
|---|---|
| CRITICAL | 2 |
| HIGH     | 2 |
| MEDIUM   | 4 |
| LOW      | 6 |
| **Total** | **14** |

## Current Architecture
O projeto já está em camadas (resultado de uma refatoração anterior): rotas só mapeiam URL → controller, controllers orquestram validator → service → view, services concentram o ORM, erros são centralizados em `middlewares/error_handler.py` e segredos vêm de `config/settings.py`. Não há SQL cru, God files nem estado global mutável. Os desvios remanescentes são de **segurança (controle de acesso incompleto)**, validação de entrada, ausência de paginação, serialização dentro de service e APIs legadas do SQLAlchemy.

## Findings
(ordenados por severidade: CRITICAL → HIGH → MEDIUM → LOW)

### [CRITICAL] AP-03 — Escalada de privilégio e sequestro de conta anônimos em `PUT /users/<id>`
- **File**: `routes/user_routes.py:11`, `controllers/user_controller.py:30-34`, `validators/user_validator.py:46-63`, `services/user_service.py:50-59`
- **Description**: `PUT /users/<id>` é registrado sem `require_auth`/`require_admin`, e o validator aceita `role`, `active`, `password` e `email` de qualquer chamador. Verificado: requisição anônima `PUT /users/1 {"role":"admin"}` → 200 com `role: admin`; `PUT /users/2 {"password":"hacked"}` → 200, e o login da vítima com a nova senha → 200. Mesmo com token, não há checagem de dono nem restrição de campos privilegiados.
- **Impact**: qualquer pessoa vira administrador, troca a senha/e-mail de qualquer conta (sequestro total) ou desativa usuários. Anula toda a proteção de `require_admin` em `DELETE /users/<id>`.
- **Recommendation**: aplicar P12 a **todas** as mutações de usuário: `require_auth` na rota; no controller, permitir só `current_user.id == user_id` ou admin; `role`/`active` só alteráveis por admin (403 para os demais, inclusive sobre si mesmo). Manter `POST /users` como registro público que nunca atribui role privilegiado (já existe a checagem em `user_controller.py:24-25`) e rejeitar também `active` na criação por não-admin. (Playbook P12)

### [CRITICAL] AP-03 — Mutações de tasks e categorias sem autenticação nem checagem de dono
- **File**: `routes/task_routes.py:9`, `routes/task_routes.py:13-14`, `routes/category_routes.py:9-11`, `controllers/task_controller.py:18-33`, `controllers/category_controller.py:14-29`, `validators/task_validator.py:69`, `validators/task_validator.py:87-88`
- **Description**: `POST /tasks`, `PUT /tasks/<id>`, `POST /categories` e `PUT /categories/<id>` aceitam requisições anônimas (verificado: 201/200 sem token). `DELETE /tasks/<id>` e `DELETE /categories/<id>` exigem apenas estar logado: qualquer usuário comum apaga a task de outro ou qualquer categoria. O campo `user_id` (dono da task) é livre na criação e na atualização, permitindo atribuir/transferir tasks de terceiros.
- **Impact**: adulteração e destruição de dados por anônimos ou por qualquer conta; impossível confiar em autoria/atribuição de tasks.
- **Recommendation**: P12 em toda a matriz de mutações: tasks → autenticado + dono (`task.user_id == current_user.id`) ou admin/manager; `user_id` diferente do próprio só por admin/manager; categorias (dado compartilhado) → somente admin. Checagens no controller/service, antes de persistir. (Playbook P12)

### [HIGH] AP-03 — Dados pessoais e relatórios expostos sem autenticação
- **File**: `routes/user_routes.py:8`, `routes/user_routes.py:10`, `routes/user_routes.py:13`, `routes/report_routes.py:7-8`, `views/user_view.py:5-13`, `services/report_service.py:75-84`, `services/report_service.py:98`
- **Description**: `GET /users`, `GET /users/<id>`, `GET /users/<id>/tasks`, `GET /reports/summary` e `GET /reports/user/<id>` são públicos e devolvem nome, **e-mail**, **role** e `active` de todos os usuários (verificado: `GET /users` anônimo → 200).
- **Impact**: enumeração de contas e identificação dos administradores — insumo direto para phishing/força bruta no `POST /login`, combinada com a política de senha fraca (achado MEDIUM abaixo).
- **Recommendation**: exigir `require_auth` nas leituras de usuários e relatórios (relatório individual: dono ou admin/manager; `/reports/summary`: admin/manager). É mudança de contrato de acesso; deve constar como mudança intencional. (Playbook P12)

### [HIGH] AP-02 — Defaults inseguros de configuração (SECRET_KEY conhecida e CORS aberto)
- **File**: `config/settings.py:13-15`, `config/settings.py:24`, `app.py:21-22`, `middlewares/auth.py:14-19`
- **Description**: sem a variável `SECRET_KEY`, a app usa `DEV_SECRET_KEY = 'dev-only-insecure-key-change-me'`, que está no código-fonte; o boot apenas registra um warning. Os tokens são assinados com essa chave e carregam só `{'id', 'role'}`. CORS padrão é `*`.
- **Impact**: num deploy sem `.env`, qualquer pessoa forja `{"id": 1}` com a chave pública e obtém token de administrador. O CORS `*` amplia a superfície para páginas de terceiros.
- **Recommendation**: não usar uma chave fixa como fallback: se `SECRET_KEY` faltar, gerar uma chave aleatória por processo (`secrets.token_urlsafe`) com warning (tokens expiram no restart, sem quebrar o `python app.py` local) ou falhar quando `DEBUG=false`; documentar `CORS_ORIGINS` restrito para produção. (Playbook P2)

### [MEDIUM] AP-03 — Política de senha fraca, credenciais de seed triviais e tokens não revogados
- **File**: `utils/constants.py:25`, `validators/user_validator.py:36-37`, `validators/user_validator.py:53-55`, `seed.py:23`, `seed.py:30`, `seed.py:37`, `middlewares/auth.py:18-36`
- **Description**: senha mínima de 4 caracteres; o seed cria um **admin** com senha `1234`; o token não carrega nenhuma versão de credencial, então continua válido por 24h após troca de senha.
- **Impact**: contas (inclusive admin) adivinháveis; um token vazado sobrevive à troca de senha.
- **Recommendation**: elevar o mínimo (ex.: 8) apenas para novas senhas, sem invalidar as existentes; ler senhas do seed de env/aleatórias e imprimi-las; opcional: incluir um fingerprint do hash de senha no token para revogação. (Playbook P2, P8)

### [MEDIUM] AP-09 — Validação de entrada incompleta (500 e dados inválidos)
- **File**: `validators/task_validator.py:66`, `validators/task_validator.py:82`, `validators/task_validator.py:13-20`, `validators/category_validator.py:7-10`, `validators/category_validator.py:25`, `validators/category_validator.py:35`, `validators/user_validator.py:7-10`, `validators/user_validator.py:19-22`, `services/task_service.py:70-72`
- **Description**: `description` (task e categoria) não tem checagem de tipo — `POST /tasks {"description": {"a":1}}` gera **500** (verificado: `sqlite3.ProgrammingError`). Nomes/e-mails não respeitam o tamanho das colunas (`String(100)`/`String(150)`): categoria com nome de 500 caracteres é aceita (verificado: 201; o SQLite não aplica o limite). Título `"   "` passa por não fazer `strip`. E-mail não é normalizado (`A@x.com` e `a@x.com` viram contas distintas). Na busca, `%` e `_` em `q` são interpretados como curingas do `LIKE`.
- **Impact**: erros 500 a partir de entrada do cliente; dados inconsistentes; duplicidade de contas.
- **Recommendation**: validar tipo `str` e tamanho máximo (constantes alinhadas às colunas) em `description`/`name`/`email`; `strip` em título e nome; normalizar e-mail com `lower()`; escapar curingas do `LIKE` (`.like(pattern, escape='\\')`). (Playbook P5)

### [MEDIUM] AP-08 — Listagens sem paginação e agregação em memória
- **File**: `services/task_service.py:18-25`, `services/task_service.py:68-79`, `services/user_service.py:13-19`, `services/user_service.py:29-31`, `services/category_service.py:9-16`, `services/report_service.py:29-30`, `services/report_service.py:88-109`
- **Description**: `GET /tasks`, `/tasks/search`, `/users`, `/users/<id>` (com tasks), `/users/<id>/tasks` e `/categories` devolvem a tabela inteira; `/reports/summary` lista todas as tasks atrasadas; `user_report` carrega todas as tasks do usuário para contar em Python.
- **Impact**: latência e memória crescem linearmente com o volume.
- **Recommendation**: `limit`/`offset` **opcionais** via query string (sem parâmetro, mantém a resposta atual, preservando o contrato); trocar a contagem de `user_report` por `GROUP BY status` + `Task.overdue_clause()` no SQL. (Playbook P9)

### [MEDIUM] AP-05 — Serialização de resposta dentro da camada de serviço
- **File**: `services/report_service.py:48-85`, `services/report_service.py:97-109`
- **Description**: `report_service` monta o JSON final (chaves, `str(due_date)`, dict do usuário com `id/name/email`), papel de View. O dict de usuário duplica parte de `views/user_view.py:5-13`.
- **Impact**: alterar o formato exige mexer na regra de negócio; os serializers de usuário divergem.
- **Recommendation**: service devolve dados/estruturas de domínio (contagens, lista de tasks atrasadas); criar `views/report_view.py` para dar forma à resposta, mantendo o JSON idêntico. (Playbook P5)

### [LOW] AP-13 — API legada: `ColumnOperators.isnot()`
- **File**: `models/task.py:36`, `services/category_service.py:13`, `services/report_service.py:40`, `services/user_service.py:17`
- **Description**: `isnot()` foi renomeado para `is_not()` no SQLAlchemy 1.4; o nome antigo permanece só por compatibilidade (confirmado na documentação do SQLAlchemy 2.0).
- **Impact**: candidato a remoção em versão futura; inconsistência com o `not_in()` moderno já usado em `models/task.py:38`.
- **Recommendation**: substituir por `is_not(None)`. (Playbook P8)

### [LOW] AP-13 — API legada: `relationship(..., backref=...)`
- **File**: `models/task.py:23-24`
- **Description**: a documentação do SQLAlchemy 2.0 classifica `relationship.backref` como legado; recomenda `back_populates` com `relationship()` explícito nos dois lados.
- **Impact**: atributos `User.tasks`/`Category.tasks` criados dinamicamente (invisíveis no código e na tipagem).
- **Recommendation**: declarar `tasks = db.relationship('Task', back_populates='user')` em `User` e `Category` e `back_populates` em `Task`. (Playbook P8)

### [LOW] AP-10 — Duplicação em validators e services
- **File**: `validators/category_validator.py:7-10`, `validators/user_validator.py:19-22`, `validators/user_validator.py:36-37`, `validators/user_validator.py:53-55`, `services/category_service.py:9-16`, `services/user_service.py:13-19`, `services/category_service.py:33-37`, `services/task_service.py:53-54`
- **Description**: `_name` idêntico em dois validators; regra de senha mínima repetida com mensagens diferentes ("Senha deve ter no mínimo 4 caracteres" vs "Senha muito curta"); padrão "lista + contagem de tasks por FK" copiado; laço `setattr` de update repetido.
- **Impact**: mudanças de regra precisam ser replicadas e tendem a divergir.
- **Recommendation**: extrair `validators/common.py` (`required_str`, `password`) e um helper de contagem por FK. Manter as mensagens atuais (contrato). (Playbook P4, P5)

### [LOW] AP-11 — Literais de status e versão espalhados
- **File**: `services/report_service.py:34`, `services/report_service.py:43`, `services/report_service.py:95`, `services/report_service.py:102-104`, `services/task_service.py:88`, `controllers/health_controller.py:11`
- **Description**: `'done'`, `'pending'`, `'in_progress'`, `'cancelled'` repetidos como literais embora existam `TASK_STATUSES`/`FINISHED_STATUSES` em `utils/constants.py`; versão da API `'1.0'` fixa no controller.
- **Impact**: renomear um status exige caçar literais.
- **Recommendation**: constantes `STATUS_DONE`, `STATUS_PENDING`… e `API_VERSION` em `utils/constants.py`. (Playbook P10)

### [LOW] AP-12 — Código morto, dependências desalinhadas e inconsistências
- **File**: `services/notification_service.py:9-46`, `requirements.txt:4-5`, `middlewares/auth.py:5`, `controllers/health_controller.py:7`, `seed.py:20-94`
- **Description**: `NotificationService` nunca é importado; além disso, abre SMTP sem `timeout` nem `with` (conexão vaza em exceção, `:19-25`) e monta o cabeçalho `Subject` com `task.title` sem sanitizar quebras de linha (`:23`, `:33`) — injeção de cabeçalho caso seja ativado. `marshmallow` e `requests` estão no `requirements.txt` sem uso; `itsdangerous` é importado diretamente mas não declarado. `/health` usa `datetime.now()` local enquanto o resto da API usa UTC (`utils/clock.py`). O seed usa nomes de uma letra (`u1`, `c1`, `t`, `td`).
- **Impact**: superfície e dependências desnecessárias; timestamps inconsistentes.
- **Recommendation**: remover (ou corrigir) o `NotificationService` — se mantido, usar `smtplib.SMTP(..., timeout=)` como context manager e `email.message.EmailMessage`; remover `marshmallow`/`requests` e declarar `itsdangerous`; `/health` com `utc_now()` mantendo o formato `str(datetime)`. (Playbook P10)

## Deprecated APIs
| API obsoleta | Local | Equivalente moderno | Severidade |
|---|---|---|---|
| `ColumnOperators.isnot()` | `models/task.py:36`, `services/category_service.py:13`, `services/report_service.py:40`, `services/user_service.py:17` | `ColumnOperators.is_not()` | LOW |
| `relationship(backref=...)` | `models/task.py:23-24` | `relationship(back_populates=...)` nos dois lados | LOW |

Boot com `python -W error::DeprecationWarning` não emitiu nenhum warning. `datetime.utcnow()`, `Query.get()` e `declarative_base` já foram substituídos (`utils/clock.py`, `Session.get()`).

## Target Architecture (proposta)
Estrutura atual mantida (já é MVC). Ajustes pontuais:
```
task-manager-api/
├── app.py                      # composition root (sem mudança)
├── config/settings.py          # SECRET_KEY sem fallback fixo
├── database.py
├── models/                     # back_populates, is_not()
├── routes/                     # require_auth em todas as mutações e leituras de PII
├── controllers/                # checagem dono/admin + campos privilegiados (P12)
├── services/                   # regra/ORM; paginação opcional; sem serialização
│   └── (notification_service.py removido ou corrigido)
├── validators/
│   └── common.py               # novo: validações compartilhadas
├── views/
│   └── report_view.py          # novo: forma JSON dos relatórios
├── middlewares/
│   ├── auth.py                 # + helpers de autorização (dono/role)
│   └── error_handler.py
└── utils/                      # constantes de status/versão
```

================================
Total: 14 achados (2 critical, 2 high, 4 medium, 6 low)
================================

> **Correção pós-auditoria (Fase 3):** o achado "[MEDIUM] AP-07 — Exclusão de categoria deixa tasks com referência órfã" foi removido por ser **falso positivo**. Testado no código original: o relacionamento `Category.tasks` (sem cascade de delete) faz o ORM zerar `category_id` das tasks na exclusão. Totais ajustados de 15 para 14.
