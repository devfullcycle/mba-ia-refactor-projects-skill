# Template de Relatório — Fase 2 (Auditoria)

Dois artefatos: (1) bloco de resumo no terminal, (2) arquivo Markdown em `reports/`.

## 1. Bloco de resumo no terminal

```
================================
PHASE 2: CODE AUDIT
================================
Project:      code-smells-project
Files audited: 4 files, ~800 LOC
Findings:     12 total (3 CRITICAL, 4 HIGH, 3 MEDIUM, 2 LOW)

CRITICAL:
  [SEC-01] SQL Injection          controllers.py:24,31
  [SEC-02] Hardcoded credentials  database.py:5
  [SEC-03] Weak crypto           models.py:47

HIGH:
  [ARCH-01] Business logic in Controller  controllers.py:15-42
  [ARCH-02] Data access in Controller    controllers.py:18,26,35
  [QUAL-02] Missing input validation     controllers.py:16,25
  [SEC-04] Unauthenticated route        controllers.py:52

MEDIUM:
  [QUAL-01] God Class          controllers.py (420 LOC)
  [QUAL-03] Generic error handling  app.py:38
  [PERF-01] N+1 queries       models.py:58-62

LOW:
  [QUAL-06] No migrations
  [QUAL-07] Hardcoded config  app.py:3, database.py:5

================================
Status: Awaiting user confirmation before Phase 3
================================
```

Regras do bloco:
- Agrupar por severidade (CRITICAL → LOW), depois por ID.
- Cada linha: `[ID] Descrição  arquivo:linha` (ou `arquivo (N LOC)` para God Class).
- Se nenhum achado numa severidade, omitir o bloco da severidade.
- Linha final sempre indica status: "Awaiting confirmation" ou "Confirmed — proceeding to Phase 3".

## 2. Arquivo `reports/audit-<projeto>.md`

```markdown
# Audit Report — <projeto>

> Gerado pela skill `refactor-arch` (Fase 2 — Auditoria).
> Data: <YYYY-MM-DD> | Raiz: <caminho> | Baseado na análise de: `reports/analysis-<projeto>.md`

## 1. Resumo

| Métrica | Valor |
|---|---|
| Arquivos auditados | <n> arquivos, ~<N> LOC |
| Total de achados | <n> |
| CRITICAL | <n> |
| HIGH | <n> |
| MEDIUM | <n> |
| LOW | <n> |

## 2. Achados detalhados

Cada achado segue o formato abaixo, ordenado por severidade (CRITICAL primeiro) e depois por ID.

---

### [CRITICAL] SEC-01 — SQL Injection

**Onde:** `controllers.py:24`, `controllers.py:31`

**Evidência:**
```python
# controllers.py:24
cursor.execute(f"SELECT * FROM products WHERE id = {product_id}")

# controllers.py:31
cursor.execute("SELECT * FROM orders WHERE user_id = %s" % user_id)
```

**Impacto:** Entrada de usuário (`product_id`, `user_id`) é interpolada diretamente na query SQL, permitindo injeção de SQL arbitrário via parâmetros da URL ou body da requisição.

**Recomendação:** Usar parâmetros posicionais:
```python
cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
# ou com placeholders nomeados:
cursor.execute("SELECT * FROM products WHERE id = :id", {"id": product_id})
```

**Referência:** `references/anti-patterns.md` → SEC-01

---

### [HIGH] ARCH-01 — Lógica de negócio no Controller

**Onde:** `controllers.py:15-42`

**Evidência:**
```python
# controllers.py:15-42
def create_order():
    data = request.json  # sem validação
    total = sum(item['price'] * item['qty'] for item in data['items'])  # regra de cálculo
    if total > 1000:     # regra de negócio
        discount = total * 0.1
    # ... mais 20 linhas de lógica
    cursor.execute("INSERT INTO orders ...")
    return jsonify({"total": total})
```

**Impacto:** A função de rota contém: (a) cálculo de total, (b) regra de desconto, (c) acesso direto ao banco. Isso acopla transporte HTTP a regra de domínio, tornando impossível testar a lógica sem mockar HTTP e DB.

**Recomendação:** Extrair para `OrderService.calculate_total()` e `OrderService.create_order()`; controller só orquestra: `service.create_order(request.json)`.

**Referência:** `references/anti-patterns.md` → ARCH-01

---

*(Repetir formato para cada achado)*

## 3. Mapa de calor por arquivo

| Arquivo | CRIT | HIGH | MED | LOW | Total |
|---|---|---|---|---|---|
| `controllers.py` | 1 | 3 | 1 | 0 | 5 |
| `models.py` | 1 | 0 | 1 | 0 | 2 |
| `database.py` | 1 | 0 | 0 | 1 | 2 |
| `app.py` | 0 | 0 | 1 | 1 | 2 |

## 4. Achados por categoria

### Segurança
- SEC-01, SEC-02, SEC-03, SEC-04 — <resumo curto>

### Arquitetura
- ARCH-01, ARCH-02 — <resumo curto>

### Performance
- PERF-01 — <resumo curto>

### Qualidade
- QUAL-01 a QUAL-08 — <resumo curto>

## 5. Recomendações prioritárias

Ordem sugerida de correção (do mais crítico ao menos crítico):

1. **[CRITICAL]** Corrigir SQL Injection em `controllers.py:24,31` — parametrizar queries
2. **[CRITICAL]** Remover credenciais hardcoded de `database.py:5` — usar env vars
3. **[CRITICAL]** Substituir MD5 por bcrypt em `models.py:47`
4. **[HIGH]** Extrair lógica de negócio de controllers para services
5. **[HIGH]** Adicionar validação de entrada nas rotas
6. ...

## 6. Notas e limitações

- <o que não pôde ser auditado com confiança>
- <falsos positivos suspeitos>
- <dependências não instaladas que impediram verificação>
```

## 3. Regras de escrita

- **Todo achado tem arquivo:linha exato.** Sem linha, não é achado — vai para "Notas e limitações".
- **Código de evidência obrigatório.** Sempre mostre o trecho problemático (3-10 linhas).
- **Recomendação com exemplo.** Sempre inclua como deveria ser (snippet curto).
- **Não duplique.** Mesmo anti-pattern no mesmo arquivo = um achado com múltiplos locais.
- **Mapa de calor obrigatório.** Tabela por arquivo mostra onde a dívida técnica se concentra.
- **Sem modificar código.** Fase 2 só reporta e escreve o relatório. A confirmação do usuário é necessária antes de iniciar a Fase 3 (refatoração).

## 4. Nome do arquivo

`reports/audit-<nome-do-projeto>.md`, onde `<nome-do-projeto>` é o nome do diretório de trabalho.

- `code-smells-project` → `reports/audit-code-smells-project.md`

Se o arquivo já existir, **numere** (`audit-<projeto>-2.md`) e avise o usuário.
