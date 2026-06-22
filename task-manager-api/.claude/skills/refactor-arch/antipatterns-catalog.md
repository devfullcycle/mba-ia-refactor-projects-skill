# Anti-Patterns Catalog — /refactor-arch

This catalog defines all detectable anti-patterns with their severity, detection signals, and examples. Use this as the knowledge base for Phase 2 of the audit.

---

## Severity Scale

| Severity | Definition |
|---|---|
| **CRITICAL** | Security vulnerabilities or architectural failures that expose data, allow arbitrary code execution, or completely break separation of concerns. Must be fixed before deployment. |
| **HIGH** | Strong MVC/SOLID violations or patterns that severely hinder testability, maintainability, and scalability. |
| **MEDIUM** | Code duplication, performance issues, or missing validations that affect quality but not immediately security. |
| **LOW** | Readability, naming, and style issues that create friction but don't break functionality. |

---

## CRITICAL Anti-Patterns

### AP-01 — SQL Injection
**Severity:** CRITICAL  
**Description:** SQL queries are built by concatenating user-supplied or variable data directly into the query string, allowing an attacker to alter query semantics.

**Detection signals:**
- `"SELECT * FROM ... WHERE id = " + str(id)` (Python string concatenation)
- `` `SELECT * FROM ... WHERE id = ${id}` `` (JavaScript template literal in SQL)
- `cursor.execute("..." + variable + "...")`
- `db.query("SELECT..." + req.body.field + "...")`
- `.format()` or `%` string formatting in SQL statements
- Any SQL string where a variable appears inside the query string without `?` or `$N` placeholder

**Example (vulnerable):**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
```

**Scope:** Check every `cursor.execute()`, `db.query()`, `db.run()`, `connection.query()` call in all files.

---

### AP-02 — Hardcoded Secrets
**Severity:** CRITICAL  
**Description:** Passwords, API keys, secret keys, or tokens are embedded directly in source code instead of loaded from environment variables or a secrets manager.

**Detection signals (Python):**
- `SECRET_KEY = "..."` assigned as a string literal in source
- `PASSWORD = "..."` or `API_KEY = "..."` as string literals
- Credentials in database seed data within source files
- `app.config["SECRET_KEY"] = "..."` with a literal string

**Detection signals (JavaScript/Node.js):**
- `const secret = "..."` or `const apiKey = "..."`
- `jwt.sign(payload, "hardcoded-secret")`

**Example:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```

---

### AP-03 — God Class / God File
**Severity:** CRITICAL  
**Description:** A single file or class is responsible for too many concerns: database access, business logic, validation, serialization, and routing all in one place. This breaks the Single Responsibility Principle and makes testing impossible.

**Detection signals:**
- A single `.py` or `.js` file exceeds 200 lines and contains functions from multiple domains (users, products, orders)
- Functions for DB queries, HTTP response formatting, and business rules coexist in the same file
- A single file contains operations for more than 2 distinct domain entities

---

### AP-04 — Unauthenticated Admin / Privileged Endpoints
**Severity:** CRITICAL  
**Description:** Administrative or destructive endpoints (database reset, raw SQL execution, user management) are exposed without any authentication or authorization check.

**Detection signals (Python/Flask):**
- `@app.route("/admin/...")` without a `@require_auth` decorator or auth check inside
- Endpoints that perform DELETE, DROP, or arbitrary SQL without verifying the caller's identity
- `cursor.execute(query)` where `query` comes from the request body without validation

**Detection signals (Node.js/Express):**
- `app.post("/admin/...")` or `router.delete(...)` without an auth middleware

**Example:**
```python
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():  # no authentication check
    cursor.execute("DELETE FROM itens_pedido")
```

---

### AP-05 — Plain-Text Passwords
**Severity:** CRITICAL  
**Description:** User passwords are stored in the database without hashing. If the database is compromised, all passwords are immediately exposed.

**Detection signals:**
- `INSERT INTO usuarios ... senha = '" + senha + "'"` storing the raw password
- Seed data in source code with plaintext passwords: `("admin@loja.com", "admin123", ...)`
- `SELECT * FROM usuarios WHERE senha = '" + senha + "'"` comparing plain text passwords
- No import of `bcrypt`, `werkzeug.security`, `hashlib`, `argon2`, or equivalent hashing library

---

## HIGH Anti-Patterns

### AP-06 — Sensitive Data Exposure in Responses
**Severity:** HIGH  
**Description:** Internal configuration, secret keys, debug flags, or passwords are included in API responses, leaking sensitive information to any caller.

**Detection signals:**
- Response JSON includes keys like `secret_key`, `password`, `senha`, `debug`, `db_path`
- `jsonify({..., "secret_key": app.config["SECRET_KEY"], ...})`
- Health-check endpoints returning configuration internals

**Example:**
```python
return jsonify({
    "secret_key": "minha-chave-super-secreta-123",
    "debug": True,
    "db_path": "loja.db"
})
```

