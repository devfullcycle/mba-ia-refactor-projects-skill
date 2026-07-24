```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.9+ (venv local: 3.9.5)
Framework:     Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.0.51 resolvido)
Dependencies:  flask-cors 4.0.0 (usada); marshmallow 3.20.1, requests 2.31.0 e
               python-dotenv 1.0.0 declaradas no requirements.txt e nunca importadas
Domain:        Task Manager — tarefas com status/prioridade/prazo, usuários, categorias e
               relatórios de produtividade por usuário
Architecture:  Parcialmente organizada. Existem `models/`, `routes/`, `services/` e `utils/`,
               mas **não existe camada de controller**: validação, regra de negócio e
               serialização vivem dentro dos handlers de rota (o maior tem 90 linhas).
               `services/` e a maior parte de `utils/` são código morto — 19 símbolos
               definidos e nunca chamados. Config inline no entry point, sem middlewares.
Source files:  15 files analyzed | ~1.158 lines of code
Entry point:   app.py:33 (`app.run(debug=True, host='0.0.0.0')`); `db.create_all()` executado
               em tempo de import (app.py:30-31)
Routes:        22 endpoints (task_routes 7, user_routes 7, report_routes 6, app.py 2)
DB tables:     tasks, users, categories (models SQLAlchemy; `sqlite:///tasks.db`)
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
```

Project: task-manager-api
Stack:   Python + Flask 3.0.0 + SQLAlchemy 2.0.51
Files:   15 analyzed | ~1.158 lines of code
Date:    2026-07-24

## Summary

CRITICAL: 3 | HIGH: 4 | MEDIUM: 7 | LOW: 8

| Camada MVC | Situação |
|---|---|
| Config | **Ausente** — configuração e segredo inline em `app.py:11-13` |
| Models | **Existe** — `models/` com SQLAlchemy, mas com regra de negócio nunca usada e senha no serializador |
| Views/Routes | **Existe e está sobrecarregada** — blueprints contêm validação, regra e serialização |
| Controllers | **Ausente** — a rota é o controller; nenhum arquivo de controller no projeto |
| Middlewares | **Ausente** — nenhum `errorhandler`, nenhuma autenticação |
| Services | **Fantasma** — `NotificationService` definido (48 linhas) e nunca instanciado |
| Entry point | **Sobrecarregado** — config, segredo, CORS, blueprints e `create_all()` no import |

## Findings

### 1. [CRITICAL] Senhas com MD5 sem Salt (AP-05)
File: models/user.py:29, 32
Description: `set_password` usa `hashlib.md5(pwd.encode()).hexdigest()` (linha 29) e
             `check_password` compara o digest MD5 (linha 32). Não há salt nem KDF.
Impact: MD5 é quebrado para senhas — bilhões de tentativas por segundo em GPU e rainbow
        tables públicas. Sem salt, dois usuários com a mesma senha têm o mesmo hash, o que
        entrega a informação de reuso. As senhas do seed (`1234`, `abcd`, `pass`,
        seed.py:18-35) são recuperáveis instantaneamente.
Recommendation: Migrar para `werkzeug.security.generate_password_hash` (scrypt) ou
                bcrypt/argon2, com coluna dimensionada para o novo formato — padrão RP-04.

### 2. [CRITICAL] Hash de Senha Exposto em Toda Resposta da API (AP-03)
File: models/user.py:21; propagado por routes/user_routes.py:33, 85, 209
Description: `User.to_dict()` inclui `'password': self.password` (linha 21). O método é usado
             em `GET /users/<id>` (user_routes.py:33), `POST /users` (85) e na resposta de
             `POST /login` (209).
Impact: Qualquer consumidor da API coleta a base de hashes MD5 dos usuários. Combinado com o
        finding 1, equivale a publicar as senhas — confirmado no baseline, onde
        `POST /login` devolveu o hash do usuário autenticado.
Recommendation: Remover o campo do serializador e manter um único ponto de saída pública da
                entidade; se algum consumidor interno precisar do hash, expor método separado
                que não é usado em resposta HTTP — padrão RP-04, RP-16.

### 3. [CRITICAL] Segredos Hardcoded (aplicação e SMTP) (AP-02)
File: app.py:13, services/notification_service.py:7-10
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` (app.py:13) e credenciais
             SMTP literais em `NotificationService.__init__` — `email_host`, `email_port`,
             `email_user = 'taskmanager@gmail.com'`, `email_password = 'senha123'`
             (notification_service.py:7-10).
