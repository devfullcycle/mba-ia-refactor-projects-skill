# Audit Report — task-manager-api

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask (Flask-SQLAlchemy)
Files:   15 analyzed | ~1400 lines of code

Summary
CRITICAL: 4 | HIGH: 7 | MEDIUM: 5 | LOW: 4

Findings
```

### [CRITICAL] C1 — Passwords hashed with unsalted MD5
- **File:** `models/user.py:29` (`self.password = hashlib.md5(pwd.encode()).hexdigest()`), `models/user.py:32` (verify)
- **Description:** MD5 is broken and unsalted — identical passwords produce identical hashes, trivially reversed via rainbow tables. Combined with the 4-char minimum policy (`routes/user_routes.py:64`).
- **Impact:** Credential disclosure on DB leak.
- **Recommendation:** Hash with bcrypt (per-user salt); verify by constant-time comparison.

### [CRITICAL] C2 — Password hash exposed in every API response
- **File:** `models/user.py:21` (`'password': self.password` inside `to_dict()`)
- **Description:** `to_dict()` serializes the password hash. It is returned by `GET /users/<id>` (`routes/user_routes.py:33`), `POST /users` (`:85`), `PUT /users/<id>` (`:129`) and `/login` (`:209`). Only `GET /users` (`:14-24`) manually omits it — an inconsistency.
- **Impact:** Offline cracking; reveals shared passwords.
- **Recommendation:** Never serialize the password; drop the field from `to_dict()`.

### [CRITICAL] C3 — Hardcoded SMTP credentials (+ committed `.env`)
- **File:** `services/notification_service.py:7-10` (`self.email_user = 'taskmanager@gmail.com'`, `self.email_password = 'senha123'`), `.env:5-6` (committed, same creds)
- **Description:** Live-looking email credentials embedded in source and checked into git; `python-dotenv` is installed but never used.
- **Impact:** Account compromise; secrets in version history.
- **Recommendation:** Move to env via a config module; `.gitignore` `.env`; ship `.env.example`.

### [CRITICAL] C4 — Hardcoded SECRET_KEY (+ committed in `.env`)
- **File:** `app.py:13` (`app.config['SECRET_KEY'] = 'super-secret-key-123'`), `.env:1`
- **Description:** The signing key is a literal in source and identical in the committed `.env`, never loaded from env.
- **Impact:** Token/CSRF forgery.
- **Recommendation:** Load from env via a config module.

### [HIGH] H1 — Fake/placeholder authentication; no authorization anywhere
- **File:** `routes/user_routes.py:210` (`'token': 'fake-jwt-token-' + str(user.id)`), `models/user.py:34-38` (`is_admin()` defined but never called)
- **Description:** Login returns a hard-coded token string that **no** endpoint verifies. Every mutating endpoint (create/delete users, change roles, etc.) is open; anyone can `PUT /users/<id>` with `role: 'admin'`.
- **Impact:** Complete access-control failure.
- **Recommendation:** Add auth middleware/decorator; enforce roles; verify tokens.

### [HIGH] H2 — N+1 query: per-task user + category in list endpoints
- **File:** `routes/task_routes.py:42` (`User.query.get(t.user_id)`), `routes/task_routes.py:51` (`Category.query.get(t.category_id)`) inside the `for t in tasks` loop (`:16`)
- **Description:** For N tasks this issues 1 + 2N queries; relationships exist (`task.user`/`task.category`) but aren't eager-loaded.
- **Impact:** Latency degrades linearly with data.
- **Recommendation:** One query with `joinedload`, or a JOIN.

### [HIGH] H3 — N+1 query: per-user task count + per-user task fetch in reports
- **File:** `routes/user_routes.py:22` (`len(u.tasks)` per user), `routes/report_routes.py:56` (`Task.query.filter_by(user_id=u.id).all()` per user), `routes/report_routes.py:163` (per-category count)
- **Description:** Repeated per-row queries instead of grouped aggregates.
- **Impact:** O(rows) DB round-trips.
- **Recommendation:** A single `GROUP BY` aggregate query.

### [HIGH] H4 — Full-table scan to compute "overdue" repeatedly in Python
- **File:** `routes/task_routes.py:281-287`, `routes/task_routes.py:30-39`, `routes/report_routes.py:30-43`, `routes/report_routes.py:119-135`
- **Description:** `Task.query.all()` then Python loops to count `due_date < now`, in 4+ places — while `Task.is_overdue()` (`models/task.py:50`) exists but is never called.
- **Impact:** Pulls the whole table into memory; duplicated logic.
- **Recommendation:** One SQL `WHERE due_date < now() AND status NOT IN (...)`; reuse the canonical helper.

### [HIGH] H5 — Debug mode + wildcard binding
- **File:** `app.py:34` (`app.run(debug=True, host='0.0.0.0', port=5000)`)
- **Description:** Werkzeug interactive debugger enabled and bound to all interfaces.
- **Impact:** Remote code execution if reachable.
- **Recommendation:** Env-driven debug, off by default; loopback in dev.

### [HIGH] H6 — Wildcard CORS
- **File:** `app.py:15` (`CORS(app)`)
- **Description:** No origin allow-list; combined with no auth, any website can call the API.
- **Impact:** Cross-site abuse.
- **Recommendation:** Explicit origin allow-list.

### [HIGH] H7 — Bare `except:` clauses swallowing exceptions
- **File:** `routes/task_routes.py:62,137,204,236`; `routes/user_routes.py:130,149`; `routes/report_routes.py:186,207,221`; `utils/helpers.py:46,48,88`
- **Description:** Bare `except:` (catches `KeyboardInterrupt`/`SystemExit`) returns generic 500s and hides root causes; the date-parse `except:` silently treats *any* error as "bad date".
- **Impact:** Bugs masked; diagnosis impossible.
- **Recommendation:** One global error handler; catch specific exceptions.

### [MEDIUM] M1 — Fat routes / no controller or real service layer
- **File:** `routes/task_routes.py` (299 lines), `routes/user_routes.py` (211), `routes/report_routes.py` (223)
- **Description:** Routes import `db` and models directly and do validation + persistence + serialization inline. `services/` exists but holds only dead code (`NotificationService` is never imported).
- **Impact:** Logic untestable, duplicated, and spread across HTTP handlers.
- **Recommendation:** Introduce `controllers/` and a real `services/` layer; keep routes thin.

### [MEDIUM] M2 — Code duplication: the "overdue" rule ×6 and validation ×3
- **File:** `models/task.py:50-60`, `routes/task_routes.py:30-39,71-80,284-287`, `routes/report_routes.py:33-43,132-135`, `routes/user_routes.py:171-180`; validation in `models/task.py:38-48`, `utils/helpers.py:57-108` and inline in routes
- **Description:** Six divergent copies of the overdue rule; three sources of truth for status/priority validation — while canonical helpers (`is_overdue`, `validate_status`, `process_task_data`) are **never called**.
- **Impact:** Bugs hide in divergence; any rule change must touch many places.
- **Recommendation:** One canonical helper, actually used; delete copies.

### [MEDIUM] M3 — Misplaced responsibility: Category CRUD under the reports blueprint
- **File:** `routes/report_routes.py:157-223` (`@report_bp.route('/categories', ...)`)
- **Description:** A first-class resource (`/categories`) is registered on `report_bp`, mixing concerns with `/reports/*`.
- **Impact:** Confusing routing ownership; poor cohesion.
- **Recommendation:** Dedicated `category_routes` blueprint.

### [MEDIUM] M4 — Missing input validation (mixed coverage)
- **File:** `routes/report_routes.py:197` (no null-check on `data` → 500), `routes/report_routes.py:177-180` (no name/color format checks despite `is_valid_color` existing), `routes/task_routes.py:141,210` (`type(x) == list`), `routes/user_routes.py:124-125` (`active` not type-checked)
- **Description:** `marshmallow` is declared but unused; some endpoints validate thoroughly, others not at all.
- **Impact:** 500s on bad input; inconsistent defense.
- **Recommendation:** Validate at the edge with a schema; reject early with 400.

### [MEDIUM] M5 — [DEPRECATED] `datetime.utcnow()` + SQLAlchemy legacy `Model.query`/`Query.get`
- **File:** `datetime.utcnow()` at `models/user.py:14`, `models/task.py:15-16,52`, all routes, `utils/helpers.py:38`, `services/notification_service.py:35`; `Model.query.get()` at `routes/task_routes.py:67,117,158,188,195,227`, `routes/user_routes.py:29,94,136,155`, `routes/report_routes.py:105,192,213`
- **Description:** `datetime.utcnow()` is deprecated in Python ≥ 3.12 (use `datetime.now(timezone.utc)`); `Query.get()`/`Model.query` are the legacy SQLAlchemy 2.x interface (use `db.session.get()`/`select()`).
- **Impact:** Forward-incompatible; noisy deprecation warnings.
- **Recommendation:** Switch to timezone-aware `now()` and the 2.x session API.

### [LOW] L1 — Dead code
- **File:** `services/notification_service.py` (never imported), `models/task.py:38-50` (`validate_status`/`validate_priority`/`is_overdue` unused), most of `utils/helpers.py` (`format_date`, `calculate_percentage`, `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `is_valid_color`, `process_task_data` + constants)
- **Recommendation:** Wire the canonical helpers in or remove.

### [LOW] L2 — Magic numbers / repeated literals
- **File:** status list `['pending','in_progress','done','cancelled']` repeated (`routes/task_routes.py:110,177`, `models/task.py:39`, `utils/helpers.py:75,110`), role list repeated (`routes/user_routes.py:71,120`), priority bounds `1..5`, date format `'%Y-%m-%d'`
- **Recommendation:** Named constants/enums in one module, referenced everywhere.

### [LOW] L3 — `print()` as logger; verbose if/else boolean returns; mixed-language strings
- **File:** `routes/user_routes.py:83,89,147`; `routes/task_routes.py:149,153,219,234`; `utils/helpers.py:39`; `models/user.py:34-38`, `models/task.py:38-48`
- **Recommendation:** Use `logging`; replace `if c: return True else: return False` with `return c`.

### [LOW] L4 — Stale build artifacts + missing `.gitignore`
- **File:** `src/{config,controllers,middlewares}/__pycache__/*.pyc` (from an abandoned prior refactor), `instance/tasks.db` shipped in repo, no `.gitignore`
- **Recommendation:** Remove generated artifacts; add `.gitignore`.

```
================================
Total: 20 findings  (CRITICAL: 4 | HIGH: 7 | MEDIUM: 5 | LOW: 4)

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
================================
```
