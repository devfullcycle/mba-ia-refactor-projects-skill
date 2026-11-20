# MVC Architecture Guidelines (target of Phase 3)

The target is a **layered MVC** backend. For JSON APIs the "View" is the HTTP presentation layer (routes + response formatting); there are no HTML templates unless the project already renders them (then templates also live in `views/`).

## 1. Layers and responsibilities

| Layer | Folder | Owns | Must NOT |
|---|---|---|---|
| **Config** | `config/` | Reading environment variables, defaults for dev, typed settings object | Contain secrets as literals (only safe dev defaults such as a SQLite path or port) |
| **Model** | `models/` | Entities, DB schema, connection lifecycle, **repositories** (all queries, parameterized), transactions, simple entity invariants (e.g. `task.is_overdue()`) | Import the web framework, read `request`, format HTTP responses, call controllers |
| **Controller** | `controllers/` | Application flow for each use case: validate input (via validators), apply business rules, coordinate models and services, raise domain errors | Import `request`/`res`/`jsonify`/`express`; execute SQL directly; know status codes |
| **View / Routes** | `views/` (Python) or `routes/` + `views/` (Node: routes in `routes/`, serializers in `views/`) | Route table (method + path), parsing path/query/body, calling one controller method, choosing status code, serializing to the response envelope | Contain business rules or queries; catch-all try/except (errors go to the middleware) |
| **Services (infra)** | `services/` | Adapters to the outside world: email/SMS/push, payment gateway, cache, clock | Contain business rules of the domain; hardcode credentials |
| **Middlewares** | `middlewares/` | Centralized error handler, authentication/authorization guards, request logging | Business rules |
| **Composition root** | `app.py` / `app.js` (`create_app()` / `createApp()`) | Build config → DB → repositories → services → controllers → routes; register middlewares; expose the app | Business logic |

### Dependency rule (arrows = "may import/call")

```
views/routes ──► controllers ──► models (repositories)
                       │
                       └──────► services (infra adapters)
middlewares ──► (domain error classes)
composition root ──► everything (wiring only)
config ◄── read only by the composition root (values are injected)
```

Forbidden: `models → controllers/views`, `controllers → web framework`, `views → models` (except importing types/serializers), circular imports.

## 2. Domain errors and the error contract

- Define a small hierarchy in `controllers/errors.(py|js)` or `middlewares/errors`: `AppError(status_code)`, `ValidationError (400)`, `UnauthorizedError (401)`, `ForbiddenError (403)`, `NotFoundError (404)`, `ConflictError (409)`.
- Controllers **raise/throw** these; the error middleware converts them to the response.
- **Keep the project's existing error envelope** (e.g. `{"erro": "...", "sucesso": false}` or `{"error": "..."}` or plain text) so clients do not break. Pick the envelope already used by most endpoints and apply it uniformly.
- Unknown exceptions → log the stack trace server-side, respond 500 with a generic message (never `str(e)`).
- Unknown routes keep the framework's 404 status.

## 3. Configuration rules

- All secrets and environment-dependent values come from environment variables: secret keys, DB URL/path, API keys, SMTP credentials, debug flag, port, CORS origins.
- `debug` defaults to **False**.
- Secret keys: if the variable is missing in development, generate a random value at startup (`secrets.token_hex(32)` / `crypto.randomBytes(32)`) and log a warning — never ship a literal.
- Provide `.env.example` listing every variable (no real values).
- Load `.env` only if the project already depends on a dotenv library; otherwise read `os.environ` / `process.env` directly (no new dependency).

## 4. Target trees

### Python / Flask

```
<project>/
├── app.py                         # Entry point: create_app() + app.run(); keeps `python app.py` working
├── src/
│   ├── __init__.py
│   ├── app.py                     # create_app(): composition root
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py            # connection lifecycle (per request / per app), schema, seed
│   │   ├── <entity>_model.py      # one repository/entity module per aggregate
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── errors.py
│   │   ├── validators.py          # input validation helpers (or per-entity validators)
│   │   └── <entity>_controller.py
│   ├── views/
│   │   ├── __init__.py
│   │   └── <entity>_routes.py     # Blueprints
│   ├── services/                  # only if integrations exist
│   │   └── notification_service.py
│   └── middlewares/
│       ├── __init__.py
│       ├── error_handler.py
│       └── auth.py                # only if admin/auth endpoints exist
└── requirements.txt
```

ORM projects (Flask-SQLAlchemy): `models/` keeps the `db.Model` classes and gets repository helpers or class methods for queries; `database.py` exports the `db` instance. Keep the entry point exports used by other scripts (e.g., `seed.py` doing `from app import app, db`).

### Node.js / Express

```
<project>/
├── package.json                   # "start" keeps working (e.g. node src/app.js)
└── src/
    ├── app.js                     # Entry point: createApp() + listen
    ├── config/index.js
    ├── models/
    │   ├── database.js            # connection + promisified helpers + schema/seed
    │   └── <entity>Model.js       # repositories (parameterized queries)
    ├── controllers/
    │   ├── errors.js
    │   └── <useCase>Controller.js
    ├── routes/                    # Express Routers (the "View/route" layer)
    │   └── <area>Routes.js
    ├── views/                     # response serializers/presenters (optional when trivial)
    ├── services/                  # payment gateway, cache, crypto adapters
    └── middlewares/
        ├── errorHandler.js
        └── asyncHandler.js        # wraps async route handlers so rejections reach errorHandler
```

### Any other stack

Apply the same folders and dependency rule using the stack's idioms (Go: `internal/{config,models,controllers,handlers,middleware}`; Spring: `config`, `model`/`repository`, `service` (= controller role), `controller` (= view/route role), `exception/GlobalExceptionHandler`). Keep the language's naming conventions.

## 5. Adapting to the starting point

| Starting point | Strategy |
|---|---|
| **Monolithic** (one manager/God file) | Full split into the target tree; the legacy files are deleted at the end |
| **Pseudo-layered** (`models.py`/`controllers.py` exist but leak) | Create the tree, move each function to its correct layer, split by entity; delete the old flat files |
| **Partially layered** (`models/`, `routes/`, `services/`, `utils/`) | Keep what complies; add the missing layers (`controllers/`, `config/`, `middlewares/`); move business logic out of `routes/` into controllers; rename `routes/` → `views/` only if needed for consistency (moving files is fine, keep URLs); move `utils` constants/validators into `controllers/validators.py` or `models` |

## 6. Naming conventions

- Use the domain vocabulary already in the code (`produto_model.py`, `pedido_controller.py` in a Portuguese codebase; `taskController.js` in English).
- Python: `snake_case` modules, `PascalCase` classes. JS: `camelCase` files and functions, `PascalCase` classes.
- One controller per aggregate/use-case area; avoid "Manager", "Utils", "Helper" names.

## 7. Definition of done for the structure

- [ ] Every route lives in `views/` (or `routes/`) and is ≤ ~15 lines
- [ ] No SQL / ORM query outside `models/`
- [ ] No web framework import inside `controllers/` or `models/`
- [ ] No literal secret anywhere; config module reads env vars
- [ ] One centralized error handler; no per-route catch-all
- [ ] Composition root wires dependencies; no module-level mutable singletons other than framework-mandated ones (e.g., Flask-SQLAlchemy `db`)
- [ ] Original run command and every route still work
