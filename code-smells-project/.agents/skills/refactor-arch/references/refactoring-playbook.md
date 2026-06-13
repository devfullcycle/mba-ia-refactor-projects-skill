# Refactoring Playbook

Apply the smallest transformation that creates a real MVC boundary. Adapt syntax, libraries, lifecycle, and validation to the detected technology. All examples are illustrative; derive additional transformations from verified findings.

## 1. Separate Model, View, And Controller Responsibilities

Before:

```text
interface handler -> validates + calculates + mutates state + formats output
```

After:

```text
interface action -> Controller -> Model/use case -> View/presenter
```

First identify responsibilities in the existing code, then extract them using conventions native to the project. Validate the original observable contract.

## 2. Extract Hardcoded Configuration

Before:

```python
app.config["SECRET_KEY"] = "secret-123"
```

After:

```python
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
```

Validate startup with configured values and verify secrets are absent from responses/logs.

## 3. Replace Unsafe Dynamic Construction

Before:

```python
cursor.execute("SELECT * FROM users WHERE email = '" + email + "'")
```

After:

```python
cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
```

This pattern also applies to shell commands, templates, paths, selectors, expressions, and other dynamically constructed operations. Use the safe API provided by the detected technology. Validate normal and hostile-shaped input.

## 4. Split A God Module

Before:

```javascript
class AppManager {
  setupRoutes(app) { /* HTTP + payment + database + report */ }
}
```

After:

```javascript
app.post('/checkout', checkoutController.create);
const checkoutController = new CheckoutController(checkoutService);
const checkoutService = new CheckoutService(enrollmentRepository, paymentGateway);
```

Extract one use case at a time and preserve route contracts.

## 5. Move Business Logic Out Of A View Or Interface Handler

Before:

```python
@route("/orders", methods=["POST"])
def create_order():
    total = calculate_total(request.json)
    save_order(total)
```

After:

```python
@route("/orders", methods=["POST"])
def create_order():
    result = order_controller.create(request.get_json())
    return jsonify(result.body), result.status
```

Put rules in the Model/use case; keep input coordination in the Controller and presentation in the View.

## 6. Add An Atomicity Or Consistency Boundary

Before:

```javascript
await enrollments.insert(enrollment);
await payments.insert(payment);
await audit.insert(event);
```

After:

```javascript
await db.transaction(async (tx) => {
  await enrollments.insert(enrollment, tx);
  await payments.insert(payment, tx);
  await audit.insert(event, tx);
});
```

The boundary may be a database transaction, idempotent workflow, compensation, atomic file replacement, message acknowledgement, or technology-specific equivalent. Force a middle-step failure and verify the defined consistency guarantee.

## 7. Replace Repeated I/O With Batch Or Set-Based Work

Before:

```python
for order in orders:
    order.items = find_items(order.id)
```

After:

```python
items_by_order = find_items_for_orders([order.id for order in orders])
for order in orders:
    order.items = items_by_order.get(order.id, [])
```

This also applies to files, remote calls, rendering, and message processing. Measure calls/work for multiple records.

## 8. Centralize Validation

Before:

```python
if status not in ["pending", "done"]:
    return {"error": "invalid"}, 400
```

After:

```python
command = CreateTaskSchema().load(request.get_json())
task_service.create(command)
```

Reuse the schema/domain validator across create and update flows where rules match.

## 9. Centralize Error Handling

Before:

```python
try:
    result = service.run()
except Exception as exc:
    return {"error": str(exc)}, 500
```

After:

```python
@app.errorhandler(ApplicationError)
def handle_application_error(error):
    return {"error": error.public_message}, error.status_code
```

Map errors at each View/interface boundary. Log internal details once and verify external outputs do not leak them.

## 10. Replace Unsafe Authentication Or Sensitive-Data Handling

Before:

```python
user.password = hashlib.md5(password.encode()).hexdigest()
```

After:

```python
user.password = password_hasher.hash(password)
password_hasher.verify(user.password, candidate)
```

Use Argon2, bcrypt, scrypt, or PBKDF2. Add login success/failure regression tests and never serialize the hash.

## 11. Replace Global Mutable State With Managed Dependencies

Before:

```javascript
let globalCache = {};
module.exports = { globalCache };
```

After:

```javascript
const cache = new CacheClient(config.cache);
const service = new CheckoutService(repository, cache);
```

Define lifecycle and test isolation; use a real shared cache only when required.

## 12. Bound Unbounded Work

Before:

```python
tasks = Task.query.all()
```

After:

```python
page = Task.query.order_by(Task.id).paginate(page=page_number, per_page=limit, max_per_page=100)
```

Use pagination, streaming, backpressure, batching, limits, cancellation, or a technology-appropriate bound. Preserve or explicitly version the observable contract if its shape must change.

## 13. Replace A Deprecated API

Before:

```python
user = User.query.get(user_id)
```

After:

```python
user = db.session.get(User, user_id)
```

Confirm the installed library version and official replacement before editing. Add a focused regression test and rerun with deprecation warnings enabled when supported.

## 14. Enforce A Domain Invariant In The Model

Before:

```text
multiple Controllers/Views each implement a slightly different rule
```

After:

```text
Controller -> one Model operation that validates and applies the invariant
```

Derive the invariant from contracts, tests, schemas, and domain behavior. Add edge-case regression tests.

## 15. Repair Resource And Failure Lifecycle

Before:

```text
open/start/consume -> success-only cleanup
```

After:

```text
acquire -> bounded operation -> cleanup/rollback/acknowledge on every path
```

Use language/runtime lifecycle primitives, explicit cancellation/timeouts, idempotency, or compensation as appropriate.

## Transformation Order

1. Capture observable contracts and tests.
2. Extract configuration and composition root.
3. Map and separate Model, View, and Controller responsibilities without behavior changes.
4. Extract supporting services, state adapters, and consistency boundaries.
5. Correct verified security, correctness, reliability, performance, and technology-specific findings.
6. Centralize validation and errors where appropriate.
7. Run full contract validation and a fresh open-ended audit.
