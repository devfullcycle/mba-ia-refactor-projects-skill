# Audit Report — code-smells-project

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~780 lines of code

Summary
CRITICAL: 7 | HIGH: 5 | MEDIUM: 4 | LOW: 4

Findings
```

### [CRITICAL] C1 — God File / complete breakdown of separation of concerns
- **File:** `app.py:1-88`, `controllers.py:1-292`, `models.py:1-314`, `database.py:1-86`
- **Description:** Four root-level files each own multiple layers. `app.py` does routing + DB wipe + arbitrary SQL execution + config. `controllers.py` does validation + business rules + notifications. `models.py` does data access + transactions + pricing. `database.py` does connection + DDL + seed data. No service layer, no DI, no app factory.
- **Impact:** Impossible to unit-test; any change has unbounded blast radius; the textbook "Big Ball of Mud".
- **Recommendation:** Split into `config/`, `models/`, `controllers/`, `services/`, `routes/`, `middlewares/` with an app factory composition root.

### [CRITICAL] C2 — SQL Injection (string-concatenated SQL everywhere)
- **File:** `models.py:28, 48-50, 58-60, 68, 92, 110-111, 127-128, 140, 148-150, 155, 157-165, 174, 188, 220, 279-281, 289-297`; `app.py:69`; `controllers.py:268-273`
- **Description:** Every query concatenates untrusted values, e.g. `models.py:28` `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))`; login `models.py:110` `"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`; dynamic search `models.py:289-297` builds `WHERE 1=1` by string append. The seed code (`database.py:70-73`) correctly uses `?` — proving the safe pattern is known and ignored.
- **Impact:** Remote auth bypass (`' OR '1'='1`), data exfiltration, and destruction on every endpoint.
- **Recommendation:** Parameterize every query: `cursor.execute("... WHERE id = ?", (id,))` + a params list for dynamic WHERE.

### [CRITICAL] C3 — Hardcoded SECRET_KEY, also leaked through a public endpoint
- **File:** `app.py:7` (`app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"`), `controllers.py:289` (health check returns it)
- **Description:** The secret is a literal in source, and `GET /health` (unauthenticated) echoes it back: `"secret_key": "minha-chave-super-secreta-123"`. A `.env` exists but is never loaded (no `python-dotenv`).
- **Impact:** Anyone can forge session tokens / CSRF tokens; full secret disclosure to anonymous callers.
- **Recommendation:** Load from env via a config module; add `.env` to `.gitignore`; remove the secret from `/health`.

### [CRITICAL] C4 — Unauthenticated destructive + arbitrary-SQL endpoints
- **File:** `app.py:47-57` (`POST /admin/reset-db` wipes all tables), `app.py:59-78` (`POST /admin/query` runs `cursor.execute(body["sql"])`)
- **Description:** No auth, no allow-list. `/admin/query` executes any SQL sent in the request body (line 69), including `DROP TABLE`. `/admin/reset-db` deletes every row with no confirmation token.
- **Impact:** Trivial full database destruction or exfiltration by any anonymous caller.
- **Recommendation:** Remove arbitrary-SQL execution entirely; require an admin role for destructive ops.

### [CRITICAL] C5 — Plaintext password storage + plaintext SQL login
- **File:** `database.py:75-79` (seed), `models.py:110-111` (login), `models.py:127-128` (registration)
- **Description:** Passwords are stored in cleartext (`("Admin","admin@loja.com","admin123",...)`). Login matches plaintext inside SQL: `WHERE email = '...' AND senha = '...'` — itself injectable.
- **Impact:** Credential disclosure on DB leak; auth bypass via SQL injection.
- **Recommendation:** Hash with bcrypt; fetch user by email then verify the hash in Python (constant-time).

### [CRITICAL] C6 — Password field returned in API responses
- **File:** `models.py:83` (`get_todos_usuarios`), `models.py:99` (`get_usuario_por_id`)
- **Description:** `"senha": row["senha"]` is included in the serialized user object returned to clients.
- **Impact:** Credential disclosure to any caller of `GET /usuarios` / `GET /usuarios/<id>`.
- **Recommendation:** Never serialize the password; drop the field from all responses.

### [CRITICAL] C7 — Debug mode + wildcard binding in the run path
- **File:** `app.py:8` (`app.config["DEBUG"] = True`), `app.py:88` (`app.run(host="0.0.0.0", port=5000, debug=True)`)
- **Description:** The Werkzeug interactive debugger is enabled and bound to all interfaces.
- **Impact:** Remote code execution if the port is reachable.
- **Recommendation:** Drive debug from env, default off; bind to loopback in dev.

### [HIGH] H1 — Business logic embedded in routes/controllers
- **File:** `controllers.py:43-54` (price/stock/name/category rules), `controllers.py:242` (status state machine), `controllers.py:208-210 & 247-250` (notification side-effects)
- **Description:** Pricing rules, category allow-lists, order state machine, and email/SMS/push side-effects all live inside HTTP handlers.
- **Impact:** Rules cannot be unit-tested or reused; controllers are untestable.
- **Recommendation:** Move rules and side-effects to a `services/` layer; controllers only orchestrate.

### [HIGH] H2 — Discount/pricing policy buried in a data-access function
- **File:** `models.py:256-268`
- **Description:** `relatorio_vendas()` hardcodes discount tiers (`>10000 → 10%`, `>5000 → 5%`, `>1000 → 2%`) with magic numbers inside a "model" function that also aggregates SQL.
- **Impact:** Business policy mixed with data access; magic numbers; cannot be configured.
- **Recommendation:** Extract to a `DiscountPolicy` service with named, configurable tiers.

