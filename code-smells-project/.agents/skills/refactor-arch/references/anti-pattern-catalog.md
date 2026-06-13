# Anti-Pattern Catalog

Use these patterns as investigation leads, not automatic findings and not an exhaustive list. Confirm behavior and cite exact lines. Read `issue-discovery.md` and create project-specific categories whenever a verified issue does not match this catalog.

## Severity Scale

- **CRITICAL:** exploitable security issue, data loss/corruption risk, broken correctness, or total collapse of separation of concerns.
- **HIGH:** strong MVC/SOLID violation that blocks isolation, testing, or safe change.
- **MEDIUM:** duplication, missing validation, inefficient access pattern, or inconsistent platform use.
- **LOW:** localized readability and maintainability issue.

## Catalog

### 1. Arbitrary Command Or Query Execution - CRITICAL

Signals: request data passed to SQL execution, shell execution, `eval`, dynamic import, or template execution.

Confirm: untrusted input reaches an execution sink without allowlisting and authorization.

Remediation: remove the endpoint or expose explicit authorized operations.

### 2. Injection Through String-Built Queries - CRITICAL

Signals: concatenation, interpolation, or format calls used to build SQL/NoSQL queries.

Confirm: external or database-derived values can reach the query text.

Remediation: parameterized queries or ORM predicates.

### 3. Exposed Secrets Or Sensitive Data - CRITICAL

Signals: credentials, tokens, secret keys, card data, passwords, or hashes in source, responses, or logs.

Confirm: the value is usable, sensitive, or establishes an unsafe pattern. Test fixtures clearly isolated from runtime may be lower severity.

Remediation: environment-backed secrets, redaction, secret rotation, safe serializers.

### 4. Broken Authentication Or Password Storage - CRITICAL

Signals: plaintext, MD5/SHA password hashing, reversible encoding, default passwords, predictable/fake tokens, no token verification.

Confirm: runtime authentication depends on the unsafe mechanism.

Remediation: Argon2/bcrypt/scrypt/PBKDF2, signed expiring tokens, explicit authorization.

### 5. God Class Or God Module - HIGH

Signals: one class/module owns routing, persistence, business rules, integration calls, configuration, and response formatting.

Confirm: unrelated reasons to change accumulate in the same unit.

Remediation: extract boundaries by responsibility and domain.

### 6. Business Logic In Interface Adapters Or Views - HIGH

Signals: route/UI/CLI/event/file handlers calculate totals, enforce domain transitions, coordinate multi-step state changes, or call integrations directly.

Confirm: logic is not presentation/input-adapter-specific and cannot be tested without interface/framework context.

Remediation: move use cases to Models/services/controllers; keep Views/interface handlers as adapters.

### 7. Global Mutable State Or Shared Connection - HIGH

Signals: module-level mutable caches/counters/connections, `global`, singleton state without lifecycle management.

Confirm: concurrent requests or tests can observe or mutate shared state unexpectedly.

Remediation: request scope, dependency injection, managed cache/database clients.

### 8. Missing Transaction Boundary - MEDIUM

Signals: one use case performs multiple dependent writes with separate commits or callbacks.

Confirm: a later failure leaves partial state.

Remediation: atomic transaction with rollback and post-commit side effects.

### 9. N+1 Query Pattern - MEDIUM

Signals: database query inside a loop over records, lazy relationship access during serialization.

Confirm: query count grows with result size.

Remediation: joins, eager loading, aggregation, or batch lookup.

### 10. Missing Or Duplicated Validation - MEDIUM

Signals: unchecked request fields, validation repeated across create/update routes, diverging allowed values.

Confirm: invalid input can fail late or equivalent flows enforce different rules.

Remediation: shared schema/validator at the transport boundary plus domain invariants.

### 11. Missing Pagination Or Unbounded Work - MEDIUM

Signals: `.all()`, full-store reads, unbounded loops/recursion/queues, reports or transformations built entirely in memory.

Confirm: operation cost grows without an appropriate bound or backpressure mechanism.

Remediation: pagination, limits, streaming, or database aggregation.

### 12. Scattered Error Handling - MEDIUM

Signals: repeated broad `try/except` or callbacks that ignore errors; raw exception text returned to clients.

Confirm: responses are inconsistent, errors leak details, or rollback/logging is unreliable.

Remediation: typed application errors and centralized boundary-specific error handlers.

### 13. Deprecated Or Obsolete API - MEDIUM

Signals: framework/library deprecation warnings, removed APIs, obsolete time/hash/query methods, dependency versions with known end-of-life.

Detection procedure:

1. Identify installed version from manifests and lockfiles.
2. Search source for APIs known to be deprecated in that version.
3. Confirm with runtime warnings, official migration notes already available in the environment, or library source/docstrings.
4. Report the exact call and modern replacement. If not verifiable, record it as a review note rather than a finding.

Examples to investigate, version permitting:

- SQLAlchemy legacy `Query.get()` versus `Session.get()`;
- naive UTC factories such as `datetime.utcnow()` when the codebase requires timezone-aware values;
- Node callback APIs where the selected library documents a supported promise replacement;
- framework startup/hooks removed in the installed major version.

Remediation: replace incrementally and add a regression test.

### 14. Contract Or Invariant Violation - Severity By Impact

Signals: implementation conflicts with tests/docs/schema, invalid state becomes representable, equivalent paths produce inconsistent results, or edge cases break expected behavior.

Confirm: establish the intended contract or invariant and a realistic violating path.

Remediation: centralize the invariant in the Model/use case and add regression coverage.

### 15. Resource Lifecycle Or Partial Failure - Severity By Impact

Signals: resources are opened without cleanup, errors/cancellation are ignored, retry duplicates effects, shutdown loses work, or multi-system operations leave partial state.

Confirm: trace failure, retry, cancellation, and shutdown paths.

Remediation: explicit lifecycle ownership, idempotency, compensation, cleanup, timeout, or atomic boundary appropriate to the technology.

### 16. Magic Values And Scattered Configuration - LOW

Signals: repeated thresholds, status strings, ports, paths, environment names, or business lists.

Confirm: the value represents configuration or a domain concept rather than a self-evident local literal.

Remediation: named constants, enums/value objects, or configuration module.

### 17. Ambiguous Naming And Built-In Shadowing - LOW

Signals: names such as `x`, `data`, `manager`, `id`, or `tmp` used across domains; language built-ins shadowed.

Confirm: the name obscures business meaning or increases misuse risk.

Remediation: domain-specific names.

### 18. Dead Code, Unused Imports, And Broad Catch - LOW

Signals: unused modules/helpers/constants, unreachable paths, bare catches.

Confirm: static inspection or tests show no legitimate use.

Remediation: remove dead code and catch only expected errors.

## Ordering Rules

Order by `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`. Within a severity, prioritize exploitability, data integrity, blast radius, and frequency.

Do not assign severity from the catalog title alone. Use the concrete impact in the audited project.
