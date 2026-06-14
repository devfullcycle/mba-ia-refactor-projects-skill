# Anti-Patterns Catalog

This catalog contains at least 8 anti-patterns with detection signals and severity classification. Use this during Phase 2 to audit the codebase.

---

## CRITICAL Severity

### AP-C1: SQL Injection
**Severity:** CRITICAL  
**Description:** User input concatenated directly into SQL queries without parameterization.

**Detection signals:**
```python
# Python — string concatenation
cursor.execute("SELECT * FROM users WHERE email = '" + email + "'")
cursor.execute("SELECT * FROM users WHERE id = " + str(id))
f"SELECT * FROM users WHERE name = '{name}'"
```
```javascript
// Node.js — string concatenation
db.run(`SELECT * FROM users WHERE email = '${email}'`)
db.get("SELECT * FROM users WHERE id = " + id)
```

**Safe pattern (parameterized):**
```python
cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
cursor.execute("SELECT * FROM users WHERE id = ?", (id,))
```
```javascript
db.get("SELECT * FROM users WHERE id = ?", [id], callback)
```

**Impact:** Complete database compromise, data exfiltration, data destruction.

---

### AP-C2: Hardcoded Credentials / Secrets
**Severity:** CRITICAL  
**Description:** Passwords, API keys, secret keys, or connection strings hardcoded in source files.

**Detection signals:**
```python
SECRET_KEY = "minha-chave-super-secreta-123"
app.config["SECRET_KEY"] = "some-fixed-string"
DB_PASSWORD = "password123"
API_KEY = "sk-live-abc123"
```
```javascript
const paymentGatewayKey = "pk_live_1234567890abcdef"
const dbPassword = "senha123"
const secretKey = "my-secret"
```

**Also check:** `.env` files committed to version control, `config.py` with literal values.

**Impact:** Credential theft, unauthorized access, complete system compromise.

---

### AP-C3: Plain Text / Weak Password Storage
**Severity:** CRITICAL  
**Description:** Passwords stored without hashing, or using broken algorithms (MD5, SHA1).

**Detection signals:**
```python
# Plain text storage
user.password = request.json['password']
db.execute("INSERT INTO users (password) VALUES (?)", (password,))

# Weak hashing
import hashlib
hashed = hashlib.md5(password.encode()).hexdigest()
hashed = hashlib.sha1(password.encode()).hexdigest()
```
```javascript
// Fake/broken crypto
function badCrypto(pwd) { return Buffer.from(pwd).toString('base64').slice(0,10) }
const hash = crypto.createHash('md5').update(password).digest('hex')
```

**Correct pattern:**
```python
from werkzeug.security import generate_password_hash, check_password_hash
hashed = generate_password_hash(password)  # bcrypt-based
```

**Impact:** All user credentials exposed if database is breached; rainbow table attacks.

---

### AP-C4: Unauthenticated Dangerous Endpoints
**Severity:** CRITICAL  
**Description:** Admin or destructive endpoints accessible without authentication.

**Detection signals:**
```python
# No auth decorator, but dangerous operations
@app.route('/admin/reset-db', methods=['POST'])
def reset_db():
    cursor.execute("DROP TABLE IF EXISTS users")

@app.route('/admin/query', methods=['POST'])
def execute_query():
    query = request.json.get('query')
    cursor.execute(query)  # executes arbitrary SQL!
```

**Impact:** Complete data loss, remote code execution, unauthorized access.

---

### AP-C5: God Class / God Module
**Severity:** CRITICAL  
**Description:** A single class or file contains all application logic across multiple domains — database access, business rules, routing, validation, and formatting — with no separation of concerns.

**Detection signals:**
- Single file > 300 lines handling 3+ domains
- Same file contains: route handlers + DB queries + business logic + validation
- Functions like `criar_produto()`, `criar_usuario()`, `criar_pedido()` all in one file
- Class with 10+ methods covering unrelated responsibilities

**Impact:** Impossible to test in isolation, cascading bugs, extremely difficult to maintain.

---

### AP-C6: Insecure Payment Processing
**Severity:** CRITICAL  
**Description:** Payment logic based on trivially-bypassable conditions, or payment gateway keys hardcoded.

**Detection signals:**
```javascript
// Card approval based on first digit only
let status = cc.startsWith("4") ? "PAID" : "DENIED"
// Any card starting with 4 (all Visa cards) is automatically approved
```

**Impact:** Financial fraud, unauthorized transactions, regulatory violations.

---

## HIGH Severity

### AP-H1: Business Logic in Controllers/Routes
**Severity:** HIGH  
**Description:** Route handlers contain complex business logic, calculations, or domain rules instead of delegating to services/models.

**Detection signals:**
```python
@app.route('/api/orders', methods=['POST'])
def create_order():
    # Complex discount calculation directly in route handler
    if total > 10000:
        discount = total * 0.10
    elif total > 5000:
        discount = total * 0.05
    # DB operations directly here
    cursor.execute("INSERT INTO orders ...")
```

