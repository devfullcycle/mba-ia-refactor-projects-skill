# Refactoring Playbook

This playbook contains concrete transformation patterns for the most common anti-patterns. Each pattern includes a before/after example. Use during Phase 3.

---

## T1: Extract Config from Hardcoded Values

**Applies to:** AP-C2 (Hardcoded Credentials), AP-L4 (Debug Mode)

### Before
```python
# app.py
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
DATABASE = "loja.db"
```

### After
```python
# config/settings.py
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-in-production")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "app.db")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# .env (never commit to git)
# SECRET_KEY=your-actual-secret-here
# DATABASE_PATH=loja.db
# DEBUG=False

# .env.example (commit this as a template)
# SECRET_KEY=your-secret-here
# DATABASE_PATH=app.db
# DEBUG=False
```

```javascript
// Node.js — config/settings.js
require('dotenv').config()
module.exports = {
    secretKey: process.env.SECRET_KEY || 'dev-only-change-in-production',
    paymentKey: process.env.PAYMENT_GATEWAY_KEY,
    dbPath: process.env.DB_PATH || './database.db',
    port: parseInt(process.env.PORT) || 3000,
}
```

**Steps:**
1. Create `config/settings.py` (or `config/settings.js`)
2. Create `.env` with real values
3. Create `.env.example` with placeholder values
4. Add `.env` to `.gitignore`
5. Replace all hardcoded values with config imports

---

## T2: Fix SQL Injection → Parameterized Queries

**Applies to:** AP-C1 (SQL Injection)

### Before
```python
# models.py — string concatenation
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
cursor.execute("SELECT * FROM produtos WHERE nome LIKE '%" + termo + "%'")
```

### After
```python
# models/product_model.py — parameterized queries
def find_by_id(self, product_id):
    return self.cursor.execute(
        "SELECT * FROM produtos WHERE id = ?", (product_id,)
    ).fetchone()

def find_by_search(self, term):
    return self.cursor.execute(
        "SELECT * FROM produtos WHERE nome LIKE ?", (f"%{term}%",)
    ).fetchall()

def authenticate_user(self, email, password_hash):
    return self.cursor.execute(
        "SELECT * FROM usuarios WHERE email = ? AND senha = ?",
        (email, password_hash)
    ).fetchone()
```

```javascript
// Node.js — parameterized queries
async findById(id) {
    return this.db.getAsync("SELECT * FROM users WHERE id = ?", [id])
}
async authenticate(email, passwordHash) {
    return this.db.getAsync(
        "SELECT * FROM users WHERE email = ? AND password = ?",
        [email, passwordHash]
    )
}
```

**Rule:** NEVER concatenate user-supplied values into SQL. ALWAYS use `?` placeholders (SQLite/MySQL) or `$1` (PostgreSQL) with a parameters array.

---

## T3: Fix Password Storage

**Applies to:** AP-C3 (Plain Text / Weak Password Storage)

### Before (Python — plain text)
```python
# models.py
def criar_usuario(nome, email, senha):
    cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                   (nome, email, senha))  # plain text!
```

### After (Python — bcrypt via werkzeug)
```python
# models/user_model.py
from werkzeug.security import generate_password_hash, check_password_hash

class UserModel:
    def create(self, name, email, password):
        password_hash = generate_password_hash(password)  # bcrypt-based
        self.db.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )

    def authenticate(self, email, password):
        user = self.db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        if user and check_password_hash(user['password'], password):
            return user
        return None
```

### Before (Python — MD5)
```python
import hashlib
hashed = hashlib.md5(password.encode()).hexdigest()
```

### After (Python — werkzeug bcrypt)
```python
from werkzeug.security import generate_password_hash
hashed = generate_password_hash(password)  # bcrypt with automatic salt
```

### Before (Node.js — fake crypto)
```javascript
function badCrypto(pwd) {
    return Buffer.from(pwd).toString('base64').repeat(10).slice(0, 10)
}
```

### After (Node.js — bcrypt)
```javascript
const bcrypt = require('bcrypt')

async function hashPassword(password) {
    return bcrypt.hash(password, 12)  // 12 rounds
}

async function verifyPassword(password, hash) {
    return bcrypt.compare(password, hash)
}
```

---

## T4: Split God Class / Module into Domain Models

**Applies to:** AP-C5 (God Class)

### Before
```python
# models.py — 350 lines, 4 domains mixed together
def get_todos_produtos(): ...    # domain: products
def criar_produto(): ...         # domain: products
def get_usuario(): ...           # domain: users
def criar_pedido(): ...          # domain: orders
def calcular_desconto(): ...     # domain: orders + business logic
```

### After
```
models/
├── __init__.py
├── product_model.py    # only product DB operations
├── user_model.py       # only user DB operations
└── order_model.py      # only order DB operations
```

