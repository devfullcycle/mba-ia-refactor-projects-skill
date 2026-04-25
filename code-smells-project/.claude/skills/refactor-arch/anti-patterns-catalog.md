# Anti-Patterns Catalog

Cada anti-pattern contem: nome, severidade, sinais de deteccao e exemplos.

---

## CRITICAL

### 1. SQL Injection

**Sinais de deteccao:**
- String concatenation ou f-strings em queries SQL
- `+ str(id)`, `+ nome`, `f"...{var}..."` dentro de `cursor.execute()` ou `db.run()`
- Query building dinamico com input do usuario sem parametros

**Python:**
```python
cursor.execute("SELECT * FROM users WHERE id = " + str(id))
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
cursor.execute("INSERT INTO t (nome) VALUES ('" + nome + "')")
```

**Node.js:**
```javascript
db.run(`DELETE FROM users WHERE id = ${id}`)
db.all(`SELECT * FROM courses WHERE title LIKE '%${term}%'`)
```

### 2. Hardcoded Credentials / Secrets

**Sinais de deteccao:**
- `SECRET_KEY = "..."` hardcoded em source
- Senhas de banco, chaves de API, credenciais SMTP no codigo
- Chaves de payment gateway em config objects
- `"password"`, `"senha"`, `"secret"`, `"key"`, `"token"` atribuidos a string literals

```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
email_password = 'senha123'
SMTP_USER = 'admin@gmail.com'
```
```javascript
dbPass: "senha_super_secreta_prod_123"
paymentGatewayKey: "pk_live_1234567890abcdef"
```

### 3. God Class / God File

**Sinais de deteccao:**
- Arquivo com 200+ linhas lidando com multiplos dominios
- Um arquivo contendo DB access, business logic e routing para 3+ entidades
- Funcoes para modelos diferentes (users, products, orders) no mesmo arquivo
- Classe que faz init DB + define routes + business logic + data access

### 4. Unauthenticated Admin Endpoints / SQL Execution

**Sinais de deteccao:**
- Rotas `/admin/*` sem middleware de autenticacao
- Endpoints aceitando SQL cru do request body (`req.body.sql`, `dados.get("sql")`)
- Endpoints de reset/delete de banco sem auth
- Qualquer endpoint que execute operacoes privilegiadas sem verificar identidade

### 5. Weak Cryptography

**Sinais de deteccao:**
- `hashlib.md5()` para hashing de senhas
- `hashlib.sha1()` para senhas
- Funcoes crypto customizadas (loops de base64, XOR caseiro)
- Senhas armazenadas em plaintext
- Ausencia de salt no hash

```python
hashlib.md5(pwd.encode()).hexdigest()
```
```javascript
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```

---

## HIGH

### 6. Business Logic in Routes / Controllers

**Sinais de deteccao:**
- Route handlers contendo queries SQL diretamente
- Calculos de preco, desconto, transicoes de status dentro de funcoes de rota
- Logica de notificacao (email, SMS) embutida em route handlers
- Validacao complexa dentro de controllers ao inves de service/validation layer
- Print statements simulando envio de email/SMS/push

### 7. Password/Secret Exposure in API Responses

**Sinais de deteccao:**
- Metodos `to_dict()` incluindo campos de senha
- Responses retornando `senha`, `password`, `pass`, `hash`
- Health check expondo SECRET_KEY ou config values
- Listagem de usuarios retornando password hashes
- Log de numeros de cartao de credito em console.log

### 8. Tight Coupling / Global Mutable State

**Sinais de deteccao:**
- `from database import get_db` usado diretamente em route handlers
- Estado global mutavel (`global db_connection`, `globalCache`, `totalRevenue`)
- `let self = this` pattern para contornar escopo de callbacks
- Servicos instanciados com config hardcoded ao inves de injetado
- Modulo de database com conexao global compartilhada

### 9. Callback Hell (Node.js)

**Sinais de deteccao:**
- 4+ niveis de callbacks aninhadas
- `db.get()` dentro de `db.get()` dentro de `db.run()`
- Contadores manuais de pending callbacks (`coursesPending--`)
- Error handling inconsistente entre niveis de callback

---

## MEDIUM

### 10. N+1 Query Problem

