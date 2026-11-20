# Project Analysis Heuristics (Phase 1)

Goal: build an accurate, evidence-based picture of the project **before** judging it. Everything printed in Phase 1 must be traceable to a file you opened.

## 1. Files to analyze

Count only first-party source files. **Ignore:**

- Dependency/vendor folders: `node_modules/`, `vendor/`, `.venv/`, `venv/`, `env/`, `site-packages/`, `__pycache__/`, `dist/`, `build/`, `target/`, `.next/`
- Tooling/metadata: `.git/`, `.claude/`, `.idea/`, `.vscode/`
- Lock files and generated files: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, `*.min.js`, compiled assets
- Data files: `*.db`, `*.sqlite`, `*.log`

Source extensions by ecosystem: `.py`, `.js/.mjs/.cjs/.ts`, `.go`, `.java/.kt`, `.rb`, `.php`, `.cs`. Count manifests (`requirements.txt`, `package.json`) and request collections (`*.http`) separately — they are inputs, not "source files analyzed".

Useful commands:
```bash
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" \) \
  -not -path "*/node_modules/*" -not -path "*/.venv/*" -not -path "*/venv/*" -not -path "*/.claude/*" | sort
wc -l <files>          # LOC per file + total
```

## 2. Language detection

| Signal (strongest first) | Language |
|---|---|
| `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`; majority of `.py` | Python |
| `package.json` + `.js` / `.mjs` / `.cjs` | JavaScript (Node.js) |
| `package.json` + `tsconfig.json` + `.ts` | TypeScript (Node.js) |
| `go.mod` | Go |
| `pom.xml`, `build.gradle(.kts)` | Java / Kotlin |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| `*.csproj` | C# |

Report the runtime constraint when declared (`"engines"` in package.json, `python_requires`, `.python-version`, `.nvmrc`). If none, say "version not pinned".

## 3. Framework detection

Read the manifest dependency list first, then confirm with imports/bootstrapping code.

| Ecosystem | Manifest entry | Confirming code signal |
|---|---|---|
| Python | `flask` | `Flask(__name__)`, `@app.route`, `Blueprint(` |
| Python | `django` | `manage.py`, `settings.py`, `urls.py` |
| Python | `fastapi` | `FastAPI()`, `@app.get` / `APIRouter` |
| Node | `express` | `require('express')` / `import express`, `app.get(`, `express.Router()` |
| Node | `fastify`, `koa`, `@nestjs/core` | `fastify()`, `new Koa()`, `@Controller()` |
| Go | `gin-gonic/gin`, `labstack/echo`, `net/http` | `gin.Default()`, `http.HandleFunc` |
| Java | `spring-boot-starter-web` | `@RestController` |

Version: take it from the manifest. For ranges (`^4.18.2`) report the range **and**, if `node_modules`/`site-packages` exists, the installed version (`npm ls express`, `pip show flask`).

List the remaining runtime dependencies (not dev-only) on the `Dependencies:` line — e.g. `flask-cors`, `flask-sqlalchemy`, `sqlite3`.

## 4. Database detection

| Signal | Engine / access style |
|---|---|
| `import sqlite3`, `sqlite3.connect(` | SQLite, raw driver (Python) |
| `require('sqlite3')`, `new sqlite3.Database(` | SQLite, raw driver (Node, callback API) |
| `':memory:'` | In-memory DB (data lost on restart) |
| `flask_sqlalchemy`, `SQLAlchemy()`, `db.Model` | SQLAlchemy ORM |
| `SQLALCHEMY_DATABASE_URI = 'sqlite:///x.db'` | SQLite via SQLAlchemy (Flask-SQLAlchemy ≥3 puts relative files in `instance/`) |
| `psycopg2`, `pg`, `mysql2`, `pymysql` | PostgreSQL / MySQL raw driver |
| `sequelize`, `typeorm`, `prisma`, `mongoose`, `knex` | ORM / query builder |

**Tables:** collect from `CREATE TABLE` statements, `__tablename__`, `class X(db.Model)`, ORM entity decorators, or migrations. Also note seed data (it tells you the domain and gives credentials useful for validation).

## 5. Domain inference

Combine three sources and summarize in one line with the main entities:
1. Table / model names (`produtos, pedidos, usuarios` → e-commerce; `courses, enrollments, payments` → LMS with checkout; `tasks, categories, users` → task manager).
2. Route nouns (`/checkout`, `/relatorios/vendas`, `/tasks/stats`).
3. Seed data and README.

Use the project's own vocabulary (keep Portuguese entity names if the code uses them).

## 6. Architecture classification

| Classification | Signals |
|---|---|
| **Monolithic (no layers)** | Routing, SQL and business rules in the same file/class; a "manager"/"utils" file that owns DB + routes; ≤ 5 source files with no folders by responsibility |
| **Pseudo-layered** | Files *named* `models.py` / `controllers.py` exist, but responsibilities leak: models contain business rules and validation, controllers import the DB directly, entry point holds routes with SQL |
| **Partially layered** | Folders by responsibility (`models/`, `routes/`, `services/`, `utils/`) exist, but routes still hold business logic / queries, no centralized error handling, config hardcoded, services unused or with infra secrets |
| **Layered (MVC-compliant)** | Matches `mvc-guidelines.md`: thin routes, controllers own flow, models own data, config module, error middleware, composition root |

Write one line justifying the classification with concrete evidence, e.g. `Monolithic — AppManager.js owns DB init, 3 routes and payment logic`.

## 7. Map current responsibilities

For each source file, note which responsibilities it holds today — this drives the Phase 3 plan:

| Responsibility | Typical location in a healthy MVC app |
|---|---|
| Configuration / secrets | `config/` |
| DB connection & schema | `models/` (or `database/`) |
| Data access (queries) | `models/` (repositories) |
| Business rules | `controllers/` (or `services/` for cross-entity domain rules) |
| HTTP routing, request parsing, response formatting | `views/` / `routes/` |
| Error handling | `middlewares/` |
| Integrations (email, payment, cache) | `services/` (infrastructure adapters) |
| Bootstrapping | entry point / app factory |

## 8. Endpoint inventory

Grep patterns:

| Stack | Pattern |
|---|---|
| Flask | `grep -nE "@(app|[a-z_]+_bp|bp)\.route\(|add_url_rule\(" -r .` and `methods=[...]` (default method = GET) |
| Flask Blueprint prefix | `Blueprint(..., url_prefix=...)` and `register_blueprint(..., url_prefix=...)` |
| Express | `grep -nE "(app|router)\.(get|post|put|patch|delete)\(" -r src` plus `app.use('/prefix', router)` |
| FastAPI | `@(app|router)\.(get|post|put|patch|delete)\(` |
| Django | `path(` / `re_path(` in `urls.py` |

Record `METHOD PATH -> file:line`. Also record framework defaults that are part of the contract (e.g., 404 for unknown routes).

## 9. Run command and port

- Python: README instructions, `if __name__ == "__main__": app.run(port=...)`, `flask run`, `Procfile`.
- Node: `package.json` `"scripts.start"`, `app.listen(port)`.
- Note prerequisite steps (e.g., `python seed.py`, `npm install`) and environment variables already read via `os.environ` / `process.env`.

## 10. Phase 1 quality checklist

- [ ] Language matches manifest and file extensions
- [ ] Framework + version taken from manifest (and installed version if available)
- [ ] Domain described with real entity names
- [ ] File count equals the list you actually analyzed (state the number)
- [ ] Every route in the code appears in the inventory