**Impact:** Cannot reuse logic, impossible to unit test business rules, violates SRP.

---

### AP-H2: Global Mutable State
**Severity:** HIGH  
**Description:** Application-level state stored in global variables that are mutated during request processing.

**Detection signals:**
```javascript
let globalCache = {}
let totalRevenue = 0

// Modified during request handling
globalCache[userId] = data
totalRevenue += amount
```
```python
active_users = []
stats = {"requests": 0}
# Modified in route handlers without synchronization
```

**Impact:** Race conditions in concurrent environments, data corruption, unpredictable behavior.

---

### AP-H3: No Dependency Injection / Hard Coupling
**Severity:** HIGH  
**Description:** Classes or functions directly instantiate their dependencies instead of receiving them, making testing and replacement impossible.

**Detection signals:**
```python
class UserService:
    def __init__(self):
        self.db = sqlite3.connect('users.db')  # hard-coded dependency
        self.mailer = SMTPMailer('smtp.gmail.com')  # hard-coded
```

**Correct pattern:**
```python
class UserService:
    def __init__(self, db_connection, mailer):
        self.db = db_connection
        self.mailer = mailer
```

**Impact:** Cannot mock dependencies for testing, tightly coupled code, hard to swap implementations.

---

### AP-H4: Password / Sensitive Data in API Responses
**Severity:** HIGH  
**Description:** Serialization methods include sensitive fields (password hashes, tokens, internal IDs) in API responses.

**Detection signals:**
```python
def to_dict(self):
    return {
        'id': self.id,
        'email': self.email,
        'password': self.password,  # NEVER include this
        'role': self.role
    }
```

**Impact:** Credential exposure, security breach, privacy violation.

---

### AP-H5: Missing Authentication / Broken Authorization
**Severity:** HIGH  
**Description:** Endpoints accessible without authentication, or users can access/modify resources belonging to other users.

**Detection signals:**
```python
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    # No auth check — any request gets all tasks
    return jsonify(Task.query.all())

@app.route('/api/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    # No check if this task belongs to the authenticated user
    task = Task.query.get(id)
    task.update(request.json)
```

**Impact:** Data theft, unauthorized modification, privacy breach.

---

### AP-H6: Race Conditions in Multi-Step Operations
**Severity:** HIGH  
**Description:** Multiple database operations that should be atomic executed separately without transactions, leading to inconsistent state.

**Detection signals:**
```javascript
// Multiple db operations without transaction
db.run("INSERT INTO enrollments ...", () => {
    db.run("INSERT INTO payments ...", () => {
        // If this fails, enrollment exists without payment
    })
})
```

**Correct pattern:**
```javascript
db.run('BEGIN TRANSACTION', () => {
    db.run("INSERT INTO enrollments ...", () => {
        db.run("INSERT INTO payments ...", (err) => {
            if (err) db.run('ROLLBACK')
            else db.run('COMMIT')
        })
    })
})
```

**Impact:** Orphaned records, financial inconsistency, data integrity violations.

---

## MEDIUM Severity

### AP-M1: N+1 Query Problem
**Severity:** MEDIUM  
**Description:** Fetching a list of items and then making a separate database query for each item, resulting in N+1 total queries.

**Detection signals:**
```python
# Get all tasks, then query user for each task
tasks = Task.query.all()  # 1 query
for task in tasks:
    user = User.query.get(task.user_id)  # N queries!
    category = Category.query.get(task.category_id)  # N more!
```
```javascript
db.all("SELECT * FROM courses", (err, courses) => {
    courses.forEach(course => {
        db.all("SELECT * FROM enrollments WHERE course_id = ?", [course.id], ...)
        // N queries for N courses
    })
})
```

**Correct pattern (JOIN):**
```python
tasks = db.session.query(Task, User).join(User).all()
# OR use eager loading
tasks = Task.query.options(joinedload(Task.user)).all()
```

**Impact:** Exponential performance degradation as data grows; 100 records = 201 queries.

---

### AP-M2: Code Duplication (DRY Violation)
**Severity:** MEDIUM  
**Description:** Same logic copy-pasted in multiple locations, leading to inconsistency when one is updated but not others.

**Detection signals:**
- Identical or near-identical blocks of 5+ lines in multiple files
- Same validation logic in multiple routes
- Overdue calculation repeated in routes, models, and reports:
```python
# In task_routes.py lines 30-39:
if task.due_date and task.status != 'done':
    if task.due_date < datetime.now():
        task_data['is_overdue'] = True

# Same block in task_routes.py lines 71-80 — exact duplicate
# Same block in report_routes.py lines 33-43 — exact duplicate
```

**Impact:** Inconsistent behavior when fixing bugs (fix in one place, miss others).

---

### AP-M3: Missing Input Validation
**Severity:** MEDIUM  
**Description:** User input accepted and used without validation of type, format, range, or business rules.

**Detection signals:**
```python
@app.route('/api/products', methods=['POST'])
def create_product():
    nome = request.json.get('nome')     # no length check
    preco = request.json.get('preco')   # no type/range check
    # Directly inserted into DB without validation

# Missing email format validation
# Missing date format validation
# Missing required field checks
```

