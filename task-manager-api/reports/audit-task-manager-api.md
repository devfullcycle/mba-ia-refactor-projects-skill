# Audit Report — task-manager-api

> Gerado pela skill `refactor-arch` (Fase 2 — Auditoria).
> Data: 2026-10-22 | Raiz: `/home/eric-ogata/codes/full_cycle/mba_engenharia_ia/desafios/desafio3/mba-ia-refactor-projects-skill/task-manager-api`
> Baseado na análise de: `reports/analysis-task-manager-api.md`

## 1. Resumo

| Métrica | Valor |
|---|---|
| Arquivos auditados | 9 arquivos de código, ~1100 LOC (exclui `__init__.py` e `seed.py`) |
| Total de achados | 16 |
| CRITICAL | 3 |
| HIGH | 3 |
| MEDIUM | 5 |
| LOW | 5 |

## 2. Achados detalhados

---

### [CRITICAL] SEC-02 — Credencial hardcoded (`SECRET_KEY`)

**Onde:** `app.py:13`

**Evidência:**
```python
# app.py:11-13
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super-secret-key-123'
```

**Impacto:** A chave de assinatura da aplicação está no código-fonte. Qualquer pessoa com acesso ao repositório pode forjar sessões/tokens e comprometer a confidencialidade dos dados. Como `python-dotenv` já está declarado em `requirements.txt`, a infraestrutura para externalizar config existe, mas não é usada.

**Recomendação:**
```python
# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ["SECRET_KEY"]  # falha explícita se ausente
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///tasks.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

**Referência:** `references/anti-patterns.md` → SEC-02

---

### [CRITICAL] SEC-02 — Credencial hardcoded (SMTP)

**Onde:** `services/notification_service.py:7-10`

**Evidência:**
```python
# services/notification_service.py:5-10
def __init__(self):
    self.notifications = []
    self.email_host = 'smtp.gmail.com'
    self.email_port = 587
    self.email_user = 'taskmanager@gmail.com'
    self.email_password = 'senha123'
```

**Impacto:** Credenciais de conta de e-mail em texto puro no repositório. Além do vazamento, a classe nunca é instanciada (código morto), o que também indica que a funcionalidade de notificação está inoperante.

**Recomendação:** Ler host/porta/usuário/senha de variáveis de ambiente (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`) e remover o módulo se a funcionalidade não fizer parte do escopo.

**Referência:** `references/anti-patterns.md` → SEC-02

---

### [CRITICAL] SEC-03 — Criptografia fraca / exposição de senha

**Onde:** `models/user.py:29`, `models/user.py:32`, `models/user.py:16-25`

**Evidência:**
```python
# models/user.py:27-32
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()

def check_password(self, pwd):
    return self.password == hashlib.md5(pwd.encode()).hexdigest()

# models/user.py:16-25 — to_dict devolve o hash
def to_dict(self):
    return {
        'id': self.id,
        ...
        'password': self.password,
        ...
    }
```

**Impacto:** MD5 sem salt é quebrável por rainbow tables/GPU em segundos. Pior: `to_dict()` inclui o hash da senha, e ele é retornado em `POST /users` (`routes/user_routes.py:85`), `PUT /users/<id>` (`:129`) e no `POST /login` (`:209`). O hash vaza para qualquer cliente da API.

**Recomendação:** Usar `werkzeug.security.generate_password_hash`/`check_password_hash` (já disponível via Flask) ou bcrypt/argon2, e remover `password` do dicionário público:
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)

def to_dict(self):
    return {'id': self.id, 'name': self.name, 'email': self.email,
            'role': self.role, 'active': self.active,
            'created_at': str(self.created_at)}  # sem 'password'
```

**Referência:** `references/anti-patterns.md` → SEC-03

---

### [HIGH] SEC-04 — Rotas de escrita sem autenticação/autorização

**Onde:** `routes/task_routes.py:85`, `:156`, `:225`; `routes/user_routes.py:42`, `:92`, `:134`; `routes/report_routes.py:167`, `:190`, `:211`; `routes/user_routes.py:207-211`

**Evidência:**
```python
# routes/task_routes.py:85-86
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()   # nenhum guard de auth

