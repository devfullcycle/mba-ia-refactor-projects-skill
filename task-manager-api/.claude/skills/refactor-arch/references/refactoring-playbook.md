# Refactoring Playbook (Phase 3)

Concrete transformations, each with **before/after** code. Python and JavaScript examples are given; apply the same idea with the idioms of any other stack. The `Fixes` line maps to catalog IDs.

| ID | Transformation | Fixes |
|---|---|---|
| T-01 | Extract configuration and secrets to env-based config | AP-01, AP-12 |
| T-02 | Parameterized queries | AP-02 |
| T-03 | Split God class/module into Model / Controller / View | AP-03 |
| T-04 | Move business logic from routes into controllers | AP-07, AP-15 |
| T-05 | Composition root + dependency injection | AP-08, AP-18 |
| T-06 | Replace global mutable state with scoped resources | AP-09 |
| T-07 | Centralized error handling with domain errors | AP-16, AP-06 (error text) |
| T-08 | Eliminate N+1 queries | AP-13 |
| T-09 | Secure password hashing (with transparent legacy upgrade) | AP-05 |
| T-10 | Remove sensitive data from responses and logs | AP-06 |
| T-11 | Transactions and referential integrity | AP-10 |
| T-12 | Callback hell → async/await | AP-11 |
| T-13 | Replace deprecated APIs | AP-17 |
| T-14 | Centralized input validation | AP-14 |
| T-15 | Named constants / enums for magic values | AP-19, AP-15 |
| T-16 | Hygiene: logging, naming, dead code, idioms | AP-20 – AP-23 |
| T-17 | Protect administrative, destructive and privilege endpoints (every operation named in the AP-04 Recommendation) | AP-04, AP-12 (fake auth) |

---

## T-01 Extract configuration and secrets

**Before (Python):**
```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
...
app.run(host="0.0.0.0", port=5000, debug=True)
```
**After:**
```python
# src/config/settings.py
import os, secrets, logging
from dataclasses import dataclass

def _bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes")

@dataclass(frozen=True)
class Settings:
    secret_key: str
    debug: bool
    host: str
    port: int
    database_path: str

def load_settings() -> Settings:
    secret = os.environ.get("SECRET_KEY")
    if not secret:
        secret = secrets.token_hex(32)
        logging.getLogger(__name__).warning("SECRET_KEY not set; using a random ephemeral key")
    return Settings(
        secret_key=secret,
        debug=_bool("FLASK_DEBUG", False),
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        database_path=os.environ.get("DATABASE_PATH", "loja.db"),
    )
```
**Before (JS):**
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_123", port: 3000 };
```
**After:**
```js
// src/config/index.js
const config = Object.freeze({
  port: Number(process.env.PORT || 3000),
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',   // empty in dev; required in prod
  dbPath: process.env.DB_PATH || ':memory:',
});
module.exports = config;
```
Add every variable to `.env.example`.

---

## T-02 Parameterized queries

**Before:**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
query += " AND categoria = '" + categoria + "'"
```
**After:**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))

clauses, params = ["1=1"], []
if termo:
    clauses.append("(nome LIKE ? OR descricao LIKE ?)")
    params += [f"%{termo}%", f"%{termo}%"]
if categoria:
    clauses.append("categoria = ?")
    params.append(categoria)
