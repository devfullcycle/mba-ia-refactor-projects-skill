# Refactor Playbook

## Objetivo
Fornecer padrões concretos de transformação para anti-patterns comuns em projetos legacy.

## 1. God Class / God Module
Antes:
- Um arquivo contém rotas, lógica de negócio e queries.

Depois:
- Rotas em `routes/`
- Fluxo em `controllers/`
- Persistência em `models/`

Exemplo Python:
- `app.py` registra rotas
- `controllers/produto_controller.py` chama `models/produto_model.py`
- `models/produto_model.py` executa SELECT/INSERT.

## 2. Hardcoded Secrets
Antes:
- `app.config['SECRET_KEY'] = 'abc'`
- `config.paymentGatewayKey = 'pk_live_...'`

Depois:
- `config/settings.py` lê `os.environ.get('SECRET_KEY')`
- `config/index.js` lê `process.env.PAYMENT_GATEWAY_KEY`

## 3. SQL Injection / Query Concatenation
Antes:
- `cursor.execute("SELECT * FROM usuarios WHERE id = " + str(id))`
- `db.run("INSERT INTO users VALUES ('" + name + "')")`

Depois:
- `cursor.execute("SELECT * FROM usuarios WHERE id = ?", (id,))`
- `db.run("INSERT INTO users VALUES (?)", [name])`

## 4. Business Logic in Controller/Route
Antes:
- Rota valida, calcula totas e atualiza estoque diretamente.

Depois:
- Rota extrai dados e chama `order_controller.create_order()`.
- Controller chama `order_service.process_order()` e `order_model.update_stock()`.

## 5. Global Mutable State
Antes:
- `let globalCache = {}`
- `db_connection = None`

Depois:
- Criar módulo de cache imutável ou session-scoped.
- Inicializar conexão de DB em `database.py`/`db.js` com função getter.

## 6. N+1 Query
Antes:
- `for item in pedidos: cursor.execute('SELECT ...')`

Depois:
- Use JOIN ou query única para buscar itens associados.
- Ou faça query em lote para IDs coletados.

## 7. Missing Input Validation
Antes:
- aceita `request.get_json()` sem checar campos.

Depois:
- validar campos obrigatórios e tipos antes de chamar o controller.
- usar middleware / helper de validação quando possível.

## 8. Deprecated API Usage
Antes:
- `badCrypto()` custom insecure hashing
- `app.use(bodyParser.json())`

Depois:
- usar `bcrypt`/`crypto` para hashing
- usar `express.json()` no Express
- evitar `DEBUG=True` no código, use env var

## Exemplo de transformação antes/depois
### Python/Flask
Antes:
```python
@app.route('/produtos', methods=['POST'])
def criar_produto():
    dados = request.get_json()
    nome = dados['nome']
    cursor.execute("INSERT INTO produtos (...) VALUES (...)" )
    return jsonify(...)
```
Depois:
```python
@produtos_bp.route('/produtos', methods=['POST'])
def criar_produto():
    return produto_controller.criar_produto(request.get_json())
```

Em `controllers/produto_controller.py`:
```python
def criar_produto(dados):
    validar_dados_produto(dados)
    novo_id = produto_model.criar_produto(dados)
    return jsonify({'id': novo_id, 'sucesso': True}), 201
```

Em `models/produto_model.py`:
```python
def criar_produto(data):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)',
        (data['nome'], data.get('descricao',''), data['preco'], data['estoque'], data.get('categoria','geral'))
    )
    db.commit()
    return cursor.lastrowid
```

### Node.js/Express
Antes:
```js
app.post('/api/checkout', (req, res) => {
    let cc = req.body.card;
    if (!cc) return res.status(400).send('Bad Request');
    db.get('SELECT * FROM courses WHERE id = ' + cid, ...)
});
```
Depois:
```js
router.post('/api/checkout', checkoutController.handleCheckout);
```

Em `controllers/checkoutController.js`:
```js
async function handleCheckout(req, res) {
    const { c_id, card } = req.body;
    validateCheckoutInput(req.body);
    const course = await courseService.findCourse(c_id);
    await paymentService.processPayment({ card, course });
    res.json({ msg: 'Sucesso' });
}
```

## Uso do playbook
- Associe cada finding do catálogo a uma transformação.
- Aplique mudanças incrementais e mantenha a aplicação funcional.
- Priorize correções de segurança e separação de responsabilidades.

## 9. Plaintext Passwords in Seeds/Defaults
Antes:
- `db.run("INSERT INTO users (pass) VALUES ('123')")`
- `u1.password = '1234'` sem hash.

Depois:
- Os seeds **devem** obrigatoriamente usar a mesma função de hash (ex: `bcrypt.hashSync`, `generate_password_hash`) usada pelo sistema.
- Node.js: `const pwd = bcrypt.hashSync('123', 10); db.run("... VALUES (?)", [pwd])`
- Python: `u1.set_password('1234')` garantindo que o método de fato faça o hash no banco.

## 10. Fake / Unsigned JWTs
Antes:
- `token = "jwt-demo-" + str(user.id)`
- Rota que ignora validação de assinatura e confia na string.

Depois:
- Gerar JWTs reais assinados usando a `SECRET_KEY` da aplicação.
- Node.js: usar `jsonwebtoken` (`jwt.sign(payload, SECRET_KEY)`).
- Python: usar `PyJWT` (`jwt.encode(payload, SECRET_KEY, algorithm="HS256")`).
- Ao verificar requisições, garantir que a assinatura do JWT seja validada.
