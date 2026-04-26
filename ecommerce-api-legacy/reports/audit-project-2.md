================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.18.2
Files:   3 analyzed | ~168 lines of code

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 3 | LOW: 4

## Findings

### [CRITICAL] Hardcoded Credentials / Secrets
File: src/utils.js:2-5
Description: Config object contains literal credentials:
```js
dbUser: "admin_master",
dbPass: "senha_super_secreta_prod_123",
paymentGatewayKey: "pk_live_1234567890abcdef",
smtpUser: "no-reply@fullcycle.com.br"
```
All secrets — DB password, payment gateway key, SMTP user — are hardcoded in source code.
Impact: Anyone with repo access has production credentials. A git leak exposes all integrated systems (database, payment gateway, email).
Recommendation: Move all secrets to environment variables via a dedicated config module. Create a `.env.example` file with required variable names.

### [CRITICAL] God Class / God File
File: src/AppManager.js:1-141
Description: Single class `AppManager` handles 5 distinct domains across 141 lines:
- Database initialization and schema creation (lines 10-23)
- Checkout flow with payment processing (lines 28-78)
- Financial report generation (lines 80-128)
- User deletion (lines 131-137)
- Seed data insertion (lines 18-21)
No functionality can be tested or modified in isolation.
Impact: Impossible to test any feature independently. Changes to one domain (e.g., payments) risk breaking another (e.g., reports). Violates Single Responsibility Principle.
Recommendation: Split into separate modules: config, models (user, course, enrollment, payment), controllers, routes, and services.

### [CRITICAL] Unauthenticated Sensitive Endpoints
File: src/AppManager.js:80-128, 131-137
Description: Both `GET /api/admin/financial-report` and `DELETE /api/users/:id` have zero authentication or authorization middleware. The DELETE endpoint permanently removes user records with no identity check. The admin report exposes all financial data to any caller.
Impact: Any anonymous user can view complete financial reports and delete user accounts. No audit trail of who performed destructive operations.
Recommendation: Add authentication middleware to all endpoints. Require admin role for `/api/admin/*` routes. Add authorization check before DELETE operations.

### [CRITICAL] Weak Cryptography
File: src/utils.js:17-23
Description: `badCrypto()` function concatenates the first 2 chars of base64-encoded password 10,000 times, then truncates to 10 chars:
```js
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```
No salt, no real hashing algorithm, trivially reversible. Used to store user passwords at AppManager.js:68.
Impact: All user passwords are effectively stored in plaintext. Any database leak exposes every user's password.
Recommendation: Replace with bcrypt or argon2. Use proper salted hashing with a vetted library.

### [HIGH] Sensitive Data Exposure in Logs
File: src/AppManager.js:45
Description: `console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)` logs the full credit card number and payment gateway API key to stdout.
Impact: PCI-DSS violation. Credit card numbers appear in logs accessible to any operator. Gateway key is logged alongside, enabling fraudulent charges.
Recommendation: Mask card numbers (show only last 4 digits). Never log API keys or secrets. Use a proper logging library with log-level controls.

### [HIGH] Business Logic in Route Layer
File: src/AppManager.js:28-78
Description: The `/api/checkout` handler performs: input validation (line 35), course lookup (line 37), user lookup/creation (lines 40-74), payment processing with card validation (lines 43-48), enrollment creation (line 50), payment recording (line 54), audit logging (line 57), and cache update (line 59) — all inside one route handler.
Impact: Zero reusability — payment logic, enrollment logic, and user creation cannot be used from any other context. Impossible to unit test any individual step.
Recommendation: Extract to controller functions calling model/service layers. Each concern (user creation, payment processing, enrollment) becomes an independent, testable function.

### [HIGH] Tight Coupling / Global Mutable State
File: src/utils.js:9-10, src/AppManager.js:26
Description: `let globalCache = {}` and `let totalRevenue = 0` are module-level mutable state exported globally. `totalRevenue` is exported but never updated. In AppManager, `const self = this` workaround (line 26) to bypass scope issues from nested callbacks.
Impact: Shared mutable state across requests creates race conditions under concurrency. The `self = this` pattern indicates poor async design. `totalRevenue` is dead code.
Recommendation: Remove global mutable state. Use proper dependency injection. Convert callbacks to async/await to eliminate scope issues.

