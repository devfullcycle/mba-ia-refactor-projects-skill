# Anti-Patterns Catalog (Phase 2)

Each entry has: **ID**, default **severity**, **detection signals** (textual greps + what to confirm by reading), **why it matters**, and the **playbook transformation** that fixes it (`T-xx` in `refactoring-playbook.md`).

A grep hit is only a *candidate*. Confirm by reading the code before reporting. Report each confirmed problem with exact `file:line`.

## Severity scale (MVC + SOLID based)

| Severity | Definition | Examples |
|---|---|---|
| **CRITICAL** | Severe architecture or security flaws that break correct operation, expose sensitive data, or completely violate separation of concerns | hardcoded credentials, SQL injection, God class mixing DB + business + routing, unauthenticated arbitrary SQL endpoint, plaintext/MD5 passwords |
| **HIGH** | Strong MVC/SOLID violations that make maintenance and testing very hard | heavy business logic in routes/controllers, tight coupling without DI, global mutable state, non-atomic multi-step writes, debug mode hardcoded on |
| **MEDIUM** | Standardization problems, duplication, moderate performance bottlenecks | N+1 queries, missing/duplicated validation, inconsistent error handling, deprecated APIs, misuse of middleware |
| **LOW** | Readability and hygiene | bad names, magic numbers, unused imports, `print` logging, verbose boolean returns |

Raise or lower a finding by **one** level only with a written reason in the finding (e.g., "raised to HIGH: endpoint is unauthenticated").

---

## CRITICAL

### AP-01 Hardcoded secrets and credentials
- **Signals:**
  - `grep -nEi "(secret|password|passwd|pass|pwd|api_?key|token|private_?key|gateway|smtp).{0,20}[:=]\s*['\"][^'\"]{3,}['\"]"`
  - Literal connection strings with user:password, `pk_live_`, `sk_live_`, `AKIA`, `-----BEGIN`
  - `app.config["SECRET_KEY"] = "<literal>"`, config objects with literal secrets (`dbPass: "..."`)
  - Seed users with known passwords are **not** this finding (that is seed data) unless used as production defaults.
- **Confirm:** value is a literal, not read from `os.environ` / `process.env` / a secret store.
- **Why:** anyone with repo access gets production credentials; secrets cannot be rotated per environment.
- **Fix:** T-01.