Impact: Segredo de sessão e credencial de e-mail versionados no Git; ambos precisam de
        rotação. `python-dotenv` está no `requirements.txt`, o que indica que a intenção
        original era configuração por ambiente — nunca implementada.
Recommendation: Módulo `config/` lendo `os.environ` (com `.env.example`), falha explícita no
                boot sem `SECRET_KEY` em produção — padrão RP-02.

### 4. [HIGH] Fat Routes — Regra de Negócio na Camada de Apresentação (AP-07)
File: routes/task_routes.py:85-154 (70 linhas), 156-223 (68 linhas); routes/report_routes.py:12-101 (90 linhas); routes/user_routes.py:42-90
Description: `create_task` e `update_task` fazem validação (task_routes.py:89-124, 166-213),
             montagem da entidade e persistência no mesmo handler. `summary_report` executa 15
             queries, calcula atrasos, agrega produtividade por usuário e monta o payload em
             uma única função de 90 linhas.
Impact: Nenhuma dessas regras pode ser exercitada sem cliente HTTP; a mesma regra é reescrita
        em cada endpoint que precisa dela (ver findings 5 e 9). É a violação central de MVC
        neste projeto: a estrutura de pastas sugere camadas que o código não tem.
Recommendation: Introduzir `controllers/` por agregado (task, user, category, report), com as
                rotas apenas mapeando caminho → controller — padrão RP-05.

### 5. [HIGH] Camada Fantasma — 19 Símbolos Definidos e Nunca Usados (AP-13, AP-22)
File: services/notification_service.py:4-48; utils/helpers.py:19-116; models/task.py:38-60; models/user.py:34-38
Description: Verificação de uso em todo o código do projeto (excluindo `.venv`) mostra apenas
             a definição, sem nenhuma chamada, para: `NotificationService` (e seus 4 métodos),
             `process_task_data`, `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`,
             `MIN_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`, `DEFAULT_PRIORITY`, `DEFAULT_COLOR`,
             `Task.is_overdue`, `Task.validate_status`, `Task.validate_priority`,
             `User.is_admin`, `validate_email`, `sanitize_string`, `generate_id`,
             `log_action`, `is_valid_color`. `format_date` e `calculate_percentage` são
             importados em report_routes.py:7 e nunca chamados.
Impact: O pior cenário de manutenção: existem duas versões de cada regra — a "oficial" em
        `utils/`/`models/` e a inline nas rotas — e elas já divergem (ex.: `process_task_data`
        aceita data em `%d/%m/%Y` via `parse_date`, as rotas só aceitam `%Y-%m-%d`).
        A estrutura de diretórios passa uma impressão de organização que o código não sustenta.
Recommendation: Decidir qual implementação é a boa, usá-la a partir dos controllers e apagar a
                outra — nunca manter as duas — padrão RP-05, RP-11, RP-16.

### 6. [HIGH] Configuração, Schema e Bootstrap Acoplados no Entry Point (AP-11, AP-01)
File: app.py:9-31
Description: Config inline (linhas 11-13), `CORS(app)` sem restrição (15), registro de
             blueprints (18-20), duas rotas declaradas inline (22-28) e
             `with app.app_context(): db.create_all()` executado em tempo de **import**
             (30-31). `app.run(debug=True, host='0.0.0.0')` na linha 34.
Impact: Importar `app` — como `seed.py:2` faz — cria o banco como efeito colateral. Não há
        application factory, então não é possível instanciar a aplicação com configuração de
        teste. O debugger do Werkzeug fica ativo e acessível na rede.
Recommendation: `create_app(config)` com config por ambiente, `db.create_all()` em CLI/factory
                explícito e debug vindo de variável de ambiente — padrão RP-02, RP-06.

