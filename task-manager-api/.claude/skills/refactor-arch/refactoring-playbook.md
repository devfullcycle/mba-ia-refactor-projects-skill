# Refactoring Playbook

This playbook provides concrete transformation patterns for Phase 3 (Refactoring). Each pattern shows a before/after transformation for a specific anti-pattern.

---

## Pattern 1: Extract Configuration from Hardcoded Values

**Anti-pattern:** Hardcoded secrets, ports, database paths directly in source code.

### Before (Python)
```python
# app.py
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
db_path = "loja.db"
app.run(host="0.0.0.0", port=5000)
```

### After (Python)
```python
# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
DB_PATH = os.environ.get('DB_PATH', 'app.db')
PORT = int(os.environ.get('PORT', 5000))
HOST = os.environ.get('HOST', '0.0.0.0')
```

```python
# app.py
from config.settings import SECRET_KEY, DEBUG, PORT, HOST
app.config['SECRET_KEY'] = SECRET_KEY
app.run(host=HOST, port=PORT, debug=DEBUG)
```

### Before (Node.js)
```javascript
// utils.js
const config = {
    dbUser: "admin_master",
    dbPassword: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
    port: 3000
};
```

### After (Node.js)
```javascript
// src/config/settings.js
require('dotenv').config();

module.exports = {
    dbUser: process.env.DB_USER || 'admin',
    dbPassword: process.env.DB_PASSWORD,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    port: parseInt(process.env.PORT || '3000', 10),
    secretKey: process.env.SECRET_KEY || 'dev-key-change-in-production'
};
```

---

## Pattern 2: Fix SQL Injection with Parameterized Queries

**Anti-pattern:** SQL queries built with string concatenation.

### Before (Python/sqlite3)
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))

cursor.execute(
    "INSERT INTO produtos (nome, preco) VALUES ('" + nome + "', " + str(preco) + ")"
)

query = "SELECT * FROM produtos WHERE 1=1"
query += " AND nome LIKE '%" + termo + "%'"
```

### After (Python/sqlite3)
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))

cursor.execute(
    "INSERT INTO produtos (nome, preco) VALUES (?, ?)", (nome, preco)
)

query = "SELECT * FROM produtos WHERE 1=1"
params = []
if termo:
    query += " AND nome LIKE ?"
    params.append(f"%{termo}%")
cursor.execute(query, params)
```

### Before (Node.js/sqlite3)
```javascript
db.get(`SELECT * FROM users WHERE email = '${email}'`, (err, row) => { ... });
```

### After (Node.js/sqlite3)
```javascript
db.get("SELECT * FROM users WHERE email = ?", [email], (err, row) => { ... });
```

---

## Pattern 3: Implement Proper Password Hashing

**Anti-pattern:** Plaintext passwords, MD5, base64 encoding.

### Before (Python)
```python
# Plaintext
self.password = password

# MD5 (broken)
import hashlib
self.password = hashlib.md5(password.encode()).hexdigest()
```

### After (Python)
```python
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
```

### Before (Node.js)
```javascript
// Base64 "encryption"
function badCrypto(pwd) {
    let h = Buffer.from(pwd).toString('base64');
    for (let i = 0; i < 10000; i++) {
        h = Buffer.from(h).toString('base64');
    }
    return h.substring(0, 10);
}
```

### After (Node.js)
```javascript
const bcrypt = require('bcrypt');
const SALT_ROUNDS = 10;

async function hashPassword(password) {
    return bcrypt.hash(password, SALT_ROUNDS);
}

async function checkPassword(password, hash) {
    return bcrypt.compare(password, hash);
}
```

---

## Pattern 4: Split God Class into Domain Modules

**Anti-pattern:** Single file with all database operations for multiple domains.

### Before
```python
# models.py (314 lines — products, users, orders, reports all in one file)
def get_all_produtos(): ...
def criar_produto(): ...
def get_usuario(): ...
def criar_usuario(): ...
def login(): ...
def criar_pedido(): ...
def relatorio_vendas(): ...
```

### After
```python
# models/product_model.py
class ProductModel:
    def get_all(self): ...
    def get_by_id(self, id): ...
    def create(self, data): ...
    def update(self, id, data): ...
    def delete(self, id): ...
    def search(self, filters): ...

# models/user_model.py
class UserModel:
    def get_all(self): ...
    def get_by_id(self, id): ...
    def create(self, data): ...
    def authenticate(self, email, password): ...

# models/order_model.py
class OrderModel:
    def create(self, user_id, items): ...
    def get_by_user(self, user_id): ...
    def get_all(self): ...
    def update_status(self, order_id, status): ...
```

