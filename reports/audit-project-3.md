```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python (versão não declarada; local 3.14)
Framework:     Flask 3.0.0
Dependencies:  flask-sqlalchemy 3.1.1, flask-cors 4.0.0, marshmallow 3.20.1 (não usado), requests 2.31.0 (não usado), python-dotenv 1.0.0 (não usado)
Domain:        Task Manager API (tasks, usuários, categorias, relatórios de produtividade)
Architecture:  Camadas parciais — models/, routes/, services/, utils/ existem, mas rotas concentram regra de negócio e queries; service e utils desconectados; sem controllers; config hardcoded
Source files:  13 files analyzed (~1158 lines)
DB tables:     tasks, users, categories (SQLite via SQLAlchemy — sqlite:///tasks.db)
Entry point:   app.py — `python seed.py && python app.py` — porta 5000 (debug=True, host 0.0.0.0)
Endpoints:     22 routes mapped
================================
```

| Método | Path | Handler |
|---|---|---|
| GET | `/` | app.py:26 `index` |
| GET | `/health` | app.py:22 `health` |
| GET | `/tasks` | routes/task_routes.py:11 `get_tasks` |
| GET | `/tasks/<id>` | routes/task_routes.py:65 `get_task` |
| POST | `/tasks` | routes/task_routes.py:85 `create_task` |
| PUT | `/tasks/<id>` | routes/task_routes.py:156 `update_task` |
| DELETE | `/tasks/<id>` | routes/task_routes.py:225 `delete_task` |
| GET | `/tasks/search` | routes/task_routes.py:240 `search_tasks` |
| GET | `/tasks/stats` | routes/task_routes.py:273 `task_stats` |
| GET | `/users` | routes/user_routes.py:10 `get_users` |
| GET | `/users/<id>` | routes/user_routes.py:27 `get_user` |
| POST | `/users` | routes/user_routes.py:42 `create_user` |
| PUT | `/users/<id>` | routes/user_routes.py:92 `update_user` |
| DELETE | `/users/<id>` | routes/user_routes.py:134 `delete_user` |
| GET | `/users/<id>/tasks` | routes/user_routes.py:153 `get_user_tasks` |
| POST | `/login` | routes/user_routes.py:185 `login` |
| GET | `/reports/summary` | routes/report_routes.py:12 `summary_report` |
| GET | `/reports/user/<id>` | routes/report_routes.py:103 `user_report` |
| GET | `/categories` | routes/report_routes.py:157 `get_categories` |
| POST | `/categories` | routes/report_routes.py:167 `create_category` |
| PUT | `/categories/<id>` | routes/report_routes.py:190 `update_category` |
| DELETE | `/categories/<id>` | routes/report_routes.py:211 `delete_category` |

````
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1)
Files:   13 analyzed | ~1158 lines of code
Date:    2026-11-03

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 6 | LOW: 4

## Findings

### F-01 [CRITICAL] Credenciais hardcoded (AP-02)
File: app.py:13, services/notification_service.py:7-10
Evidence:
```python
app.config['SECRET_KEY'] = 'super-secret-key-123'
self.email_password = 'senha123'
```
Description: SECRET_KEY e credenciais SMTP (usuário + senha do Gmail) versionadas no código.
Impact: Chave de assinatura e conta de e-mail comprometidas para qualquer pessoa com acesso ao repositório.
Recommendation: `config/settings.py` lendo variáveis de ambiente + `.env.example` (PB-02).

### F-02 [CRITICAL] Exposição de hash de senha (AP-04)
File: models/user.py:16-25, routes/user_routes.py:33, routes/user_routes.py:85, routes/user_routes.py:129, routes/user_routes.py:209
Evidence:
```python
'password': self.password,
```
Description: `User.to_dict()` inclui o hash da senha, devolvido por GET /users/<id>, POST/PUT /users e POST /login.
Impact: Hashes MD5 sem salt são revertidos em segundos (rainbow tables) — equivale a expor as senhas.
Recommendation: Serialização pública sem `password` (PB-04).

