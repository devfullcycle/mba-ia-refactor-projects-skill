# 03 — Audit Report Template

Phase 2 output MUST follow this exact format. Keep the `====` rulers, the header block, the Summary
line, the per-finding blocks, and the Total line. Findings are ordered **CRITICAL → HIGH → MEDIUM → LOW**.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <project folder name>
Stack:   <Language + Framework>
Files:   <N> analyzed | ~<rounded> lines of code

Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

Findings

[CRITICAL] <Pattern title>
File: <path>:<line>  (or <path>:<start>-<end>)
Description: <1-3 lines, quote the offending code minimally>
Impact: <why it matters / blast radius>
Recommendation: <the fix in one line>

[HIGH] <Pattern title>
File: <path>:<line>
Description: ...
Impact: ...
Recommendation: ...

[MEDIUM] ...

[LOW] ...

================================
Total: <n> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Rules

1. **Exact locations.** Every finding cites `path:line` or `path:start-end`. Use the real line numbers.
2. **One block per finding.** If a pattern recurs at many call sites (e.g. SQL injection ×20), you may
   either (a) list the top 3–5 worst sites as separate blocks, or (b) one block with a line range like
   `models.py:28,48-50,110-111,279-297`. Choose whichever is clearer; never omit the locations.
3. **Order within severity:** by file, then by line.
4. **Quote sparingly.** At most one short code excerpt inside Description; the location is the source of truth.
5. **Deprecated-API findings** use the same block, with `[MEDIUM] [DEPRECATED] <api>` as the title.
6. The Summary counts must equal the number of findings shown (grouped ranges count as 1).
7. Always end with the confirmation prompt — Phase 2 stops there.
8. When saving the report to disk (e.g. `reports/audit-project-1.md`), keep this same structure as
   Markdown: turn the `[SEVERITY] Title` lines into `### [SEVERITY] Title` headings and keep the
   `File:`/`Description:`/`Impact:`/`Recommendation:` fields. Add a top `# Audit Report — <project>`
   title.
