# Refactoring Playbook

Padroes concretos de transformacao para cada anti-pattern. Cada padrao descreve o conceito da mudanca com exemplos ilustrativos antes/depois.

---

## 1. SQL Injection → Parameterized Queries

**Conceito:** Substituir string concatenation por placeholders com parametros separados.

**Antes:**
```
query = "SELECT * FROM users WHERE id = " + user_input
execute(query)

query = "INSERT INTO users (name) VALUES ('" + name + "')"
execute(query)
```

**Depois:**
```
query = "SELECT * FROM users WHERE id = ?"
execute(query, [user_input])

query = "INSERT INTO users (name) VALUES (?)"
execute(query, [name])
```

**Para queries dinamicas com filtros opcionais:**
```
// Antes: concatenando filtros
query = "SELECT * FROM products WHERE 1=1"
if term:
    query += " AND name LIKE '%" + term + "%'"
if category:
    query += " AND category = '" + category + "'"

// Depois: acumulando parametros
query = "SELECT * FROM products WHERE 1=1"
params = []
if term:
    query += " AND name LIKE ?"
    params.add("%" + term + "%")
if category:
    query += " AND category = ?"
    params.add(category)
execute(query, params)
```

---

## 2. Hardcoded Credentials → Environment Variables

**Conceito:** Mover todos os valores sensiveis para variaveis de ambiente, acessadas via modulo de configuracao.

**Antes:**
```
SECRET_KEY = "minha-chave-super-secreta-123"
DB_PASSWORD = "senha_do_banco"
SMTP_PASSWORD = "senha123"
PAYMENT_KEY = "pk_live_1234567890abcdef"
```

**Depois (modulo de configuracao):**
```
// Modulo config:
SECRET_KEY = env("SECRET_KEY")                    // obrigatorio, falha se nao definido
DB_URI = env("DATABASE_URL", default="local.db")  // com default para dev
SMTP_PASSWORD = env("SMTP_PASSWORD", default="")  // opcional
PAYMENT_KEY = env("PAYMENT_GATEWAY_KEY")
```

**Criar arquivo de exemplo** listando todas as variaveis necessarias sem seus valores reais.

---

## 3. God Class → Split by Domain

**Conceito:** Dividir arquivo que acumula multiplos dominios em um modulo por dominio.

**Antes (um arquivo com tudo):**
```
// data_access.py — 300+ linhas
function get_all_products(): ...
function get_product_by_id(id): ...
function create_user(name, email, password): ...
function create_order(user_id, items): ...
function get_sales_report(): ...
```

**Depois (um modulo por dominio):**
```
// models/product_model
class ProductModel:
    function get_all(): ...
    function get_by_id(id): ...
    function create(data): ...
    function search(filters): ...

// models/user_model
class UserModel:
    function get_all(): ...
    function get_by_id(id): ...
    function create(data): ...
    function authenticate(email, password): ...

// models/order_model
class OrderModel:
    function create(user_id, items): ...
    function get_by_user(user_id): ...
    function get_all(): ...
    function update_status(id, status): ...
```

---

## 4. Business Logic in Routes → Extract to Controller/Service

**Conceito:** Route apenas extrai dados do request e chama controller. Controller orquestra a logica e chama models/services.

**Antes (tudo no handler):**
```
route POST /orders:
    data = request.body
    // validacao inline
    if not data.user_id: return error("user_id required")
    // chamada ao banco direta
    result = OrderModel.create(data.user_id, data.items)
    // notificacao inline
    send_email("New order " + result.id)
    send_sms("Order received")
    return response(result)
```

**Depois — Route:**
```
route POST /orders:
    data = request.body
    result, status = OrderController.create(data)
    return response(result, status)
```

**Depois — Controller:**
```
class OrderController:
    function create(data):
        user_id = data.user_id
        items = data.items
        // validacao de negocio
        if not user_id or not items:
            return {error: "Invalid data"}, 400
        // delega ao model
        result = OrderModel.create(user_id, items)
        // delega ao service
        NotificationService.notify_new_order(result.id, user_id)
        return {data: result, success: true}, 201
```

---

## 5. Sensitive Data Exposure → Filter in Serialization

**Conceito:** Garantir que serializacao de modelos nunca inclua campos sensiveis.

**Antes:**
```
function to_dict():
    return {
        id: self.id,
        name: self.name,
        email: self.email,
        password: self.password,    // EXPÕE SENHA!
        role: self.role
    }
```

**Depois:**
```
function to_dict():
    return {
        id: self.id,
        name: self.name,
        email: self.email,
        role: self.role,
        active: self.active,
        created_at: self.created_at
    }
    // password removido da serializacao publica
```

