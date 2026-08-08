# Python Development Guidelines

Practical reference for writing clear, safe, and maintainable Python 3 code.
Examples use the standard library only. Third-party libraries listed in Project Stack are reference metadata.

## Project Stack

The following libraries were specified for reference in this project:

**User-Specified Libraries** (detected from codebase):
- **ORM/Database**: sqlite3 (stdlib) - DB-API 2.0 SQLite driver used with raw SQL - https://docs.python.org/3/library/sqlite3.html
- **Web Framework**: Flask (v3.1.1) - Lightweight WSGI web application framework - https://flask.palletsprojects.com/
- **CORS**: flask-cors (v5.0.1) - Cross-Origin Resource Sharing for Flask - https://pypi.org/project/flask-cors/
- **Database**: SQLite (`loja.db`) - Embedded SQL database engine - https://www.sqlite.org/

**Auto-Populated Essential Tools**:
- **Testing**: pytest (v9.1.1) - Test runner and assertion framework - https://docs.pytest.org/en/stable/
- **Formatting**: Ruff (v0.16.2) - Fast Python formatter (`ruff format`) - https://docs.astral.sh/ruff/
- **Linting**: Ruff (v0.16.2) - Fast Python linter (`ruff check`) - https://docs.astral.sh/ruff/
- **Logging**: logging (stdlib) - Hierarchical application logging - https://docs.python.org/3/library/logging.html
- **Build Tool**: pip + requirements.txt - Package installer for Python - https://pip.pypa.io/

> **Note**: This section lists libraries for quick reference.
> All code examples in this guideline use standard library or language-native features.
> Principles and patterns apply regardless of library choices.

---

## 1. Core Principles

### 1.1 Philosophy and Style

- Prefer readability over cleverness (PEP 20 / Zen of Python).
- Format with `ruff format`; lint with `ruff check`.
- Follow PEP 8 naming and layout; let the formatter own whitespace.
- Explicit is better than implicit: prefer clear control flow over magic.

```bash
python -c "import this"
ruff format .
ruff check .
```

### 1.2 Clarity over Brevity

- Names communicate intent: `user_id` beats `uid` in business logic.
- Self-explanatory code reduces comment volume.
- Optimize only after measuring; clarity ships first.

| Prefer | Avoid |
|--------|-------|
| `total_price = unit_price * quantity` | `t = u * q` |
| Early returns for guards | Deep nesting |
| Small pure functions | God modules |

---

## 2. Project Initialization

### 2.1 Creating a New Project

```bash
mkdir myapp && cd myapp
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
echo "myapp" > README.md
touch pyproject.toml requirements.txt requirements-dev.txt
```

Minimal `pyproject.toml`:

```toml
[project]
name = "myapp"
version = "0.1.0"
requires-python = ">=3.12"

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

### 2.2 Dependency Management

```bash
python -m pip install flask==3.1.1
python -m pip freeze > requirements.txt
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m pip list --outdated
python -m pip uninstall some-package
```

Pin production deps; keep tools (`pytest`, `ruff`) in `requirements-dev.txt`.

---

## 3. Project Structure

Recommended layout for libraries and services:

```text
myapp/
├── src/
│   └── myapp/
│       ├── __init__.py
│       ├── main.py
│       ├── domain/
│       ├── services/
│       └── db/
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
├── scripts/
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

| Path | Role |
|------|------|
| `src/myapp/` | Application package |
| `tests/` | Unit and integration tests |
| `scripts/` | One-off ops / migrations helpers |
| `docs/` | Design notes and API docs |

