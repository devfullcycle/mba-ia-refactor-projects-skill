# Refactoring Playbook

Padroes concretos de transformacao para cada anti-pattern. Cada padrao mostra codigo antes e depois para Python e Node.js quando aplicavel.

---

## 1. SQL Injection → Parameterized Queries

### Python — Antes
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("INSERT INTO usuarios (nome, email) VALUES ('" + nome + "', '" + email + "')")
query = "SELECT * FROM produtos WHERE 1=1"
query += " AND (nome LIKE '%" + termo + "%' OR descricao LIKE '%" + termo + "%')"
query += " AND categoria = '" + categoria + "'"
cursor.execute(query)
```

### Python — Depois
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute("INSERT INTO usuarios (nome, email) VALUES (?, ?)", (nome, email))

query = "SELECT * FROM produtos WHERE 1=1"
params = []
if termo:
    query += " AND (nome LIKE ? OR descricao LIKE ?)"
    params.extend([f"%{termo}%", f"%{termo}%"])
if categoria:
    query += " AND categoria = ?"
    params.append(categoria)
cursor.execute(query, params)
```

### Node.js — Antes
```javascript
db.run(`DELETE FROM users WHERE id = ${id}`);
```

### Node.js — Depois
```javascript
db.run("DELETE FROM users WHERE id = ?", [id]);
```

---

## 2. Hardcoded Credentials → Environment Variables

### Python — Antes
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
email_password = 'senha123'
```

### Python — Depois (config/settings.py)
```python
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-prod")
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
```

### Node.js — Antes
```javascript
const config = {
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
    port: 3000
};
```

### Node.js — Depois (config/settings.js)
```javascript
require('dotenv').config();

module.exports = {
    dbPath: process.env.DB_PATH || './database.db',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    port: process.env.PORT || 3000
};
```

---

## 3. God Class → Split by Domain

### Antes (um arquivo models.py com 300+ linhas para 4 dominios)
```python
# models.py — tudo misturado
def get_todos_produtos(): ...
def get_produto_por_id(id): ...
def criar_usuario(nome, email, senha): ...
def criar_pedido(usuario_id, itens): ...
def relatorio_vendas(): ...
```

### Depois (um model por dominio)
```python
# models/produto_model.py
class ProdutoModel:
    @staticmethod
    def get_all(): ...

    @staticmethod
    def get_by_id(id): ...

    @staticmethod
    def create(nome, descricao, preco, estoque, categoria): ...

    @staticmethod
    def search(termo, categoria=None, preco_min=None, preco_max=None): ...

# models/usuario_model.py
class UsuarioModel:
    @staticmethod
    def get_all(): ...

    @staticmethod
    def get_by_id(id): ...

    @staticmethod
    def create(nome, email, senha): ...

    @staticmethod
    def authenticate(email, senha): ...

# models/pedido_model.py
class PedidoModel:
    @staticmethod
    def create(usuario_id, itens): ...

    @staticmethod
    def get_by_usuario(usuario_id): ...

    @staticmethod
    def get_all(): ...

    @staticmethod
    def update_status(pedido_id, status): ...
```

### Node.js — Antes (AppManager faz tudo)
```javascript
class AppManager {
    initDb() { /* CREATE TABLE + seeds */ }
    setupRoutes(app) {
        // checkout + financial report + delete user
    }
}
```

### Node.js — Depois (modulos separados)
```javascript
// models/userModel.js
// models/courseModel.js
// models/enrollmentModel.js
// controllers/checkoutController.js
// controllers/reportController.js
// routes/checkoutRoutes.js
// routes/reportRoutes.js
// database.js (init + seed)
```

---

## 4. Business Logic in Routes → Extract to Controller/Service

### Python — Antes
```python
@app.route('/pedidos', methods=['POST'])
def criar_pedido():
    dados = request.get_json()
    resultado = models.criar_pedido(usuario_id, itens)
    print("ENVIANDO EMAIL...")
    print("ENVIANDO SMS...")
    return jsonify(resultado), 201
```

### Python — Depois — Route
```python
# routes/pedido_routes.py
pedido_bp = Blueprint('pedidos', __name__)

@pedido_bp.route('/pedidos', methods=['POST'])
def criar_pedido():
    dados = request.get_json()
    resultado, status = PedidoController.criar_pedido(dados)
    return jsonify(resultado), status
```

### Python — Depois — Controller
```python
# controllers/pedido_controller.py
class PedidoController:
    @staticmethod
    def criar_pedido(dados):
        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])
        if not usuario_id or not itens:
            return {"erro": "Dados invalidos"}, 400
        resultado = PedidoModel.create(usuario_id, itens)
        if "erro" in resultado:
            return {"erro": resultado["erro"]}, 400
        NotificationService.notify_new_order(resultado["pedido_id"], usuario_id)
        return {"dados": resultado, "sucesso": True, "mensagem": "Pedido criado"}, 201
```

---

## 5. Password/Secret Exposure → Filter in Serialization

### Antes
```python
def to_dict(self):
    return {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        'password': self.password,   # EXPÕE A SENHA!
    }
```

### Depois
```python
def to_dict(self):
    return {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        'role': self.role,
        'active': self.active,
        'created_at': str(self.created_at),
    }
