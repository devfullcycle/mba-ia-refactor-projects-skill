# Playbook de Refatoração (Fase 3)

Cada padrão mapeia um anti-pattern do catálogo para uma transformação concreta, com exemplo antes/depois. Os exemplos são ilustrativos (Python/Flask e Node/Express) — aplique o **princípio** na stack do projeto atual.

---

## RF-01 — Parametrizar queries (corrige AP-01)

**Antes (Python):**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
```
**Depois:**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
```

**Antes (Node):**
```js
db.get(`SELECT * FROM courses WHERE id = ${cid}`, cb);
```
**Depois:**
```js
db.get("SELECT * FROM courses WHERE id = ?", [cid], cb);
```
Princípio: valores dinâmicos sempre por placeholder, nunca concatenados.

---

## RF-02 — Externalizar configuração e segredos (corrige AP-02)

**Antes:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```
**Depois (`config/settings.py`):**
```python
import os
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
```
```python
# app entry point
from config import settings
app.config["SECRET_KEY"] = settings.SECRET_KEY
```
Node equivalente: `const paymentKey = process.env.PAYMENT_GATEWAY_KEY;`. Nunca devolver segredo em resposta HTTP (remover de `/health` etc.).

---

## RF-03 — Hash de senha seguro + não serializar senha (corrige AP-03)

**Antes:**
```python
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()
```
**Depois:**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)
```
E remover `password`/`senha` do `to_dict()`/serialização de resposta.

Node (substituir `badCrypto`):
```js
const bcrypt = require('bcrypt');
const hash = await bcrypt.hash(pwd, 10);
// verificação: await bcrypt.compare(pwd, hash)
```

---

## RF-04 — Remover/proteger endpoint perigoso (corrige AP-04)

**Antes:**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    query = request.get_json().get("sql", "")
    cursor.execute(query)  # SQL arbitrário do cliente
