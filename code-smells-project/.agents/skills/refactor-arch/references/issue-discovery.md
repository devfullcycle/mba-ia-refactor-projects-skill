# Open-Ended Issue Discovery

The anti-pattern catalog is a starting set of examples. It is never the boundary of the audit. Discover issues from the project itself, including issue types not named in any reference.

## Core Method

For each project:

1. Identify observable contracts and expected behavior.
2. Identify domain invariants and data that must remain correct.
3. Trace representative flows from input through decisions, state changes, integrations, and output.
4. Ask how each flow behaves for success, invalid input, failure, retry, concurrency, scale, and shutdown.
5. Inspect dependency direction and responsibility placement against MVC.
6. Compare implementation with the conventions and guarantees of the detected technologies.
7. Convert only verified risks into findings with exact evidence.

## Audit Dimensions

Inspect every applicable dimension. Add dimensions discovered from the project.

- **Correctness:** broken conditions, inconsistent state, wrong calculations, edge cases, contract violations.
- **Security and privacy:** trust boundaries, authorization, authentication, injection, secret/data exposure, unsafe deserialization, supply chain.
- **Architecture and MVC:** mixed Model/View/Controller responsibilities, hidden coupling, cycles, unstable boundaries, framework leakage.
- **Data integrity:** transactions, migrations, idempotency, ordering, duplicate processing, stale state, schema constraints.
- **Reliability:** error propagation, retries, timeouts, cancellation, cleanup, startup/shutdown, partial failure.
- **Concurrency:** races, shared mutable state, deadlocks, unsafe parallelism, thread/process assumptions.
- **Performance and scale:** complexity, repeated I/O, memory growth, unbounded work, caching correctness, hot paths.
- **Interfaces and compatibility:** API/UI/CLI/event/library contracts, versioning, validation, accessibility where applicable.
- **Dependencies and platform:** deprecated/unsupported APIs, vulnerable or incompatible dependencies, incorrect framework lifecycle use.
- **Operations:** configuration, observability, health/readiness, logging, deployment assumptions, recovery.
- **Testing and maintainability:** missing high-risk coverage, duplication, dead code, confusing naming, excessive complexity.

## Project-Specific Hypotheses

Generate hypotheses from evidence such as:

- comments, TODOs, error messages, and disabled code;
- repeated conditional rules or transformations;
- mismatches between docs/tests and implementation;
- calls whose return values/errors are ignored;
- resources opened without visible cleanup;
- state mutations across multiple modules or external systems;
- framework/library APIs used against their intended lifecycle;
- assumptions about ordering, uniqueness, timezone, encoding, locale, precision, or file paths;
- code paths with no validation or no corresponding tests.

Do not require a hypothesis to match a named catalog pattern. Use a clear project-specific category when needed.

## Evidence Standard

A finding must answer:

- What exact code or configuration creates the risk?
- Under what realistic condition does it matter?
- What behavior or quality attribute is affected?
- How should it be corrected in this technology and project?

Do not report style preferences as architecture issues. Do not infer exploitability or failure without a plausible path.

## Completion Rule

The audit is complete when all applicable dimensions and major flows have been inspected, not when a fixed finding count or catalog coverage is reached.