```python
# models/product_model.py
class ProductModel:
    def __init__(self, db): self.db = db
    def find_all(self): ...
    def find_by_id(self, id): ...
    def create(self, name, price, stock): ...
    def update(self, id, data): ...
    def delete(self, id): ...

# models/user_model.py
class UserModel:
    def __init__(self, db): self.db = db
    def find_by_email(self, email): ...
    def create(self, name, email, password): ...

# models/order_model.py
class OrderModel:
    def __init__(self, db): self.db = db
    def find_by_user(self, user_id): ...
    def create(self, user_id, items): ...
```

---

## T5: Extract Business Logic to Controllers/Services

**Applies to:** AP-H1 (Business Logic in Routes), AP-H5 (Missing Auth)

### Before
```python
# app.py — business logic in route
@app.route('/api/pedidos', methods=['POST'])
def criar_pedido():
    items = request.json.get('items', [])
    total = sum(item['price'] * item['qty'] for item in items)
    if total > 10000:
        discount = total * 0.10
    elif total > 5000:
        discount = total * 0.05
    else:
        discount = 0
    final = total - discount
    cursor.execute("INSERT INTO pedidos ...", (user_id, final))
    return jsonify({'total': final})
```

### After
```python
# controllers/order_controller.py
PREMIUM_THRESHOLD = 10000
STANDARD_THRESHOLD = 5000
PREMIUM_DISCOUNT = 0.10
STANDARD_DISCOUNT = 0.05

class OrderController:
    def __init__(self, order_model):
        self.order_model = order_model

    def _calculate_discount(self, total):
        if total > PREMIUM_THRESHOLD:
            return total * PREMIUM_DISCOUNT
        elif total > STANDARD_THRESHOLD:
            return total * STANDARD_DISCOUNT
        return 0

    def create_order(self, user_id, items):
        if not items:
            return {'error': 'Order must have at least one item'}, 400
        total = sum(item['price'] * item['qty'] for item in items)
        discount = self._calculate_discount(total)
        final = total - discount
        self.order_model.create(user_id, items, final)
        return {'total': final, 'discount': discount}, 201

# views/order_routes.py
@orders_bp.route('/api/orders', methods=['POST'])
def create_order():
    controller = OrderController(OrderModel(get_db()))
    result, status = controller.create_order(
        get_current_user_id(), request.get_json() or {}
    )
    return jsonify(result), status
```

---

## T6: Fix N+1 Queries with JOINs

**Applies to:** AP-M1 (N+1 Query Problem)

### Before (SQLite raw queries)
```python
# N+1 — one query per order item
def get_orders(user_id):
    orders = cursor.execute("SELECT * FROM pedidos WHERE user_id = ?", (user_id,)).fetchall()
    result = []
    for order in orders:
        items = cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (order['id'],)).fetchall()  # N!
        result.append({**dict(order), 'items': [dict(i) for i in items]})
    return result
```

### After (JOIN)
```python
def get_orders_with_items(user_id):
    rows = cursor.execute("""
        SELECT p.id, p.total, p.data,
               i.produto_id, i.quantidade, i.preco_unitario
        FROM pedidos p
        LEFT JOIN itens_pedido i ON i.pedido_id = p.id
        WHERE p.user_id = ?
        ORDER BY p.id
    """, (user_id,)).fetchall()

    orders = {}
    for row in rows:
        oid = row['id']
        if oid not in orders:
            orders[oid] = {'id': oid, 'total': row['total'], 'items': []}
        if row['produto_id']:
            orders[oid]['items'].append({
                'product_id': row['produto_id'],
                'quantity': row['quantidade'],
                'unit_price': row['preco_unitario'],
            })
    return list(orders.values())
```

### Before (SQLAlchemy ORM)
```python
tasks = Task.query.all()
for task in tasks:
    user = User.query.get(task.user_id)  # N+1
```

### After (SQLAlchemy eager loading)
```python
from sqlalchemy.orm import joinedload
tasks = Task.query.options(joinedload(Task.user)).all()
# Single query with JOIN
```

---

## T7: Convert Callback Hell to async/await (Node.js)

**Applies to:** AP-M5 (Deprecated Callback Pattern)

### Before
```javascript
app.post('/api/checkout', (req, res) => {
    const {usr, eml, pwd, cid, cc} = req.body
    db.get("SELECT id FROM users WHERE email = ?", [eml], (err, user) => {
        if (err) return res.send("Erro DB")
        db.run("INSERT INTO enrollments ...", [user.id, cid], (err) => {
            if (err) return res.send("Erro")
            db.run("INSERT INTO payments ...", [user.id, cc], (err) => {
                if (err) return res.send("Erro")
                res.json({success: true})
            })
        })
    })
})
```

