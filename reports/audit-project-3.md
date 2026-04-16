# Audit Report — Project 3: task-manager-api

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.0.0
Dependencies:  flask-sqlalchemy 3.1.1, flask-marshmallow 1.2.0, marshmallow 3.20.1, flask-cors 4.0.0, python-dotenv 1.0.0
Domain:        Task Manager API (tarefas, usuários, categorias, relatórios)
Architecture:  Parcialmente organizada — possui models/, routes/, services/, utils/ mas lógica de negócio misturada nas rotas
Source files:  12 files analyzed
DB tables:     users, tasks, categories
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 + SQLAlchemy
Files:   12 analyzed | ~1158 lines of code

## Summary
CRITICAL: 3 | HIGH: 2 | MEDIUM: 5 | LOW: 3

## Findings

### [CRITICAL] Insecure Password Hashing (MD5)
File: models/user.py:29, models/user.py:32
Description: Senhas hashadas com MD5: `hashlib.md5(pwd.encode()).hexdigest()`. MD5 é criptograficamente quebrado desde 2004 — colisões podem ser geradas em segundos. Usado tanto no `set_password()` (linha 29) quanto no `check_password()` (linha 32).
Impact: Se o banco for comprometido, todas as senhas podem ser revertidas com rainbow tables em minutos. MD5 não deve NUNCA ser usado para senhas.
Recommendation: Substituir por `werkzeug.security.generate_password_hash()` e `check_password_hash()`, ou usar `bcrypt`.

### [CRITICAL] Hardcoded Credentials
File: app.py:13, services/notification_service.py:9-10
Description: SECRET_KEY hardcoded como `'super-secret-key-123'` em app.py:13. Credenciais de email hardcoded em notification_service.py: `email_user = 'taskmanager@gmail.com'`, `email_password = 'senha123'`.
Impact: Credenciais expostas no controle de versão. Acesso ao email e chave secreta comprometidos.
Recommendation: Usar `os.environ.get()` para todas as credenciais. Projeto já tem `python-dotenv` nas dependências mas não está sendo usado para secrets.

### [CRITICAL] Fake JWT Authentication
File: routes/user_routes.py:210
Description: Endpoint de login retorna token falso: `'token': 'fake-jwt-token-' + str(user.id)`. Nenhum endpoint valida tokens. Toda API é publicamente acessível sem autenticação.
Impact: Autenticação completamente inexistente. Qualquer pessoa pode acessar, modificar ou deletar dados de qualquer usuário.
Recommendation: Implementar JWT real com `PyJWT` ou `flask-jwt-extended`. Adicionar decorador `@auth_required` nos endpoints protegidos.

### [HIGH] Sensitive Data Exposure in API Responses
File: models/user.py:21, routes/user_routes.py:20-21
Description: Método `to_dict()` do modelo User inclui o hash da senha na resposta da API: `'password': self.password`. Todas as rotas que retornam dados de usuário expõem o hash.
Impact: Hash de senhas exposto publicamente via API. Combinado com MD5, senhas podem ser revertidas por qualquer cliente da API.
Recommendation: Remover campo `password` do método `to_dict()`. Nunca retornar dados de senha em respostas API.

### [HIGH] Massive Code Duplication
File: routes/task_routes.py:17-28 vs models/task.py:23-36, routes/task_routes.py:30-39 (duplicado em 5 locais)
Description: Lógica de conversão task-to-dict duplicada entre task_routes.py:17-28 e models/task.py:23-36. Cálculo de overdue duplicado em 5 locais: task_routes.py:30-39, task_routes.py:71-80, user_routes.py:171-180, report_routes.py:33-43, report_routes.py:132-135. Validação de status/prioridade também triplicada.
Impact: Correções de bug precisam ser aplicadas em 5+ lugares. Risco alto de inconsistência entre implementações.
Recommendation: Extrair lógica comum para métodos no model ou utility functions. Manter uma única fonte de verdade.

