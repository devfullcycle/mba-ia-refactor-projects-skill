# Validation Protocol (Phase 3, Step 0 and Step 3)

The refactor is only "complete" when you have **observed** the refactored app booting and answering every original endpoint. Never report a ✓ you did not see in command output.

## 1. Baseline capture (before touching any file)

1. Install dependencies if missing, in the project's usual place (`pip install -r requirements.txt` inside an existing/new `.venv`; `npm install`). Do not commit them.
2. Run prerequisites documented by the project (e.g., `python seed.py`).
3. Boot the **original** app in the background and wait until it answers:
   ```bash
   python app.py > /tmp/refactor-arch-before.log 2>&1 &      # or: npm start
   for i in $(seq 30); do curl -s -o /dev/null http://localhost:<port>/ && break; sleep 0.5; done
   ```
   Use any route from the inventory as the readiness probe if `/` is not defined (any HTTP status counts as "up").
4. For **every** route of the Phase 1 inventory, send:
   - one happy-path request (use seed data IDs/credentials; create resources before reading/updating/deleting them), and
   - one error-path request where applicable (unknown ID → 404, missing required field → 400, bad credentials → 401).
5. Record for each request: method, path, body sent, status code, top-level response keys (or `text` for plain-text bodies). Keep this list in the conversation (or a temp file outside the project) — it is the contract to compare against.
6. Stop the server **by port**, not by process name (debug reloaders spawn children):
   ```bash
   kill $(lsof -tiTCP:<port> -sTCP:LISTEN) 2>/dev/null
   ```
7. Remove database files created by the run (e.g., `loja.db`, `instance/tasks.db`) so both runs start from the same state. In-memory DBs need nothing.

Order destructive requests (DELETE, reset) last so they do not invalidate later requests.

## 2. Boot check (after refactor)

- Start with the **original run command** (`python app.py`, `npm start`). Also run the project's prerequisite scripts (seed) if they exist — they must still work.
- Pass criteria: the process stays up, the log has no traceback / unhandled rejection, the readiness probe answers.
- For Python, additionally run `python -W error::DeprecationWarning -c "import app"`-style import check, or boot with `-W default` and confirm no deprecation warnings originate from project files.

## 3. Endpoint check

Re-send the exact baseline request set to the refactored app and compare:

| Compare | Rule |
|---|---|
| Status code | Must be equal |
| Top-level response keys / envelope | Must be equal |
| Values | Equal for deterministic data (counts, names, totals); ignore timestamps and generated IDs |
| Allowed differences | Only those listed as **Intentional behavior changes** (security fixes: password/secret fields removed, admin endpoints now 403 without token, injection payloads no longer succeed, 500 on special characters now 2xx/4xx) |

Also send the security probes that motivated CRITICAL findings and confirm they are now neutralized, e.g.:
- SQL injection: login with `"' OR 1=1 --"` → 401, search with `') OR 1=1 --` → empty/normal result, names with apostrophes → 201.
- Secrets: `/health` (or equivalent) no longer returns secret/config values.
- Authorization: for **every** operation listed in the AP-04 Recommendation of the report, run the matrix: anonymous → 401 (403 for a static admin-token guard), authenticated non-privileged → 403 (apps with users; for owner-or-admin guards, a *different* non-admin user), the account owner → baseline status (owner-or-admin guards), admin → the baseline status/body. For apps with login, also replay the account-takeover chain (change another user's — the admin's — password/email without being them or an admin, then log in with it): it must fail at the update. Obtain tokens through the app's own login (seed users) or the configured admin token. A guarded operation missing from the matrix, or answering 2xx anonymously, fails the validation.

For baseline comparison, replay guarded operations **with authorized credentials**. The happy-path contract must still match the baseline for an authorized caller.

Present the comparison as a table: `METHOD PATH | before | after | result`.

## 4. Anti-pattern re-scan

Re-run the catalog's quick grep pack on the refactored code. Expected:
- AP-01: no literal secrets (only `os.environ` / `process.env` reads and safe dev defaults)
- AP-02: no SQL built with `+`, f-strings or template literals containing user data
- AP-03: no file mixing routes + SQL + rules
- AP-09: no `global`, no module-level mutable caches
- AP-16: no bare `except:`; no per-route catch-all
- AP-17: deprecated APIs from the report are gone
- AP-22: no `print`/`console.log` in request paths (startup banner via logger is fine)

List any accepted residual with a reason (e.g., "`print` kept in seed.py — CLI script output").

## 5. Cleanup

- Stop every server you started (by port).
- Delete DB files and logs created by validation runs.
- Do not leave `.venv/`, `node_modules/` or `*.db` staged for commit (check `.gitignore`).

## 6. Failure handling

If the boot or any endpoint check fails: read the traceback, fix the code, and re-run §2–§4. Up to 3 iterations. If still failing, mark the corresponding line with ✗ in the Phase 3 summary and explain what is broken — partial honesty beats a false ✓.