Production references: [CPython](https://github.com/python/cpython), [Flask](https://github.com/pallets/flask), [requests](https://github.com/psf/requests).

---

## 4. Container Development (Docker)

### 4.1 Container Philosophy

Use Docker so every developer shares the same Python runtime, OS packages, and ports. No local Python version drift.

### 4.2 Docker File Structure

```text
Dockerfile
docker-compose.yaml
.dockerignore
```

### 4.3 Dockerfile for Development

Pin the official Alpine image. Keep the container alive with `sleep infinity` for interactive work.

```dockerfile
FROM python:3.14.7-alpine3.24

WORKDIR /app

RUN apk add --no-cache gcc musl-dev libffi-dev

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY . .

CMD ["sleep", "infinity"]
```

### 4.4 Docker Compose

```yaml
services:
  app:
    build: .
    working_dir: /app
    volumes:
      - .:/app
    ports:
      - "5003:5003"
    environment:
      PYTHONUNBUFFERED: "1"
      APP_ENV: development
    healthcheck:
      test: ["CMD", "python", "-c", "print('ok')"]
      interval: 30s
      timeout: 5s
      retries: 3
```

### 4.5 .dockerignore

```text
.venv
__pycache__
*.pyc
.git
.pytest_cache
.ruff_cache
*.db
.env
```

### 4.6 Essential Commands

| Action | Command |
|--------|---------|
| Start | `docker compose up -d --build` |
| Logs | `docker compose logs -f app` |
| Run app | `docker compose exec app python -m myapp.main` |
| Tests | `docker compose exec app pytest -q` |
| Shell | `docker compose exec app sh` |
| Stop | `docker compose down` |

### 4.7 Best Practices

- Pin image tags (`python:3.14.7-alpine3.24`), never `latest` in shared envs.
- Mount source for hot reload; install deps inside the image.
- Keep secrets in env files excluded from the image build context.

---

## 5. Naming Conventions

Follow PEP 8:

| Kind | Convention | Example |
|------|------------|---------|
| Modules / packages | `snake_case` | `order_service.py` |
| Classes | `PascalCase` | `OrderService` |
| Functions / methods | `snake_case` | `create_order` |
| Variables | `snake_case` | `total_amount` |
| Constants | `UPPER_SNAKE` | `MAX_RETRIES` |
| Private | leading `_` | `_cache` |
| Type aliases | `PascalCase` | `ProductId` |

```python
MAX_ITEMS = 100

class OrderLine:
    def __init__(self, product_id: int, quantity: int) -> None:
        self.product_id = product_id
        self.quantity = quantity

def calculate_line_total(unit_price: float, quantity: int) -> float:
    return unit_price * quantity
```

Avoid single-letter names outside short loops (`i`, `j`) or math.

---

## 6. Types and Type System

Python is dynamically typed with optional gradual typing (PEP 484). Annotate public APIs.

### 6.1 Type Declaration

```python
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class OrderStatus(Enum):
    PENDING = "pendente"
    APPROVED = "aprovado"
    CANCELLED = "cancelado"


@dataclass(frozen=True)
class Product:
    id: int
    name: str
    price: float
    stock: int


class Repository(Protocol):
    def get(self, product_id: int) -> Product | None: ...
```

### 6.2 Type Safety

```bash
python -m pip install mypy
mypy src
```

- Prefer `X | None` over bare optional returns without annotation.
- Use `list[str]`, `dict[str, int]` (Python 3.9+).
- Avoid `Any` except at system boundaries.

### 6.3 Allocation and Initialization

```python
from dataclasses import dataclass, field


@dataclass
class Cart:
    items: list[int] = field(default_factory=list)

    def add(self, product_id: int) -> None:
        self.items.append(product_id)
```

Never use mutable default arguments (`def f(items=[])`).

---

## 7. Functions and Methods

### 7.1 Signatures

```python
def create_product(
    name: str,
    price: float,
    stock: int,
    category: str = "geral",
) -> int:
    """Persist a product and return its id.

    Raises:
        ValueError: if validation fails.
    """
    if price < 0 or stock < 0:
        raise ValueError("price and stock must be non-negative")
    if len(name) < 2:
        raise ValueError("name too short")
    return _insert_product(name, price, stock, category)
```

### 7.2 Returns and Errors — Good vs Bad

```python
# Good: explicit error, typed return
def get_product(product_id: int) -> dict[str, object]:
    product = find_product(product_id)
    if product is None:
        raise LookupError(f"product {product_id} not found")
    return product


# Bad: ambiguous None / silent failure
def get_product_bad(product_id: int):
    try:
        return find_product(product_id)
    except Exception:
        return None
```

### 7.3 Best Practices

- One responsibility per function.
- Prefer <= 4 parameters; group with a dataclass when more.
- No hidden I/O side effects in pure calculators.
- Document non-obvious preconditions in the docstring.

---

## 8. Error Handling

### 8.1 Philosophy

Python uses exceptions. Create domain errors; wrap lower-level failures with context.

```python
class DomainError(Exception):
    """Base application error."""


class InsufficientStockError(DomainError):
    def __init__(self, product_id: int, requested: int, available: int) -> None:
        super().__init__(
            f"product {product_id}: requested {requested}, available {available}"
        )
        self.product_id = product_id
```

### 8.2 Conventions — Good vs Bad

```python
# Good: catch specific errors, add context, re-raise or translate
def reserve_stock(product_id: int, quantity: int) -> None:
    try:
        available = fetch_stock(product_id)
    except OSError as exc:
        raise DomainError(f"stock lookup failed for {product_id}") from exc
    if quantity > available:
        raise InsufficientStockError(product_id, quantity, available)
    update_stock(product_id, available - quantity)


# Bad: swallow everything
def reserve_stock_bad(product_id: int, quantity: int) -> None:
    try:
        update_stock(product_id, quantity)
    except Exception:
        pass
```

### 8.3 Best Practices

- Never bare `except:` or `except Exception: pass`.
- Use `raise ... from exc` to preserve cause chains.
- Log at I/O boundaries (HTTP handlers, CLI), not in every helper.
- Map domain errors to HTTP/status codes only at the edge.

---

## 9. Concurrency and Parallelism

### 9.1 Concurrency Model

- **threading**: I/O-bound work under the GIL.
- **multiprocessing**: CPU-bound parallelism.
- **asyncio**: cooperative async I/O on one thread.

```python
import asyncio


async def fetch_all(urls: list[str]) -> list[bytes]:
    async def one(url: str) -> bytes:
        await asyncio.sleep(0.01)
        return url.encode()

    return await asyncio.gather(*(one(u) for u in urls))
```

### 9.2 Synchronization

```python
import threading

_lock = threading.Lock()
_counter = 0


def increment() -> int:
    global _counter
    with _lock:
        _counter += 1
        return _counter
```

Prefer queues (`queue.Queue`, `asyncio.Queue`) over shared mutable state.

### 9.3 Best Practices

- Bound lifetimes: cancel tasks, join threads, close pools.
- Always set timeouts on network and lock waits.
- Graceful shutdown via signals / `asyncio.Event`.

### 9.4 Common Pitfalls

- Sharing one `sqlite3.Connection` across threads without serialization.
- Fire-and-forget tasks that hide exceptions.
- CPU work blocking the asyncio event loop (use `asyncio.to_thread`).

---

## 10. Interfaces and Abstractions

### 10.1 Interface Design

Prefer small Protocols (PEP 544) or ABCs over fat base classes.

```python
from typing import Protocol


class ProductStore(Protocol):
    def get(self, product_id: int) -> dict[str, object] | None: ...
    def save(self, product: dict[str, object]) -> int: ...
```

### 10.2 Implementation

```python
class MemoryProductStore:
    def __init__(self) -> None:
        self._items: dict[int, dict[str, object]] = {}
        self._seq = 0

    def get(self, product_id: int) -> dict[str, object] | None:
        return self._items.get(product_id)

    def save(self, product: dict[str, object]) -> int:
        self._seq += 1
        self._items[self._seq] = product
        return self._seq
```

### 10.3 Composition

```python
class OrderService:
    def __init__(self, store: ProductStore) -> None:
        self._store = store

    def assert_exists(self, product_id: int) -> None:
        if self._store.get(product_id) is None:
            raise LookupError(product_id)
```

Depend on Protocols in constructors; swap implementations in tests.

---

## 11. Unit Tests

### 11.1 Structure

```python
# tests/unit/test_pricing.py
import pytest

from myapp.pricing import apply_discount


def test_apply_discount_ten_percent() -> None:
    assert apply_discount(100.0, 0.10) == 90.0


def test_apply_discount_rejects_negative() -> None:
    with pytest.raises(ValueError, match="negative"):
        apply_discount(-1.0, 0.1)
```

Naming: `test_<unit>_<scenario>_<expected>`.

### 11.2 Table-Driven Tests

```python
@pytest.mark.parametrize(
    ("amount", "rate", "expected"),
    [
        (100.0, 0.0, 100.0),
        (100.0, 0.05, 95.0),
        (100.0, 0.10, 90.0),
    ],
)
def test_apply_discount_table(amount: float, rate: float, expected: float) -> None:
    assert apply_discount(amount, rate) == expected
```

### 11.3 Assertions

- Prefer plain `assert` with pytest rewriting.
- Use `pytest.raises` for exceptions.
- Compare floats with `pytest.approx` when needed.

### 11.4 Commands

```bash
pytest
pytest tests/unit/test_pricing.py
pytest -k discount
pytest -vv
pytest --cov=myapp --cov-report=term-missing
pytest -x
```

---

## 12. Mocks and Testability

### 12.1 Mock Strategies

Prefer fakes implementing Protocols. Use `unittest.mock` when fakes are heavy.

```python
from unittest.mock import Mock


def test_order_service_uses_store() -> None:
    store = Mock()
    store.get.return_value = {"id": 1, "nome": "Mouse"}
    service = OrderService(store)
    service.assert_exists(1)
    store.get.assert_called_once_with(1)
```

### 12.2 Dependency Injection

```python
def build_service(store: ProductStore | None = None) -> OrderService:
    return OrderService(store or MemoryProductStore())
```

Inject collaborators; avoid importing globals for I/O inside domain logic.

### 12.3 Test Doubles

| Double | Use |
|--------|-----|
| Stub | Fixed return values |
| Fake | In-memory working impl |
| Mock | Interaction assertions |
| Spy | Record calls on real object |

---

## 13. Integration Tests

### 13.1 Structure and Organization

```text
tests/
  unit/
  integration/
```

Mark integration tests:

```python
import pytest

pytestmark = pytest.mark.integration


def test_sqlite_roundtrip(tmp_path) -> None:
    import sqlite3

    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO items (name) VALUES (?)", ("x",))
    conn.commit()
    row = conn.execute("SELECT name FROM items").fetchone()
    assert row[0] == "x"
    conn.close()
```

### 13.2 Selective Execution

```bash
pytest -m "not integration"
pytest -m integration
```

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
  "integration: tests that touch filesystem or database",
]
```

### 13.3 Real Dependencies

- Prefer temp SQLite files (`tmp_path`) over shared `loja.db`.
- For Postgres/MySQL in CI, use disposable containers and migrate schema each run.
- Never point integration tests at production data.

---

## 14. Load and Stress Tests

### 14.1 Tools

- **Locust** — Python-native load scripts.
- **hey** / **vegeta** — HTTP CLI load generators.
- **pytest-benchmark** — microbenchmarks in the test suite.

### 14.2 Load Benchmarks

```bash
python -m pip install locust
# locust -f scripts/locustfile.py --headless -u 50 -r 5 -t 1m
hey -n 1000 -c 20 http://127.0.0.1:5003/health
```

Define success criteria: p95 latency, error rate < 1%, no connection leaks.

### 14.3 Concurrency Tests

```python
from concurrent.futures import ThreadPoolExecutor


