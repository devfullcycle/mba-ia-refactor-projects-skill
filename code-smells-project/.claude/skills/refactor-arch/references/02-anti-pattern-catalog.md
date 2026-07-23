# 02 — Anti-Pattern Catalog

Phase 2 scans the code against this catalog. For each pattern: **what it is**, **detection signals**
(concrete, grep-able), **default severity**, and a **typical recommendation**. Severities follow the
project standard (CRITICAL / HIGH / MEDIUM / LOW).

> A single pattern often appears at many call sites. Record the worst offenders with exact `path:line`
> ranges; you may collapse identical instances into one finding with a line range.

---

## CRITICAL

### C1. SQL Injection (string-concatenated / f-string SQL)
**What:** untrusted values are concatenated into a SQL string instead of being parameterized.
**Signals (Python):** `cursor.execute("... " + value)`, `cursor.execute(f"... {value}")`,
`cursor.execute("... %s" % ...)`, `"... WHERE id = " + str(id)`, dynamic `"WHERE 1=1" + query +=`.
**Signals (JS):** `` db.run(`SELECT ... ${x}`) ``, `"SELECT ... " + x`, template literals in SQL.
**Severity:** CRITICAL (remote data exfiltration / auth bypass / destruction).
**Note:** parameterized placeholders (`?` in sqlite3, `%s` in psycopg2, `?`/`$1`) are SAFE — do not
flag them. A project can be safe from C1 and still guilty of everything else.
**Recommendation:** use placeholders + a params list/tuple everywhere.

### C2. Hardcoded Secrets & Credentials
**What:** secrets (API keys, `SECRET_KEY`, DB passwords, SMTP passwords, `pk_live_`/`sk_` keys)
committed in source, or a `.env` file that IS committed / present but never loaded.
**Signals:** `SECRET_KEY = "..."`, `app.config["SECRET_KEY"] = "literal"`, `password = "..."`,
`"pk_live_..."`, `senha_super_secreta`, a `.env` file present in the tree, `SMTP_PASSWORD=...`.
**Severity:** CRITICAL.
**Recommendation:** move every secret to env vars (`os.environ` / `process.env`) loaded via a config
module; add `.env` to `.gitignore` and provide `.env.example`.

### C3. God Class / God File / Big Ball of Mud
**What:** one file or class owns multiple architectural responsibilities (DB connection + schema +
seeds + routing + business logic + reporting). Impossible to test or reason about in isolation.
**Signals:** a single class named `*Manager`/`*Service`/`*Container` with `db`, `setupRoutes`,
`initDb`, and route handlers all as methods; a `models.py`/`app.py` that also runs SQL and enforces
business rules; > ~150 lines mixing concerns.
**Severity:** CRITICAL (complete breakdown of separation of concerns).
**Recommendation:** split into Models / Controllers / Services / Routes; keep the entry point as a
thin composition root.

### C4. Insecure Password Storage
**What:** passwords stored in plaintext, or hashed with a broken/unsalted algorithm.
**Signals:** `INSERT INTO usuarios (... senha ...) VALUES (... '<plain>')`; `hashlib.md5(pwd).hexdigest()`;
`hashlib.sha1`; a hand-rolled "hash" (base64, XOR, truncation); login that does `WHERE senha = '<plain>'`.
**Severity:** CRITICAL (credential disclosure / trivial cracking).
**Recommendation:** hash with bcrypt/argon2/scrypt (per-user salt) via a vetted library; verify by
constant-time comparison, never by matching hashes inside SQL.

### C5. Unauthenticated Destructive / Arbitrary-Execution Endpoints
**What:** admin or dangerous routes (DB wipe, arbitrary raw SQL execution, bulk delete, user
impersonation) exposed with no authentication, authorization, or confirmation token.
**Signals:** `@app.route("/admin/reset-db"...)`, `@app.route("/admin/query"...)` that runs
`cursor.execute(request_body)`, `app.delete('/api/users/:id')` with no auth middleware.
**Severity:** CRITICAL.
**Recommendation:** require auth + role check; never execute user-supplied SQL; gate destructive
ops behind an explicit, scoped admin role.

### C6. Sensitive Data Leakage in Responses / Logs
**What:** passwords (even hashed), full card numbers (PAN), or secret keys returned in API responses
or written to stdout/logs.
**Signals:** `"senha": row["senha"]` in a serializer / `to_dict()`; `"password": self.password`;
`"secret_key": ...` in a health-check payload; `console.log(\`cartão ${cc}\`)`; `print(card)`.
**Severity:** CRITICAL (PCI-DSS breach; offline cracking; full secret disclosure).
**Recommendation:** never serialize secrets; redact PAN to last 4; mask secrets in logs.

---

## HIGH

### H1. Business Logic in Routes / Controllers (no service layer)
**What:** pricing, discounts, state machines, validation rules, and side-effects (notifications,
audit) live inside HTTP handlers instead of a domain/service layer.
**Signals:** `if preco < 0:` / category allow-lists / status state machines inside a `def route`;
`print("ENVIANDO EMAIL ...")` inside a controller; discount tiers computed in a "model" function.
**Severity:** HIGH.
**Recommendation:** move rules to a `services/` layer; controllers orchestrate HTTP ↔ service only.

