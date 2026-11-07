# Refactoring Playbook (Fase 3)

Transformações concretas **antes → depois** para os anti-patterns do catálogo.
Cada padrão aponta para o(s) `AP-0X` que resolve. Exemplos em Python/Flask e
Node/Express para reforçar que o padrão é agnóstico — aplique o equivalente na
stack detectada.

---

## T-01 · Extrair configuração para env (resolve AP-02, AP-17)

**Antes**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```
**Depois** — `config/settings.py`
```python
import os
class Config:
    SECRET_KEY = os.environ["SECRET_KEY"]
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
```
`.env.example`
```
SECRET_KEY=troque-por-um-segredo-forte
FLASK_DEBUG=0
DB_PATH=loja.db
```
Node: `const config = { secret: process.env.SECRET_KEY, port: process.env.PORT || 3000 }`.

---

## T-02 · Parametrizar queries (resolve AP-03)

**Antes**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("...WHERE email = '" + email + "' AND senha = '" + senha + "'")
```
**Depois**
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
```
Busca dinâmica com filtros opcionais: construa a cláusula com placeholders e
uma lista de params.
```python
clauses, params = ["1=1"], []
if termo:
    clauses.append("(nome LIKE ? OR descricao LIKE ?)"); params += [f"%{termo}%", f"%{termo}%"]
if categoria:
    clauses.append("categoria = ?"); params.append(categoria)
cursor.execute(f"SELECT * FROM produtos WHERE {' AND '.join(clauses)}", params)
```

---

## T-03 · Quebrar God File em models por entidade (resolve AP-01)

**Antes:** `models.py` com produtos + usuários + pedidos + relatórios + SQL cru.
**Depois:**
```
models/
├── base_model.py        # conexão/execução parametrizada compartilhada
├── produto_model.py     # ProdutoModel: CRUD + serialização de produto
├── usuario_model.py     # UsuarioModel: CRUD + auth
└── pedido_model.py      # PedidoModel: criação de pedido, itens, relatório
```
Cada model recebe a conexão por injeção e expõe métodos de alto nível
(`list()`, `get(id)`, `create(...)`) com queries parametrizadas e `to_dict()`.

---

## T-04 · Mover regra de negócio da rota para service (resolve AP-05)

**Antes** (no handler HTTP): cálculo de total, verificação de estoque, criação
de itens, disparo de "e-mail/SMS/push" via `print`.
**Depois** — `services/pedido_service.py`
```python
class PedidoService:
    def __init__(self, pedido_model, produto_model, notifier):
        self._pedidos = pedido_model
        self._produtos = produto_model
        self._notifier = notifier

    def criar(self, usuario_id, itens):
        total = self._calcular_total(itens)   # regra de domínio isolada
        pedido_id = self._pedidos.criar(usuario_id, itens, total)
        self._notifier.pedido_criado(usuario_id, pedido_id)
        return {"pedido_id": pedido_id, "total": total}
```
O controller só chama `service.criar(...)` e devolve JSON.

---

## T-05 · Hash de senha forte + parar de expor segredos (resolve AP-04)

**Antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
# e to_dict() devolvendo 'password'
```
**Depois**
```python
from werkzeug.security import generate_password_hash, check_password_hash
def set_password(self, pwd): self.password = generate_password_hash(pwd)
def check_password(self, pwd): return check_password_hash(self.password, pwd)
def to_dict(self):            # NUNCA inclui o hash
    return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}
```
Node: substituir `badCrypto` por `bcrypt.hash(pwd, 10)` / `bcrypt.compare`.
Também remover `secret_key` de respostas como `/health`.

---

## T-06 · Injeção de dependência em vez de estado global (resolve AP-06, AP-07)

**Antes**
```python
db_connection = None          # global mutável
def get_db():
    global db_connection
    if db_connection is None: db_connection = sqlite3.connect(...)
    return db_connection
```
**Depois** — fábrica + injeção no composition root
```python
# config/database.py
def create_connection(path):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
# app.py
conn = create_connection(Config.DB_PATH)
produto_model = ProdutoModel(conn)          # injeta a conexão
produto_ctrl  = ProdutoController(produto_model)
```
Node: remover `globalCache`/`totalRevenue` do módulo `utils`; passar `db` ao
construir controllers/repos.

---

## T-07 · Achatar callback hell com async/await (resolve AP-08)

**Antes** (Express + sqlite3 callbacks aninhados, contadores `pending--`).
**Depois** — promisify + `async/await`
```js
const { promisify } = require('util');
class Db {
  constructor(db) { this.get = promisify(db.get.bind(db)); this.all = promisify(db.all.bind(db)); this.run = promisify(db.run.bind(db)); }
}
async function checkout(req, res, next) {
  try {
    const course = await db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [cid]);
    if (!course) return res.status(404).json({ error: "Curso não encontrado" });
    const user = await userRepo.findOrCreate(email, name, pwd);
    const enrollment = await enrollmentRepo.create(user.id, cid);
    // ...
    res.status(200).json({ msg: "Sucesso", enrollment_id: enrollment.id });
  } catch (err) { next(err); }   // delega ao error handler central
}
```