def test_counter_thread_safe() -> None:
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: increment(), range(100)))
    assert increment.__wrapped_total__ >= 100  # adapt to your API
```

Stress shared resources (DB writes, caches) under parallel callers.

---

## 15. Profiling and Diagnostics

### 15.1 CPU and Memory Profiling

```bash
python -m cProfile -o out.prof -m myapp.main
python -m pstats out.prof
python -m pip install memory_profiler
python -m memory_profiler scripts/hot_path.py
```

### 15.2 Diagnostic Tools

| Tool | Purpose |
|------|---------|
| `cProfile` / `pstats` | CPU hotspots |
| `tracemalloc` | Allocation tracing |
| `pdb` / `breakpoint()` | Interactive debug |
| `faulthandler` | Fatal error dumps |

```python
import tracemalloc

tracemalloc.start()
# ... workload ...
current, peak = tracemalloc.get_traced_memory()
print(f"current={current} peak={peak}")
tracemalloc.stop()
```

### 15.3 Performance Analysis

1. Reproduce with a realistic dataset.
2. Profile before changing code.
3. Fix the top hotspot; re-measure.
4. Commit the benchmark numbers in the PR description.

---

## 16. Benchmarks

### 16.1 Writing Benchmarks

```python
import timeit


def bench_join() -> float:
    return timeit.timeit(lambda: "".join(["a"] * 1000), number=10_000)
