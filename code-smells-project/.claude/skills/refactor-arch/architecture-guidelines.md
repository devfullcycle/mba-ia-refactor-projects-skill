# Architecture Guidelines — MVC Target Pattern

This document defines the target MVC architecture for the refactoring phase. Use it to plan and execute Phase 3.

---

## 1. MVC Layer Responsibilities

### Model Layer (`models/`)
**Responsibility:** Data structure, persistence, and data access logic only.

**Contains:**
- Database schema definition (ORM models or table creation)
- CRUD operations for a single domain entity
- Simple queries to fetch/save data
- Relationships between entities
- Data validation at the persistence level (constraints)

**Does NOT contain:**
- Business rules or calculations
- HTTP request/response handling
- Email/notification sending
- Multiple domain entities in one file

**Python/Flask example:**
```python
# models/product_model.py
class ProductModel:
    def __init__(self, db):
        self.db = db

    def find_all(self):
        return self.db.execute("SELECT * FROM products").fetchall()

    def find_by_id(self, product_id):
        return self.db.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()

    def create(self, name, price, stock):
        self.db.execute(
            "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
            (name, price, stock)
        )
        self.db.commit()
```

**Node.js/Express example:**
```javascript
// models/ProductModel.js
class ProductModel {
    constructor(db) { this.db = db }

    async findAll() {
        return this.db.allAsync("SELECT * FROM products")
    }

    async findById(id) {
        return this.db.getAsync("SELECT * FROM products WHERE id = ?", [id])
    }
}
module.exports = ProductModel
```

---

### Controller Layer (`controllers/`)
**Responsibility:** Orchestrate the application flow. Receive validated input, call the appropriate service/model methods, and return the result.

**Contains:**
- Input validation (type, required fields, format)
- Calls to service layer or model layer
- Response formatting (HTTP status codes, JSON structure)
- Error handling for expected cases
- Authentication checks

**Does NOT contain:**
- Database queries (delegate to models)
- Complex business logic (delegate to services)
- Email/notification logic (delegate to services)

**Python/Flask example:**
```python
# controllers/product_controller.py
class ProductController:
    def __init__(self, product_model):
        self.product_model = product_model

    def get_all_products(self):
        products = self.product_model.find_all()
        return [dict(p) for p in products], 200

    def create_product(self, data):
        name = data.get('name', '').strip()
        if not name or len(name) > 200:
            return {'error': 'Invalid name'}, 400

        try:
            price = float(data['price'])
            if price < 0:
                return {'error': 'Price must be non-negative'}, 400
        except (KeyError, ValueError):
            return {'error': 'Price must be a number'}, 400

        self.product_model.create(name, price, data.get('stock', 0))
        return {'message': 'Product created'}, 201
```

---

### View / Routes Layer (`views/` or `routes/`)
**Responsibility:** Define HTTP endpoints, parse request data, call controllers, and send responses. In REST APIs this is the "routes" layer; it has no HTML rendering logic.

**Contains:**
- Route definitions (`@app.route`, `router.get`, `app.post`)
- Request parameter extraction (`request.json`, `req.body`, `req.params`)
- Response serialization (`jsonify`, `res.json`)
- Middleware application (auth, CORS, rate limiting)

**Does NOT contain:**
- Business logic
- Direct database calls
- Complex validation

**Python/Flask example:**
```python
# views/product_routes.py
from flask import Blueprint, request, jsonify
from controllers.product_controller import ProductController
from models.product_model import ProductModel

products_bp = Blueprint('products', __name__)

@products_bp.route('/api/products', methods=['GET'])
def list_products():
    controller = ProductController(ProductModel(get_db()))
    result, status = controller.get_all_products()
    return jsonify(result), status

@products_bp.route('/api/products', methods=['POST'])
def create_product():
    controller = ProductController(ProductModel(get_db()))
    result, status = controller.create_product(request.get_json() or {})
    return jsonify(result), status
```

---

### Config Layer (`config/`)
**Responsibility:** Centralize all configuration. Read from environment variables, never hardcode values.

**Contains:**
- Database connection settings
- Secret keys
- Debug flags
- External service URLs/credentials
- Environment-specific settings (development/production)

**Python/Flask example:**
```python
# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'app.db')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000')
```

