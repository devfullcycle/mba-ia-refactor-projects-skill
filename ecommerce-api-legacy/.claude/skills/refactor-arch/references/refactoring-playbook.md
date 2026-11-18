# Playbook de Refatoração

Padrões de transformação (antes → depois). Exemplos em Python/Node por serem comuns; **aplique o mesmo princípio na sintaxe da stack detectada**. Preserve sempre URLs, métodos e formato de resposta.

Índice: P1 SQL parametrizado · P2 Segredos em config · P3 Extrair controller · P4 Extrair model · P5 Validação e serializer · P6 Eliminar estado global · P7 Erros centralizados · P8 Substituir deprecated/inseguro · P9 Corrigir N+1 · P10 Constantes e nomenclatura · P11 Quebrar God file / composition root

---

## P1 — Query parametrizada (AP-01)
**Antes**
```python
cur.execute("SELECT * FROM users WHERE email = '" + email + "'")
```
```js
db.get(`SELECT * FROM users WHERE id = ${req.params.id}`)
```
**Depois**
```python
cur.execute("SELECT * FROM users WHERE email = ?", (email,))
```
```js
db.get("SELECT * FROM users WHERE id = ?", [req.params.id])
```
Para ORM, use os métodos de filtro (`filter_by`, `where`) e nunca interpole strings. Nomes de coluna/ordenação dinâmicos: valide contra uma lista permitida (whitelist).

## P2 — Segredos para configuração (AP-02, AP-03)
**Antes**
```python
app.config["SECRET_KEY"] = "minha-chave-123"
DB_PASSWORD = "admin123"
```
**Depois**
```python
# config/settings.py
import os
SECRET_KEY = os.environ["SECRET_KEY"]            # falha cedo se faltar
DB_PATH = os.getenv("DB_PATH", "app.db")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
```
```js
// config/index.js
module.exports = { port: process.env.PORT || 3000, jwtSecret: process.env.JWT_SECRET }
```
Crie `.env.example` (sem valores reais), adicione `.env` ao `.gitignore`. Para valores obrigatórios sem default seguro, lance erro na inicialização. Para ambiente de desafio/dev, use default explícito de desenvolvimento e documente.

## P3 — Extrair lógica da rota para o controller (AP-05)
**Antes** (rota fazendo tudo)
```python
@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json()
    total = sum(i["price"] * i["qty"] for i in data["items"])
    if total > 500: total *= 0.9
    cur.execute("INSERT ...", ...)
    return jsonify({"id": cur.lastrowid, "total": total})
```
**Depois**
```python
# routes/order_routes.py
bp.add_url_rule("/orders", view_func=order_controller.create, methods=["POST"])

# controllers/order_controller.py
def create():
    payload = validate_order(request.get_json())
    order = order_model.create(payload)
    return jsonify(order_view.render(order)), 201
```
A rota só mapeia; o controller coordena; regra e SQL ficam no model (P4).

## P4 — Extrair acesso a dados e regras para o Model/Service (AP-04, AP-05, AP-10)
**Antes**: SQL e cálculo no controller.
**Depois**
```python
# models/order_model.py
DISCOUNT_THRESHOLD = 500
DISCOUNT_RATE = 0.10

def calculate_total(items):
    total = sum(i["price"] * i["qty"] for i in items)
    return total * (1 - DISCOUNT_RATE) if total > DISCOUNT_THRESHOLD else total

def create(payload, db):
    total = calculate_total(payload["items"])
    cur = db.execute("INSERT INTO orders (total) VALUES (?)", (total,))
    return {"id": cur.lastrowid, "total": total}
```
```js
// models/orderModel.js
exports.findById = (db, id) => db.get("SELECT * FROM orders WHERE id = ?", [id])
```
O model não importa `request`/`response`. Consolide a conversão linha→objeto em uma função única (remove duplicação).

## P5 — Validação centralizada e serializer/View (AP-09, AP-10, AP-03)
**Antes**
```js
app.post("/users", (req, res) => {
  const u = req.body; // usa direto
  ...
  res.json(userRow) // devolve password
})
```
**Depois**
```js
// validators/userValidator.js
exports.validateUser = (b) => {
  if (!b || typeof b.email !== "string" || !b.email.includes("@")) throw new ValidationError("email inválido")
  return { name: String(b.name).trim(), email: b.email.toLowerCase() }
}
// views/userView.js
exports.render = ({ id, name, email }) => ({ id, name, email }) // nunca expõe password
```
Lance `ValidationError` e deixe o handler central (P7) mapear para 400.

## P6 — Eliminar estado/conexão global (AP-06)
**Antes**
```python
conn = sqlite3.connect("app.db")   # global compartilhado
cache = {}                         # mutável solto
```
**Depois**
```python
# database/connection.py
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(settings.DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db: db.close()
```
Em Node, exporte uma fábrica/pool e injete no model; em Java/Spring use beans singleton gerenciados. Caches legítimos viram componente explícito com ciclo de vida.

