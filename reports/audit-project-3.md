```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.x
Framework:     Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Dependencies:  flask, flask-sqlalchemy, flask-cors, marshmallow (não usado),
               requests, python-dotenv
Domain:        Task Manager API (tasks, users, categories, reports)
Architecture:  Camadas parciais — já existem models/, routes/ (Blueprints),
               services/ e utils/, mas com regra de negócio nas rotas,
               serialização duplicada, service não utilizado e falhas de
               segurança
Source files:  11 files analyzed (app.py, database.py, seed.py,
               models/{task,user,category}.py, routes/{task,user,report}_routes.py,
               services/notification_service.py, utils/helpers.py)
DB tables:     tasks, users, categories
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask (SQLAlchemy)
Files:   11 analyzed | ~900 lines of code
Date:    2026-11-07

## Summary
CRITICAL: 3 | HIGH: 3 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] Hash de senha fraco (MD5 sem salt) (AP-04)
File: models/user.py:29, 32
Description: `set_password`/`check_password` usam `hashlib.md5(pwd).hexdigest()`.
MD5 é quebrado, sem salt e vulnerável a rainbow tables.
Impact: Senhas trivialmente recuperáveis em caso de vazamento do banco.
Recommendation: `werkzeug.security.generate_password_hash`/`check_password_hash`
(ou bcrypt/argon2) (T-05).

### [CRITICAL] Hash de senha exposto na serialização (AP-04)
File: models/user.py:16-25; routes/user_routes.py:85-86, 128-129, 207-210
Description: `User.to_dict()` inclui o campo `password`, que vaza em
`GET /users/<id>`, na resposta de criação de usuário e no login.
Impact: Exposição direta do hash de senha de qualquer usuário via API.
Recommendation: Remover `password` da serialização pública (T-05, T-10).

### [CRITICAL] Credenciais hardcoded (SECRET_KEY e SMTP) (AP-02)
File: app.py:13; services/notification_service.py:9-10
Description: `SECRET_KEY = 'super-secret-key-123'` e, no serviço de notificação,
`email_user`/`email_password = 'senha123'` embutidos no código.
Impact: Segredos versionados no repositório; comprometimento de sessão e da
conta de e-mail.
Recommendation: Mover para variáveis de ambiente (`.env` + `.env.example`) (T-01).

### [HIGH] Regra de negócio pesada dentro das rotas (AP-05)
File: routes/report_routes.py:12-101, 103-155; routes/task_routes.py:11-63, 273-299
Description: `summary_report`, `user_report`, `get_tasks` e `task_stats` fazem
toda a agregação, contagem e montagem de relatório diretamente no handler da
rota. A camada `services/` existe mas quase não é usada.
Impact: Lógica não reutilizável nem testável sem HTTP; rotas enormes.
Recommendation: Extrair para `TaskService`/`ReportService` (T-04).

### [HIGH] Serialização e regra `overdue` duplicadas (AP-11)
File: routes/task_routes.py:30-39, 71-80; routes/user_routes.py:171-180; models/task.py:50-60
Description: O cálculo de "task atrasada" é reimplementado inline em três rotas,
além de existir `Task.is_overdue()`. A montagem do dicionário de task também é
repetida (manual em `get_tasks`/`get_user_tasks` e em `to_dict`).
Impact: Divergência silenciosa quando uma cópia muda.
Recommendation: Centralizar em `Task.is_overdue()` e `Task.to_dict()` (T-10).

### [HIGH] Camada de serviço morta e validação duplicada (AP-18, AP-10)
File: services/notification_service.py:1-49; utils/helpers.py:57-108; routes/task_routes.py:85-145, 156-214
Description: `NotificationService` nunca é importado/usado; `process_task_data`
em `utils/helpers.py` duplica a validação que também está inline em
`create_task`/`update_task`; `marshmallow` está nas dependências mas não é usado.
Impact: Código morto, três fontes de validação divergentes, confusão de responsabilidade.
Recommendation: Validador único por entidade e remover/usar o service de fato (T-09).

### [MEDIUM] Query N+1 na listagem e nos relatórios (AP-09)
File: routes/task_routes.py:41-57; routes/report_routes.py:53-68
Description: `get_tasks` faz `User.query.get()` e `Category.query.get()` por task;
`summary_report` consulta as tasks de cada usuário em loop.
Impact: Degradação de performance proporcional ao volume.
Recommendation: `joinedload`/`selectinload` para carregar relacionamentos de uma vez (T-08).

### [MEDIUM] Uso de APIs deprecated (AP-13)
File: models/task.py:15-16, 52; models/user.py:14; routes/task_routes.py:31, 67, 285; routes/report_routes.py:35, 42, 45; seed.py:66-70
Description: `datetime.utcnow()` (deprecated no Python 3.12+) usado em todo o
projeto; `Model.query.get(id)` (API legada do SQLAlchemy 2.x) em várias rotas.
Impact: Warnings de deprecação e código preso a APIs em fim de vida.
Recommendation: `datetime.now(timezone.utc)` (mantendo compatibilidade naive) e
`db.session.get(Model, id)` (T-13).

### [MEDIUM] Autenticação falsa / token fake (AP-10)
File: routes/user_routes.py:210
Description: O login retorna `'fake-jwt-token-' + str(user.id)` — não há emissão
real de token nem proteção das rotas.
Impact: Sensação falsa de segurança; nenhuma rota é de fato autenticada.
Recommendation: Emitir JWT real (ex.: PyJWT) e proteger rotas sensíveis; no
mínimo, documentar como stub (T-12).

### [MEDIUM] Entry point sem factory e `create_all` no import (AP-01 parcial)
File: app.py:9-31
Description: A app é criada no escopo do módulo e `db.create_all()` roda na
importação; sem `create_app()` fica difícil testar/instanciar com outra config.
Impact: Acoplamento à configuração global; testes e múltiplos ambientes difíceis.
Recommendation: Padrão application factory com `Config` injetável (T-01, T-06).

### [LOW] Imports mortos espalhados (AP-15 relacionado)
File: app.py:7; routes/task_routes.py:7; routes/user_routes.py:6; utils/helpers.py:3-6
Description: `import os, sys, json, datetime` / `json, os, sys, time` / `math`
em grande parte não são usados.
Impact: Ruído e falsa impressão de dependências.
Recommendation: Remover imports não utilizados.

### [LOW] Prints de debug no fluxo (AP-15)
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147
Description: `print(f"Task criada ...")`, `print(f"ERRO: ...")` como log.
Impact: Ruído; sem controle de nível de log.
Recommendation: Logger configurável (T-14).

### [LOW] Retornos booleanos verbosos e lógica inflada (AP-16)
File: models/task.py:38-48, 50-60; models/user.py:34-38
Description: `validate_status`/`validate_priority`/`is_admin`/`is_overdue` usam
`if/else` para retornar `True/False` onde a expressão booleana bastaria.
Impact: Verbosidade desnecessária.
Recommendation: Simplificar para retorno direto da condição.

================================
Total: 13 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