### F-03 [CRITICAL] Hash de senha inseguro — MD5 sem salt (AP-06)
File: models/user.py:27-32
Evidence:
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```
Description: Senhas armazenadas com MD5 puro, sem salt nem custo computacional.
Impact: Vazamento da base expõe todas as senhas; senhas iguais geram hashes iguais.
Recommendation: `werkzeug.security` (scrypt/pbkdf2 com salt) + migração transparente do MD5 legado no login (PB-06).

### F-04 [HIGH] Autenticação falsa / sem autorização (AP-11)
File: routes/user_routes.py:207-211, routes/user_routes.py:52, routes/user_routes.py:71
Evidence:
```python
'token': 'fake-jwt-token-' + str(user.id)
```
Description: Login emite token previsível derivado apenas do id; nenhum endpoint verifica identidade, e POST /users aceita `role: admin` de qualquer cliente.
Impact: Qualquer um forja tokens e pode criar usuários administradores (escalonamento de privilégio).
Recommendation: Token assinado com expiração (itsdangerous + SECRET_KEY) e, em seguida, guard de autenticação/papel nos endpoints de escrita (PB-11, PB-05).

### F-05 [HIGH] Regra de negócio nas rotas — Fat Controller (AP-07)
File: routes/report_routes.py:12-101, routes/report_routes.py:103-155, routes/task_routes.py:11-63, routes/task_routes.py:85-154, routes/task_routes.py:156-223, routes/task_routes.py:273-299, routes/user_routes.py:42-90
Evidence:
```python
for t in all_tasks:
    if t.due_date:
        if t.due_date < datetime.utcnow():
            if t.status != 'done' and t.status != 'cancelled':
                overdue_count = overdue_count + 1
```
Description: Rotas fazem validação, consultas, cálculo de estatísticas, regras de atraso e serialização manual campo a campo; não existe camada de controllers.
Impact: Regras de negócio não reutilizáveis nem testáveis sem HTTP; handlers de até 90 linhas.
Recommendation: Introduzir controllers/ e mover regras para os models (PB-07).

### F-06 [HIGH] Acoplamento forte / service desconectado / responsabilidade mal posicionada (AP-09)
File: services/notification_service.py:4-48, routes/task_routes.py:2-5, routes/user_routes.py:2-4, routes/report_routes.py:157-223
Evidence:
```python
from database import db
from models.task import Task
from models.user import User
```
Description: Rotas importam `db` e models concretos diretamente; `NotificationService` nunca é instanciado (camada morta); CRUD de categorias está dentro de `report_routes.py`.
Impact: Impossível injetar dublês em testes; camadas existentes não cumprem seu papel; navegação confusa.
Recommendation: Composition root com controllers recebendo dependências; blueprint próprio de categorias; service injetado (PB-09, PB-03).

### F-07 [HIGH] Debug ativo em produção (AP-12)
File: app.py:34
Evidence:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```
Description: Debugger do Werkzeug ativo e servidor exposto em todas as interfaces.
Impact: Execução remota de código pelo console de debug.
Recommendation: DEBUG/HOST/PORT via config com padrão seguro (PB-02).

### F-08 [MEDIUM] Queries N+1 (AP-13)
File: routes/task_routes.py:41-57, routes/report_routes.py:53-68, routes/report_routes.py:157-165, routes/user_routes.py:22, routes/report_routes.py:15-28
Evidence:
```python
for t in tasks:
    ...
    user = User.query.get(t.user_id)
    ...
    cat = Category.query.get(t.category_id)
```
Description: Listagem de tasks faz 2 queries por task; relatório faz 1 query por usuário; categorias 1 COUNT por categoria; `len(u.tasks)` carrega lazy por usuário; resumo faz 12 COUNTs separados.
Impact: Número de queries cresce linearmente com os dados.
Recommendation: `joinedload` e agregações com `GROUP BY` (PB-12).

