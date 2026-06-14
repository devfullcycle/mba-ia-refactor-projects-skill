================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript + Express 4.18.2
Files:   4 analyzed | ~193 lines of code

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 3 | LOW: 1

## Findings

### [CRITICAL] Hardcoded Credentials and Secrets
File: src/utils.js:1-7
Description: Four production secrets hardcoded in source:
  `dbPass: "senha_super_secreta_prod_123"`,
  `paymentGatewayKey: "pk_live_1234567890abcdef"`,
  `smtpUser: "no-reply@fullcycle.com.br"`,
  `dbUser: "admin_master"`
Impact: Any developer with repository access owns all credentials. Leaked via git history even if later removed.
Recommendation: Remove all secrets from source. Load via `process.env.*` using the `dotenv` package. Add `.env` to `.gitignore`.

### [CRITICAL] Weak/Fake Password Hashing
File: src/utils.js:17-22 | src/AppManager.js:18,68
Description: `badCrypto()` uses base64 repetition truncated to 10 chars — not a cryptographic hash. Additionally, the seed user has password `'123'` stored as plain text (`AppManager.js:18`).
Impact: Entire user credential database exposed if DB is breached; trivially reversible.
Recommendation: Replace with `bcrypt.hash(password, 10)` and `bcrypt.compare()`. Install `bcryptjs` package.

### [CRITICAL] Unauthenticated Admin Financial Endpoint
File: src/AppManager.js:80-128
Description: `GET /api/admin/financial-report` returns full revenue data, student names and emails, and payment amounts with no authentication middleware whatsoever.
Impact: Any anonymous caller can exfiltrate all financial and PII data.
Recommendation: Add an authentication middleware (JWT or session) and an admin role check before this route.

### [CRITICAL] Insecure Payment Processing
File: src/AppManager.js:44-47
Description: Payment approval based solely on card number prefix: `let status = cc.startsWith("4") ? "PAID" : "DENIED"`. Any Visa card number (starting with 4) is approved automatically.
Impact: Financial fraud — anyone who knows a Visa card starts with "4" gets free enrollment.
Recommendation: Integrate a real payment gateway SDK (Stripe, Adyen). Never implement payment logic in application code.

### [CRITICAL] God Class — No Separation of Concerns
File: src/AppManager.js:1-141
Description: Single class mixes DB schema initialization, seed data, route definitions, business logic (payment processing, user creation, enrollment), and audit logging across 141 lines covering 4+ domains.
Impact: Impossible to unit test any layer in isolation; every change risks breaking unrelated functionality; onboarding is blocked by the entire class needing to be understood at once.
Recommendation: Split into MVC layers: controllers/ (route handlers), services/ (business logic), models/ (DB access), config/ (configuration).

### [HIGH] Business Logic Embedded in Route Handlers
File: src/AppManager.js:28-137
Description: All checkout orchestration, user creation, payment simulation, enrollment, and audit logging live inside inline callback functions inside `setupRoutes()`. No service or model layer exists.
Impact: Business rules cannot be reused, unit tested, or swapped independently.
Recommendation: Extract to service layer: `CheckoutService`, `UserService`, `EnrollmentService`.

### [HIGH] No Database Transactions on Multi-Step Operations
File: src/AppManager.js:50-62
Description: Checkout creates an enrollment record, then a payment record, then an audit log in three separate `db.run()` calls with no transaction wrapping. Each step can fail independently.
Impact: Partial failures leave orphaned enrollments without payments, or payments without enrollments — financial and data integrity violations.
Recommendation: Wrap in `BEGIN TRANSACTION` / `COMMIT` / `ROLLBACK` using sqlite3's serialize + transaction API.

### [HIGH] Unauthenticated Destructive DELETE Endpoint
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` accepts any `id` from URL params with no authentication, no authorization check, and deletes the user row while leaving all associated enrollments and payments orphaned (the response message even acknowledges this: `"matrículas e pagamentos ficaram sujos no banco"`).
Impact: Unauthenticated user deletion + cascading data corruption in enrollments/payments.
Recommendation: Add auth middleware; perform cascading delete or soft-delete with FK constraints.

### [HIGH] Global Mutable State
File: src/utils.js:9-10
Description: `let globalCache = {}` and `let totalRevenue = 0` are module-level mutable variables mutated during request processing via `logAndCache()`.
Impact: In a multi-process or concurrent environment, requests share and corrupt each other's state. Cache never expires.
Recommendation: Use a proper caching layer (e.g., node-cache, Redis) or pass state explicitly through service instances.

### [MEDIUM] N+1 Query Problem in Financial Report
File: src/AppManager.js:88-127
Description: For each course (1 query), fetches all enrollments (N queries), then for each enrollment fetches user + payment (2N more queries). For 2 courses with 1 enrollment each: 1+2+2+2 = 7 queries; scales as O(N²).
Impact: Response time and DB load grow exponentially with data volume.
Recommendation: Replace nested callbacks with a single JOIN query:
  `SELECT c.title, u.name, p.amount, p.status FROM courses c LEFT JOIN enrollments e ON ... LEFT JOIN users u ON ... LEFT JOIN payments p ON ...`

### [MEDIUM] Deprecated Callback Hell Pattern
File: src/AppManager.js:28-77
Description: Checkout handler nests 5 levels of callbacks: `db.get → db.get → db.run → db.run → db.run`. Error handling is inconsistent (some `err` checks silently proceed).
Impact: Unreadable code, missing error propagation, impossible to add try/catch, deprecated Node.js async pattern.
Recommendation: Promisify sqlite3 calls with `util.promisify()` and refactor to `async/await` with centralized try/catch.

### [MEDIUM] Missing Input Validation
File: src/AppManager.js:29-35
Description: Checkout only checks for field presence (`!u || !e || !cid || !cc`) with no format, type, or range validation. Email format, card number format, course ID as integer, and name length are all unchecked.
Impact: Invalid data stored in DB; potential crashes on malformed input; no meaningful error messages.
Recommendation: Validate with a schema library (`joi` or `zod`): email regex, `courseId` as positive integer, card as non-empty string.

### [LOW] Poor Variable Naming
File: src/AppManager.js:29-34
Description: Request fields destructured as single-letter abbreviations: `u` (username), `e` (email), `p` (password), `cid` (course_id), `cc` (credit card). The request body fields themselves use obscure names: `usr`, `eml`, `pwd`, `c_id`.
Impact: Reduced readability; card number variable `cc` is ambiguous; new developers cannot understand code without decoding abbreviations.
Recommendation: Use full names: `const { username, email, password, courseId, cardNumber } = req.body`.

================================
Total: 13 findings
CRITICAL: 5 | HIGH: 4 | MEDIUM: 3 | LOW: 1
================================