```

### 16.2 Sub-benchmarks

```python
import timeit


def run_cases() -> None:
    for size in (10, 100, 1000):
        stmt = f"sum(range({size}))"
        seconds = timeit.timeit(stmt, number=50_000)
        print(size, seconds)
```

### 16.3 Execution and Analysis

```bash
python -m timeit "sum(range(1000))"
python -m pytest tests/bench --benchmark-only
python -c "from scripts.bench import run_cases; run_cases()"
```

Compare against a baseline branch; reject unexplained regressions > 10% on hot paths.

---

## 17. Optimization

### 17.1 Principles

- Measure first (`cProfile`, benchmarks).
- Prefer algorithmic wins over micro-tweaks.
- Document trade-offs when optimizing for speed over clarity.

### 17.2 Common Optimizations

```python
# Good: pre-size / single pass
def total(prices: list[float]) -> float:
    return sum(prices)


# Bad: repeated concatenation in a loop
def bad_join(parts: list[str]) -> str:
    out = ""
    for part in parts:
        out += part
    return out


# Good
def good_join(parts: list[str]) -> str:
    return "".join(parts)
```

Use generators for large streams; cache pure expensive calls with `functools.lru_cache` when inputs are hashable.

### 17.3 Memory Optimization

- Stream rows (`cursor` iteration) instead of `fetchall()` on huge tables.
- Avoid holding duplicate dict copies of the same entities.
- Prefer `__slots__` or frozen dataclasses for millions of tiny objects.

### 17.4 Basic Performance

- Local variable lookups are faster than global; keep hot loops tight.
- Avoid N+1 queries: join or batch-load related rows.
- Do not guess: profile I/O before rewriting CPU paths.

---

## 18. Security

### 18.1 Essential Practices

- Never hardcode secrets (`SECRET_KEY`, DB passwords); use env vars.
- Validate and sanitize all external input.
- Use parameterized SQL only (never string-concatenate user data).
- Hash passwords (e.g. stdlib-compatible approaches / established libs); never store plaintext.
- Principle of least privilege on admin endpoints.

```python
import os

