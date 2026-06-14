================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 6 | HIGH: 4 | MEDIUM: 5 | LOW: 1

## Findings

### [CRITICAL] SQL Injection — Multiple Locations
File: models.py:28, 47-50, 57-62, 67, 92, 109-111, 127-129,
      140, 148-150, 155, 157-160, 163-165, 174, 188, 192,
      220, 224, 279-281, 290-296
Description: User-controlled values concatenated directly into SQL strings
  throughout the file. Worst cases:
  - Login (line 109-111): `"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`
  - Search (line 290-296): dynamic query built by concatenating termo, categoria, preco_min, preco_max
  - Every SELECT/INSERT/UPDATE/DELETE in the file uses str() concatenation instead of parameterized queries.
Impact: Complete database compromise — attacker can bypass login, exfiltrate
  all data, drop tables, or execute arbitrary SQL via any endpoint.
Recommendation: Replace every concatenated query with parameterized form:
  `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`
  Use the same pattern for all INSERT/UPDATE/DELETE operations.

### [CRITICAL] Hardcoded Secret Key + Secret Exposed in Response
File: app.py:7 | controllers.py:289
Description:
  - app.py:7: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` hardcoded in source.
  - controllers.py:289: The same secret key is returned verbatim in the
    `/health` endpoint response body: `"secret_key": "minha-chave-super-secreta-123"`.
Impact: Any caller of `/health` receives the session signing key. Attackers
  can forge session tokens and bypass CSRF protection.
Recommendation: Load from environment: `os.environ.get("SECRET_KEY")`. Remove
  secret_key, debug, and db_path from the health response entirely.

### [CRITICAL] Plain Text Password Storage and Comparison
File: models.py:109-111, 127-129 | database.py:76-82
Description:
  - models.py:127-129: `criar_usuario` inserts raw `senha` with no hashing.
  - models.py:109-111: `login_usuario` compares raw input directly to the stored value.
  - database.py:76-82: Seed data stores "admin123", "123456", "senha123" as plain text.
Impact: A single database read (or breach) exposes every user's password in
  cleartext. Admin credentials are trivially guessable from the seed data.
Recommendation: Use `werkzeug.security.generate_password_hash(senha)` on
  registration and `check_password_hash(stored, senha)` on login.
  Re-seed with hashed values.

### [CRITICAL] Unauthenticated Dangerous Admin Endpoints
File: app.py:47-57, 59-78
Description:
  - `/admin/reset-db` (lines 47-57): Deletes ALL rows from all tables with
    no authentication check whatsoever.
  - `/admin/query` (lines 59-78): Executes arbitrary SQL from the request body
    (`cursor.execute(query)`) with no authentication. Any HTTP client can
    send a DROP TABLE or SELECT * FROM usuarios.
Impact: Complete data loss and remote code execution without credentials.
Recommendation: Remove `/admin/query` entirely — there is no safe version of
  an unauthenticated arbitrary SQL endpoint. Protect `/admin/reset-db` with
  an admin-only JWT/session check and restrict to non-production environments.

### [CRITICAL] God Module — models.py Mixes All Domain Logic
File: models.py:1-314
Description: Single file handles DB access for ALL four domains (produtos,
  usuarios, pedidos, itens_pedido) AND contains business logic
  (discount calculation in relatorio_vendas, lines 256-263, stock management
  embedded in criar_pedido lines 133-168). 314 lines, 14 public functions.
Impact: Any change to one domain risks breaking another. Business rules
  (discount tiers) are invisible in a data-access file. Impossible to unit
  test business logic without a real database.
Recommendation: Split into domain-specific model files:
  models/product_model.py, models/user_model.py, models/order_model.py.
  Extract business rules (discount logic) into a service layer:
  services/order_service.py.

### [CRITICAL] Debug Mode Hardcoded to True
File: app.py:8, 88
Description:
  - Line 8:  `app.config["DEBUG"] = True`
  - Line 88: `app.run(host="0.0.0.0", port=5000, debug=True)`
  Both are hardcoded; there is no environment variable override.
Impact: Flask's interactive debugger is publicly accessible on 0.0.0.0,
  enabling remote code execution via the Werkzeug debugger PIN bypass.
  Full stack traces are returned to any HTTP caller.
Recommendation: `app.config["DEBUG"] = os.getenv("DEBUG", "False").lower() == "true"`
  and `app.run(debug=app.config["DEBUG"])`.

---

### [HIGH] Passwords and Secret Key Exposed in API Responses
File: models.py:82-83, 97-98 | controllers.py:285-292
Description:
  - models.py:82-83 and 97-98: `get_todos_usuarios()` and `get_usuario_por_id()`
    both include `"senha": row["senha"]` in their return dicts, which are
    serialized directly to JSON responses on GET /usuarios and GET /usuarios/<id>.
  - controllers.py:285-292: `/health` returns `"secret_key"`, `"debug": True`,
    and `"db_path"` in the response body.
Impact: Any authenticated (or unauthenticated) caller receives user password
  hashes (or plain text, per AP-C3) and the application secret key.
Recommendation: Remove `senha` from all to_dict serializations. Return only
  `{"status": "ok"}` from health.

### [HIGH] No Authentication on Any Endpoint
File: app.py:1-88 | controllers.py:1-292
Description: Zero authentication middleware or decorators exist. Every
  endpoint — including GET /usuarios (returns all users + passwords),
  POST /pedidos (creates orders as any user), and PUT /pedidos/<id>/status
  (escalates order status) — is publicly accessible with no token or session.
Impact: Any unauthenticated client can read all user data, create orders on
  behalf of any user, and manipulate order statuses.
Recommendation: Add a JWT or session-based auth middleware. At minimum, protect
  /usuarios (GET), /pedidos (GET), and all /admin/* routes.

### [HIGH] Race Condition — Order Creation Without Transaction
File: models.py:133-168
Description: `criar_pedido` performs a multi-step operation: (1) check stock
  for all items, (2) INSERT into pedidos, (3) INSERT into itens_pedido for
  each item, (4) UPDATE produtos estoque for each item — all without wrapping
  in a transaction. A failure at step 3 or 4 leaves a pedido record with
  no items and no stock restored.
Impact: Data integrity violation — orphaned orders, stock permanently reduced
  without a corresponding order item, financial inconsistency.
Recommendation: Wrap the entire operation in `db.execute("BEGIN"); ... db.commit()`
  with a rollback on any error.

### [HIGH] Global Mutable Database Connection
File: database.py:4, 7-8
Description: `db_connection = None` is a module-level global mutated by `get_db()`.
  SQLite connection is shared across all requests with `check_same_thread=False`.
Impact: In any multi-threaded deployment (gunicorn, etc.) concurrent writes
  can corrupt the connection state. The singleton pattern also makes testing
  impossible without monkey-patching the global.
Recommendation: Use Flask's `g` object for per-request connections, or use a
  connection pool. Pass the connection as a dependency to model classes.

---

### [MEDIUM] N+1 Query Problem — Order Listing
File: models.py:171-201, 203-233
Description: Both `get_pedidos_usuario()` and `get_todos_pedidos()` execute
  a query per order to fetch items, and then another query per item to fetch
  the product name — nested cursor2/cursor3 loops. For 10 orders with 5 items
  each: 1 + 10 + 50 = 61 queries.
Impact: Response time grows O(orders × items). With real data volumes this
  causes timeouts and excessive DB load.
Recommendation: Replace with a single JOIN query:
  `SELECT p.*, ip.*, prod.nome FROM pedidos p
   JOIN itens_pedido ip ON ip.pedido_id = p.id
   JOIN produtos prod ON prod.id = ip.produto_id
   WHERE p.usuario_id = ?`

### [MEDIUM] Code Duplication — Order Hydration Logic
File: models.py:171-201 vs. models.py:203-233
Description: `get_pedidos_usuario()` and `get_todos_pedidos()` contain
  near-identical loops (30 lines each) for building the order dict with
  nested item/product name lookups.
Impact: A bug fix (e.g., fixing the N+1 query above) must be applied in
  two places; missing one creates inconsistent behavior.
Recommendation: Extract shared logic into a private helper:
  `def _hydrate_orders(rows): ...` and call it from both functions.

### [MEDIUM] Missing Input Validation — User Registration
File: controllers.py:146-165
Description: `criar_usuario()` accepts `email` and `senha` without validating:
  email format (no `@` check), minimum password length, or password strength.
  Any string (including empty after strip) passes the `if not nome or not email
  or not senha` guard.
Impact: Invalid emails stored in DB; trivially weak passwords accepted ("a").
Recommendation: Validate email with regex or a library. Enforce `len(senha) >= 8`.

### [MEDIUM] Missing Pagination on All List Endpoints
File: models.py:4-22, 72-87, 203-233
Description: `get_todos_produtos()`, `get_todos_usuarios()`, and
  `get_todos_pedidos()` all execute `SELECT * FROM <table>` with no LIMIT.
Impact: With 100k products/orders the response will exhaust memory and time out.
Recommendation: Add `page`/`per_page` query params and `LIMIT ? OFFSET ?`
  to all list queries.

### [MEDIUM] Bare Exception Handling Throughout Controllers
File: controllers.py:10-12, 60-62, 95-96, 125-126, 163-165, 219-220, etc.
Description: Every function in controllers.py catches `except Exception as e`
  and returns a generic `{"erro": str(e)}` 500. This masks programming errors,
  swallows expected exceptions (e.g., IntegrityError for duplicate email), and
  leaks internal error messages to clients.
Impact: Duplicate email registration returns a raw SQLite traceback to the
  caller instead of a clean 409. Real bugs are invisible in logs.
Recommendation: Catch specific exceptions (ValueError, sqlite3.IntegrityError).
  Log unexpected errors server-side; return a generic 500 message to clients.

---

### [LOW] Magic Numbers — Discount Thresholds
File: models.py:257-263
Description: Discount calculation uses inline literals `10000`, `5000`, `1000`,
  `0.1`, `0.05`, `0.02` with no named constants:
  `if faturamento > 10000: desconto = faturamento * 0.1`
Impact: Business rules are invisible. Changing a threshold requires finding all
  occurrences manually; a second use of 10000 elsewhere won't be updated.
Recommendation: Define module-level constants:
  `DISCOUNT_TIER_HIGH = 10000; DISCOUNT_RATE_HIGH = 0.10`

================================
Total: 16 findings
CRITICAL: 6 | HIGH: 4 | MEDIUM: 5 | LOW: 1
================================