## P7 — Tratamento de erros centralizado (AP-07)
**Antes**
```python
try: ...
except: pass
```
```js
catch (e) { res.status(200).json({ error: e.stack }) }
```
**Depois**
```python
class AppError(Exception):
    status = 500
class NotFound(AppError): status = 404
class ValidationError(AppError): status = 400

@app.errorhandler(AppError)
def handle_app_error(e): return jsonify({"error": str(e)}), e.status

@app.errorhandler(Exception)
def handle_unexpected(e):
    app.logger.exception("erro inesperado")
    return jsonify({"error": "Erro interno"}), 500
```
```js
app.use((err, req, res, next) => {
  const status = err.status || 500
  if (status === 500) console.error(err)
  res.status(status).json({ error: status === 500 ? "Erro interno" : err.message })
})
```
Nunca devolva stack trace; nunca engula exceção sem log. Em Express 4, handlers `async` precisam de `next(err)` ou wrapper.

## P8 — Substituir APIs deprecated e inseguras (AP-13, AP-03)
**Antes → Depois**
```js
new Buffer(str)                → Buffer.from(str)
fs.exists(p, cb)               → fs.promises.access(p)
const bp = require("body-parser"); app.use(bp.json()) → app.use(express.json())
app.del("/x", h)               → app.delete("/x", h)
```
```python
datetime.utcnow()              → datetime.now(timezone.utc)
Model.query.get(id)            → db.session.get(Model, id)
hashlib.md5(pw).hexdigest()    → werkzeug.security.generate_password_hash(pw)  # ou bcrypt/argon2
```
Para senhas: troque por hash com salt; migre registros existentes (rehash no próximo login ou migração) e nunca devolva o hash. Endpoints administrativos perigosos: remova ou proteja com autenticação/flag de ambiente. Confirme o equivalente na documentação da versão em uso.

## P9 — Corrigir N+1 e queries ineficientes (AP-08)
**Antes**
```python
orders = db.execute("SELECT * FROM orders").fetchall()
for o in orders:
    o["items"] = db.execute("SELECT * FROM items WHERE order_id = ?", (o["id"],)).fetchall()
```
**Depois**
```python
rows = db.execute("""
  SELECT o.id, o.total, i.id AS item_id, i.name, i.qty
  FROM orders o LEFT JOIN items i ON i.order_id = o.id
""").fetchall()
orders = group_by_order(rows)   # agrupa em memória uma vez
```
Alternativa: `WHERE order_id IN (?, ?, ...)` em lote, ou eager loading do ORM (`joinedload`, `include`). Adicione paginação (`LIMIT/OFFSET`) em listagens.

## P10 — Constantes e nomenclatura (AP-11, AP-12)
**Antes**
```js
if (status === "pendente" && total > 100) total *= 0.95
```
**Depois**
```js
const ORDER_STATUS = { PENDING: "pendente" }
const FREE_SHIPPING_MIN = 100
const SMALL_DISCOUNT = 0.05
if (status === ORDER_STATUS.PENDING && total > FREE_SHIPPING_MIN) total *= 1 - SMALL_DISCOUNT
```
Renomeie para nomes que revelam intenção, adote uma convenção por linguagem (snake_case Python, camelCase JS), troque `print/console.log` de debug por logger, remova código comentado.

## P11 — Quebrar God file e criar composition root (AP-04)
**Antes**: `app.py` de 600 linhas com config, conexão, rotas, SQL e `app.run`.
**Depois**
```python
# app.py (composition root)
from config import settings
from database import init_db
from routes import register_routes
from middlewares.error_handler import register_error_handlers

def create_app():
    app = Flask(__name__)
    app.config.from_object(settings)
    init_db(app)
    register_routes(app)
    register_error_handlers(app)
    return app

if __name__ == "__main__":
    create_app().run(port=settings.PORT)
```
```js
// server.js
const app = express()
app.use(express.json())
app.use("/api", routes)
app.use(errorHandler)
app.listen(config.port)
```
Procedimento: (1) crie pastas; (2) mova config → `config/`; (3) mova SQL/regras por entidade → `models/`; (4) mova handlers → `controllers/`; (5) deixe rotas só com mapeamento; (6) reduza o entry point; (7) suba a app e valide a cada passo.

---

## Ordem recomendada de aplicação

1. P2, P1, P8 (segurança) → 2. P11 (estrutura) → 3. P4, P3, P5 (camadas) → 4. P6, P7 → 5. P9 → 6. P10.

Após cada bloco, suba a aplicação e rode os endpoints; reverta o bloco se o comportamento mudar sem intenção.