cursor.execute(f"SELECT * FROM produtos WHERE {' AND '.join(clauses)}", params)  # only placeholders interpolated
```
**JS:**
```js
// before
db.all(`SELECT * FROM users WHERE email = '${email}'`);
// after
db.all('SELECT * FROM users WHERE email = ?', [email]);
```

---

## T-03 Split a God class/module into MVC

**Before (one class does everything):**
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initDb() { /* CREATE TABLE ... INSERT seed ... */ }
  setupRoutes(app) {
    app.post('/api/checkout', (req, res) => { /* validation + SQL + payment + audit + response */ });
  }
}
```
**After (one responsibility per module):**
```js
// models/courseModel.js
class CourseModel {
  constructor(db) { this.db = db; }
  findActiveById(id) { return this.db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]); }
}
// controllers/checkoutController.js
class CheckoutController {
  constructor({ courses, users, enrollments, paymentGateway }) { Object.assign(this, { courses, users, enrollments, paymentGateway }); }
  async checkout(input) { /* business flow only, throws domain errors */ }
}
// routes/checkoutRoutes.js
router.post('/checkout', asyncHandler(async (req, res) => {
  const result = await checkoutController.checkout(parseCheckoutBody(req.body));
  res.status(200).json(result);
}));
```
Python equivalent: split `models.py` into `models/produto_model.py`, `models/usuario_model.py`, `models/pedido_model.py`; rules from `models.py`/`controllers.py` move into `controllers/*_controller.py`; `add_url_rule` table moves to `views/*_routes.py` blueprints.

---

## T-04 Move business logic out of routes

**Before:**
```python
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    for t in tasks:
        ...
        if t.due_date:
            if t.due_date < datetime.utcnow():
                if t.status != 'done' and t.status != 'cancelled':
                    task_data['overdue'] = True
```
**After:**
```python
# models/task.py
def is_overdue(self, now=None):
    now = now or utcnow()
    return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

# controllers/task_controller.py
class TaskController:
    def __init__(self, repo): self.repo = repo
    def list_tasks(self):
        return [present_task(t, with_relations=True) for t in self.repo.list_with_relations()]

# views/task_routes.py
@bp.get("/tasks")
def list_tasks():
    return jsonify(controller().list_tasks()), 200
```
The rule now exists once, in the model, and every endpoint reuses it.

---

## T-05 Composition root and dependency injection

**Before:**
```python
# every module
from database import get_db          # concrete global
import controllers                    # routes bound at import time
app = Flask(__name__)                 # side effects on import
```
**After:**
```python
# src/app.py
def create_app(settings=None):
    settings = settings or load_settings()
    app = Flask(__name__)
    app.config.update(SECRET_KEY=settings.secret_key, DEBUG=settings.debug)
    db = Database(settings.database_path); db.init_app(app)
    produtos = ProdutoController(ProdutoModel(db))
    app.register_blueprint(build_produto_routes(produtos))
    register_error_handlers(app)
    return app
```
```js
// src/app.js
function createApp(deps) {
  const app = express();
  app.use(express.json());
  app.use('/api', buildCheckoutRoutes(deps.checkoutController));
  app.use(errorHandler);
  return app;
}
```
Infra (emails, payment, cache) becomes an injected adapter in `services/`, so tests can pass a fake.

---

## T-06 Replace global mutable state

**Before:**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
    return db_connection
```
**After (one connection per request, closed on teardown):**
```python
class Database:
    def __init__(self, path): self.path = path
    def connection(self):
        if "db" not in g:
            g.db = sqlite3.connect(self.path)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db
    def close(self, _exc=None):
        conn = g.pop("db", None)
        if conn is not None: conn.close()
    def init_app(self, app):
        app.teardown_appcontext(self.close)
```
**JS:** replace `let globalCache = {}` exported from utils with a `CacheService` instance created in the composition root and injected where needed.

---

## T-07 Centralized error handling

**Before:**
```python
def buscar_produto(id):
    try:
        ...
        return jsonify({"erro": "Produto não encontrado"}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```
**After:**
```python
# controllers/errors.py
class AppError(Exception):
    status_code = 400
    def __init__(self, message): super().__init__(message); self.message = message
class NotFoundError(AppError): status_code = 404

# middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code
    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException): return err          # keep 404/405 from Flask
        app.logger.exception("Unhandled error")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500

# controller
def obter(self, produto_id):
    produto = self.model.find_by_id(produto_id)
    if produto is None: raise NotFoundError("Produto não encontrado")
    return produto
