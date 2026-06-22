# Refactoring Playbook — /refactor-arch

Each entry describes a concrete transformation pattern. Use these patterns in Phase 3 to fix each finding. Every pattern includes the problematic code (**Before**) and the corrected code (**After**) with brief rationale.

---

## PT-01 — Fix SQL Injection: Use Parameterized Queries

**Fixes:** AP-01  
**Applies to:** Python (sqlite3, psycopg2), Node.js (better-sqlite3, pg, mysql2)

### Python — Before
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))

cursor.execute(
    "INSERT INTO produtos (nome, preco) VALUES ('" + nome + "', " + str(preco) + ")"
)

cursor.execute(
    "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
)

query = "SELECT * FROM produtos WHERE 1=1"
if termo:
    query += " AND nome LIKE '%" + termo + "%'"
cursor.execute(query)
```

### Python — After
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))

cursor.execute(
    "INSERT INTO produtos (nome, preco) VALUES (?, ?)",
    (nome, preco)
)

cursor.execute(
    "SELECT * FROM usuarios WHERE email = ? AND senha_hash = ?",
    (email, senha_hash)
)

query = "SELECT * FROM produtos WHERE 1=1"
params = []
if termo:
    query += " AND (nome LIKE ? OR descricao LIKE ?)"
    params.extend([f"%{termo}%", f"%{termo}%"])
cursor.execute(query, params)
```

### Node.js — Before
```javascript
db.get(`SELECT * FROM produtos WHERE id = ${id}`)
db.run(`INSERT INTO produtos (nome) VALUES ('${nome}')`)
```

### Node.js — After
```javascript
db.get("SELECT * FROM produtos WHERE id = ?", [id])
db.run("INSERT INTO produtos (nome) VALUES (?)", [nome])
```

---

## PT-02 — Fix Hardcoded Secrets: Use Environment Variables

**Fixes:** AP-02  
**Applies to:** Python/Flask, Node.js/Express

### Python — Before
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```

### Python — After
```python
# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-fallback-change-in-prod")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
```

```python
# app.py — composition root
from config.settings import SECRET_KEY, DEBUG
app.config["SECRET_KEY"] = SECRET_KEY
app.config["DEBUG"] = DEBUG
```

```
# .env (never commit to git — add to .gitignore)
SECRET_KEY=<generate-with-python-secrets-module>
DEBUG=false
DATABASE_PATH=loja.db
```

### Node.js — Before
```javascript
const SECRET = "hardcoded-secret-key"
```

### Node.js — After
```javascript
// config/settings.js
require('dotenv').config()
module.exports = {
  secret: process.env.SECRET_KEY,
  debug: process.env.DEBUG === 'true',
  dbPath: process.env.DATABASE_PATH || ':memory:'
}
```

---

## PT-03 — Fix God File: Separate by Domain Entity

**Fixes:** AP-03  
**Applies to:** Python, Node.js

### Python — Before
```python
# models.py — 350 lines mixing products, users, orders
def get_todos_produtos(): ...
def criar_produto(): ...
def get_todos_usuarios(): ...
def criar_usuario(): ...
def criar_pedido(): ...
def relatorio_vendas(): ...
```

### Python — After
```
models/
├── produto_model.py    # Only product queries
├── usuario_model.py    # Only user queries
├── pedido_model.py     # Only order queries
└── relatorio_model.py  # Only reporting queries
```

```python
# models/produto_model.py
from database import get_db

def get_todos_produtos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE ativo = 1")
    return [dict(row) for row in cursor.fetchall()]

