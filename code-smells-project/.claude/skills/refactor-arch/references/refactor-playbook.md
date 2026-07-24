# Playbook de Refatoração

16 padrões de transformação, cada um ligado aos anti-patterns do catálogo. Exemplos em Python
e JavaScript; a **mecânica** é a mesma em qualquer linguagem.

| ID | Padrão | Resolve |
|---|---|---|
| RP-01 | Decompor God Class em camadas | AP-01, AP-08 |
| RP-02 | Extrair configuração e segredos | AP-02, AP-11 |
| RP-03 | Parametrizar queries e isolar em repository | AP-04, AP-08 |
| RP-04 | Corrigir autenticação e blindar serialização | AP-03, AP-05 |
| RP-05 | Extrair regra de negócio do controller/rota | AP-07, AP-13 |
| RP-06 | Substituir estado global por injeção de dependência | AP-09 |
| RP-07 | Estabelecer fronteira transacional | AP-10 |
| RP-08 | Centralizar tratamento de erro em middleware | AP-15, AP-06 |
| RP-09 | Desaninhar callback hell | AP-12 |
| RP-10 | Eliminar N+1 | AP-14 |
| RP-11 | Unificar validação em um único ponto | AP-16, AP-18 |
| RP-12 | Substituir print por logger | AP-19 |
| RP-13 | Nomear constantes e variáveis | AP-20, AP-21 |
| RP-14 | Proteger rota administrativa | AP-06 |
| RP-15 | Substituir API deprecated | AP-17 |
| RP-16 | Remover código morto e centralizar serialização | AP-22, AP-23 |

Ordem de aplicação: RP-02 → RP-03/RP-04 → RP-01 → RP-05 → RP-06 → RP-07 → RP-08 → resto.
Configuração e segurança primeiro porque tudo depende deles; limpeza cosmética por último.

---

## RP-01 — Decompor God Class em camadas

**Mecânica:** (1) liste as responsabilidades do arquivo; (2) agrupe por agregado de domínio;
(3) para cada agregado, crie model (dados) e controller (fluxo); (4) mova as rotas para a
camada de views; (5) mova DDL/seed para inicialização de banco; (6) apague o original.

**Antes** (`AppManager.js` — DB + rotas + pagamento + cache):
```js
class AppManager {
    constructor() { this.db = new sqlite3.Database(':memory:'); }
    initDb() { this.db.run("CREATE TABLE users (...)"); /* + seed */ }
    setupRoutes(app) {
        app.post('/api/checkout', (req, res) => { /* 50 linhas: SQL + pagamento + resposta */ });
        app.get('/api/admin/financial-report', (req, res) => { /* N+1 + agregação */ });
    }
}
```

**Depois:**
```js
// src/database/connection.js — infra
const createConnection = (config) => new sqlite3.Database(config.dbFile);

// src/models/enrollment.repository.js — só dados
class EnrollmentRepository {
    constructor(db) { this.db = db; }
    async create({ userId, courseId }) { /* INSERT parametrizado */ }
    async findByCourse(courseId) { /* SELECT com JOIN */ }
}

// src/services/checkout.service.js — regra que atravessa agregados
class CheckoutService {
    constructor({ userRepo, courseRepo, enrollmentRepo, paymentRepo, gateway, uow }) { ... }
    async execute({ name, email, password, courseId, card }) { /* orquestra em transação */ }
}

// src/controllers/checkout.controller.js — fluxo HTTP
class CheckoutController {
    constructor(checkoutService) { this.service = checkoutService; }
    create = async (req, res, next) => {
        try {
            const result = await this.service.execute(req.body);
            res.status(201).json(result);
        } catch (err) { next(err); }        // erro vai para o middleware
    };
}

// src/routes/checkout.routes.js — só mapeamento
router.post('/checkout', controller.create);
```

Regra prática: se o nome da classe termina em `Manager`, `Helper`, `Utils` ou `Handler` e ela
tem mais de 100 linhas, ela é um agrupamento de responsabilidades, não uma abstração.

## RP-02 — Extrair configuração e segredos

