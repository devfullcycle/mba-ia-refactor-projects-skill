# 05 — Refactor Playbook

Concrete before → after transformations for Phase 3. Each pattern shows the broken form and the fixed
form. Apply the one matching the stack. Keep behavior identical (same routes, same success shapes).

---

## P1. String-concatenated SQL → parameterized query

### Python (sqlite3)
```python
# BEFORE (C1) — models.py
cursor.execute("SELECT * FROM produtos WHERE id = " + str(pid))
cursor.execute(
    "INSERT INTO usuarios (nome,email,senha) VALUES ('" + nome + "','" + email + "','" + senha + "')"
)

# AFTER
cursor.execute("SELECT * FROM produtos WHERE id = ?", (pid,))
cursor.execute(
    "INSERT INTO usuarios (nome,email,senha) VALUES (?,?,?)", (nome, email, hashed)
)
```
Dynamic `WHERE 1=1 + query +=` becomes a query + params list:
```python
query = "SELECT * FROM produtos WHERE 1=1"
params = []
if termo:
    query += " AND (nome LIKE ? OR descricao LIKE ?)"; params += [f"%{termo}%"]*2
if categoria:
    query += " AND categoria = ?"; params.append(categoria)
cursor.execute(query, params)
```

### JavaScript (sqlite3 / generic)
```js
// BEFORE (C1)
db.run("DELETE FROM users WHERE id = " + id);
// AFTER
db.run("DELETE FROM users WHERE id = ?", [id]);
```

---

## P2. Hardcoded secret → env-driven config module

### Python
```python
# BEFORE (C2) — app.py
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
db_path = "loja.db"

# AFTER — config/settings.py
import os
from dotenv import load_dotenv
load_dotenv()
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///loja.db")
# app.py
app.config.from_object(Config)
```
Add `.env` to `.gitignore` and ship `.env.example`.

### JavaScript
```js
// BEFORE (C2) — utils.js
const config = { paymentGatewayKey: "pk_live_1234567890abcdef", port: 3000 };
// AFTER — config/index.js
require('dotenv').config();
const config = {
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,   // required
  port: Number(process.env.PORT ?? 3000),
  nodeEnv: process.env.NODE_ENV ?? 'development',
};
if (!config.paymentGatewayKey && config.nodeEnv === 'production')
  throw new Error('PAYMENT_GATEWAY_KEY is required');
module.exports = config;
```

---

## P3. God file → split into MVC layers

Take a file that owns DB + schema + routes + business logic (e.g. `AppManager.js`, or a `models.py`
that also enforces pricing) and decompose:
- DB connection + schema → `db/index.js` / `extensions.py` + a `scripts/seed`.
- Routes → `routes/` (thin, call controllers).
- Use cases → `controllers/`.
- Business rules (pricing, checkout flow, transactions) → `services/`.
- Row shape + queries → `models/`.

```js
// BEFORE (C3) — AppManager.js (God class: db + setupRoutes + checkout logic all in one)
class AppManager {
  constructor(){ this.db = new sqlite3.Database(':memory:'); }
  setupRoutes(app){
    app.post('/api/checkout', (req,res) => { /* 50 lines of DB + payment + audit */ });
  }
}

// AFTER — routes/checkout.js
const router = require('express').Router();
const checkoutController = require('../controllers/checkoutController');
router.post('/checkout', checkoutController.checkout);
module.exports = router;
// controllers/checkoutController.js  -> calls services/checkoutService
// services/checkoutService.js        -> transaction: enroll + pay + audit
// models/enrollment.js, models/payment.js -> queries (parameterized)
```

---

## P4. Insecure password storage → bcrypt

### Python
```python
# BEFORE (C4) — plaintext insert / MD5
cursor.execute("INSERT INTO usuarios (...,senha) VALUES (...,'"+senha+"')")
self.password = hashlib.md5(pwd.encode()).hexdigest()

# AFTER — services/auth_service.py or models/user.py
import bcrypt
def hash_password(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
def verify_password(pwd: str, hashed: str) -> bool:
    return bcrypt.checkpw(pwd.encode(), hashed.encode())
# login: fetch user by email, then verify_password(pwd, user.password) in Python (constant-time)
```