**Impact:** Invalid/corrupt data in database, application crashes, security vulnerabilities.

---

### AP-M4: Missing Pagination on List Endpoints
**Severity:** MEDIUM  
**Description:** Endpoints that return lists fetch ALL records from the database without limits.

**Detection signals:**
```python
Task.query.all()                    # returns ALL rows
cursor.execute("SELECT * FROM products")  # returns ALL rows
```

**Correct pattern:**
```python
page = request.args.get('page', 1, type=int)
per_page = request.args.get('per_page', 20, type=int)
tasks = Task.query.paginate(page=page, per_page=per_page)
```

**Impact:** Memory overflow, timeout errors, denial of service with large datasets.

---

### AP-M5: Deprecated Callback Pattern (Node.js)
**Severity:** MEDIUM  
**Description:** Using callback-style asynchronous code instead of Promises or async/await, leading to callback hell.

**Detection signals:**
```javascript
// Callback hell — nested 4+ levels deep
db.get("SELECT ...", (err, user) => {
    if (err) return res.send("Erro DB")
    db.run("INSERT ...", (err) => {
        if (err) return res.send("Erro")
        db.run("INSERT ...", (err) => {
            // 4+ levels deep
        })
    })
})
```

**Modern pattern:**
```javascript
// async/await
async function processCheckout(req, res) {
    try {
        const user = await db.getAsync("SELECT ...", [params])
        await db.runAsync("INSERT ...", [values])
        res.json({ success: true })
    } catch (err) {
        res.status(500).json({ error: err.message })
    }
}
```

**Impact:** Error handling impossible, unreadable code, difficult to debug, deprecated Node.js pattern.

---

### AP-M6: Bare Exception Handling
**Severity:** MEDIUM  
**Description:** Catching all exceptions without specifics, hiding bugs and making debugging impossible.

**Detection signals:**
```python
try:
    db.session.commit()
except:                      # catches EVERYTHING including KeyboardInterrupt
    pass                     # silently swallows the error

try:
    result = process()
except Exception:            # still too broad
    return jsonify({'error': 'Unknown error'})
```

**Correct pattern:**
```python
try:
    db.session.commit()
except sqlalchemy.exc.IntegrityError as e:
    db.session.rollback()
    return jsonify({'error': 'Duplicate entry'}), 409
except sqlalchemy.exc.SQLAlchemyError as e:
    db.session.rollback()
    logger.error(f"DB error: {e}")
    return jsonify({'error': 'Database error'}), 500
```

**Impact:** Bugs hidden in production, impossible to debug, system in unknown state.

---

## LOW Severity

### AP-L1: Magic Numbers
**Severity:** LOW  
**Description:** Unexplained numeric literals embedded in code without named constants.

**Detection signals:**
```python
if total > 10000:          # what does 10000 represent?
    discount = total * 0.1

if len(title) > 200:       # why 200?
    return error

if priority < 1 or priority > 5:  # business rule not expressed
```

**Correct pattern:**
```python
MAX_TITLE_LENGTH = 200
MIN_PRIORITY = 1
MAX_PRIORITY = 5
PREMIUM_DISCOUNT_THRESHOLD = 10000

if len(title) > MAX_TITLE_LENGTH:
    return error
```

**Impact:** Unclear business rules, values changed in some places but missed in others.

---

### AP-L2: Poor Variable Naming
**Severity:** LOW  
**Description:** Single-letter variables, abbreviations, or names that don't describe their purpose.

**Detection signals:**
```javascript
const u = req.body.usr      // what is u? what is usr?
const e = req.body.eml      // email?
const p = req.body.pwd      // password?
const cid = req.body.cid    // course id?
let r = db.get(...)         // r = result?
```

**Correct pattern:**
```javascript
const username = req.body.username
const email = req.body.email
const password = req.body.password
const courseId = req.body.courseId
```

**Impact:** Reduced readability, harder onboarding, confusion during debugging.

---

### AP-L3: Unused Imports
**Severity:** LOW  
**Description:** Import statements for modules that are never used in the file.

**Detection signals:**
```python
import json, os, sys, time  # only one of these may be used
from flask import Flask, jsonify, request, session  # session never used
```

**Impact:** Code bloat, confusion about what the module actually uses, slower startup.

---

### AP-L4: Debug Mode in Production Code
**Severity:** LOW (if addressed via config) / CRITICAL (if hardcoded `True`)  
**Description:** Debug flags hardcoded to `True` instead of read from environment.

**Detection signals:**
```python
app.config["DEBUG"] = True          # hardcoded
app.run(debug=True, host="0.0.0.0") # hardcoded
```

**Correct pattern:**
```python
app.config["DEBUG"] = os.getenv("DEBUG", "False").lower() == "true"
app.run(debug=app.config["DEBUG"])
```

**Note:** Classify as CRITICAL if `debug=True` is the only setting and there's no environment override.

**Impact:** Stack traces exposed to users, interactive debugger accessible remotely.
