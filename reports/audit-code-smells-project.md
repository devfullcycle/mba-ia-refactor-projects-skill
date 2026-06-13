# Architecture Audit Report

## Project

- **Name:** code-smells-project
- **Path:** `C:\Users\marcio\.codex\worktrees\0229\mba-ia-refactor-projects-skill\code-smells-project`
- **Stack:** Python 3.x, Flask 3.1.1, flask-cors 5.0.1, SQLite
- **Domain:** E-commerce API for products, users, orders, and sales reports
- **Architecture:** Monolithic Flask API with coupled controller and persistence responsibilities
- **Interfaces/contracts:** HTTP API for `/produtos`, `/usuarios`, `/login`, `/pedidos`, `/relatorios/vendas`, `/health`, plus admin maintenance endpoints `/admin/reset-db` and `/admin/query`
- **Source files analyzed:** 4 Python source files (`app.py`, `controllers.py`, `database.py`, `models.py`)
- **Generated at:** 2026-06-13T13:50:58.3968391-03:00

## Summary

| Severity | Count |
|---|---:|
| CRITICAL | 5 |
| HIGH | 1 |
| MEDIUM | 1 |
| LOW | 0 |
| **Total** | **7** |

## Findings

### [CRITICAL] Hardcoded Flask secret and leaked runtime secret

- **Location:** `app.py:7-8`
- **Category:** Exposed Secrets Or Sensitive Data
- **Evidence:** The Flask `SECRET_KEY` is hardcoded in source and debug mode is enabled. The health endpoint also echoes the same secret key and debug flag back to clients in `controllers.py:276-289`.
- **Impact:** Any deployment using Flask sessions inherits a forgeable secret, and the health endpoint leaks internal configuration to unauthenticated callers.
- **Recommendation:** Read secrets from environment variables, rotate the secret, disable debug outside local development, and remove secret/debug fields from API responses.

### [CRITICAL] Unauthenticated arbitrary SQL execution

- **Location:** `app.py:59-78`
- **Category:** Arbitrary Command Or Query Execution
- **Evidence:** The `/admin/query` handler reads `sql` from the request body and passes it directly to `cursor.execute(query)` with no authentication, allowlist, or parameterization. SELECT queries return raw rows, and non-SELECT queries are committed.
- **Impact:** Any caller can read or modify database state and execute destructive SQL against the SQLite backend.
- **Recommendation:** Remove the endpoint or replace it with explicit admin-only operations backed by parameterized repository methods.

### [CRITICAL] String-built SQL injection throughout the persistence layer

- **Location:** `models.py:24-29`
- **Category:** Injection Through String-Built Queries
- **Evidence:** This module concatenates untrusted values directly into SQL text for product lookup, creation, update, deletion, login, order creation, status updates, and search, for example at `models.py:47-60`, `models.py:109-110`, `models.py:126-129`, `models.py:279-299`.
- **Impact:** User-controlled fields such as IDs, names, emails, search terms, and categories can alter query semantics, leading to unauthorized reads, data corruption, or deletion.
- **Recommendation:** Replace string concatenation with parameterized queries everywhere and centralize persistence behind repository functions.

### [CRITICAL] Plaintext password storage and disclosure

- **Location:** `models.py:72-103`
- **Category:** Broken Authentication Or Password Storage
- **Evidence:** Seed data in `database.py:75-83` stores passwords in plaintext, `get_todos_usuarios` and `get_usuario_por_id` return `senha` to callers, and `login_usuario` compares raw email/password strings at `models.py:105-120`.
- **Impact:** API users or database readers can recover credentials directly, and password reuse can compromise accounts outside this system.
- **Recommendation:** Hash passwords with Argon2, bcrypt, scrypt, or PBKDF2; never return `senha` in responses; and migrate existing rows to hashed values.

### [CRITICAL] Unauthenticated destructive reset endpoint

- **Location:** `app.py:47-57`
- **Category:** Contract Or Invariant Violation
- **Evidence:** Any POST request to `/admin/reset-db` deletes every row from `itens_pedido`, `pedidos`, `produtos`, and `usuarios` without authorization, confirmation, or audit logging.
- **Impact:** A single request can wipe the entire business dataset, causing immediate data loss.
- **Recommendation:** Remove this route from production or protect it behind explicit admin authorization and an operationally safe reset workflow.

### [HIGH] Shared global SQLite connection across requests

- **Location:** `database.py:4-11`
- **Category:** Global Mutable State Or Shared Connection
- **Evidence:** The module stores one global `db_connection` and opens it with `check_same_thread=False`, then reuses the same connection for all requests with no teardown or locking.
- **Impact:** Concurrent requests can share connection state unexpectedly, causing intermittent SQLite errors, lock contention, and difficult-to-debug cross-request interference.
- **Recommendation:** Create request-scoped connections with explicit Flask teardown lifecycle management or introduce a repository layer that owns connection creation and disposal.

### [MEDIUM] N+1 query pattern in order serialization

