# Audit Report Template

Use este template para gerar os relatórios da Fase 2.

---
ARCHITECTURE AUDIT REPORT
---
Project: {{project_name}}
Stack: {{language}} + {{framework}}
Files: {{file_count}} analyzed | {{line_count}} lines approx.

## Summary
CRITICAL: {{critical_count}} | HIGH: {{high_count}} | MEDIUM: {{medium_count}} | LOW: {{low_count}}

## Findings

{{#each findings}}
### [{{severity}}] {{title}}
File: {{file}}:{{line_start}}-{{line_end}}
Description: {{description}}
Impact: {{impact}}
Recommendation: {{recommendation}}

{{/each}}
---
Total: {{total_findings}} findings
---

Notes:
- Ordene findings por severidade decrescente.
- Use linhas exatas quando possível.
- Inclua pelo menos um finding por severidade sempre que aplicável.
- Se o projeto usa APIs deprecated, destaque isso como parte da auditoria.
