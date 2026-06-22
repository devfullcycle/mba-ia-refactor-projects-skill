# MVC Architecture Guidelines — /refactor-arch

This document defines the target MVC architecture for the `/refactor-arch` skill. The structure adapts to the detected technology stack but always enforces the same layer responsibilities.

---

## Core Principle: Strict Layer Separation

| Layer | Responsibility | What it must NOT do |
|---|---|---|
| **Model** | Database access, data persistence, query execution | Handle HTTP, format responses, implement business rules |
| **Controller** | Orchestrate request flow: validate input → call model → return response | Execute SQL directly, format database rows, send notifications |
| **View / Routes** | Define HTTP endpoints and map them to controllers | Contain business logic or database calls |
| **Config** | Load environment variables, constants, and app configuration | Contain business logic |
| **Service** | Cross-cutting business logic (notifications, payments, calculations) | Access HTTP request/response objects directly |
| **Middleware** | Authentication, error handling, logging, rate limiting | Contain business logic |

---

## Python / Flask Target Structure

```
src/
├── config/
│   ├── settings.py           # ENV vars: SECRET_KEY, DEBUG, DATABASE_PATH, etc.
│   └── logging_config.py     # Logging setup (format, level, handlers)
│
├── database/
│   └── connection.py         # get_db() using flask.g, init_app(), schema creation
│
├── models/
│   ├── produto_model.py      # CRUD queries for produtos — parameterized SQL only
│   ├── usuario_model.py      # CRUD queries for usuarios — password hashing
│   ├── pedido_model.py       # Order queries with JOIN (no N+1)
│   └── relatorio_model.py    # Reporting queries
│
├── controllers/
│   ├── produto_controller.py # Validates input, calls produto_model, returns jsonify()
│   ├── usuario_controller.py # Validates input, calls usuario_model, returns jsonify()
│   └── pedido_controller.py  # Validates input, calls pedido_model, calls notification service
│
├── routes/
│   └── api_routes.py         # Flask Blueprint — maps URLs to controller functions
│
├── middlewares/
│   ├── auth.py               # @require_token, @require_admin decorators
│   └── error_handler.py      # register_error_handlers(app) — 404, 500, generic Exception
│
├── services/
│   └── notification_service.py  # notify_order_created(), notify_order_status_changed()
│
├── .env                      # SECRET_KEY, DEBUG, DATABASE_PATH (gitignored)
├── .env.example              # Template for .env — safe to commit
├── requirements.txt          # Updated dependencies (add python-dotenv, werkzeug, PyJWT)
└── app.py                    # Composition root ONLY — creates Flask app, registers blueprint
```

### `app.py` — Composition Root (Flask)
```python
from flask import Flask
from flask_cors import CORS
from config.settings import SECRET_KEY, DEBUG
from config.logging_config import configure_logging
from database.connection import init_app
from routes.api_routes import api_bp
from middlewares.error_handler import register_error_handlers

def create_app():
    configure_logging()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["DEBUG"] = DEBUG
    CORS(app)
    init_app(app)
    app.register_blueprint(api_bp)
    register_error_handlers(app)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
```