```
**JS:**
```js
// middlewares/asyncHandler.js
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
// middlewares/errorHandler.js
module.exports = (err, req, res, next) => {
  if (err instanceof AppError) return res.status(err.statusCode).send(err.message);
  console.error(err);
  res.status(500).send('Erro interno');
};
```

---

## T-08 Eliminate N+1 queries

**Before (1 + N + N·M queries):**
```python
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
**After (2 queries total):**
```python
pedidos = conn.execute("SELECT * FROM pedidos ORDER BY id").fetchall()
itens = conn.execute("""
    SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario,
           COALESCE(p.nome, 'Desconhecido') AS produto_nome
    FROM itens_pedido i LEFT JOIN produtos p ON p.id = i.produto_id
    ORDER BY i.id""").fetchall()
by_order = defaultdict(list)
for i in itens: by_order[i["pedido_id"]].append(dict(i))
```
**ORM:** `Task.query.options(joinedload(Task.user), joinedload(Task.category))`; counts with one `GROUP BY`:
```python
rows = db.session.execute(db.select(Task.status, func.count()).group_by(Task.status)).all()
```
**JS (report):** one `JOIN` query, then group in memory:
```js
const rows = await db.all(`
  SELECT c.id AS course_id, c.title, u.name AS student, p.amount, p.status
  FROM courses c
  LEFT JOIN enrollments e ON e.course_id = c.id
  LEFT JOIN users u ON u.id = e.user_id
  LEFT JOIN payments p ON p.enrollment_id = e.id
  ORDER BY c.id, e.id`);
```

---

## T-09 Secure password hashing

**Before:**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```
```js
function badCrypto(pwd) { let h = ""; for (...) h += Buffer.from(pwd).toString('base64').substring(0, 2); return h.substring(0, 10); }
```
**After (Python — Werkzeug ships with Flask, no new dependency):**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, raw): self.password = generate_password_hash(raw)
def check_password(self, raw):
    if self.password.startswith(("scrypt:", "pbkdf2:")):
        return check_password_hash(self.password, raw)
    # legacy MD5/plaintext row: verify once, then upgrade transparently
    legacy_ok = self.password in (raw, hashlib.md5(raw.encode()).hexdigest())
    if legacy_ok: self.set_password(raw)
    return legacy_ok
```
**After (Node — built-in `crypto.scrypt`):**
```js
const crypto = require('crypto');
function hashPassword(pwd) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(pwd, salt, 64).toString('hex');
  return `scrypt$${salt}$${hash}`;
}
function verifyPassword(pwd, stored) {
  const [, salt, hash] = stored.split('$');
  const candidate = crypto.scryptSync(pwd, salt, 64);
  return crypto.timingSafeEqual(candidate, Buffer.from(hash, 'hex'));
}
```
Login must query by email only and verify the hash in code — never `WHERE senha = ?`.

---

## T-10 Remove sensitive data from responses and logs

**Before:**
```python
def to_dict(self):
    return {'id': self.id, 'email': self.email, 'password': self.password}
...
"secret_key": "minha-chave-super-secreta-123", "db_path": "loja.db", "debug": True   # /health
```
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```
**After:**
```python
PUBLIC_FIELDS = ("id", "name", "email", "role", "active", "created_at")
def to_dict(self): return {f: getattr(self, f) for f in PUBLIC_FIELDS}
# /health returns only status + counts
```
```js
logger.info(`Processing card ****${card.slice(-4)}`);   // never the key, never the full PAN
```
Keep the response key set otherwise identical so clients keep working.

---

## T-11 Transactions and referential integrity

**Before:**
```python
for item in itens: check stock ...           # may `return` midway
cursor.execute("INSERT INTO pedidos ...")
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ...")
db.commit()
```
**After:**
```python
with conn:  # sqlite3: commits on success, rolls back on exception
    pedido_id = conn.execute("INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
                             (usuario_id, total)).lastrowid
    for item in itens:
        conn.execute("INSERT INTO itens_pedido (...) VALUES (?, ?, ?, ?)", (...))
        updated = conn.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                               (qtd, produto_id, qtd)).rowcount
        if updated == 0:
            raise ValidationError("Estoque insuficiente")      # rollback
