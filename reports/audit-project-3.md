================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (SQLite via Flask-SQLAlchemy 3.1.1 / SQLAlchemy 2.1.9)
Files:   15 analyzed | ~1158 lines of code
Architecture: Partially layered — `models/`, `routes/`, `services/`, `utils/` existem, mas as rotas concentram queries e regras de negócio, a configuração está hardcoded em `app.py`, não há tratamento de erros centralizado e `services/` e `utils/` nunca são chamados

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 6 | LOW: 5

## Findings

### [CRITICAL] AP-04 Unprotected privilege and account-state endpoints
File: routes/user_routes.py:42-90, 52, 71-78, 92-132, 119-125, 134-151, 207-211
Description: Qualquer chamador anônimo pode criar um usuário com `role: "admin"` (`role = data.get('role', 'user')` em `POST /users`), promover qualquer conta (`user.role = data['role']`), ativar/desativar contas (`user.active = data['active']`) em `PUT /users/<id>` e apagar contas com todas as suas tasks (`db.session.delete(user)` em `DELETE /users/<id>`). O login devolve `'fake-jwt-token-' + str(user.id)`, um token previsível que nenhuma rota verifica: o guard não existe.
Impact: Escalada de privilégio e tomada de controle trivial (`POST /users {"role":"admin"}`), bloqueio de contas legítimas e perda de dados por qualquer cliente anônimo.
Recommendation: Emitir no `POST /login` um token assinado e com expiração (`itsdangerous.URLSafeTimedSerializer`, já incluso no Flask, chave = `SECRET_KEY`), mantendo o formato da resposta, e criar os guards `require_auth` / `require_role` / `optional_auth` (header `Authorization: Bearer <token>`; 401 sem token válido, 403 autenticado sem o papel exigido). Proteger exatamente estas operações:
  - `POST /users` quando o corpo traz `role` diferente de `"user"` (`"admin"` ou `"manager"`) → admin
  - `PUT /users/<id>` quando o corpo contém `role` ou `active` → admin
  - `DELETE /users/<id>` → admin
  Operações sem esses campos (`POST /users` com role `user`/omitido, `PUT /users/<id>` só com `name`/`email`/`password`) e o CRUD de tasks/categorias permanecem públicos. (T-17, variante 17-B)

### [CRITICAL] AP-06 Sensitive data exposure (password hash in responses)
File: models/user.py:21, routes/user_routes.py:33, 85, 129, 209
Description: `User.to_dict()` inclui `'password': self.password`; esse dicionário é devolvido por `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e dentro de `user` na resposta de `POST /login`.
Impact: Qualquer cliente obtém o hash MD5 (sem salt) de qualquer usuário e o quebra em segundos com rainbow tables.
Recommendation: Remover `password` de `User.to_dict()` (serialização pública única), mantendo todas as demais chaves das respostas. (T-10)

### [CRITICAL] AP-05 Insecure password storage (MD5)
File: models/user.py:27-32
Description: `set_password` grava `hashlib.md5(pwd.encode()).hexdigest()` e `check_password` compara com o mesmo MD5 sem salt.
Impact: Um vazamento do banco expõe todas as senhas (MD5 é rápido e sem salt; reuso em outros serviços).
Recommendation: Usar `werkzeug.security.generate_password_hash` / `check_password_hash` (Werkzeug já é dependência do Flask). Para bancos existentes, `check_password` aceita o hash MD5 legado (32 hex) e o re-hasheia com o algoritmo novo no primeiro login bem-sucedido. (T-09)

### [CRITICAL] AP-01 Hardcoded secrets and credentials
File: app.py:13, services/notification_service.py:7-10
Description: `app.config['SECRET_KEY'] = 'super-secret-****'`; credenciais SMTP literais no construtor: `email_user = 'taskmanager@****'`, `email_password = 'senh****'`, host/porta fixos.
Impact: Quem tem acesso ao repositório obtém a chave que passará a assinar os tokens de autenticação e a senha do e-mail; impossível rotacionar por ambiente.
Recommendation: Criar `config/settings.py` lendo `SECRET_KEY`, `DATABASE_URL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `TOKEN_MAX_AGE` de variáveis de ambiente (carregando `.env` via `python-dotenv`, já declarado); sem `SECRET_KEY` gerar valor aleatório por processo com aviso no log; documentar as variáveis em `.env.example`. `NotificationService` recebe as configurações SMTP por injeção. (T-01)

