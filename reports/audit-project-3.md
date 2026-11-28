================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.14 + Flask 3.0.0 (SQLite via Flask-SQLAlchemy 3.1.1 / SQLAlchemy 2.1.9)
Files:   15 analyzed | ~1158 lines of code
Architecture: Partially layered — `models/`, `routes/`, `services/`, `utils/` existem, mas as rotas concentram validação, regras de negócio e queries N+1; configuração/segredos hardcoded em `app.py`; sem tratamento de erro centralizado; `NotificationService` e a maior parte de `utils/helpers.py` nunca são usados.

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 6 | LOW: 5

## Findings

### [CRITICAL] AP-04 Unprotected privilege / account endpoints (escalada de privilégio e account takeover)
File: routes/user_routes.py:42-90, 52, 71-78, 92-132, 105-112, 114-117, 119-122, 124-125, 134-151, 207-211
Description: Nenhuma rota verifica identidade ou papel. `POST /users` aceita `role` do corpo (`data.get('role', 'user')`, linha 52) e cria contas `admin`/`manager` para qualquer chamador anônimo. `PUT /users/<id>` altera `role` (119-122), `active` (124-125), `password` (`user.set_password(data['password'])`, 114-117) e `email` (105-112) de qualquer conta sem checar quem chama. `DELETE /users/<id>` (134-151) apaga qualquer usuário e suas tasks. O login devolve `'fake-jwt-token-' + str(user.id)` (linha 210), um token previsível que nenhuma rota verifica — o guard simplesmente não existe. Não há rotas `/admin/*`, SQL arbitrário ou wipe em massa expostos via HTTP (o wipe de `seed.py:11-14` é script CLI).
Impact: Qualquer anônimo executa `PUT /users/1 {"password": "x"}` sobre o admin (João, id 1), faz login com a nova senha e assume a conta admin; também pode se autopromover (`role: "admin"`), desativar ou apagar contas.
Recommendation: Implementar token assinado e com expiração emitido no login (`itsdangerous.URLSafeTimedSerializer`, que já vem com o Flask — sem nova dependência) em `services/token_service.py`, enviado como `Authorization: Bearer <token>`, e guards `require_auth` / `require_role` / `optional_auth` em `middlewares/auth.py`. A resposta do login mantém o mesmo formato (`message`, `user`, `token`); muda só o valor do token. Respostas: **401** sem credenciais válidas, **403** para autenticado sem permissão, status/corpo originais para chamador autorizado. Operações guardadas (lista fechada e obrigatória):
- `POST /users` quando o corpo contém `role` com valor diferente de `"user"` (`admin` ou `manager`) → admin
- `PUT /users/<id>` quando o corpo contém a chave `role` ou `active` → admin
- `PUT /users/<id>` quando o corpo contém a chave `password` ou `email` → o próprio usuário (`<id>` == chamador) ou admin (owner-or-admin)
- `DELETE /users/<id>` → admin
`POST /users` sem `role` (ou com `role: "user"`), `PUT /users/<id>` alterando só `name`, e todo o CRUD de tasks/categorias continuam públicos (ver follow-ups). (T-17, 17-B)

### [CRITICAL] AP-06 Sensitive data exposure — hash de senha nas respostas
File: models/user.py:21, routes/user_routes.py:33, 85, 129, 209
Description: `User.to_dict()` inclui `'password': self.password` (linha 21), e esse dict é devolvido por `GET /users/<id>` (33), `POST /users` (85), `PUT /users/<id>` (129) e `POST /login` (209).
Impact: Qualquer cliente anônimo obtém o hash de senha de qualquer usuário; como o hash é MD5 sem salt (AP-05), as senhas do seed (`1234`, `abcd`, `pass`) são revertidas instantaneamente.
Recommendation: Remover `password` de `to_dict()` (o serializer público nunca expõe credenciais); nenhum log imprime senha ou hash. Mudança de contrato intencional por segurança. (T-10)

### [CRITICAL] AP-05 Insecure password storage (MD5 sem salt)
File: models/user.py:3, 27-32
Description: `set_password` grava `hashlib.md5(pwd.encode()).hexdigest()` e `check_password` compara o mesmo MD5 com `==` (não é comparação em tempo constante).
Impact: Um vazamento do banco expõe todas as senhas (MD5 sem salt é quebrado por tabelas rainbow em segundos).
Recommendation: Usar `werkzeug.security.generate_password_hash` / `check_password_hash` (Werkzeug é dependência do Flask — sem nova dependência). Para hashes MD5 legados, `check_password` aceita o formato antigo uma vez e regrava com o hash novo (migração transparente). O seed passa a gerar hashes novos via `set_password`. (T-09)

