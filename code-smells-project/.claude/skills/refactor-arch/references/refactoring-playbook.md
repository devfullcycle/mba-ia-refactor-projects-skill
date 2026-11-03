# Playbook de Refatoração (Fase 3)

Cada padrão (PB-xx) corrige um ou mais anti-patterns do catálogo (AP-xx) e traz exemplos **antes/depois** em Python e/ou JavaScript. Adapte nomes ao domínio do projeto, mas mantenha a ideia.

| PB | Transformação | Corrige |
|---|---|---|
| PB-01 | Queries parametrizadas | AP-01 |
| PB-02 | Configuração via ambiente | AP-02, AP-12 |
| PB-03 | Decompor God Class/File em camadas MVC | AP-03 |
| PB-04 | Serialização segura e mascaramento de logs | AP-04 |
| PB-05 | Guard para endpoints administrativos | AP-05 |
| PB-06 | Hash de senha seguro + migração de legado | AP-06 |
| PB-07 | Extrair regra de negócio para Controller/Model | AP-07 |
| PB-08 | Eliminar estado global mutável | AP-08 |
| PB-09 | Composition root + Injeção de Dependência | AP-09 |
| PB-10 | async/await + transação atômica | AP-10 |
| PB-11 | Token assinado com expiração | AP-11 |
| PB-12 | Eliminar N+1 (JOIN / GROUP BY / eager load) | AP-13 |
| PB-13 | Validators centralizados | AP-14 |
| PB-14 | Exceções de domínio + error handler central | AP-15 |
| PB-15 | Extrair função única (DRY) | AP-16 |
| PB-16 | Deleção em cascata transacional | AP-17 |
| PB-17 | Substituir APIs deprecated | AP-18 |
| PB-18 | Constantes nomeadas | AP-19 |
| PB-19 | Renomear e remover código morto | AP-20, AP-21 |
| PB-20 | Logger estruturado | AP-22 |

---

## PB-01 — Queries parametrizadas (AP-01)

**Antes (Python / sqlite3)**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
query += " AND (nome LIKE '%" + termo + "%')"
```
**Depois**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))

clauses, params = ["1=1"], []
if termo:
    clauses.append("(nome LIKE ? OR descricao LIKE ?)")
    params += [f"%{termo}%", f"%{termo}%"]
cursor.execute(f"SELECT * FROM produtos WHERE {' AND '.join(clauses)}", params)  # só placeholders interpolados
```
**JS (sqlite3)**: `db.get("SELECT * FROM users WHERE email = ?", [email])` — nunca template literal com dados.
Regra: interpolação só é aceitável para **fragmentos fixos do código** (nomes de colunas de uma whitelist), nunca para valores.

## PB-02 — Configuração via ambiente (AP-02, AP-12)

**Antes**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.run(host="0.0.0.0", port=5000, debug=True)
```
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_123", port: 3000 };
```
**Depois**
```python
# src/config/settings.py
import os, secrets

def _bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)  # dev: efêmero
    DEBUG = _bool("FLASK_DEBUG", False)
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
```
```js
// src/config/index.js
module.exports = Object.freeze({
  port: Number(process.env.PORT) || 3000,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  db: { user: process.env.DB_USER || '', pass: process.env.DB_PASS || '' },
});
```
E criar `.env.example` listando as variáveis **sem valores reais**.

## PB-03 — Decompor God Class/File (AP-03)

**Antes (JS)**
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initDb() { /* CREATE TABLE + seeds */ }
  setupRoutes(app) { app.post('/api/checkout', (req, res) => { /* SQL + regras + pagamento */ }); }
}
```
**Depois**
```
src/database/connection.js   -> createDatabase(), helpers async
src/database/schema.js       -> createSchema(db), seed(db)
src/models/courseModel.js    -> findActiveById(id)
src/services/paymentService.js -> charge(card, amount)
src/controllers/checkoutController.js -> checkout(input)
src/views/checkoutRoutes.js  -> router.post('/api/checkout', ...)
src/app.js                   -> composition root
```
Passos: (1) mover schema/seed; (2) criar um Model por tabela/agregado com as queries; (3) para cada rota, mover o corpo para um método de Controller que recebe dados puros; (4) a rota só extrai `req` e chama o controller; (5) apagar a classe antiga.

## PB-04 — Serialização segura e mascaramento (AP-04)

**Antes**
```python
return {"id": row["id"], "email": row["email"], "senha": row["senha"]}
```
```python
"secret_key": "minha-chave-super-secreta-123", "debug": True   # no /health
```
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```
**Depois**
```python
PUBLIC_FIELDS = ("id", "nome", "email", "tipo", "criado_em")
def to_public_dict(row):
    return {field: row[field] for field in PUBLIC_FIELDS}
```
```python
return {"status": "ok", "database": "connected", "counts": counts, "versao": APP_VERSION}
```
```js
const maskCard = (card) => `**** **** **** ${String(card).slice(-4)}`;
logger.info(`Processando pagamento do cartão ${maskCard(card)}`);
```

