================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3 + Flask 3.0.0 (flask-sqlalchemy, flask-cors)
Files:   15 analyzed | ~1158 lines of code

## Summary
CRITICAL: 2 | HIGH: 1 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] Credenciais hardcoded no código-fonte (AP-02)
File: app.py:13, services/notification_service.py:9-10
Description: `SECRET_KEY = 'super-secret-key-123'` está fixo em `app.py:13`. `NotificationService.__init__` grava usuário e senha SMTP em texto plano (`self.email_user = 'taskmanager@gmail.com'`, `self.email_password = 'senha123'`) em `services/notification_service.py:9-10`.
Impact: Qualquer pessoa com acesso ao repositório obtém a chave de assinatura de sessão da aplicação e a credencial da conta de e-mail usada para notificações, permitindo forjar sessões ou enviar e-mail em nome do serviço.
Recommendation: Mover ambos para variáveis de ambiente (`os.environ.get('SECRET_KEY')`, `os.environ.get('EMAIL_USER')`, `os.environ.get('EMAIL_PASSWORD')`) com defaults seguros apenas para desenvolvimento local; nunca versionar segredos reais.

### [CRITICAL] Hash de senha com MD5 sem salt (AP-03 / API deprecated)
File: models/user.py:27-32
Description: `User.set_password` e `User.check_password` usam `hashlib.md5(pwd.encode()).hexdigest()` para armazenar e comparar senhas, sem salt.
Impact: MD5 é criptograficamente quebrado e vulnerável a rainbow tables e ataques de força bruta em GPU; um vazamento do banco expõe as senhas de todos os usuários de forma trivial.
Recommendation: Substituir por `werkzeug.security.generate_password_hash` / `check_password_hash` (já disponível via Flask) ou `bcrypt`/`argon2`, ambos com salt automático.

### [HIGH] Ausência de autenticação/autorização nas rotas (AP-08)
File: routes/task_routes.py:11-299, routes/user_routes.py:10-183 (exceto /login), routes/report_routes.py:12-223
Description: Existe um endpoint `POST /login` (`user_routes.py:185-211`) que retorna um token, mas nenhuma rota de tasks, usuários ou relatórios exige ou valida esse token — qualquer requisição HTTP sem credenciais lê e altera dados de qualquer usuário. Agravante: o token retornado (`'fake-jwt-token-' + str(user.id)`, `user_routes.py:210`) é previsível e não assinado, então mesmo que fosse checado seria trivialmente forjável.
Impact: Qualquer cliente não autenticado pode listar, criar, editar ou apagar tasks e usuários de terceiros, e ler relatórios de produtividade de toda a base.
Recommendation: Adicionar um middleware/decorator de autenticação (`@login_required`) que valide um JWT real (assinado, com expiração) em todas as rotas exceto `/login` e `/health`; checar autorização por recurso (usuário só edita os próprios dados, exceto admin).

### [MEDIUM] Código duplicado — cálculo de "overdue" reimplementado ignorando o model (AP-13)
File: routes/task_routes.py:30-39,71-80,282-287, routes/user_routes.py:171-180, routes/report_routes.py:33-43,132-135
Description: A mesma lógica `if due_date < utcnow() and status not in (done, cancelled)` é copiada manualmente em 6 pontos diferentes, apesar de `Task.is_overdue()` já existir e implementar exatamente essa regra em `models/task.py:50-60`.
Impact: Qualquer mudança futura na regra de negócio (ex.: novo status que não conta como pendente) precisa ser replicada em 6 lugares, com alto risco de divergência e bugs sutis.
Recommendation: Remover as reimplementações e chamar `task.is_overdue()` em todos os pontos.

### [MEDIUM] Queries N+1 (AP-11)
File: routes/task_routes.py:41-57, routes/report_routes.py:53-68,161-164
Description: `get_tasks` executa `User.query.get(...)` e `Category.query.get(...)` dentro do loop `for t in tasks` (uma query por task). `summary_report` executa `Task.query.filter_by(user_id=u.id)` dentro do loop `for u in users`. `get_categories` executa `Task.query.filter_by(category_id=c.id).count()` dentro do loop `for c in categories`.
Impact: Cada listagem/relatório dispara N queries adicionais ao banco; com o crescimento da base de tasks/usuários/categorias, o tempo de resposta cresce linearmente e satura o banco.
Recommendation: Usar `joinedload`/`selectinload` do SQLAlchemy para carregar `user`/`category` junto da query principal, e agregações únicas (`GROUP BY`) para contagens por usuário/categoria em vez de uma query por item.