---

## Pattern 5: Refactor Callback Hell to Async/Await

**Anti-pattern:** Deeply nested callbacks in Node.js.

### Before
```javascript
app.post('/api/checkout', (req, res) => {
    const { usr, eml, pwd, c_id, card } = req.body;
    db.get("SELECT * FROM users WHERE email = ?", [eml], (err, user) => {
        if (err) return res.status(500).json({ error: "Erro DB" });
        if (!user) {
            db.run("INSERT INTO users ...", [usr, eml, pwd], function(err) {
                if (err) return res.status(500).json({ error: "Erro" });
                db.run("INSERT INTO enrollments ...", [this.lastID, c_id], function(err) {
                    if (err) return res.status(500).json({ error: "Erro" });
                    db.run("INSERT INTO payments ...", [], function(err) {
                        // ... more nesting
                    });
                });
            });
        }
    });
});
```

### After
```javascript
// Promisify database operations
function dbGet(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => err ? reject(err) : resolve(row));
    });
}

function dbRun(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function(err) {
            err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

// Clean async/await handler
router.post('/checkout', async (req, res, next) => {
    try {
        const { username, email, password, courseId, card } = req.body;

        let user = await dbGet("SELECT * FROM users WHERE email = ?", [email]);
        if (!user) {
            const result = await dbRun("INSERT INTO users ...", [username, email, password]);
            user = { id: result.lastID };
        }

        const enrollment = await dbRun("INSERT INTO enrollments ...", [user.id, courseId]);
        await dbRun("INSERT INTO payments ...", [enrollment.lastID, amount, status]);

        res.status(201).json({ message: "Success", enrollmentId: enrollment.lastID });
    } catch (error) {
        next(error);
    }
});
```

---

## Pattern 6: Fix N+1 Queries with JOINs

**Anti-pattern:** Database query inside a loop.

### Before (Python)
```python
def get_pedidos_usuario(usuario_id):
    cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
    pedidos = cursor.fetchall()
    result = []
    for pedido in pedidos:
        cursor2 = conn.cursor()
        cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (pedido["id"],))
        itens = cursor2.fetchall()
        for item in itens:
            cursor3 = conn.cursor()
            cursor3.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],))
            produto = cursor3.fetchone()
            item["produto_nome"] = produto["nome"] if produto else "Desconhecido"
        result.append({**pedido, "itens": itens})
    return result
```

### After (Python)
```python
def get_pedidos_usuario(usuario_id):
    cursor.execute("""
        SELECT p.*, i.id as item_id, i.quantidade, i.preco_unitario,
               pr.nome as produto_nome, pr.id as produto_id
        FROM pedidos p
        LEFT JOIN itens_pedido i ON p.id = i.pedido_id
        LEFT JOIN produtos pr ON i.produto_id = pr.id
        WHERE p.usuario_id = ?
        ORDER BY p.id
    """, (usuario_id,))
    rows = cursor.fetchall()

    pedidos = {}
    for row in rows:
        pid = row["id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": pid, "status": row["status"],
                "total": row["total"], "itens": []
            }
        if row["item_id"]:
            pedidos[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"],
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"]
            })
    return list(pedidos.values())
```

---

## Pattern 7: Centralize Error Handling

**Anti-pattern:** Try/except or try/catch blocks duplicated in every route handler.

### Before (Python)
```python
@app.route('/products', methods=['POST'])
def create_product():
    try:
        data = request.json
        # ... logic
        return jsonify(result), 201
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.json
        # ... logic
        return jsonify(result), 201
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
```

### After (Python)
```python
# middlewares/error_handler.py
import logging

logger = logging.getLogger(__name__)

class AppError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        logger.warning(f"App error: {error}")
        return {"error": str(error)}, error.status_code

    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Resource not found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}")
        return {"error": "Internal server error"}, 500
```

```python
# views/product_routes.py — clean route with no try/except
@product_bp.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    if not data:
        raise AppError("Request body is required", 400)
    product = controller.create_product(data)
    return jsonify(product), 201
```

### Before (Node.js)
```javascript
app.post('/api/checkout', (req, res) => {
    try { /* ... */ }
    catch (e) { res.status(500).json({ error: e.message }); }
});
```

