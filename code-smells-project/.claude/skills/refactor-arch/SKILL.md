---
name: refactor-arch
description: "Audit and refactor a backend codebase to the MVC (Model-View-Controller) pattern, technology-agnostic. Runs 3 sequential phases: (1) project analysis — detect language, framework, database, domain and current architecture; (2) architecture audit — cross the code against an anti-pattern catalog, emit a severity-ranked report with exact file:line, then STOP and ask for confirmation; (3) refactoring — restructure into Models / Views(Routes) / Controllers, fix the findings, and validate that the app boots and every original endpoint still responds. Use when the user runs /refactor-arch, asks to 'audit the architecture', 'find code smells / anti-patterns', 'refactor to MVC', or 'clean up this legacy API'."
argument-hint: "[--report <path>] [--audit-only]"
disable-model-invocation: true
---

# refactor-arch

You are acting as a **senior software architect** hired to rescue a legacy backend. You analyze, audit, and then — only with explicit human approval — refactor the project in the **current working directory** to the MVC pattern defined in this skill's references, without breaking its public behavior.

The skill is **technology-agnostic**: never assume a stack. Detect it (Phase 1) and pick the matching guidance from the references. Every reference file has sections per ecosystem (Python, Node.js/JavaScript, plus generic rules that apply to anything else).

## Arguments

`$ARGUMENTS` may contain:

- `--report <path>` — where to save the Phase 2 report (relative to the project root). Default: `audit-report.md` in the project root.
- `--audit-only` — run Phases 1 and 2, save the report, and stop. Never modify source files.

## Reference files — read them at the phase that needs them

| File | Read during | Purpose |
|---|---|---|
| `references/project-analysis.md` | Phase 1 | Heuristics to detect language, framework, DB, domain, architecture; how to inventory endpoints |
| `references/anti-patterns-catalog.md` | Phase 2 | The catalog (IDs, severity, detection signals, deprecated-API table) |
| `references/audit-report-template.md` | Phase 2 | The exact report format — follow it literally |
| `references/mvc-guidelines.md` | Phase 3 | Target architecture: layers, responsibilities, dependency rules, target trees per stack |
| `references/refactoring-playbook.md` | Phase 3 | Concrete before/after transformations, one per anti-pattern family |
| `references/validation-protocol.md` | Phase 3 (step 0 and final step) | Baseline capture, boot + endpoint verification, re-scan |

Paths are relative to this SKILL.md. Read a file fully the first time you need it; do not rely on memory of a previous run.

## Global rules (apply to every phase)

1. **No file is modified, created, moved, or deleted before the user confirms at the end of Phase 2.** Phases 1–2 are read-only (running read-only shell commands such as `ls`, `grep`, `wc`, `cat`, a dependency listing, or booting the *original* app to capture a baseline is allowed).
2. **Evidence over opinion.** Every finding cites `file:line` (or `file:start-end`) that you actually read. Never invent line numbers — re-open the file to confirm before writing the report.
3. **Preserve the public contract.** Routes (method + path), request field names, response envelope shapes, status codes for the happy path, and the documented run command (`python app.py`, `npm start`, …) must keep working. The only allowed contract changes are security fixes (e.g., no longer returning password hashes, protecting admin endpoints) — each must be listed under "Intentional behavior changes" in the Phase 3 summary.
4. **The audit report is binding on Phase 3.** Every Recommendation in the report is implemented in full, on every endpoint/file it names — Phase 3 never silently narrows a recommendation. Scope decisions (e.g., "is adding auth here worth the contract change?") are made **in Phase 2**, when writing the Recommendation; after the user confirms, the report is the work order. If Phase 3 discovers that a recommendation is wrong (a false positive proven by the baseline), correct the report explicitly with a dated note — never by leaving it unimplemented.
5. **Authorization rule (AP-04).** In Phase 2, the AP-04 Recommendation must list **explicitly, endpoint by endpoint** (`METHOD /path` + the condition, e.g. "only when the body changes `role`"), every operation that receives a guard. These operations are **always** in scope and must be guarded in Phase 3:
   - administrative endpoints (`/admin/*`), raw-SQL execution, bulk data wipes;
   - **privilege and account-state changes:** creating a privileged account (e.g. `role: "admin"`), changing a user's `role`, activating/deactivating an account (`active`, `enabled`, `status`), and deleting user accounts;
   - any other destructive operation the Description cites as part of the finding.
   Ordinary resource CRUD (e.g., tasks, categories, products) that is not named in the Recommendation stays public and goes to "Recommended follow-ups". Each guarded endpoint is an intentional behavior change: it must answer **401** without credentials (or 403 when the guard is a static admin token, T-17A), **403** for an authenticated non-privileged caller (when the app has users), and keep its original status/body for an authorized caller — implement it with T-17 and validate all three cases.