### [MEDIUM] Validação duplicada e código morto de validação (AP-12 / AP-18)
File: utils/helpers.py:57-108, routes/task_routes.py:92-124,166-213
Description: `process_task_data()` em `utils/helpers.py` reimplementa toda a validação de título/status/prioridade/data/tags que já está (de forma diferente) inline em `create_task` e `update_task`, mas essa função nunca é importada nem chamada em nenhuma rota — é validação morta e duplicada ao mesmo tempo. As constantes já definidas em `utils/helpers.py:110-116` (`VALID_STATUSES`, `MIN_TITLE_LENGTH`, etc.) também não são usadas pelas rotas, que repetem os mesmos literais (`'pending'`, `3`, `200`) em cada handler.
Impact: Duas fontes de verdade para a mesma regra de validação divergem silenciosamente (ex.: `process_task_data` aceita string em `priority` e converte, as rotas exigem int); a manutenção fica ambígua sobre qual usar.
Recommendation: Escolher um único ponto de validação (idealmente um schema `marshmallow`, já presente no `requirements.txt` mas não utilizado) e remover a duplicata morta; reutilizar as constantes de `utils/helpers.py` nas rotas.

### [MEDIUM] CORS irrestrito e debug habilitado em produção (AP-14)
File: app.py:15,34
Description: `CORS(app)` é aplicado sem restrição de origem (libera qualquer domínio) e `app.run(debug=True, ...)` está fixo no código, não condicionado a ambiente.
Impact: `debug=True` em produção expõe o Werkzeug debugger interativo (execução de código arbitrário) e stack traces detalhados; CORS aberto permite que qualquer site faça requisições autenticadas contra a API.
Recommendation: Restringir CORS a origens explícitas via variável de ambiente e controlar `debug` por `os.environ.get('FLASK_DEBUG', 'false')`, nunca hardcoded como `True`.

### [LOW] `datetime.utcnow()` deprecated (API obsoleta)
File: models/task.py:15,16,52, models/user.py:14, routes/task_routes.py:31,72,136,203,215,285, routes/user_routes.py:172, routes/report_routes.py:35,42,45,48,50,71,133, services/notification_service.py:35, seed.py (múltiplas linhas)
Description: `datetime.utcnow()` está deprecated desde Python 3.12 e usado de forma pervasiva no projeto (models, rotas, seed e services).
Impact: Gera `DeprecationWarning` em cada chamada hoje e deixará de funcionar em uma futura versão do Python, exigindo uma migração ampla se adiada.
Recommendation: Substituir por `datetime.now(datetime.UTC)` em todos os pontos listados.

### [LOW] Tratamento de exceção genérico (AP-19)
File: routes/task_routes.py:62,236, routes/user_routes.py:130,149, routes/report_routes.py:186,207,221
Description: Blocos `except:` (bare) engolem qualquer exceção sem logar tipo, mensagem ou stack trace, retornando apenas uma mensagem genérica ao cliente.
Impact: Erros inesperados (bug de código, falha de conexão) ficam indistinguíveis de erros esperados, dificultando o diagnóstico em produção.
Recommendation: Capturar `except Exception as e`, logar `str(e)` (via `logging`, não `print`) e, quando fizer sentido, diferenciar exceções específicas (`IntegrityError`, `ValueError`).

### [LOW] Imports não utilizados (AP-18)
File: routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:8, utils/helpers.py:3-7
Description: `task_routes.py` importa `json, os, sys, time` e não usa nenhum; `user_routes.py` importa `json, hashlib` sem uso (hash é feito no model); `report_routes.py` importa `json` sem uso; `utils/helpers.py` importa `os, sys, math, json, hashlib` sem uso.
Impact: Ruído que dificulta entender as dependências reais de cada módulo; nenhum impacto funcional.
Recommendation: Remover os imports não utilizados.

================================
Total: 11 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
