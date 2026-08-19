================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   20 analyzed | ~500 lines of code

## Summary
CRITICAL: 2 | HIGH: 1 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] SQL Injection Vulnerability
- **File:** models/pedido.py:13-65
- **Description:** Raw SQL queries are constructed using concatenation and f-strings without parameterization.
- **Impact:** Allows malicious input to compromise the database.
- **Recommendation:** Use SQLAlchemy parameterized queries or Flask-SQLAlchemy built-in methods.

### [CRITICAL] Unsafe Database Cleanup Endpoint
- **File:** routes/routes.py:51-57
- **Description:** Admin endpoint `/admin/reset-db` performs `DELETE` on all tables without authentication.
- **Impact:** Immediate data loss for production instances.
- **Recommendation:** Implement strict role-based access control (RBAC).

### [HIGH] Hardcoded Secret Key
- **File:** app.py:8
- **Description:** `SECRET_KEY` is hardcoded as a literal string in the main application file.
- **Impact:** Session hijacking vulnerability if committed to VCS.
- **Recommendation:** Load `SECRET_KEY` from environment variables using `python-dotenv`.

### [MEDIUM] Violation of Separation of Concerns (God Class)
- **File:** models/pedido.py:1-150
- **Description:** The `Pedido` model handles database logic, business rules, and serialization.
- **Impact:** Impossible to maintain or unit test independently.
- **Recommendation:** Refactor into `PedidoService`, `PedidoModel`, and a dedicated DTO.

### [MEDIUM] Direct Model Manipulation in Controller
- **File:** controllers/pedido_controller.py:15-26
- **Description:** Controller directly calls `PedidoModel.criar` instead of delegating to a Service layer.
- **Impact:** Controller becomes tightly coupled to domain model internals.
- **Recommendation:** Introduce a Service layer (`PedidoService`) to manage business transactions.

### [MEDIUM] Inconsistent Error Handling
- **File:** controllers/produto_controller.py:all
- **Description:** Each route handler implements its own `try-except` blocks.
- **Impact:** Unpredictable API responses and code duplication.
- **Recommendation:** Implement a global error handler middleware.

### [MEDIUM] Missing Input Sanitization
- **File:** controllers/pedido_controller.py:15
- **Description:** User input is processed without prior validation against a schema.
- **Impact:** Injection vulnerabilities and data integrity issues.
- **Recommendation:** Use Pydantic or Marshmallow for schema validation.

### [LOW] Magic Numbers
- **File:** models/pedido.py:120-130
- **Description:** Business thresholds for discounts are hardcoded as literals.
- **Impact:** Fragile code, difficult to update business logic.
- **Recommendation:** Move thresholds to a configuration file.

### [LOW] Missing Type Annotations
- **File:** services/usuario_service.py:all
- **Description:** Functions lack explicit Python type hints.
- **Impact:** Decreased code maintainability and IDE tooling effectiveness.
- **Recommendation:** Add type annotations to all public methods.

### [LOW] Inconsistent Variable Naming
- **File:** controllers/usuario_controller.py:all
- **Description:** Mixing snake_case and camelCase.
- **Impact:** Low maintainability, confusing API schema.
- **Recommendation:** Enforce consistent naming conventions throughout.

================================
Total: 10 findings
================================
