# Anti-Patterns Catalog

This catalog defines anti-patterns to detect during Phase 2 (Architecture Audit). Each entry includes detection signals, severity classification, and recommended fixes.

---

## Severity Scale

- **CRITICAL**: Security vulnerabilities or severe architectural flaws that compromise data integrity, expose sensitive information, or make the system fundamentally broken.
- **HIGH**: Strong violations of MVC/SOLID that severely hinder maintainability, testability, or scalability.
- **MEDIUM**: Code quality issues, performance problems, or moderate architectural violations.
- **LOW**: Style issues, naming conventions, or minor improvements for readability.

---

## 1. SQL Injection (CRITICAL)

**Detection Signals:**
- String concatenation in SQL queries: `"SELECT * FROM x WHERE id = " + variable`
- Template strings in SQL: `` `SELECT * FROM x WHERE id = ${variable}` ``
- f-strings in SQL: `f"SELECT * FROM x WHERE id = {variable}"`
- `.format()` in SQL: `"SELECT * WHERE id = {}".format(variable)`
- Direct execution of user-provided SQL queries

**Impact:** Attackers can read, modify, or delete any data. Full database compromise possible.

**Recommendation:** Use parameterized queries / prepared statements:
- Python (sqlite3): `cursor.execute("SELECT * FROM x WHERE id = ?", (id,))`
- Python (SQLAlchemy): Use ORM methods or `text()` with bound parameters
- Node.js (sqlite3): `db.get("SELECT * FROM x WHERE id = ?", [id], callback)`
- Node.js (Sequelize): Use model methods or `sequelize.query()` with replacements

---

## 2. Hardcoded Credentials / Secrets (CRITICAL)

**Detection Signals:**
- Variables named `SECRET_KEY`, `PASSWORD`, `API_KEY`, `TOKEN` assigned string literals
- Database connection strings with embedded credentials
- Email passwords, SMTP credentials in source code
- Payment gateway keys in source code
- Default/weak passwords like `'123'`, `'admin123'`, `'senha123'`, `'password'`

**Impact:** Credentials exposed in version control. Attackers gaining repo access get full system access.

**Recommendation:** Use environment variables:
- Python: `os.environ.get('SECRET_KEY')` or `python-dotenv`
- Node.js: `process.env.SECRET_KEY` or `dotenv` package
- Create `.env` file (add to `.gitignore`) with all secrets

---

## 3. Insecure Password Storage (CRITICAL)

**Detection Signals:**
- Plaintext password comparison: `senha == input_senha`
- MD5 hashing: `hashlib.md5()`
- SHA1/SHA256 without salt for passwords
- Base64 encoding used as "encryption": `Buffer.from(pwd).toString('base64')`
- Custom/homegrown hashing functions (e.g., `badCrypto()`)
- Reversible encoding presented as hashing

**Impact:** If database is breached, all passwords are immediately compromised.

**Recommendation:** Use purpose-built password hashing:
- Python: `bcrypt.hashpw()` or `werkzeug.security.generate_password_hash()`
- Node.js: `bcrypt.hash()` or `argon2.hash()`

---

## 4. God Class / God File (HIGH)

**Detection Signals:**
- Single file with 200+ lines containing multiple responsibilities
- One class/module handling database access, business logic, validation, AND formatting
- File serving multiple unrelated domains (products + users + orders in same file)
- Class with 10+ methods spanning different concern areas

**Impact:** Impossible to test in isolation. Any change risks breaking unrelated functionality. High merge conflict risk.

**Recommendation:** Split into domain-specific modules following Single Responsibility Principle. One module per domain entity, one concern per layer.

---

## 5. Missing Authentication / Authorization (HIGH)

**Detection Signals:**
- Admin endpoints without auth middleware/decorators
- No token/session validation on protected routes
- Delete/update operations accessible without authentication
- Fake JWT tokens: `'fake-jwt-token-' + id`
- Login endpoint that returns user data but no actual auth mechanism