## PB-05 — Guard para endpoints administrativos (AP-05)

**Antes**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json()["sql"])
```
**Depois**
```python
# src/middlewares/auth.py
import hmac
from functools import wraps
from flask import current_app, request
from src.utils.errors import ForbiddenError, UnauthorizedError

def require_admin_token(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN")
        if not expected:
            raise ForbiddenError("Endpoint administrativo desabilitado")
        provided = request.headers.get("X-Admin-Token", "")
        if not hmac.compare_digest(provided, expected):
            raise UnauthorizedError("Token administrativo inválido")
        return view(*args, **kwargs)
    return wrapper
```
Endpoints de SQL arbitrário: além do guard, restringir a **uma única instrução `SELECT`** somente leitura (ou removê-los, documentando). Express: `router.get('/api/admin/x', requireAdmin, handler)`.

## PB-06 — Hash de senha seguro + migração (AP-06)

**Antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```
```js
function badCrypto(pwd) { let h = ""; for (let i = 0; i < 10000; i++) h += Buffer.from(pwd).toString('base64').substring(0, 2); return h.substring(0, 10); }
```
**Depois (Python — werkzeug já vem com Flask)**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, raw):
    self.password = generate_password_hash(raw)

def check_password(self, raw):
    if self.password and len(self.password) == 32 and ":" not in self.password:   # hash MD5 legado
        if hmac.compare_digest(self.password, hashlib.md5(raw.encode()).hexdigest()):
            self.set_password(raw)   # migra para o hash forte no primeiro login
            return True
        return False
    return check_password_hash(self.password, raw)
```
**Depois (Node — `crypto` nativo)**
```js
const crypto = require('crypto');
function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(password, salt, 64).toString('hex');
  return `scrypt$${salt}$${hash}`;
}
function verifyPassword(password, stored) {
  const [, salt, hash] = stored.split('$');
  const candidate = crypto.scryptSync(password, salt, 64);
  return crypto.timingSafeEqual(candidate, Buffer.from(hash, 'hex'));
}
```
Nunca atribua senha padrão silenciosamente — retorne 400.

## PB-07 — Extrair regra de negócio (AP-07)

**Antes (rota gorda)**
```python
@report_bp.route('/reports/user/<int:user_id>')
def user_report(user_id):
    tasks = Task.query.filter_by(user_id=user_id).all()
    done = 0
    for t in tasks:
        if t.status == 'done': done += 1
        ...
    return jsonify({...}), 200
```
**Depois**
```python
# models/task.py
def is_overdue(self, now=None): ...

# controllers/report_controller.py
class ReportController:
    def user_report(self, user_id):
        user = self._users.get_or_404(user_id)
        tasks = self._tasks.by_user(user_id)
        return {"user": user.to_summary(), "statistics": TaskStatistics.from_tasks(tasks)}

# routes/report_routes.py
@bp.get('/reports/user/<int:user_id>')
def user_report(user_id):
    return jsonify(controller.user_report(user_id)), 200
```
Side-effects (e-mail, SMS, push) saem do handler e vão para um Service chamado pelo controller.

## PB-08 — Eliminar estado global mutável (AP-08)

**Antes**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
    return db_connection
```
```js
let globalCache = {};
function logAndCache(key, data) { globalCache[key] = data; }
```
**Depois**
```python
from flask import current_app, g

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
```
```js
class CacheService {
  constructor() { this.store = new Map(); }
  set(key, value) { this.store.set(key, value); }
  get(key) { return this.store.get(key); }
}
// instanciado uma vez no composition root e injetado onde for necessário
```

## PB-09 — Composition root + DI (AP-09)

