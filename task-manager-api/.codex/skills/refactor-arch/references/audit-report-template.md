# Template do relatório de auditoria

Renderize este template completo durante a Fase 2. Substitua todos os placeholders das Fases 1 e 2, marque `Phase 3 Results` como `PENDING` sem inventar resultados e remova instruções auxiliares. Persista-o no diretório `reports/` da raiz do repositório de entrega antes de apresentar o checkpoint humano; essa deve ser a única escrita das Fases 1 e 2.

Use paths de evidência relativos à raiz da codebase e o caminho do relatório relativo à raiz do repositório de entrega. Confirme as linhas no código atual e ordene findings por `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`. Dentro da mesma severidade, ordene pelo impacto.

## Sumário do template

- Metadata e Project Analysis
- Public Contract Baseline e Summary
- Deprecated API Check e Findings
- Proposed Refactoring Plan e Expected MVC Target
- Risks, Human Gate e Phase 3 Results
- Regras de qualidade

````markdown
# Architecture Audit Report — <codebase-name>

## Metadata

- **Codebase root:** `<audited-scope-root>`
- **Delivery repository root:** `<repository-root-containing-reports>`
- **Version-control snapshot:** `<revision/status or unavailable>`
- **Audited source fingerprint:** `<revision plus diff hash, or inventory/content hashes; exclude this report>`
- **Preexisting changes:** `<summary from VCS or file inventory/hashes>`
- **Audited at:** `<ISO-8601 timestamp>`
- **Scope:** `<included source/config/test patterns>`
- **Exclusions:** `<vendor/cache/build/data patterns>`
- **Source files:** `<count using declared rule>`
- **Lines inspected:** `<exact count or not measured>`
- **Report path:** `reports/<resolved-report-name>.md`
- **Phase 1–2 filesystem changes:** `<this report only>`

## Project Analysis

| Attribute | Result | Evidence | Confidence |
|---|---|---|---|
| Language/runtime | <result> | `<path:lines or manifest key>` | HIGH/MEDIUM/LOW |
| Build/dependencies | <result> | `<evidence>` | HIGH/MEDIUM/LOW |
| Framework/interfaces | <result> | `<evidence>` | HIGH/MEDIUM/LOW |
| Persistence/integrations | <result> | `<evidence>` | HIGH/MEDIUM/LOW |
| Domain | <result> | `<evidence>` | HIGH/MEDIUM/LOW |
| Current architecture | <result> | `<evidence>` | HIGH/MEDIUM/LOW |
| Units/entry points | <units, files and discovered commands> | `<evidence>` | HIGH/MEDIUM/LOW |
| Tests | <framework/command/absent> | `<evidence>` | HIGH/MEDIUM/LOW |

## Public Contract Baseline

| Type | Identity | Handler | Location | Input/auth | Expected output/error/effect |
|---|---|---|---|---|---|
| `<HTTP/CLI/event/job/library/UI/file>` | `<operation identity>` | `<handler>` | `<path:start-end>` | `<essential input>` | `<essential contract>` |

> Marque contratos destrutivos ou externos para validação isolada; não os execute contra dados/serviços reais.

## Summary

| Severity | Count |
|---|---:|
| CRITICAL | <n> |
| HIGH | <n> |
| MEDIUM | <n> |
| LOW | <n> |
| **Total** | **<n>** |

**Acceptance check:** `<>= 5 verified findings: PASS/FAIL>`; `<>= 1 CRITICAL or HIGH: PASS/FAIL>`.

## Deprecated API Check

- **Status:** `<confirmed findings / no confirmed occurrence / candidates require version evidence>`
- **Versions inspected:** `<runtime and relevant packages>`
- **Sources checked:** `<manifest/lock/warnings/primary docs>`
- **Candidates not counted as findings:** `<symbol, location, missing proof>`

## Findings

### <F-001> — [<CRITICAL|HIGH|MEDIUM|LOW>] <title>

- **Catalog rule:** `<AP-NN — name>`
- **Location:** `<relative/path:start-end>`
- **Evidence:** `<concise, redacted evidence; never reproduce secrets>`
- **Description:** `<what happens and which responsibilities/data flows are involved>`
- **Impact:** `<concrete security, correctness, maintenance or performance effect>`
- **Recommendation:** `<technology-appropriate target behavior>`
- **Transformation:** `<TNN from the playbook or custom approved step>`
- **Validation:** `<specific test or observable proof of remediation>`
- **Confidence:** `<HIGH|MEDIUM|LOW and reason when not HIGH>`
- **Deprecated API proof:** `<effective version; primary source; replacement — omit for other findings>`