### After (Node.js)
```javascript
// middlewares/errorHandler.js
function errorHandler(err, req, res, next) {
    const status = err.status || 500;
    console.error(`[${status}] ${err.message}`);
    res.status(status).json({ error: err.message || 'Internal server error' });
}

// routes — just throw or call next(error)
router.post('/checkout', async (req, res, next) => {
    try {
        const result = await controller.checkout(req.body);
        res.status(201).json(result);
    } catch (error) {
        next(error);
    }
});
```

---

## Pattern 8: Extract Duplicated Validation Logic

**Anti-pattern:** Same validation repeated in multiple route handlers.

### Before
```python
# In create_product handler
if not nome or len(nome) < 2:
    return jsonify({"error": "Nome obrigatório (min 2 chars)"}), 400
if preco is None or preco <= 0:
    return jsonify({"error": "Preço deve ser positivo"}), 400
if estoque is not None and estoque < 0:
    return jsonify({"error": "Estoque não pode ser negativo"}), 400

# In update_product handler (SAME code again)
if not nome or len(nome) < 2:
    return jsonify({"error": "Nome obrigatório (min 2 chars)"}), 400
if preco is None or preco <= 0:
    return jsonify({"error": "Preço deve ser positivo"}), 400
if estoque is not None and estoque < 0:
    return jsonify({"error": "Estoque não pode ser negativo"}), 400
```

### After
```python
# controllers/product_controller.py
class ProductController:
    VALID_STATUSES = ['active', 'inactive']

    def validate_product_data(self, data, is_update=False):
        errors = []
        name = data.get('nome', '').strip()
        price = data.get('preco')
        stock = data.get('estoque')

        if not name or len(name) < 2:
            errors.append("Nome obrigatório (mínimo 2 caracteres)")
        if price is not None and price <= 0:
            errors.append("Preço deve ser positivo")
        if stock is not None and stock < 0:
            errors.append("Estoque não pode ser negativo")

        if errors:
            raise AppError("; ".join(errors), 400)

        return {"nome": name, "preco": price, "estoque": stock, **data}
```

---

## Pattern 9: Eliminate Sensitive Data Exposure

**Anti-pattern:** API responses include passwords, secrets, or debug information.

### Before
```python
# Health endpoint exposes secrets
@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "secret_key": "minha-chave-super-secreta-123",
        "debug": True,
        "db_path": "loja.db"
    })

# User model returns password
def to_dict(self):
    return {"id": self.id, "name": self.name, "email": self.email, "password": self.password}
```

### After
```python
# Health endpoint — no secrets
@app.route('/health')
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

# User model excludes password
def to_dict(self):
    return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}
```

---

## Pattern 10: Replace Print Logging with Proper Framework

**Anti-pattern:** Using `print()` or `console.log()` for logging.

### Before (Python)
```python
print(f"Produto criado: {produto['nome']}")
print(f"ERRO ao criar produto: {str(e)}")
```

### After (Python)
```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Product created: {product['name']}")
logger.error(f"Error creating product: {e}")
```

### Before (Node.js)
```javascript
console.log(`Processing card ${card} with key ${config.paymentGatewayKey}`);
```

### After (Node.js)
```javascript
const logger = require('../config/logger');
logger.info(`Processing payment for enrollment ${enrollmentId}`);
// Never log card numbers or API keys
```

---

## Refactoring Execution Checklist

When executing Phase 3, apply these patterns in this order:

1. **Create config module** — Extract all hardcoded values (Pattern 1)
2. **Create model layer** — Split God Class into domain models (Pattern 4)
3. **Fix SQL injection** — Parameterize all queries (Pattern 2)
4. **Fix password hashing** — Replace insecure hashing (Pattern 3)
5. **Create controller layer** — Extract business logic from routes (Pattern 8)
6. **Create route/view layer** — Thin routes that delegate to controllers
7. **Fix N+1 queries** — Replace loops with JOINs (Pattern 6)
8. **Add error handling middleware** — Centralized error handling (Pattern 7)
9. **Fix data exposure** — Remove sensitive data from responses (Pattern 9)
10. **Replace print logging** — Use proper logging (Pattern 10)
11. **Refactor callbacks** — Convert to async/await for Node.js (Pattern 5)
12. **Create composition root** — Wire everything in app.py/app.js
13. **Validate** — Start app, test all endpoints, verify no regressions