### 7. [HIGH] Autenticação Fake e Nenhuma Rota Protegida (AP-06, AP-05)
File: routes/user_routes.py:207-211
Description: O login devolve `'token': 'fake-jwt-token-' + str(user.id)` (linha 210) — token
             previsível, não assinado e nunca verificado em nenhum lugar. Busca por
             `login_required|jwt|authenticate|Authorization` no projeto não retorna nenhuma
             ocorrência além dessa linha.
Impact: `DELETE /users/<id>`, `PUT /users/<id>`, `/reports/*` e todo o CRUD de tarefas estão
        abertos a qualquer cliente. Como o token é derivado do id, ele é forjável mesmo se
        passasse a ser verificado.
Recommendation: Emitir token assinado (JWT com segredo do ambiente) e proteger as rotas de
                escrita e de relatório com middleware que nega por default — padrão RP-14.

### 8. [MEDIUM] N+1 Queries em Quatro Endpoints (AP-14)
File: routes/task_routes.py:41-57; routes/user_routes.py:22; routes/report_routes.py:53-68, 157-165
Description: `GET /tasks` executa `User.query.get` e `Category.query.get` por tarefa
             (task_routes.py:42, 51). `GET /users` usa `len(u.tasks)` (user_routes.py:22),
             disparando lazy load por usuário. `summary_report` consulta as tarefas de cada
             usuário dentro do laço (report_routes.py:56). `GET /categories` faz um `count()`
             por categoria (report_routes.py:163).
Impact: `GET /tasks` com 100 tarefas executa ~201 queries; `/reports/summary` cresce com o
        número de usuários. Todos os quatro casos são resolvíveis com `joinedload` ou
        `GROUP BY`.
Recommendation: `selectinload`/`joinedload` para as relações e agregação em SQL
                (`func.count` + `group_by`) — padrão RP-10.

### 9. [MEDIUM] Regra de "Tarefa Atrasada" Duplicada em 6 Lugares (AP-16)
File: models/task.py:50-60 (implementação correta, nunca chamada); routes/task_routes.py:30-39, 71-80, 283-287; routes/user_routes.py:171-180; routes/report_routes.py:33-43, 132-135
Description: O model já define `Task.is_overdue()`, mas as rotas reimplementam a condição
             `due_date < utcnow() and status not in ('done','cancelled')` em seis blocos
             `if/else` aninhados.
Impact: Mudar a definição de atraso (ex.: passar a considerar fuso ou incluir o status
        `blocked`) exige seis edições sincronizadas — e uma delas já difere: `task_stats`
        (task_routes.py:283-287) não trata `due_date` nulo da mesma forma que `get_tasks`.
Recommendation: Chamar `Task.is_overdue()` a partir de `to_dict()` e dos controllers, apagando
                as cópias inline — padrão RP-05, RP-11.

### 10. [MEDIUM] `except:` Nu Engolindo Exceções, sem Handler Central (AP-15)
File: routes/task_routes.py:62, 137, 204, 236; routes/user_routes.py:130, 149; routes/report_routes.py:186, 207, 221; utils/helpers.py:46, 49, 88 (12 ocorrências)
Description: `except:` sem tipo captura tudo — inclusive `KeyboardInterrupt` e `SystemExit` —
             e devolve mensagem genérica (`{'error': 'Erro interno'}`, 500). Não existe
             `@app.errorhandler` em nenhum arquivo.
Impact: O stacktrace é descartado: uma falha de integridade no banco aparece ao cliente como
        500 sem nenhum registro do motivo. Em `helpers.py:46-50` o `except` aninhado esconde
        até erro de formato de data.
Recommendation: Exceções de domínio + `register_error_handlers` no factory; `except` sempre
                tipado, com log do stacktrace — padrão RP-08.