def get_produto_por_id(produto_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
    row = cursor.fetchone()
    return dict(row) if row else None
```

### Node.js — Before
```javascript
// AppManager.js — 600 lines mixing all concerns
class AppManager {
  getAllUsers() { ... }
  createProduct() { ... }
  processCheckout() { ... }
  generateReport() { ... }
}
```

### Node.js — After
```javascript
// models/userModel.js
// models/productModel.js
// models/orderModel.js
```

---

## PT-04 — Fix Plain-Text Passwords: Hash with bcrypt/werkzeug

**Fixes:** AP-05  
**Applies to:** Python, Node.js

### Python — Before
```python
def criar_usuario(nome, email, senha, tipo="cliente"):
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
        (nome, email, senha)  # plaintext password!
    )

def login_usuario(email, senha):
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = ? AND senha = ?",
        (email, senha)  # comparing plaintext!
    )
```

### Python — After
```python
from werkzeug.security import generate_password_hash, check_password_hash

def criar_usuario(nome, email, senha, tipo="cliente"):
    senha_hash = generate_password_hash(senha)
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha_hash, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo)
    )

def login_usuario(email, senha):
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = ?",
        (email,)
    )
    row = cursor.fetchone()
    if row and check_password_hash(row["senha_hash"], senha):
        return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
    return None
```

### Node.js — Before
```javascript
db.run(`INSERT INTO users (email, password) VALUES ('${email}', '${password}')`)
```

### Node.js — After
```javascript
const bcrypt = require('bcrypt')
const SALT_ROUNDS = 10
const hash = await bcrypt.hash(password, SALT_ROUNDS)
db.run("INSERT INTO users (email, password_hash) VALUES (?, ?)", [email, hash])

// Login:
const valid = await bcrypt.compare(plainPassword, user.password_hash)
```

---

## PT-05 — Fix Global DB Connection: Per-Request Connection via flask.g

**Fixes:** AP-07  
**Applies to:** Python/Flask

### Python — Before
```python
# database.py
db_connection = None  # global mutable state

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
    return db_connection
```

### Python — After
```python
# database.py
import sqlite3
import os
from flask import g, current_app

def get_db():
    if "db" not in g:
        db_path = current_app.config.get("DATABASE_PATH", "loja.db")
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
```

```python
# app.py
from database import init_app
init_app(app)
```

### Node.js — Before
```javascript
let db = null
function getDb() {
    if (!db) db = new Database(':memory:')
    return db
}
```

### Node.js — After (better-sqlite3 is synchronous, so a module-level singleton is acceptable here)
```javascript
// database/connection.js
const Database = require('better-sqlite3')
const path = require('path')
const db = new Database(process.env.DB_PATH || ':memory:')
db.pragma('journal_mode = WAL')
module.exports = db
```

---

## PT-06 — Fix N+1 Queries: Use JOIN

**Fixes:** AP-10  
**Applies to:** Python (sqlite3), Node.js (better-sqlite3)

### Python — Before
```python
# 1 query for orders + N queries for items + N*M queries for product names
cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
rows = cursor.fetchall()
for row in rows:
    cursor2 = db.cursor()
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (row["id"],))
    itens = cursor2.fetchall()
    for item in itens:
        cursor3 = db.cursor()
        cursor3.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],))
```

### Python — After
```python
# 1 query with JOIN — O(1) database round-trips
cursor.execute("""
    SELECT
        p.id, p.usuario_id, p.status, p.total, p.criado_em,
        ip.produto_id, ip.quantidade, ip.preco_unitario,
        pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = ip.produto_id
    WHERE p.usuario_id = ?
    ORDER BY p.id
""", (usuario_id,))

rows = cursor.fetchall()
pedidos = {}
for row in rows:
    pid = row["id"]
    if pid not in pedidos:
        pedidos[pid] = {
            "id": pid, "usuario_id": row["usuario_id"],
            "status": row["status"], "total": row["total"],
            "criado_em": row["criado_em"], "itens": []
        }
    if row["produto_id"]:
        pedidos[pid]["itens"].append({
            "produto_id": row["produto_id"],
            "produto_nome": row["produto_nome"],
            "quantidade": row["quantidade"],
            "preco_unitario": row["preco_unitario"]
        })