### F-09 [MEDIUM] Validação duplicada, incompleta e utilitários ignorados (AP-14)
File: routes/task_routes.py:92-114, routes/task_routes.py:166-184, routes/task_routes.py:260-264, routes/report_routes.py:196-202, routes/user_routes.py:61, routes/user_routes.py:106, utils/helpers.py:57-108
Evidence:
```python
if priority < 1 or priority > 5:       # TypeError (500) se priority for string
tasks = tasks.filter(Task.priority == int(priority))   # ValueError (500)
```
Description: Regras de task duplicadas entre create/update (e uma terceira cópia não usada em `process_task_data`); tipos não validados geram 500; PUT /categories sem body gera TypeError; cor de categoria não validada (`is_valid_color` existe e não é usada); regex de e-mail duplicada.
Impact: Erros 500 para entrada inválida e regras divergentes entre endpoints.
Recommendation: Validators centralizados por entidade (PB-13).

### F-10 [MEDIUM] Tratamento de erros inadequado (AP-15)
File: routes/task_routes.py:62, routes/task_routes.py:137, routes/task_routes.py:204, routes/task_routes.py:221, routes/task_routes.py:236, routes/user_routes.py:130, routes/user_routes.py:149, routes/report_routes.py:186, routes/report_routes.py:207, routes/report_routes.py:221, utils/helpers.py:46, utils/helpers.py:49, utils/helpers.py:88
Evidence:
```python
except:
    return jsonify({'error': 'Erro interno'}), 500
```
Description: 13 `except:` sem tipo (capturam até `KeyboardInterrupt`/`SystemExit`), erros engolidos sem log; sem error handler central.
Impact: Falhas silenciosas e diagnóstico impossível.
Recommendation: Exceções de domínio + error handler central com logging (PB-14).

### F-11 [MEDIUM] Código duplicado (AP-16)
File: routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/task_routes.py:283-287, routes/user_routes.py:171-180, routes/report_routes.py:33-37, routes/report_routes.py:132-135, routes/task_routes.py:17-28, routes/user_routes.py:162-169, models/task.py:50-60
Evidence:
```python
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
```
Description: A regra "task atrasada" é reimplementada 6 vezes, embora `Task.is_overdue()` exista; serialização de task repetida manualmente em 3 lugares.
Impact: Mudança de regra precisa ser replicada; alto risco de divergência.
Recommendation: Usar um único `Task.is_overdue()` e serializadores do model (PB-15).

### F-12 [MEDIUM] Uso de APIs deprecated (AP-18)
File: models/task.py:15-16, models/task.py:52, models/user.py:14, models/category.py:11, routes/task_routes.py:31, routes/task_routes.py:42, routes/task_routes.py:67, routes/report_routes.py:105, seed.py:66-74, utils/helpers.py:38, services/notification_service.py:35 (ver tabela completa abaixo)
Evidence:
```python
created_at = db.Column(db.DateTime, default=datetime.utcnow)
task = Task.query.get(task_id)
```
Description: `datetime.utcnow()` (deprecated desde Python 3.12) em 22 pontos e `Query.get()` (legacy no SQLAlchemy 2.x) em 16 pontos.
Impact: DeprecationWarning hoje e quebra em versões futuras.
Recommendation: helper `utcnow()` com `datetime.now(timezone.utc)` (naive UTC) e `db.session.get(Model, id)` (PB-17).

### F-13 [MEDIUM] Integridade referencial ao excluir categoria (AP-17)
File: routes/report_routes.py:211-223
Evidence:
```python
db.session.delete(cat)
db.session.commit()
```
Description: Excluir categoria deixa tasks apontando para `category_id` inexistente (SQLite sem `PRAGMA foreign_keys`).
Impact: Dados inconsistentes; `category_name` nulo inesperado.
Recommendation: Desassociar tasks (`category_id = NULL`) na mesma transação (PB-16).