**Impact:** Any user can access or modify any data. Admin functions exposed to public.

**Recommendation:** Implement proper JWT or session-based authentication. Add auth middleware to protected routes. Validate tokens on every request.

---

## 6. Callback Hell / Pyramid of Doom (HIGH)

**Detection Signals (Node.js):**
- Nested callbacks 3+ levels deep
- `function(err, result)` patterns nested inside each other
- `const self = this` to preserve context across callbacks
- Inconsistent error handling across callback levels
- Complex async coordination with manual counters

**Impact:** Code is extremely hard to read, maintain, and debug. Error handling is unreliable. Race conditions are likely.

**Recommendation:** Refactor to async/await or Promises:
```javascript
// Before (callback hell)
db.get(query1, (err, row) => {
  db.run(query2, (err) => {
    db.run(query3, (err) => { ... });
  });
});

// After (async/await)
const row = await db.getAsync(query1);
await db.runAsync(query2);
await db.runAsync(query3);
```

---

## 7. N+1 Query Problem (MEDIUM)

**Detection Signals:**
- Database query inside a `for`/`forEach` loop
- Nested cursor/query execution for related data
- Creating new database cursors inside loops (e.g., `cursor2`, `cursor3`)
- Fetching parent records, then looping to fetch children one by one

**Impact:** Performance degrades linearly with data size. 100 orders = 100+ extra queries.

**Recommendation:** Use JOIN queries or batch loading:
```sql
-- Before: N+1
SELECT * FROM orders;
-- then for each order:
SELECT * FROM items WHERE order_id = ?;

-- After: Single JOIN
SELECT o.*, i.* FROM orders o
LEFT JOIN items i ON o.id = i.id;
```

---

## 8. Code Duplication (MEDIUM)

**Detection Signals:**
- Same validation logic repeated in multiple functions/routes
- Identical data transformation code in different handlers
- Copy-pasted error handling blocks
- Same business rules implemented in multiple locations
- Overdue/status checks duplicated across routes

**Impact:** Bug fixes must be applied in multiple places. Risk of inconsistent behavior.

**Recommendation:** Extract common logic into shared utility functions, base classes, or middleware. Define constants in a single location.

---

## 9. Missing Input Validation (MEDIUM)

**Detection Signals:**
- `request.json.get()` or `req.body` used without validation
- No type checking on user inputs
- No length/range validation on strings/numbers
- Email format not validated
- No schema validation library in use (despite being installed, e.g., Marshmallow)

**Impact:** Invalid data enters the system. Application crashes on unexpected input. Data integrity compromised.

**Recommendation:** Use validation libraries (Marshmallow, Joi, Zod) or implement validation middleware. Validate at system boundaries.

---

## 10. Sensitive Data Exposure (MEDIUM)

**Detection Signals:**
- Password hashes returned in API responses (`to_dict()` includes password field)
- Debug mode enabled in production: `app.config["DEBUG"] = True`
- Health endpoints exposing internal config (secret keys, DB paths)
- Secrets logged to console: `console.log(...paymentKey...)`
- Stack traces returned to clients in error responses

**Impact:** Attackers can extract sensitive information from normal API usage.

**Recommendation:** Exclude sensitive fields from API responses. Disable debug mode. Sanitize error messages. Never log secrets.

---

## 11. Global Mutable State (MEDIUM)

**Detection Signals:**
- Module-level mutable variables: `db_connection = None`, `globalCache = {}`, `totalRevenue = 0`
- Singleton patterns without thread safety
- `check_same_thread=False` on SQLite connections
- In-memory state that is lost on restart

**Impact:** Race conditions in concurrent environments. Unpredictable behavior. Data loss on restart.

**Recommendation:** Use dependency injection. Use thread-safe connection pools. Use proper caching solutions (Redis, Memcached) instead of in-memory dicts.

---

## 12. Poor Error Handling (MEDIUM)