**Antes** (Python):
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
db_path = "loja.db"
```

**Depois:**
```python
# src/config/settings.py
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    @classmethod
    def validate(cls):
        if not cls.SECRET_KEY:
            raise RuntimeError("SECRET_KEY é obrigatória — defina no ambiente (.env)")
```
```ini
# .env.example  (versionado, sem valores reais)
SECRET_KEY=
DATABASE_PATH=loja.db
FLASK_DEBUG=false
```

**Antes** (Node):
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_1234..." };
```
**Depois:**
```js
// src/config/index.js
const required = (name) => {
    const v = process.env[name];
    if (!v) throw new Error(`Variável de ambiente obrigatória ausente: ${name}`);
    return v;
};
module.exports = {
    port: Number(process.env.PORT ?? 3000),
    dbFile: process.env.DB_FILE ?? ':memory:',
    paymentGatewayKey: required('PAYMENT_GATEWAY_KEY'),
};
```

Cheque: `.env` no `.gitignore`; `.env.example` com todas as chaves; falha explícita no boot
quando falta segredo obrigatório (melhor que subir com default inseguro). Segredo que estava
no código deve ser considerado comprometido — registre no relatório que precisa de rotação.

## RP-03 — Parametrizar queries e isolar em repository

**Antes:**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
query = "SELECT * FROM produtos WHERE 1=1"
if termo:
    query += " AND (nome LIKE '%" + termo + "%')"
```

**Depois:**
```python
# src/models/usuario_model.py
class UsuarioModel:
    def __init__(self, conn):
        self._conn = conn

    def find_by_email(self, email):
        row = self._conn.execute(
            "SELECT id, nome, email, senha_hash, tipo, criado_em FROM usuarios WHERE email = ?",
            (email,),
        ).fetchone()
        return dict(row) if row else None

# filtro dinâmico continua parametrizado
def search(self, termo=None, categoria=None, preco_min=None):
    sql = ["SELECT * FROM produtos WHERE 1=1"]
    params = []
    if termo:
        sql.append("AND (nome LIKE ? OR descricao LIKE ?)")
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        sql.append("AND categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        sql.append("AND preco >= ?")
        params.append(preco_min)
    return [dict(r) for r in self._conn.execute(" ".join(sql), params).fetchall()]
```

Pontos: nunca concatene valor; concatene apenas *fragmentos de SQL fixos*. Selecione colunas
explicitamente em vez de `SELECT *` (evita vazar coluna nova sensível). Autenticação **não** se
faz no `WHERE` — busque por identificador e verifique o hash na aplicação (RP-04).

```js
// Node — mesma ideia
const row = await this.db.get('SELECT id, name, email FROM users WHERE email = ?', [email]);
```

## RP-04 — Corrigir autenticação e blindar serialização

**Antes:**
```python
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()

def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}  # vaza o hash
```

**Depois:**
```python
from werkzeug.security import generate_password_hash, check_password_hash
# (ou bcrypt/argon2 — o requisito é KDF com salt e custo configurável)

class User(db.Model):
    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)      # salt automático

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email,
                "role": self.role, "active": self.active}     # nunca o hash
```

**Node:**
```js
const bcrypt = require('bcrypt');
const hash = await bcrypt.hash(password, 12);
const ok = await bcrypt.compare(password, user.passwordHash);
```

Regras: um único `toPublicJSON()`/`to_dict()` por model é a **única** porta de saída da entidade
(RP-16) — assim o campo sensível não reaparece por cópia esquecida. Sem senha default quando o
cliente não envia: rejeite com 400. Health check devolve só `status` (e, no máximo,
conectividade) — nunca segredo, caminho de banco ou flag de debug. Se a API antes devolvia
senha, a remoção **é** mudança de contrato — declare no relatório final como correção de segurança.

## RP-05 — Extrair regra de negócio do controller/rota

**Antes** (rota com validação + regra + serialização):
```python
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    result = []
    for t in tasks:
        d = {'id': t.id, 'title': t.title, ...}
        if t.due_date:                                    # regra de domínio na view
            if t.due_date < datetime.utcnow():
                if t.status != 'done' and t.status != 'cancelled':
                    d['overdue'] = True
        ...
        result.append(d)
    return jsonify(result), 200