---

### AP-07 — Global Mutable State (Shared Connection)
**Severity:** HIGH  
**Description:** A single database connection (or other resource) is stored as a global variable and shared across all requests. This is not thread-safe and leads to race conditions under concurrent load.

**Detection signals (Python):**
- `db_connection = None` at module level, then mutated inside a function
- `global db_connection` inside a function
- No per-request connection lifecycle management

**Detection signals (Node.js):**
- `let db = null` at module level, mutated in a lazy-init function shared across routes

---

### AP-08 — Business Logic / Side Effects in Controller
**Severity:** HIGH  
**Description:** The controller layer contains notification logic (email, SMS, push), complex business calculations, or workflow orchestration that belongs in a service layer. This violates MVC separation.

**Detection signals:**
- `print("ENVIANDO EMAIL: ...")` or `sendEmail(...)` inside a controller/route handler
- `print("ENVIANDO SMS: ...")` or SMS/push notification calls in a controller
- Complex multi-step business logic (more than simple data retrieval + validation + response) in a controller function

---

### AP-09 — Missing Authentication Middleware
**Severity:** HIGH  
**Description:** The application has a login endpoint but does not protect any other routes with authentication. Any caller can access protected resources without credentials.

**Detection signals:**
- A `/login` endpoint exists, but no JWT verification, session check, or token validation in other routes
- No import of JWT library (`flask-jwt-extended`, `jsonwebtoken`, `pyjwt`)
- No decorator like `@login_required` or `@token_required` on protected routes

---

## MEDIUM Anti-Patterns

### AP-10 — N+1 Query Problem
**Severity:** MEDIUM  
**Description:** For each record in a result set, an additional query is made to fetch related data. This causes O(n) database round-trips instead of O(1), degrading performance severely as data grows.

**Detection signals:**
- A `for row in rows:` loop that contains `cursor.execute("SELECT ...")` inside it
- Nested cursor objects (`cursor2`, `cursor3`) used inside loops
- `forEach` or `.map()` in Node.js that triggers a database query per iteration

**Example:**
```python
for row in rows:  # N orders
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))  # +1 query per order
    for item in itens:
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))  # +1 more
```

---

### AP-11 — Duplicated Code (DRY Violation)
**Severity:** MEDIUM  
**Description:** Two or more functions share more than 80% identical logic, indicating that a shared abstraction is missing.

**Detection signals:**
- Two functions with near-identical bodies (same queries, same loop structure, same response format)
- Copy-pasted validation blocks in multiple controllers
- Identical SQL query patterns repeated across multiple model functions

---

### AP-12 — Missing or Inconsistent Input Validation
**Severity:** MEDIUM  
**Description:** Some endpoints validate their inputs while others don't, creating an inconsistent security surface. Missing validation can lead to data corruption or unexpected errors.

**Detection signals:**
- One endpoint validates a field (`categoria`) but the sibling endpoint (update) does not
- No validation of numeric types before use (e.g., `preco_min = float(request.args.get(...))` without try/except)
- Required fields checked in create but not in update endpoints

---

## LOW Anti-Patterns

### AP-13 — Print-as-Logging
**Severity:** LOW  
**Description:** `print()` statements are used for operational logging instead of a structured logging framework. This prevents log level filtering, structured output, and integration with log aggregators.

**Detection signals (Python):**
- `print("ERRO: " + str(e))` inside exception handlers
- `print("Produto criado com ID: " + str(id))` for operational events
- No `import logging` anywhere in the codebase

**Detection signals (Node.js):**
- `console.log(...)` used for operational events (not just debugging)

---

### AP-14 — Magic Numbers / Magic Strings
**Severity:** LOW  
**Description:** Literal numeric or string values with business meaning appear directly in code without being assigned to named constants. This makes the code harder to understand and modify.

**Detection signals:**
- Business threshold values like `if faturamento > 10000` or `if faturamento > 5000` without named constants
- Discount rates like `faturamento * 0.1` without a named constant `DISCOUNT_TIER_1 = 0.10`
- Status strings like `"pendente"`, `"aprovado"` scattered without a central enum or constant list

---

### AP-15 — Deprecated or Obsolete API Usage
**Severity:** LOW  
**Description:** The code uses deprecated APIs, old library patterns, or functions scheduled for removal that will cause issues in future versions.

**Detection signals (Python/Flask):**
- `from flask.ext.*` imports (removed in Flask 1.0)
- `@app.before_first_request` decorator (deprecated in Flask 2.2, removed in 2.3)
- `flask.signals_available` usage
- `sqlite3.connect()` called without `check_same_thread=False` in a multi-threaded context

**Detection signals (Node.js/Express):**
- `app.use(express.bodyParser())` (removed in Express 4)
- `require('connect').multipart()` (deprecated)
- Callback-style database drivers where Promise-based alternatives are available
