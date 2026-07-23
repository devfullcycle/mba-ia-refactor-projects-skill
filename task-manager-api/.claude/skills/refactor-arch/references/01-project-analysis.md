# 01 — Project Analysis Heuristics

Goal of Phase 1: detect **language, framework, database, architecture, and domain** without assuming
anything. Work top-down: manifests → source structure → source contents.

## 1. Detect the language (from manifests first)

| Signal file | Language |
|---|---|
| `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`, `poetry.lock` | Python |
| `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` | JavaScript / Node.js |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `composer.json` | PHP |
| `Gemfile` | Ruby |

Fallback: file extensions of source files (`.py`, `.js`/`.ts`, `.go`, …).
Report the **runtime version** if discoverable (e.g. from `.python-version`, `engines` in package.json,
or `python --version`).

## 2. Detect the framework + exact version

Read the manifest and the `import`/`require` statements.

| Import / dependency | Framework | Notes |
|---|---|---|
| `flask` (`from flask import Flask`) | Flask | check `requirements.txt` pin |
| `fastapi` | FastAPI | |
| `django` | Django | |
| `express` (`require('express')`) | Express | check `package.json` dep version |
| `nestjs` / `@nestjs/core` | NestJS | |
| `koa`, `hapi`, `fastify` | … | |

Report **exact version** from the manifest (e.g. `flask==3.1.1`, `express ^4.18.2`).
If the version is unpinned (`flask` with no version), say so — that is itself a (LOW) finding later.

Also list the **meaningful runtime dependencies**: ORM (`flask-sqlalchemy`, `sequelize`, `prisma`),
DB driver (`sqlite3`, `psycopg2`), validation (`marshmallow`, `joi`, `zod`, `express-validator`),
auth (`flask-jwt-extended`, `jsonwebtoken`, `bcrypt`), CORS, etc.

## 3. Detect the database

- Look for a connection string / URI: `sqlite:///...`, `:memory:`, `postgresql://`, `mysql://`.
- Look for a driver/ORM import: `sqlite3`, `flask_sqlalchemy`, `mongoose`, `pg`, `sequelize`.
- Find the **schema**: DDL (`CREATE TABLE ...`), model classes (`class X(db.Model)`), or migrations.
- **List every table** found, with a 2–4 word purpose. Example: `produtos, usuarios, pedidos, itens_pedido`.
- Note whether tables are created via `CREATE TABLE IF NOT EXISTS`, `db.create_all()`, migrations, or
  schema-as-code in a manager class. Note in-memory vs. file DB.

## 4. Map the current architecture

Inspect the directory tree and how modules import each other.

- **Monolithic / flat:** a handful of root-level files each doing many things
  (e.g. `app.py` + `models.py` + `controllers.py` + `database.py`, all at root). No package folders.
- **Single God file:** one class/file owns DB + schema + routes + business logic
  (e.g. `AppManager.js`, `GodManager.js`). Strong signal of "Big Ball of Mud".
- **Layered (cosmetic or real):** folders like `models/`, `routes/`, `controllers/`, `services/`.
  Check whether they are actually used — if `routes/` imports the DB directly and `services/` is empty
  or never imported, the layering is **fake/partial**. Say so explicitly.

Count the **source files analyzed** (exclude `node_modules`, `__pycache__`, `.venv`, lock files, docs).
Note **layer violations** you can already see (routes → DB direct, circular imports, dead packages).

## 5. Infer the domain

Combine two signals:
- **Route nouns** (the path segments): `/produtos`, `/pedidos`, `/checkout`, `/courses`, `/tasks`.
- **Model / table names**: `produtos`, `enrollments`, `payments`, `tasks`, `users`.

Produce a **one-line domain description**, e.g.:
- `E-commerce API (produtos, pedidos, usuários)`
- `LMS API with checkout flow (courses, enrollments, payments)`
- `Task Manager API (tasks, users, categories)`

If a folder name or README contradicts the real domain (e.g. project called "ecommerce" but it is
actually an LMS), trust the **routes + tables** and note the mismatch.

## 6. File-count rules (so "Source files: N" is accurate)

Count as source files: `.py`, `.js`, `.ts`, `.go`, `.rb`, `.php`, etc. that belong to the app
(including files inside `src/`, `routes/`, `models/`, ...).
Do NOT count: `node_modules/`, `__pycache__/`, `.venv/`, lock files, `*.db`, `*.http`, `README.md`,
manifest files themselves, or compiled artifacts (`.pyc`, `.min.js`).
State the number clearly: `Source files: 4 files analyzed`.

## 7. Output

Feed the detected values into the boxed summary from SKILL.md Phase 1. Do not dump the raw tree —
only the structured summary. Keep it tight; the detail belongs in Phase 2.