### 11. [MEDIUM] Validação Duplicada e Divergente (AP-18, AP-16)
File: routes/task_routes.py:96-124 vs 166-213 vs utils/helpers.py:57-108; routes/user_routes.py:61, 106 vs utils/helpers.py:21; routes/user_routes.py:64, 115
Description: A lista de status válidos aparece em task_routes.py:110, 177 e helpers.py:75, 110;
             os limites de título em task_routes.py:96-100, 167-170 e helpers.py:64, 112-113;
             os roles em user_routes.py:71, 120 e helpers.py:111; a regex de e-mail em
             user_routes.py:61, 106 e helpers.py:21. O update de tarefa não revalida
             `user_id`/`category_id` com o mesmo rigor do create.
Impact: Quatro definições da mesma regra, com divergências reais: `POST /tasks` valida
        `priority` como inteiro entre 1 e 5, mas `PUT /tasks/<id>` compara sem converter tipo
        (task_routes.py:182), então `"priority": "abc"` levanta `TypeError` → 500.
Recommendation: Um validador por agregado, usado por create e update, com as constantes que já
                existem em `utils/helpers.py` — padrão RP-11.

### 12. [MEDIUM] Blueprint Mal Delimitado — CRUD de Categorias em `report_routes` (AP-01)
File: routes/report_routes.py:157-223
Description: Quatro rotas de `/categories` (GET, POST, PUT, DELETE) estão registradas no
             blueprint `reports`, junto com os relatórios.
Impact: Quem procura o CRUD de categoria em `routes/` não o encontra por nome de arquivo; o
        blueprint acumula dois domínios não relacionados.
Recommendation: Blueprint próprio (`category_routes.py`) com controller correspondente —
                padrão RP-01.

### 13. [MEDIUM] Regex de E-mail Aceita Endereço sem TLD (AP-18)
File: routes/user_routes.py:61, 106; utils/helpers.py:21
Description: `^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$` valida `a@b` como e-mail válido — não exige
             ponto no domínio.
Impact: Cadastro de e-mail inválido que nunca receberá notificação; e o dado entra na coluna
        `unique`, ocupando o endereço.
Recommendation: Exigir TLD na regex e centralizar a validação em um único ponto — padrão RP-11.

### 14. [MEDIUM] Deleção Manual em Cascata em vez de Cascade no Relacionamento (AP-10)
File: routes/user_routes.py:140-142; models/task.py:20-21
Description: `delete_user` percorre as tarefas do usuário e as remove uma a uma antes de
             remover o usuário; o `relationship` em `models/task.py:20-21` não declara
             `cascade`. As duas remoções ocorrem sem transação explícita — só o `commit`
             final (linha 146).
Impact: Qualquer novo ponto de deleção precisa repetir o laço, ou deixa tarefas órfãs
        apontando para um `user_id` inexistente. Falha entre as remoções deixa estado parcial.
Recommendation: `cascade="all, delete-orphan"` no relacionamento (ou FK com `ondelete`),
                deleção em uma transação — padrão RP-07.

### 15. [LOW] API Deprecated — `datetime.utcnow()` em 18 Ocorrências (AP-17)
File: models/task.py:15, 16, 52; models/user.py:14; routes/task_routes.py:31, 72, 215, 285; routes/report_routes.py:35, 42, 45, 71, 133; routes/user_routes.py:172; utils/helpers.py:38; services/notification_service.py:35; seed.py:66, 67, 69, 70, 74
Description: `datetime.utcnow()` está deprecada desde Python 3.12 e devolve datetime *naive*
             (sem fuso).
Impact: Emite `DeprecationWarning` a partir do 3.12 e será removida; além disso, comparar
        naive com aware levanta `TypeError`, então a migração precisa ser feita de uma vez em
        todo o fluxo de datas.
Recommendation: `datetime.now(timezone.utc)` com convenção única de fuso no projeto —
                padrão RP-15.

### 16. [LOW] API Deprecated — Legacy Query API do SQLAlchemy em 16 Ocorrências (AP-17)
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 191, 213; seed.py:94-96
Description: `Model.query.get(pk)` é legado desde SQLAlchemy 1.4 e emite `LegacyAPIWarning` no
             2.0 (versão instalada: 2.0.51). O padrão `Model.query` em geral (57 ocorrências)
             também é a API legada.