SECRET_KEY = os.environ["APP_SECRET_KEY"]
```

### 18.2 Tools

```bash
python -m pip install pip-audit
pip-audit
python -m pip install bandit
bandit -r src
```

### 18.3 Security at API Boundaries

```python
# Good: placeholders
conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,))

# Bad: SQL injection
conn.execute("SELECT * FROM usuarios WHERE email = '" + email + "'")
```

- Do not return password hashes or secret keys in JSON health/debug payloads.
- Disable debug mode in production.
- Protect destructive admin routes with authz.

---

## 19. Code Patterns

### 19.1 Early Return

```python
# Good
def create_user(payload: dict[str, str]) -> int:
    if not payload.get("email"):
        raise ValueError("email required")
    if not payload.get("senha"):
        raise ValueError("senha required")
    return persist_user(payload)


# Bad: deep nesting
def create_user_bad(payload: dict[str, str]) -> int | None:
    if payload.get("email"):
        if payload.get("senha"):
            return persist_user(payload)
        else:
            return None
    else:
        return None
```

### 19.2 Separation of Concerns

- HTTP layer: parse request, map status codes.
- Service layer: business rules.
- Persistence layer: SQL only.

### 19.3 DRY

Extract duplicated validation and row-mapping helpers. Stop abstracting at two similar call sites if a third is speculative.

### 19.4 Variable Scope

Declare variables close to use; avoid module-level mutable globals for request state.

---

## 20. Dependency Management

### 20.1 Principles

- Standard library first.
- Prefer maintained packages with clear licenses.
- Pin versions in production (`flask==3.1.1`).
- Minimize the dependency graph.

### 20.2 Commands

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
pip-audit
python -m pip list --outdated
python -m pip cache purge
python -m pip check
```

