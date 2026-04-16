# MVC Architecture Guidelines

This document defines the target MVC architecture for refactored projects. The skill must restructure any backend project to follow these guidelines.

---

## Target Directory Structure

### Python / Flask Projects

```
project/
├── config/
│   ├── __init__.py
│   └── settings.py          # All configuration from environment variables
├── models/
│   ├── __init__.py
│   ├── <entity>_model.py    # One file per domain entity
│   └── database.py          # Database connection and initialization
├── controllers/
│   ├── __init__.py
│   └── <entity>_controller.py  # Business logic per domain
├── views/
│   ├── __init__.py
│   └── <entity>_routes.py   # Route definitions per domain
├── middlewares/
│   ├── __init__.py
│   └── error_handler.py     # Centralized error handling
├── app.py                   # Composition root — wires everything together
├── requirements.txt
└── .env                     # Environment variables (gitignored)
```

### Node.js / Express Projects

```
project/
├── src/
│   ├── config/
│   │   └── settings.js       # All configuration from environment variables
│   ├── models/
│   │   ├── database.js       # Database connection and initialization
│   │   └── <entity>Model.js  # One file per domain entity
│   ├── controllers/
│   │   └── <entity>Controller.js  # Business logic per domain
│   ├── routes/
│   │   ├── index.js          # Route aggregator
│   │   └── <entity>Routes.js # Route definitions per domain
│   ├── middlewares/
│   │   └── errorHandler.js   # Centralized error handling
│   └── app.js                # Composition root
├── package.json
└── .env                      # Environment variables (gitignored)
```

---

## Layer Responsibilities

### 1. Config Layer (`config/`)

**Responsibility:** Centralize ALL application configuration.

**Rules:**
- Read ALL settings from environment variables
- Provide sensible defaults for development
- Never import from other project layers
- Export a single config object or module

**Must contain:**
- `SECRET_KEY` from environment
- `DATABASE_URL` or `DB_PATH` from environment
- `DEBUG` flag from environment (default `False` / `false`)
- `PORT` from environment (default `5000` or `3000`)
- `HOST` from environment (default `0.0.0.0`)

**Example (Python):**
```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
PORT = int(os.environ.get('PORT', 5000))
```

**Example (Node.js):**
```javascript
require('dotenv').config();

module.exports = {
  secretKey: process.env.SECRET_KEY || 'dev-key-change-in-production',
  database: process.env.DATABASE_URL || './app.db',
  debug: process.env.DEBUG === 'true',
  port: parseInt(process.env.PORT || '3000', 10),
};
```

---

### 2. Model Layer (`models/`)

**Responsibility:** Data access and representation. Models define the shape of data and how to interact with the database.

**Rules:**
- One model file per domain entity (e.g., `product_model.py`, `user_model.py`)
- Models contain ONLY data access logic (CRUD operations)
- Use parameterized queries or ORM methods — NEVER string concatenation
- Define data validation at the schema level (constraints, types)
- Return plain data objects (dicts, dataclasses, or ORM instances)
- No HTTP-specific code (no `request`, `response`, status codes)
- No business logic (calculations, workflows, decisions)

**Database module (`database.py` / `database.js`):**
- Initialize database connection
- Create tables / run migrations
- Seed initial data if needed
- Export connection getter function

---

### 3. Controller Layer (`controllers/`)

**Responsibility:** Business logic, orchestration, and data transformation. Controllers process data from routes and coordinate between models.

**Rules:**
- One controller file per domain entity or feature
- Controllers contain business logic (validation, calculations, workflows)
- Controllers call model methods to read/write data
- Controllers return processed data (dicts, objects) — NOT HTTP responses
- Controllers may call other controllers for cross-domain operations
- No direct database queries — always go through models
- No HTTP-specific code (no `request` objects, no `jsonify`)

**Example (Python):**
```python
from models.product_model import ProductModel

class ProductController:
    def __init__(self):
        self.model = ProductModel()

    def create_product(self, data):
        # Validate
        if not data.get('name') or len(data['name']) < 2:
            raise ValueError("Product name must be at least 2 characters")
        if data.get('price', 0) <= 0:
            raise ValueError("Price must be positive")

        # Business logic
        product = self.model.create(data)
        return product
```

---

### 4. View / Routes Layer (`views/` or `routes/`)

**Responsibility:** HTTP interface. Routes define endpoints, parse requests, and format responses.

**Rules:**
- One route file per domain entity or feature group
- Routes handle HTTP concerns: parse request data, set status codes, format JSON responses
- Routes call controllers — NEVER models directly
- Routes handle HTTP error codes (400, 404, 500)
- Keep routes thin — minimal logic, delegate to controllers
- Register routes using blueprints (Flask) or Router (Express)

**Example (Python/Flask):**
```python
from flask import Blueprint, request, jsonify
from controllers.product_controller import ProductController

product_bp = Blueprint('products', __name__)
controller = ProductController()

@product_bp.route('/products', methods=['POST'])
def create_product():
    try:
        data = request.get_json()
        product = controller.create_product(data)
        return jsonify(product), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500
```

**Example (Node.js/Express):**
```javascript
const express = require('express');
const router = express.Router();
const ProductController = require('../controllers/productController');

const controller = new ProductController();

router.post('/products', async (req, res, next) => {
    try {
        const product = await controller.createProduct(req.body);
        res.status(201).json(product);
    } catch (error) {
        next(error);
    }
});

module.exports = router;
```

---

### 5. Middleware Layer (`middlewares/`)

**Responsibility:** Cross-cutting concerns that apply to multiple routes.

**Must include:**
- **Error handler**: Centralized error handling middleware that catches all errors and returns consistent JSON responses with appropriate HTTP status codes
- **Logging**: Request/response logging using proper logging framework (not `print()` or `console.log()`)

**Example Error Handler (Python/Flask):**
```python
from flask import jsonify

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request", "message": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500
```

**Example Error Handler (Node.js/Express):**
```javascript
function errorHandler(err, req, res, next) {
    const status = err.status || 500;
    res.status(status).json({
        error: err.message || 'Internal server error'
    });
}

module.exports = errorHandler;
```

---

### 6. Composition Root (`app.py` / `app.js`)

**Responsibility:** Wire everything together. This is the entry point of the application.

**Rules:**
- Create the application instance
- Load configuration
- Initialize database
- Register all routes/blueprints
- Register middleware (error handlers, CORS, logging)
- Start the server
- Keep it minimal — no business logic, no route handlers

**Example (Python/Flask):**
```python
from flask import Flask
from flask_cors import CORS
from config.settings import SECRET_KEY, DEBUG, PORT
from models.database import init_db
from views.product_routes import product_bp
from views.user_routes import user_bp
from middlewares.error_handler import register_error_handlers

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    CORS(app)

    init_db()

    app.register_blueprint(product_bp)
    app.register_blueprint(user_bp)

    register_error_handlers(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=DEBUG, port=PORT)
```

---

## Security Requirements

Every refactored project MUST address these security concerns:

1. **No hardcoded secrets** — All secrets via environment variables
2. **Parameterized queries** — No SQL string concatenation
3. **Proper password hashing** — bcrypt or argon2 (NEVER MD5/SHA/plaintext/base64)
4. **No sensitive data in responses** — Exclude passwords, internal configs from API output
5. **Debug mode disabled by default** — Only enable via environment variable
6. **Input validation** — Validate all user inputs at the route level
7. **Proper error messages** — No stack traces or internal details in production responses
