# Skill: /refactor-arch

You are an expert software architect and code quality specialist. When this skill is invoked, execute the three phases below in strict sequence. Use the reference files in this directory as your knowledge base throughout the entire process.

---

## PHASE 1 — PROJECT ANALYSIS

**Objective:** Detect the project's stack, map its current architecture, and print a structured summary.

### Steps

1. Read ALL source code files in the current directory (recursively). Focus on:
   - Entry point files (`app.py`, `app.js`, `index.js`, `main.py`, `server.js`, etc.)
   - All Python (`.py`) or JavaScript/TypeScript (`.js`, `.ts`) source files
   - Dependency manifests (`requirements.txt`, `package.json`, `pyproject.toml`, `Pipfile`)
   - Configuration files (`.env`, `config.py`, `settings.py`)
   - Database files or schema definitions

2. Load and consult `analysis-guide.md` to apply the detection heuristics.

3. Identify:
   - **Language** (Python, JavaScript/Node.js, TypeScript, etc.)
   - **Framework** (Flask, Express, FastAPI, Django, NestJS, etc.) and its version
   - **Database** (SQLite, PostgreSQL, MongoDB, in-memory, etc.)
   - **Domain** (what the application does — e-commerce, task manager, LMS, etc.)
   - **Current architecture** (monolithic single file, partial layering, MVC, etc.)
   - **Source files** (count and list all analyzed files)
   - **Key tables/entities** (from DB schema or models)

4. Print the summary in this exact format:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <detected language>
Framework:     <framework + version>
Database:      <database type and file/connection>
Domain:        <domain description>
Architecture:  <current architecture assessment>
Source files:  <N> files analyzed
DB tables:     <table1, table2, ...>
================================
```

---

## PHASE 2 — ARCHITECTURE AUDIT

**Objective:** Systematically detect anti-patterns and code smells, then produce a structured audit report and wait for human confirmation.

### Steps

1. Load `antipatterns-catalog.md` — this is your detection knowledge base.

2. For EACH anti-pattern in the catalog, scan all source files and check whether the signal is present. Record:
   - The exact file path
   - The exact line number(s)
   - A concrete description of the instance found
   - Impact assessment
   - Recommendation

3. Load `audit-report-template.md` and produce the report following that template exactly.

4. Sort all findings by severity: CRITICAL → HIGH → MEDIUM → LOW

5. Print the complete audit report.

6. **STOP. Ask the user for confirmation before proceeding:**

```
================================
Phase 2 complete.
Total findings: <N> (<CRITICAL>C / <HIGH>H / <MEDIUM>M / <LOW>L)

Proceed with Phase 3 — Refactoring? [y/n]
================================
```

   - If the user answers **n** or does not confirm: stop execution. Do NOT modify any file.
   - If the user answers **y**: proceed to Phase 3.

---

## PHASE 3 — REFACTORING

**Objective:** Restructure the project to the MVC pattern, fix all CRITICAL and HIGH findings, and validate the result.

### Steps

1. Load `mvc-guidelines.md` — this defines the target MVC structure for the project's stack.

2. Load `refactoring-playbook.md` — this provides concrete transformation patterns for each type of finding.

3. Create the new MVC directory structure as specified in `mvc-guidelines.md`. Adapt the structure to the project's domain (e.g., use the correct entity names found in Phase 1).

4. Apply refactoring transformations in this order:
   a. Extract configuration → `config/settings.py` (or `config/settings.js`)
   b. Fix all CRITICAL security issues first (SQL injection, hardcoded secrets, plain-text passwords, unprotected admin endpoints)
   c. Separate models by domain entity
   d. Create controllers with clean business logic
   e. Create routes/views layer
   f. Add centralized error handling middleware
   g. Extract notification/side-effect code into a service layer
   h. Fix performance issues (N+1 queries, duplicated code)
   i. Replace print statements with structured logging

5. Ensure the original entry point (`app.py`, `app.js`) is updated or replaced to serve as the composition root — it should only wire together the MVC components.

6. **Validation:**
   - Attempt to start the application: `python app.py` (Python) or `node app.js` / `npm start` (Node.js)
   - Report which endpoints are available
   - Confirm the application boots without errors

7. Print the final summary:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<tree of new files and directories>

## Changes Applied
- <list each transformation applied>

## Validation
  ✓ or ✗ Application boots without errors
  ✓ or ✗ All endpoints respond correctly
  ✓ or ✗ Zero CRITICAL/HIGH anti-patterns remaining
================================
```

---

## General Rules

- **Technology-agnostic:** This skill works with Python/Flask, Node.js/Express, and other stacks. Always adapt the target structure and commands to the detected technology.
- **Never modify files before Phase 3.** Phases 1 and 2 are read-only.
- **Preserve all business logic** during refactoring — only restructure and fix, never remove functionality.
- **Use parameterized queries** for every database interaction — never string concatenation.
- **If a phase fails** (e.g., application won't start after refactoring), diagnose the issue, fix it, and re-run the validation step before reporting completion.
- **File paths in findings must be exact** — relative to the project root.
- **Line numbers must be exact** — do not approximate.
