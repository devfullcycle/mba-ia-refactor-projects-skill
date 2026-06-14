================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   15 analyzed | ~1158 lines of code

## Summary
CRITICAL: 5 | HIGH: 3 | MEDIUM: 6 | LOW: 2

## Findings

### [CRITICAL] Hardcoded SECRET_KEY
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` hardcoded
  como string literal no código-fonte.
Impact: Qualquer desenvolvedor com acesso ao repositório pode forjar cookies
  de sessão do Flask e contornar proteção CSRF. Vaza via histórico do git
  mesmo se removido posteriormente.
Recommendation: Carregar do ambiente: `app.config['SECRET_KEY'] =
  os.getenv('SECRET_KEY')`. Adicionar SECRET_KEY ao .env (gitignored) e
  ao .env.example com valor placeholder.

### [CRITICAL] Hardcoded Email Credentials
File: services/notification_service.py:8-10
Description: Credenciais da conta Gmail hardcoded como literais de string:
  `self.email_user = 'taskmanager@gmail.com'`
  `self.email_password = 'senha123'`
Impact: Roubo de credenciais — credenciais commitadas no histórico do git
  e visíveis a qualquer pessoa com acesso ao repositório. Possibilita envio
  não autorizado de emails e comprometimento da conta Google.
Recommendation: Mover para variáveis de ambiente:
  `os.getenv('EMAIL_USER')` / `os.getenv('EMAIL_PASSWORD')`.
  Adicionar placeholders ao .env.example.

### [CRITICAL] MD5 Password Hashing (Broken Algorithm)
File: models/user.py:29-32
Description: Senhas hashadas com MD5, algoritmo criptograficamente quebrado:
  `self.password = hashlib.md5(pwd.encode()).hexdigest()`
  `return self.password == hashlib.md5(pwd.encode()).hexdigest()`
Impact: MD5 é reversível via rainbow tables em segundos. Uma breach do banco
  de dados expõe todas as senhas. MD5 não produz salt, permitindo ataques
  pré-computados.
Recommendation: Substituir pelo wrapper bcrypt do werkzeug:
  `from werkzeug.security import generate_password_hash, check_password_hash`
  `self.password = generate_password_hash(password)`
  `return check_password_hash(self.password, pwd)`

### [CRITICAL] Fake / Forgeable JWT Token
File: routes/user_routes.py:210
Description: Login retorna token trivialmente previsível:
  `'token': 'fake-jwt-token-' + str(user.id)`
  Como IDs de usuários são visíveis via GET /users, qualquer atacante
  pode construir um token válido para qualquer user_id.
Impact: Bypass completo de autenticação — qualquer usuário pode se passar
  por qualquer outro. Nenhuma validação de token existe em nenhuma parte do
  código (nenhum decorator @login_required ou middleware JWT).
Recommendation: Implementar JWT real usando PyJWT ou Flask-JWT-Extended.
  Assinar tokens com SECRET_KEY e validar em toda rota protegida.

### [CRITICAL] Debug Mode Hardcoded True on Public Interface
File: app.py:34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` — debug
  hardcoded como True sem nenhum override de variável de ambiente, e o
  servidor escuta em todas as interfaces de rede.
Impact: O debugger interativo do Flask fica acessível remotamente,
  permitindo execução arbitrária de código Python no servidor. Stack traces
  completas são retornadas aos clientes, expondo caminhos internos e lógica.
Recommendation: `app.run(debug=os.getenv('DEBUG','False').lower()=='true',
  host=os.getenv('HOST','127.0.0.1'))` — padrão localhost apenas.

---

### [HIGH] Password Hash Exposed in API Responses
File: models/user.py:17-25
Description: `to_dict()` retorna explicitamente `'password': self.password`
  (o hash MD5). Este método é chamado em:
  - routes/user_routes.py:33 (GET /users/:id)
  - routes/user_routes.py:85-86 (resposta POST /users)
  - routes/user_routes.py:129 (resposta PUT /users/:id)
  - routes/user_routes.py:209 (resposta POST /login)
Impact: Todo consumidor da API recebe o hash da senha, permitindo ataques
  de força bruta offline. Viola princípios de minimização de dados.
Recommendation: Remover `'password'` de `to_dict()`. Nunca incluir o campo
  de senha em respostas públicas da API.