return list(pedidos.values())
```

---

## PT-07 — Fix Duplicated Code: Extract Shared Function

**Fixes:** AP-11  
**Applies to:** Python, Node.js

### Python — Before
```python
# get_pedidos_usuario and get_todos_pedidos are 95% identical
def get_pedidos_usuario(usuario_id):
    cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
    # ... 20 lines of identical loop logic

def get_todos_pedidos():
    cursor.execute("SELECT * FROM pedidos")
    # ... same 20 lines of identical loop logic
```

### Python — After
```python
def _build_pedidos_query(usuario_id=None):
    """Returns (query_string, params) for orders with items."""
    base = """
        SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
               ip.produto_id, ip.quantidade, ip.preco_unitario, pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = ip.produto_id
    """
    if usuario_id is not None:
        return base + " WHERE p.usuario_id = ? ORDER BY p.id", (usuario_id,)
    return base + " ORDER BY p.id", ()

def get_pedidos_usuario(usuario_id):
    return _execute_pedidos_query(*_build_pedidos_query(usuario_id))

def get_todos_pedidos():
    return _execute_pedidos_query(*_build_pedidos_query())

def _execute_pedidos_query(query, params):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(query, params)
    pedidos = {}
    for row in cursor.fetchall():
        pid = row["id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": pid, "usuario_id": row["usuario_id"],
                "status": row["status"], "total": row["total"],
                "criado_em": row["criado_em"], "itens": []
            }
        if row["produto_id"]:
            pedidos[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"]
            })
    return list(pedidos.values())
```

---

## PT-08 — Fix Controller Side-Effects: Extract Notification Service

**Fixes:** AP-08  
**Applies to:** Python, Node.js

### Python — Before
```python
# controllers.py — mixed business logic and notification side-effects
def criar_pedido():
    resultado = models.criar_pedido(usuario_id, itens)

    print("ENVIANDO EMAIL: Pedido " + str(resultado["pedido_id"]) + " criado")
    print("ENVIANDO SMS: Seu pedido foi recebido!")
    print("ENVIANDO PUSH: Novo pedido recebido pelo sistema")

    return jsonify({...}), 201
```

### Python — After
```python
# services/notification_service.py
import logging
logger = logging.getLogger(__name__)

def notify_order_created(pedido_id, usuario_id):
    logger.info(f"[EMAIL] Order {pedido_id} created for user {usuario_id}")
    logger.info(f"[SMS] Order receipt sent to user {usuario_id}")
    logger.info(f"[PUSH] New order {pedido_id} received")
    # In production: call actual email/SMS/push provider here

def notify_order_status_changed(pedido_id, novo_status):
    if novo_status == "aprovado":
        logger.info(f"[NOTIFICATION] Order {pedido_id} approved — prepare shipment")
    elif novo_status == "cancelado":
        logger.info(f"[NOTIFICATION] Order {pedido_id} cancelled — restore stock")
```

```python
# controllers/pedido_controller.py
from services.notification_service import notify_order_created

def criar_pedido():
    resultado = pedido_model.criar_pedido(usuario_id, itens)
    notify_order_created(resultado["pedido_id"], usuario_id)
    return jsonify({...}), 201
```

---

## PT-09 — Fix Admin Endpoints: Add Authentication Middleware

**Fixes:** AP-04, AP-09  
**Applies to:** Python/Flask, Node.js/Express

### Python — Before
```python
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():  # no auth check
    cursor.execute("DELETE FROM itens_pedido")
    ...
```

### Python — After
```python
# middlewares/auth.py
import functools
from flask import request, jsonify, current_app
import jwt

def require_admin(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"erro": "Token de autenticação obrigatório"}), 401
        try:
            payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            if payload.get("tipo") != "admin":
                return jsonify({"erro": "Acesso negado — requer perfil admin"}), 403
        except jwt.InvalidTokenError:
            return jsonify({"erro": "Token inválido"}), 401
        return f(*args, **kwargs)
    return decorated
