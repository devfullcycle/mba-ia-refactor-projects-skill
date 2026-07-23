# 04 — MVC Target Architecture Guidelines

Phase 3 restructures the project into clean **MVC** with supporting cross-cutting layers. The exact
folder names follow each stack's convention, but the responsibilities are identical.

## Layer responsibilities (stack-agnostic)

| Layer | Owns | Must NOT |
|---|---|---|
| **Models** | data shape, persistence, serialization (`to_dict`/`toJSON`), simple invariants | run workflows, send notifications, import routes/controllers |
| **Views / Routes** | HTTP only: parse request, call controller, return response with the right status | touch the DB directly, enforce business rules, format business data |
| **Controllers** | orchestrate one use case: validate input → call service(s) → map result to HTTP | contain pricing/state-machine rules, SQL, side-effects like email |
| **Services** (domain) | business rules: pricing, discounts, state machines, transactions, side-effects | import Flask/Express request/response objects |
| **Config** | env-driven settings, secret loading, feature flags | hardcode secrets, know about HTTP |
| **Middlewares** | cross-cutting: error handler, auth, CORS, request logging | contain business logic |
| **Repositories/DB** (optional) | connection management, schema/seed as a CLI command | be a global mutable singleton imported everywhere |

## Mapping per stack

### Python / Flask
```
<project>/
├── app.py                  # composition root: create_app(), registers blueprints + errorhandler
├── config/settings.py      # class Config: SECRET_KEY = os.environ[...], DEBUG from env, DB URI
├── extensions.py           # db = SQLAlchemy()  (the single shared extension object)
├── models/                 # one file per entity: produto_model.py, usuario_model.py, ...
├── controllers/            # one file per resource: produto_controller.py, pedido_controller.py
├── services/               # pedido_service.py (transactions, discounts), notification_service.py
├── routes/                 # blueprints: produto_routes.py ... (the "Views" layer)
├── middlewares/            # error_handler.py (app.errorhandler), auth.py (decorators)
├── schemas/                # marshmallow schemas for input validation (optional but encouraged)
├── scripts/seed.py         # seeding as a CLI, guarded by env (not import-time)
├── requirements.txt
└── .env.example            # documents required env vars (the real .env is gitignored)
```
- Use an **application factory**: `def create_app(config_class): app = Flask(__name__); app.config.from_object(...); db.init_app(app); register blueprints; return app`.
- "Views" = the **routes** (Flask is an API, so views are JSON route functions). Keep them thin.
- DB access goes through **models** or a thin repository, never raw `sqlite3` in a route.

### Node.js / Express
```
<project>/
├── src/
│   ├── app.js              # createApp(): express(), json(), mounts routers + error middleware
│   ├── server.js           # app.listen (separate from app.js so it is testable)
│   ├── config/index.js     # reads process.env, validates required vars
│   ├── db/index.js         # open connection + schema init (no business logic)
│   ├── models/             # one file per entity (query helpers / shape)
│   ├── controllers/        # checkoutController.js, reportController.js, userController.js
│   ├── services/           # checkoutService.js (transactions, payment), reportService.js
│   ├── routes/             # routers wire method+path -> controller (the "Views" layer)
│   ├── middlewares/        # errorHandler.js (the 4-arg handler), auth.js, notFound.js
│   └── utils/              # logger.js, hash.js (bcrypt)
├── .env.example
└── package.json
```
- Separate `app.js` (exportable, testable) from `server.js` (listen) so `supertest` works.
- The error handler is the **last** `app.use((err, req, res, next) => ...)`.
- Use `async/await` + a `asyncHandler` wrapper (or `express-async-errors`) — no callback pyramids.

## Layering rules (the "smell tests" to re-check after refactor)

1. **No route imports the DB driver directly.** Routes → Controllers → Services → Models/DB.
2. **No `request`/`response` inside services.** They receive plain values and return plain values/exceptions.
3. **One error handler** centralizes error responses. Routes never repeat `try/except Exception`.
4. **Secrets only in `config`**, read from env. No literal keys anywhere else.
5. **No global mutable state** in the request path (no shared connection, no module cache mutated per request).
6. **Every original route still responds** with the same method + path after the refactor.
7. **Validation lives at the edge** (controller or middleware schema), not scattered in services.

## What "preserving behavior" means in Phase 3

- Keep the same HTTP method + path for every public endpoint.
- Keep the same response shape where reasonable (don't break clients). Adding fields is OK; removing
  fields that clients need is not. (Removing a leaked `password` field IS the intended fix.)
- Keep seed data equivalent so endpoints return data after boot.
- The login endpoint keeps returning a token (even if it is still simple) so the contract holds; you
  may improve its verification but the route and success-path shape stay.