### [CRITICAL] AP-01 Hardcoded secrets and credentials
File: app.py:11, 13, services/notification_service.py:7-10
Description: `app.config['SECRET_KEY'] = 'super-secret-****'` (app.py:13); credenciais SMTP literais `email_user = 'taskmanager@****'` e `email_password = 'senha****'` (notification_service.py:9-10), além de host/porta SMTP fixos (7-8); URI do banco fixa `'sqlite:///tasks.db'` (app.py:11).
Impact: Qualquer pessoa com acesso ao repositório obtém a chave de assinatura (que passará a assinar os tokens de auth — AP-04) e a senha do e-mail; impossível rotacionar por ambiente.
Recommendation: Criar `config/settings.py` que lê `SECRET_KEY`, `DATABASE_URL` (default `sqlite:///tasks.db`), `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `TOKEN_MAX_AGE`, `DEBUG`, `HOST`, `PORT`, `CORS_ORIGINS` de variáveis de ambiente (carregando `.env` via `python-dotenv`, já presente no `requirements.txt`). `SECRET_KEY` ausente → valor aleatório gerado no boot com aviso no log (dev). Nenhum segredo literal no código; documentar as variáveis em `.env.example`. (T-01)

### [HIGH] AP-12 Insecure configuration hardcoded for production
File: app.py:34, 15
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` liga o debugger do Werkzeug em todas as interfaces; `CORS(app)` libera qualquer origem sem configuração.
Impact: O debugger do Werkzeug exposto na rede permite execução remota de código; CORS aberto somado a autenticação (após AP-04) permite chamadas de qualquer site.
Recommendation: `DEBUG` lido de env com default `False`; `HOST` de env com default `127.0.0.1`; `PORT` de env com default `5000` (mantém `python app.py` em `http://localhost:5000`); origens CORS de `CORS_ORIGINS` (default `*` preserva o comportamento atual; produção define a lista explícita). (T-01, T-17)

### [HIGH] AP-07 Business logic in route handlers (fat routes)
File: routes/task_routes.py:11-63, 85-154, 156-223, 240-271, 273-299, routes/user_routes.py:42-90, 92-132, 134-151, 153-183, 185-211, routes/report_routes.py:12-101, 103-155, 157-223
Description: Os handlers fazem parsing, validação, consultas ORM (`Task.query`, `db.session`), regras de negócio (atraso, taxa de conclusão, agregações do relatório) e formatação no mesmo corpo — ex.: `summary_report` tem 89 linhas com 13 queries e agregação manual; `create_task` tem 70 linhas. O CRUD de categorias está dentro do blueprint de relatórios (`report_routes.py:157-223`).
Impact: Regras não podem ser reutilizadas nem testadas sem HTTP; qualquer mudança mexe na camada web (viola SRP/MVC).
Recommendation: Criar `controllers/` (`task_controller.py`, `user_controller.py`, `report_controller.py`, `category_controller.py`) com as regras e a orquestração; mover consultas para métodos de modelo/repositório em `models/`; deixar em `routes/` (camada view) apenas parsing → chamada do controller → `jsonify`; mover as rotas de categorias para `routes/category_routes.py` mantendo os mesmos paths. (T-04)

### [HIGH] AP-08 Tight coupling / no composition root
File: app.py:9-31, services/notification_service.py:5-10, 15, seed.py:2
Description: `app = Flask(__name__)` é criado no import com configuração, blueprints e `db.create_all()` (30-31) executados como efeito colateral; `NotificationService` monta sua própria configuração e instancia `smtplib.SMTP(...)` internamente; `seed.py` depende do objeto global `from app import app`.
Impact: Impossível criar uma app com outra configuração/banco (ex.: testes) ou trocar o adaptador de e-mail.
Recommendation: `create_app(settings=None)` em `app.py` como composition root: config → `db.init_app` + `create_all` → serviços (token, notificação, injetados com `settings`) → controllers → blueprints → error handlers; `python app.py` continua funcionando via `if __name__ == '__main__'`; `seed.py` usa `create_app()`. `NotificationService` recebe host/porta/credenciais no construtor. (T-05)

