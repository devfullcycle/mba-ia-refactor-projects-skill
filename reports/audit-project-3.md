================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (SQLite via Flask-SQLAlchemy 3.1.1 / SQLAlchemy 2.1.9)
Files:   15 analyzed | ~1158 lines of code
Architecture: Partially layered — `models/`, `routes/`, `services/`, `utils/` existem, mas as rotas concentram queries e regras de negócio, a configuração está hardcoded em `app.py`, services/helpers não são usados e não há tratamento de erros centralizado

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 6 | LOW: 5

> Correção (Phase 3, baseline): o achado AP-10 (integridade referencial em `DELETE /categories/<id>`) foi removido. A execução mostrou que o backref `Category.tasks` do SQLAlchemy anula `category_id` das tasks ao excluir a categoria (`GET /tasks/4` → `category_id: null`), portanto não há FK órfã. `DELETE /users/<id>` também é atômico (tasks e usuário no mesmo commit).

## Findings

### [CRITICAL] AP-04 Unprotected administrative / destructive endpoints
File: routes/user_routes.py:52, 71-72, 119-122, 134-151, 185-211, routes/task_routes.py:225-238, routes/report_routes.py:211-223
Description: Nenhuma rota verifica identidade ou papel. `POST /users` aceita `role` vindo do corpo (`data.get('role', 'user')`, aceitando `'admin'`), `PUT /users/<id>` permite trocar `role` e `active` de qualquer usuário, e `DELETE /users/<id>` apaga o usuário **e todas as suas tasks** (linhas 140-142) sem qualquer guarda. O `token` retornado pelo login (`'fake-jwt-token-' + str(user.id)`) nunca é validado em nenhuma rota.
Impact: Qualquer cliente anônimo pode se autopromover a `admin`, desativar outros usuários ou apagar usuários, tasks e categorias em massa.
Recommendation: Emitir token assinado no login e criar decorator `require_auth`/`require_role('admin')` aplicado às operações de escrita sensíveis (criação de admin, troca de role, DELETE de usuário); impedir auto-atribuição de `role='admin'` por chamada anônima. (T-17)

### [CRITICAL] AP-06 Sensitive data exposure (password hash in responses)
File: models/user.py:21, routes/user_routes.py:33, 85, 129, 209
Description: `User.to_dict()` inclui `'password': self.password`, e esse dicionário é devolvido por `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`. Confirmado em execução: `GET /users/1` retorna `password = '81dc9b****'` (MD5 de `'1234'`).
Impact: Qualquer cliente obtém os hashes de senha; combinados com MD5 sem salt (AP-05), as senhas são recuperadas instantaneamente via rainbow tables.
Recommendation: Remover `password` da serialização pública (`to_dict`) e nunca retorná-lo em nenhuma resposta. (T-10)

### [CRITICAL] AP-05 Insecure password storage (MD5 without salt)
File: models/user.py:27-32
Description: `set_password` usa `hashlib.md5(pwd.encode()).hexdigest()` e `check_password` compara com o mesmo hash, sem salt e sem fator de custo. A política de senha mínima é de 4 caracteres (`routes/user_routes.py:64`).
Impact: Um vazamento do banco (ou da API, ver AP-06) expõe todas as senhas; MD5 é quebrado em segundos.
Recommendation: Usar `werkzeug.security.generate_password_hash`/`check_password_hash` (PBKDF2/scrypt com salt, já disponível via Flask), com verificação compatível para hashes MD5 legados no login. (T-09)

### [CRITICAL] AP-01 Hardcoded secrets and credentials
File: app.py:13, services/notification_service.py:7-10
Description: `app.config['SECRET_KEY'] = 'super-secret-****'` literal; `NotificationService` define `email_user = 'taskmanager@****'` e `email_password = 'senha****'` (SMTP `smtp.gmail.com:587`) diretamente no código.
Impact: Qualquer pessoa com acesso ao repositório obtém o segredo de sessão e as credenciais SMTP; impossível rotacionar por ambiente.
Recommendation: Ler `SECRET_KEY`, `DATABASE_URL` e `SMTP_*` de variáveis de ambiente em `config/settings.py` (com `.env.example`); gerar chave aleatória apenas em desenvolvimento. (T-01)