# routes/user_routes.py:207-211
return jsonify({
    'message': 'Login realizado com sucesso',
    'user': user.to_dict(),
    'token': 'fake-jwt-token-' + str(user.id)   # token previsível
}), 200
```

**Impacto:** Qualquer cliente anônimo cria, altera e deleta tasks, usuários e categorias. O login não emite credencial verificável — o "token" é o id do usuário com prefixo fixo, trivialmente forjável e nunca validado pelas rotas. Combinado com a exposição do hash de senha (SEC-03), o modelo de autenticação é inexistente.

**Recomendação:** Emitir JWT real (ex.: `flask-jwt-extended`) e proteger as rotas de escrita com decorator `@jwt_required()`; restringir operações administrativas (ex.: criação/edição de usuários) a `role == 'admin'`. A Fase 3 deve ao menos implementar um guard central reutilizável, sem quebrar o contrato dos endpoints.

**Referência:** `references/anti-patterns.md` → SEC-04

---

### [HIGH] ARCH-01 — Lógica de negócio no Controller/Rota

**Onde:** `routes/task_routes.py:85-238`, `routes/user_routes.py:42-151`, `routes/report_routes.py:12-155`

**Evidência:**
```python
# routes/task_routes.py:92-132 (trecho)
title = data.get('title')
if not title: ...
if len(title) < 3: ...
if len(title) > 200: ...
status = data.get('status', 'pending')
if status not in ['pending', 'in_progress', 'done', 'cancelled']: ...
if priority < 1 or priority > 5: ...
if user_id:
    user = User.query.get(user_id)
...
task = Task()
task.title = title
```

**Impacto:** Validação, regras de estado, cálculo de atraso, agregações de relatório e montagem de resposta vivem nas funções de rota (algumas com 70+ linhas). A regra de negócio não pode ser testada sem subir HTTP e banco; `utils/helpers.py:57-108` já contém uma versão paralela dessa validação, que ficou órfã.

**Recomendação:** Extrair casos de uso para `services/` (ex.: `TaskService.create_task`, `TaskService.update_task`, `ReportService.summary`) e deixar a rota apenas: ler request → chamar service → formatar resposta HTTP/erro.

**Referência:** `references/anti-patterns.md` → ARCH-01

---

### [HIGH] ARCH-02 — Acesso a dados no Controller/Rota

**Onde:** `routes/task_routes.py:14`, `:42`, `:51`, `:67`, `:117`, `:122`, `:147-148`, `:158`, `:188`, `:195`, `:227`, `:232`, `:247-266`, `:275-281`; `routes/user_routes.py:12`, `:29`, `:35`, `:67`, `:81-82`, `:94`, `:109`, `:136`, `:140-145`, `:155`, `:159`, `:197`; `routes/report_routes.py:15-56`, `:105`, `:109`, `:159-163`, `:183-184`, `:192`, `:218`

**Evidência:**
```python
# routes/task_routes.py:14, 41-57
tasks = Task.query.all()
...
if t.user_id:
    user = User.query.get(t.user_id)
if t.category_id:
    cat = Category.query.get(t.category_id)
```

**Impacto:** ORM e `db.session` são usados diretamente na camada de transporte. Não há repositório nem ponto único para trocar persistência, aplicar filtros de tenant ou testar com repositório fake. As mesmas consultas aparecem duplicadas em `task_routes`, `user_routes` e `report_routes`.

**Recomendação:** Introduzir repositórios (ex.: `repositories/task_repository.py`) ou, no mínimo, métodos de consulta nos Models; services dependem dos repositórios, rotas dependem dos services.

**Referência:** `references/anti-patterns.md` → ARCH-02

---

### [MEDIUM] PERF-01 — Queries N+1

**Onde:** `routes/task_routes.py:41-57`; `routes/user_routes.py:22`; `routes/report_routes.py:53-68`, `routes/report_routes.py:157-164`

**Evidência:**
```python
# routes/task_routes.py:14, 41-57
tasks = Task.query.all()
for t in tasks:
    if t.user_id:
        user = User.query.get(t.user_id)
    if t.category_id:
        cat = Category.query.get(t.category_id)