```
**JS:**
```js
await db.run('BEGIN');
try { /* inserts */ await db.run('COMMIT'); } catch (e) { await db.run('ROLLBACK'); throw e; }
```
Deleting a parent: delete/cascade children inside the same transaction (or declare `FOREIGN KEY ... ON DELETE CASCADE` and enable `PRAGMA foreign_keys = ON`).

---

## T-12 Callback hell → async/await

**Before:**
```js
this.db.get(sqlA, [a], (err, course) => {
  this.db.get(sqlB, [b], (err, user) => {
    this.db.run(sqlC, [c], function (err) {
      self.db.run(sqlD, [d], function (err) { res.json(...); });
    });
  });
});
```
**After:**
```js
// models/database.js — promisified wrapper
const run = (sql, params = []) => new Promise((resolve, reject) =>
  db.run(sql, params, function (err) { err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes }); }));
const get = (sql, params = []) => new Promise((resolve, reject) =>
  db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row))));
const all = (sql, params = []) => new Promise((resolve, reject) =>
  db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows))));

// controller
const course = await courses.findActiveById(courseId);
if (!course) throw new NotFoundError('Curso não encontrado');
const user = await users.findByEmail(email);
```

---

## T-13 Replace deprecated APIs

**Before → After:**
```python
datetime.utcnow()                 →  datetime.now(timezone.utc)   # or a utcnow() helper returning naive UTC
                                                                   # if the DB column stores naive datetimes
Task.query.get(task_id)           →  db.session.get(Task, task_id)
User.query.get_or_404(id)         →  db.get_or_404(User, id)
```
```js
new Buffer(pwd)                   →  Buffer.from(pwd)
app.use(bodyParser.json())        →  app.use(express.json())
res.send(404, 'x')                →  res.status(404).send('x')
```
Keep datetime naive-vs-aware consistent with what the DB stores. For SQLite + SQLAlchemy `DateTime` (naive), use a helper:
```python
def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)
```

---

## T-14 Centralized input validation

**Before (duplicated in create and update, unsafe types):**
```python
if "preco" not in dados: return jsonify({"erro": "Preço é obrigatório"}), 400
if preco < 0: ...                      # TypeError → 500 if preco is "abc"
```
**After:**
```python
# controllers/validators.py
def require_number(data, field, label, minimum=None):
    if field not in data or data[field] is None:
        raise ValidationError(f"{label} é obrigatório")
    value = data[field]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{label} deve ser numérico")
    if minimum is not None and value < minimum:
        raise ValidationError(f"{label} não pode ser negativo")
    return value
```
Views use `request.get_json(silent=True) or {}` so a missing body becomes a 400, not a 500.

---

## T-15 Named constants / enums for magic values

**Before:**
```python
if faturamento > 10000: desconto = faturamento * 0.1
elif faturamento > 5000: desconto = faturamento * 0.05
if novo_status not in ["pendente", "aprovado", "enviado", "entregue", "cancelado"]: ...
```
**After:**
```python
# models/pedido_model.py
STATUS_VALIDOS = ("pendente", "aprovado", "enviado", "entregue", "cancelado")
# controllers/relatorio_controller.py
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))   # (faturamento mínimo, taxa)
def calcular_desconto(faturamento):
    return next((faturamento * taxa for limite, taxa in FAIXAS_DESCONTO if faturamento > limite), 0)
```
```js
const PaymentStatus = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });
```

---

## T-16 Hygiene: logging, naming, dead code, idioms

**Before:**
```python
import os, sys, json, datetime      # only datetime used
print("Produto criado com ID: " + str(id))
def is_admin(self):
    if self.role == 'admin': return True
    else: return False
