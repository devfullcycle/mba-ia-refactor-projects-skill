# Audit Report — ecommerce-api-legacy

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express
Files:   3 analyzed | ~180 lines of code

Summary
CRITICAL: 5 | HIGH: 5 | MEDIUM: 6 | LOW: 4

Findings
```

### [CRITICAL] C1 — God Class / Big Ball of Mud
- **File:** `src/AppManager.js:1-141`
- **Description:** One class owns the DB connection (`:7`), schema + seeds (`:11-22`), all routing (`:25`), the full checkout business workflow (`:28-78`), the financial report (`:80-129`), and a destructive delete (`:131-137`). No models/controllers/services/routes split.
- **Impact:** Untestable, unmaintainable; a change to payments can break routing.
- **Recommendation:** Decompose into `db/`, `models/`, `controllers/`, `services/`, `routes/`, `middlewares/` with a thin `app.js`/`server.js`.

### [CRITICAL] C2 — Hardcoded production secrets (+ committed `.env`)
- **File:** `src/utils.js:1-7` (`dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `smtpUser`), `.env:1-4` (committed, same `pk_live` key)
- **Description:** A *live* payment key and DB/SMTP credentials are literals in source; a `.env` with the same secrets is committed and never even loaded (no `dotenv`).
- **Impact:** Anyone with repo access owns production credentials; rotation requires a code change.
- **Recommendation:** Move every secret to env via a `config/` module; `.gitignore` `.env`; ship `.env.example`.

### [CRITICAL] C3 — Insecure password storage (reversible fake hash + plaintext seed)
- **File:** `src/utils.js:17-23` (`badCrypto`), `src/AppManager.js:18` (seed `'123'` plaintext), `src/AppManager.js:68` (`badCrypto(p)`)
- **Description:** `badCrypto` base64-encodes in a loop and truncates to 10 chars — every password collapses to the same trivial value. The seed user's password is stored in plaintext (`'123'`).
- **Impact:** Effective credential disclosure for every user.
- **Recommendation:** Hash with `bcrypt` (per-user salt) via `utils/hash.js`.

