---
name: refactor-arch
description: Automates legacy backend codebase migration to Model-View-Controller (MVC). It analyzes project tech stack, audits code smells and security vulnerabilities, generates a structured report, and executes sequential refactoring while validating runtime correctness. Works with Python/Flask and Node.js/Express.
---

# Refactor Arch

## Overview

This skill transforms monolithic, legacy, or partially organized Python/Flask and Node.js/Express codebases into highly structured, clean, and safe MVC (Model-View-Controller) projects. It operates in 3 sequential phases: Analysis, Audit, and Refactoring.

## Sequential Workflow

### Phase 1: Project Analysis

You must analyze the codebase structure, files, and dependencies to detect:
- Language & Runtime
- Framework Name & Version
- Database Engine
- Business Domain
- Current Architecture (Monolith without layers, Partially organized, etc.)

Use the heuristics described in [project_analysis.md](references/project_analysis.md) to detect these features.

Upon completion, print a structured text summary exactly like this:
```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      [Detected Language]
Framework:     [Detected Framework and Version]
Dependencies:  [List of core packages/dependencies]
Domain:        [E-commerce API / LMS / Task Manager / etc.]
Architecture:  [Short description of the current architecture structure]
Source files:  [Number of files] files analyzed
DB tables:     [Detected tables list]
================================
```

---

### Phase 2: Architecture Audit

Audit the codebase to find anti-patterns, security bugs, and quality issues.
1. You MUST iterate over EVERY source file in the project.
2. For each file, check against ALL anti-patterns listed in [anti_patterns.md](references/anti_patterns.md).
3. Find ALL architectural, security, and quality issues. Be exhaustive; do not stop at a minimum count.
4. You MUST include detection for deprecated APIs.
5. Generate a structured report following the exact format of [report_template.md](references/report_template.md).
6. Save the generated report in `reports/audit-project-[number].md`.
7. **PAUSE AND CONFIRM**: You MUST explicitly ask the user for confirmation before making any code modifications or moving to Phase 3.

---

### Phase 3: Refactoring & Validation

Once the user confirms (replies yes), proceed to re-architect and rewrite the codebase:
1. Adhere to the MVC guidelines in [architecture_guidelines.md](references/architecture_guidelines.md).
2. Utilize the transformation patterns with before/after examples in [refactoring_playbook.md](references/refactoring_playbook.md) to surgically refactor each code smell.
3. Structure the folders cleanly:
   - Extract configurations and secrets into `config/` (never hardcoded, utilize environment variables or config files).
   - Abstraia queries and data storage inside `models/`. Models must not import or depend on HTTP request/response contexts.
   - Separate HTTP request handling, validation, and orchestrations into `controllers/`.
   - Setup route paths inside a clean `routes/` or `views/` mapping.
   - Centralize exceptions using a middleware under `middlewares/`.
   - Maintain a clean entry point in the root (such as `app.py` or `server.js` acting as Composition Root).
4. **Validation**: Validate that the refactored codebase works.
   - Ensure the application boots without errors.
   - Test that **all original endpoints respond correctly** with correct JSON structures and status codes.
   - Confirm that all identified anti-patterns are resolved.

## References

Review these detailed files to execute each phase correctly:
- [Heurísticas de Análise de Projeto](references/project_analysis.md)
- [Catálogo de Anti-Patterns e Code Smells](references/anti_patterns.md)
- [Template do Relatório de Auditoria](references/report_template.md)
- [Guidelines da Arquitetura Alvo (MVC)](references/architecture_guidelines.md)
- [Playbook de Refatoração e Transformações](references/refactoring_playbook.md)