### H2. Global Mutable State / Module-Level DB Singleton
**What:** a module-level shared DB connection or mutable cache used across all requests/threads.
**Signals:** `db_connection = None` + `global db_connection`; `let globalCache = {}`;
`let totalRevenue = 0`; a single `sqlite3.connect(..., check_same_thread=False)` reused everywhere;
`db = SQLAlchemy()` at module scope that every file imports directly.
**Severity:** HIGH (race conditions, cross-request leakage, untestable).
**Recommendation:** request-scoped connections (Flask `g` / per-request in Node), or a proper pool;
inject the store, don't import a global.

### H3. Missing Authentication / Authorization
**What:** endpoints that mutate data, return PII, or change roles have no auth/session/role check;
a `role`/`tipo` field exists but is never enforced; login returns a token that is never verified.
**Signals:** `app.delete(...)` / `POST /users` / `/admin/*` with no decorator/middleware; a `token`
field returned by `/login` that no other endpoint reads; `is_admin()` defined but never called.
**Severity:** HIGH.
**Recommendation:** add auth middleware/decorator; enforce roles; verify tokens on protected routes.

### H4. Callback Hell / No DI / Tight Coupling
**What:** deep nested callbacks (Pyramid of Doom), layers wired by direct `import`/`require` (no
injection), `const self = this` workarounds, the framework app passed INTO a manager.
**Signals:** 4+ levels of nested `(err, x) => {}`; `const manager = new AppManager(); manager.setupRoutes(app)`;
`import models` hardcoded inside `controllers`; `const self = this;`.
**Severity:** HIGH (untestable, unmaintainable).
**Recommendation:** use async/await; invert dependencies via constructors/parameters; thin entry point.

### H5. Non-Atomic Multi-Write / TOCTOU Races
**What:** several writes that should be one transaction are done without `BEGIN/COMMIT/ROLLBACK`;
stock validated in one pass then decremented in another with no locking.
**Signals:** multiple `INSERT`/`UPDATE` in sequence with a single `commit()` at the end and no
rollback on partial failure; `SELECT` stock → later `UPDATE estoque = estoque - n` with no lock.
**Severity:** HIGH.
**Recommendation:** wrap multi-writes in a transaction; re-check constraints inside the transaction.

### H6. Debug Mode + Wildcard Binding in Production Path
**What:** `debug=True`/`app.run(debug=True)` reachable in the run path, and/or binding to `0.0.0.0`.
**Signals:** `app.run(debug=True, host="0.0.0.0", ...)`; `app.config["DEBUG"] = True`;
`app.run(debug=True)` under `if __name__ == "__main__"`.
**Severity:** HIGH (Werkzeug debugger = remote code execution if reachable).
**Recommendation:** drive debug from env (`os.environ.get("FLASK_DEBUG")`), default off; bind to loopback in dev.

---

## MEDIUM

### M1. N+1 Queries
**What:** a DB query executed inside a loop (or inside `.forEach`/`.map`), once per parent row.
**Signals (Python):** `for row in rows: ... cursor.execute(...)` ; `for t in tasks: User.query.get(t.user_id)`;
`len(u.tasks)` inside a loop; `Task.query.filter_by(user_id=u.id)` inside `for u in users`.
**Signals (JS):** `courses.forEach(c => db.all(...))`; nested `db.get` inside `forEach`.
**Severity:** MEDIUM (latency scales with data).
**Recommendation:** one JOIN / aggregate / `joinedload`, or a grouped `GROUP BY` count.

### M2. Bare/Swallowed Exceptions + Error Information Leakage
**What:** `except:` / `except Exception as e: return jsonify({"erro": str(e)}), 500` everywhere;
internal messages/stack fragments leaked to clients; no logging.
**Signals:** repeated `try: ... except Exception as e: return ..., 500`; bare `except:`; returning
`str(e)` to the client; no `app.errorhandler`.
**Severity:** MEDIUM (info disclosure + hides bugs).
**Recommendation:** one global error handler; catch specific exceptions; log server-side, return
generic messages to clients.

### M3. Missing Input Validation
**What:** request bodies/params read with no schema check; `int(request.args[...])` that throws 500;
no email/password/format rules; tags/arrays stored verbatim.
**Signals:** `dados.get(...)` with no validation; `int(priority)` on raw query strings; no
`marshmallow`/`joi`/`zod` despite complex payloads; `data['active']` assigned without type check.
**Severity:** MEDIUM.
**Recommendation:** validate at the edge with a schema lib; coerce and reject early with 400.

### M4. Code Duplication / Divergent Parallel Logic
**What:** the same rule copy-pasted across handlers (overdue calc ×N, validation ×N, the boilerplate
try/except ×N, two near-identical list functions).
**Signals:** 6 copies of the same `if due_date < now` block; a `validate_status`/`is_overdue` helper
that exists but is **never called** while routes re-implement it inline.
**Severity:** MEDIUM.
**Recommendation:** extract one canonical helper; actually use it; delete the copies.