**Antes**
```python
# controllers.py
import models
from database import get_db
def health_check():
    db = get_db(); ...
```
**Depois**
```python
# src/app.py
def create_app(config=Settings):
    app = Flask(__name__)
    app.config.from_object(config)
    database.init_app(app)

    produto_model = ProdutoModel(database.get_db)
    notifier = NotificationService(logger)
    produto_controller = ProdutoController(produto_model)
    pedido_controller = PedidoController(PedidoModel(database.get_db), produto_model, notifier)

    app.register_blueprint(create_produto_routes(produto_controller))
    app.register_blueprint(create_pedido_routes(pedido_controller))
    register_error_handlers(app)
    return app
```
```js
// src/app.js
const db = await createDatabase(config.databaseUrl);
const courseModel = new CourseModel(db);
const checkoutController = new CheckoutController({ db, courseModel, userModel, paymentService });
app.use(createCheckoutRoutes(checkoutController));
```

## PB-10 — async/await + transação (AP-10)

**Antes**
```js
db.get(q1, [cid], (err, course) => {
  db.get(q2, [e], (err, user) => {
    db.run(q3, [...], function (err) {
      self.db.run(q4, [...], function (err) { /* ... */ });
    });
  });
});
```
**Depois**
```js
// src/database/connection.js — wrapper Promise
const run = (sql, params = []) => new Promise((resolve, reject) =>
  db.run(sql, params, function (err) { err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes }); }));

async function transaction(work) {
  await run('BEGIN');
  try { const result = await work(); await run('COMMIT'); return result; }
  catch (err) { await run('ROLLBACK'); throw err; }
}

// controller
const enrollmentId = await db.transaction(async () => {
  const { lastID } = await enrollments.create(userId, course.id);
  await payments.create(lastID, course.price, 'PAID');
  await auditLogs.record(`Checkout curso ${course.id} por ${userId}`);
  return lastID;
});
```
**Python (sqlite3)**: `with conn:` (commit/rollback automático) ou `try: ... conn.commit() except: conn.rollback(); raise`. Valide **tudo** (estoque, existência) antes de escrever.

## PB-11 — Token assinado (AP-11)

**Antes**
```python
'token': 'fake-jwt-token-' + str(user.id)
```
**Depois (itsdangerous já é dependência do Flask)**
```python
from itsdangerous import URLSafeTimedSerializer

class TokenService:
    def __init__(self, secret_key, max_age_seconds=3600):
        self._serializer = URLSafeTimedSerializer(secret_key, salt="auth-token")
        self._max_age = max_age_seconds
    def issue(self, user):
        return self._serializer.dumps({"user_id": user.id, "role": user.role})
    def verify(self, token):
        return self._serializer.loads(token, max_age=self._max_age)
```
Node: `jsonwebtoken` (se já for dependência) ou `crypto.createHmac('sha256', secret)`.

## PB-12 — Eliminar N+1 (AP-13)

**Antes (sqlite3)**
```python
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
**Depois**
```python
rows = db.execute("""
    SELECT p.id AS pedido_id, i.produto_id, i.quantidade, i.preco_unitario,
           COALESCE(pr.nome, 'Desconhecido') AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    WHERE (? IS NULL OR p.usuario_id = ?)
    ORDER BY p.id, i.id""", (usuario_id, usuario_id)).fetchall()
# agrupar em Python por pedido_id
```
**Depois (SQLAlchemy)**
```python
from sqlalchemy.orm import joinedload
tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()

counts = dict(db.session.query(Task.status, db.func.count(Task.id)).group_by(Task.status).all())
```
**Depois (JS)** — um único `SELECT ... FROM courses LEFT JOIN enrollments LEFT JOIN users LEFT JOIN payments` e agregação em memória, eliminando contadores manuais de callbacks.

## PB-13 — Validators centralizados (AP-14)

**Antes**
```python
if "nome" not in dados: return jsonify({"erro": "Nome é obrigatório"}), 400
if preco < 0: ...           # repetido em criar e atualizar; TypeError se preco for string
```
**Depois**
```python
# src/validators/produto_validator.py
def validate_produto(dados):
    if not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    for campo, msg in (("nome", "Nome é obrigatório"), ("preco", "Preço é obrigatório"), ("estoque", "Estoque é obrigatório")):
        if campo not in dados:
            raise ValidationError(msg)
    if not isinstance(dados["preco"], (int, float)) or dados["preco"] < 0:
        raise ValidationError("Preço não pode ser negativo")
    ...
    return ProdutoInput(...)