**Sinais de deteccao:**
- Queries dentro de loops (for/forEach) consultando a mesma tabela por iteracao
- `cursor.execute()` ou `Model.query.get()` dentro de um `for` loop
- Carregamento de associacoes uma-a-uma ao inves de eager loading
- Queries separadas para dados relacionados que poderiam ser JOINed

```python
for row in rows:
    cursor.execute("SELECT * FROM itens WHERE pedido_id = " + str(row["id"]))
```
```javascript
courses.forEach(c => {
    this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {
        enrollments.forEach(enr => {
            this.db.get("SELECT * FROM users WHERE id = ?", [enr.user_id], ...);
        });
    });
});
```

### 11. Duplicated Code

**Sinais de deteccao:**
- Funcoes quase identicas para modelos diferentes (mesma estrutura, tabela diferente)
- Blocos `try/except` repetidos com padrao identico
- Logica de serializacao repetida em multiplos lugares
- Logica de overdue/check copiada em 3+ arquivos de routes
- Validacao duplicada entre criar e atualizar

### 12. Bare Except / Missing Error Handling

**Sinais de deteccao:**
- `except:` sem tipo de excecao especifico (bare except)
- `except Exception as e:` que retorna erro generico sem log util
- Promises nao tratadas em Node.js
- Routes sem try/except
- Erros retornados como strings ao inves de JSON estruturado

### 13. Deprecated API Usage

**Sinais de deteccao:**

**Python:**
- `datetime.utcnow()` — deprecated Python 3.12+. Usar `datetime.now(timezone.utc)`
- `datetime.utcnow` sem `()` — referencia ao metodo ao inves de chamada
- `Model.query.get(id)` — deprecated SQLAlchemy 2.x. Usar `db.session.get(Model, id)`

**Node.js:**
- `sqlite3.verbose()` em producao
- Callback patterns ao inves de async/await
- `new sqlite3.Database(':memory:')` em codigo de producao

---

## LOW

### 14. Poor Variable Naming

**Sinais de deteccao:**
- Variaveis de uma letra (`u`, `e`, `p`) para dados importantes
- Abreviacoes obscuras (`usr`, `eml`, `pwd`, `cid`, `cc`, `enr`)
- Nomes genericos (`data`, `result`, `item`) onde nomes especificos seriam mais claros

### 15. Magic Numbers / Magic Strings

**Sinais de deteccao:**
- Numeros hardcoded sem explicacao (thresholds de desconto: `> 10000`, `> 5000`)
- Strings de status repetidas (`'pendente'`, `'aprovado'`, `'done'`)
- Portas hardcoded (`5000`, `3000`)
- Tamanho minimo de senha como numero solto (`< 4`)

### 16. Debug Mode / Verbose Logging in Production

**Sinais de deteccao:**
- `debug=True` em `app.run()` ou `app.config`
- `print()` como logging ao inves de framework estruturado
- `console.log()` em producao Node.js
- `sqlite3.verbose()` em producao

### 17. Unused Imports

**Sinais de deteccao:**
- Modulos importados mas nao referenciados no codigo
- `import os, sys, json, time` quando apenas um ou nenhum e usado
- Imports de modules que poderiam ser lazy-loaded

---

## Resumo

| # | Anti-Pattern | Severidade |
|---|-------------|------------|
| 1 | SQL Injection | CRITICAL |
| 2 | Hardcoded Credentials | CRITICAL |
| 3 | God Class / God File | CRITICAL |
| 4 | Unauthenticated Admin Endpoints | CRITICAL |
| 5 | Weak Cryptography | CRITICAL |
| 6 | Business Logic in Routes | HIGH |
| 7 | Password/Secret Exposure | HIGH |
| 8 | Tight Coupling / Global State | HIGH |
| 9 | Callback Hell | HIGH |
| 10 | N+1 Query Problem | MEDIUM |
| 11 | Duplicated Code | MEDIUM |
| 12 | Bare Except / Missing Error Handling | MEDIUM |
| 13 | Deprecated API Usage | MEDIUM |
| 14 | Poor Variable Naming | LOW |
| 15 | Magic Numbers / Strings | LOW |
| 16 | Debug Mode in Production | LOW |
| 17 | Unused Imports | LOW |