Commit lock-style freezes or pinned requirements used by CI and Docker builds.

---

## 21. Comments and Documentation

### 21.1 Code Comments

Comment **why**, not what.

```python
# Refund window is 7 days per finance policy FN-14
DEADLINE_DAYS = 7
```

### 21.2 API Documentation

Use PEP 257 docstrings on public functions and classes.

```python
def apply_discount(amount: float, rate: float) -> float:
    """Return amount after applying a fractional discount rate.

    Args:
        amount: Gross value (>= 0).
        rate: Fraction in [0, 1].

    Returns:
        Net amount after discount.
    """
    if amount < 0 or not 0 <= rate <= 1:
        raise ValueError("invalid amount or rate")
    return amount * (1 - rate)
```

### 21.3 Package Documentation

- Module docstring at top of each package `__init__.py` describing the public surface.
- Keep README with run, test, and env setup commands.
- Generate API docs with `pydoc` or Sphinx when the surface grows.

```bash
python -m pydoc myapp.pricing
```

---

## 22. Database

### 22.1 Approach

| Approach | When |
|----------|------|
| Raw SQL + `sqlite3` | Simple apps, full control |
| Query builder | Dynamic filters without full ORM |
| ORM | Complex graphs, migrations, teams already invested |

This guideline demonstrates **stdlib `sqlite3`** with parameterized SQL.

### 22.2 Connection and Driver

```python
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def connect(db_path: str) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

Parameterized queries (required):

```python
def get_user_by_email(conn: sqlite3.Connection, email: str) -> sqlite3.Row | None:
    cur = conn.execute(
        "SELECT id, nome, email, tipo FROM usuarios WHERE email = ?",
        (email,),
    )
    return cur.fetchone()