- **Location:** `models.py:171-201`
- **Category:** N+1 Query Pattern
- **Evidence:** `get_pedidos_usuario` fetches orders and then performs additional queries for each order and each line item; `get_todos_pedidos` repeats the same pattern at `models.py:203-233`.
- **Impact:** Response cost grows with the number of orders and items, making list endpoints progressively slower as the dataset grows.
- **Recommendation:** Replace per-row lookups with joins or batch queries and serialize from preloaded result sets.

## Deprecated API Review

- **Checked:** `requirements.txt`, `app.py`, `controllers.py`, `models.py`, `database.py`, Flask 3.1.1 usage, and the sqlite3 access pattern.
- **Findings:** No verifiable deprecated API usage found.
- **Notes:** `check_same_thread=False` is a concurrency-risk configuration, not a deprecation.

## Discovery Coverage

| Area | Evidence inspected | Result |
|---|---|---|
| Observable contracts | `README.md`, Flask routes in `app.py`, handlers in `controllers.py` | Verified HTTP API for products, users, login, orders, reports, health, and admin maintenance endpoints |
| MVC responsibilities | Route registration in `app.py`, input/response logic in `controllers.py`, data access in `models.py`, persistence bootstrap in `database.py` | Coupled and monolithic; controllers contain validation, orchestration, and side effects |
| Correctness/data integrity | Create/update/login/order flows, reset endpoint, persistence methods | Critical findings on injection, plaintext credentials, and destructive reset; no transaction or rollback discipline |
| Security/privacy | Secret handling, admin routes, user serialization, login flow | Critical findings on exposed secrets, arbitrary SQL execution, password exposure, and unauthenticated destructive operations |
| Reliability/concurrency/performance | Global DB connection, order listing loops, broad exception handling | High shared-connection risk and medium N+1 query overhead verified |
| Technology-specific risks | Flask 3.1.1, sqlite3, `check_same_thread=False`, debug mode, CORS on all routes | No deprecated API issue verified; development-style configuration is unsafe for production |

## Proposed Refactoring

| Priority | Finding | Proposed transformation | Validation |
|---:|---|---|---|
| 1 | Hardcoded Flask secret and leaked runtime secret | Move config to typed environment-backed settings, rotate the secret, and redact sensitive health output | Boot the app and verify `/health` no longer exposes secret/debug fields |
| 2 | Unauthenticated arbitrary SQL execution | Remove the query executor or replace it with explicit admin-only maintenance operations | Add negative tests for arbitrary SQL payloads and smoke-test admin paths |
| 3 | String-built SQL injection throughout the persistence layer | Introduce parameterized repositories and extract persistence logic out of handlers | Add regression tests for quoted input and malicious payloads |
| 4 | Plaintext password storage and disclosure | Hash passwords, remove `senha` from serializers, and migrate seeded rows | Test login with hashed credentials and verify user listing omits passwords |
| 5 | Unauthenticated destructive reset endpoint | Gate or remove the endpoint and move destructive maintenance to a protected workflow | Verify unauthorized callers cannot reset data and that reset is only available through approved tooling |
| 6 | Shared global SQLite connection across requests | Replace the module-global connection with request-scoped lifecycle management | Run concurrent request smoke checks and confirm clean connection handling |
| 7 | N+1 query pattern in order serialization | Rewrite order reads with joins or batched lookups inside a repository | Measure query count on list endpoints and confirm it stays bounded |

## Phase 3 Approval

No source, configuration, dependency, generated artifact, or state/persistence files were modified during Phases 1 and 2.

Status: **AWAITING EXPLICIT APPROVAL**

## Phase 3 Results

### Changes Applied

- Moved application configuration into `config.py` with environment-backed secrets and test overrides, and removed hardcoded secret/debug exposure from runtime responses.
- Replaced the shared global SQLite connection with request-scoped connections in `database.py`, plus explicit bootstrap open/commit/close handling.
- Rewrote `models.py` as a parameterized persistence layer, including order reads with joins instead of per-row lookups and transaction-safe order creation.
- Added `security.py` for PBKDF2 password hashing and admin-token checks, then migrated seeded and legacy plaintext passwords on startup.
- Extracted business rules into `services.py` and reduced `controllers.py` to request coordination and response selection.
- Secured `/admin/reset-db` and `/admin/query` behind an admin token, and limited the query endpoint to read-only `SELECT` statements.
- Added regression tests for health output, password disclosure, admin authorization, SQL-safe input handling, and order atomicity.

### Validation

| Check | Command/request | Result |
|---|---|---|
| Syntax/import | `python -m py_compile app.py controllers.py database.py models.py config.py errors.py security.py services.py tests/test_app.py` | PASS |
| Tests | `python -m unittest discover -s tests -v` | PASS |
| Boot | `create_app(...)` exercised inside `tests/test_app.py` and initialized the SQLite schema/seed data successfully | PASS |
| Contract smoke tests | `GET /health`, `GET /usuarios`, `POST /login`, `POST /admin/reset-db`, `POST /admin/query`, `POST /produtos`, `GET /produtos/busca`, `POST /pedidos` via Flask test client | PASS |