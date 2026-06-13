---
name: refactor-arch
description: Analyze, audit, and refactor any software project toward an MVC architecture while preserving behavior, independent of language, framework, interface style, or known issue catalog. Use when Codex must discover an unfamiliar project's technology and contracts, identify both known and project-specific architecture/security/correctness/quality issues with exact evidence, generate an audit report, or restructure the project into clear Model, View, and Controller responsibilities.
---

# Refactor Architecture

Execute three sequential phases. Treat the project root as the current working directory unless the user provides another target.

## Mandatory Safety Gate

- During Phases 1 and 2, do not modify source code, tests, configuration, dependency manifests, lockfiles, generated artifacts, or any state/persistence used by the project.
- The only file that may be created before approval is the Phase 2 audit report under `reports/`.
- End Phase 2 by asking exactly: `Prosseguir com a Fase 3 e aplicar a refatoração? [s/n]`
- Stop and wait. Do not interpret the original request to run the skill as approval for Phase 3.
- Start Phase 3 only after an explicit affirmative answer received after the audit.
- Preserve unrelated user changes. Inspect `git status` before editing and never overwrite or revert them.

## Required References

Load only the references needed for the current phase:

- Phase 1: [agent-discovery.md](references/agent-discovery.md) and [project-analysis.md](references/project-analysis.md)
- Phase 2: [issue-discovery.md](references/issue-discovery.md), [anti-pattern-catalog.md](references/anti-pattern-catalog.md), and [report-template.md](references/report-template.md)
- Phase 3: [mvc-guidelines.md](references/mvc-guidelines.md) and [refactoring-playbook.md](references/refactoring-playbook.md)

## Phase 1 - Project Analysis

1. Inspect the repository and read the agent-discovery and project-analysis references.
2. Prefer an exploratory subagent for the first discovery pass when subagent support is available. Ask it to inventory stack, contracts, entry points, persistence/state, architecture, and high-risk paths.
3. Use `python <skill-dir>/scripts/project_inventory.py .` only as a fallback or normalization helper.
4. Treat all discovery output as preliminary. Investigate every unrecognized extension and manifest before finalizing the source count or stack.
5. Exclude generated, dependency, environment, cache, build, and VCS directories from source counts.
6. Detect all relevant languages, runtimes, frameworks or libraries, dependency/build tools, persistence mechanisms, domain, entry points, external interfaces, test commands, architecture, and existing boundaries.
7. Treat built-in detector results as candidates, never as the supported-technology list. When a technology is unknown, infer it from manifests, imports, build files, startup code, documentation, and repository conventions.
8. Derive the domain from public interfaces, entities, schemas, workflows, and README content. Mark uncertain conclusions as inference.
9. Identify the project's observable contracts: UI, CLI, HTTP/API, events/messages, scheduled jobs, library APIs, files, or other inputs/outputs.
10. Print this summary:

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Project:
Language:
Runtime/framework/libraries:
Dependencies:
State/persistence:
Domain:
Architecture:
Entry point:
Interfaces/contracts:
Source files:
Test/validation commands:
================================
```

Use `none`, `custom`, or `unknown` when appropriate; never force a known framework or persistence label. Do not continue until the source count and stack are supported by concrete evidence.

## Phase 2 - Architecture Audit

1. Read the issue-discovery guide, anti-pattern catalog, and report template.
2. Inspect all relevant source, configuration, dependency, migration, and test files.
3. Use the catalog as seed knowledge, not as a checklist or limit. Derive additional hypotheses from the project's own contracts, invariants, data flows, dependency graph, concurrency model, failure modes, and technology conventions.
4. Cross-check every hypothesis against actual behavior. Do not report a pattern from filename or keyword alone.
5. Search for deprecated APIs in every detected runtime, framework, library, and toolchain. Report them only when a modern replacement is known and the usage is verifiable.
6. Create findings with:
   - one severity from `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`;
   - exact project-relative file and line or tight line range;
   - concrete evidence and impact;
   - actionable recommendation.
7. Order findings by severity, then by impact within each severity.
8. Include at least five findings when evidence supports them. Never invent findings to reach a quota. Do not stop after five or after matching the catalog; continue until all material areas have been inspected.
9. Save the report using the template. Honor a user-provided report path; otherwise use `reports/audit-<normalized-project-name>.md`.
10. Print the report summary and the safety-gate question.
11. Stop and wait for explicit confirmation.

## Phase 3 - Refactoring

After explicit approval:

1. Read the MVC guidelines and refactoring playbook.
2. Inspect `git status` and record the pre-existing changes that must be preserved.
3. Build a refactoring plan mapping each accepted finding to a transformation and validation.
4. Refactor incrementally, starting with behavior-preserving extraction before security or behavioral changes.
5. Preserve every observable contract found in Phase 1 unless the audit explicitly identifies it as unsafe or incorrect and the user approved the change.
6. Follow the target boundaries:
   - configuration reads environment and exposes typed/defaulted settings;
   - models/entities describe domain data;
   - repositories/data access own persistence;
   - services own business rules and transactions;
   - controllers receive actions/input and coordinate application flow;
   - views present output and map the project's interface concerns, whether API, UI, CLI, event, file, or another delivery mechanism;
   - boundary handlers centralize errors appropriate to each interface;
   - entry point acts as composition root.
7. Add or update focused tests for changed behavior.
8. Validate in increasing scope:
   - syntax/import/module checks;
   - unit or existing test suite;
   - application boot;
   - contract smoke tests covering all original interfaces;
   - security regression checks for corrected critical findings.
9. If validation fails, diagnose and fix it before reporting completion. Do not hide failed checks.
10. Update the audit report with a Phase 3 section listing changes, validation commands, results, and remaining risks.

Print:

```text
================================
PHASE 3: REFACTORING COMPLETE
================================
New structure:
Findings resolved:
Validation:
Remaining risks:
================================
```

## Quality Rules

- MVC is the required target. Map Model, View, and Controller responsibilities to the technology actually found instead of requiring framework-specific names or folders.
- Prefer existing project conventions when they already provide a sound boundary.
- Adapt the depth of refactoring to the starting architecture; do not rebuild a well-organized application merely to rename folders.
- Treat all examples and catalog entries as illustrative, not exhaustive.
- Select remediations from evidence and the detected technology; do not force SQL, HTTP, authentication, or database patterns onto projects where they do not apply.
- Do not claim a contract works without exercising it or explaining why it could not be exercised.
- Do not claim zero anti-patterns remain unless a fresh audit supports that statement.
