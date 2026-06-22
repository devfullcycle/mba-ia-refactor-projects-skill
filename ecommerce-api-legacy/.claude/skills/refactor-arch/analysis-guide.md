# Analysis Guide — /refactor-arch

This guide provides the heuristics for Phase 1: detecting language, framework, database, domain, and current architecture of any project.

---

## Step 1 — Detect Language

Read all files in the project directory. Determine language based on file extensions:

| Extension | Language |
|---|---|
| `.py` | Python |
| `.js`, `.mjs`, `.cjs` | JavaScript / Node.js |
| `.ts` | TypeScript |
| `.java` | Java |
| `.go` | Go |
| `.rb` | Ruby |
| `.php` | PHP |

If a project has both `.js` and `.ts`, report **TypeScript** (TS projects always transpile from `.ts`).

---

## Step 2 — Detect Framework

### Python
- Read `requirements.txt`, `pyproject.toml`, or `Pipfile`
- `flask` → **Flask**
- `django` → **Django**
- `fastapi` → **FastAPI**
- Verify version: `flask==3.1.1` → Flask 3.1.1
- Also check import statements: `from flask import Flask`, `import django`

### Node.js
- Read `package.json` → `dependencies` section
- `express` → **Express**
- `fastify` → **Fastify**
- `koa` → **Koa**
- `@nestjs/core` → **NestJS**
- Verify version from `package.json`

---

## Step 3 — Detect Database

### Signals
- File extensions: `.db`, `.sqlite`, `.sqlite3` present in the directory → **SQLite** (file-based)
- Import/require: `import sqlite3`, `require('better-sqlite3')`, `require('sqlite3')` → **SQLite**
- `DATABASE_URL` in env: `postgres://...` → **PostgreSQL**, `mysql://...` → **MySQL**
- `pymongo`, `mongoose` → **MongoDB**
- `:memory:` in database connection → **SQLite in-memory**
- `psycopg2`, `asyncpg` → **PostgreSQL**

### Extract DB tables
Look for `CREATE TABLE` statements in any `.py`, `.js`, or `.sql` file. List all table names found.

---

## Step 4 — Detect Domain

Read function names, route paths, table names, and variable names to infer what the application does:

| Indicators | Domain |
|---|---|
| Routes: `/produtos`, `/pedidos`, `/usuarios`; Tables: `produtos`, `pedidos` | **E-commerce API** |
| Routes: `/tasks`, `/categories`; Tables: `tasks`, `tags` | **Task Manager API** |
| Routes: `/courses`, `/enrollments`, `/checkout`; Tables: `users`, `courses` | **LMS (Learning Management System)** |
| Routes: `/auth`, `/users`, `/roles` | **Auth / User Management API** |
| Routes: `/posts`, `/comments` | **Blog / CMS API** |

---

## Step 5 — Detect Current Architecture

Analyze the project's file structure and classify:

### Architecture Patterns

**Monolith — All in One File**
- Signal: Only 1-2 source files (`app.py`, `app.js`) containing all routes, DB queries, and business logic
- Example: Single `app.py` with `@app.route` AND `cursor.execute()` in the same file

**Flat Files — No Layer Separation**
- Signal: Multiple files but with no clear MVC structure (e.g., `app.py`, `controllers.py`, `models.py`, `database.py` — flat, no subdirectories)
- All concerns are at the same level, files are not organized by architectural layer or domain

**Partial MVC — Some Separation**
- Signal: Directories like `models/`, `routes/`, `services/`, `utils/` exist BUT:
  - Models still do business logic
  - Routes contain DB queries
  - No consistent pattern across all modules
- Example: `task-manager-api/` with `models/`, `routes/`, `services/` but still has code smells

**Full MVC — Well Structured**
- Signal: Clean `models/`, `views/` (or `routes/`), `controllers/` directories, config extracted, no direct DB calls in controllers

---

## Step 6 — Count Source Files

Count all source files analyzed (only code files, not config/data files):
- Python: count `.py` files (exclude `__pycache__`, `.pyc`, migrations)
- Node.js: count `.js` and `.ts` files (exclude `node_modules/`, `dist/`, `build/`)

---

## Summary Format Reference

After completing Steps 1–6, print this block:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Database:      SQLite (file: loja.db)
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Flat Files — 4 files, no MVC separation, all concerns mixed
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

---

## Technology-Specific Notes

### Flask Projects
- Entry point is typically `app.py`
- Look for `app = Flask(__name__)` to confirm
- Routes defined with `@app.route(...)` or `app.add_url_rule(...)`
- Check for `flask_cors`, `flask_jwt_extended` in requirements
- DB init often in a `database.py` file

### Express Projects
- Entry point is typically `app.js`, `server.js`, or `index.js`
- Look for `const app = express()` or `const express = require('express')`
- Routes defined with `app.get(...)`, `app.post(...)`, or `router.get(...)`
- Check `package.json` for `start` script
- DB init often inline in the main file or a `database.js`/`db.js` file

### Django Projects
- Entry point is `manage.py`
- `settings.py` configures the app
- Models defined in `models.py` within each app directory
- URLs defined in `urls.py`

### NestJS Projects
- Entry point is `main.ts`
- Controllers decorated with `@Controller`
- Services decorated with `@Injectable`
- Modules decorated with `@Module`
