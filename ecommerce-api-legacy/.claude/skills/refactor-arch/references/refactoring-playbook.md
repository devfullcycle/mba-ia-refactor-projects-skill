# Playbook de refatoração (Fase 3)

Padrões de transformação em **pseudocódigo neutro de linguagem**. Cada um liga um anti-pattern a um antes/depois. **Traduza para a forma idiomática da stack** usando o Stack Profile (estrutura, DI, erros, validação, segurança, comandos). Preserve rotas, status e formato de resposta.

Convenção do pseudocódigo: `route(METHOD, path, handler)`, `db.execute(sql, [params])`, `request.body`, `respond(status, data)`, `env("NAME")`, `raise Error(msg, status)`.

Índice: PB-01 Separar camadas · PB-02 Config/segredos · PB-03 Consultas parametrizadas · PB-04 Segurança de auth/dados · PB-05 Extrair lógica do controller · PB-06 DI e fim do estado global · PB-07 Error handling central · PB-08 Resolver N+1 · PB-09 Validação de entrada · PB-10 Eliminar duplicação · PB-11 Substituir APIs deprecated · PB-12 Legibilidade

---

## PB-01 Separar God File em camadas e domínios (AP-01, AP-07)

**Antes** (um arquivo: rota + consulta + regra)
```pseudo
route(POST, "/products", function(request):
    data = request.body
    db.execute("INSERT INTO products (name, price) VALUES ('" + data.name + "', " + data.price + ")")
    respond(201, {ok: true})
)
```
**Depois**
```pseudo
// routes/product_routes
route(POST, "/products", product_controller.create)

// controllers/product_controller
function create(request):
    data = validate_product(request.body)        // PB-09
    product = product_model.insert(data)
    respond(201, product)

// models/product_model
function insert(data):
    id = db.execute("INSERT INTO products (name, price) VALUES (?, ?)", [data.name, data.price])
    return {id: id, name: data.name, price: data.price}
```
**Passos**: um módulo por domínio e camada; mova sem mudar comportamento; compile/execute a cada domínio movido.

---

## PB-02 Config e segredos externos (AP-02, AP-08)

**Antes**
```pseudo
SECRET = "my-super-secret-123"
start_server(host="0.0.0.0", debug=true)
```
**Depois**
```pseudo
// config/settings
function required(name):
    v = env(name)
    if v is empty: raise Error("Missing required config: " + name)
    return v

SECRET = required("SECRET")
DEBUG  = env("APP_DEBUG", default="false") == "true"
PORT   = to_int(env("PORT", default="8080"))
```
**Passos**: crie um arquivo de exemplo de configuração com placeholders (nunca valores reais); documente as variáveis; se o segredo estava versionado, recomende **rotacioná-lo**; use o mecanismo de config do Stack Profile.

---

## PB-03 Consultas parametrizadas (AP-03)

**Antes**
```pseudo
db.query("SELECT * FROM users WHERE email = '" + email + "'")
```
**Depois**
```pseudo
db.query("SELECT * FROM users WHERE email = ?", [email])
```
**Passos**: troque **toda** consulta dinâmica; identificadores dinâmicos (ordenação, coluna) só por **lista de permissão**, nunca interpolados; use o formato de placeholder do driver/ORM da stack.

---

## PB-04 Segurança de autenticação e dados (AP-04)

**Antes**
```pseudo
stored = weak_hash(password)                  // hash rápido/sem sal
respond(200, user)                            // inclui o campo password
route(POST, "/admin/reset-db", reset_handler) // sem autenticação
```
**Depois**
```pseudo
stored = password_hash(password)              // algoritmo recomendado no Stack Profile
ok = password_verify(input, stored)

function to_public(user): return {id: user.id, name: user.name, email: user.email}
route(POST, "/admin/reset-db", require_auth(admin_only(reset_handler)))   // ou remover
```
**Passos**: use o algoritmo de hash recomendado pela fonte da stack; exponha só campos listados (lista de permissão); proteja ou **remova** endpoints destrutivos/arbitrários; migração de hashes antigos (re-hash no login) vai em "Deviations / Needs Human". Mudanças de comportamento de segurança vão em **Deviations**.

---

## PB-05 Extrair lógica de negócio do controller (AP-05, AP-07)

**Antes**
```pseudo
route(POST, "/checkout", function(request):
    total = 0
    for item in request.body.items: total += item.price * item.qty
    if total > 500: total = total * 0.9
    db.execute("INSERT INTO orders ...")
    respond(200, {total: total})
)
```
**Depois**
```pseudo
// routes
route(POST, "/checkout", order_controller.checkout)

// controller (orquestra)
function checkout(request):
    result = order_service.checkout(request.body)
    respond(201, result)

// service (regra, testável sem HTTP)
DISCOUNT_THRESHOLD = 500
DISCOUNT_RATE = 0.10
function checkout(payload):
    subtotal = sum(i.price * i.qty for i in payload.items)
    total = subtotal * (1 - DISCOUNT_RATE) if subtotal > DISCOUNT_THRESHOLD else subtotal
    return order_model.create(payload.items, total)
```
**Passos**: controller curto (poucas linhas); regra em função testável; model só persiste. Preserve o status original se o contrato o definir.

