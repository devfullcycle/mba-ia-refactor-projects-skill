# Playbook de refatoração (≥8 transformações)

Cada item liga-se a anti-patterns do catálogo. Inclui **antes / depois** ilustrativo (adaptar ao projeto).

---

## T1 — SQL concatenado → SQL parametrizado (AP-01)

**Antes (Python):**
```python
cursor.execute("SELECT * FROM users WHERE email = '" + email + "'")
```

**Depois:**
```python
cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
```

---

## T2 — Remover execução SQL arbitrária (AP-02)

**Antes:** rota `/admin/query` executa `cursor.execute(query)` do body.  
**Depois:** **remover** a rota ou proteger com política enterprise (fora do escopo) — em desafios, **delete** + documentar no relatório.

---

## T3 — Segredos inline → variáveis de ambiente (AP-03)

**Antes:**
```python
app.config["SECRET_KEY"] = "hardcoded"
```

**Depois:**
```python
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-unsafe")
```

---

## T4 — God module → pastas Model / Controller / View (AP-04)

**Antes:** `models.py` com SQL + regras + formatação JSON.  
**Depois:**
- `models/order_repository.py` — apenas persistência
- `controllers/order_controller.py` — `criar_pedido(dto)`
- `views/routes.py` — `@bp.post("/pedidos")` chama controller

---

## T5 — Senha MD5/custom → KDF da stack (AP-05)

**Antes (Python):**
```python
hashlib.md5(pwd.encode()).hexdigest()
```

**Depois:**
```python
from werkzeug.security import generate_password_hash, check_password_hash
generate_password_hash(password)
```

**Antes (Node):**
```javascript
function badCrypto(pwd) { /* ... */ }
```

**Depois:**
```javascript
const bcrypt = require('bcryptjs');
await bcrypt.hash(password, 10);
```
*(Se não puder adicionar deps, usar `crypto.scrypt` nativo com documentação de custo.)*

---

## T6 — Health vazando segredo → health seguro (AP-06)

**Antes:** `return jsonify({..., "secret_key": app.config["SECRET_KEY"]})`  
**Depois:** retornar apenas `status`, `version`, contagens não sensíveis.

---

## T7 — N+1 → JOIN ou batch load (AP-08)

**Antes (Python/ORM):**
```python
for t in Task.query.all():
    user = User.query.get(t.user_id)
```

**Depois:**
```python
from sqlalchemy.orm import joinedload
Task.query.options(joinedload(Task.user)).all()
```

**Antes (Node):** loops com `db.get` interno.  
**Depois:** uma query com `IN (...)` ou view SQL agregada.

---

## T8 — Callback pyramid → async/await (AP-09)

**Antes:**
```javascript
this.db.get("...", [], (err, row) => {
  this.db.run("...", [], (err2) => { /* ... */ });
});
```

**Depois:**
```javascript
const row = await dbGet(db, sql, params);
await dbRun(db, sql2, params2);
```
*(Wrappers `dbGet`/`dbRun` com Promise.)*

---

## T9 — Global cache mutável → escopo de serviço (AP-07)

**Antes:** `module.exports = { globalCache: {} }` mutado por requests.  
**Depois:** classe `CacheService` injetada ou `Map` local ao app; em demo, `const cache = new Map()` dentro da factory do app.

---

## T10 — `except:` → exceções específicas + handler (AP-11)

**Antes:**
```python
except:
    return jsonify({'error': 'Erro interno'}), 500
```

**Depois:**
```python
except ValueError as e:
    return jsonify({'error': str(e)}), 400
# não tratado → errorhandler 500
```

---

*(T1–T10 listados; use um subconjunto mínimo de 8 no relatório de skill — este arquivo contém 10 para margem.)*