### JavaScript
```js
// BEFORE (C4) — badCrypto (reversible/colliding)
function badCrypto(pwd){ /* base64 loop */ }
// AFTER — utils/hash.js
const bcrypt = require('bcrypt');
const hashPassword = (p) => bcrypt.hash(p, 10);
const verifyPassword = (p, h) => bcrypt.compare(p, h);
```

---

## P5. Business logic in route → extract to service

```python
# BEFORE (H1) — controllers.py (validation + pricing + state machine inline)
categorias_validas = ["informatica","moveis",...]
if categoria not in categorias_validas: return jsonify(...),400
# ... later ...
if novo_status not in ["pendente","aprovado",...]: ...
if novo_status == "aprovado": print("NOTIFICAÇÃO ...")

# AFTER — services/produto_service.py + constants
class ProdutoService:
    def create(self, data):
        validate_categoria(data["categoria"])   # raises ValidationError
        return produto_repo.insert(data)
# services/pedido_service.py
class PedidoService:
    def update_status(self, pid, status):
        validate_status_transition(...)
        pedido_repo.update_status(pid, status)
        if status == "aprovado": notifier.send(...)
# controller just calls the service and maps exceptions to HTTP codes
```

---

## P6. Global mutable DB singleton → request-scoped / proper extension

### Python (Flask-SQLAlchemy app factory)
```python
# BEFORE (H2) — database.py
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)

# AFTER — extensions.py + app factory
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()          # one object, request-scoped session managed by Flask-SQLAlchemy
# app.py
def create_app():
    app = Flask(__name__); app.config.from_object(Config)
    db.init_app(app)
    with app.app_context(): db.create_all()
    return app
```
(If staying on raw sqlite3, use Flask `g` so each request gets its own connection, closed on teardown.)

### JavaScript
```js
// BEFORE (H2) — shared global cache mutated per request
let globalCache = {}; logAndCache(k, v){ globalCache[k] = v; }
// AFTER — a request-scoped or injected store; no module-scope mutation in the request path
```

---

## P7. N+1 query → single JOIN / aggregate

### Python (SQLAlchemy)
```python
# BEFORE (M1) — 1 + 2N queries
for t in tasks:
    user = User.query.get(t.user_id)
    cat  = Category.query.get(t.category_id)
# AFTER — one query with eager loading
from sqlalchemy.orm import joinedload
tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
# counts: one grouped query instead of len(u.tasks) per user
```

### Python (raw sqlite3)
```sql
-- BEFORE: loop SELECT nome FROM produtos WHERE id = ?  per item
-- AFTER: one JOIN
SELECT ip.*, p.nome AS produto_nome
FROM itens_pedido ip JOIN produtos p ON p.id = ip.produto_id
WHERE ip.pedido_id = ?;
```

### JavaScript
```js
// BEFORE (M1) — nested db callbacks per course / enrollment
courses.forEach(c => db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], ...));
// AFTER — one aggregate query with JOINs
const rows = await allQuery(`
  SELECT c.title, u.name AS student, p.amount, p.status
  FROM courses c
  LEFT JOIN enrollments e ON e.course_id = c.id
  LEFT JOIN users u ON u.id = e.user_id
  LEFT JOIN payments p ON p.enrollment_id = e.id
`);
// then group in JS by course title
```

---

## P8. Bare/swallowed exceptions + error leakage → global error handler

### Python (Flask)
```python
# BEFORE (M2) — repeated in every handler
try:
    ...
except Exception as e:
    return jsonify({"erro": str(e)}), 500      # leaks internals

# AFTER — middlewares/error_handler.py
class ValidationError(ValueError): ...
class NotFoundError(LookupError): ...
def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def _bad(e): return jsonify({"erro": str(e)}), 400
    @app.errorhandler(NotFoundError)
    def _nf(e): return jsonify({"erro": str(e)}), 404
    @app.errorhandler(Exception)
    def _all(e):
        app.logger.exception("unhandled")
        return jsonify({"erro": "Erro interno"}), 500
# handlers now just `raise ValidationError("...")`
```

### JavaScript (Express)
```js
// AFTER — middlewares/errorHandler.js (registered LAST) + asyncHandler
const asyncHandler = (fn) => (req,res,next) => Promise.resolve(fn(req,res,next)).catch(next);
// routes: router.post('/checkout', asyncHandler(checkoutController.checkout));
app.use((err, req, res, next) => {
  const status = err.status || 500;
  logger.error(err);
  res.status(status).json({ error: status >= 500 ? 'Erro interno' : err.message });
});
```