---

## PB-06 Injeção de dependência e fim do estado global (AP-06)

**Antes**
```pseudo
db = connect("app.db")                  // global compartilhado
cache = {}                              // global mutável
class OrderService:
    repo = new OrderRepo()              // cria a dependência dentro
```
**Depois**
```pseudo
// entry point (composition root)
function build_app(config):
    db = connect(config.database)
    repo = new OrderRepo(db)
    service = new OrderService(repo)    // dependência injetada
    controller = new OrderController(service)
    register_routes(controller)
    register_error_handlers()
```
**Passos**: crie as dependências no entry point e passe por construtor/parâmetro; troque estado global mutável por escopo de requisição ou objeto injetado; use o mecanismo de DI que o Stack Profile indica (container, fábrica, construtor), sem impor framework novo.

---

## PB-07 Error handling centralizado (AP-11, AP-08)

**Antes**
```pseudo
try:  ...
catch e:  respond(500, {error: e.message, stack: e.stack})
```
**Depois**
```pseudo
// middlewares/error_handler
class AppError(message, status)

function handle_error(err):
    if err is AppError: respond(err.status, {error: err.message})
    else:
        log.error(err)                              // detalhes só no log
        respond(500, {error: "Internal error"})

register_error_handler(handle_error)                // no mecanismo idiomático da stack
```
**Passos**: controllers/models levantam `AppError`; sem captura vazia; **preserve o formato de erro original** se houver contrato.

---

## PB-08 Resolver N+1 (AP-09)

**Antes**
```pseudo
orders = db.query("SELECT * FROM orders")
for order in orders:
    order.items = db.query("SELECT * FROM items WHERE order_id = ?", [order.id])
```
**Depois**
```pseudo
orders = db.query("SELECT * FROM orders")
ids = [o.id for o in orders]
items = db.query("SELECT * FROM items WHERE order_id IN (<placeholders de ids>)", ids)
by_order = group_by(items, key="order_id")
for order in orders: order.items = by_order.get(order.id, [])
```
**Passos**: uma consulta por relação, não por item (JOIN, conjunto de IDs ou carregamento antecipado do ORM, conforme a stack); trate lista vazia de IDs; só gere placeholders, nunca valores.

---

## PB-09 Validação de entrada (AP-10)

**Antes**
```pseudo
price = to_number(request.body.price)    // sem checar presença/tipo/faixa
```
**Depois**
```pseudo
function validate_product(body):
    if body is not an object: raise AppError("Invalid body", 400)
    name = trim(body.name)
    if name is empty: raise AppError("name is required", 400)
    price = try_to_number(body.price) or raise AppError("price must be numeric", 400)
    if price < 0: raise AppError("price must be >= 0", 400)
    return {name: name, price: price}
```
**Passos**: valide na borda (controller), uma vez e de forma reutilizável; use o mecanismo de validação do Stack Profile se já fizer parte do projeto, sem adicionar dependências desnecessárias; mantenha mensagens/status originais quando existirem.

---

## PB-10 Eliminar duplicação (AP-12)

**Antes**
```pseudo
return {id: row[0], name: row[1], price: row[2]}      // repetido em 5 lugares
```
**Depois**
```pseudo
function product_to_dto(row): return {id: row.id, name: row.name, price: row.price}
```
**Passos**: extraia serializer/validador/helper para um único lugar do domínio; substitua **todas** as ocorrências; confirme saída idêntica.

---

## PB-11 Substituir APIs deprecated (AP-13)

**Antes → Depois** (forma geral; os símbolos reais vêm do Stack Profile)
```pseudo
old_api_call(args)                 →  modern_api_call(args)        // fonte: <URL do guia de migração>
callback_nested_flow(...)          →  structured_async_flow(...)   // quando a stack oferece
```
**Passos**: confirme a **versão instalada** e o comportamento do substituto (tipo de retorno, tratamento de fuso/encoding, erros); verifique serialização e comparações afetadas; mantenha o formato de saída; troque **todas** as ocorrências do relatório; registre em Deviations qualquer mudança observável.

---

## PB-12 Legibilidade: magic numbers, nomes, código morto (AP-14/15/16)

**Antes**
```pseudo
if s == 3 and t > 0.1: ...
function p(d): ...
print("debug", x)
// old = compute(x)
```
**Depois**
```pseudo
STATUS_CANCELLED = 3
MIN_RATE = 0.1
if status == STATUS_CANCELLED and rate > MIN_RATE: ...
function process_order(data): ...
log.debug("order processed", order_id)
```
**Passos**: constantes num módulo de config/constantes; renomeie com refactor seguro (todas as referências); remova código comentado e declarações não usadas; troque saída de debug por logger. Faça por último: baixo risco, alto volume.

---

## Ordem recomendada de aplicação

PB-02 → PB-03/PB-04 → PB-01 → PB-05/PB-06 → PB-09 → PB-07 → PB-08 → PB-10 → PB-11 → PB-12.
Segurança primeiro, estrutura depois, estilo por último.

## Verificação após cada padrão

- Compila/inicia segundo os comandos do Stack Profile?
- As rotas afetadas respondem com o mesmo status e formato?
- O sinal de detecção do anti-pattern sumiu no re-scan?