---

## T-08 · Eliminar query N+1 (resolve AP-09)

**Antes**
```python
for row in pedidos:
    cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in itens:
        cursor.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
**Depois** — uma query com JOIN (ou `IN (...)` + agrupamento em memória)
```python
cursor.execute("""
    SELECT p.id pedido_id, ip.produto_id, pr.nome produto_nome,
           ip.quantidade, ip.preco_unitario
    FROM pedidos p
    JOIN itens_pedido ip ON ip.pedido_id = p.id
    JOIN produtos pr ON pr.id = ip.produto_id
""")
# agrupa por pedido_id no código
```
SQLAlchemy: usar `joinedload`/`selectinload` em vez de `Model.query.get()` dentro de loop.

---

## T-09 · Centralizar validação (resolve AP-10, AP-18)

**Antes:** blocos `if not x: return 400` repetidos em create/update e em
`utils.process_task_data`.
**Depois** — validador único por entidade (schema marshmallow/pydantic ou
função dedicada) chamado pelas rotas:
```python
# validators/task_validator.py
def validate_task(data, partial=False):
    errors = {}
    # título, status, prioridade, due_date, tags ... em UM lugar
    return cleaned, errors
```
A rota só faz: `cleaned, errors = validate_task(body)` → 400 se `errors`.

---

## T-10 · Serializer único (resolve AP-11)

**Antes:** montagem manual de dicionário repetida em `get_tasks`, `to_dict`,
`get_user_tasks`, com `overdue` recalculado inline em 3 lugares.
**Depois:** `Task.to_dict()` é a única fonte; `is_overdue()` vive no model e é
chamado por ele:
```python
def to_dict(self):
    d = {...}; d["overdue"] = self.is_overdue(); return d
```
Todas as rotas usam `task.to_dict()`.

---

## T-11 · Error handler centralizado (resolve AP-14)

**Antes:** `try/except Exception as e: return jsonify({"erro": str(e)}), 500`
em cada função (vaza detalhes).
**Depois** — Flask
```python
# middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle(err):
        app.logger.exception(err)
        return jsonify({"error": "Erro interno"}), 500
    @app.errorhandler(404)
    def not_found(err): return jsonify({"error": "Não encontrado"}), 404
```
Express: `app.use((err, req, res, next) => { logger.error(err); res.status(err.status||500).json({error: "Erro interno"}); })` registrado por último.

---

## T-12 · Remover/Proteger endpoints administrativos perigosos (resolve AP-12)

**Antes:** `/admin/reset-db` apaga tudo; `/admin/query` executa SQL do body;
`DELETE /users/:id` deixa órfãos.
**Depois:** remover `/admin/query` (nunca exponha SQL arbitrário); proteger
`/admin/*` com middleware de auth + role; deleção com cascata/transação para
não deixar dados órfãos. Se o endpoint existir só para dev, isolá-lo atrás de
flag de ambiente.

---

## T-13 · Substituir APIs deprecated (resolve AP-13)

| Antes | Depois |
|---|---|
| `datetime.utcnow()` | `datetime.now(datetime.UTC)` |
| `Model.query.get(id)` | `db.session.get(Model, id)` |
| `Task.query.filter_by(...)` (estilo legacy) | `db.session.execute(db.select(Task).filter_by(...))` |
| `new Buffer(x)` | `Buffer.from(x)` |
| `md5`/base64 p/ senha | `bcrypt`/`werkzeug.security` |
| `before_first_request` | init dentro de `with app.app_context()` |

Troque mantendo o comportamento; rode a app para confirmar que nada quebrou.

---

## T-14 · Logger no lugar de print/console.log (resolve AP-15, AP-16)

**Antes:** `print("ENVIANDO EMAIL...")`, `console.log(\`...cartão ${cc}...\`)`,
magic numbers de desconto.
**Depois:** `logging.getLogger(__name__)` / logger configurável; nunca logar
dado sensível (cartão, senha); extrair faixas e limites para constantes
nomeadas em config (`DESCONTO_FAIXAS`, `PRIORITY_RANGE = (1, 5)`).

---

## Ordem sugerida de aplicação

1. Config + segredos (T-01) e DEBUG.
2. Estrutura de pastas + split de models (T-03) com queries parametrizadas (T-02).
3. Services/controllers extraindo regra da rota (T-04), DI (T-06).
4. Segurança: senha (T-05), endpoints perigosos (T-12).
5. Qualidade: N+1 (T-08), validação (T-09), serializer (T-10), callbacks (T-07).
6. Cross-cutting: error handler (T-11), logging/constantes (T-14), deprecated (T-13).
7. **Validar**: boot + cada endpoint. Só então declarar concluído.