6. **Adapt to the starting point.** A single-file monolith needs a full split; a partially layered project needs targeted moves (e.g., extract business logic from routes into controllers, centralize error handling) — do not rewrite what already complies with `mvc-guidelines.md`.
7. **Stay inside the project directory.** Never touch the skill folder itself (`.claude/`), VCS metadata, lock files, virtualenvs, or `node_modules/`.
8. Print the phase banners exactly as shown below so the run is easy to follow in the terminal.

---

## Phase 1 — Project Analysis

Read `references/project-analysis.md`, then:

1. List source files (exclude the paths that the reference tells you to ignore) and count lines.
2. Detect **language** and **framework + version** from manifests (`requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`, `pom.xml`, …) and confirm with imports.
3. Detect **database**: engine, access style (raw driver / query builder / ORM), and table names (from DDL, ORM models, or migrations).
4. Infer the **business domain** from table names, route nouns, and seed data.
5. Classify the **current architecture** using the reference's scale (Monolithic / Partially layered / Layered) and note which MVC responsibilities live where today.
6. Build the **endpoint inventory** (method, path, handler `file:line`). This inventory is the contract that Phase 3 must preserve — keep it.
7. Determine the **run command**, port, and any prerequisite step (e.g., seed script).

Print:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <language + version constraint if known>
Framework:     <framework + version>
Dependencies:  <runtime deps, comma-separated>
Database:      <engine> via <driver/ORM>
Domain:        <one-line description (main entities)>
Architecture:  <classification> — <one-line justification>
Source files:  <N> files analyzed (~<LOC> lines)
DB tables:     <comma-separated>
Endpoints:     <N> routes
Run command:   <command> (port <port>)
================================
```

Then print the endpoint inventory as a compact table (`METHOD  PATH  -> file:line`). Continue to Phase 2 automatically.

---

## Phase 2 — Architecture Audit

Read `references/anti-patterns-catalog.md` and `references/audit-report-template.md`, then:

1. Go through **every catalog entry** and run its detection signals against **every source file** found in Phase 1. Use `grep -n` for the textual signals and read the surrounding code to confirm — a grep hit alone is not a finding.
2. Check the **Deprecated APIs** section of the catalog against the detected stack and dependency versions. If the runtime is available, confirm by running the app/tests with deprecation warnings enabled (e.g., `python -W default`, `node --trace-deprecation`).
3. For each confirmed problem, create a finding with: catalog ID + title, severity (from the catalog; you may raise/lower one level only with a written justification), exact `file:line`, description with the concrete evidence (quote the offending identifier/value), impact, and recommendation pointing to the playbook transformation ID.
4. Group repeated occurrences of the same anti-pattern into **one finding listing all locations**, unless they live in different layers and need different fixes.
5. Sort findings **CRITICAL → HIGH → MEDIUM → LOW**; within a severity, most impactful first (ties by file, then line).
6. Render the report **exactly** per `audit-report-template.md` and print it.
7. Save the report to the `--report` path (default `audit-report.md`). This is the only write allowed before confirmation, and it is a new file outside the source tree's modules — never overwrite source code here.

Sanity gates before printing (fix the report if any fails):
- At least one finding per catalog entry whose signal matched and was confirmed — do not silently drop findings.
- Every finding has a real `file:line`.
- Summary counts equal the number of findings per severity.
- Every Recommendation is concrete enough to be executed and verified. The AP-04 Recommendation lists each guarded operation as `METHOD /path` (+ condition), covering everything required by Global rule 5.

Then **STOP and ask**, using the `AskUserQuestion` tool when available (otherwise print the line and wait for the user's reply):

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

- `n` (or `--audit-only`): end the run. Print where the report was saved. Do not modify anything.
- `y`: continue to Phase 3.

**Never proceed to Phase 3 without an explicit "y" from the user in this conversation.**

---

## Phase 3 — Refactoring

Read `references/mvc-guidelines.md`, `references/refactoring-playbook.md`, and `references/validation-protocol.md`, then:

### Step 0 — Baseline (before touching code)
Follow `validation-protocol.md` §1: boot the **original** app, exercise every endpoint from the Phase 1 inventory (happy path + one error path each where applicable), and record method, path, status code, and the top-level response keys. Stop the server and remove any database file that the run created, so the refactored app starts from the same state.

### Step 1 — Plan
Write a short plan (print it, do not ask again): target directory tree from `mvc-guidelines.md` for the detected stack, and the list of playbook transformations you will apply, mapped to finding IDs. For partially layered projects, state explicitly which existing modules are kept, which are moved, and which are split.

Include a **Recommendation conformance table**: one row per finding → the exact change that implements its Recommendation. For AP-04, one row per guarded operation (`METHOD /path` + condition → guard → required role). Nothing in the report may be missing from this table.

### Step 2 — Execute
Apply transformations in this order (it minimizes broken intermediate states):

1. Configuration extraction (secrets/env) → `config` module.
2. Data layer: models / repositories with parameterized queries, transactions, N+1 fixes, deprecated API replacements.
3. Controllers: move business rules and orchestration out of routes/God classes.
4. Views/Routes: thin HTTP layer that only parses input, calls a controller, and formats the response.
5. Cross-cutting: centralized error handler, input validation, logging instead of print, security fixes (password hashing, sensitive field removal, admin protection).
6. Composition root / entry point: app factory that wires config → DB → models → controllers → routes; keep the original run command working.
7. Remove the now-empty legacy files and dead code; update the project README run instructions only if they changed; add new config variables to a `.env.example`.

Rules while executing:
- Use the playbook's patterns; adapt naming to the project's language and domain vocabulary (keep Portuguese names if the domain is in Portuguese, etc.).
- Do not add new third-party dependencies unless the playbook says the stack lacks a standard-library alternative; if you add one, pin it in the manifest.
- Keep every route path and method from the inventory.

### Step 3 — Validate
Follow `validation-protocol.md` §2–§4:
1. Boot the refactored app with the original run command — it must start without errors or tracebacks.
2. Re-run the baseline request set and compare: same status codes and response keys, except for the intentional behavior changes you listed.
3. Re-scan the code with the catalog's detection signals and confirm the findings are gone (list any accepted residuals with a reason).
4. **Recommendation conformance check:** re-read every Recommendation in the saved report and confirm, with `file:line` in the refactored code, that each one is implemented in full. For every AP-04 guarded operation, send three requests and record them in an authorization matrix: anonymous → 401 (403 for a static admin token), authenticated non-privileged user → 403 (when the app has users), authorized caller → original success status. Any gap is a ✗. Fix it and re-validate — it is not a follow-up.
5. If anything fails, fix and re-validate (up to 3 iterations); if still failing, report it honestly — never claim success that you did not observe.
6. Stop every server you started and delete database files created by the validation run.

Print:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<tree of the new layout, source files only>

## Findings addressed
<finding ID → transformation applied → file(s)>  (one line each)

## Intentional behavior changes
<list, or "None">

## Authorization matrix
<METHOD /path (condition) | anonymous | non-privileged | authorized>  (one line per AP-04 guarded operation, or "No AP-04 finding">

## Recommended follow-ups
<improvements beyond the report's Recommendations (e.g., auth on ordinary CRUD that the report did not name), or "None". Never a Recommendation from the report: those are mandatory>

## Validation
  ✓|✗ Application boots without errors (<command>)
  ✓|✗ All <N> endpoints respond as in baseline (<passed>/<N>)
  ✓|✗ Every report Recommendation implemented (<implemented>/<total>; AP-04 guards <guarded>/<named>)
  ✓|✗ Zero catalog anti-patterns remaining (<residuals or "none">)
================================
```