---

## P9. Missing validation → schema at the edge

### Python (marshmallow)
```python
# AFTER — schemas/produto_schema.py
from marshmallow import Schema, fields, validate
class ProdutoSchema(Schema):
    nome = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    preco = fields.Number(required=True, validate=validate.Range(min=0))
    estoque = fields.Int(required=True, validate=validate.Range(min=0))
    categoria = fields.Str(load_default="geral", validate=validate.OneOf(CATEGORIAS))
# controller:
errors = ProdutoSchema().validate(data or {});  if errors: raise ValidationError(errors)
```

### JavaScript (zod / joi)
```js
// AFTER — schemas/checkout.js
const { z } = require('zod');
const CheckoutSchema = z.object({
  name: z.string().min(1), email: z.string().email(),
  courseId: z.number().int().positive(), card: z.string().regex(/^\d{12,19}$/),
});
// middleware: const parsed = CheckoutSchema.parse(req.body);
```

---

## P10. Callback hell → async/await (+ transactions)

```js
// BEFORE (H1/H4/H5) — 4-level nested callbacks, no transaction
this.db.run("INSERT INTO enrollments ...", [...], function(err){
   self.db.run("INSERT INTO payments ...", [...], function(err){
       self.db.run("INSERT INTO audit_logs ...", [...], (err)=> res.json(...));
   });
});

// AFTER — services/checkoutService.js (promisified db + transaction)
await run('BEGIN');
try {
  const enrId = await run('INSERT INTO enrollments (user_id,course_id) VALUES (?,?)', [uid, cid]);
  await run('INSERT INTO payments (enrollment_id,amount,status) VALUES (?,?,?)', [enrId, price, 'PAID']);
  await run("INSERT INTO audit_logs (action,created_at) VALUES (?,datetime('now'))", [`Checkout curso ${cid} por ${uid}`]);
  await run('COMMIT');
} catch (e) { await run('ROLLBACK'); throw e; }
```
(Promisify `db.run`/`db.all` once in `db/index.js`.)

---

## P11. Misplaced resource / blueprint → one module per resource

```python
# BEFORE (M5) — categories live under report_bp
@report_bp.route('/categories', methods=['GET']) ...
# AFTER — routes/category_routes.py + category_bp registered on its own
cat_bp = Blueprint('categories', __name__, url_prefix='')
@cat_bp.route('/categories', methods=['GET'])
def get_categories(): return category_controller.list()
```

---

## P12. Dead code & magic numbers → remove + named constants

```python
# BEFORE (L1/L3) — duplicated status list; unused helpers; magic tiers
if novo_status not in ["pendente","aprovado",...]: ...   # in 3 places
if faturamento > 10000: desconto = faturamento*0.1        # magic

# AFTER — core/constants.py
class OrderStatus: PENDENTE="pendente"; APROVADO="aprovado"; ...   # single source
class DiscountTier:
    TIERS = [(10000,0.10),(5000,0.05),(1000,0.02)]
    @classmethod
    def for_amount(cls, amount):
        return next((r for t,r in cls.TIERS if amount > t), 0)
# delete the unused is_admin()/validate_status() copies OR actually call the canonical one.
```

---

## P13. Deprecated APIs → modern equivalents

```python
# BEFORE (deprecated)
created_at = db.Column(db.DateTime, default=datetime.utcnow)          # Py>=3.12 deprecated
user = User.query.get(uid)                                             # SQLA 2.x legacy
# AFTER
from datetime import datetime, timezone
created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
user = db.session.get(User, uid)                                       # SQLA 2.x
```
```js
// BEFORE
const sqlite3 = require('sqlite3').verbose();   // verbose() is noisy/deprecated in prod
// AFTER
const sqlite3 = require('sqlite3');
```
Also: replace standalone `body-parser` with `express.json()`; replace `app.run(debug=True)` with
env-driven debug; replace `flask.__version__` with `importlib.metadata.version("flask")`.

---

## Applying the playbook

- Order matters: P2 (config) and P6 (DB/app factory) first — they define the skeleton the other
  transforms plug into. Then P3 (split files), then P1/P4/P5/P7 (security + logic), then P8/P9
  (cross-cutting), finally P11/P12/P13 (hygiene).
- After each transform, re-run the in-process validation (`test_client` for Flask; `supertest` or
  background HTTP for Express) so a regression is caught immediately.