```
Use a **mesma ordem de checagem e as mesmas mensagens** da API original para preservar o contrato. Use `request.get_json(silent=True)` para que JSON ausente vire 400, não 500.

## PB-14 — Exceções de domínio + error handler central (AP-15)

**Antes**
```python
def listar_produtos():
    try:
        ...
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```
**Depois**
```python
# src/utils/errors.py
class AppError(Exception):
    status_code = 500
    def __init__(self, message, status_code=None):
        super().__init__(message); self.message = message
        if status_code: self.status_code = status_code
class ValidationError(AppError): status_code = 400
class UnauthorizedError(AppError): status_code = 401
class ForbiddenError(AppError): status_code = 403
class NotFoundError(AppError): status_code = 404
class ConflictError(AppError): status_code = 409

# src/middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            return jsonify({"erro": err.description}), err.code
        app.logger.exception("Erro inesperado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
```
```js
// src/middlewares/errorHandler.js
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
function errorHandler(err, req, res, _next) {
  if (err instanceof AppError) return res.status(err.statusCode).send(err.message);
  console.error(err);
  res.status(500).send('Erro interno');
}
```

## PB-15 — Extrair função única (AP-16)

**Antes** (lógica de "atrasada" repetida em 5 rotas)
```python
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            task_data['overdue'] = True
```
**Depois**
```python
# models/task.py
CLOSED_STATUSES = frozenset({"done", "cancelled"})
def is_overdue(self, now=None):
    now = now or utcnow()
    return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

# em qualquer lugar
data["overdue"] = task.is_overdue()
```

## PB-16 — Deleção em cascata transacional (AP-17)

**Antes**
```js
db.run("DELETE FROM users WHERE id = ?", [id], () => res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."));
```
**Depois**
```js
await db.transaction(async () => {
  await db.run('DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)', [id]);
  await db.run('DELETE FROM enrollments WHERE user_id = ?', [id]);
  await db.run('DELETE FROM users WHERE id = ?', [id]);
});
```
SQLAlchemy: `db.relationship(..., cascade="all, delete-orphan")` ou deleção explícita em uma única transação. Para categorias, desassocie (`category_id = NULL`) em vez de apagar tasks.

## PB-17 — Substituir APIs deprecated (AP-18)

```python
# Antes
datetime.utcnow()
Task.query.get(task_id)
# Depois
from datetime import datetime, timezone
def utcnow():
    """UTC naive — compatível com colunas DateTime sem timezone."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
db.session.get(Task, task_id)
```
```js
// Antes
new Buffer(pwd); url.parse(req.url); str.substr(0, 2)
// Depois
Buffer.from(pwd); new URL(req.url, base); str.slice(0, 2)
```
Atenção: trocar `utcnow()` por `datetime.now(timezone.utc)` **com** tzinfo quebra comparações com datas *naive* vindas do banco (`TypeError: can't compare offset-naive and offset-aware`) — use o helper acima.

## PB-18 — Constantes nomeadas (AP-19)

**Antes**
```python
if faturamento > 10000: desconto = faturamento * 0.1
elif faturamento > 5000: desconto = faturamento * 0.05
```
**Depois**
```python
# models/pedido.py
DISCOUNT_TIERS = ((10000, 0.10), (5000, 0.05), (1000, 0.02))  # (faturamento mínimo exclusivo, taxa)

def calcular_desconto(faturamento):
    for minimo, taxa in DISCOUNT_TIERS:
        if faturamento > minimo:
            return faturamento * taxa
    return 0
```
Listas de valores válidos (`STATUS_VALIDOS`, `CATEGORIAS_VALIDAS`, `VALID_ROLES`) e limites (`MIN_TITLE_LENGTH`) vivem no Model da entidade.

## PB-19 — Renomear e remover código morto (AP-20, AP-21)

**Antes**
```js
let u = req.body.usr; let e = req.body.eml; let p = req.body.pwd; let cid = req.body.c_id; let cc = req.body.card;
```
```python
import os, sys, json, time   # nenhum usado
```
**Depois**
```js
const { usr: name, eml: email, pwd: password, c_id: courseId, card } = req.body;  // contrato preservado
```
Remova imports não usados, funções nunca chamadas e exports mortos (confirme com `grep -rn`).

## PB-20 — Logger estruturado (AP-22)

**Antes**
```python
print("ENVIANDO EMAIL: Pedido " + str(pedido_id) + " criado")
```
**Depois**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Notificação de pedido criado enviada", extra={"pedido_id": pedido_id})
```
Configure `logging.basicConfig(level=...)` no composition root (nível vindo da config). Em Node, centralize em `src/utils/logger.js` (wrapper de `console` com níveis) para poder trocar por `pino`/`winston` depois.