```
**Depois:** eliminar o endpoint. Se uma operação administrativa for realmente necessária, expor uma ação específica e tipada (ex.: `POST /admin/produtos/reindex`) protegida por autenticação/autorização — nunca aceitar SQL bruto. Endpoints destrutivos (`reset-db`) exigem auth + confirmação explícita, ou saem para um script de manutenção fora da API.

---

## RF-05 — Quebrar God Class / God File em camadas (corrige AP-05)

**Antes:** `AppManager.js` com DB + schema + seed + todas as rotas.
**Depois:**
```
config/db.js            # cria/abre a conexão
models/user.model.js    # acesso a dados de user
models/course.model.js
controllers/checkout.controller.js
routes/checkout.routes.js
middlewares/error.js
seed.js                 # schema + dados iniciais, fora da API
app.js                  # composition root: liga tudo
```
Migre cada bloco para sua camada, mantendo rotas e respostas idênticas.

---

## RF-06 — Mover lógica de negócio da rota para model/service (corrige AP-06, AP-13)

**Antes (regra "overdue" duplicada na rota):**
```python
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            task_data['overdue'] = True
```
**Depois (usar o método já existente no model):**
```python
# models/task.py já tem is_overdue()
task_data['overdue'] = t.is_overdue()
```
Controller só orquestra; regra vive no model/service e é reutilizada em todos os pontos.

---

## RF-07 — Encapsular estado global mutável (corrige AP-07, AP-10)

**Antes:**
```js
let globalCache = {};
let totalRevenue = 0;
function logAndCache(key, data) { globalCache[key] = data; }
```
**Depois:**
```js
class CacheService {
  constructor() { this._store = {}; }
  set(key, data) { this._store[key] = data; }
  get(key) { return this._store[key]; }
}
module.exports = CacheService; // injetado onde for preciso
```
Dependências passam a ser injetadas (construtor/parâmetro), não instanciadas internamente — permite mock em teste.

---

## RF-08 — Achatar callback hell e tratar erros (corrige AP-09)

**Antes:**
```js
db.get(q1, (err, a) => {
  db.get(q2, (err, b) => {
    db.run(q3, (err) => { res.json(...); });
  });
});
```
**Depois (async/await com wrapper Promise):**
```js
const a = await dbGet(q1, [p1]);
if (!a) return res.status(404).send("...");
const b = await dbGet(q2, [p2]);
await dbRun(q3, [p3]);
res.json(...);
// dbGet/dbRun = util.promisify das funções do driver, ou usar biblioteca async
```
Erros tratados por `try/catch` + middleware de erro central.

---

## RF-09 — Adicionar autenticação e tokens reais (corrige AP-08)

**Antes:**
```python
return jsonify({'token': 'fake-jwt-token-' + str(user.id)})
```
**Depois:**
```python
import jwt, datetime  # PyJWT
payload = {"sub": user.id, "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)}
token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
```
Middleware verifica o token assinado nas rotas protegidas e injeta o usuário no contexto. (Se adicionar dependência de JWT não for desejável no escopo, no mínimo remover o token forjável e documentar a limitação — mas preservar o formato de resposta.)

---

## RF-10 — Eliminar query N+1 (corrige AP-11)

**Antes:**
```python
for row in pedidos:
    cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in itens:
        cursor.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
**Depois:** uma query com JOIN (ou `IN (...)`), agrupando em memória:
```python
cursor.execute("""
    SELECT p.id AS pedido_id, ip.produto_id, pr.nome, ip.quantidade, ip.preco_unitario
    FROM pedidos p
    JOIN itens_pedido ip ON ip.pedido_id = p.id
    JOIN produtos pr ON pr.id = ip.produto_id
""")
```
Com ORM: usar eager loading (`joinedload`) em vez de acessar relações dentro de loop.

---

## RF-11 — Centralizar e reutilizar validação (corrige AP-12)

**Antes:** mesmo bloco de `if not dados: ...` copiado em criar e atualizar.
**Depois:** um validador único por entidade e reutilizado:
```python
def validar_produto(dados):
    erros = []
    if not dados.get("nome") or len(dados["nome"]) < 2:
        erros.append("Nome inválido")
    # ...
    return erros
```
Ou usar schema (marshmallow/pydantic/Joi). Controllers chamam o validador; sem duplicação.

---

## RF-12 — Tratamento de erro centralizado + logging estruturado (corrige AP-14, AP-15, AP-19)

**Antes:** cada rota com `try/except` genérico e `print(...)`.
**Depois (Flask):**
```python
import logging
logger = logging.getLogger(__name__)

@app.errorhandler(Exception)
def handle_error(e):
    logger.exception("Erro não tratado")
    return jsonify({"erro": "Erro interno"}), 500
```
Rotas ficam limpas; erros vão para um único handler; `logging` substitui `print`. Express: middleware `(err, req, res, next)` no fim da cadeia.

---

## RF-13 — Constantes nomeadas e limpeza (corrige AP-16, AP-17, AP-18)

**Antes:**
```python
if faturamento > 10000: desconto = faturamento * 0.1
categorias_validas = ["informatica", "moveis", ...]  # repetido em vários pontos
```
**Depois:** extrair para `config`/módulo de constantes:
```python
FAIXA_DESCONTO_ALTO = 10000
TAXA_DESCONTO_ALTO = 0.10
CATEGORIAS_VALIDAS = ["informatica", "moveis", ...]
```
Renomear variáveis opacas (`u, e, p` → `usuario, email, senha`) e remover imports/código morto.

---

## RF-14 — Substituir APIs deprecated (corrige seção deprecated)

Trocar pelo equivalente moderno conforme o catálogo. Exemplos:
- `datetime.utcnow()` → `datetime.now(datetime.UTC)`
- body-parser externo → `express.json()` nativo
- `var` → `const`/`let`
- MD5 para senha → `generate_password_hash`/`bcrypt` (ver RF-03)

Preservar o comportamento observável; a troca é interna.