# routes/report_routes.py:53-56
users = User.query.all()
for u in users:
    user_tasks = Task.query.filter_by(user_id=u.id).all()

# routes/user_routes.py:22
'task_count': len(u.tasks)     # lazy load por usuário
```

**Impacto:** `GET /tasks` dispara 1 + 2N consultas; `GET /reports/summary` dispara 1 + N consultas para produtividade; `GET /users` carrega todas as tasks de cada usuário. Em bases com centenas de registros a latência cresce linearmente e o endpoint de relatório fica inviável.

**Recomendação:** Eager loading e agregação no banco:
```python
from sqlalchemy.orm import joinedload
tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()

# contagem por usuário em uma query
from sqlalchemy import func
counts = dict(db.session.query(Task.user_id, func.count(Task.id))
                        .group_by(Task.user_id).all())
```

**Referência:** `references/anti-patterns.md` → PERF-01

---

### [MEDIUM] QUAL-02 — Validação de entrada ausente/insuficiente

**Onde:** `routes/report_routes.py:196-202`, `routes/task_routes.py:166-184`, `routes/task_routes.py:104`, `:113`

**Evidência:**
```python
# routes/report_routes.py:196-202 — data pode ser None
data = request.get_json()
if 'name' in data:          # TypeError: argument of type 'NoneType' is not iterable
    cat.name = data['name']

# routes/task_routes.py:166-169 — title pode ser None
if 'title' in data:
    if len(data['title']) < 3:   # TypeError se title == null

# routes/task_routes.py:104,113 — priority pode ser string
priority = data.get('priority', 3)
if priority < 1 or priority > 5:   # TypeError se vier "3"
```

**Impacto:** Bodies `null`, campos com tipo incorreto (`title: null`, `priority: "alta"`) ou JSON ausente em `PUT /categories/<id>` resultam em 500 em vez de 400. `marshmallow` está declarado no manifesto justamente para isso, mas não é usado.

**Recomendação:** Validar com schemas (marshmallow/pydantic) ou helpers explícitos que checam presença, tipo e faixa antes de qualquer acesso; retornar 400 com mensagem de campo.

**Referência:** `references/anti-patterns.md` → QUAL-02

---

### [MEDIUM] QUAL-03 — Tratamento de erro genérico

**Onde:** `routes/task_routes.py:62`, `:137`, `:151`, `:204`, `:221`, `:236`, `:283`; `routes/user_routes.py:130`, `:149`; `routes/report_routes.py:186`, `:207`, `:221`

**Evidência:**
```python
# routes/task_routes.py:61-63
    return jsonify(result), 200
except:                       # captura tudo, sem log
    return jsonify({'error': 'Erro interno'}), 500

# routes/task_routes.py:134-138
if due_date:
    try:
        task.due_date = datetime.strptime(due_date, '%Y-%m-%d')
    except:               # mascara até KeyboardInterrupt/SystemExit
        return jsonify({'error': 'Formato de data inválido...'}), 400
```

**Impacto:** `except:` nu engole erros de programação (AttributeError, TypeError, até `SystemExit`) e os converte em 400/500 sem log, dificultando diagnóstico. Não há error handler central: o mesmo bloco `try/except` é repetido 11 vezes, com respostas inconsistentes.

**Recomendação:** Capturar exceções específicas (`ValueError`, `SQLAlchemyError`) e registrar handlers globais:
```python
@app.errorhandler(ValueError)
def handle_value_error(err):
    return jsonify({'error': str(err)}), 400

@app.errorhandler(500)
def handle_500(err):
    app.logger.exception('Erro não tratado')
    return jsonify({'error': 'Erro interno'}), 500
```

**Referência:** `references/anti-patterns.md` → QUAL-03

---

### [MEDIUM] QUAL-04 — Estado global mutável

**Onde:** `services/notification_service.py:6`, `:31-36`, `:43-48`

**Evidência:**
```python
# services/notification_service.py:4-6
class NotificationService:
    def __init__(self):
        self.notifications = []   # lista mutável compartilhada pela instância