### `routes/api_routes.py` — Blueprint (Flask)
```python
from flask import Blueprint
import controllers.produto_controller as produto_ctrl
import controllers.usuario_controller as usuario_ctrl
import controllers.pedido_controller as pedido_ctrl

api_bp = Blueprint("api", __name__)

# Products
api_bp.add_url_rule("/produtos", view_func=produto_ctrl.listar_produtos, methods=["GET"])
api_bp.add_url_rule("/produtos/busca", view_func=produto_ctrl.buscar_produtos, methods=["GET"])
api_bp.add_url_rule("/produtos/<int:id>", view_func=produto_ctrl.buscar_produto, methods=["GET"])
api_bp.add_url_rule("/produtos", view_func=produto_ctrl.criar_produto, methods=["POST"])
api_bp.add_url_rule("/produtos/<int:id>", view_func=produto_ctrl.atualizar_produto, methods=["PUT"])
api_bp.add_url_rule("/produtos/<int:id>", view_func=produto_ctrl.deletar_produto, methods=["DELETE"])

# Users
api_bp.add_url_rule("/usuarios", view_func=usuario_ctrl.listar_usuarios, methods=["GET"])
api_bp.add_url_rule("/usuarios/<int:id>", view_func=usuario_ctrl.buscar_usuario, methods=["GET"])
api_bp.add_url_rule("/usuarios", view_func=usuario_ctrl.criar_usuario, methods=["POST"])
api_bp.add_url_rule("/login", view_func=usuario_ctrl.login, methods=["POST"])

# Orders
api_bp.add_url_rule("/pedidos", view_func=pedido_ctrl.criar_pedido, methods=["POST"])
api_bp.add_url_rule("/pedidos", view_func=pedido_ctrl.listar_todos_pedidos, methods=["GET"])
api_bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", view_func=pedido_ctrl.listar_pedidos_usuario, methods=["GET"])
api_bp.add_url_rule("/pedidos/<int:pedido_id>/status", view_func=pedido_ctrl.atualizar_status_pedido, methods=["PUT"])

# Reports
api_bp.add_url_rule("/relatorios/vendas", view_func=pedido_ctrl.relatorio_vendas, methods=["GET"])

# Health
api_bp.add_url_rule("/health", view_func=usuario_ctrl.health_check, methods=["GET"])
```

---

## Node.js / Express Target Structure

```
src/
├── config/
│   └── settings.js           # process.env values with defaults
│
├── database/
│   └── connection.js         # better-sqlite3 singleton, schema init, seed
│
├── models/
│   ├── userModel.js
│   ├── productModel.js
│   ├── orderModel.js
│   └── reportModel.js
│
├── controllers/
│   ├── userController.js
│   ├── productController.js
│   └── orderController.js
│
├── routes/
│   ├── userRoutes.js
│   ├── productRoutes.js
│   └── orderRoutes.js
│
├── middlewares/
│   ├── auth.js               # requireToken, requireAdmin
│   └── errorHandler.js       # Express error-handling middleware (4 params)
│
├── services/
│   └── notificationService.js
│
├── .env
├── .env.example
├── package.json
└── app.js                    # createApp(), register routes, export for testing
```

### `app.js` — Composition Root (Express)
```javascript
require('dotenv').config()
const express = require('express')
const cors = require('cors')
const userRoutes = require('./routes/userRoutes')
const productRoutes = require('./routes/productRoutes')
const orderRoutes = require('./routes/orderRoutes')
const { errorHandler } = require('./middlewares/errorHandler')

function createApp() {
    const app = express()
    app.use(cors())
    app.use(express.json())

    app.use('/users', userRoutes)
    app.use('/products', productRoutes)
    app.use('/orders', orderRoutes)

    app.use(errorHandler)
    return app
}

if (require.main === module) {
    const app = createApp()
    const PORT = process.env.PORT || 3000
    app.listen(PORT, () => console.log(`Server running on port ${PORT}`))
}

module.exports = { createApp }
```

---

## Layer Responsibilities — Quick Reference

### Model Rules
- Only one domain entity per file (one model file = one DB table or one aggregate)
- All SQL must use parameterized queries (never string concatenation)
- Returns plain objects/dicts (never HTTP responses)
- Contains schema creation and seed logic for its own entity

### Controller Rules
- Reads from `request` (Flask) / `req` (Express), never from the DB directly
- Validates all input before calling the model
- Calls exactly one model (or one service that wraps models)
- Returns an HTTP response — this is the only layer that does `jsonify()` / `res.json()`
- Does NOT contain `print()` for operational events — use the notification service

### Route / View Rules
- Maps HTTP method + path → controller function
- Contains no logic beyond the mapping and optional middleware chain
- Groups related routes into a Blueprint (Flask) or Router (Express)

### Config Rules
- All values come from `os.environ` / `process.env`
- Provides typed defaults for non-secret values
- Never import from models, controllers, or services

### Service Rules
- Receives domain objects (not HTTP objects) as input
- Can be called from multiple controllers
- Produces side effects (notifications, calculations) cleanly

### Middleware Rules
- Auth middleware: validates token, attaches user to request context, calls next
- Error handler: catches all unhandled exceptions, returns consistent JSON error shape
- Never contains business logic