### [HIGH] AP-12 Insecure configuration hardcoded for production
File: app.py:15, 34, routes/user_routes.py:210
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` liga o debugger do Werkzeug exposto na rede; `CORS(app)` sem restrição de origem; token falso `'fake-jwt-token-'` (ver AP-04).
Impact: O debugger interativo permite execução remota de código a quem alcança a porta; CORS aberto + token falso = nenhum controle de acesso real.
Recommendation: `DEBUG` lido de `FLASK_DEBUG` (padrão desligado), `HOST` (padrão `127.0.0.1`) e `PORT` (padrão `5000`) de variáveis de ambiente; origens CORS de `CORS_ORIGINS` (lista separada por vírgula; padrão `*` para manter o comportamento atual em desenvolvimento); token substituído conforme AP-04. (T-01, T-17)

### [HIGH] AP-10 Broken referential integrity on category deletion
File: routes/report_routes.py:211-223
Description: `DELETE /categories/<id>` faz `db.session.delete(cat)` sem tratar as tasks que referenciam a categoria; o SQLite não aplica as foreign keys (PRAGMA desligado), então as tasks ficam com `category_id` apontando para um registro inexistente.
Impact: Tasks órfãs: `GET /tasks` passa a devolver `category_name: null` com `category_id` preenchido, e `PUT /tasks/<id>` com esse `category_id` falha com 404.
Recommendation: No controller de categorias, na mesma transação, setar `category_id = NULL` nas tasks da categoria e então remover a categoria (commit único, rollback em erro). A exclusão de usuário mantém a remoção das tasks dele e do usuário em uma única transação. (T-11)
Correction (2026-11-23, Phase 3 baseline): a descrição/impacto acima estão incorretos. O teste no código original (`DELETE /categories/2` e depois `GET /tasks`) mostrou a task 2 com `category_id: null`: o relacionamento `Category.tasks` (backref, cascade padrão `save-update`) já anula a FK dos filhos ao remover o pai, então não há tasks órfãs. O risco real é menor (a integridade depende de um comportamento implícito do ORM e não vale para deletes em massa / SQL direto); a severidade efetiva é LOW. A Recommendation continua válida e é implementada integralmente (anulação explícita na mesma transação), sem mudar o contrato observado.

### [HIGH] AP-07 Business logic in route handlers (fat routes)
File: routes/task_routes.py:11-63, 85-154, 156-223, 240-271, 273-299; routes/user_routes.py:42-90, 92-132, 153-183; routes/report_routes.py:12-101, 103-155, 157-223
Description: Os handlers fazem parsing, validação, consultas ORM (`Task.query`, `db.session`), regras de negócio (cálculo de atraso, taxa de conclusão, agregações de relatório, unicidade de e-mail, verificação de FK) e serialização no mesmo corpo; `summary_report` tem 90 linhas. As rotas de categoria vivem em `report_routes.py`.
Impact: Regras não reutilizáveis nem testáveis sem HTTP; qualquer alteração exige editar várias rotas (viola SRP/MVC).
Recommendation: Criar `controllers/` (`task_controller.py`, `user_controller.py`, `category_controller.py`, `report_controller.py`) com toda a orquestração e regras; rotas em `views/` (blueprints de tasks, users, categories, reports, system) apenas fazem parsing do request, chamam o controller e formatam a resposta; mover as rotas de categoria para seu próprio blueprint mantendo os mesmos paths. (T-04)

### [HIGH] AP-08 Tight coupling / no composition root
File: app.py:9-31, routes/task_routes.py:2-5, routes/user_routes.py:2-4, routes/report_routes.py:2-5, services/notification_service.py:5-16, seed.py:2
Description: `app = Flask(__name__)` criado no import com efeitos colaterais (`db.create_all()`); toda rota importa diretamente o singleton `db` e os models; `NotificationService` monta suas próprias credenciais e abre `smtplib.SMTP(...)` internamente; `seed.py` importa `app` diretamente.
Impact: Impossível trocar banco/integrações em testes ou configurar a aplicação por ambiente (violação de DIP).
Recommendation: App factory `create_app(settings=None)` que conecta config → DB → repositórios → serviços → controllers → blueprints; controllers recebem dependências pelo construtor; `NotificationService` recebe as configurações SMTP; `app.py` mantém `python app.py` funcionando e `seed.py` usa `create_app()`. (T-05)

### [MEDIUM] AP-14 Missing and duplicated input validation
File: routes/task_routes.py:96-114, 166-184, 260-264; routes/user_routes.py:54-72, 102-122; routes/report_routes.py:196-197; utils/helpers.py:19-23, 57-108
Description: `priority < 1` sem checar tipo (`"priority": "2"` → `TypeError` → 500); `len(data['title'])` com `title: null` → 500 no update; `int(priority)` / `int(user_id)` em `/tasks/search` com valor não numérico → 500; `PUT /categories/<id>` faz `'name' in data` sem checar corpo vazio → 500; regras de task e de usuário copiadas entre create e update, enquanto `process_task_data` e `validate_email` existem e não são usados.
Impact: Entradas inválidas retornam 500 em vez de 400; regras divergem entre endpoints.
Recommendation: Módulo `controllers/validators.py` único (derivado de `process_task_data`/`validate_email`) usado por create e update de tasks e usuários; checar tipo de `priority` (inteiro, não bool) e `title` (string); parâmetros de busca não numéricos → 400; corpo ausente em `PUT /categories/<id>` → 400 `Dados inválidos`; mensagens de erro existentes preservadas. (T-14)

### [MEDIUM] AP-13 N+1 queries
File: routes/task_routes.py:41-57, 275-287; routes/user_routes.py:22; routes/report_routes.py:15-28, 53-68, 159-164
Description: `GET /tasks` chama `User.query.get` e `Category.query.get` para cada task; `GET /users` acessa `len(u.tasks)` (lazy load por usuário); `/reports/summary` executa 12 `COUNT` separados e uma query de tasks por usuário; `GET /categories` faz um `COUNT` por categoria; `/tasks/stats` faz 5 `COUNT` + carrega todas as tasks.
Impact: Tempo de resposta e carga no banco crescem linearmente com o volume de dados.
Recommendation: `joinedload(Task.user, Task.category)` na listagem de tasks; contagens agregadas com `GROUP BY` (`task_count` por usuário e por categoria, tasks por status e por prioridade, concluídas por usuário) em métodos de repositório; uma única consulta de tasks para o cálculo de atrasadas. (T-08)

### [MEDIUM] AP-16 Inconsistent / absent error handling
File: routes/task_routes.py:62, 137, 151, 204, 221, 236; routes/user_routes.py:87, 130, 149; routes/report_routes.py:186, 207, 221; utils/helpers.py:46, 49, 88
Description: `except:` nus e `except Exception` repetidos em cada handler (o `GET /tasks` inteiro fica dentro de um `try` que devolve `{'error': 'Erro interno'}` escondendo a causa); não há `@app.errorhandler`; erros não previstos voltam como página HTML do Flask/debugger.
Impact: Falhas reais escondidas, formato de erro imprevisível para o cliente.
Recommendation: Hierarquia de exceções de domínio (`ValidationError` 400, `UnauthorizedError` 401, `ForbiddenError` 403, `NotFoundError` 404, `ConflictError` 409) e `middlewares/error_handler.py` registrado na factory, sempre respondendo `{'error': <mensagem>}`; exceções inesperadas → 500 `{'error': 'Erro interno'}` com `logger.exception`, e rollback da sessão; remover os `try/except` dos handlers e capturar apenas `ValueError` no parse de datas. (T-07)

### [MEDIUM] AP-15 Code duplication (overdue rule, serialization, constants)
File: routes/task_routes.py:17-39, 71-80, 110, 177, 283-287; routes/user_routes.py:61, 71, 106, 120, 162-180; routes/report_routes.py:34-37, 132-135; models/task.py:39, 50-60; utils/helpers.py:21, 75, 110-111
Description: A regra "task atrasada" está reimplementada 6 vezes (enquanto `Task.is_overdue` existe e não é usado); o mapeamento task→dict é copiado de `Task.to_dict()` em `GET /tasks` e `GET /users/<id>/tasks`; a lista de status, a lista de roles e a regex de e-mail aparecem em 3–4 lugares.
Impact: As regras divergem com o tempo; cada correção precisa ser aplicada N vezes.
Recommendation: `Task.is_overdue()` como fonte única da regra; serializações derivadas de `Task.to_dict()` (variantes de lista e de tarefas do usuário em `views/presenters.py`); constantes `TASK_STATUSES`, `USER_ROLES` e `EMAIL_REGEX` definidas uma única vez nos models/validators. (T-15, T-04)

### [MEDIUM] AP-17 Deprecated APIs (`datetime.utcnow`, `Query.get`)
File: models/task.py:15-16, 52; models/user.py:14; models/category.py:11; routes/task_routes.py:31, 42, 51, 67, 72, 117, 122, 158, 188, 195, 215, 227, 285; routes/user_routes.py:29, 94, 136, 155, 172; routes/report_routes.py:35, 42, 45, 71, 105, 133, 192, 213; utils/helpers.py:38; services/notification_service.py:35; seed.py:66-74
Description: `datetime.utcnow()` está deprecado no Python 3.12+ (confirmado: `DeprecationWarning` com `python -W default` no 3.14 instalado); `Model.query.get(id)` emite `LegacyAPIWarning` no SQLAlchemy 2.1.9 instalado.
Impact: Quebra em upgrades futuros e polui os logs com warnings.
Recommendation: Helper único `utcnow()` = `datetime.now(timezone.utc).replace(tzinfo=None)` (mantém datetimes naive e o mesmo formato de string nas respostas) usado em defaults de coluna e regras; `db.session.get(Model, id)` no lugar de `Model.query.get(id)`. (T-13)

### [MEDIUM] AP-18 Side effects and infrastructure in the wrong place
File: app.py:30-31; services/notification_service.py:5-25; seed.py:2
Description: `db.create_all()` executa no import de `app.py` (importar o módulo cria o banco); `NotificationService` mistura credenciais, conexão SMTP e `print`; `seed.py` depende desse efeito colateral do import.
Impact: Efeitos ocultos ao importar módulos, impossível testar sem criar banco/abrir conexão SMTP.
Recommendation: `db.create_all()` dentro da app factory; `NotificationService` como adaptador em `services/` com configuração injetada e `logging`, construído pela composition root. (T-05, T-01)

### [LOW] AP-22 `print` used as logging
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24; utils/helpers.py:39, 41
Description: Mensagens operacionais e de erro (`print(f"Erro ao criar task: {str(e)}")`, `print(f"Usuário criado: ...")`) via `print`.
Impact: Sem níveis, sem estrutura, impossível silenciar ou encaminhar.
Recommendation: `logging.getLogger(__name__)` com níveis `info`/`exception`; configuração de logging na factory (o `print` de saída do CLI `seed.py` permanece). (T-16)

### [LOW] AP-21 Unused imports and dead code
File: app.py:7; routes/task_routes.py:7; routes/user_routes.py:6; routes/report_routes.py:7-8; models/task.py:3, 38-48; models/user.py:3, 34-38; utils/helpers.py:3-7, 9-55; requirements.txt:4-5
Description: `import os, sys, json` (app.py), `json, os, sys, time` (task_routes), `hashlib, json` (user_routes), `format_date, calculate_percentage, json` (report_routes) nunca usados; `validate_status`, `validate_priority`, `is_admin`, `format_date`, `calculate_percentage`, `sanitize_string`, `generate_id`, `log_action`, `is_valid_color` nunca chamados; `marshmallow` e `requests` declarados e não importados.
Impact: Ruído e dependências enganosas.
Recommendation: Remover imports e funções não usados (reaproveitando `is_admin` nos guards e `parse_date`/`process_task_data` nos validators) e remover `marshmallow`/`requests` do `requirements.txt`. (T-16)

### [LOW] AP-19 Magic numbers and strings
File: routes/task_routes.py:96, 99, 104, 113, 167, 169, 182; routes/user_routes.py:64, 115; routes/report_routes.py:24-28, 129, 180; app.py:34
Description: Limites literais `len(title) < 3`, `> 200`, `priority < 1 or > 5`, `len(password) < 4`, `t.priority <= 2` (alta prioridade), `'#000000'`, prioridades `1..5` mapeadas para `critical..minimal`, porta `5000`; as constantes já existem em `utils/helpers.py:110-116` mas não são usadas.
Impact: Significado escondido; mudar uma regra exige caçar literais.
Recommendation: Constantes nomeadas (`TITLE_MIN_LENGTH`, `TITLE_MAX_LENGTH`, `PRIORITY_MIN`, `PRIORITY_MAX`, `DEFAULT_PRIORITY`, `HIGH_PRIORITY_THRESHOLD`, `MIN_PASSWORD_LENGTH`, `DEFAULT_COLOR`, `PRIORITY_LABELS`) nos models; porta em `config`. (T-15)

### [LOW] AP-23 Verbose conditionals and non-idiomatic code
File: models/user.py:35-38; models/task.py:39-43, 46-48, 51-60; routes/task_routes.py:30-39, 141, 210; routes/report_routes.py:58-61, 119-135; utils/helpers.py:21-23, 53-55, 103
Description: `if cond: return True else: return False`; pirâmides de 3 `if` para um booleano (atraso); `type(tags) == list`; contadores manuais em loop.
Impact: Legibilidade.
Recommendation: Retornar a expressão booleana diretamente, `isinstance`, `sum(...)`/agregações SQL. (T-16)

### [LOW] AP-20 Poor naming
File: routes/task_routes.py:16, 51; routes/user_routes.py:14; routes/report_routes.py:24-28, 55, 159; models/task.py:45; models/user.py:27
Description: Nomes de uma letra ou crípticos: `t`, `u`, `c`, `cat`, `p`, `p1`..`p5`, `pwd`.
Impact: Intenção do código menos clara.
Recommendation: Renomear internamente (`task`, `user`, `category`, `priority`, `password`); campos públicos do request/response permanecem iguais. (T-16)

## Deprecated APIs
| Location | Deprecated API | Modern replacement |
|---|---|---|
| models/task.py:15-16, 52; models/user.py:14; models/category.py:11 | `datetime.utcnow` (column defaults / overdue rule) | `datetime.now(timezone.utc)` (helper naive UTC) |
| routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133 | `datetime.utcnow()` | `datetime.now(timezone.utc)` |
| utils/helpers.py:38; services/notification_service.py:35; seed.py:66-74 | `datetime.utcnow()` | `datetime.now(timezone.utc)` |
| routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227 | `Model.query.get(id)` | `db.session.get(Model, id)` |
| routes/user_routes.py:29, 94, 136, 155 | `Model.query.get(id)` | `db.session.get(Model, id)` |
| routes/report_routes.py:105, 192, 213 | `Model.query.get(id)` | `db.session.get(Model, id)` |

## Endpoint contract (to preserve in Phase 3)
| Method | Path | Handler |
|---|---|---|
| GET | /health | app.py:22 |
| GET | / | app.py:26 |
| GET | /tasks | routes/task_routes.py:11 |
| GET | /tasks/<id> | routes/task_routes.py:65 |
| POST | /tasks | routes/task_routes.py:85 |
| PUT | /tasks/<id> | routes/task_routes.py:156 |
| DELETE | /tasks/<id> | routes/task_routes.py:225 |
| GET | /tasks/search | routes/task_routes.py:240 |
| GET | /tasks/stats | routes/task_routes.py:273 |
| GET | /users | routes/user_routes.py:10 |
| GET | /users/<id> | routes/user_routes.py:27 |
| POST | /users | routes/user_routes.py:42 |
| PUT | /users/<id> | routes/user_routes.py:92 |
| DELETE | /users/<id> | routes/user_routes.py:134 |
| GET | /users/<id>/tasks | routes/user_routes.py:153 |
| POST | /login | routes/user_routes.py:185 |
| GET | /reports/summary | routes/report_routes.py:12 |
| GET | /reports/user/<id> | routes/report_routes.py:103 |
| GET | /categories | routes/report_routes.py:157 |
| POST | /categories | routes/report_routes.py:167 |
| PUT | /categories/<id> | routes/report_routes.py:190 |
| DELETE | /categories/<id> | routes/report_routes.py:211 |

================================
Total: 19 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