**Tambem aplicar a health checks e endpoints de debug:**
```
// Antes: health check expondo secrets
return {secret_key: config.SECRET_KEY, db_path: config.DB_URI}

// Depois: health check sem dados sensiveis
return {status: "ok", database: "connected"}
```

---

## 6. Weak Cryptography → Secure Hashing

**Conceito:** Substituir algoritmos fracos ou implementacoes caseiras por bibliotecas criptograficas reconhecidas da stack.

**Antes:**
```
// Hash inseguro
hash = md5(password)
// ou funcao caseira
hash = custom_encode(password)
```

**Depois:**
```
// Usar biblioteca de hashing segura da stack
// (bcrypt, argon2, werkzeug.security, etc.)
hash = secure_hash(password)   // automaticamente gera salt
verify = secure_verify(password, hash)
```

**A biblioteca especifica depende da stack detectada** — o importante e que:
- Usa algoritmo projetado para senhas (bcrypt, argon2, scrypt)
- Gera salt automaticamente
- Nao e reversivel

---

## 7. Callback/Promise Nesting → Linear Async Flow

**Conceito:** Transformar cadeias profundas de callbacks/promises em fluxo linear.

**Antes (aninhamento profundo):**
```
async_op1(params, (result1) ->
    async_op2(result1, (result2) ->
        async_op3(result2, (result3) ->
            async_op4(result3, (result4) ->
                return response(result4)
            )
        )
    )
)
```

**Depois (fluxo linear):**
```
// Promisify operacoes assincronas se necessario
result1 = await async_op1(params)
result2 = await async_op2(result1)
result3 = await async_op3(result2)
result4 = await async_op4(result3)
return response(result4)
```

**Para linguagens sem async/await nativo**, encadear promises ou usar o padrao equivalente da stack.

---

## 8. N+1 Queries → JOINs / Batch Loading

**Conceito:** Substituir queries dentro de loops por uma unica query otimizada com JOIN ou batch loading.

**Antes (1 + N + N queries):**
```
orders = query("SELECT * FROM orders")
for order in orders:
    items = query("SELECT * FROM order_items WHERE order_id = " + order.id)
    for item in items:
        product = query("SELECT name FROM products WHERE id = " + item.product_id)
```

**Depois (1 query com JOIN):**
```
results = query("""
    SELECT o.*, oi.product_id, oi.quantity, oi.price, p.name as product_name
    FROM orders o
    LEFT JOIN order_items oi ON oi.order_id = o.id
    LEFT JOIN products p ON p.id = oi.product_id
    WHERE o.user_id = ?
""", [user_id])
// Agrupar resultados por order no codigo
```

**Para ORMs**, usar eager loading:
```
orders = Order.query.include("items.product").filter(user_id)
```

---

## 9. Global Mutable State → Dependency Injection

**Conceito:** Eliminar estado global mutavel, passando dependencias via parametros ou construtores.

**Antes (estado global):**
```
// Modulo exportando estado mutavel
global connection = null
global cache = {}
global counter = 0

function get_connection():
    if connection == null:
        connection = create_connection(...)
    return connection
```

**Depois (injecao):**
```
// Factory function — cada chamada cria instancia independente
function create_connection(config):
    conn = connect(config.db_uri)
    conn.configure(config.options)
    return conn

// No entry point, criar e injetar
conn = create_connection(app_config)
productModel = new ProductModel(conn)
productController = new ProductController(productModel)
```

---

## 10. Duplicated Code → Extract Shared Functions

**Conceito:** Identificar logica repetida e extrair para funcoes/metodos compartilhados.

**Antes (validacao duplicada):**
```
// Em criar:
if not name: return error("Name required")
if not email: return error("Email required")
if len(name) < 3: return error("Name too short")

// Em atualizar (copia):
if not name: return error("Name required")
if not email: return error("Email required")
if len(name) < 3: return error("Name too short")
```

**Depois (funcao compartilhada):**
```
function validate_user(data):
    if not data.name: return error("Name required")
    if not data.email: return error("Email required")
    if len(data.name) < 3: return error("Name too short")
    return null

// Em criar:
validation = validate_user(data)
if validation: return validation

// Em atualizar:
validation = validate_user(data)
if validation: return validation
```

**Antes (logica de verificacao copiada em N arquivos):**
```
// Arquivo 1, 2 e 3 — mesma logica:
if entity.due_date:
    if entity.due_date < now():
        if entity.status != "done" and entity.status != "cancelled":
            is_overdue = true
```

**Depois (metodo no model):**
```
// No model:
function is_overdue():
    if not self.due_date: return false
    if self.due_date >= now(): return false
    if self.status == "done" or self.status == "cancelled": return false
    return true

// Em qualquer lugar:
result.overdue = entity.is_overdue()
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
8. Dados sensiveis nao sao expostos em respostas de API?