### [MEDIUM] AP-14 Missing or duplicated input validation
File: routes/task_routes.py:92-114, 113, 166-184, 182, 261, 264, routes/user_routes.py:61, 102-103, 106, 124-125, routes/report_routes.py:196-202, utils/helpers.py:19-23, 57-108
Description: `priority` é comparado com `<` sem checar tipo — `POST /tasks {"priority": "x"}` gera `TypeError` → HTTP 500 (confirmado); `int(priority)` / `int(user_id)` em `/tasks/search` sem `try` — `?priority=abc` → `ValueError` → HTTP 500 (confirmado); `len(data['title'])` quebra com `title` não-string/`null`; `update_category` faz `'name' in data` com `data` possivelmente `None`; `name` e `active` do usuário aceitos sem validação de tipo; cor da categoria não validada. A validação de task é copiada entre create e update, enquanto `process_task_data` e `validate_email` existem em `utils/helpers.py` e não são usados (regex de e-mail duplicada em user_routes 61 e 106).
Impact: Entradas inválidas viram 500 em vez de 400; regras divergem entre create e update.
Recommendation: Centralizar validação em `controllers/validators.py` (task, user, category, filtros de busca) usada por create e update, retornando 400 com `{'error': ...}` para tipos/intervalos inválidos (incluindo `priority` não inteiro, filtros de busca não numéricos, corpo ausente/não-objeto, `title` não-string, `active` não booleano), preservando as mensagens existentes do caminho de erro. (T-14)

### [MEDIUM] AP-16 Inconsistent / absent error handling
File: routes/task_routes.py:62, 137, 151, 204, 221, 236, routes/user_routes.py:87, 130, 149, routes/report_routes.py:186, 207, 221, utils/helpers.py:46, 49, 88, app.py:9-34
Description: 16 blocos `except:` / `except Exception` repetidos; `get_tasks` engole qualquer erro em `except:` (62); não existe `@app.errorhandler` — exceções não tratadas (ex.: `/tasks/search?priority=abc`) devolvem a página HTML padrão de 500 do Flask, enquanto os demais erros são JSON `{'error': ...}`.
Impact: Formato de erro imprevisível para o cliente; falhas reais ficam escondidas.
Recommendation: `middlewares/error_handler.py` com exceções de domínio (`ValidationError` 400, `UnauthorizedError` 401, `ForbiddenError` 403, `NotFoundError` 404, `ConflictError` 409) e handlers para HTTPException e `Exception` (500, com rollback e log), sempre no envelope `{'error': <mensagem>}`; remover os try/except por handler; trocar `except:` por exceções específicas. (T-07)

### [MEDIUM] AP-13 N+1 queries
File: routes/task_routes.py:41-57, 275-281, routes/user_routes.py:22, routes/report_routes.py:15-30, 53-68, 157-165
Description: `GET /tasks` executa `User.query.get` e `Category.query.get` por task (41-57); `GET /users` faz `len(u.tasks)` (lazy load) por usuário (22); `summary_report` roda `Task.query.filter_by(user_id=u.id)` por usuário (56) e 12 `COUNT`s separados por status/prioridade (15-28); `GET /categories` faz um `COUNT` por categoria (163); `task_stats` faz 5 counts + carga total (275-281).
Impact: O tempo de resposta e a carga do banco crescem linearmente com o número de registros.
Recommendation: Carregar relacionamentos com `joinedload`/`selectinload` em `GET /tasks`; usar `GROUP BY` (`func.count` agrupado por `status`, `priority`, `user_id`, `category_id`) em stats, summary, `/users` e `/categories`, mantendo os mesmos campos de resposta. (T-08)

### [MEDIUM] AP-15 Code duplication (DRY)
File: models/task.py:38-60, routes/task_routes.py:17-39, 71-80, 110, 177, 284-287, 296, routes/user_routes.py:61, 71, 106, 120, 171-180, routes/report_routes.py:34-37, 67, 132-135, 151, utils/helpers.py:21, 75, 110-111
Description: A regra "task atrasada" é reimplementada em 7 lugares (o método `Task.is_overdue` existe e não é usado); a serialização de task é copiada à mão em `get_tasks` (17-28) em vez de `to_dict()`; a lista de status válidos aparece 5 vezes, a de roles 3 vezes, a regex de e-mail 3 vezes e o cálculo de taxa de conclusão 3 vezes (`calculate_percentage` é importado e não usado).
Impact: As regras divergem com o tempo; correções precisam ser aplicadas N vezes.
Recommendation: Uma única regra `Task.is_overdue()` (usada por todas as rotas/relatórios), `to_dict()` como único serializer (com variantes explícitas para as respostas que têm campos extras), constantes únicas em `models/constants.py` (status, roles, limites) e `calculate_percentage` para taxas. (T-15, T-04)

