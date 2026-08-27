================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express
Files:   20 analyzed | ~600 lines of code

## Summary
CRITICAL: 3 | HIGH: 1 | MEDIUM: 3 | LOW: 3

## Findings

### [CRITICAL] Insecure Password Storage
- **File:** utils/utils.js:4-7
- **Description:** Uses Base64 encoding for "hashing" passwords in `secureCrypto`.
- **Impact:** Passwords are trivially reversible; high risk of credential exposure.
- **Recommendation:** Replace with `bcrypt` or `argon2` for secure one-way hashing.

### [CRITICAL] Callback Hell
- **File:** controllers/checkoutController.js:15-60
- **Description:** Deeply nested callbacks for DB transactions create a "Pyramid of Doom".
- **Impact:** Extremely fragile and impossible to test or maintain effectively.
- **Recommendation:** Refactor to use `async/await` with `util.promisify` or promise-based SQLite driver.

### [CRITICAL] Direct SQL Injection
- **File:** routes/routes.js:all
- **Description:** Query parameters are concatenated directly into raw SQL queries.
- **Impact:** Complete database exposure.
- **Recommendation:** Use parameterized queries via `sqlite3` driver.

### [HIGH] Hardcoded Payment Credentials
- **File:** config/config.js:6
- **Description:** Payment gateway keys are hardcoded in the configuration object.
- **Impact:** Risk of credential theft if repository is exposed.
- **Recommendation:** Migrate to `.env` file and `process.env`.

### [MEDIUM] Database Atomicity Violation
- **File:** controllers/userController.js:4-10
- **Description:** `deleteUser` removes the user but orphan records remain in `enrollments` and `payments`.
- **Impact:** Inconsistent database state; broken integrity.
- **Recommendation:** Use database transactions or cascading deletes.

### [MEDIUM] Query N+1 Vulnerability
- **File:** controllers/reportController.js:20-40
- **Description:** Iterates through users to fetch payments one by one in a loop.
- **Impact:** Massive database load; performance bottleneck as user count grows.
- **Recommendation:** Implement a SQL JOIN or `IN` clause to fetch data in one query.

### [MEDIUM] Generic Error Handling
- **File:** middlewares/errorHandler.js:4-5
- **Description:** Error handler simply sends 500 without classifying error type.
- **Impact:** Hides root cause; poor developer experience.
- **Recommendation:** Distinguish between client errors (4xx) and server errors (5xx).

### [LOW] Lack of Input Sanitization
- **File:** routes/routes.js:all
- **Description:** Direct usage of `req.body` without validation middleware.
- **Impact:** Open to malformed input causing application crashes.
- **Recommendation:** Implement `joi` or `express-validator` middleware.

### [LOW] Poor Variable Naming
- **File:** controllers/checkoutController.js:all
- **Description:** Uses single-letter variables like `u`, `e`, `p`.
- **Impact:** Code is difficult to understand without excessive documentation.
- **Recommendation:** Use descriptive variable names (`user`, `email`, `payment`).

### [LOW] Dead Code / Unused Dependencies
- **File:** package.json:all
- **Description:** Multiple unused libraries included.
- **Impact:** Security attack surface increase and bloated node_modules.
- **Recommendation:** Run `npm prune` and remove unused packages.

================================
Total: 10 findings
================================
