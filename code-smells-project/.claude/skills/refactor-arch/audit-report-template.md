# Audit Report Template

Use this template to generate the Phase 2 audit report. Fill in all placeholders with actual values from the analysis.

---

## Report Format

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <project directory name>
Stack:   <Language> + <Framework>
Files:   <N> analyzed | ~<M> lines of code

## Summary
CRITICAL: <count> | HIGH: <count> | MEDIUM: <count> | LOW: <count>

## Findings

### [<SEVERITY>] <Anti-Pattern Name>
File: <file_path>:<start_line>-<end_line>
Description: <Clear description of the problem found>
Impact: <What happens if this is not fixed>
Recommendation: <Specific action to resolve>

### [<SEVERITY>] <Anti-Pattern Name>
File: <file_path>:<line>
Description: <Clear description of the problem found>
Impact: <What happens if this is not fixed>
Recommendation: <Specific action to resolve>

... (repeat for each finding, ordered by severity: CRITICAL -> HIGH -> MEDIUM -> LOW)

================================
Total: <N> findings
================================
```

---

## Rules

1. **Ordering**: Findings MUST be ordered by severity — CRITICAL first, then HIGH, MEDIUM, LOW.

2. **Minimum findings**: The report must contain at least **5 findings**. If fewer are found, look deeper.

3. **Minimum critical/high**: At least **1 finding** must be CRITICAL or HIGH severity.

4. **File references**: Every finding MUST include exact file path and line number(s).
   - Single line: `File: models.py:28`
   - Line range: `File: models.py:1-350`
   - Multiple locations: `File: models.py:28, models.py:47, models.py:57`

5. **Description**: Must be specific and actionable. Avoid vague descriptions like "bad code" or "could be better". Instead: "SQL query built with string concatenation allowing injection attacks".

6. **Impact**: Explain the real-world consequence — security breach, data loss, performance degradation, maintenance burden.

7. **Recommendation**: Provide a concrete fix, not just "fix it". Example: "Use parameterized queries: `cursor.execute('SELECT * FROM x WHERE id = ?', (id,))`"

8. **Anti-pattern name**: Use the standard name from the anti-patterns catalog (e.g., "SQL Injection", "God Class", "N+1 Query Problem").

9. **Deprecated APIs**: If any deprecated API usage is found, include it as a separate finding with the modern replacement.

10. **Confirmation prompt**: After printing the report, ALWAYS display:
```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
Wait for user confirmation before proceeding.

---

## Example Finding

```
### [CRITICAL] SQL Injection
File: models.py:28
Description: SQL query built using string concatenation: `"SELECT * FROM produtos WHERE id = " + str(id)`. User-controlled input is directly interpolated into the query string.
Impact: Attackers can execute arbitrary SQL, read/modify/delete any data, or bypass authentication entirely.
Recommendation: Use parameterized queries: `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`
```

```
### [HIGH] God Class
File: models.py:1-314
Description: Single file contains all database operations for 4 different domains (products, users, orders, reports) with 314 lines of mixed business logic and data access.
Impact: Impossible to test individual components in isolation. Any change risks breaking unrelated functionality.
Recommendation: Split into domain-specific model files: produto_model.py, usuario_model.py, pedido_model.py, each handling only its own domain.
```

```
### [MEDIUM] N+1 Query Problem
File: models.py:187-200
Description: For each order, separate queries are executed to fetch order items (cursor2) and product names (cursor3), creating nested query loops.
Impact: Performance degrades linearly. 100 orders = 300+ queries instead of 2-3 JOINs.
Recommendation: Use JOIN query: `SELECT p.*, i.* FROM pedidos p LEFT JOIN itens_pedido i ON p.id = i.pedido_id`
```