Impact: Confirmado em runtime nesta instalação:
        `LegacyAPIWarning: The Query.get() method is considered legacy as of the 1.x series of
        SQLAlchemy and becomes a legacy construct in 2.0. (deprecated since: 2.0)`.
Recommendation: `db.session.get(Model, pk)` e `db.session.execute(select(...))` — padrão RP-15.

### 17. [LOW] Imports Não Utilizados e Dependências Declaradas sem Uso (AP-22)
File: app.py:7; routes/task_routes.py:7; routes/user_routes.py:6; routes/report_routes.py:7-8; utils/helpers.py:3-7; models/task.py:3; requirements.txt
Description: `os, sys, json` em app.py:7; `json, os, sys, time` em task_routes.py:7;
             `hashlib, json` em user_routes.py:6; `format_date`, `calculate_percentage` e
             `json` em report_routes.py:7-8; `os, json, sys, math, hashlib` em helpers.py:3-7;
             `json` em models/task.py:3. No `requirements.txt`, `marshmallow`, `requests` e
             `python-dotenv` não são importados em nenhum arquivo do projeto.
Impact: Sugere dependências e integrações que não existem; aumenta a superfície de instalação
        sem retorno.
Recommendation: Remover imports e dependências não usados — ou usar `marshmallow` para
                resolver o finding 11 e `python-dotenv` para o finding 3 — padrão RP-16.

### 18. [LOW] `type(x) == list` em vez de `isinstance` (AP-23)
File: routes/task_routes.py:141, 210; utils/helpers.py:103
Description: Comparação direta de tipo, que falha para subclasses de `list`.
Recommendation: `isinstance(x, list)` — padrão RP-16.

### 19. [LOW] Magic Numbers com Constantes Equivalentes Ignoradas (AP-20)
File: routes/task_routes.py:96, 99, 113, 182; routes/user_routes.py:64, 115; routes/report_routes.py:45, 129; utils/helpers.py:110-116
Description: `3`/`200` (título), `1`/`5` (prioridade), `4` (tamanho mínimo de senha), `7`
             (janela do relatório), `priority <= 2` como "alta prioridade" — todos literais,
             enquanto `MIN_TITLE_LENGTH`, `MAX_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH` e
             `DEFAULT_PRIORITY` já existem em `utils/helpers.py:110-116` e nunca são usados.
Impact: O limite de senha (4 caracteres) é fraco e está espalhado; mudar exige achar todos.
Recommendation: Importar as constantes existentes e nomear as que faltam — padrão RP-13.

### 20. [LOW] `if/else` Retornando Booleano Literal (AP-23)
File: models/task.py:38-48, 50-60; models/user.py:34-38; utils/helpers.py:19-23, 52-55
Description: Blocos como `if new_status in valid: return True else: return False`, onde a
             própria expressão já é o valor de retorno.
Recommendation: `return new_status in VALID_STATUSES` — padrão RP-16.

### 21. [LOW] `print()` como Estratégia de Log em 21 Ocorrências (AP-19)
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; utils/helpers.py:39, 41; seed.py:93-96
Description: Diagnóstico por `print`, incluindo mensagens de erro (`print(f"Erro ao criar
             task: {str(e)}")`, task_routes.py:153). Nenhum `import logging` no projeto.
Impact: Sem nível, timestamp ou destino configurável; o erro real fica só no stdout, enquanto o
        cliente recebe 500 genérico (finding 10).
Recommendation: `logging` configurado por `LOG_LEVEL`, logger por módulo — padrão RP-12.

### 22. [LOW] Nomes de Variáveis Pobres (AP-21)
File: routes/task_routes.py:16, 268, 283; routes/user_routes.py:14, 141, 161; routes/report_routes.py:24-28, 33, 55, 59, 119, 161
Description: `t`, `u`, `c`, `cat`, `p` fora de laços triviais e `p1`..`p5` como contadores por
             prioridade (report_routes.py:24-28), que depois são mapeados para nomes de
             negócio no payload (`critical`, `high`, `medium`, `low`, `minimal`).
Impact: A relação entre `p1` e "critical" só existe na cabeça de quem escreveu.
Recommendation: Nomes do domínio e agregação por dicionário de prioridade — padrão RP-13.

