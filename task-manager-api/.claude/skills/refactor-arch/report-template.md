# Audit Report Template

Use this exact template to generate the Phase 2 audit report. Fill in all sections based on your findings.

---

## Template

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <project-directory-name>
Stack:   <Language> + <Framework>
Files:   <N> analyzed | ~<total-lines> lines of code

## Summary
CRITICAL: <N> | HIGH: <N> | MEDIUM: <N> | LOW: <N>

## Findings

### [CRITICAL] <Title>
File: <path/to/file.py>:<start-line>-<end-line>
Description: <What is wrong — be specific. Quote the problematic code if < 3 lines.>
Impact: <Why this is dangerous or problematic.>
Recommendation: <How to fix it — specific action, not vague advice.>

### [CRITICAL] <Title>
File: <path/to/file.py>:<line>
Description: ...
Impact: ...
Recommendation: ...

### [HIGH] <Title>
File: <path/to/file.py>:<start-line>-<end-line>
Description: ...
Impact: ...
Recommendation: ...

[... repeat for all findings, ordered CRITICAL → HIGH → MEDIUM → LOW ...]

================================
Total: <N> findings
CRITICAL: <N> | HIGH: <N> | MEDIUM: <N> | LOW: <N>
================================
```

---

## Rules for Writing Findings

### Ordering
Always output findings in this order:
1. CRITICAL findings first (most dangerous)
2. HIGH findings
3. MEDIUM findings
4. LOW findings

Within each severity group, order by impact (most impactful first).

### File and Line References
- Always include the exact file path relative to the project root
- Always include line numbers: single line → `file.py:42`, range → `file.py:10-45`
- If the problem spans the entire file → `file.py:1-<total-lines>`

**Good:** `File: models.py:110` (points to exact line)  
**Bad:** `File: models.py` (no line number — invalid finding)

### Descriptions
- Quote the problematic code if it's 1-3 lines and makes the issue clearer
- Be concrete: "SQL query concatenates user input on line 28" not "has SQL issues"
- Reference the anti-pattern code from the catalog when relevant

### Deprecated API Section
If the project uses deprecated APIs, add a section:

```
## Deprecated APIs Found

### [MEDIUM] Deprecated Callback Pattern
File: src/AppManager.js:28-77
Description: Uses nested callback functions instead of async/await (deprecated Node.js pattern).
Impact: Unreadable code, error handling impossible, potential unhandled promise rejections.
Recommendation: Refactor to async/await using util.promisify() or native Promise wrappers.
```

### Security Findings
Security findings (SQL Injection, hardcoded credentials, weak crypto) should ALWAYS be CRITICAL or HIGH — never downgrade them to MEDIUM or LOW.

---

## Example Filled Report

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~450 lines of code

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] SQL Injection
File: models.py:28
Description: User-supplied ID directly concatenated into SQL: `"SELECT * FROM produtos WHERE id = " + str(id)`
Impact: Attacker can exfiltrate entire database, modify or delete records.
Recommendation: Replace with parameterized query: `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`

### [CRITICAL] Hardcoded Secret Key
File: app.py:7
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` hardcoded in source.
Impact: Session tokens can be forged; CSRF protection bypassed.
Recommendation: Load from environment: `app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")`

### [CRITICAL] Plain Text Password Storage
File: models.py:127-128
Description: Passwords stored as plain text in database without hashing.
Impact: All user credentials exposed if database is accessed.
Recommendation: Use `werkzeug.security.generate_password_hash()` before storing.

### [CRITICAL] Arbitrary SQL Execution Endpoint
File: app.py:59-78
Description: `/admin/query` endpoint executes any SQL from request body with no authentication.
Impact: Complete database compromise; no authentication required.
Recommendation: Remove this endpoint entirely. If needed, add admin authentication and whitelist allowed operations.

### [HIGH] God Class — Mixed Concerns
File: models.py:1-350
Description: Single file contains all business logic, SQL queries, validation, and formatting for 4+ domains.
Impact: Impossible to test in isolation; any change can break unrelated domains.
Recommendation: Split into domain-specific model files (product_model.py, user_model.py, order_model.py).

### [HIGH] Business Logic in Routes
File: controllers.py:208-250
Description: Order status change logic, discount calculations, and notification triggers embedded directly in route handlers.
Impact: Cannot reuse business rules; unit testing requires a running HTTP server.
Recommendation: Extract to a service layer (order_service.py, product_service.py).

### [HIGH] Health Endpoint Exposes Secrets
File: controllers.py:264-290
Description: `/api/health` returns `SECRET_KEY`, `debug` flag, and `db_path` in response body.
Impact: Internal configuration disclosed to any caller.
Recommendation: Return only `{"status": "ok", "timestamp": "..."}`.

### [MEDIUM] N+1 Query Problem
File: models.py:187-200
Description: `get_pedidos_usuario()` executes a new DB query for each order item inside a loop.
Impact: 1 order with 10 items = 11 queries. Performance degrades linearly.
Recommendation: Use a JOIN query to fetch all items at once.

### [MEDIUM] Code Duplication — Order Listing
File: models.py:177-200 and models.py:209-232
Description: Nearly identical logic duplicated across `get_pedidos_usuario()` and `get_todos_pedidos()`.
Impact: Bug fixes must be applied in multiple places; easy to miss one.
Recommendation: Extract shared logic into a `_build_order_dict(row)` helper function.

### [MEDIUM] Missing Input Validation
File: controllers.py:39-50
Description: `/api/produtos` accepts `preco` and `estoque` fields without type validation (only range check).
Impact: Non-numeric values cause unhandled exceptions.
Recommendation: Validate types using `isinstance()` or a schema library before processing.

### [LOW] Magic Numbers
File: models.py:256-262
Description: Discount thresholds `10000`, `5000`, `1000` and rates `0.1`, `0.05`, `0.02` hardcoded inline.
Impact: Business rules not expressed as named constants; confusing to readers.
Recommendation: Define as module-level constants: `PREMIUM_THRESHOLD = 10000`.

### [LOW] Poor Variable Naming
File: controllers.py:113-116
Description: Variable names `preco_min`/`preco_max` use inconsistent naming convention vs rest of codebase.
Impact: Reduced readability.
Recommendation: Standardize naming convention throughout.

================================
Total: 12 findings
CRITICAL: 4 | HIGH: 3 | MEDIUM: 3 | LOW: 2
================================
```
