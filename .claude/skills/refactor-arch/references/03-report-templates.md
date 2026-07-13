# Templates de Saída — Seguir à Risca

Reproduza estes templates **exatamente**: mesma estrutura, mesmos rótulos, mesma ordem de seções,
mesmos separadores. A largura dos separadores é de **32 sinais de igual** (`====...`). Os campos
usam alinhamento por espaços para os valores ficarem em coluna. Não adicione, remova ou renomeie
seções. A única variação permitida é **omitir linhas de campos que não se aplicam** (Fase 1) e
**refletir o estado real** na linha de anti-patterns (Fase 3).

---

## Fase 1 — `PHASE 1: PROJECT ANALYSIS`

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem (+ runtime se relevante)>
Framework:     <framework + versão>
Dependencies:  <diretas principais, por nome, separadas por vírgula>
Database:      <engine + forma de acesso + nuances (ex.: in-memory)>
Domain:        <domínio (entidades principais)>
Architecture:  <resumo da organização atual em 1 linha>
Source files:  <N> files analyzed
DB tables:     <tabelas detectadas, separadas por vírgula>
================================
```

**Regras:**
- Omita a linha inteira de qualquer campo sem valor no projeto (ex.: projeto sem banco → sem
  `Database` e sem `DB tables`). Não escreva "N/A".
- Mantenha a ordem dos campos acima.

**Exemplo real (code-smells-project):**
```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors
Database:      SQLite (driver sqlite3, conexão global) — loja.db
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

---

## Fase 2 — `ARCHITECTURE AUDIT REPORT`

Este é o conteúdo **impresso no console** e **salvo** em `reports/audit-project-<N>.md` (idêntico).

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do projeto>
Stack:   <linguagem + framework>
Files:   <N> analyzed | ~<LOC> lines of code

Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

MVC Adherence: <score>/10 (<rótulo>)
  Models:       <presente | parcial | ausente> — <motivo curto>
  Views/Routes: <presente | parcial | ausente> — <motivo curto>
  Controllers:  <presente | parcial | ausente> — <motivo curto>
  Separation:   <ok | violada> — <motivo curto>

Findings

[SEVERIDADE] <Título do problema>
File: <arquivo>:<linhas>
Description: <o que é o problema>
Impact: <consequência>
Recommendation: <como corrigir>

[SEVERIDADE] <Título do próximo problema>
File: <arquivo>:<linhas>
Description: ...
Impact: ...
Recommendation: ...

================================
Total: <N> findings
================================
```

**Regras:**
- `MVC Adherence`: score de 0 a 10; rótulo sugerido — `Monolítico` (0–3), `Parcial` (4–7),
  `Aderente` (8–10). Cada camada marcada como presente / parcial / ausente; `Separation` como
  `ok` ou `violada`.
- `Findings`: ordenados por severidade decrescente (CRITICAL → HIGH → MEDIUM → LOW). Separe cada
  finding com uma linha em branco. As violações de MVC entram aqui como findings normais.
- `Total: <N> findings` = soma de todos os findings (deve bater com o `Summary`).
- Logo após imprimir o relatório no console, **peça a confirmação** (bloco abaixo). O texto de
  confirmação **não** faz parte do arquivo salvo.

**Gate de confirmação (somente no console, após o relatório):**
```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

---

## Fase 3 — `PHASE 3: REFACTORING COMPLETE`

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
<árvore de diretórios MVC gerada, no estilo tree>

Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  <linha de anti-patterns — ver regra>
================================
```

**Regra da linha de anti-patterns (reflete o estado real):**
- Se o loop resolveu tudo:
  ```
    ✓ Zero anti-patterns remaining
  ```
- Se sobraram findings após 3 loops:
  ```
    ⚠ <N> findings remaining after 3 loops:
       - [SEVERIDADE] <título> (<arquivo>:<linha>)
       - ...
  ```

**Regras adicionais:**
- `Application boots without errors` e `All endpoints respond correctly` só recebem `✓` se a
  validação real (subir app + bater endpoints) passou. Se algo falhou, **não** finalize como
  concluído — corrija e revalide.
- A árvore em `New Project Structure` deve refletir os arquivos realmente criados, com uma nota
  curta entre parênteses nos pontos-chave quando ajudar (ex.: `app.py (composition root)`).

**Exemplo de árvore (Python/Flask):**
```
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)
```