...
    def get_notifications(self, user_id):
        for n in self.notifications:   # cresce sem limite, sem thread-safety
```

**Impacto:** Notificações acumulam indefinidamente em memória; se o serviço fosse usado como singleton, requisições concorrentes compartilhariam estado, e em múltiplos workers cada processo teria uma visão diferente. Além disso, o serviço não é instanciado em nenhum lugar (código morto).

**Recomendação:** Persistir notificações em tabela/repositório com escopo de request, ou remover o módulo caso a funcionalidade não seja usada.

**Referência:** `references/anti-patterns.md` → QUAL-04

---

### [MEDIUM] ARCH-03 — Model com responsabilidades duplas

**Onde:** `models/user.py:1-38`, `models/task.py:23-60`

**Evidência:**
```python
# models/user.py — entidade + criptografia + serialização pública + regra de papel
class User(db.Model):
    ...
    def to_dict(self): ...
    def set_password(self, pwd): ...      # criptografia
    def check_password(self, pwd): ...
    def is_admin(self): ...               # regra de autorização

# models/task.py:38-60 — entidade + validação + regra de atraso
    def validate_status(self, new_status): ...
    def validate_priority(self, p): ...
    def is_overdue(self): ...
```

**Impacto:** `User` acumula persistência, hashing, serialização e autorização; `Task` acumula serialização, validação e cálculo de atraso duplicado nas rotas. A regra de atraso existe em três versões (`Task.is_overdue`, `task_routes.py:30-39`, `user_routes.py:171-180`), com risco de divergência.

**Recomendação:** Manter no Model apenas invariantes de entidade e `to_dict` público (sem segredo); mover hashing para um `PasswordService`/`security.py`, validações para schema/service e cálculo de atraso para um único método reutilizado por todos os endpoints.

**Referência:** `references/anti-patterns.md` → ARCH-03

---

### [LOW] QUAL-05 — Dependências e código mortos

**Onde:** `requirements.txt:4`, `:5`, `:6`; `services/notification_service.py` (módulo inteiro); `app.py:7`; `routes/task_routes.py:7`; `routes/user_routes.py:6`; `utils/helpers.py:3-7`

**Evidência:**
```text
# requirements.txt:4-6
marshmallow==3.20.1
requests==2.31.0
python-dotenv==1.0.0
```
```python
# app.py:7 — imports não usados
import os, sys, json, datetime       # só datetime é usado
# routes/task_routes.py:7
import json, os, sys, time           # nenhum é usado
```

**Impacto:** Três dependências declaradas não são importadas em nenhum arquivo; `NotificationService` nunca é referenciado; imports mortos poluem o módulo e aumentam a superfície de ataque/tempo de build.

**Recomendação:** Remover dependências e imports não usados **exceto** `python-dotenv`, que deve passar a ser usado para eliminar SEC-02; remover ou implementar `notification_service.py`.

**Referência:** `references/anti-patterns.md` → QUAL-05

---

### [LOW] QUAL-06 — Schema sem versionamento (sem migrations)

**Onde:** `app.py:30-31`

**Evidência:**
```python
# app.py:30-31
with app.app_context():
    db.create_all()
