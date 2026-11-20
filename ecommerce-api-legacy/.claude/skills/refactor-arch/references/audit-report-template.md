# Audit Report Template (Phase 2)

Render the report **exactly** in this structure. It is printed to the terminal and saved as Markdown, so it must read well in both.

## Rules

- Header banner lines are 32 `=` characters.
- `Files:` uses the same file count and LOC as Phase 1.
- Summary counts must match the findings below.
- Findings are ordered **CRITICAL → HIGH → MEDIUM → LOW**; within a severity, most impactful first (security exploits before structural problems), ties broken by file then line.
- Heading format: `### [SEVERITY] <AP-ID> <Title>` — title from the catalog, optionally specialized (e.g. `AP-02 SQL Injection in login`).
- `File:` is `path:line`, `path:start-end`, or a comma-separated list for grouped occurrences (`models.py:28, 49, 58-60`). Paths are relative to the project root.
- `Description:` states the concrete evidence (quote identifiers/values; never paste secrets in full — mask them, e.g. `'minha-chave-****'`).
- `Impact:` one or two sentences on the consequence.
- `Recommendation:` the fix, ending with the playbook reference `(T-xx)`.
- Write descriptions in the language of the project's README/domain (e.g., Portuguese for a pt-BR project). Keep headings and field labels in English.
- End with the totals banner and the confirmation question.

## Template

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <project folder name>
Stack:   <Language> + <Framework> <version> (<DB engine> via <driver/ORM>)
Files:   <N> analyzed | ~<LOC> lines of code
Architecture: <classification from Phase 1>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] AP-01 Hardcoded Credentials
File: app.py:7
Description: SECRET_KEY definido como literal `'minha-chave-****'`.
Impact: Qualquer pessoa com acesso ao repositório obtém o segredo; impossível rotacionar por ambiente.
Recommendation: Ler de variável de ambiente em `config/settings.py`; falhar ou gerar valor aleatório em dev. (T-01)

### [HIGH] AP-07 Business logic in route handlers
File: routes/task_routes.py:85-154
Description: ...
Impact: ...
Recommendation: ... (T-04)

<... one block per finding ...>

## Deprecated APIs
| Location | Deprecated API | Modern replacement |
|---|---|---|
| models/task.py:15 | `datetime.utcnow` | `datetime.now(timezone.utc)` |

<If none: "No deprecated API usage detected for <stack/version>.">

## Endpoint contract (to preserve in Phase 3)
| Method | Path | Handler |
|---|---|---|
| GET | /produtos | controllers.py:5 |

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
````

## Field-by-field example (good vs bad)

Bad (vague, no evidence):
```
### [HIGH] Bad code
File: models.py
Description: The code is messy.
```

Good:
```
### [CRITICAL] AP-02 SQL Injection
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140-166, 174-224, 279-281, 289-297
Description: Todas as queries são montadas por concatenação de strings com dados da requisição, ex.: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` (login).
Impact: `email = "' OR 1=1 --"` autentica como o primeiro usuário (admin); nomes com apóstrofo (`D'Agua`) quebram o INSERT com HTTP 500.
Recommendation: Usar queries parametrizadas (`?` placeholders) em uma camada de repositório. (T-02)
```