```

```python
# routes/admin_routes.py
from flask import Blueprint
from middlewares.auth import require_admin

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/reset-db", methods=["POST"])
@require_admin
def reset_database():
    ...
```

### Node.js — Before
```javascript
app.post('/admin/reset', (req, res) => {
    db.run('DELETE FROM users')  // no auth
})
```

### Node.js — After
```javascript
// middlewares/auth.js
const jwt = require('jsonwebtoken')
function requireAdmin(req, res, next) {
    const token = req.headers.authorization?.replace('Bearer ', '')
    if (!token) return res.status(401).json({ error: 'Token required' })
    try {
        const payload = jwt.verify(token, process.env.SECRET_KEY)
        if (payload.role !== 'admin') return res.status(403).json({ error: 'Admin only' })
        req.user = payload
        next()
    } catch {
        res.status(401).json({ error: 'Invalid token' })
    }
}
module.exports = { requireAdmin }

// routes/admin.js
const { requireAdmin } = require('../middlewares/auth')
router.post('/reset', requireAdmin, resetHandler)
```

---

## PT-10 — Fix Print Logging: Use Structured Logger

**Fixes:** AP-13  
**Applies to:** Python, Node.js

### Python — Before
```python
print("ERRO: " + str(e))
print("Produto criado com ID: " + str(id))
print("Login bem-sucedido: " + email)
```

### Python — After
```python
# config/logging_config.py
import logging
import sys

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
```

```python
# In each module:
import logging
logger = logging.getLogger(__name__)

logger.error(f"Error processing request: {e}")
logger.info(f"Product created with ID: {produto_id}")
logger.info(f"Successful login: {email}")
```

### Node.js — Before
```javascript
console.log('User created: ' + email)
console.log('ERROR: ' + err.message)
```

### Node.js — After
```javascript
// Use the built-in console with structured format, or a library like pino/winston
const logger = {
    info: (msg, meta = {}) => console.log(JSON.stringify({ level: 'INFO', msg, ...meta, ts: new Date().toISOString() })),
    error: (msg, meta = {}) => console.error(JSON.stringify({ level: 'ERROR', msg, ...meta, ts: new Date().toISOString() }))
}
logger.info('User created', { email })
logger.error('Request failed', { error: err.message })
```

---

## PT-11 — Fix Sensitive Data Exposure: Sanitize Responses

**Fixes:** AP-06  
**Applies to:** Python, Node.js

### Python — Before
```python
return jsonify({
    "status": "ok",
    "secret_key": "minha-chave-super-secreta-123",
    "debug": True,
    "db_path": "loja.db"
}), 200
```

### Python — After
```python
return jsonify({
    "status": "ok",
    "database": "connected",
    "counts": {
        "produtos": produtos,
        "usuarios": usuarios,
        "pedidos": pedidos
    },
    "versao": "1.0.0"
}), 200
```

Also: never include `senha`, `senha_hash`, or `password` fields in user response objects.

---

## PT-12 — Fix Magic Numbers: Extract Named Constants

**Fixes:** AP-14  
**Applies to:** Python, Node.js

### Python — Before
```python
if faturamento > 10000:
    desconto = faturamento * 0.1
elif faturamento > 5000:
    desconto = faturamento * 0.05
elif faturamento > 1000:
    desconto = faturamento * 0.02
```

### Python — After
```python
# config/settings.py
DISCOUNT_TIERS = [
    (10000, 0.10),
    (5000,  0.05),
    (1000,  0.02),
]

# models/relatorio_model.py
from config.settings import DISCOUNT_TIERS

def calcular_desconto(faturamento):
    for threshold, rate in DISCOUNT_TIERS:
        if faturamento > threshold:
            return round(faturamento * rate, 2)
    return 0.0
```