def create_product(
    conn: sqlite3.Connection,
    name: str,
    price: float,
    stock: int,
    category: str,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO produtos (nome, preco, estoque, categoria)
        VALUES (?, ?, ?, ?)
        """,
        (name, price, stock, category),
    )
    return int(cur.lastrowid)
```

### 22.3 Migrations

- Version schema changes as numbered SQL files (`migrations/001_init.sql`).
- Apply in order; record applied versions in a `schema_migrations` table.
- Never edit applied migrations; add a new one.

```bash
python scripts/migrate.py --database loja.db
```

### 22.4 Best Practices

- Always use `?` placeholders; never concatenate SQL.
- Index columns used in WHERE/JOIN.
- One connection per request/thread for SQLite; avoid `check_same_thread=False` without a lock.
- Use transactions for multi-step writes (order + items + stock).
- Fix N+1 with JOINs or `WHERE id IN (...)`.

---

## 23. Logs and Observability

### 23.1 Log Levels

| Level | Use |
|-------|-----|
| DEBUG | Detailed diagnostics |
| INFO | Lifecycle / business events |
| WARNING | Recoverable anomalies |
| ERROR | Operation failed |
| CRITICAL | Process cannot continue |

### 23.2 Structured Logs

```python
import json
import logging
import sys


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            payload["request_id"] = record.request_id
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
```

### 23.3 Logging Implementation

```python
import logging

logger = logging.getLogger(__name__)


def create_order(user_id: int, item_count: int) -> None:
    logger.info(
        "order_created user_id=%s item_count=%s",
        user_id,
        item_count,
        extra={"request_id": "req-123"},
    )
```

- Use `getLogger(__name__)`.
- Prefer `%s` lazy interpolation over f-strings in log calls.
- Never log secrets, tokens, or raw passwords.

### 23.4 Metrics and Observability

- Track latency, error rate, and throughput at HTTP/DB boundaries.
- Expose `/health` (liveness) and `/ready` (dependencies OK) without secrets.
- Keep metric label cardinality low (no raw user IDs as label values).

---

## 24. Golden Rules

1. **Simplicity** — smallest clear design that works.
2. **Explicit errors** — raise typed exceptions; never swallow failures.
3. **Tests** — unit-test domain logic; integration-test SQL and I/O.
4. **Documentation** — README + docstrings on public APIs.
5. **Measured performance** — profile before optimizing.
6. **Secure by default** — parameterized SQL, env-based secrets, least privilege.
7. **Stdlib first** — add dependencies only when they pay rent.

---

## 25. Pre-Commit Checklist

### Code

- [ ] `ruff format` applied
- [ ] `ruff check` with no critical findings
- [ ] Application imports/runs without errors

### Tests

- [ ] `pytest` passes
- [ ] Coverage >= 70% on critical domain/service code
- [ ] Integration tests run when persistence changed
- [ ] Benchmarks checked if hot paths changed

### Quality

- [ ] Errors handled explicitly (no bare except)
- [ ] Connections/files closed (`with` / context managers)
- [ ] No hardcoded secrets
- [ ] `pip-audit` clean for known vulns

### Documentation

- [ ] Public functions documented
- [ ] README run/test instructions updated
- [ ] Comments explain non-obvious rationale

### Docker

- [ ] Dockerfile pins `python:3.14.7-alpine3.24` (or current agreed tag)
- [ ] `docker compose up` starts cleanly
- [ ] App healthcheck passes inside the container

---

## 26. References

### Official Documentation

- [Python 3 Documentation](https://docs.python.org/3/)
- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/)
- [PEP 484 – Type Hints](https://peps.python.org/pep-0484/)
- [typing – Support for type hints](https://docs.python.org/3/library/typing.html)
- [sqlite3 – DB-API 2.0 for SQLite](https://docs.python.org/3/library/sqlite3.html)
- [logging – Logging facility](https://docs.python.org/3/library/logging.html)
- [Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [asyncio – Asynchronous I/O](https://docs.python.org/3/library/asyncio.html)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [The Zen of Python (PEP 20)](https://peps.python.org/pep-0020/)

### Industry Style Guides

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Google styleguide repository](https://github.com/google/styleguide)

### Essential Tools

- [pip](https://pip.pypa.io/)
- [pytest](https://docs.pytest.org/en/stable/)
- [Ruff](https://docs.astral.sh/ruff/)
- [mypy](https://mypy.readthedocs.io/)
- [pip-audit](https://pypi.org/project/pip-audit/)
- [bandit](https://bandit.readthedocs.io/)

### Framework / Stack (project reference)

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask 3.1.1 on PyPI](https://pypi.org/project/Flask/3.1.1/)
- [flask-cors](https://pypi.org/project/flask-cors/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

### Containers and Ops

- [Official Python Docker Image](https://hub.docker.com/_/python)
- [Docker Compose overview](https://docs.docker.com/compose/)

### Production Codebases

- [CPython](https://github.com/python/cpython)
- [Flask](https://github.com/pallets/flask)
- [requests](https://github.com/psf/requests)

### Community

- [Awesome Python](https://github.com/vinta/awesome-python)
- [Real Python](https://realpython.com/)
- [Python Discuss](https://discuss.python.org/)