### [MEDIUM] AP-18 Side effects and infrastructure in the wrong place
File: app.py:30-31, services/notification_service.py:4-48
Description: `db.create_all()` roda no import do módulo `app`; `NotificationService` mistura configuração SMTP fixa, conexão `smtplib` aberta dentro do método e um armazenamento em memória `self.notifications` — e nunca é instanciado por nenhuma rota.
Impact: Importar `app` cria o banco como efeito colateral; o serviço não é testável nem configurável.
Recommendation: Mover `create_all` para dentro de `create_app()`; transformar `NotificationService` em adaptador de infraestrutura configurado por injeção (settings do AP-01), com `logging` no lugar de `print`, instanciado no composition root e exposto em `app.extensions`. Ele continua sem ser chamado por endpoints (nenhuma mudança de comportamento); ligar notificações a eventos de task é follow-up. (T-05, T-01)

### [MEDIUM] AP-17 Deprecated / legacy APIs
File: models/user.py:14, models/task.py:15-16, 52, models/category.py:11, routes/task_routes.py:31, 42, 51, 67, 72, 117, 122, 158, 188, 195, 215, 227, 285, routes/user_routes.py:29, 94, 136, 155, 172, routes/report_routes.py:35, 42, 45, 71, 105, 133, 192, 213, services/notification_service.py:35, utils/helpers.py:38, seed.py:66-74
Description: `datetime.utcnow()` (deprecated desde Python 3.12; runtime é 3.14) em 23 pontos; `Model.query.get(id)` em 16 pontos — `LegacyAPIWarning` confirmado com `python -W default` (ex.: `routes/user_routes.py:29`, `routes/task_routes.py:67`, `routes/report_routes.py:192`).
Impact: Quebra em upgrades futuros do Python/SQLAlchemy; avisos poluem os logs.
Recommendation: Helper `utcnow()` único (`datetime.now(timezone.utc).replace(tzinfo=None)`, preservando datetimes naive no SQLite e o formato `str()` atual) e `db.session.get(Model, id)` em todos os pontos. (T-13)

### [LOW] AP-22 `print` as logging
File: routes/task_routes.py:149, 153, 219, 234, routes/user_routes.py:83, 89, 147, services/notification_service.py:21, 24, utils/helpers.py:39, 41
Description: Mensagens operacionais e de erro com `print(f"...")` no caminho das requisições (ex.: `print(f"ERRO: {str(e)}")`).
Impact: Sem níveis nem estrutura; impossível silenciar ou encaminhar.
Recommendation: `logging.getLogger(__name__)` com níveis `info`/`exception`; o `print` de `seed.py` (script CLI) pode permanecer. (T-16)

### [LOW] AP-19 Magic numbers and strings
File: routes/task_routes.py:96, 99, 104, 113, 167, 169, 182, routes/user_routes.py:64, 115, routes/report_routes.py:45, 129, 180, models/category.py:10, models/task.py:11-12
Description: Limites literais `3`/`200` (título), `1`/`5` (prioridade), `4` (senha), `priority <= 2` (alta prioridade), `days=7` (atividade recente), `'#000000'`, `'pending'`/`3` como defaults; as constantes já existem em `utils/helpers.py:110-116` e não são usadas.
Impact: Significado oculto; alterar uma regra exige caçar literais.
Recommendation: Usar constantes nomeadas em `models/constants.py` (`MIN_TITLE_LENGTH`, `MAX_TITLE_LENGTH`, `MIN_PRIORITY`, `MAX_PRIORITY`, `HIGH_PRIORITY_THRESHOLD`, `MIN_PASSWORD_LENGTH`, `RECENT_ACTIVITY_DAYS`, `DEFAULT_COLOR`, `DEFAULT_PRIORITY`, `STATUS_*`, `ROLE_*`). (T-15)

### [LOW] AP-21 Unused imports, variables and dead code
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, 38-48, utils/helpers.py:3-7, 9-12, 25-41, requirements.txt:4-5
Description: Imports não usados: `os, sys, json` (app.py:7), `json, os, sys, time` (task_routes.py:7), `hashlib, json` (user_routes.py:6), `format_date, calculate_percentage, json` (report_routes.py:7-8), `json` (models/task.py:3), `os, json, sys, math, hashlib` (helpers.py:3-7); funções nunca chamadas: `format_date`, `sanitize_string`, `generate_id`, `log_action`, `Task.validate_status`, `Task.validate_priority`; dependências não usadas `marshmallow`, `requests`.
Impact: Ruído e dependências enganosas.
Recommendation: Remover imports/funções mortas (reaproveitando o que for útil nos validators/constantes); remover `marshmallow` e `requests` do `requirements.txt`. (T-16)