<!-- Repeat one section per verified finding. Do not add evidence-free findings. -->

## Proposed Refactoring Plan

| Order | Finding IDs | Transformation | Files/roles affected | Risk | Validation |
|---:|---|---|---|---|---|
| 1 | `<F-...>` | `<T...>` | `<config/model/controller/route/etc.>` | `<risk>` | `<test>` |

## Expected MVC Target

```text
<logical or physical tree adapted to the detected units; show configuration, models/domain,
 controllers/use cases, views/adapters, infrastructure, error mapping and bootstrap>
```

State the intended dependency direction, map View/Controller/Model roles for each unit and explain any native equivalent used instead of literal MVC folder names.

## Risks and Preconditions

- `<preexisting changes to preserve>`
- `<missing test/credential/infrastructure>`
- `<migration or compatibility risk>`
- `<operation that must use temporary data or a test double>`

## Human Gate

Phase 2 complete. No codebase files were changed. This report was saved at `<report-path>`.

**Checkpoint status:** `AWAITING HUMAN APPROVAL`

Para retomar em uma janela de contexto nova, invoque a skill, identifique este arquivo e autorize explicitamente a Fase 3, por exemplo: `Autorizo a Fase 3 conforme <report-path>`.

**Phase 2 complete. Autoriza executar a Fase 3 e modificar os arquivos conforme o plano apresentado? [y/n]**

## Phase 3 Results

**Status:** `<na Fase 2 usar PENDING; após a Fase 3 usar COMPLETE ou INCOMPLETE>`

> Na Fase 2, omitir as subseções abaixo e deixar somente `Status: PENDING — aguardando aprovação explícita e execução`. Após a aprovação, substituir a seção pendente pelos resultados no formato abaixo. Manter os findings e o plano da Fase 2 congelados; registrar a remediação separadamente em vez de reescrever o histórico.

### Changes

- **Report saved at:** `<path>`
- **Changed files:** `<list>`
- **New architecture:** `<summary and tree>`
- **Resolved findings:** `<IDs>`
- **Residual findings/risks:** `<IDs or none demonstrated>`

### Validation Evidence

| Check | Command/method | Result | Evidence |
|---|---|---|---|
| Restore/build/load | `<command>` | PASS/FAIL/SKIP | `<exit code/reason>` |
| Static analysis/types/lint | `<command>` | PASS/FAIL/SKIP | `<exit code/reason>` |
| Automated tests | `<command>` | PASS/FAIL/SKIP | `<counts/error>` |
| Unit boot/readiness | `<command + readiness + timeout or not applicable>` | PASS/FAIL/SKIP | `<log/exit/reason>` |
| Public contracts | `<runner/method>` | PASS/FAIL | `<passed/total and mismatches>` |
| Regression audit | `<method>` | PASS/FAIL | `<critical/high regressions and residuals>` |
| Scope/diff | `<available VCS diff or inventory/hash comparison>` | PASS/FAIL | `<summary>` |

### Contract Comparison

| Type | Identity | Before | After | Result |
|---|---|---|---|---|
| `<interface type>` | `<operation identity>` | `<contract>` | `<contract>` | PASS/FAIL |

### Final Status

`<COMPLETE only if MVC/equivalent roles, applicable boot/load and every original public contract passed; otherwise INCOMPLETE>`
````

## Regras de qualidade

- Mantenha o relatório verificável; não use `aproximadamente` para paths, linhas ou totais declarados exatos.
- Use um intervalo mínimo que prove o finding. Para fluxos em vários arquivos, liste todas as localizações essenciais.
- Não copie blocos grandes de código. Descreva a evidência ou inclua um trecho curto e redigido.
- Faça as contagens da tabela coincidirem com as seções de findings.
- Registre a checagem de deprecated APIs mesmo quando não houver finding.
- Não marque validação como `PASS` sem comando/observação executada; use `SKIP` com razão quando aplicável.
- Não altere os achados originais depois da refatoração. Preencha os resultados da Fase 3 para preservar o histórico.