### M5. Misplaced Responsibility / Wrong Layer for a Resource
**What:** a first-class resource (e.g. `/categories`) registered under the wrong blueprint
(e.g. `report_bp`); `/login` hidden inside the users blueprint; health/login on the app root.
**Signals:** `@report_bp.route('/categories', ...)`; a CRUD resource whose routes live in a
non-matching module.
**Severity:** MEDIUM.
**Recommendation:** one blueprint/module per resource; system routes (`/health`, `/login`) isolated.

### M6. CORS Misconfiguration / Missing Security Headers
**What:** `CORS(app)` with no origin allow-list; no `helmet`; no rate limiting on auth/checkout.
**Signals:** `CORS(app)`; no `cors` config object; `app.use(helmet(...))` absent.
**Severity:** MEDIUM.
**Recommendation:** explicit origin allow-list; add `helmet` (Node) / `flask-talisman` (Python).

### M7. Import-Time Side Effects / Manual Cascade Delete
**What:** `db.create_all()` runs at import time; seeding destroys data with no env guard; deletes
manually loop to "cascade" instead of a DB-level FK `ON DELETE CASCADE`.
**Signals:** `with app.app_context(): db.create_all()` at module scope; `for t in tasks: db.session.delete(t)`;
`Model.query.delete()` in a seed with no guard.
**Severity:** MEDIUM.
**Recommendation:** move schema/seed to a CLI command; declare FK cascades; guard seeds by env.

---

## LOW

### L1. Magic Numbers / Hardcoded Literals
**What:** unnamed constants scattered (`10000`, `0.1`, `"4"`, `"PAID"`, port `5000/3000`, discount
tiers, status/category lists defined in two places).
**Signals:** numeric literals in conditions; duplicated string enums; a `VALID_STATUSES` constant
that exists but routes don't use.
**Severity:** LOW.
**Recommendation:** named constants/enums in one place; reference them everywhere.

### L2. `print`/`console.log` as the Logger
**What:** diagnostics via `print(...)` / `console.log(...)` with no levels, timestamps, or redaction.
**Signals:** `print("Listando ...")`, `console.log(...)` sprinkled in handlers.
**Severity:** LOW.
**Recommendation:** use the stdlib/app logger (Python `logging`, Node `pino`/`winston`).

### L3. Poor Naming / Shadowed Builtins / Dead Code / Style
**What:** params named `id` (shadows builtin), `u`/`e`/`cc` single letters, `badCrypto`, `self = this`;
`var` where `const` fits; missing `"use strict"`; `if x: return True else: return False`; unused
imports; entire dead modules (e.g. a `NotificationService` never imported; a `services/` package that
is empty); `type(x) == list` instead of `isinstance`.
**Signals:** grep for `def foo(id)`, `let [a-z] =`, `return True`/`return False` pairs, modules that
no file imports.
**Severity:** LOW.
**Recommendation:** rename, simplify, remove dead code, use a linter (`ruff`/`flake8`, `eslint`).

### L4. Stale Build Artifacts / Repo Hygiene
**What:** committed `__pycache__/`, `*.pyc`, `*.db`, `node_modules/`, or an abandoned `src/` refactor
tree left as bytecode only; no `.gitignore`.
**Signals:** `.pyc` files with no `.py` sibling; `instance/*.db` tracked; `package-lock` fine, but
`node_modules/` tracked is not.
**Severity:** LOW.
**Recommendation:** add a proper `.gitignore`; remove generated artifacts.

---

## Deprecated / Obsolete API detection (ALWAYS run)

Scan for these and report under the matching severity (usually MEDIUM, HIGH if security-relevant).
Always include **what to use instead**. Add "Not applicable" only if genuinely absent.

| Deprecated signal | Replace with |
|---|---|
| `datetime.utcnow()` / `datetime.datetime.utcnow()` (Python ≥ 3.12) | `datetime.now(timezone.utc)` |
| SQLAlchemy `Model.query` / `Query.get(id)` (SQLAlchemy 2.x legacy) | `db.session.get(Model, id)` / `select(Model)` |
| `flask.__version__` / `flask._version` (Flask ≥ 3.2) | `importlib.metadata.version("flask")` |
| `sqlite3.verbose()` in production (Node) | plain `require('sqlite3')` |
| standalone `body-parser` package (Express) | `app.use(express.json())` / `express.urlencoded()` |
| `app.run(debug=True)` hardcoded | env-driven debug, off by default |
| `app.run(host="0.0.0.0")` hardcoded | env-driven host, loopback default |
| `md5`/`sha1` for passwords | `bcrypt`/`argon2` (also a CRITICAL C4) |
| `request.host` / unsafe redirects | validated redirect targets |
| Python `distutils` | `packaging` / `setuptools` |

Report a deprecated-API finding in the same Finding block format with `[DEPRECATED]` in the title.