### AP-02 SQL injection (query built by string concatenation / interpolation)
- **Signals:**
  - Python: `execute\(\s*["'].*["']\s*\+`, `execute\(f["']`, `"... WHERE x = " + str(`, `% (` inside SQL, `.format(` inside SQL
  - JS: `` db\.(run|get|all|query)\(`[^`]*\$\{ `` , `"SELECT ... " + req.`
  - Query strings assembled in a variable then executed: `query += " AND col = '" + value + "'"`
- **Confirm:** user-controlled data reaches the concatenated string (trace from `request.*`, `req.body`, `req.params`, function args fed by routes).
- **Why:** authentication bypass (`' OR 1=1 --`), data exfiltration, data destruction; also breaks on legitimate input such as `D'Agua`.
- **Fix:** T-02.

### AP-03 God Class / God Module (no separation of concerns)
- **Signals:**
  - One class/file that contains **two or more** of: DB connection/schema, SQL/ORM queries, business rules, HTTP route registration, external integrations (payment, email)
  - Class names like `*Manager`, `*Handler`, `App*`, `Utils` with `setupRoutes(app)` + `db.run(` in the same body
  - A `models.py`/`models.js` > ~200 lines serving 3+ unrelated domain entities with business rules (pricing, discounts, stock) inside
- **Confirm:** list the responsibilities with line ranges; report the whole range (e.g. `models.py:1-314`).
- **Why:** impossible to test in isolation; any change risks every feature (violates SRP).
- **Fix:** T-03.

### AP-04 Unprotected administrative / destructive / privilege endpoints
- **Signals:**
  - Routes containing `admin`, `reset`, `query`, `exec`, `debug` without an authentication/authorization check
  - Endpoint that executes SQL received from the request (`cursor.execute(request...` / `execute(dados["sql"])`)
  - Endpoint that wipes tables (`DELETE FROM` without `WHERE`)
  - **Privilege / account-state changes without a guard:** a body field such as `role`, `is_admin`, `tipo`, `permissions` accepted on create/update (`data.get('role')`, `req.body.role`); `active` / `enabled` / `status` of a *user account* changed by any caller; deletion of user accounts (`DELETE /users/<id>`, `db.session.delete(user)`)
  - **Account takeover without a guard:** `password` / `email` / `username` of an existing user changed by a caller that is neither that user nor an admin (`user.set_password(data['password'])`, `user.email = data['email']` in an update route with no identity check). Changing an admin's password and logging in yields an admin token, so this is privilege escalation too
  - Login that returns a token that no route ever verifies (`'fake-jwt-token-' + id`): the guard does not exist
- **Confirm:** no decorator/middleware/guard checks identity or role before the action.
- **Why:** remote arbitrary SQL execution, full data loss, or privilege escalation by any anonymous caller.
- **Recommendation format (mandatory):** list every operation that will be guarded, one per line, as `METHOD /path` + condition + required role. Example:
  - `POST /users` when `role` is privileged → admin
  - `PUT /users/<id>` when the body changes `role` or `active` → admin
  - `PUT /users/<id>` when the body changes `password` or `email` → the user themself or an admin (owner-or-admin)
  - `DELETE /users/<id>` → admin

  Every operation listed here is mandatory work for Phase 3 (SKILL.md Global rules 4–5).
- **Fix:** T-17 (and remove arbitrary-SQL capability or restrict it to read-only behind admin auth).

### AP-05 Insecure password storage
- **Signals:**
  - Password stored as received: `INSERT ... senha` / `pass` with the raw request value
  - Weak/fast hashes: `hashlib.md5(`, `hashlib.sha1(`, `crypto.createHash('md5'|'sha1')`
  - Home-made "crypto": base64 loops, `Buffer.from(pwd).toString('base64')`, truncation `substring(0, 10)`
  - Login comparing plaintext in SQL: `WHERE email = ? AND senha = ?`
- **Why:** a single DB leak exposes every user's password (and their reuse elsewhere).
- **Fix:** T-09.

### AP-06 Sensitive data exposure (responses and logs)
- **Signals:**
  - Serializers returning secrets: `to_dict()` / row mappers including `password`, `senha`, `pass`, tokens
  - Health/info endpoints returning config: `"secret_key":`, `"db_path":`, `"debug":`
  - Logs printing card numbers, passwords, keys: `console.log(\`...${cc}...${config.paymentGatewayKey}\`)`, `print(... senha ...)`
  - Raw exception text returned to clients: `jsonify({"erro": str(e)})`, `res.send(err.message)` (lower to MEDIUM if only error text)
- **Why:** leaks credentials/PII to any client or log reader (LGPD/PCI violations).
- **Fix:** T-10.

---

## HIGH

### AP-07 Business logic in the routing / controller-HTTP layer (Fat route)
- **Signals:**
  - Route handlers > ~30 lines; handlers containing pricing, discount, stock, status-transition, payment, or report-aggregation rules
  - Handlers calling the DB directly (`Model.query`, `db.session`, `cursor.execute`, `db.run`) **and** applying rules on the result
  - Same handler mixing request parsing, validation, persistence, notifications (`print("ENVIANDO EMAIL")`)
- **Why:** rules cannot be reused or unit-tested without HTTP; violates SRP and MVC.
- **Fix:** T-04.

### AP-08 Tight coupling / no dependency injection
- **Signals:**
  - Modules importing a concrete DB singleton everywhere (`from database import get_db` in every layer)
  - Classes instantiating their own dependencies in constructors (`this.db = new sqlite3.Database(...)`, `self.smtp = smtplib.SMTP(...)`)
  - No composition root / app factory (`app = Flask(__name__)` at import time with side effects; `new AppManager()` creating everything)
- **Why:** cannot swap DB/integrations for tests; every module depends on concretions (DIP violation).
- **Fix:** T-05.

### AP-09 Global mutable state
- **Signals:**
  - `global ` keyword; module-level `x = None` later reassigned (`db_connection`); module-level dict/list caches (`globalCache = {}`, `let totalRevenue = 0`, `self.notifications = []` on a singleton)
  - `sqlite3.connect(..., check_same_thread=False)` shared across threads/requests
- **Why:** race conditions, cross-request data leaks, untestable hidden coupling.
- **Fix:** T-06.

### AP-10 Non-atomic multi-step writes / broken referential integrity
- **Signals:**
  - Several `INSERT`/`UPDATE` in sequence (order + items + stock; enrollment + payment + audit) without `BEGIN/COMMIT/ROLLBACK` or `with session.begin()`
  - Early `return` in the middle of a write sequence leaving partial data
  - Deleting a parent row without handling children (`DELETE FROM users` while `enrollments`/`payments` reference it), no `FOREIGN KEY` / cascade
  - Read-then-write stock check without locking (oversell)
- **Why:** partial writes and orphan rows corrupt data; reports become wrong.
- **Fix:** T-11.

### AP-11 Callback hell / pyramid of doom (async control flow)
- **Signals:** (JS) 3+ nested callbacks `(err, x) => { ... db.get(..., (err, y) => {` ; manual counters to know when parallel callbacks finish (`pending--; if (pending === 0) res.json(...)`); errors ignored in inner callbacks (`(err) => {` with no `if (err)`).
- **Why:** unreadable, error paths silently dropped, response ordering non-deterministic, easy to send two responses.
- **Fix:** T-12.

### AP-12 Insecure configuration hardcoded for production
- **Signals:** `debug=True` / `app.config["DEBUG"] = True` / `app.run(debug=True, host="0.0.0.0")`; `CORS(app)` with no origin restriction on an API with auth; `NODE_ENV` ignored; fake auth tokens (`'fake-jwt-token-' + id`).
- **Why:** Werkzeug debugger = remote code execution when exposed; permissive CORS + fake tokens = no real access control.
- **Fix:** T-01 (debug from env, default off) and T-17 for auth.

---

## MEDIUM

### AP-13 N+1 queries
- **Signals:**
  - A query inside a `for` / `forEach` / `map` over the result of another query (`for row in rows: cursor.execute(...)`, `courses.forEach(c => db.all(...))`)
  - ORM lazy relationship access in loops (`len(u.tasks)`, `Model.query.get(t.user_id)` inside a loop)
  - Multiple `COUNT(*)` queries that a single `GROUP BY` could answer
- **Why:** response time grows linearly with data; DB load multiplies.
- **Fix:** T-08.

### AP-14 Missing or duplicated input validation
- **Signals:**
  - Request fields used without type/range checks (`dados["preco"]` compared with `< 0` without checking it is a number; `int(request.args[...])` without try)
  - The same validation copy-pasted in create and update handlers; validation helpers that exist but are not used (`process_task_data`, `validate_email` unused)
  - Payload `None` dereferenced (`request.get_json().get(...)` when body is absent)
- **Why:** 500 errors from bad input, inconsistent rules between endpoints.
- **Fix:** T-14.

### AP-15 Code duplication (DRY violations)
- **Signals:** identical row→dict mapping blocks repeated; the same business rule (e.g., "is overdue") re-implemented in several handlers; same list of valid statuses in multiple files.
- **Why:** rules diverge over time; fixes must be applied N times.
- **Fix:** T-15 (constants) + T-04 (single rule in model/controller).

### AP-16 Inconsistent / absent error handling
- **Signals:**
  - Bare `except:` or `except Exception` that swallows errors; `try/except` repeated in every handler
  - Mixed response formats for errors (plain text `res.send("Erro DB")` vs JSON), inner callbacks ignoring `err`
  - No global error handler (`@app.errorhandler`, Express `(err, req, res, next)` middleware)
- **Why:** clients cannot rely on error shape; real failures are hidden.
- **Fix:** T-07.

### AP-17 Deprecated / legacy APIs
- **Signals:** see the table below. Confirm against the **installed** version (and with deprecation warnings enabled when possible).
- **Why:** will break on upgrade; often already emits warnings; modern replacements are safer/faster.
- **Fix:** T-13.

| Ecosystem | Deprecated usage (grep) | Modern equivalent |
|---|---|---|
| Python ≥ 3.12 | `datetime.utcnow()` / `datetime.utcfromtimestamp(` | `datetime.now(timezone.utc)` / `datetime.fromtimestamp(ts, timezone.utc)` |
| SQLAlchemy ≥ 2.0 | `Model.query.get(id)` / `session.query(X).get(id)` | `db.session.get(Model, id)` |
| SQLAlchemy ≥ 2.0 | `Model.query.filter(...)` (legacy Query API) | `db.session.execute(db.select(Model).where(...)).scalars()` (acceptable to keep `Model.query` for simple reads if Flask-SQLAlchemy 3.x; `.get` must change) |
| SQLAlchemy | `engine.execute(` / `connection.execute("raw string")` | `connection.execute(text("..."), params)` |
| Flask ≥ 2.3 | `@app.before_first_request`, `flask.json.JSONEncoder`, `app.json_encoder` | app factory init / `app.json` provider |
| Flask ≥ 2.2 | `send_file(..., attachment_filename=)`, `cache_timeout=` | `download_name=`, `max_age=` |
| Python | `imp`, `distutils`, `asyncio.get_event_loop()` without running loop, `typing.List` (3.9+) | `importlib`, `setuptools`/`packaging`, `asyncio.run`, `list[...]` |
| Node.js | `new Buffer(` / `Buffer(` | `Buffer.from(` / `Buffer.alloc(` |
| Node.js | `require('body-parser')` with Express ≥ 4.16 | `express.json()` / `express.urlencoded()` |
| Node.js | `url.parse(`, `querystring` | `new URL(`, `URLSearchParams` |
| Node.js | `fs.exists(`, `crypto.createCipher(` | `fs.access`/`fs.existsSync`, `crypto.createCipheriv(` |
| Node.js | callback-only DB/driver usage where a promise API exists | `util.promisify` / `async`/`await` |
| Express 4 → 5 | `res.send(status, body)`, `res.json(status, obj)`, `req.param()`, `app.del(` | `res.status(s).send(body)`, `req.params/req.query/req.body`, `app.delete(` |
| sqlite3 (Node) | `.verbose()` left on in production code paths | call only in development (it adds stack-trace overhead) — LOW unless used in prod |

### AP-18 Side effects and infrastructure in the wrong place
- **Signals:** notifications/emails simulated with `print` inside controllers; SMTP connection details inside a domain service; `db.create_all()` / schema creation executed at import time; seed data mixed with connection code.
- **Why:** hidden side effects on import, hard to test, couples domain to infrastructure.
- **Fix:** T-05 (move to `services/` adapters wired by the composition root) + T-01 for credentials.

---

## LOW

### AP-19 Magic numbers and magic strings
- **Signals:** literal thresholds in rules (`> 10000`, `* 0.1`, `priority <= 2`, `len(password) < 4`), status strings repeated (`'pending'`, `'PAID'`, `'aprovado'`), port numbers, `"#000000"`.
- **Why:** meaning hidden; changing a rule requires hunting literals.
- **Fix:** T-15.

### AP-20 Poor naming
- **Signals:** one/two-letter names outside tiny lambdas (`u`, `e`, `p`, `cc`, `cid`, `t`), cryptic API fields (`usr`, `eml`, `pwd`, `c_id`), misleading names (`badCrypto`, `AppManager`, `utils` holding config).
- **Why:** readability; misleading names hide intent.
- **Fix:** T-16 (rename internally; keep public request field names for compatibility).

### AP-21 Unused imports, variables and dead code
- **Signals:** Python `import os, sys, json` never referenced (check with `grep -c`), exported-but-unused values (`totalRevenue`), helper functions never called, unused method params.
- **Why:** noise, misleading dependencies, slower imports.
- **Fix:** T-16.

### AP-22 `print` / `console.log` as logging
- **Signals:** `print(` / `console.log(` in request paths for operational messages or errors.
- **Why:** no levels, no structure, cannot be silenced or shipped; often leaks data (see AP-06).
- **Fix:** T-16.

### AP-23 Verbose conditionals and non-idiomatic code
- **Signals:** `if cond: return True else: return False`; deeply nested `if` pyramids (3+ levels) for a single boolean; `type(x) == list` instead of `isinstance`; manual counting loops where `sum`/`filter` fits.
- **Why:** readability.
- **Fix:** T-16.

---

## Quick grep pack

Run from the project root (adapt the file globs to the detected stack):

```bash
# AP-01 secrets
grep -rnEi "(secret|passw|pwd|api_?key|token|gateway|smtp)[a-z_]*['\"]?\s*[:=]\s*['\"][^'\"]{3,}" --include=*.{py,js,ts} .
# AP-02 SQL injection
grep -rnE "execute\(.*(\+|%|\.format\(|f\")|(run|get|all|query)\(\`[^\`]*\\$\{" --include=*.{py,js,ts} .
grep -rnE "(SELECT|INSERT|UPDATE|DELETE).*['\"]\s*\+" --include=*.{py,js,ts} .
# AP-05 password hashing
grep -rnE "md5|sha1|base64|badCrypto" --include=*.{py,js,ts} .
# AP-06 sensitive output
grep -rnE "['\"](password|senha|pass|secret_key)['\"]\s*:" --include=*.{py,js,ts} .
# AP-09 global state
grep -rnE "^\s*global |^(let|var) [a-zA-Z]+ = (\{\}|\[\]|0)|check_same_thread=False" --include=*.{py,js,ts} .
# AP-12 debug
grep -rnE "debug\s*=\s*True|DEBUG\"?\]?\s*=\s*True" --include=*.py .
# AP-13 N+1 (inspect loops around these)
grep -rnE "for .* in .*:|\.forEach\(" --include=*.{py,js,ts} .
# AP-16 bare except
grep -rnE "except\s*:|except Exception" --include=*.py .
# AP-17 deprecated
grep -rnE "utcnow\(|\.query\.get\(|new Buffer\(|body-parser|url\.parse\(" --include=*.{py,js,ts} .
# AP-22 print logging
grep -rnE "^\s*print\(|console\.log\(" --include=*.{py,js,ts} .
```

## Coverage rule

The audit must evaluate **all 23 entries** for every project. In the report only confirmed findings appear, but you must be able to justify why an entry did not apply (e.g., "no SQL — ORM with bound parameters").