if type(tags) == list: ...
```
```js
let u = req.body.usr; let e = req.body.eml; let cc = req.body.card;
```
**After:**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Produto criado id=%s", produto_id)
def is_admin(self): return self.role == ROLE_ADMIN
if isinstance(tags, list): ...
```
```js
const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;  // public field names kept
```

---

## T-17 Protect administrative, destructive and privilege endpoints

**Rule:** apply a guard to **every** operation listed in the AP-04 Recommendation of the report: same `METHOD /path`, same condition, same required role. Phase 3 does not drop or narrow any of them (SKILL.md Global rules 4–5). Pick the mechanism by what the project has:

| Situation | Mechanism |
|---|---|
| The app has users + login (or a fake token) | **17-B** signed token issued at login + `require_auth` / `require_role` guards |
| No user model, only operational/admin routes | **17-A** static admin token from env (`X-Admin-Token`) |
| Arbitrary SQL endpoint | **17-A** + read-only single `SELECT` (or remove the endpoint) |

### 17-A Admin token for operational endpoints (no user model)

**Before:**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json()["sql"])     # anyone can run any SQL
```
**After:**
```python
# middlewares/auth.py
def require_admin_token(settings):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            token = request.headers.get("X-Admin-Token", "")
            if not settings.admin_token or not hmac.compare_digest(token, settings.admin_token):
                raise ForbiddenError("Acesso negado")
            return view(*args, **kwargs)
        return wrapper
    return decorator
```
- Endpoint disabled (403) unless `ADMIN_TOKEN` is configured.
- Arbitrary SQL endpoints: restrict to a **single read-only SELECT** (reject `;`, run on a read-only connection / `PRAGMA query_only = ON`) or remove the endpoint and document it as an intentional behavior change.

### 17-B Signed login token + role guards (app with users)

**Before** (token is never checked; anyone deletes users, changes roles, deactivates accounts, or resets another user's password — including the admin's — and logs in as them):
```python
@user_bp.route('/login', methods=['POST'])
def login():
    ...
    return jsonify({'user': user.to_dict(), 'token': 'fake-jwt-token-' + str(user.id)})

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id): ...                       # no guard

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    ...
    if 'role' in data: user.role = data['role']     # privilege escalation
    if 'active' in data: user.active = data['active']
    if 'password' in data: user.set_password(data['password'])  # account takeover:
    if 'email' in data: user.email = data['email']               # reset admin's password, log in
```
**After:**
```python
# services/token_service.py — itsdangerous ships with Flask (no new dependency)
class TokenService:
    def __init__(self, secret_key, max_age):
        self._s = URLSafeTimedSerializer(secret_key, salt="auth")
        self._max_age = max_age
    def issue(self, user_id): return self._s.dumps({"uid": user_id})
    def verify(self, token):
        try: return self._s.loads(token, max_age=self._max_age)["uid"]
        except (BadSignature, SignatureExpired): return None

# middlewares/auth.py
def build_guards(tokens, users):
    def current_user():
        header = request.headers.get("Authorization", "")
        uid = tokens.verify(header[7:]) if header.startswith("Bearer ") else None
        user = users.get(uid) if uid else None
        return user if user and user.active else None

    def require_auth(view):                      # 401 when there is no valid token
        @wraps(view)
        def wrapper(*a, **kw):
            g.current_user = current_user()
            if g.current_user is None: raise UnauthorizedError("Autenticação necessária")
            return view(*a, **kw)
        return wrapper

    def require_role(*roles):                    # 403 when authenticated but not allowed
        def decorator(view):
            @wraps(view)
            @require_auth
            def wrapper(*a, **kw):
                if g.current_user.role not in roles: raise ForbiddenError("Acesso negado")
                return view(*a, **kw)
            return wrapper
        return decorator

    def optional_auth(view):                     # resolves caller for conditional guards
        @wraps(view)
        def wrapper(*a, **kw):
            g.current_user = current_user()
            return view(*a, **kw)
        return wrapper
    return require_auth, require_role, optional_auth

