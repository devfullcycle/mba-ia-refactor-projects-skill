---
name: refactor-arch
description: Audita e refatora APIs legadas para MVC. Use quando o usuário pedir auditoria arquitetural, code smells, migração MVC ou invocar /refactor-arch em projetos Python/Flask ou Node/Express.
disable-model-invocation: true
---

# Skill: refactor-arch (auditoria + refatoração MVC)

Execute **em ordem** as três fases. Não pule etapas. Não modifique arquivos antes do gate da Fase 2.

## Referências (progressive disclosure)

Leia **on-demand** (não precisa carregar tudo de uma vez):

| Fase | Arquivo |
|------|---------|
| 1 | [project-analysis-heuristics.md](project-analysis-heuristics.md) |
| 2 | [anti-patterns-catalog.md](anti-patterns-catalog.md), [audit-report-template.md](audit-report-template.md) |
| 3 | [mvc-guidelines.md](mvc-guidelines.md), [refactoring-playbook.md](refactoring-playbook.md) |

---

## Fase 1 — Análise do projeto

1. Identifique **linguagem**, **framework** e **entrypoint** (`app.py`, `src/app.js`, etc.) lendo manifestos: `requirements.txt`, `pyproject.toml`, `package.json`.
2. Mapeie **banco de dados** (SQLite file, `:memory:`, URI em config).
3. Conte arquivos fonte relevantes (`.py`, `.js` excl. `node_modules`, `.venv`).
4. Descreva **domínio** a partir de rotas e entidades.
5. Imprima o resumo **exatamente** neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      ...
Framework:     ...
Dependencies:  ...
Domain:        ...
Architecture:  ...
Source files:  N analyzed
DB tables:     ... (ou N/A)
================================
```

Use heurísticas do arquivo `project-analysis-heuristics.md` quando tiver dúvida.

---

## Fase 2 — Auditoria

1. Leia `anti-patterns-catalog.md` e **varra o repositório** (Grep/Read) procurando sinais listados.
2. Para **APIs deprecated**: seção “Deprecated APIs” do catálogo — se nada se aplicar, inclua um finding **MEDIUM** ou **LOW** “N/A — nenhuma API deprecada detectada” com justificativa breve.
3. Produza o relatório **seguindo** `audit-report-template.md`:
   - Cada finding com **arquivo e intervalo de linhas** (ex. `models.py:24-31`).
   - Ordem **CRITICAL → HIGH → MEDIUM → LOW**.
   - Mínimo **5 findings** no total; pelo menos **1 CRITICAL ou HIGH**.
4. Imprima o relatório entre:

```
================================
ARCHITECTURE AUDIT REPORT
================================
...
================================
Total: N findings
================================
```

### Gate obrigatório (human-in-the-loop)

**PARE.** Não use ferramentas de edição (Write/Edit/patch) nem comandos destrutivos até o usuário responder explicitamente que deseja prosseguir com a Fase 3 (ex.: “y”, “sim”, “prosseguir”).

Mensagem sugerida:

`Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`

---

## Fase 3 — Refatoração MVC + validação

**Só execute após confirmação na Fase 2.**

1. Aplique `mvc-guidelines.md` e transformações de `refactoring-playbook.md` adequadas à stack detectada.
2. **Remova ou neutralize** superfícies críticas (ex.: execução SQL arbitrária, segredos hardcoded) — não deixe backdoors ativos.
3. Estrutura alvo (adaptar nomes ao projeto):
   - `config` / variáveis de ambiente para segredos
   - **Models** (persistência / entidades)
   - **Controllers** (orquestração / caso de uso)
   - **Views** (rotas HTTP, bindings)
   - **Error handling** centralizado
   - **Entry point** claro (`app.py` / `src/app.js`)
4. **Validação:**
   - Instale deps se necessário (`pip install -r requirements.txt` / `npm install`).
   - Suba a aplicação e verifique **boot sem erro**.
   - Teste **health** (se existir) e **pelo menos 2 endpoints de negócio** representativos (GET + POST ou fluxo principal).
5. Imprima:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
(tree resumido)

Validation
  ✓ Application boots without errors
  ✓ Endpoints verified: ...
================================
```

Se um teste falhar, **corrija** antes de declarar conclusão.

---

## Regras finais

- Preserve **comportamento observável** das rotas públicas sempre que possível (URLs e métodos).
- Prefira **queries parametrizadas** e **hash de senha** adequado à stack.
- Documente no relatório qualquer **breaking change** inevitável.
