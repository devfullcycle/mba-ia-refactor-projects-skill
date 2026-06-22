# Audit Report Template — /refactor-arch

Use this exact format when producing the Phase 2 audit report. Fill in all fields — never omit a field or approximate line numbers.

---

## Report Format

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <project directory name>
Stack:   <Language> + <Framework>
Files:   <N> analyzed | ~<total lines> lines of code

## Summary
CRITICAL: <N> | HIGH: <N> | MEDIUM: <N> | LOW: <N>
Total findings: <N>

---

## Findings

<repeat the finding block below for each issue, ordered CRITICAL → HIGH → MEDIUM → LOW>

### [<SEVERITY>] <Anti-pattern Name>
ID:          <AP-XX>
File:        <exact/relative/path/to/file.py>
Lines:       <exact line number or range, e.g. "45" or "45-52">
Description: <concrete description of the specific instance found — not generic>
Impact:      <what can go wrong if this is not fixed>
Fix:         <which playbook pattern to apply — PT-XX>
Recommendation: <one-sentence specific recommendation>

---

<next finding>
```

---

## Example Report

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 5 | HIGH: 3 | MEDIUM: 2 | LOW: 3
Total findings: 13

---

## Findings

### [CRITICAL] SQL Injection
ID:          AP-01
File:        models.py
Lines:       17, 30, 37, 45, 70, 83, 106, 116, 145, 170, 205, 230
Description: All SQL queries in models.py use string concatenation to inject variables
             directly into query strings. For example: cursor.execute("SELECT * FROM
             produtos WHERE id = " + str(id)). An attacker can manipulate `id` to
             execute arbitrary SQL.
Impact:      Full database compromise — attacker can read, modify, or delete all data.
             Authentication can be bypassed via: email = "' OR '1'='1".
Fix:         PT-01
Recommendation: Replace all string-concatenated queries with parameterized queries
             using `?` placeholders and tuple parameters.

---

### [CRITICAL] Hardcoded Secret Key
ID:          AP-02
File:        app.py
Lines:       8
Description: app.config["SECRET_KEY"] = "minha-chave-super-secreta-123" — the Flask
             secret key is hardcoded as a string literal in the source file. This
             secret will be committed to version control and visible to anyone with
             repository access.
Impact:      Attacker can forge session tokens and impersonate any user including admin.
Fix:         PT-02
Recommendation: Move SECRET_KEY to an environment variable loaded via python-dotenv.

---

### [CRITICAL] Unauthenticated Admin Endpoints
ID:          AP-04
File:        app.py
Lines:       48-58, 60-79
Description: /admin/reset-db (line 48) deletes all data from all tables with no
             authentication. /admin/query (line 60) executes arbitrary SQL from the
             request body with no authentication. Any HTTP client can reach these.
Impact:      Complete data loss and arbitrary code/query execution by any unauthenticated caller.
Fix:         PT-09
Recommendation: Move admin routes to a Blueprint protected by a @require_admin decorator
             that validates a JWT token with admin role.

---

### [CRITICAL] Plain-Text Passwords
ID:          AP-05
File:        database.py
Lines:       46-53
Description: Seed users are inserted with plaintext passwords: ("admin@loja.com",
             "admin123", "admin"). The login function in models.py compares passwords
             as plaintext strings.
Impact:      If the SQLite file is accessed, all user passwords are immediately readable.
Fix:         PT-04
Recommendation: Hash passwords at creation using werkzeug.security.generate_password_hash
             and verify with check_password_hash at login.

---

### [CRITICAL] SQL Injection in Search Query Builder
ID:          AP-01
File:        models.py
Lines:       275-285
Description: buscar_produtos() builds a dynamic query by appending user-supplied strings:
             query += " AND nome LIKE '%" + termo + "%'". This allows injection via the
             search term parameter.
Impact:      Attacker can exfiltrate or corrupt data via the /produtos/busca endpoint.
Fix:         PT-01
Recommendation: Use parameterized query with LIKE ? and pass "%termo%" as a tuple param.

---

### [HIGH] Secret Key and Debug Flag Exposed in Health Check Response
ID:          AP-06
File:        controllers.py
Lines:       114-120
Description: The /health endpoint returns secret_key: "minha-chave-super-secreta-123"
             and debug: True in its JSON response, exposing internal configuration to
             any caller.
Impact:      Attacker discovers the signing secret, enabling session forgery.
Fix:         PT-11
Recommendation: Remove secret_key, debug, and db_path from the health check response.

---

### [HIGH] Global Mutable Database Connection
ID:          AP-07
File:        database.py
Lines:       4-5, 8-10
Description: db_connection = None is a module-level global mutated by get_db() using
             `global db_connection`. A single connection shared across all threads is
             not thread-safe under concurrent requests.
Impact:      Race conditions and database corruption under concurrent load; application
             behaves unpredictably in production.
Fix:         PT-05
Recommendation: Replace with Flask's application context using flask.g per-request
             connection lifecycle.

---

### [HIGH] Notification Side-Effects Inside Controller
ID:          AP-08
File:        controllers.py
Lines:       83-90
Description: criar_pedido() contains print("ENVIANDO EMAIL/SMS/PUSH") directly in the
             controller after creating an order. This mixes notification concerns with
             HTTP flow orchestration.
Impact:      Notification logic cannot be tested, swapped, or disabled independently.
             Adding real email/SMS would bloat the controller further.
Fix:         PT-08
Recommendation: Extract notification calls to a services/notification_service.py module.

---

### [MEDIUM] N+1 Query Problem in Order Listing
ID:          AP-10
File:        models.py
Lines:       175-205, 215-245
Description: get_pedidos_usuario() and get_todos_pedidos() execute a SELECT per order
             to fetch items, and another SELECT per item to fetch the product name.
             For 10 orders with 3 items each, this generates 1 + 10 + 30 = 41 queries.
Impact:      Response time scales linearly with data; will degrade severely in production.
Fix:         PT-06
Recommendation: Replace nested loop queries with a single LEFT JOIN across pedidos,
             itens_pedido, and produtos.

---

### [MEDIUM] Duplicated Order Fetch Logic
ID:          AP-11
File:        models.py
Lines:       175-205, 215-245
Description: get_pedidos_usuario() and get_todos_pedidos() share identical 30-line loop
             bodies that differ only in the WHERE clause. Any bug fix must be applied
             to both functions.
Impact:      Maintenance burden doubles; functions will diverge and create inconsistent behavior.
Fix:         PT-07
Recommendation: Extract a shared _build_pedidos_query() helper and a single
             _execute_pedidos_query() function.

---

### [LOW] Print Statements as Logging
ID:          AP-13
File:        controllers.py, models.py, app.py
Lines:       Various (controllers.py:14, 25, 75, 95, 107, 119; models.py:throughout; app.py:52)
Description: print() is used for all operational logging across the codebase. There is
             no log level filtering, no structured output, and no way to control verbosity.
Impact:      Production logs are noisy and unfiltered; cannot integrate with log aggregators.
Fix:         PT-10
Recommendation: Replace all print() calls with import logging; logger = logging.getLogger(__name__).

---

### [LOW] Magic Numbers in Discount Calculation
ID:          AP-14
File:        models.py
Lines:       257-263
Description: relatorio_vendas() contains: if faturamento > 10000, if faturamento > 5000,
             if faturamento > 1000 with multipliers 0.1, 0.05, 0.02 as unexplained literals.
Impact:      Business rules cannot be understood or changed without reading the code.
Fix:         PT-12
Recommendation: Extract DISCOUNT_TIERS to config/settings.py as named constants.

---

### [LOW] Inconsistent Input Validation Between Create and Update
ID:          AP-12
File:        controllers.py
Lines:       53-65 (criar_produto), 77-95 (atualizar_produto)
Description: criar_produto() validates categoria against categorias_validas and validates
             nome length. atualizar_produto() does not validate categoria at all, allowing
             invalid categories on update.
Impact:      Data integrity inconsistency — valid create, corrupt update.
Fix:         Extract validation to a shared helper function called by both endpoints.
Recommendation: Create a validate_produto_input() helper in a validators module.

================================
Phase 2 complete.
Total findings: 13 (5C / 3H / 2M / 3L)

Proceed with Phase 3 — Refactoring? [y/n]
================================
```

---

## Formatting Rules

1. **Order:** Always CRITICAL first, then HIGH, MEDIUM, LOW within each group.
2. **Line numbers:** Must be exact integers or ranges (e.g., `45` or `45-52`). Never write "various" or "throughout" for the Lines field in findings — list specific line numbers.
3. **File paths:** Use relative paths from the project root (e.g., `models.py`, `src/controllers/user.js`).
4. **Description:** Must reference the specific code instance found, not generic descriptions. Quote the actual code snippet when possible.
5. **Impact:** Describe the worst-case scenario if the issue is not fixed.
6. **Fix:** Always reference the relevant Playbook pattern (PT-XX).
7. **Do not merge multiple files** into a single finding unless they are truly the same pattern. Each location gets its own finding or is explicitly listed in Lines with the exact line for each file.