**Detection Signals:**
- Bare `except:` or `except Exception:` catching everything
- Generic error messages: `"Erro DB"`, `"Internal error"`
- `print()` statements instead of logging framework
- Silent failures (catching exceptions and returning default values)
- No distinction between client errors (4xx) and server errors (5xx)

**Impact:** Difficult to debug production issues. Users get unhelpful error messages. Real errors hidden by catch-all handlers.

**Recommendation:** Catch specific exceptions. Use a logging framework (Python `logging`, Node.js `winston`/`pino`). Return appropriate HTTP status codes.

---

## 13. Missing Database Integrity Constraints (LOW)

**Detection Signals:**
- No FOREIGN KEY constraints defined
- No UNIQUE constraints on fields that should be unique (e.g., email)
- No NOT NULL constraints on required fields
- No CHECK constraints on value ranges (e.g., price >= 0)
- No CASCADE rules for related records
- Manual cascade deletes in application code

**Impact:** Orphaned records, duplicate entries, invalid data stored in database.

**Recommendation:** Add proper constraints at the database level. Use ORM relationship definitions with cascade rules.

---

## 14. Magic Numbers and Hardcoded Values (LOW)

**Detection Signals:**
- Numeric literals used directly: `if priority > 5`, `port = 3000`
- String literals for status values scattered across files
- Hardcoded URLs, ports, file paths
- Date format strings repeated: `'%Y-%m-%d'`

**Impact:** Difficult to maintain. Inconsistent values across codebase when changed in one place but not others.

**Recommendation:** Define constants in a central configuration or constants module. Use enums for status/type values.

---

## 15. No Pagination (LOW)

**Detection Signals:**
- `SELECT * FROM table` without LIMIT/OFFSET
- `.query.all()` or `.find({})` returning all records
- List endpoints returning unbounded results
- No `page`/`limit` query parameters

**Impact:** Performance degrades with data growth. Memory usage spikes. API response times increase.

**Recommendation:** Add pagination with sensible defaults (e.g., 20 items per page). Support `page` and `limit` query parameters.

---

## 16. Deprecated API Usage

### Python

| Deprecated | Modern Replacement | Since |
|------------|-------------------|-------|
| `datetime.utcnow()` | `datetime.now(timezone.utc)` | Python 3.12 |
| `os.popen()` | `subprocess.run()` | Python 3.0 |
| `cgi` module | `email.message`, `urllib.parse` | Python 3.11 |
| `imp` module | `importlib` | Python 3.4 |
| `optparse` module | `argparse` | Python 3.2 |
| `formatter` module | Removed | Python 3.10 |
| `distutils` module | `setuptools` | Python 3.10 |
| `asyncore` / `asynchat` | `asyncio` | Python 3.6 |
| `ssl.PROTOCOL_TLS` | `ssl.TLSVersion` | Python 3.10 |
| `hashlib.md5()` for passwords | `bcrypt` / `argon2` | N/A (insecure) |
| `flask.json.jsonify` redundant with `flask>=2.2` | Return dict directly | Flask 2.2 |

### Node.js

| Deprecated | Modern Replacement | Since |
|------------|-------------------|-------|
| `new Buffer()` | `Buffer.from()` / `Buffer.alloc()` | Node 6 |
| `require('url').parse()` | `new URL()` | Node 10 |
| `require('querystring')` | `URLSearchParams` | Node 10 |
| `fs.exists()` | `fs.existsSync()` or `fs.access()` | Node 4 |
| `crypto.createCipher()` | `crypto.createCipheriv()` | Node 10 |
| `util.pump()` | `stream.pipeline()` | Node 10 |
| `domain` module | `async_hooks` | Node 4 |
| Callback-based `fs` APIs | Promise-based `fs/promises` | Node 10 |
| `express.bodyParser()` | `express.json()` + `express.urlencoded()` | Express 4 |

**Detection:** Check import statements and function calls against this table. Flag any matches with the recommended modern replacement.