# views/user_routes.py — unconditional guard
@bp.delete("/users/<int:user_id>")
@require_role(ROLE_ADMIN)
def delete_user(user_id):
    controller.delete_user(user_id)
    return jsonify({"message": "Usuário deletado com sucesso"}), 200

# views/user_routes.py — conditional guard: the route stays public, the rule lives in the controller
@bp.put("/users/<int:user_id>")
@optional_auth
def update_user(user_id):
    user = controller.update_user(user_id, request.get_json(silent=True), caller=g.current_user)
    return jsonify(user.to_dict()), 200

# controllers/user_controller.py
PRIVILEGED_FIELDS = ("role", "active")        # admin only
CREDENTIAL_FIELDS = ("password", "email")     # the account owner or an admin

def update_user(self, user_id, data, caller):
    if any(f in data for f in PRIVILEGED_FIELDS):
        if caller is None: raise UnauthorizedError("Autenticação necessária")
        if caller.role != ROLE_ADMIN: raise ForbiddenError("Apenas administradores podem alterar role/active")
    if any(f in data for f in CREDENTIAL_FIELDS):
        if caller is None: raise UnauthorizedError("Autenticação necessária")
        if caller.id != user_id and caller.role != ROLE_ADMIN:
            raise ForbiddenError("Apenas o próprio usuário ou um administrador pode alterar senha/e-mail")
    ...
```
**Node/Express equivalent:**
```js
// middlewares/auth.js
const requireAuth = (tokens, users) => asyncHandler(async (req, res, next) => {
  const [, token] = (req.headers.authorization || '').split(' ');
  const userId = token && tokens.verify(token);            // HMAC-signed, crypto.createHmac
  req.user = userId ? await users.findById(userId) : null;
  if (!req.user) throw new UnauthorizedError('Autenticação necessária');
  next();
});
const requireRole = (...roles) => (req, res, next) =>
  roles.includes(req.user.role) ? next() : next(new ForbiddenError('Acesso negado'));

const requireSelfOrRole = (...roles) => (req, res, next) =>
  String(req.user.id) === req.params.id || roles.includes(req.user.role)
    ? next() : next(new ForbiddenError('Acesso negado'));

router.delete('/users/:id', requireAuth(tokens, users), requireRole('admin'), asyncHandler(...));
router.put('/users/:id/password', requireAuth(tokens, users), requireSelfOrRole('admin'), asyncHandler(...));
```

Checklist for 17-B:
- Keep the login response shape; only the `token` value changes (signed and expiring). Document it as an intentional change.
- The seed must contain at least one admin and one non-admin user, so the guards can be exercised.
- **Validation matrix**, mandatory for every guarded operation:

  | Operation | anonymous | other non-admin user | the account owner | admin token |
  |---|---|---|---|---|
  | `DELETE /users/<id>` | 401 | 403 | — | 200 (as baseline) |
  | `PUT /users/<id>` with `role`/`active` | 401 | 403 | 403 (unless admin) | 200 (as baseline) |
  | `PUT /users/<id>` with `password`/`email` | 401 | 403 | 200 (as baseline) | 200 (as baseline) |
  | `PUT /users/<id>` with other fields only | 200 (as baseline) | 200 | 200 | 200 |
  | `POST /users` with `role: "admin"` | 401 | 403 | — | 201 (as baseline) |

- **Takeover replay:** anonymously (and as another non-admin user) send `PUT /users/<admin id>` with a new `password`, then `POST /login` as the admin with that password. The PUT must be 401/403 and the login must still fail with the new password.

- Operations **not** named in the Recommendation (e.g., task/category CRUD) stay public and go to "Recommended follow-ups".