```

**Depois:**
```python
# src/models/task.py — a regra vive no agregado (e já existia: reutilize!)
class Task(db.Model):
    def is_overdue(self):
        if not self.due_date:
            return False
        return self.due_date < now_utc() and self.status not in TERMINAL_STATUSES

    def to_dict(self):
        return {**self._base_fields(), "overdue": self.is_overdue()}

# src/controllers/task_controller.py — orquestra
class TaskController:
    def __init__(self, repo):
        self._repo = repo

    def list(self):
        tasks = self._repo.list_with_relations()      # sem N+1 (RP-10)
        return [t.to_dict() for t in tasks], 200

# src/views/task_routes.py — só mapeia
@task_bp.route("/tasks", methods=["GET"])
def get_tasks():
    body, status = controller.list()
    return jsonify(body), status
```

Se a regra atravessa agregados (checkout, relatório consolidado), ela vai para um **service**,
não para o controller. Se já existe método no model ou validador em `utils/` fazendo isso
(camada fantasma, AP-13), **use o existente** em vez de criar outro — e apague as cópias inline.

## RP-06 — Substituir estado global por injeção de dependência

**Antes:**
```python
db_connection = None                      # estado global mutável

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
        cursor.execute("CREATE TABLE IF NOT EXISTS ...")   # DDL escondido no getter
    return db_connection
```

**Depois:**
```python
# src/database/connection.py — conexão por request, sem global
import sqlite3
from flask import g, current_app

def get_connection():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_connection(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()

def init_schema(app):                 # DDL explícito, chamado no factory/CLI
    with app.app_context():
        conn = get_connection()
        conn.executescript(SCHEMA_SQL)
        conn.commit()

# src/app.py — composition root injeta as dependências
def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    app.teardown_appcontext(close_connection)
    produto_model = ProdutoModel(get_connection)          # injeção
    register_routes(app, ProdutoController(produto_model))
    return app
```

**Node:** cache/contador global (`globalCache = {}`) vira instância criada no composition root e
passada ao service; sem TTL ou limite, um cache de módulo é vazamento de memória. Nunca use
`check_same_thread=False` para silenciar o driver — o problema é a conexão compartilhada.

## RP-07 — Estabelecer fronteira transacional

**Antes** (pedido, itens e estoque sem transação):
```python
cursor.execute("INSERT INTO pedidos ...")
pedido_id = cursor.lastrowid
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ...")
db.commit()          # exceção no meio do laço deixa tudo parcial
```

**Depois:**
```python
def create(self, usuario_id, itens):
    conn = self._conn()
    try:
        conn.execute("BEGIN")
        total = self._calcular_total_e_validar_estoque(conn, itens)   # falha antes de escrever
        cur = conn.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, PedidoStatus.PENDENTE, total),
        )
        pedido_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)"
            " VALUES (?, ?, ?, ?)",
            [(pedido_id, i["produto_id"], i["quantidade"], i["preco"]) for i in itens],
        )
        for i in itens:
            conn.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (i["quantidade"], i["produto_id"], i["quantidade"]),
            )
        conn.commit()
        return pedido_id
    except Exception:
        conn.rollback()
        raise                      # o middleware de erro traduz para HTTP (RP-08)
```

**Node (sqlite3 callback → promise + transação):**
```js
async function withTransaction(db, work) {
    await run(db, 'BEGIN');
    try { const r = await work(); await run(db, 'COMMIT'); return r; }
    catch (e) { await run(db, 'ROLLBACK'); throw e; }
}
```

Cheque também integridade referencial: `ON DELETE CASCADE` no schema (ou cascade no ORM) em vez
de laço manual deletando filhos; e valide antes de escrever, para não precisar desfazer.

## RP-08 — Centralizar tratamento de erro em middleware

**Antes** (16 blocos iguais, vazando detalhe interno):
```python
try:
    ...