### [LOW] AP-23 Verbose conditionals and non-idiomatic code
File: models/user.py:34-38, models/task.py:38-60, routes/task_routes.py:30-57, 141, 210, routes/report_routes.py:58-61, 119-135, utils/helpers.py:21-23, 53-55, 103
Description: `if cond: return True else: return False` (`is_admin`, `validate_status`, `validate_email`, `is_valid_color`); pirâmides de `if` de 3 níveis para um booleano (`is_overdue` e cópias); `type(tags) == list` em vez de `isinstance`; contadores manuais `completed = completed + 1`.
Impact: Legibilidade.
Recommendation: Retornar a expressão booleana diretamente, `isinstance`, `sum(...)`/agregação no banco. (T-16)

### [LOW] AP-20 Poor naming
File: routes/task_routes.py:16, routes/user_routes.py:14, routes/report_routes.py:24-28, 54, 161, models/category.py:14, seed.py:78
Description: Nomes de uma ou duas letras fora de lambdas: `t`, `u`, `c`, `d`, `td`, `p1`…`p5`, `cat`, `e`.
Impact: Legibilidade; intenção escondida.
Recommendation: Renomear internamente (`task`, `user`, `category`, `priority_counts`…), mantendo os nomes de campos públicos da API. (T-16)

## Deprecated APIs
| Location | Deprecated API | Modern replacement |
|---|---|---|
| models/user.py:14, models/task.py:15-16, models/category.py:11 | `default=datetime.utcnow` | `default=utcnow` helper (`datetime.now(timezone.utc)` naive) |
| models/task.py:52, routes/task_routes.py:31, 72, 215, 285, routes/user_routes.py:172, routes/report_routes.py:35, 42, 45, 71, 133, services/notification_service.py:35, utils/helpers.py:38, seed.py:66-74 | `datetime.utcnow()` (Python ≥ 3.12) | `datetime.now(timezone.utc)` |
| routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227, routes/user_routes.py:29, 94, 136, 155, routes/report_routes.py:105, 192, 213 | `Model.query.get(id)` (SQLAlchemy 2.x `LegacyAPIWarning`) | `db.session.get(Model, id)` |

## Endpoint contract (to preserve in Phase 3)
| Method | Path | Handler |
|---|---|---|
| GET | /health | app.py:22 |
| GET | / | app.py:26 |
| GET | /tasks | routes/task_routes.py:11 |
| GET | /tasks/<int:task_id> | routes/task_routes.py:65 |
| POST | /tasks | routes/task_routes.py:85 |
| PUT | /tasks/<int:task_id> | routes/task_routes.py:156 |
| DELETE | /tasks/<int:task_id> | routes/task_routes.py:225 |
| GET | /tasks/search | routes/task_routes.py:240 |
| GET | /tasks/stats | routes/task_routes.py:273 |
| GET | /users | routes/user_routes.py:10 |
| GET | /users/<int:user_id> | routes/user_routes.py:27 |
| POST | /users | routes/user_routes.py:42 |
| PUT | /users/<int:user_id> | routes/user_routes.py:92 |
| DELETE | /users/<int:user_id> | routes/user_routes.py:134 |
| GET | /users/<int:user_id>/tasks | routes/user_routes.py:153 |
| POST | /login | routes/user_routes.py:185 |
| GET | /reports/summary | routes/report_routes.py:12 |
| GET | /reports/user/<int:user_id> | routes/report_routes.py:103 |
| GET | /categories | routes/report_routes.py:157 |
| POST | /categories | routes/report_routes.py:167 |
| PUT | /categories/<int:cat_id> | routes/report_routes.py:190 |
| DELETE | /categories/<int:cat_id> | routes/report_routes.py:211 |

> **Nota de execução (2026-11-27, Fase 3):** os caminhos citados nas Recommendations foram materializados sob `src/`, conforme a árvore-alvo de `mvc-guidelines.md`: `config/` → `src/config/`, `controllers/` → `src/controllers/`, `models/constants.py` → `src/models/constants.py`, `middlewares/` → `src/middlewares/`, `services/` → `src/services/`. A camada view citada como `routes/` (AP-07) ficou em `src/views/` (incluindo `src/views/category_routes.py`). Nenhuma Recommendation teve escopo reduzido; os paths HTTP são os mesmos.

Catalog entries evaluated and not applicable: AP-02 (ORM only; `like(f'%{query}%')` is a bound parameter), AP-03 (no single file mixes DB schema + routing + integrations; the route-level mix is AP-07), AP-09 (`self.notifications` is instance state of a never-instantiated class, not a shared singleton — covered by AP-18), AP-10 (deletes run in one commit with rollback; SQLAlchemy nullifies `tasks.category_id` when a category is deleted), AP-11 (no async callbacks in Python).

================================
Total: 18 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
