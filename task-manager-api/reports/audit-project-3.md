================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 + SQLAlchemy + SQLite
Files:   15 analyzed | ~650 lines of code

## Summary
CRITICAL: 4 | HIGH: 2 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] Hardcoded Credentials / Secrets
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` — secret key da aplicacao hardcoded no codigo-fonte.
File: services/notification_service.py:8-10
Description: Credenciais SMTP hardcoded: `self.email_user = 'taskmanager@gmail.com'`, `self.email_password = 'senha123'`, `self.email_host = 'smtp.gmail.com'`, `self.email_port = 587`.
Impact: Qualquer pessoa com acesso ao repositorio possui as credenciais de producao. Vazamento no Git expoe todos os sistemas integrados.
Recommendation: Mover TODOS os secrets para variaveis de ambiente via `python-dotenv` (ja listado em requirements.txt mas nao utilizado). Criar arquivo `.env.example` com as variaveis necessarias.

### [CRITICAL] God Class / God File
File: routes/report_routes.py:1-223
Description: Arquivo de 223 linhas que acumula DOIS dominios distintos: (1) relatorios (summary_report, user_report) e (2) CRUD de categorias (get_categories, create_category, update_category, delete_category). Categorias nao tem relacao direta com relatorios e deveriam estar em seu proprio modulo de rotas.
File: routes/task_routes.py:1-300
Description: Arquivo de 300 linhas com CRUD de tasks, logica de busca, calculo de estatisticas, verificacao de overdue, validacao de campos e queries diretas ao banco — multiplas responsabilidades em um unico arquivo.
Impact: Impossivel testar em isolamento. Mudancas em categorias podem afetar relatorios e vice-versa. Viola Single Responsibility Principle.
Recommendation: Separar categorias em `routes/category_routes.py` com seu proprio controller. Extrair logica de negocio de `task_routes.py` para controllers dedicados.

### [CRITICAL] Unauthenticated Sensitive Endpoints
File: routes/task_routes.py (todas as rotas)
File: routes/user_routes.py (todas as rotas)
File: routes/report_routes.py (todas as rotas)
Description: Nenhum endpoint requer autenticacao. Operacoes destrutivas (DELETE em tasks, users, categories) estao disponiveis sem qualquer verificacao de identidade ou autorizacao. O endpoint `/login` existe mas retorna um token falso (`fake-jwt-token-{id}`) que nao e verificado em nenhuma requisicao.
Impact: Qualquer usuario anonimo pode criar, alterar e deletar todos os dados do sistema.
Recommendation: Implementar middleware de autenticacao JWT real que valide o token em todas as rotas exceto `/login` e endpoints publicos. Adicionar verificacao de autorizacao (role-based) para operacoes administrativas.

### [CRITICAL] Weak Cryptography
File: models/user.py:29-32
Description: Senhas hasheadas com MD5 sem salt: `self.password = hashlib.md5(pwd.encode()).hexdigest()` e `return self.password == hashlib.md5(pwd.encode()).hexdigest()`. MD5 e criptograficamente quebrado e nao deve ser usado para senhas.
Impact: Database leak permite recuperacao trivial de todas as senhas via rainbow tables. MD5 sem salt e equivalente a armazenar senhas em plaintext do ponto de vista de seguranca.
Recommendation: Substituir por `werkzeug.security.generate_password_hash()` e `check_password_hash()` (ja incluido no Flask) ou `bcrypt`/`argon2`.

### [HIGH] Business Logic in Route Layer
File: routes/task_routes.py:11-63 (get_tasks), 85-154 (create_task), 156-223 (update_task), 240-271 (search_tasks), 273-299 (task_stats)
File: routes/user_routes.py:10-25 (get_users), 42-90 (create_user), 92-132 (update_user), 134-151 (delete_user), 153-183 (get_user_tasks), 185-211 (login)
File: routes/report_routes.py:12-101 (summary_report), 103-155 (user_report)
Description: Todos os route handlers executam queries diretamente via `Task.query`, `User.query`, `Category.query`, contem validacao de regras de negocio (status, prioridade, email), calculos (overdue, completion_rate) e logica de serializacao. Nao existe camada de controllers.
Impact: Impossivel reutilizar logica em outro contexto (CLI, tests, outros endpoints). Impossivel testar unitariamente sem subir o servidor HTTP.
Recommendation: Criar camada de controllers (ex: `controllers/task_controller.py`, `controllers/user_controller.py`, `controllers/report_controller.py`) que encapsulem toda logica de negocio. Routes devem apenas extrair parametros do request e chamar controllers.

### [HIGH] Sensitive Data Exposure in API Responses
File: models/user.py:16-25
Description: O metodo `to_dict()` retorna o campo `password` (hash MD5) na resposta: `'password': self.password`. Todos os endpoints que serializam User (GET /users, GET /users/<id>, POST /users, PUT /users/<id>, POST /login) expoem o hash da senha.
Impact: Qualquer consumidor da API tem acesso ao hash das senhas de todos os usuarios, facilitando ataques de forca bruta offline.
Recommendation: Remover campo `password` do `to_dict()`. Criar metodo `to_public_dict()` que retorne apenas campos seguros (id, name, email, role, active, created_at).

### [MEDIUM] N+1 Query Problem
File: routes/task_routes.py:42-57
Description: Para cada task no loop, executa `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` — N tasks geram ate 2N+1 queries.
File: routes/report_routes.py:53-68
Description: Para cada user no loop, executa `Task.query.filter_by(user_id=u.id).all()` e depois itera cada task — N users geram N+1 queries.
File: routes/report_routes.py:159-163
Description: Para cada categoria, executa `Task.query.filter_by(category_id=c.id).count()` — N categorias geram N queries.
Impact: Performance degrada linearmente com o volume de dados. Uma listagem de 100 tasks pode gerar 200+ queries ao banco.
Recommendation: Usar `joinedload()` ou `subqueryload()` para carregar relacionamentos em uma unica query. Usar `db.session.query()` com `func.count()` e `group_by()` para agregacoes.

### [MEDIUM] Duplicated Code
File: routes/task_routes.py:30-39, 71-80, 283-287 | routes/report_routes.py:34-43, 132-135 | routes/user_routes.py:171-180
Description: Logica de verificacao de overdue copiada em 6 locais diferentes com estrutura identica: verifica `due_date < datetime.utcnow()` e `status not in ['done', 'cancelled']`. O model `Task` ja possui metodo `is_overdue()` (task.py:50-60) que NUNCA e utilizado.
File: routes/task_routes.py:110, routes/user_routes.py:71, utils/helpers.py:75
Description: Validacao de status (`['pending', 'in_progress', 'done', 'cancelled']`) repetida em 3 locais. Constantes `VALID_STATUSES` existem em `helpers.py:110` mas nao sao utilizadas.
Impact: Mudancas na regra de overdue ou status precisam ser replicadas em multiplos arquivos. Bug fix em um ponto pode ser esquecido nos outros.
Recommendation: Utilizar o metodo `Task.is_overdue()` ja existente. Centralizar constantes e validacoes em um unico local e importa-las.

### [MEDIUM] Inadequate Error Handling
File: routes/task_routes.py:62, 137, 237 | routes/user_routes.py:131, 149 | routes/report_routes.py:186, 207, 222
Description: 8 blocos `except:` sem tipo especifico de excecao (bare except). Excecoes sao capturadas silenciosamente sem log util, retornando mensagens genericas como `{'error': 'Erro interno'}`.
Impact: Bugs reais podem ser escondidos silenciosamente. Debug dificultado pela falta de informacao util. Nao e possivel distinguir entre erro de validacao, erro de banco e erro de sistema.
Recommendation: Usar `except Exception as e:` com log da excecao. Criar middleware centralizado de error handling. Definir excecoes customizadas para diferentes cenarios.

### [MEDIUM] Deprecated API Usage
File: models/task.py:16, models/user.py:14, models/category.py:11 e todos os routes
Description: `datetime.utcnow()` usado em todo o projeto — deprecated no Python 3.12+. Substituir por `datetime.now(datetime.timezone.utc)`.
File: routes/task_routes.py:67, 158 | routes/user_routes.py:29, 93 | routes/report_routes.py:105
Description: `Model.query.get(id)` — deprecated no SQLAlchemy 2.x. Deve ser substituido por `db.session.get(Model, id)`.
File: app.py:34
Description: `app.run(debug=True)` — modo debug nao deve ser usado em producao.
Impact: Warnings em versoes atuais do Python. Codigo quebrara ao atualizar para versoes futuras. Comportamento sem timezone pode causar bugs em ambientes com fusos diferentes.
Recommendation: Substituir `datetime.utcnow()` por `datetime.now(timezone.utc)`. Substituir `Model.query.get()` por `db.session.get()`. Tornar debug condicional via variavel de ambiente.

### [LOW] Poor Variable Naming
File: routes/task_routes.py:16, 268 (variavel `t`), routes/user_routes.py:14 (variavel `u`), routes/report_routes.py:33 (variavel `t`), report_routes.py:119 (variavel `t`), report_routes.py:162 (variavel `c`)
Description: Variaveis de uma letra como `t` para tasks, `u` para users, `c` para categories usadas em loops com logica complexa.
Impact: Dificulta a leitura e compreensao do codigo, especialmente em blocos longos.
Recommendation: Usar nomes descritivos: `task`, `user`, `category`.

### [LOW] Magic Numbers / Strings
File: app.py:34 (porta 5000), routes/task_routes.py:110 (status list), routes/user_routes.py:64 (min password length 4)
Description: Valores literais espalhados pelo codigo: porta `5000`, status `['pending', 'in_progress', 'done', 'cancelled']`, roles `['user', 'admin', 'manager']`, prioridade `1-5`, tamanho minimo de senha `4`. Constantes equivalentes existem em `utils/helpers.py:110-116` mas nao sao utilizadas.
Impact: Dificil entender regras de negocio. Mudancas exigem procura em todo o codigo.
Recommendation: Importar e usar as constantes ja definidas em `utils/helpers.py`.

### [LOW] Debug Artifacts in Production Code
File: app.py:34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` — debug habilitado e bind em todas as interfaces.
File: routes/task_routes.py:149, 154, 219, 234 | routes/user_routes.py:83, 89, 147 | seed.py:93-96
Description: Multiplas chamadas `print()` como mecanismo de logging em vez de usar o modulo `logging` do Python.
Impact: Em producao, expoe informacoes internas, polui logs e pode vazar dados sensiveis via output.
Recommendation: Tornar debug condicional via `os.environ.get('FLASK_DEBUG', 'false')`. Substituir `print()` por `app.logger` ou modulo `logging`.

### [LOW] Unused Imports / Dead Code
File: app.py:7 — `import os, sys, json, datetime` (os, sys, json nao utilizados; datetime ja importado no modulo)
File: routes/task_routes.py:7 — `import json, os, sys, time` (todos nao utilizados)
File: routes/report_routes.py:8 — `import json` (nao utilizado)
File: routes/user_routes.py:6 — `import hashlib, json, re` (hashlib e json nao utilizados)
File: utils/helpers.py:31-34 (`generate_id`), helpers.py:52-55 (`is_valid_color`), helpers.py:26-29 (`sanitize_string`), helpers.py:36-41 (`log_action`), helpers.py:9-12 (`format_date`)
Description: Modulos importados mas nao referenciados. Funcoes definidas em `helpers.py` que nunca sao chamadas em nenhum lugar do projeto.
Impact: Polui o codigo e causa confusao sobre dependencias reais. `helpers.py` contem funcoes mortas que sugerem refactor incompleto.
Recommendation: Remover imports nao utilizados. Remover funcoes mortas ou integra-las ao codigo.

================================
Total: 14 findings
================================