## Deprecated APIs

Verificação executada: (a) busca pelos símbolos deprecated de Python, Flask e SQLAlchemy do
catálogo; (b) execução de código do projeto com `warnings.simplefilter("always")` para
capturar avisos de runtime.

| API | Arquivo:linha | Substituto | Removida em |
|---|---|---|---|
| `datetime.utcnow()` | models/task.py:15, 16, 52; models/user.py:14; routes/task_routes.py:31, 72, 215, 285; routes/report_routes.py:35, 42, 45, 71, 133; routes/user_routes.py:172; utils/helpers.py:38; services/notification_service.py:35; seed.py:66, 67, 69, 70, 74 | `datetime.now(timezone.utc)` | deprecada no 3.12, remoção futura |
| `Model.query.get()` | routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 191, 213; seed.py:94-96 | `db.session.get(Model, pk)` | legado desde 1.4; `deprecated since 2.0` |
| `Model.query` (Legacy Query API) | 57 ocorrências em routes/ e seed.py | `db.session.execute(select(...))` | legado desde 1.4 |

Evidência de runtime capturada nesta instalação (SQLAlchemy 2.0.51):

```
LegacyAPIWarning: The Query.get() method is considered legacy as of the 1.x series of
SQLAlchemy and becomes a legacy construct in 2.0. The method is now available as
Session.get() (deprecated since: 2.0)
```

Observação sobre `utcnow()`: no Python 3.9 desta venv o aviso não é emitido (a depreciação
começa no 3.12), mas o uso é incompatível com runtimes atuais e já produz datetimes *naive*.

## Endpoints inventariados (baseline da Fase 3)

| Método | Rota | Handler | Observação |
|---|---|---|---|
| GET | / | app.py:26 | rota inline no entry point |
| GET | /health | app.py:22 | rota inline; `utcnow()` deprecado |
| GET | /tasks | routes/task_routes.py:11 | N+1 (finding 8), regra inline (9) |
| GET | /tasks/`<id>` | routes/task_routes.py:65 | regra inline (9) |
| POST | /tasks | routes/task_routes.py:85 | fat route de 70 linhas (4) |
| PUT | /tasks/`<id>` | routes/task_routes.py:156 | validação divergente (11) |
| DELETE | /tasks/`<id>` | routes/task_routes.py:225 | `except:` nu (10) |
| GET | /tasks/search | routes/task_routes.py:240 | `int()` sem tratamento |
| GET | /tasks/stats | routes/task_routes.py:273 | regra inline divergente (9) |
| GET | /users | routes/user_routes.py:10 | N+1 via `len(u.tasks)` (8) |
| GET | /users/`<id>` | routes/user_routes.py:27 | expõe hash de senha (2) |
| POST | /users | routes/user_routes.py:42 | expõe hash na resposta (2) |
| PUT | /users/`<id>` | routes/user_routes.py:92 | sem auth (7) |
| DELETE | /users/`<id>` | routes/user_routes.py:134 | deleção manual (14), sem auth (7) |
| GET | /users/`<id>`/tasks | routes/user_routes.py:153 | regra inline (9) |
| POST | /login | routes/user_routes.py:185 | token fake (7), expõe hash (2) |
| GET | /reports/summary | routes/report_routes.py:12 | 90 linhas, N+1 (4, 8) |
| GET | /reports/user/`<id>` | routes/report_routes.py:103 | agregação inline (4) |
| GET | /categories | routes/report_routes.py:157 | blueprint errado (12), N+1 (8) |
| POST | /categories | routes/report_routes.py:167 | blueprint errado (12) |
| PUT | /categories/`<id>` | routes/report_routes.py:190 | sem validação de cor |
| DELETE | /categories/`<id>` | routes/report_routes.py:211 | `except:` nu (10) |

Baseline capturado: 42 chamadas cobrindo os 22 endpoints (caminhos felizes, 400, 401, 404 e
409). Resultado em `reports/validation-project-3.md`.

```
================================
Total: 22 findings
================================
```