### After
```javascript
// Promisify DB methods first
const { promisify } = require('util')
db.getAsync = promisify(db.get.bind(db))
db.runAsync = promisify(db.run.bind(db))
db.allAsync = promisify(db.all.bind(db))

// Controller
class CheckoutController {
    async processCheckout(req, res) {
        const { email, courseId, cardNumber } = req.body

        if (!email || !courseId || !cardNumber) {
            return res.status(400).json({ error: 'Missing required fields' })
        }

        try {
            const user = await this.userModel.findByEmail(email)
            if (!user) return res.status(404).json({ error: 'User not found' })

            const paymentStatus = await this.paymentService.processCard(cardNumber)
            if (paymentStatus !== 'PAID') {
                return res.status(402).json({ error: 'Payment declined' })
            }

            await this.db.runAsync('BEGIN TRANSACTION')
            try {
                await this.enrollmentModel.create(user.id, courseId)
                await this.paymentModel.record(user.id, courseId, paymentStatus)
                await this.db.runAsync('COMMIT')
            } catch (err) {
                await this.db.runAsync('ROLLBACK')
                throw err
            }

            res.status(201).json({ success: true, status: paymentStatus })
        } catch (err) {
            res.status(500).json({ error: 'Internal server error' })
        }
    }
}
```

---

## T8: Remove Duplicate Code (DRY)

**Applies to:** AP-M2 (Code Duplication)

### Before
```python
# task_routes.py lines 30-39
if task.due_date and task.status != 'done':
    if task.due_date < datetime.now():
        task_data['is_overdue'] = True
        task_data['days_overdue'] = (datetime.now() - task.due_date).days

# task_routes.py lines 71-80 — EXACT DUPLICATE
if task.due_date and task.status != 'done':
    if task.due_date < datetime.now():
        task_data['is_overdue'] = True
        task_data['days_overdue'] = (datetime.now() - task.due_date).days

# report_routes.py lines 33-43 — NEAR DUPLICATE
```

### After
```python
# utils/task_helpers.py
from datetime import datetime

def compute_overdue_status(task):
    """Returns overdue fields for a task dict."""
    if task.due_date and task.status != 'done' and task.due_date < datetime.now():
        return {
            'is_overdue': True,
            'days_overdue': (datetime.now() - task.due_date).days
        }
    return {'is_overdue': False, 'days_overdue': 0}

# Used in all routes:
task_data = task.to_dict()
task_data.update(compute_overdue_status(task))
```

---

## T9: Add Centralized Error Handling

**Applies to:** AP-M6 (Bare Exception Handling)

### Before
```python
try:
    db.session.commit()
except:
    pass  # silently swallows everything
```

### After (Python/Flask)
```python
# middlewares/error_handler.py
import logging
from flask import jsonify
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad request', 'details': str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Internal error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# In controllers — catch specific exceptions
def create_user(self, data):
    try:
        self.user_model.create(data['name'], data['email'], data['password'])
        return {'message': 'User created'}, 201
    except IntegrityError:
        return {'error': 'Email already exists'}, 409
    except SQLAlchemyError as e:
        logger.error(f"DB error creating user: {e}")
        return {'error': 'Database error'}, 500
```

### After (Node.js)
```javascript
// middlewares/errorHandler.js
module.exports = (err, req, res, next) => {
    console.error(err.stack)
    const status = err.status || 500
    res.status(status).json({
        error: err.message || 'Internal server error'
    })
}

// app.js — register last
app.use(errorHandler)

// In controllers — use next(err) for async errors
async function createUser(req, res, next) {
    try {
        await userModel.create(req.body)
        res.status(201).json({ message: 'Created' })
    } catch (err) {
        next(err)  // pass to centralized handler
    }
}
```

---

## T10: Remove Sensitive Fields from API Responses

**Applies to:** AP-H4 (Password in API Responses)

### Before
```python
def to_dict(self):
    return {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        'password': self.password,  # NEVER
        'role': self.role
    }
```

### After
```python
def to_dict(self, include_sensitive=False):
    data = {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        'role': self.role
    }
    return data
    # password is NEVER included in public API responses
```

---

## General Refactoring Order

Execute transformations in this order to minimize risk:

1. **T1** — Extract config (reduces security exposure immediately)
2. **T2** — Fix SQL injections (CRITICAL security)
3. **T3** — Fix password storage (CRITICAL security)
4. **T4** — Split God Class (enables clean layering)
5. **T5** — Extract business logic to controllers (core MVC)
6. **T9** — Add centralized error handling (stability)
7. **T10** — Remove sensitive fields from responses (security)
8. **T6** — Fix N+1 queries (performance)
9. **T7** — Convert callbacks to async/await if Node.js (maintainability)
10. **T8** — Remove code duplication (DRY)
