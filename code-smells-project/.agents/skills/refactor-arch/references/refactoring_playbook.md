# Playbook de Refatoração Arquitetural

Este playbook fornece padrões concretos de transformação com exemplos **Antes e Depois** para os anti-patterns catalogados. Estes padrões devem ser aplicados na **Fase 3 (Refatoração)** para transformar código legado no padrão MVC.

---

## Padrão 1: Eliminação de SQL Injection com Queries Parametrizadas

### Antes (Vulnerável):
```python
# Concatenação de string permite injeção arbitrária de comandos SQL
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("INSERT INTO usuarios (nome, email) VALUES ('" + nome + "', '" + email + "')")
```

### Depois (Seguro):
```python
# Prepared statement com tupla de parâmetros do SQLite
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute("INSERT INTO usuarios (nome, email) VALUES (?, ?)", (nome, email))
```

---

## Padrão 2: Extração de Secrets Hardcoded para Módulo de Configuração

### Antes (Inseguro):
```javascript
// Credenciais críticas expostas no código-fonte
const config = {
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
    port: 3000
};
```

### Depois (Seguro):
```javascript
// config/settings.js - leitura segura via variáveis de ambiente com defaults de dev
const config = {
    dbPass: process.env.DB_PASSWORD || "dev_password",
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || "pk_test_default",
    port: parseInt(process.env.PORT, 10) || 3000
};
module.exports = config;
```

---

## Padrão 3: Decomposição de God Class/File em Módulos MVC Coesos

### Antes (Monolítico):
```
// AppManager.js concentrando inicialização de banco, schemas,
// rotas HTTP, callbacks de pagamento, queries SQL e logs em 1 arquivo
class AppManager {
    initDb() { ... }
    setupRoutes(app) {
        app.post('/api/checkout', (req, res) => { ... });
        app.get('/api/admin/financial-report', (req, res) => { ... });
    }
}
```

### Depois (MVC Desacoplado):
```
src/
├── config/config.js           # Configurações de ambiente
├── models/
│   ├── database.js            # Conexão do banco de dados
│   ├── userModel.js           # Métodos de consulta e criação de usuários
│   ├── courseModel.js         # Métodos de consulta de cursos
│   └── paymentModel.js        # Transações de matrículas e pagamentos
├── controllers/
│   ├── checkoutController.js  # Lógica de orquestração do checkout
│   └── reportController.js    # Agregação do relatório financeiro
├── routes/
│   ├── checkoutRoutes.js      # Rotas Express dedicadas a checkout
│   └── reportRoutes.js        # Rotas Express dedicadas a relatórios
└── app.js                     # Composition Root limpo
```

---

## Padrão 4: Remoção de Consultas SQL de Controllers e Otimização de Health Check

### Antes (Controller Acoplado com Consulta Pesada):
```python
# controllers.py executando queries diretamente e fazendo contagens em rota de infraestrutura
def health_check():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM produtos")
    produtos = cursor.fetchone()[0]
    return jsonify({"produtos": produtos, "status": "ok"})
```

### Depois (Camada Isolada com Checagem Atômica):
```python
# models/database.py
def check_connection():
    """Valida conectividade ativa sem sobrecarregar o banco com contagens."""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        return cursor.fetchone() is not None
    except Exception:
        return False

# controllers/health_controller.py
from models.database import check_connection

def health_check():
    db_ok = check_connection()
    status_code = 200 if db_ok else 503
    return jsonify({
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable"
    }), status_code
```

---

## Padrão 5: Hashing Seguro e Ocultação de Senhas na Serialização

### Antes (Inseguro):
```python
# models/user.py
class User(db.Model):
    def set_password(self, pwd):
        self.password = hashlib.md5(pwd.encode()).hexdigest()  # MD5 fraco sem salt

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'password': self.password  # Expondo senha no payload público!
        }
```

### Depois (Seguro):
```python
# models/user.py
import hashlib
import os

class User(db.Model):
    def set_password(self, pwd):
        # Utilizando SHA-256 com salt ou algoritmo de derivação segura
        salt = os.urandom(16).hex()
        hash_val = hashlib.sha256((pwd + salt).encode()).hexdigest()
        self.password = f"{salt}${hash_val}"

    def check_password(self, pwd):
        if not self.password or '$' not in self.password:
            return False
        salt, expected_hash = self.password.split('$', 1)
        actual_hash = hashlib.sha256((pwd + salt).encode()).hexdigest()
        return actual_hash == expected_hash

    def to_dict(self):
        # Senha estritamente excluída da serialização pública
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at)
        }
```