### [HIGH] Callback / Promise Nesting Hell
File: src/AppManager.js:37-77
Description: 5 levels of nested callbacks in checkout:
`db.get()` (course) → `db.get()` (user) → `db.run()` (enrollment) → `db.run()` (payment) → `db.run()` (audit_log)
Plus manual counter pattern in financial report (lines 86-127): `coursesPending`, `enrPending` decremented to track completion.
Impact: Code is extremely difficult to read and maintain. Errors in inner callbacks are hard to trace. No way to use try/catch for error handling.
Recommendation: Use async/await with promise-based db wrapper or a library like `sqlite3` with `.promise()` support. Flatten all nested callbacks into sequential await calls.

### [MEDIUM] N+1 Query Problem
File: src/AppManager.js:83-128
Description: Financial report executes queries inside loops: for each course → query enrollments (line 92); for each enrollment → query user (line 104) AND query payment (line 106). With 10 courses of 50 enrollments each, this generates 500+ individual queries.
Impact: Report performance degrades linearly with data volume. At scale, this endpoint becomes unusable.
Recommendation: Replace with a single JOIN query: `SELECT c.title, u.name, u.email, p.amount, p.status FROM courses c LEFT JOIN enrollments e ON c.id = e.course_id LEFT JOIN users u ON e.user_id = u.id LEFT JOIN payments p ON e.id = p.enrollment_id`.

### [MEDIUM] Inadequate Error Handling
File: src/AppManager.js:passim (lines 41, 51, 55, 58, 84, 134)
Description: All error responses are generic strings: `"Erro DB"`, `"Erro Matrícula"`, `"Erro Pagamento"`, `"Erro ao criar usuário"`. No error codes, no structured format, and `err` object is never logged — the actual error details are silently discarded.
Impact: Impossible to debug issues from API responses. Client receives no actionable information. Real errors are swallowed without logging.
Recommendation: Create centralized error handling middleware. Use structured error responses with error codes. Always log the actual `err` object server-side.

### [MEDIUM] Deprecated API Usage — Callback-based sqlite3 + Verbose Mode
File: src/AppManager.js:1
Description: `require('sqlite3').verbose()` enables verbose tracing in all environments. All database operations use callback-based API instead of modern async/await patterns.
Impact: Verbose mode pollutes production logs with internal SQLite traces. Callback-based code is harder to maintain and error-prone compared to async/await.
Recommendation: Remove `.verbose()` call. Use a promise-based wrapper or switch to a modern sqlite library that supports async/await natively.

### [LOW] Poor Variable Naming
File: src/AppManager.js:29-33
Description: Variables use cryptic abbreviations:
```js
let u = req.body.usr;    // username
let e = req.body.eml;    // email
let p = req.body.pwd;    // password
let cid = req.body.c_id; // course id
let cc = req.body.card;  // credit card
```
Impact: Code requires mental translation. New developers must decode abbreviations before understanding the logic.
Recommendation: Use descriptive names: `userName`, `email`, `password`, `courseId`, `cardNumber`. Also rename request body keys to match.

### [LOW] Magic Numbers / Magic Strings
File: src/AppManager.js:46, AppManager.js:48
Description: Card validation logic `cc.startsWith("4") ? "PAID" : "DENIED"` uses hardcoded "4" as approval rule, and strings `"PAID"`/`"DENIED"` as payment status — these should be constants.
Impact: Business rules are hidden in conditionals. Changing payment status values requires finding all occurrences.
Recommendation: Define constants: `PAYMENT_STATUS = { PAID: 'PAID', DENIED: 'DENIED' }`. Extract card validation to a named function with a descriptive constant.

### [LOW] Debug Artifacts in Production Code
File: src/AppManager.js:45, src/utils.js:12-14
Description: `console.log()` used as logging mechanism throughout (checkout processing, cache operations). No log levels, no structured logging, no way to disable in production.
Impact: Console output clutters production logs. No way to filter or redirect log output.
Recommendation: Replace `console.log` with a proper logging library (winston, pino) with configurable log levels.

### [LOW] Unused Code / Dead Code
File: src/utils.js:10
Description: `let totalRevenue = 0` is exported but never read or updated anywhere in the codebase. `globalCache` is written to (AppManager.js:59) but never read back.
Impact: Dead code adds confusion about intended functionality. Future developers may waste time understanding unused state.
Recommendation: Remove `totalRevenue` and `globalCache`. If caching is needed, implement it properly with a dedicated cache module.

================================
Total: 15 findings
CRITICAL: 4 | HIGH: 4 | MEDIUM: 3 | LOW: 4
================================