except Exception as e:
    return jsonify({"erro": str(e)}), 500
```

**Depois:**
```python
# src/middlewares/error_handler.py
class AppError(Exception):
    status = 500
    message = "Erro interno"

class NotFoundError(AppError):
    status, message = 404, "Recurso não encontrado"

class ValidationError(AppError):
    status, message = 400, "Dados inválidos"

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _app_error(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status

    @app.errorhandler(Exception)
    def _unexpected(err):
        app.logger.exception("Erro não tratado")          # detalhe no log
        return jsonify({"erro": "Erro interno", "sucesso": False}), 500
```
```python
# controller: sem try/except — levanta exceção de domínio
produto = self._model.get(id)
if not produto:
    raise NotFoundError("Produto não encontrado")
```

**Node:** `next(err)` nos controllers e, registrado **por último**,
`app.use((err, req, res, next) => { logger.error(err); res.status(err.status ?? 500).json({ error: err.expose ? err.message : 'Erro interno' }); })`.

Regra: mensagem interna vai para o log, nunca para o cliente. Preserve os códigos de status que
a API já devolvia (o baseline valida isso). Erro de callback nunca é ignorado — `if (err) return next(err)`.

## RP-09 — Desaninhar callback hell

**Antes** (5 níveis, erro tratado de forma diferente em cada um):
```js
this.db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
    this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
        this.db.run("INSERT INTO enrollments ...", [...], function (err) {
            self.db.run("INSERT INTO payments ...", [...], function (err) {
                self.db.run("INSERT INTO audit_logs ...", [...], (err) => { res.json(...); });
            });
        });
    });
});
```

**Depois:**
```js
// src/database/promisify.js
const { promisify } = require('util');
const wrap = (db) => ({
    get: promisify(db.get.bind(db)),
    all: promisify(db.all.bind(db)),
    run: (sql, params = []) => new Promise((resolve, reject) =>
        db.run(sql, params, function (err) { err ? reject(err) : resolve({ lastID: this.lastID }); })),
});

