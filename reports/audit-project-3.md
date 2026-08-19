================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask
Files:   18 analyzed | ~550 lines of code

## Summary
CRITICAL: 1 | HIGH: 2 | MEDIUM: 3 | LOW: 4

## Findings

### [CRITICAL] Hardcoded SMTP Credentials
- **File:** services/notification_service.py:8-9
- **Description:** Gmail password for SMTP is hardcoded in clear text.
- **Impact:** Immediate exposure of email credentials.
- **Recommendation:** Utilize environment variables and an email provider service.

### [HIGH] Fat Controller (Violation of MVC)
- **File:** routes/task_routes.py:10-100
- **Description:** Controller methods contain heavy business logic (status checks, date parsing, mail logic).
- **Impact:** Logic is untestable, bloated controllers.
- **Recommendation:** Extract all business logic to `TaskService`.

### [HIGH] SQL Injection in Task Filter
- **File:** routes/task_routes.py:12-15
- **Description:** Task filter criteria uses string formatting directly from request args.
- **Impact:** Allows malicious users to bypass filters or extract sensitive data.
- **Recommendation:** Use SQLAlchemy filter parameters.

### [MEDIUM] Hardcoded Secret Key
- **File:** app.py:14
- **Description:** Flask `SECRET_KEY` is hardcoded as string.
- **Impact:** Potential for session integrity compromise.
- **Recommendation:** Load via `python-dotenv`.

### [MEDIUM] Bare Except Clause
- **File:** routes/task_routes.py:30-40
- **Description:** `try...except` block captures *all* exceptions, silencing errors.
- **Impact:** Debugging failures is nearly impossible in production.
- **Recommendation:** Catch specific exceptions and log stack traces.

### [MEDIUM] Missing Declarative Validation
- **File:** controllers/task_controller.py:all
- **Description:** Validation logic is imperative and scattered across functions.
- **Impact:** Inconsistent input validation, prone to bugs.
- **Recommendation:** Implement Pydantic models for request validation.

### [LOW] Direct Model Manipulation in Routing
- **File:** routes/task_routes.py:all
- **Description:** Direct query manipulation inside the route definitions.
- **Impact:** Violates MVC pattern; database logic leaked into the routing layer.
- **Recommendation:** Delegate database interactions to the Service/Model layers.

### [LOW] Outdated Date/Time API
- **File:** routes/task_routes.py:50
- **Description:** Usage of `datetime.utcnow()` (deprecated in Python 3.12+).
- **Impact:** Potential timezone inconsistencies.
- **Recommendation:** Use `datetime.now(timezone.utc)`.

### [LOW] Missing Type Hints
- **File:** services/task_service.py:all
- **Description:** No type annotations for function parameters or return types.
- **Impact:** Reduced IDE support and maintainability.
- **Recommendation:** Add PEP 484 type annotations.

### [LOW] Inconsistent API Response Schema
- **File:** controllers/task_controller.py:all
- **Description:** Error responses use inconsistent keys (e.g., `error` vs `message`).
- **Impact:** Poor developer experience; unpredictable API behavior.
- **Recommendation:** Centralize response formatting in a helper function.

================================
Total: 10 findings
================================