### [HIGH] H3 — Global mutable DB singleton
- **File:** `database.py:4-11`
- **Description:** `db_connection = None` + `global db_connection`, reused across all requests/threads via `sqlite3.connect(..., check_same_thread=False)`.
- **Impact:** Race conditions, cursor-reuse conflicts, unbounded connection lifetime, untestable.
- **Recommendation:** App factory + Flask-SQLAlchemy (request-scoped sessions) or per-request connection via Flask `g`.

### [HIGH] H4 — Missing authentication/authorization on every endpoint
- **File:** `app.py:11-30` (all routes registered with no guard), e.g. `/pedidos/usuario/<int:usuario_id>` at `app.py:25`
- **Description:** Despite a `usuarios.tipo` (`admin`/`cliente`) field, no route checks identity or role. Anyone reads any user's orders, runs the sales report, or mutates data.
- **Impact:** Total access-control failure.
- **Recommendation:** Add auth + role checks; protect admin/order/report routes.

### [HIGH] H5 — Non-atomic order creation + TOCTOU on stock
- **File:** `models.py:133-169`
- **Description:** Stock is validated in a first loop (`models.py:140`) then decremented in a second loop (`models.py:163-165`) with no row locking and a single `db.commit()` at the end; no rollback path on partial failure. Concurrent orders can oversell.
- **Impact:** Oversell / inconsistent state under concurrency.
- **Recommendation:** Wrap in a transaction; re-check/decrement stock atomically.

### [MEDIUM] M1 — N+1 queries
- **File:** `models.py:171-201` (`get_pedidos_usuario`), `models.py:203-233` (`get_todos_pedidos`)
- **Description:** For each order, a query fetches its items (`:188`), and for each item another query fetches the product name (`:192`) — three nested query levels inside loops.
- **Impact:** Latency grows as O(orders × items).
- **Recommendation:** One JOIN across `pedidos`/`itens_pedido`/`produtos`.

### [MEDIUM] M2 — Bare `except Exception` repeated in every handler + error leakage
- **File:** `controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292`; `app.py:77-78`
- **Description:** 17 handlers catch `Exception` and `return jsonify({"erro": str(e)}), 500`, leaking SQL/internals to clients with no logging.
- **Impact:** Information disclosure; root causes hidden.
- **Recommendation:** One global `app.errorhandler`; specific exceptions; log server-side.

### [MEDIUM] M3 — Missing input validation
- **File:** `controllers.py:111-126` (`float(preco_min)` uncaught → 500), `controllers.py:146-165` (no email/password/uniqueness rules), `controllers.py:188-201` (no item shape checks), `controllers.py:237-243` (no pedido-existence/transition check)
- **Description:** Bodies/params are read with no schema; malformed input becomes a 500; no format/strength/uniqueness rules.
- **Impact:** 500s instead of 400s; weak data integrity.
- **Recommendation:** Validate at the edge with a schema (marshmallow); reject early.

### [MEDIUM] M4 — Duplicate / divergent code
- **File:** `models.py:171-201` ≈ `models.py:203-233` (two near-identical order-list functions); `controllers.py:30-54` vs `controllers.py:72-91` (product validation blocks that inconsistently skip length/category checks on update)
- **Description:** Copy-pasted logic that drifts (the update path silently drops name-length and category rules).
- **Impact:** Bugs hide in the divergence; maintenance burden.
- **Recommendation:** Extract one canonical helper; reuse it on both paths.

### [MEDIUM] M5 — [DEPRECATED] Legacy dev-server boot pattern
- **File:** `app.py:80-88`
- **Description:** `if __name__ == "__main__": app.run(host="0.0.0.0", port=5000, debug=True)` is the legacy hardcoded boot. No app factory, no env-driven host/port/debug.
- **Impact:** Couples run config to source; unsafe defaults.
- **Recommendation:** App factory + env-driven config (`FLASK_RUN_HOST`, `FLASK_DEBUG`); rely on `flask run` or a production WSGI server.

### [LOW] L1 — Magic numbers / hardcoded literals
- **File:** `models.py:257-262` (discount tiers `10000/0.1/5000/0.05/1000/0.02`), `app.py:85,88` (port `5000`, host `"0.0.0.0"`), `controllers.py:52,242` (category/status lists duplicated)
- **Recommendation:** Named constants/enums in one module.

### [LOW] L2 — `print()` used as the logger
- **File:** `controllers.py:8,57,106,161,179,182,208-210,219,248,250`; `app.py:56,83-86`
- **Recommendation:** Use Python `logging` with levels/correlation.

### [LOW] L3 — Naming / style / shadowed builtins
- **File:** `controllers.py:14,64,98,136` & `models.py:24,54,65` (param `id` shadows builtin); string concat instead of f-strings (`controllers.py:8`, `models.py:143`)
- **Recommendation:** Rename `id` → `produto_id`/`usuario_id`; use f-strings; add a linter (`ruff`).

### [LOW] L4 — Orphaned build artifacts
- **File:** `src/**/__pycache__/*.pyc` (compiled bytecode from an abandoned prior refactor, no `.py` siblings)
- **Recommendation:** Remove; add a `.gitignore`.

```
================================
Total: 20 findings  (CRITICAL: 7 | HIGH: 5 | MEDIUM: 5 | LOW: 4)

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
================================
```