---

## Padrão 6: Resolução do Problema N+1 com JOINs SQL Consolidados

### Antes (N+1 Queries em Loop):
```python
# models.py - 1 query de pedidos + N queries de itens + N*M queries de produtos
pedidos = cursor.execute("SELECT * FROM pedidos").fetchall()
for p in pedidos:
    itens = cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(p["id"])).fetchall()
    for item in itens:
        prod = cursor.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"])).fetchone()
```

### Depois (Consulta Consolidada via JOIN):
```python
# models/pedido_model.py - 1 query única trazendo todos os dados relacionados
query = """
    SELECT 
        p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
        ip.id AS item_id, ip.produto_id, ip.quantidade, ip.preco_unitario,
        prod.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON p.id = ip.pedido_id
    LEFT JOIN produtos prod ON ip.produto_id = prod.id
    ORDER BY p.id
"""
cursor.execute(query)
rows = cursor.fetchall()
# Agrupamento eficiente em memória sem chamadas adicionais de rede/banco
```

---

## Padrão 7: Refatoração de Condicionais Aninhadas com Guard Clauses

### Antes (Alta Complexidade Ciclomática):
```python
def is_overdue(self):
    if self.due_date:
        if self.due_date < datetime.utcnow():
            if self.status != 'done' and self.status != 'cancelled':
                return True
            else:
                return False
        else:
            return False
    else:
        return False
```

### Depois (Guard Clauses Lineares e Limpas):
```python
def is_overdue(self):
    if not self.due_date:
        return False
    now = datetime.now(timezone.utc) if self.due_date.tzinfo else datetime.utcnow()
    return self.due_date < now and self.status not in ('done', 'cancelled')
```

---

## Padrão 8: Centralização de Error Handling e Eliminação de Falhas Silenciosas

### Antes (Exceções Engolidas sem Diagnóstico):
```python
try:
    tasks = Task.query.all()
    # ...
    return jsonify(result), 200
except:
    return jsonify({'error': 'Erro interno'}), 500  # Oculta o erro e o log
```

### Depois (Tratamento Estruturado e Centralizado):
```python
# middlewares/error_handler.py
import logging

def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logging.exception("Exceção não tratada capturada pelo middleware global: %s", error)
        return jsonify({
            "error": "Ocorreu um erro interno no processamento",
            "tipo": error.__class__.__name__
        }), 500
```

---

## Padrão 9: Atualização de APIs Deprecated

### Antes (Python datetime.utcnow() obsoleto):
```python
from datetime import datetime
created_at = datetime.utcnow()  # Deprecated no Python 3.12+ (gera DeprecationWarning)
```

### Depois (API Moderna com Timezone Aware):
```python
from datetime import datetime, timezone
created_at = datetime.now(timezone.utc)
```

---

## Padrão 10: Roteamento Consistente e Declaração Explícita de Verbos HTTP

### Antes:
```python
@app.route("/")
def index():
    return {"status": "ok"}
```

### Depois:
```python
@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok"}), 200
```

---

## Padrão 11: Validação e Desvinculação Prévia de Registros Dependentes em Entidades Opcionais

### Antes (Deleção em Cascata Destrutiva ou Violação de Integridade):
```python
# models/category.py
# cascade='all, delete-orphan' apaga todas as tarefas do usuário quando a categoria é excluída!
tasks = db.relationship('Task', backref='category', cascade='all, delete-orphan')

# controllers/category_controller.py
def delete_category(cat_id):
    cat = Category.query.get(cat_id)
    db.session.delete(cat)  # Exclusão destrói todas as tarefas vinculadas
    db.session.commit()
```

### Depois (Validação e Desvinculação com SET NULL):
```python
# models/category.py
# Sem cascade destrutivo em entidades de classificação opcional
tasks = db.relationship('Task', backref='category', lazy=True)

# models/task.py
category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)

# controllers/category_controller.py
def delete_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        return {'error': 'Categoria não encontrada'}, 404

    # Validação e desvinculação prévia das entidades dependentes
    dependent_tasks = Task.query.filter_by(category_id=cat_id).all()
    if dependent_tasks:
        for task in dependent_tasks:
            task.category_id = None

    db.session.delete(cat)
    db.session.commit()
    return {'message': 'Categoria deletada'}, 200
```
