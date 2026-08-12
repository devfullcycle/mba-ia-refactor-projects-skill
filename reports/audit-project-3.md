# ARCHITECTURE AUDIT REPORT

**Project:** task-manager-api
**Stack:** Python + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
**Files:** 15 analyzed | ~1600 lines of code

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 4 | LOW: 2

## Findings

### [CRITICAL] Hardcoded Secrets
File: `app.py:13`, `services/notification_service.py:7-10`
Description: `SECRET_KEY='super-secret-key-123'` no código; credenciais SMTP hardcoded (`taskmanager@gmail.com` / `senha123`).
Impact: Vazamento de chave de assinatura e credenciais de e-mail em qualquer controle de versão.
Recommendation: Mover para `config/settings.py` lendo variáveis de ambiente (python-dotenv já é dependência solta no requirements).

### [CRITICAL] Weak Password Hashing (MD5 - Deprecated/Insecure API)
File: `models/user.py:29,32`
Description: `hashlib.md5(pwd).hexdigest()` usado para armazenar e conferir senhas — algoritmo trivialmente recuperável (rainbow tables).
Impact: Qualquer senha comprometida é decifrável; inclusive as do seed.
Recommendation: Usar `werkzeug.security.generate_password_hash` (pbkdf2) / `check_password_hash`.

### [CRITICAL] Sensitive Data Exposed in API Responses
File: `models/user.py:16-25`
Description: `User.to_dict()` retorna o campo `password` (hash) em `/users`, `/users/<id>` e `/login`.
Impact: Exposição de hashes de credenciais a qualquer usuário da API.
Recommendation: `to_dict()` não deve serializar `password`; nunca incluir o hash em respostas.

### [CRITICAL] Global Mutable State in NotificationService
File: `services/notification_service.py:6`
Description: `self.notifications = []` acumula notificações em memória indefinidamente (estado global crescente).
Impact: Vazamento de memória e comportamento imprevisível em instância compartilhada.
Recommendation: Limitar o histórico (cap) ou persistir notificações.

### [HIGH] Business Logic Inside Routes
File: `routes/task_routes.py`, `routes/report_routes.py`, `routes/user_routes.py`
Description: Rotas contêm validação de dados, cálculo de "overdue", estatísticas e CRUD manual (ex: `task_routes.py:30-57`, `report_routes.py:33-68`) em vez de delegar a serviços. `routes/` é a camada View do MVC e não deve abrigar rules.
Impact: Rotas grossas, difíceis de testar, validação duplicada.
Recommendation: Extraporting para `services/task_service`/`user_service`/`report_service`.

### [HIGH] Massive N+1 Queries in Reports
File: `routes/report_routes.py:55-68`, `routes/task_routes.py:42-57`
Description: `Task.query.filter_by(user_id).all()` dentro de loop por usuário; `User.query.get()` e `Category.query.get()` por task; count por categoria em loop (`task_count`).
Impact: centenas de queries SQL por request; degradação clara.
Recommendation: eager loading (`joinedload`), agregação única por usuário, ou consulta em batch.

### [HIGH] Fake JWT Token (Forged Auth Claim)
File: `routes/user_routes.py:210`
Description: `token: 'fake-jwt-token-' + str(user.id)` — string não assinada apresentada como token de autenticação.
Impact: dá falsa sensação de segurança; qualquer client pode forjá-lo.
Recommendation: usar `pyjwt` com `SECRET_KEY` real, ou remover a claim de auth.

### [HIGH] Duplicated "Is Overdue" Logic
File: `routes/task_routes.py:30-39,71-80`, `routes/report_routes.py:33-43,132-135`, `routes/user_routes.py:171-180`
Description: A mesma condição `due_date < utcnow AND status not in (done, cancelled)` repetida em ~5 lugares com variações.
Impact: inconsistência futura ao mudar regra.
Recommendation: centralizar em `Task.is_overdue()` (model já tem) e reutilizar.

### [MEDIUM] Inconsistent Error Handling
File: múltiplos `except:` e `except Exception as e` com mensagens duplicadas (`report_routes.py:186,207,221'; `task_routes.py`).
Impact: erros difíceis de depurar; respostas inconsistentes.
Recommendation: decorator/middleware central de erro que traduz exceções em JSON.

### [MEDIUM] Implicit Configuration
File: `app.py:11,34`, `requirements` tem `python-dotenv`
Description: `SQLALCHEMY_DATABASE_URI`, `SECRET_KEY`, `debug=True`, host/porta hardcoded.
Impact: ambiente (test/prod) difícil de trocar.
Recommendation: `config/settings.py` via env (dotenv).

### [MEDIUM] Missing/Weak Input Validation in Some Endpoints
File: `routes/report_routes.py:167-188` (categorias não validam cor), `routes/user_routes.py:93-132` (dados aceitos sem checagem parcial).
Impact: dados inconsistentes no banco.
Recommendation: unificar validações no service usando constantes de `config`.

### [MEDIUM] Debug Print Statements
File: `services`/`routes` — `print(...)` espalhados (`task_routes.py:149,153,219`; `user_routes:83,89,147`; `notification:21,24`).
Impact: ruído no log; sem severidade/estrutura.
Recommendation: usar `logging`.

### [LOW] Dead Code / Unused Imports & Dependencies
File: imports `os,sys,time,math,hashlib,json` sem uso; `requests`/`marshmallow` na requirements sem uso.
Impact: manutenabilidade confusa.
Recommendation: remover.

### [LOW] Magic Values / Inconsistent Naming
File: strings `'pending','done',...` e cores/# limites repetidos em vez de constantes (`utils/helpers.py` já define `VALID_STATUSES`, mas rotas não usam).
Impact: legibilidade/erros de digitação.
Recommendation: usar constantes de `config`.

---
**Total: 14 findings** (ordenação por severidade CRITICAL → LOW)