```

Tambem remover secret_key e debug do health check:
```python
# Antes
return jsonify({"secret_key": "minha-chave...", "debug": True})
# Depois
return jsonify({"status": "ok", "database": "connected"})
```

---

## 6. Weak Cryptography → Secure Hashing

### Python — Antes
```python
import hashlib
self.password = hashlib.md5(pwd.encode()).hexdigest()
```

### Python — Depois
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)
```

### Node.js — Antes
```javascript
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```

### Node.js — Depois
```javascript
const bcrypt = require('bcrypt');
const SALT_ROUNDS = 10;

async function hashPassword(pwd) {
    return bcrypt.hash(pwd, SALT_ROUNDS);
}

async function verifyPassword(pwd, hash) {
    return bcrypt.compare(pwd, hash);
}
```

---

## 7. Callback Hell → Async/Await

### Node.js — Antes
```javascript
this.db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
    this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
        this.db.run("INSERT INTO enrollments ...", [...], function(err) {
            self.db.run("INSERT INTO payments ...", [...], function(err) {
                self.db.run("INSERT INTO audit_logs ...", [...], (err) => {
                    res.status(200).json({ msg: "Sucesso" });
                });
            });
        });
    });
});
```

### Node.js — Depois
```javascript
// database.js — promisify
const dbAsync = {
    get: (sql, params) => new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => err ? reject(err) : resolve(row));
    }),
    all: (sql, params) => new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => err ? reject(err) : resolve(rows));
    }),
    run: (sql, params) => new Promise((resolve, reject) => {
        db.run(sql, params, function(err) { err ? reject(err) : resolve(this) });
    })
};

// controller/checkoutController.js
async function checkout(req, res) {
    const { usr, eml, pwd, c_id, card } = req.body;
    const course = await dbAsync.get("SELECT * FROM courses WHERE id = ? AND active = 1", [c_id]);
    if (!course) return res.status(404).json({ error: "Curso nao encontrado" });

    let user = await dbAsync.get("SELECT id FROM users WHERE email = ?", [eml]);
    if (!user) {
        const hash = await hashPassword(pwd || "123456");
        const result = await dbAsync.run("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", [usr, eml, hash]);
        user = { id: result.lastID };
    }

    const enrResult = await dbAsync.run("INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [user.id, c_id]);
    await dbAsync.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)", [enrResult.lastID, course.price, "PAID"]);
    await dbAsync.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [`Checkout curso ${c_id} por ${user.id}`]);

    res.status(200).json({ msg: "Sucesso", enrollment_id: enrResult.lastID });
}
```

---

## 8. N+1 Queries → JOINs / Eager Loading

### Python — Antes (3 queries por pedido)
```python
for row in rows:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    itens = cursor2.fetchall()
    for item in itens:
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
        prod = cursor3.fetchone()
```

### Python — Depois (1 query com JOIN)
```python
cursor.execute("""
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           ip.produto_id, ip.quantidade, ip.preco_unitario,
           pr.nome as produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = ip.produto_id
    WHERE p.usuario_id = ?
    ORDER BY p.id, ip.id
""", (usuario_id,))
```

### SQLAlchemy — Depois
```python
orders = Order.query.options(
    db.joinedload(Order.items).joinedload(OrderItem.product)
).filter_by(user_id=user_id).all()
```

---

## 9. Global Mutable State → Dependency Injection

### Python — Antes
```python
db_connection = None  # global mutavel

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(...)
```

### Python — Depois
```python
# database.py — factory
def create_connection(db_path):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Em config ou app.py
from config.settings import SQLALCHEMY_DATABASE_URI
db = create_connection(SQLALCHEMY_DATABASE_URI)
```

### Node.js — Antes
```javascript
let globalCache = {};
let totalRevenue = 0;
```

### Node.js — Depois
```javascript
class CacheService {
    constructor() { this.cache = new Map(); }
    set(key, value) { this.cache.set(key, value); }
    get(key) { return this.cache.get(key); }
}
// Injetar via construtor nos controllers
```

---

## 10. Duplicated Code → Extract Shared Functions

### Antes (serializacao repetida)
```python
result.append({
    "id": row["id"],
    "nome": row["nome"],
    "preco": row["preco"],
    # ... 5+ campos copiados/colados
})
```

### Depois
```python
# No model
def to_dict(self):
    return {
        "id": self.id,
        "nome": self.nome,
        "preco": self.preco,
    }

# Na route
result = [item.to_dict() for item in items]
```

### Antes (logica de overdue copiada 3x)
```python
# Em 3 arquivos diferentes:
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            task_data['overdue'] = True
```

### Depois
```python
# No model Task
def is_overdue(self):
    if self.due_date:
        if self.due_date < datetime.now(timezone.utc):
            if self.status != 'done' and self.status != 'cancelled':
                return True
    return False

# Nas routes
task_data['overdue'] = task.is_overdue()
```

---

## Validation Checklist (apos cada refatoracao)

1. A funcionalidade original foi preservada?
2. Todos os endpoints ainda respondem com os mesmos status codes?
3. Nao ha SQL injection?
4. Nao ha secrets hardcoded?
5. Cada arquivo tem uma responsabilidade clara?
6. A aplicacao inicia sem erros?
7. O entry point e limpo (composition root)?