### [HIGH] No Authentication on Any Endpoint
File: routes/task_routes.py:1-300, routes/user_routes.py:1-212,
      routes/report_routes.py:1-224
Description: Zero rotas utilizam decorators de autenticação ou middleware.
  Qualquer chamador anônimo pode: listar todos os usuários com histórico de
  tasks, deletar qualquer usuário, atualizar qualquer task (incluindo as de
  outros usuários), gerar relatórios de produtividade e deletar categorias.
Impact: Breach completa de dados — todos os registros são legíveis e
  graváveis sem credenciais. Usuários podem alterar dados uns dos outros.
Recommendation: Implementar decorator @login_required usando Flask-JWT-Extended.
  Proteger todas as rotas não-públicas. Adicionar verificações de ownership
  (task.user_id == current_user.id) antes de operações update/delete.

### [HIGH] Business Logic Embedded in Route Handlers
File: routes/task_routes.py:13-63, routes/report_routes.py:12-101
Description: Route handlers contêm lógica de domínio complexa:
  (1) get_tasks() (task_routes.py:30-39) reimplementa manualmente
  `task.is_overdue()`, que já existe em models/task.py:50-60.
  (2) summary_report() (report_routes.py:53-68) calcula métricas de
  produtividade de usuários (taxas de conclusão, contagens de overdue)
  inline na rota, iterando sobre todos os usuários e suas tasks.
  (3) report_routes.py:157-223 mistura operações CRUD de categorias em
  um arquivo chamado "report_routes", violando separação de domínios.
Impact: Lógica não pode ser testada em isolamento sem um servidor HTTP ativo.
  Mudanças em regras de domínio exigem edição em múltiplos arquivos de rotas.
Recommendation: Extrair lógica de domínio para controllers/. Mover rotas de
  categorias para views/category_routes.py. Usar task.is_overdue() em vez
  de reimplementar a verificação.

---

### [MEDIUM] Overdue Calculation Duplicated 6 Times
File: routes/task_routes.py:30-39, routes/task_routes.py:71-80,
      routes/task_routes.py:282-287, routes/user_routes.py:171-180,
      routes/report_routes.py:33-43, routes/report_routes.py:132-135
Description: Bloco idêntico de 5-8 linhas repetido 6 vezes:
  `if t.due_date: if t.due_date < datetime.utcnow():
    if t.status != 'done' and t.status != 'cancelled': ...`
  Nota: models/task.py:50-60 já implementa `is_overdue()` — nenhuma
  das rotas o chama.
Impact: Uma correção de bug ou mudança de regra deve ser aplicada em 6
  lugares. Um erro causa relatórios de overdue inconsistentes entre endpoints.
Recommendation: Chamar `task.is_overdue()` uniformemente em todas as rotas.

### [MEDIUM] Manual Task Serialization Duplicates to_dict()
File: routes/task_routes.py:17-28, routes/user_routes.py:163-169
Description: Ambos os locais constroem manualmente um dict de task campo
  a campo (`task_data['id'] = t.id`, `task_data['title'] = t.title`, etc.)
  em vez de chamar `t.to_dict()`, que já existe em models/task.py:23-36
  e faz exatamente a mesma coisa.
Impact: Qualquer novo campo adicionado ao Task deve ser adicionado em 3
  lugares. task_routes.py:17-28 adiciona `overdue` manualmente usando lógica
  duplicada em vez de delegar ao model.
Recommendation: Substituir ambos os blocos manuais por `task_data = t.to_dict()`
  e depois `task_data['overdue'] = t.is_overdue()`.

### [MEDIUM] N+1 Query Problem in Two Endpoints
File: routes/task_routes.py:41-57, routes/report_routes.py:54-68
Description:
  (1) get_tasks() executa `User.query.get(t.user_id)` e
  `Category.query.get(t.category_id)` dentro de um loop sobre todas as
  tasks — produzindo 2N+1 queries para N tasks (task_routes.py:41-57).
  (2) summary_report() executa `Task.query.filter_by(user_id=u.id)` dentro
  de um loop sobre todos os usuários — produzindo N+1 queries
  (report_routes.py:54-68).
Impact: Com 100 tasks e 10 usuários: get_tasks = 201 queries,
  summary_report = 11 queries. Performance degrada linearmente com o crescimento dos dados.
