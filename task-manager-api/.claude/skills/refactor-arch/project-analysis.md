# Project Analysis — Detection Heuristics

This document provides heuristics for Phase 1 (Project Analysis) to detect the technology stack, map the architecture, and generate the analysis summary.

---

## 1. Language Detection

Detect the primary programming language by examining file extensions and configuration files.

| Signal | Language |
|--------|----------|
| `*.py` files + `requirements.txt` or `setup.py` or `pyproject.toml` | Python |
| `*.js` files + `package.json` | JavaScript (Node.js) |
| `*.ts` files + `tsconfig.json` | TypeScript |
| `*.rb` files + `Gemfile` | Ruby |
| `*.java` files + `pom.xml` or `build.gradle` | Java |
| `*.go` files + `go.mod` | Go |
| `*.php` files + `composer.json` | PHP |

---

## 2. Framework Detection

### Python Frameworks

| Signal | Framework |
|--------|-----------|
| `from flask import` or `Flask(__name__)` | Flask |
| `from django` or `django.setup()` | Django |
| `from fastapi import` or `FastAPI()` | FastAPI |
| `from bottle import` | Bottle |

Check `requirements.txt` or `pyproject.toml` for exact version numbers.

### Node.js Frameworks

| Signal | Framework |
|--------|-----------|
| `require('express')` or `import express` | Express.js |
| `require('koa')` or `import Koa` | Koa |
| `require('fastify')` or `import fastify` | Fastify |
| `require('hapi')` or `import hapi` | Hapi |
| `require('nestjs')` or `@nestjs/` | NestJS |

Check `package.json` `dependencies` for exact version numbers.

---

## 3. Database Detection

| Signal | Database |
|--------|----------|
| `import sqlite3` or `require('sqlite3')` or `better-sqlite3` | SQLite |
| `CREATE TABLE` statements in code | Embedded SQL (usually SQLite) |
| `psycopg2` or `pg` or `postgres` in dependencies | PostgreSQL |
| `pymysql` or `mysql2` or `mysql` in dependencies | MySQL |
| `pymongo` or `mongoose` in dependencies | MongoDB |
| `SQLAlchemy` in imports | SQLAlchemy ORM (check DB URI for actual engine) |
| `sequelize` in dependencies | Sequelize ORM |
| `typeorm` in dependencies | TypeORM |

### Schema Extraction

- Look for `CREATE TABLE` statements to extract table names and columns
- Look for ORM model class definitions (e.g., `db.Model`, `Model.extend`)
- Document column names, types, primary keys, foreign keys, and constraints

---

## 4. Dependency Analysis

### Python
- Read `requirements.txt` — list all packages and versions
- Check for pinned vs unpinned versions
- Key packages to note: web framework, ORM, authentication, CORS, validation

### Node.js
- Read `package.json` `dependencies` and `devDependencies`
- Check for version ranges (^ ~ exact)
- Key packages to note: web framework, database driver, middleware, auth

---

## 5. Architecture Classification

Classify the current architecture based on these signals:

### Monolithic (no separation)
- All logic in 1-4 files
- Routes, business logic, and database access in the same functions
- No directory structure for different concerns
- Global state shared across modules

### Partial Separation
- Some attempt at separating concerns (e.g., routes in separate files)
- But business logic still mixed with data access
- Models exist but contain business logic
- Some but not all concerns are separated

### Layered / MVC
- Clear separation into models, views/routes, controllers
- Business logic in dedicated service/controller layer
- Data access abstracted in model layer
- Configuration extracted to dedicated module

---

## 6. Domain Identification

Identify the application domain by analyzing:
- Route paths (e.g., `/produtos`, `/users`, `/tasks`, `/courses`)
- Database table names
- Variable and function naming patterns
- README or documentation

Common domains:
- **E-commerce**: products, orders, carts, payments, users
- **Task Manager**: tasks, projects, categories, users, assignments
- **LMS (Learning Management)**: courses, enrollments, students, payments
- **Blog/CMS**: posts, categories, comments, users, tags
- **Social Network**: profiles, posts, followers, messages

---

## 7. File Analysis

For each source file, collect:
- File path (relative to project root)
- Line count
- Primary responsibility (routes, models, config, utils, etc.)
- Key functions/classes defined
- Imports and dependencies on other project files

Count total source files (exclude `node_modules/`, `__pycache__/`, `.git/`, lock files, etc.).