**Node.js example:**
```javascript
// config/settings.js
require('dotenv').config()

module.exports = {
    secretKey: process.env.SECRET_KEY || 'change-me-in-production',
    dbPath: process.env.DB_PATH || './database.db',
    debug: process.env.DEBUG === 'true',
    port: parseInt(process.env.PORT) || 3000,
}
```

---

### Middleware Layer (`middlewares/`)
**Responsibility:** Cross-cutting concerns that apply to multiple routes.

**Contains:**
- Authentication/authorization checks
- Request logging
- Error handling (global error handler)
- CORS headers
- Rate limiting
- Input sanitization

**Python/Flask example:**
```python
# middlewares/error_handler.py
from flask import jsonify

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad request', 'message': str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'error': 'Internal server error'}), 500
```

---

## 2. Target Directory Structure

### Python/Flask Project
```
src/
├── config/
│   └── settings.py          # Environment-based configuration
├── models/
│   ├── __init__.py
│   ├── product_model.py     # One file per domain entity
│   ├── user_model.py
│   └── order_model.py
├── controllers/
│   ├── __init__.py
│   ├── product_controller.py
│   ├── user_controller.py
│   └── order_controller.py
├── views/
│   ├── __init__.py
│   ├── product_routes.py    # Blueprint per domain
│   ├── user_routes.py
│   └── order_routes.py
├── middlewares/
│   ├── __init__.py
│   ├── auth.py
│   └── error_handler.py
├── services/                # Optional — for complex business logic
│   ├── __init__.py
│   └── notification_service.py
└── app.py                   # Composition root — just wires things together
```

### Node.js/Express Project
```
src/
├── config/
│   └── settings.js
├── models/
│   ├── UserModel.js
│   ├── ProductModel.js
│   └── OrderModel.js
├── controllers/
│   ├── UserController.js
│   ├── ProductController.js
│   └── OrderController.js
├── routes/
│   ├── userRoutes.js
│   ├── productRoutes.js
│   └── orderRoutes.js
├── middlewares/
│   ├── auth.js
│   └── errorHandler.js
├── services/                # Optional
│   └── PaymentService.js
└── app.js                   # Entry point
```

---

## 3. Entry Point (Composition Root)

The entry point (`app.py` / `app.js`) should ONLY:
1. Create the application instance
2. Load configuration
3. Register routes/blueprints
4. Register middleware
5. Start the server

**Python/Flask:**
```python
# app.py — composition root only
from flask import Flask
from config.settings import Config
from views.product_routes import products_bp
from views.user_routes import users_bp
from middlewares.error_handler import register_error_handlers

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(products_bp)
    app.register_blueprint(users_bp)
    register_error_handlers(app)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config['DEBUG'])
```

**Node.js/Express:**
```javascript
// app.js — composition root only
const express = require('express')
const config = require('./config/settings')
const userRoutes = require('./routes/userRoutes')
const productRoutes = require('./routes/productRoutes')
const errorHandler = require('./middlewares/errorHandler')

const app = express()
app.use(express.json())
app.use('/api/users', userRoutes)
app.use('/api/products', productRoutes)
app.use(errorHandler)

app.listen(config.port, () => console.log(`Running on ${config.port}`))
```

---

## 4. Security Checklist

Apply these security fixes during refactoring:

- [ ] Move all secrets to `.env` file (never commit)
- [ ] Add `.env` to `.gitignore` if not already present
- [ ] Create `.env.example` with placeholder values
- [ ] Replace plain text passwords with `bcrypt` / `werkzeug.security`
- [ ] Replace MD5/SHA1 password hashing with bcrypt/argon2
- [ ] Fix all SQL injections → parameterized queries
- [ ] Remove debug mode hardcoding → use environment variable
- [ ] Remove dangerous admin endpoints (arbitrary SQL execution, unauthenticated resets)
- [ ] Strip sensitive fields from API responses (password hashes, internal keys)
- [ ] Add basic input validation to all POST/PUT endpoints

---

## 5. Adapting to Existing Structure

If a project already has partial MVC (has `models/`, `routes/`, etc.), do not recreate from scratch. Instead:
1. Identify which layer responsibilities are violated (e.g., business logic in routes)
2. Move misplaced code to the correct layer
3. Fix security issues in place
4. Rename for consistency if needed
5. Add missing layers (usually `config/` and `middlewares/`)

The goal is improvement, not mechanical reconstruction.
