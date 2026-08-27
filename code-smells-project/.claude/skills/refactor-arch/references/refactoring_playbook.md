# Playbook de Refatoração Arquitetural

Este playbook fornece padrões práticos de transformação para corrigir os principais anti-patterns identificados no catálogo, contendo exemplos concretos de **Antes** (com code smell) e **Depois** (refatorado).

---

## Padrão 1: Correção de SQL Injection (Python/sqlite3)

### Antes:
```python
def get_produto_por_id(id):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
    return cursor.fetchone()
```

### Depois:
```python
def get_produto_por_id(id):
    cursor = db.cursor()
    # Uso correto de placeholders para consulta parametrizada
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
    return cursor.fetchone()
```

---

## Padrão 2: Correção de SQL Injection (Node.js/sqlite3)

### Antes:
```javascript
let query = `SELECT * FROM users WHERE email = '${email}' AND pass = '${pwd}'`;
db.get(query, (err, row) => { ... });
```

### Depois:
```javascript
// Consulta parametrizada segura utilizando array de parâmetros (?)
let query = `SELECT * FROM users WHERE email = ? AND pass = ?`;
db.get(query, [email, pwd], (err, row) => { ... });
```

---

## Padrão 3: Transformação de Callback Hell em Async/Await Promises (Node.js)

### Antes:
```javascript
this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
    this.db.run("INSERT INTO enrollments (user_id, c_id) VALUES (?, ?)", [user.id, cid], function(err) {
        self.db.run("INSERT INTO payments (enrollment_id, amount) VALUES (?, ?)", [this.lastID, price], (err) => {
            res.status(200).send("Sucesso");
        });
    });
});
```

### Depois:
```javascript
// Abstraia as chamadas do sqlite para retornarem Promises
const dbGet = (sql, params) => new Promise((res, rej) => {
    db.get(sql, params, (err, row) => err ? rej(err) : res(row));
});
const dbRun = (sql, params) => new Promise((res, rej) => {
    db.run(sql, params, function(err) { err ? rej(err) : res(this.lastID); });
});

// Use Async/Await sequencial e limpo
async function processCheckout(userId, cid, price) {
    const user = await dbGet("SELECT id FROM users WHERE email = ?", [e]);
    const enrId = await dbRun("INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [user.id, cid]);
    await dbRun("INSERT INTO payments (enrollment_id, amount) VALUES (?, ?)", [enrId, price]);
    return enrId;
}
```

---

## Padrão 4: Correção de Falsa Criptografia (Node.js)

### Antes:
```javascript
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```

### Depois:
```javascript
const bcrypt = require('bcrypt');

function secureHash(pwd) {
    // Uso de algoritmo de hash adaptativo (bcrypt) com salt dinâmico gerado automaticamente
    return bcrypt.hashSync(pwd, 10);
}
```

---

## Padrão 5: Extração de Credenciais e Segredos para Configurações (Python)

### Antes:
```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```

### Depois:
```python
import os
from dotenv import load_dotenv

load_dotenv() # Carrega variáveis do arquivo .env

app = Flask(__name__)
# Lê das variáveis de ambiente com um valor padrão seguro para desenvolvimento
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-fallback-key-deve-mudar-em-producao")
```

---

## Padrão 6: Extração de Regras de Negócio do Controller/Rotas (Python)

### Antes (Fat Controller):
```python
@app.route("/pedidos", methods=["POST"])
def criar_pedido():
    dados = request.get_json()
    # Muita lógica de estoque e e-mail no controller
    produto = cursor.execute("SELECT estoque FROM produtos WHERE id = ?", (dados["prod_id"],)).fetchone()
    if produto["estoque"] < dados["quantidade"]:
        return jsonify({"erro": "Estoque insuficiente"}), 400
    
    cursor.execute("INSERT INTO pedidos ...")
    print("ENVIANDO EMAIL...")
    return jsonify({"sucesso": True}), 201
```

### Depois (MVC Separado):
```python
# No Model ou Service:
class PedidoModel:
    @staticmethod
    def processar_pedido(usuario_id, itens):
        # Validações de estoque e persistência isolada
        # Retorna o id do pedido criado ou levanta uma exceção de domínio
        pass

# No Controller:
def criar_pedido_controller():
    dados = request.get_json()
    try:
        resultado = PedidoModel.processar_pedido(dados["usuario_id"], dados["itens"])
        # Disparo de eventos via camada de serviço de notificação dedicada
        NotificationService.send_order_created_email(dados["usuario_id"])
        return jsonify({"dados": resultado, "sucesso": True}), 201
    except DomainException as e:
        return jsonify({"erro": str(e)}), 400
```

---

## Padrão 7: Resolução de Queries N+1 (Node.js)

### Antes:
```javascript
db.all("SELECT * FROM courses", (err, courses) => {
    courses.forEach(course => {
        db.all("SELECT * FROM enrollments WHERE course_id = ?", [course.id], (err, enrollments) => {
            // Nova query para cada elemento de forma síncrona/recorrente
        });
    });
});
```

### Depois:
```javascript
// Use SQL JOIN para trazer todos os dados de forma otimizada em uma única query
const query = `
    SELECT c.title as course, e.user_id, p.amount, p.status, u.name as student
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN payments p ON p.enrollment_id = e.id
    LEFT JOIN users u ON e.user_id = u.id
`;
db.all(query, [], (err, rows) => {
    // Processamento de agregação de memória limpo e performático
});
```

---

## Padrão 8: Correção de Tratamento Genérico de Erros (Python)

### Antes:
```python
@app.route("/tasks")
def get_tasks():
    try:
        tasks = Task.query.all()
        return jsonify(tasks)
    except:
        return jsonify({'error': 'Erro interno'}), 500
```

### Depois:
```python
import logging

# Criação de um logger
logger = logging.getLogger(__name__)

@app.route("/tasks")
def get_tasks():
    try:
        tasks = Task.query.all()
        return jsonify([t.to_dict() for t in tasks])
    except Exception as e:
        # Grava o stack trace completo internamente para diagnóstico
        logger.exception("Falha ao recuperar tarefas do banco de dados")
        # Retorna mensagem limpa para o cliente
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
```

---

## Padrão 9: Substituição de APIs Deprecated (Python - datetime)

### Antes:
```python
from datetime import datetime

# deprecated no Python 3.12
data_limite = datetime.utcnow()
```

### Depois:
```python
from datetime import datetime, timezone

# Utiliza fuso horário correto timezone-aware (UTC) recomendado modernos
data_limite = datetime.now(timezone.utc)
```