### [MEDIUM] Bare Except Clauses
File: routes/task_routes.py:62, 137, 151, 221, 236-238; routes/user_routes.py:130, 149; routes/report_routes.py:186, 207, 221
Description: Uso de `except:` (bare) e `except Exception as e:` genérico em 11+ locais. Nenhuma exceção específica é capturada, dificultando debug e mascarando erros reais.
Impact: Erros reais são silenciados. Debug em produção se torna extremamente difícil. Comportamento inesperado pode passar despercebido.
Recommendation: Capturar exceções específicas (`ValueError`, `IntegrityError`, etc.). Usar logging framework para registrar erros.

### [MEDIUM] N+1 Query Problem
File: routes/task_routes.py:41-48, routes/task_routes.py:50-57
Description: Para cada task, queries separadas buscam dados do usuário (linha 41-48) e da categoria (linha 50-57) individualmente dentro do loop de listagem.
Impact: Performance degrada linearmente. 100 tasks = 200+ queries extras.
Recommendation: Usar `joinedload()` do SQLAlchemy ou fazer JOIN na query principal.

### [MEDIUM] Inefficient Loops for Aggregation
File: routes/report_routes.py:30-43, routes/report_routes.py:53-68, routes/report_routes.py:119-135
Description: Loops Python para calcular estatísticas que poderiam ser queries de agregação no banco: contagem de overdue (30-43), produtividade por usuário (53-68), estatísticas por usuário (119-135).
Impact: Carrega todos os registros na memória para fazer contagens. Não escala com volume de dados.
Recommendation: Usar queries de agregação SQL: `SELECT status, COUNT(*) FROM tasks GROUP BY status`.

### [MEDIUM] Unused Imports
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:8
Description: Imports não utilizados em múltiplos arquivos: `os`, `sys`, `json`, `time` importados mas nunca referenciados no código.
Impact: Poluição do namespace. Indica falta de linting e revisão de código.
Recommendation: Remover imports não utilizados. Configurar linter (flake8, ruff) no projeto.

### [MEDIUM] Marshmallow Installed but Never Used
File: requirements.txt, routes/*.py
Description: `flask-marshmallow` e `marshmallow` estão nas dependências mas nenhum schema de validação é definido. Validação feita manualmente em cada rota com código repetitivo.
Impact: Validação inconsistente e duplicada. Biblioteca instalada desnecessariamente ou oportunidade desperdiçada.
Recommendation: Implementar schemas Marshmallow para validação automática de input em todas as rotas, ou remover a dependência.

### [LOW] No Pagination on List Endpoints
File: routes/task_routes.py:14, routes/user_routes.py:12
Description: `GET /tasks` e `GET /users` retornam todos os registros sem LIMIT/OFFSET: `Task.query.all()`, `User.query.all()`.
Impact: Performance degrada com crescimento. Respostas enormes consomem banda e memória.
Recommendation: Adicionar parâmetros `page` e `per_page` com `query.paginate()`.

### [LOW] Deprecated API: datetime.utcnow()
File: models/user.py:14, models/task.py:16, models/task.py:17, models/category.py:12
Description: Uso de `datetime.utcnow()` que está deprecated desde Python 3.12. Usado como default em colunas `created_at` e `updated_at`.
Impact: Vai gerar warnings em Python 3.12+ e pode ser removido em versões futuras.
Recommendation: Substituir por `datetime.now(timezone.utc)` ou `func.now()` do SQLAlchemy.

### [LOW] Weak Seed Passwords
File: seed.py:19, 26, 33
Description: Senhas de seed extremamente fracas: `'1234'`, `'abcd'`, `'pass'`. Combinado com MD5, essas senhas são trivialmente reversíveis.
Impact: Se seed data for usada em ambientes de staging/produção, contas ficam vulneráveis.
Recommendation: Usar senhas fortes em dados de seed ou documentar claramente que são apenas para desenvolvimento.

================================
Total: 13 findings
================================
```