### F-14 [LOW] Magic numbers / strings (AP-19)
File: routes/task_routes.py:96-114, routes/task_routes.py:177, routes/user_routes.py:64, routes/user_routes.py:71, routes/report_routes.py:24-28, routes/report_routes.py:129, models/task.py:39, models/task.py:46, utils/helpers.py:110-116
Evidence:
```python
if status not in ['pending', 'in_progress', 'done', 'cancelled']:
```
Description: Status, papéis, limites de título/senha e faixas de prioridade repetidos como literais — e as constantes que já existem em `utils/helpers.py:110-116` não são usadas.
Impact: Regras espalhadas e inconsistentes.
Recommendation: Constantes no model de cada entidade (PB-18).

### F-15 [LOW] Imports não usados / código morto (AP-21)
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, utils/helpers.py:3-7, utils/helpers.py:9-108
Evidence:
```python
import json, os, sys, time
```
Description: 20 imports sem uso (pyflakes) e funções utilitárias nunca chamadas (`format_date`, `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `process_task_data`...); dependências `marshmallow`, `requests` e `python-dotenv` não utilizadas.
Impact: Ruído, falsa sensação de reuso e superfície de dependências maior.
Recommendation: Remover o que não é usado e reutilizar o que for necessário (PB-19).

### F-16 [LOW] Logging via print (AP-22)
File: routes/task_routes.py:149, routes/task_routes.py:153, routes/task_routes.py:219, routes/task_routes.py:234, routes/user_routes.py:83, routes/user_routes.py:89, routes/user_routes.py:147, services/notification_service.py:21, services/notification_service.py:24, utils/helpers.py:39-41
Evidence:
```python
print(f"Task criada: {task.id} - {task.title}")
```
Description: Eventos e erros registrados com `print`.
Impact: Sem níveis nem destino configurável.
Recommendation: `logging` por módulo (PB-20).

### F-17 [LOW] Condicionais verbosas / nomenclatura (AP-20)
File: models/task.py:38-60, models/user.py:34-38, routes/report_routes.py:24-28
Evidence:
```python
if self.role == 'admin':
    return True
else:
    return False
```
Description: Funções booleanas com if/else aninhados em vez de expressões; variáveis `p1..p5`, `t`, `u`, `c`.
Impact: Leitura mais lenta e propensa a erros.
Recommendation: Expressões booleanas diretas e nomes descritivos (PB-19).

## Deprecated APIs
| File:Line | Deprecated API | Modern replacement |
|---|---|---|
| models/task.py:15, 16, 52; models/user.py:14; models/category.py:11; routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; seed.py:66, 67, 69, 70, 74; utils/helpers.py:38; services/notification_service.py:35 | `datetime.utcnow()` (deprecated no Python 3.12) | `datetime.now(timezone.utc)` via helper `utcnow()` naive |
| routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213 | `Model.query.get()` (legacy `Query.get`, SQLAlchemy 2.0) | `db.session.get(Model, id)` |

## Refactoring Plan (preview of Phase 3)
- Target structure (adaptação: projeto já em camadas na raiz — sem mover para `src/`): `config/`, `controllers/`, `validators/`, `middlewares/` novos; `routes/` (camada View) apenas mapeando HTTP; `models/` com regras/consultas; `services/` (notificação + token) injetados; `utils/` com erros e tempo; `app.py` com `create_app()` mantendo `from app import app, db` para o `seed.py`
- F-01, F-07 → PB-02 | F-02 → PB-04 | F-03 → PB-06 | F-04 → PB-11
- F-05, F-06 → PB-07/PB-09/PB-03 | F-08 → PB-12 | F-09 → PB-13 | F-10 → PB-14
- F-11 → PB-15 | F-12 → PB-17 | F-13 → PB-16 | F-14..F-17 → PB-18/PB-19/PB-20
- Contract changes required for security: campo `password` removido das respostas de usuário; `token` do login passa a ser assinado (mesmo campo, valor diferente).

================================
Total: 17 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
````