// src/services/checkout.service.js — fluxo linear e legível
async execute({ name, email, password, courseId, card }) {
    const course = await this.courseRepo.findActiveById(courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');

    return withTransaction(this.db, async () => {
        const user = await this.userRepo.findByEmail(email)
                  ?? await this.userRepo.create({ name, email, password });
        const payment = await this.gateway.charge({ card, amount: course.price });
        if (payment.status !== 'PAID') throw new PaymentDeclinedError();

        const enrollment = await this.enrollmentRepo.create({ userId: user.id, courseId });
        await this.paymentRepo.create({ enrollmentId: enrollment.id, ...payment });
        await this.auditRepo.log(`Checkout curso ${courseId} por ${user.id}`);
        return { enrollmentId: enrollment.id };
    });
}
```

Ganhos: um único caminho de erro (o `throw` sobe até o middleware), transação real, e o
`let self = this` desaparece. Elimine também contador manual de pendências
(`pending--; if (pending === 0) res.json()`) — use `Promise.all`.

## RP-10 — Eliminar N+1

**Antes** (1 + N + N×M queries):
```python
for row in pedidos:
    itens = db.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"])).fetchall()
    for item in itens:
        prod = db.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"])).fetchone()
```

**Depois — SQL cru, um JOIN:**
```python
rows = conn.execute("""
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
      FROM pedidos p
      LEFT JOIN itens_pedido i ON i.pedido_id = p.id
      LEFT JOIN produtos pr    ON pr.id = i.produto_id
     WHERE (? IS NULL OR p.usuario_id = ?)
     ORDER BY p.id
""", (usuario_id, usuario_id)).fetchall()
return self._group_by_pedido(rows)          # agrupa em memória, 1 query
```

**Depois — ORM, eager loading:**
```python
from sqlalchemy.orm import joinedload
tasks = db.session.execute(
    select(Task).options(joinedload(Task.user), joinedload(Task.category))
).unique().scalars().all()

# contagens agregadas em uma query, em vez de count() por item
counts = dict(db.session.execute(
    select(Task.status, func.count()).group_by(Task.status)
).all())
```

**Node:** troque a cascata de callbacks por um `JOIN` no repository; quando precisar de várias
consultas independentes, `Promise.all` em vez de sequência.

Também vale: `len(user.tasks)` (lazy load por usuário) → `func.count` agrupado; `count()` por
categoria → um `GROUP BY`.

## RP-11 — Unificar validação em um único ponto

**Antes** — regras repetidas e divergentes entre create e update:
```python
if len(title) < 3: ...          # em create
if len(data['title']) < 3: ...  # em update, sem a checagem de máximo
if status not in ['pending', 'in_progress', 'done', 'cancelled']: ...   # lista repetida 4x
```

**Depois:**
```python
# src/models/task.py (ou src/validators/task_validator.py)
VALID_STATUSES = ("pending", "in_progress", "done", "cancelled")
TITLE_MIN, TITLE_MAX = 3, 200
PRIORITY_MIN, PRIORITY_MAX = 1, 5

def validate_task_payload(data, partial=False):
    """Retorna (dados_normalizados, erros). partial=True para PATCH/PUT."""
    errors = {}
    out = {}
    if "title" in data or not partial:
        title = (data.get("title") or "").strip()
        if not TITLE_MIN <= len(title) <= TITLE_MAX:
            errors["title"] = f"deve ter entre {TITLE_MIN} e {TITLE_MAX} caracteres"
        else:
            out["title"] = title
    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            errors["status"] = f"deve ser um de {', '.join(VALID_STATUSES)}"
        else:
            out["status"] = data["status"]
    ...
    return out, errors
```
```python
# controller — uma linha, mesma regra nos dois endpoints
payload, errors = validate_task_payload(body, partial=True)
if errors:
    raise ValidationError(errors)
```

Se o projeto já declara constantes/validadores em `utils/` sem usar (AP-13), **importe-os** em vez
de reescrever. Alternativa idiomática: schema declarativo (marshmallow/pydantic/zod/joi) —
prefira essa via se a dependência já estiver no manifesto. Valide também tipo e formato, não só
presença (e-mail com TLD, número realmente numérico, faixa).

## RP-12 — Substituir print por logger

**Antes:** `print("Produto criado com ID: " + str(id))`, `console.log(\`Processando cartão ${cc}\`)`

**Depois (Python):**
```python
# src/config/logging.py
import logging, os

def configure_logging(app):
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    app.logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# uso
logger = logging.getLogger(__name__)
logger.info("Produto criado", extra={"produto_id": produto_id})
```

**Depois (Node):** logger injetado (`pino`/`winston`) ou wrapper mínimo com nível por
`process.env.LOG_LEVEL`; nível `error` no middleware de erro.

**Nunca logue** número de cartão, senha, token ou chave de API — se o `print` original fazia
isso, o finding é CRITICAL e a correção é remover o dado, não só trocar o mecanismo:
```js
logger.info('Processando pagamento', { courseId, cardLast4: card.slice(-4) });
```

## RP-13 — Nomear constantes e variáveis

**Antes:**
```python
if faturamento > 10000:  desconto = faturamento * 0.1
elif faturamento > 5000: desconto = faturamento * 0.05
```
```js
let status = cc.startsWith("4") ? "PAID" : "DENIED";
let u = req.body.usr, e = req.body.eml, cc = req.body.card;
```

**Depois:**
```python
# src/models/pedido_model.py — a política fica declarada, não escondida em literais
FAIXAS_DESCONTO = (
    (10_000, 0.10),
    ( 5_000, 0.05),
    ( 1_000, 0.02),
)

def calcular_desconto(faturamento):
    for minimo, taxa in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return round(faturamento * taxa, 2)
    return 0.0
```
```js
const { name, email, password, courseId, card } = req.body;   // nomes do domínio
const VISA_PREFIX = '4';
```
Renomeie também parâmetros que sombreiam builtin (`id` → `produto_id`), variáveis de uma letra
fora de laço trivial, e contadores enumerados (`p1..p5` → dicionário por prioridade). Mantenha
**um** idioma por projeto; se o legado é em português, siga em português — consistência importa
mais que preferência.

## RP-14 — Proteger rota administrativa

**Antes:** `POST /admin/query` executa SQL arbitrário; `POST /admin/reset-db` apaga tudo;
`GET /api/admin/financial-report` aberto.

**Depois:**
1. **Remova** o que não tem razão de existir em produção — endpoint de SQL arbitrário não se
   protege, se elimina (é backdoor por design). Registre a remoção no relatório final.
2. Operações destrutivas legítimas (reset de banco de desenvolvimento) migram para comando de
   CLI/script, fora da superfície HTTP.
3. O que precisa continuar exposto ganha middleware de autenticação **e** autorização:

```python
# src/middlewares/auth.py
from functools import wraps
from flask import request

def require_role(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = authenticate(request.headers.get("Authorization"))
            if user is None:
                raise UnauthorizedError()
            if user["role"] not in roles:
                raise ForbiddenError()
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# views
admin_bp.add_url_rule("/relatorios/vendas", view_func=require_role("admin")(controller.vendas))
```
```js
router.get('/admin/financial-report', requireRole('admin'), controller.financialReport);
```

Token de sessão precisa ser verificável (assinatura/JWT ou consulta a sessão) — `'fake-jwt-token-' + id`
não é autenticação. Se implementar auth de verdade estiver fora do escopo da refatoração,
registre a rota como "protegida por middleware pendente de integração" e deixe o middleware no
lugar, negando por padrão — nunca deixe aberto silenciosamente.

## RP-15 — Substituir API deprecated

```python
# antes                                    # depois
datetime.utcnow()                          datetime.now(timezone.utc)
Task.query.get(task_id)                    db.session.get(Task, task_id)
Task.query.filter_by(status=s).all()       db.session.scalars(select(Task).where(Task.status == s)).all()
@app.before_first_request                  # mover para o factory, dentro de app_context()
```
```js
// antes                                   // depois
new Buffer(data)                           Buffer.from(data)
url.parse(req.url)                         new URL(req.url, `http://${req.headers.host}`)
crypto.createCipher(...)                   crypto.createCipheriv(...)
app.use(bodyParser.json())                 app.use(express.json())
Model.update({...})                        Model.updateOne({...})
```

Cuidado com a semântica, não só com a assinatura: `utcnow()` devolve datetime **naive** e
`now(timezone.utc)` devolve **aware** — comparar os dois levanta `TypeError`. Ao trocar, troque
**todas** as ocorrências do fluxo (colunas `default=`, comparações, serialização) e escolha uma
convenção única de fuso para o projeto. Depois de migrar, rode a aplicação com avisos ligados
(`python -W all`, `node --pending-deprecation`) e confirme que o warning desapareceu.

## RP-16 — Remover código morto e centralizar serialização

**Antes** — o mesmo `row → dict` em 6 lugares e imports não usados:
```python
import sqlite3, os, sys, json      # nenhum usado neste arquivo
result.append({"id": row["id"], "nome": row["nome"], ...})   # repetido 6x
```

**Depois:**
```python
# src/models/produto_model.py — uma única definição de forma pública
FIELDS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")

def _to_dict(row):
    return {field: row[field] for field in FIELDS}
```

Passe a limpar, na ordem: (1) import não usado; (2) função/classe definida e nunca chamada
(confirme com `grep` do símbolo no projeto inteiro antes de apagar); (3) export inútil;
(4) laço sem efeito (ex.: 10.000 iterações de hash caseiro que será substituído por bcrypt);
(5) dependência declarada no manifesto e não usada; (6) arquivo legado que ficou vazio após a
migração. Simplifique também `if/else` que devolve booleano (`return cond`) e
`type(x) == list` → `isinstance(x, list)`.

**Cuidado:** símbolo aparentemente morto pode ser ponto de extensão usado por reflexão,
plugin ou nome dinâmico. Ausência de referência textual em projeto pequeno é evidência
suficiente; em projeto com carregamento dinâmico, verifique antes.