Recommendation: Usar eager loading do SQLAlchemy:
  `Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()`
  Para o relatório: query de Task com GROUP BY ou agregação por usuário.

### [MEDIUM] Missing Pagination on All List Endpoints
File: routes/task_routes.py:14, routes/user_routes.py:11,
      routes/report_routes.py:30, routes/report_routes.py:159
Description: Todos os endpoints de listagem chamam `.all()` sem limites:
  `Task.query.all()`, `User.query.all()`, `Category.query.all()`.
  Nenhum parâmetro `page`/`per_page` existe.
Impact: Com 100k tasks, um único GET /tasks carrega a tabela inteira na
  memória, causando timeouts e potenciais crashes por OOM.
Recommendation: Adicionar paginação:
  `page = request.args.get('page', 1, type=int)`
  `tasks = Task.query.paginate(page=page, per_page=20, error_out=False)`

### [MEDIUM] Bare Exception Handling Throughout
File: routes/task_routes.py:62, 138, 205, 237;
      routes/user_routes.py:130, 149;
      routes/report_routes.py:187, 218, 222;
      utils/helpers.py:47, 49
Description: 10 cláusulas `except:` bare engolem todos os erros silenciosamente,
  incluindo KeyboardInterrupt, SystemExit e bugs genuínos.
  Exemplo — task_routes.py:62: `except: return jsonify({'error':
  'Erro interno'}), 500` captura toda exceção sem logging.
Impact: Bugs completamente ocultos em produção. Impossível debugar falhas.
  O sistema pode estar em estado corrompido sem que ninguém saiba.
Recommendation: Capturar exceções específicas (SQLAlchemyError, ValueError)
  e registrá-las. Registrar um handler global de 500 em
  middlewares/error_handler.py para evitar repetição.

### [MEDIUM] Missing None Check in update_category
File: routes/report_routes.py:196-209
Description: `update_category()` chama `request.get_json()` e imediatamente
  acessa `if 'name' in data:` sem verificar se `data` é None (o que ocorre
  quando Content-Type está ausente ou o body está vazio). Isso lança
  `TypeError: argument of type 'NoneType' is not iterable`.
Impact: Exceção não tratada retorna 500 em vez de 400, mascarando um erro
  do cliente como erro do servidor.
Recommendation: Adicionar `if not data: return jsonify({'error': 'Invalid
  data'}), 400` antes de acessar o dict.

---

### [LOW] Unused Imports in Multiple Files
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6,
      utils/helpers.py:3-7
Description:
  - app.py:7 — `os, sys, json` importados mas nunca referenciados
  - task_routes.py:7 — `import json, os, sys, time` todos não utilizados
  - user_routes.py:6 — `hashlib, json` importados mas não utilizados
  - utils/helpers.py:3-7 — `json, sys, math, hashlib` todos não utilizados
Impact: Code bloat, induz leitores a enganos sobre as dependências reais
  do módulo, lentidão marginal no startup.
Recommendation: Remover todos os imports não utilizados.

### [LOW] Constants Defined but Not Used / Magic Numbers Inline
File: utils/helpers.py:111-116, routes/task_routes.py:96-100,
      routes/task_routes.py:113-114, routes/user_routes.py:64
Description: utils/helpers.py define `MAX_TITLE_LENGTH = 200`,
  `MIN_TITLE_LENGTH = 3`, `MIN_PASSWORD_LENGTH = 4` mas nenhum arquivo de
  rotas os importa ou utiliza. Em vez disso, os mesmos valores aparecem como
  magic numbers inline (ex: `if len(title) > 200`, `if len(password) < 4`).
  Adicionalmente, `MIN_PASSWORD_LENGTH = 4` é perigosamente fraco para
  um sistema em produção.
Impact: Alterar o tamanho mínimo do título exige edições em pelo menos 3
  arquivos. O mínimo de 4 caracteres para senha permite senhas trivialmente
  fracas como "1234".
Recommendation: Importar e usar as constantes de utils/helpers.py nos
  controllers. Aumentar MIN_PASSWORD_LENGTH para pelo menos 8.

================================
Total: 16 findings
CRITICAL: 5 | HIGH: 3 | MEDIUM: 6 | LOW: 2
================================