### [CRITICAL] C4 — Sensitive data logged (PAN + gateway key)
- **File:** `src/AppManager.js:45` (`` console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`) ``)
- **Description:** Full card number (PAN) plus the live payment key are written to stdout on every checkout.
- **Impact:** PCI-DSS violation; credentials/PII shipped to any log aggregator.
- **Recommendation:** Redact PAN to last 4; never log secrets.

### [CRITICAL] C5 — No authN/authZ on admin & destructive endpoints
- **File:** `src/AppManager.js:80` (`GET /api/admin/financial-report` returns PII + revenue), `src/AppManager.js:131` (`DELETE /api/users/:id`)
- **Description:** Any anonymous caller reads the financial report (student names + amounts) or deletes arbitrary users. No JWT/session, no middleware.
- **Impact:** Full unauthorized read/write to data.
- **Recommendation:** Add auth middleware + role checks; protect `/api/admin/*`.

### [HIGH] H1 — Business logic, payment & DB writes inside a route handler
- **File:** `src/AppManager.js:28-78`
- **Description:** The checkout route is simultaneously controller + payment gateway + repository + audit logger (`processPaymentAndEnroll`).
- **Impact:** Payment correctness buried in an anonymous nested function; untestable.
- **Recommendation:** Extract a `services/checkoutService.js`; route → controller → service → model.

### [HIGH] H2 — Multi-step writes with no transaction
- **File:** `src/AppManager.js:50-57` (enrollment insert → payment insert → audit insert)
- **Description:** Three dependent inserts with no `BEGIN/COMMIT/ROLLBACK`; if `payments` fails after `enrollments`, the DB is left inconsistent.
- **Impact:** Broken referential integrity; orphaned enrollments without payments.
- **Recommendation:** Wrap the workflow in a transaction.

### [HIGH] H3 — Callback hell / no async-await / tight coupling
- **File:** `src/AppManager.js:37-77` (4–5 nesting levels), `src/AppManager.js:26` (`const self = this`), `src/app.js:8-10` (`new AppManager(); manager.setupRoutes(app)`)
- **Description:** Pyramid of Doom; the Express app is passed *into* the manager, inverting dependency direction; `self = this` workaround.
- **Impact:** Untestable, fragile control flow.
- **Recommendation:** Promisify the DB, use async/await; inject dependencies; thin entry point.

### [HIGH] H4 — Global mutable state shared across requests
- **File:** `src/utils.js:9-15` (`globalCache = {}`, `totalRevenue = 0`, `logAndCache`), `src/AppManager.js:59` (`logAndCache` write)
- **Description:** Module-scope mutable cache mutated on every request; unbounded (memory leak); `totalRevenue` exported but never updated — a latent bug.
- **Impact:** Cross-request leakage, memory growth, concurrency hazards.
- **Recommendation:** Remove module-scope mutation from the request path; use an injected store if caching is needed.

### [HIGH] H5 — Destructive endpoint intentionally orphans related rows
- **File:** `src/AppManager.js:131-137`
- **Description:** `DELETE /api/users/:id` hard-deletes the user and knowingly leaves `enrollments` and `payments` dangling (the response admits it).
- **Impact:** Referential integrity broken; downstream reports show ghost enrollments.
- **Recommendation:** Declare FK `ON DELETE CASCADE` or a transactional cleanup; prefer soft-delete.

### [MEDIUM] M1 — N+1 query
- **File:** `src/AppManager.js:89-125`
- **Description:** For each course, a query for enrollments (`:92`); for each enrollment, a query for the user (`:104`) and the payment (`:106`) — `1 + C + C·E·2` queries.
- **Impact:** Quadratic latency as data grows.
- **Recommendation:** One aggregate query with JOINs; group in JS.

### [MEDIUM] M2 — Missing input validation
- **File:** `src/AppManager.js:35` (`if (!u || !e || !cid || !cc) return 400`), `src/AppManager.js:29-33` (abbreviated fields `usr/eml/pwd/c_id/card`)
- **Description:** Only truthiness is checked — no email format, no card Luhn/length, no type checks; non-idiomatic field names harm clients.
- **Impact:** Bad data accepted; client friction.
- **Recommendation:** Validate with `zod`/`joi`; rename fields to `name/email/courseId/card`.

### [MEDIUM] M3 — Hardcoded business rule
- **File:** `src/AppManager.js:46` (`let status = cc.startsWith("4") ? "PAID" : "DENIED"`)
- **Description:** Payment approval is a hardcoded Visa-prefix check, not a real gateway call.
- **Impact:** Fake payment semantics; change requires a code edit.
- **Recommendation:** Isolate behind a `PaymentService` with configurable rules.

### [MEDIUM] M4 — Code duplication (error/response boilerplate ×8)
- **File:** `src/AppManager.js:38,41,48,51,55,70,84` (repeated `if (err) return res.status(500).send(...)`)
- **Description:** Same fail-handling pattern copy-pasted; no central error handler.
- **Impact:** Inconsistent error responses; maintenance burden.
- **Recommendation:** One Express error-handling middleware + a DB wrapper.

### [MEDIUM] M5 — In-memory DB + unused `data.db`; no security headers
- **File:** `src/AppManager.js:7` (`:memory:`), `.env:1` / `data.db` (28 KB, ignored), `src/app.js` (no `helmet`, no `cors`, no rate-limit)
- **Description:** Data is lost on restart; the committed `data.db` and `DB_PATH` are dead artifacts; no security middleware.
- **Impact:** Can't scale/persist; misleading artifacts; exposed to common attacks.
- **Recommendation:** Use the configured file DB; add `helmet`, CORS policy, rate limiting.

### [MEDIUM] M6 — Errors swallowed (no error middleware, `err` discarded)
- **File:** `src/AppManager.js:104,106,133` (callbacks ignore `err`), no `app.use((err,req,res,next)=>...)`
- **Description:** DB errors are routinely discarded; no central handler; no `process.on('unhandledRejection')`.
- **Impact:** Silent failures; impossible to diagnose.
- **Recommendation:** Add Express error middleware; log and propagate errors.

### [LOW] L1 — `let` used where `const` fits
- **File:** `src/AppManager.js:29-33,81,90`, `src/utils.js:9-10,12,18`
- **Recommendation:** Use `const` for non-reassigned bindings.

### [LOW] L2 — Poor naming
- **File:** `src/AppManager.js:26` (`self`), `:29-33` (`u`, `e`, `p`, `cid`, `cc`), `src/utils.js:17` (`badCrypto`)
- **Recommendation:** Meaningful names; drop the `self` workaround via arrow functions.

### [LOW] L3 — [DEPRECATED] `sqlite3.verbose()` + CommonJS-only + no graceful shutdown
- **File:** `src/AppManager.js:1` (`require('sqlite3').verbose()`), `src/app.js:12-14` (no error/shutdown handler)
- **Description:** `.verbose()` adds noisy trace logging (unsuitable for prod); no ESM; `app.listen` has no `on('error')`/`SIGTERM` handling.
- **Recommendation:** Drop `.verbose()`; add graceful shutdown and error handlers.

### [LOW] L4 — Misleading package name vs. real domain
- **File:** `package.json:2` (`"desafio-arquitetura-ia-boilerplate"`) vs. README ("LMS API")
- **Recommendation:** Rename to reflect the actual LMS domain.

```
================================
Total: 20 findings  (CRITICAL: 5 | HIGH: 5 | MEDIUM: 6 | LOW: 4)

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
================================
```