```

**Impacto:** O schema é criado no import do módulo, sem histórico de alterações. Mudanças em colunas (ex.: trocar o tamanho de `password` para bcrypt) não são aplicadas em bancos existentes, exigindo recriação manual.

**Recomendação:** Adotar Flask-Migrate/Alembic (`flask db init/migrate/upgrade`) e remover `db.create_all()` do caminho de import.

**Referência:** `references/anti-patterns.md` → QUAL-06

---

### [LOW] QUAL-07 — Configuração hardcoded

**Onde:** `app.py:11`, `:13`, `:34`

**Evidência:**
```python
# app.py:11,13,34
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SECRET_KEY'] = 'super-secret-key-123'
app.run(debug=True, host='0.0.0.0', port=5000)
```

**Impacto:** Host, porta, flag de debug e URI do banco são fixos. Em produção, `debug=True` expõe o debugger interativo (execução remota de código) e o bind em `0.0.0.0` amplia a exposição. Não é possível promover a mesma build entre ambientes.

**Recomendação:** Externalizar em classe `Config` lendo `os.getenv`, com `DEBUG` padrão `False` e `HOST` padrão `127.0.0.1`.

**Referência:** `references/anti-patterns.md` → QUAL-07

---

### [LOW] QUAL-08 — Ausência de testes automatizados

**Onde:** raiz do projeto (nenhum `tests/`, `pytest.ini`, `*_test.py`)

**Evidência:**
```text
$ find . -name 'test*' -o -name 'pytest.ini' -o -name 'conftest.py'
(nenhum resultado)
```

**Impacto:** Não há rede de segurança para a refatoração: qualquer regressão em contratos de resposta ou regras de atraso só será detectada em produção.

**Recomendação:** Adicionar ao menos testes de integração dos endpoints principais (`/health`, CRUD de tasks, `/login`, `/reports/summary`) usando `pytest` + `app.test_client()` com banco SQLite em memória.

**Referência:** `references/anti-patterns.md` → QUAL-08

---

### [LOW] DEP-01 — Uso de APIs deprecated

**Onde:** `models/task.py:15`, `:16`, `:52`; `models/user.py:14`; `models/category.py:11`; `services/notification_service.py:35`; `utils/helpers.py:38`; `routes/task_routes.py:31`, `:42`, `:51`, `:67`, `:72`, `:117`, `:122`, `:158`, `:188`, `:195`, `:215`, `:227`, `:285`; `routes/user_routes.py:29`, `:94`, `:136`, `:155`, `:172`; `routes/report_routes.py:35`, `:42`, `:45`, `:71`, `:105`, `:133`, `:192`, `:213`

**Evidência:**
```python
# models/task.py:15-16 — datetime.utcnow() deprecated desde Python 3.12
created_at = db.Column(db.DateTime, default=datetime.utcnow)
updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# routes/task_routes.py:67 — Query.get() é legacy API no SQLAlchemy 2.0
task = Task.query.get(task_id)
```

**Impacto:** `datetime.utcnow()` retorna datetime *naive* e está marcado como deprecated (Python 3.12+); em versões futuras emitirá erro. `Query.get()` é API legada do SQLAlchemy 2.0, mantida apenas por compatibilidade — emite `LegacyAPIWarning` e deve ser substituída por `db.session.get(Model, id)`.

**Recomendação:**
```python
from datetime import datetime, timezone
datetime.now(timezone.utc)            # em vez de datetime.utcnow()