### [HIGH] AP-12 Insecure configuration hardcoded for production
File: app.py:15, 34, routes/user_routes.py:210
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` liga o debugger Werkzeug em todas as interfaces; `CORS(app)` libera qualquer origem; login devolve token falso `'fake-jwt-token-' + str(user.id)` (previsível e nunca verificado).
Impact: Debugger exposto na rede permite execução remota de código; CORS aberto + token falso = nenhum controle de acesso real.
Recommendation: `DEBUG`, `HOST`, `PORT` e `CORS_ORIGINS` vindos de config com default seguro (`debug` desligado); token assinado com `itsdangerous` (já dependência do Flask). (T-01, T-17)

### [HIGH] AP-07 Business logic in route handlers (Fat routes)
File: routes/task_routes.py:11-63, 85-154, 156-223, 273-299, routes/user_routes.py:42-90, 92-132, 153-183, routes/report_routes.py:12-101, 103-155
Description: Handlers de 50-90 linhas fazem parsing, validação, consultas `Model.query`, regras de negócio (cálculo de atraso, taxa de conclusão, mapeamento de prioridade `critical/high/...`, contagem por status) e persistência com `db.session.commit()` no mesmo corpo. Ex.: `summary_report` (90 linhas) agrega 15+ consultas e monta o relatório na própria rota.
Impact: Regras não podem ser reutilizadas nem testadas sem HTTP; qualquer mudança exige editar várias rotas.
Recommendation: Criar `controllers/` (task, user, category, report) com as regras; rotas apenas leem a requisição, chamam o controller e formatam a resposta. (T-04)

### [HIGH] AP-08 Tight coupling / no composition root
File: app.py:9-31, routes/task_routes.py:2, routes/user_routes.py:2, routes/report_routes.py:2, services/notification_service.py:15, seed.py:2
Description: `app = Flask(__name__)` é criado no import com configuração, CORS, registro de blueprints e `db.create_all()` como efeitos colaterais — não há app factory. Todas as rotas importam o singleton `from database import db` e operam a sessão diretamente; `NotificationService.send_email` instancia `smtplib.SMTP(...)` internamente; `seed.py` importa `app` do módulo de entrada.
Impact: Impossível criar uma instância de teste com outro banco/config; integrações não podem ser substituídas por fakes (violação de DIP).
Recommendation: `create_app(config)` como composition root que liga config → DB → models → controllers → rotas; services recebem configuração por injeção. (T-05)

### [MEDIUM] AP-14 Missing or duplicated input validation
File: routes/task_routes.py:96-99, 113, 166-171, 182, 260-264, routes/user_routes.py:102-103, 124-125, routes/report_routes.py:196-202, utils/helpers.py:19-23, 57-108
Description: Campos usados sem checar tipo: `priority < 1` com `priority='high'` → `TypeError`; `len(title)` com `title=12345` → `TypeError`; `int(request.args['priority'])` em `/tasks/search?priority=abc` → `ValueError`; `update_category` faz `'name' in data` sem checar `data is None`. Todos confirmados retornando **HTTP 500**. `PUT /users` aceita `name` vazio e `active` de qualquer tipo. As mesmas validações estão copiadas em create/update, enquanto `process_task_data` e `validate_email` em `utils/helpers.py` existem e nunca são usadas.
Impact: Entradas inválidas geram 500 em vez de 400; regras divergem entre criação e atualização.
Recommendation: Centralizar validadores (`validators.py`) reutilizados por create/update, com checagem de tipo e retorno 400 padronizado. (T-14)

### [MEDIUM] AP-16 Inconsistent / absent error handling
File: routes/task_routes.py:13, 62-63, 137, 151-154, 204, 221-223, 236, routes/user_routes.py:87-90, 130, 149, routes/report_routes.py:186, 207, 221, utils/helpers.py:46, 49, 88, services/notification_service.py:23, app.py:9-34
Description: 15 blocos `except:` / `except Exception` espalhados; `get_tasks` envolve todo o handler em `try/except:` que engole qualquer erro e devolve `'Erro interno'`. Não há `@app.errorhandler`: 404/405/500 do framework retornam HTML (`text/html`, confirmado em `GET /nope`), enquanto as rotas retornam JSON `{'error': ...}`. Mensagens divergem para a mesma regra (`'Formato de data inválido. Use YYYY-MM-DD'` vs `'Formato de data inválido'`; `'Senha deve ter no mínimo 4 caracteres'` vs `'Senha muito curta'`).
Impact: Clientes não podem confiar no formato de erro; falhas reais ficam ocultas.
Recommendation: Exceções de domínio (`NotFoundError`, `ValidationError`, `ConflictError`) + error handler central que sempre devolve JSON `{'error': ...}`; remover `except:` genéricos. (T-07)

### [MEDIUM] AP-13 N+1 queries
File: routes/task_routes.py:41-57, 275-281, routes/user_routes.py:22, routes/report_routes.py:15-30, 53-56, 159-163
Description: `get_tasks` faz `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` dentro do loop (2 queries por task); `get_users` acessa `len(u.tasks)` (lazy load por usuário); `summary_report` executa 12 `count()` separados + `Task.query.filter_by(user_id=u.id)` por usuário; `get_categories` faz um `count()` por categoria; `task_stats` faz 5 `count()` + `Task.query.all()`.
Impact: Tempo de resposta e carga no banco crescem linearmente com o volume de dados.
Recommendation: `joinedload`/`selectinload` para user/category e agregações com `GROUP BY` (`func.count` por status/prioridade/usuário/categoria). (T-08)

### [MEDIUM] AP-15 Code duplication (DRY violations)
File: routes/task_routes.py:17-39, 71-80, 110, 177, 284-287, 296, routes/user_routes.py:61, 71, 106, 120, 162-180, routes/report_routes.py:34-36, 67, 132-135, 151, models/task.py:23-60, utils/helpers.py:21, 75, 110-111
Description: A regra "task atrasada" (`due_date < utcnow()` e status ≠ `done`/`cancelled`) está reimplementada em 6 lugares, embora `Task.is_overdue()` exista e não seja usada. A serialização de task é refeita manualmente em `get_tasks` e `get_user_tasks` em vez de `to_dict()`. A lista de status aparece em 5 lugares, a de roles em 3 e a regex de email em 3. A fórmula de taxa de conclusão é repetida 3 vezes enquanto `calculate_percentage` é importada e não usada.
Impact: As regras divergem com o tempo; uma correção precisa ser aplicada N vezes.
Recommendation: Constantes únicas de domínio, regra `is_overdue` no model e serialização única no model/view. (T-15, T-04)

### [MEDIUM] AP-17 Deprecated / legacy APIs
File: models/task.py:15-16, 52, models/user.py:14, models/category.py:11, routes/task_routes.py:31, 42, 51, 67, 72, 117, 122, 158, 188, 195, 215, 227, 285, routes/user_routes.py:29, 94, 136, 155, 172, routes/report_routes.py:35, 42, 45, 71, 105, 133, 192, 213, services/notification_service.py:35, utils/helpers.py:38, seed.py:66-74
Description: `datetime.utcnow()` (deprecado no Python ≥ 3.12; runtime local 3.14) e `Model.query.get(id)` (legado no SQLAlchemy 2.x; instalado 2.1.9). Confirmado com `python -W default`: `DeprecationWarning: datetime.datetime.utcnow() is deprecated` e `LegacyAPIWarning: The Query.get() method is considered legacy`.
Impact: Quebrará em upgrades futuros e já polui os logs com avisos.
Recommendation: Helper `utcnow()` baseado em `datetime.now(timezone.utc)` (gravando naive-UTC para manter o formato atual das datas) e `db.session.get(Model, id)`. (T-13)

### [MEDIUM] AP-18 Side effects and infrastructure in the wrong place
File: app.py:30-31, seed.py:2, 8-14
Description: `db.create_all()` roda no import de `app.py`, portanto qualquer `import app` (inclusive `seed.py` e testes) cria/toca o banco. `seed.py` depende do módulo de entrada (`from app import app, db`) em vez de uma factory.
Impact: Efeitos colaterais ocultos no import; impossível importar a aplicação sem tocar no banco.
Recommendation: Mover `create_all()` para dentro de `create_app()` e fazer o seed usar a factory. (T-05)

### [LOW] AP-21 Unused imports, variables and dead code
File: app.py:7, models/task.py:3, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, utils/helpers.py:3-7, 9-108, 110-116, services/notification_service.py:1-48, models/task.py:38-60, models/user.py:34-38, requirements.txt:4-6
Description: Imports sem uso: `os, sys, json` (app.py), `json` (models/task.py), `json, os, sys, time` (task_routes), `hashlib, json` (user_routes), `format_date, calculate_percentage, json` (report_routes), `os, json, sys, math, hashlib` (helpers). Nunca chamados: todas as funções e constantes de `utils/helpers.py`, `NotificationService` inteiro, `Task.validate_status/validate_priority/is_overdue`, `User.is_admin`; parâmetro `existing_task` sem uso. `marshmallow`, `requests` e `python-dotenv` declarados em requirements e nunca importados.
Impact: Ruído, dependências enganosas e código que aparenta estar em uso.
Recommendation: Remover imports/código mortos e reaproveitar o que for útil na nova camada (constantes, `is_overdue`). (T-16)

### [LOW] AP-22 `print` used as logging
File: routes/task_routes.py:149, 153, 219, 234, routes/user_routes.py:83, 89, 147, services/notification_service.py:21, 24, utils/helpers.py:39, 41
Description: Eventos operacionais e erros registrados com `print(f"Task criada: ...")`, `print(f"ERRO: {str(e)}")`.
Impact: Sem nível, sem estrutura, impossível silenciar ou direcionar para um coletor.
Recommendation: `logging.getLogger(__name__)` com níveis `info`/`exception`. (T-16)

### [LOW] AP-19 Magic numbers and magic strings
File: routes/task_routes.py:96, 99, 104, 110, 113, routes/user_routes.py:64, 71, 115, routes/report_routes.py:24-28, 45, 129, 180, app.py:34
Description: Limites literais (`len(title) < 3`, `> 200`, `len(password) < 4`, `priority <= 2` como "alta prioridade", `timedelta(days=7)`), prioridades `1..5` mapeadas a `'critical'...'minimal'` inline, cor `'#000000'`, porta `5000` e strings de status repetidas — embora `utils/helpers.py:110-116` já defina `VALID_STATUSES`, `MIN_TITLE_LENGTH` etc. sem uso.
Impact: Significado oculto; alterar uma regra exige caçar literais.
Recommendation: Módulo de constantes de domínio reutilizado por models/controllers. (T-15)

### [LOW] AP-23 Verbose conditionals and non-idiomatic code
File: models/task.py:38-60, models/user.py:34-38, routes/task_routes.py:30-39, 141, 210, 268-269, routes/report_routes.py:57-61, 119-135, utils/helpers.py:21-23, 53-55, 103
Description: `if cond: return True else: return False`; pirâmides de 3 níveis de `if` para um único booleano (`is_overdue`); `type(tags) == list` em vez de `isinstance`; loops manuais de contagem onde `sum(...)`/list comprehension servem.
Impact: Legibilidade.
Recommendation: Expressões booleanas diretas, `isinstance`, comprehensions. (T-16)

### [LOW] AP-20 Poor naming
File: routes/report_routes.py:10, 157-223, 24-28, routes/task_routes.py:15, 268, routes/user_routes.py:14, models/task.py:45
Description: `report_routes.py` / `report_bp` hospedam o CRUD de categorias (nome enganoso); variáveis de uma/duas letras `t`, `u`, `c`, `p`, `p1..p5`, `cat`.
Impact: Dificulta localizar funcionalidades e entender a intenção.
Recommendation: Separar `category_routes`; nomes descritivos internamente (sem alterar campos públicos). (T-16)

## Deprecated APIs
| Location | Deprecated API | Modern replacement |
|---|---|---|
| models/task.py:15-16, models/user.py:14, models/category.py:11 | `default=datetime.utcnow` | callable baseado em `datetime.now(timezone.utc)` |
| models/task.py:52, routes/task_routes.py:31, 72, 215, 285, routes/user_routes.py:172, routes/report_routes.py:35, 42, 45, 71, 133, services/notification_service.py:35, utils/helpers.py:38, seed.py:66-74 | `datetime.utcnow()` | `datetime.now(timezone.utc)` |
| routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227, routes/user_routes.py:29, 94, 136, 155, routes/report_routes.py:105, 192, 213 | `Model.query.get(id)` | `db.session.get(Model, id)` |

## Endpoint contract (to preserve in Phase 3)
| Method | Path | Handler |
|---|---|---|
| GET | / | app.py:26 |
| GET | /health | app.py:22 |
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

================================
Total: 18 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
