# Audit Report Template

Use project-relative paths and exact 1-based line references. Keep evidence concise and reproducible.

```markdown
# Architecture Audit Report

## Project

- **Name:** <project name>
- **Path:** <audited path>
- **Stack:** <languages + runtimes/frameworks/libraries + state/persistence>
- **Domain:** <domain description>
- **Architecture:** <current architecture>
- **Interfaces/contracts:** <HTTP/UI/CLI/events/library/files/etc.>
- **Source files analyzed:** <count and scope>
- **Generated at:** <ISO timestamp>

## Summary

| Severity | Count |
|---|---:|
| CRITICAL | <n> |
| HIGH | <n> |
| MEDIUM | <n> |
| LOW | <n> |
| **Total** | **<n>** |

## Findings

### [CRITICAL] <Finding title>

- **Location:** `<relative/path:line-line>`
- **Category:** <catalog anti-pattern or project-specific issue category>
- **Evidence:** <what the code does>
- **Impact:** <concrete security, correctness, performance, or maintenance impact>
- **Recommendation:** <specific remediation>

<repeat in severity order>

## Deprecated API Review

- **Checked:** <manifests/frameworks/APIs inspected>
- **Findings:** <finding references or "No verifiable deprecated API usage found">
- **Notes:** <uncertainty or version constraints>

## Discovery Coverage

| Area | Evidence inspected | Result |
|---|---|---|
| Observable contracts | <interfaces/tests/docs> | <findings or no verified issue> |
| MVC responsibilities | <flows/modules> | <findings or no verified issue> |
| Correctness/data integrity | <flows/state> | <findings or no verified issue> |
| Security/privacy | <trust boundaries/data> | <findings or no verified issue> |
| Reliability/concurrency/performance | <failure/scale/lifecycle paths> | <findings or no verified issue> |
| Technology-specific risks | <runtime/framework/library conventions> | <findings or no verified issue> |

## Proposed Refactoring

| Priority | Finding | Proposed transformation | Validation |
|---:|---|---|---|
| 1 | <title> | <playbook transformation> | <test/check> |

## Phase 3 Approval

No source, configuration, dependency, generated artifact, or state/persistence files were modified during Phases 1 and 2.

Status: **AWAITING EXPLICIT APPROVAL**
```

After Phase 3, append:

```markdown
## Phase 3 Results

### Changes Applied

- <change mapped to finding>

### Validation

| Check | Command/request | Result |
|---|---|---|
| Syntax/import | `<command>` | PASS/FAIL |
| Tests | `<command>` | PASS/FAIL |
| Boot | `<command>` | PASS/FAIL |
| Contract smoke tests | `<requests/commands/actions/messages/etc.>` | PASS/FAIL |

### Remaining Risks

- <unresolved or unverified item>
```