task = db.session.get(Task, task_id)  # em vez de Task.query.get(task_id)
```

**Referência:** `references/anti-patterns.md` → DEP-01

---

## 3. Mapa de calor por arquivo

| Arquivo | CRIT | HIGH | MED | LOW | Total |
|---|---|---|---|---|---|
| `app.py` | 1 | 0 | 0 | 2 | 3 |
| `models/user.py` | 1 | 0 | 1 | 0 | 2 |
| `models/task.py` | 0 | 0 | 0 | 1 | 1 |
| `models/category.py` | 0 | 0 | 0 | 0 | 0 |
| `routes/task_routes.py` | 0 | 2 | 3 | 1 | 6 |
| `routes/user_routes.py` | 0 | 3 | 3 | 0 | 6 |
| `routes/report_routes.py` | 0 | 3 | 3 | 0 | 6 |
| `services/notification_service.py` | 1 | 0 | 1 | 0 | 2 |
| `requirements.txt` | 0 | 0 | 0 | 1 | 1 |
| *(ausência de testes)* | 0 | 0 | 0 | 1 | 1 |

> A soma das linhas excede o total de achados porque `SEC-02`, `QUAL-02`, `QUAL-03`, `PERF-01` e `DEP-01` ocorrem em vários arquivos. A coluna Total conta ocorrências por arquivo; o resumo da seção 1 conta achados agrupados.

## 4. Achados por categoria

### Segurança
- **SEC-02** — `SECRET_KEY` e credenciais SMTP em texto puro.
- **SEC-03** — MD5 sem salt e hash de senha devolvido pela API.
- **SEC-04** — rotas de escrita sem auth, token falso e previsível.
- Sem ocorrências de SQL Injection (SEC-01): o projeto usa ORM com parâmetros, sem SQL cru.
- Sem ocorrências de XSS (SEC-05): API JSON, sem templates HTML.
- Sem log explícito de senha/token (SEC-06), embora `to_dict()` **retorne** o hash na resposta (coberto por SEC-03).

### Arquitetura
- **ARCH-01** — validação, regras e agregações dentro das rotas.
- **ARCH-02** — ORM/`db.session` manipulados diretamente nas rotas.
- **ARCH-03** — Models acumulando criptografia, autorização e serialização.
- Camadas `config/`, `middlewares/` e `repositories/` ausentes; `services/` existe mas é código morto.

### Performance
- **PERF-01** — N+1 em `/tasks`, `/users`, `/reports/summary` e `/categories` (contagens em loop).

### Qualidade
- **QUAL-02** — validação insuficiente; `null`/tipo errado geram 500.
- **QUAL-03** — 11 usos de `except:`/`except Exception` nu, sem handler global.
- **QUAL-04** — lista `notifications` mutável e sem limite.
- **QUAL-05** — 3 dependências mortas + módulo de serviço não usado.
- **QUAL-06** — `db.create_all()` sem migrations.
- **QUAL-07** — host/porta/debug/URI hardcoded.
- **QUAL-08** — nenhum teste automatizado.
- **DEP-01** — `datetime.utcnow()` e `Query.get()` deprecated.

## 5. Recomendações prioritárias

1. **[CRITICAL]** Externalizar `SECRET_KEY` e credenciais SMTP para env vars (`app.py:13`, `services/notification_service.py:7-10`).
2. **[CRITICAL]** Trocar MD5 por `generate_password_hash`/bcrypt e remover `password` de `User.to_dict` (`models/user.py:16-32`).
3. **[HIGH]** Implementar guard de autenticação/autorização e substituir o token falso (`routes/*_routes.py`, `routes/user_routes.py:210`).
4. **[HIGH]** Extrair regra de negócio das rotas para `services/` (`TaskService`, `UserService`, `CategoryService`, `ReportService`).
5. **[HIGH]** Introduzir repositórios/acesso a dados encapsulado; rotas não tocam `db.session`.
6. **[MEDIUM]** Eliminar N+1 com `joinedload`/agregação (`group_by`).
7. **[MEDIUM]** Validação de entrada com marshmallow (já declarado) retornando 400.
8. **[MEDIUM]** Error handler central + exceções específicas.
9. **[MEDIUM]** Remover estado global mutável de `NotificationService` (ou o módulo).
10. **[LOW]** Migrations, config por env, testes, remoção de deps/imports mortos, `datetime.now(timezone.utc)` e `db.session.get()`.

## 6. Notas e limitações

- `routes/task_routes.py` tem 299 LOC — **não** atinge o limiar de God Class do catálogo (>300 LOC). Não foi reportado QUAL-01 para evitar severidade inflada; ainda assim, concentra 6 achados e deve ser dividido na refatoração.
- Não foi possível executar a aplicação nesta fase (auditoria somente leitura); comportamento real de N+1 e dos 500 por validação foi inferido do código.
- Versões de runtime das bibliotecas não confirmadas (sem ambiente virtual/lockfile verificado).
- `seed.py` usa senhas de exemplo fracas (`1234`, `abcd`, `pass`); é um script de desenvolvimento, não conta como achado de produção, mas será ajustado se o hashing mudar.
- A ausência de autenticação pode ser intencional no projeto-base; ainda assim, pelo critério do catálogo (SEC-04), é um achado HIGH e será endereçado sem alterar os contratos de resposta existentes.
- `DEP-01` foi incorporado ao catálogo de referência (`references/anti-patterns.md`), cobrindo o requisito de detecção de APIs deprecated que antes não tinha ID dedicado.
