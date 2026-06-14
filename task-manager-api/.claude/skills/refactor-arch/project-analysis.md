# Project Analysis — Heuristics Guide

Use this guide to detect the stack, architecture, and domain of any project during Phase 1.

---

## 1. Language Detection

### Python
- Files: `*.py`, `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`
- Indicators: `import flask`, `from django`, `def `, `self.`, `if __name__ == '__main__'`
- Versions: Check `python_requires` in `setup.py`, or `python -V`

### JavaScript / Node.js
- Files: `*.js`, `*.mjs`, `package.json`, `package-lock.json`, `.nvmrc`
- Indicators: `require(`, `const express`, `module.exports`, `async/await`, `callback(err, result)`
- Versions: Check `engines.node` in `package.json`

### TypeScript
- Files: `*.ts`, `*.tsx`, `tsconfig.json`
- Indicators: `: string`, `interface `, `<T>`, `import type`

---

## 2. Framework Detection

### Python Frameworks

| Framework | Detection Signal | Files |
|---|---|---|
| Flask | `from flask import Flask`, `@app.route` | `app.py`, `wsgi.py` |
| Django | `from django.db import models`, `urls.py`, `settings.py` | `manage.py`, `settings.py` |
| FastAPI | `from fastapi import FastAPI`, `@app.get`, `async def` | `main.py` |

**Flask version:** Check `requirements.txt` for `Flask==X.Y.Z`

### Node.js Frameworks

| Framework | Detection Signal | Files |
|---|---|---|
| Express | `require('express')`, `app.get(`, `app.use(` | `app.js`, `server.js`, `index.js` |
| Fastify | `require('fastify')`, `fastify.get(` | `app.js` |
| NestJS | `@Module`, `@Injectable`, `@Controller` | `*.module.ts`, `*.controller.ts` |
| Koa | `require('koa')`, `ctx.body =` | `app.js` |

---

## 3. Database Detection

### Python
| Database | Indicator |
|---|---|
| SQLite | `import sqlite3`, `sqlite3.connect(`, `.db` file extension |
| PostgreSQL | `psycopg2`, `DATABASE_URL=postgresql://`, `pg.connect(` |
| MySQL | `pymysql`, `mysql-connector`, `DATABASE_URL=mysql://` |
| SQLAlchemy ORM | `from sqlalchemy`, `db.Model`, `Column(`, `relationship(` |
| MongoDB | `pymongo`, `MongoClient(` |

### Node.js
| Database | Indicator |
|---|---|
| SQLite | `require('better-sqlite3')`, `require('sqlite3')`, `.db` file |
| PostgreSQL | `require('pg')`, `Pool(`, `Client(` |
| MySQL | `require('mysql2')`, `require('mysql')` |
| Mongoose/MongoDB | `require('mongoose')`, `Schema(`, `.connect('mongodb://` |
| Sequelize ORM | `require('sequelize')`, `Model.define(` |
| Prisma ORM | `require('@prisma/client')`, `prisma.` |

---

## 4. Architecture Pattern Recognition

### Monolithic (Single-file or few-file)
**Signs:**
- 1-3 Python/JS files containing everything
- Routes, business logic, DB queries, and models in the same file
- `app.py` or `app.js` doing everything
- No subdirectories except for static files

**Example indicators:**
```
project/
├── app.py        ← all routes + logic + DB
├── models.py     ← models + business logic + queries
└── database.py   ← DB connection
```

### MVC Partial
**Signs:**
- Has separate files for models, routes, or controllers
- But layers still bleed into each other (business logic in routes, DB in controllers)
- May have `models/`, `routes/`, `controllers/` but responsibilities mixed

### Layered (Services + Repository)
**Signs:**
- Has `services/`, `repositories/`, `utils/`
- Separation of concerns attempted but not complete
- May have DI-like patterns but still issues

### Flat/Spaghetti
**Signs:**
- No directory structure
- Random file names
- Global variables everywhere

---

## 5. Domain Identification

Map the application domain from:
1. **Route paths**: `/api/products`, `/api/tasks`, `/api/users`, `/api/courses`
2. **Table names**: `produtos`, `tasks`, `users`, `courses`, `enrollments`
3. **Model names**: Product, Task, User, Course, Order
4. **README or comments** if present

Common domains:
- **E-commerce**: products, orders, users, cart, payments
- **Task Manager**: tasks, users, categories, priorities, due dates
- **LMS**: courses, users, enrollments, payments, lessons
- **Blog**: posts, comments, authors, tags

---

## 6. Source File Enumeration

**Files to include:**
- `*.py` (Python source files)
- `*.js`, `*.mjs`, `*.ts` (JavaScript/TypeScript)
- `*.json` (package.json, config files)
- `requirements.txt`, `Pipfile`, `pyproject.toml`

**Files to exclude:**
- `node_modules/` — too many files, not project code
- `venv/`, `.venv/`, `env/` — virtual environment
- `__pycache__/`, `*.pyc` — compiled Python
- `.git/` — version control
- `dist/`, `build/` — compiled output
- `*.min.js` — minified files

**Count command hints:**
```bash
# Python
find . -name "*.py" -not -path "*/venv/*" -not -path "*/__pycache__/*"

# Node.js
find . -name "*.js" -not -path "*/node_modules/*"
```

---

## 7. Deprecated API Detection

### Python/Flask
| Deprecated | Modern Equivalent |
|---|---|
| `@app.before_first_request` | Use `with app.app_context():` on startup |
| `flask.ext.*` imports | Direct package imports |
| `flask.json.provider` old API | `flask.json` new API |
| `flask.Markup` | `markupsafe.Markup` |

### Node.js/Express
| Deprecated | Modern Equivalent |
|---|---|
| `app.configure()` | Direct `app.use()` calls |
| `express.bodyParser()` | `express.json()` and `express.urlencoded()` |
| Callback-based SQLite | Promise-based or async/await wrappers |
| `req.param()` | `req.params`, `req.query`, `req.body` |
| `res.send(404)` | `res.status(404).send()` |
| `var` declarations | `const`/`let` |
| Callback hell | `async/await` |

### Security Libraries
| Outdated/Missing | Modern Equivalent |
|---|---|
| Plain text passwords | `bcrypt`, `argon2` |
| MD5 for passwords | `bcrypt`, `argon2` |
| SHA1 for passwords | `bcrypt`, `argon2` |
| Hardcoded secrets | Environment variables + `python-dotenv`/`dotenv` |
| No input validation | `marshmallow`, `pydantic`, `joi`, `zod` |
