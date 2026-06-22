# Architecture Audit Report — Projeto 1

> Gerado pela skill `/refactor-arch` — Fase 2: Auditoria

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~850 lines of code
         app.py, controllers.py, models.py, database.py

## Summary
CRITICAL: 5 | HIGH: 3 | MEDIUM: 2 | LOW: 3
Total findings: 13

================================
PHASE 1: PROJECT ANALYSIS (recap)
================================
Language:      Python
Framework:     Flask 3.1.1
Database:      SQLite (file: loja.db)
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Flat Files — 4 arquivos sem separação MVC, todas as camadas misturadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

---

## Findings

### [CRITICAL] SQL Injection — String Concatenation em Queries
**ID:** AP-01  
**File:** `models.py`  
**Lines:** 17, 30, 37, 44, 70, 84, 106, 116, 145, 172, 206, 232, 275–285  
**Description:** Todas as queries SQL em `models.py` constroem strings via concatenação direta de variáveis. Exemplo (linha 17): `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))`. Na função `buscar_produtos()` (linha 275), a query dinâmica concatena o termo de busca do usuário: `query += " AND nome LIKE '%" + termo + "%'"`. Qualquer parâmetro de entrada pode alterar a semântica da query.  
**Impact:** Comprometimento total do banco — leitura, modificação ou exclusão de todos os dados. A autenticação pode ser bypassada com email = `' OR '1'='1`.  
**Fix:** PT-01  
**Recommendation:** Substituir toda concatenação por queries parametrizadas com `?` e tupla de parâmetros: `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`.

---

### [CRITICAL] Hardcoded Secret Key
**ID:** AP-02  
**File:** `app.py`  
**Lines:** 8  
**Description:** `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` — a chave secreta do Flask está hardcoded como literal de string no código-fonte. Este valor será commitado no repositório e visível a qualquer pessoa com acesso ao código.  
**Impact:** Um atacante pode forjar tokens de sessão e se passar por qualquer usuário, incluindo admin.  
**Fix:** PT-02  
**Recommendation:** Mover `SECRET_KEY` para variável de ambiente carregada via `python-dotenv`.

---

### [CRITICAL] Endpoints Administrativos Sem Autenticação
**ID:** AP-04  
**File:** `app.py`  
**Lines:** 48–57, 60–79  
**Description:** `/admin/reset-db` (linha 48) deleta todos os dados de todas as tabelas sem nenhuma verificação de autenticação. `/admin/query` (linha 60) executa SQL arbitrário do corpo da requisição sem autenticação — qualquer cliente HTTP pode enviar `{"sql": "DROP TABLE usuarios"}` e destruir o banco.  
**Impact:** Perda total de dados e execução arbitrária de SQL por qualquer chamador não autenticado.  
**Fix:** PT-09  
**Recommendation:** Mover rotas admin para um Blueprint protegido por decorator `@require_admin` que valide token JWT com perfil admin.

---

### [CRITICAL] Senhas Armazenadas em Texto Plano
**ID:** AP-05  
**File:** `database.py`, `models.py`  
**Lines:** `database.py:46–53`, `models.py:106–116`  
**Description:** Os usuários seed em `database.py` são inseridos com senhas em texto plano: `("admin@loja.com", "admin123", "admin")`. A função `login_usuario()` em `models.py` compara senhas como strings planas via query SQL: `WHERE senha = '" + senha + "'"`.  
**Impact:** Se o arquivo SQLite for acessado (ou via SQL injection), todas as senhas de usuários ficam imediatamente expostas.  
**Fix:** PT-04  
**Recommendation:** Usar `werkzeug.security.generate_password_hash` na criação e `check_password_hash` no login.

---

### [CRITICAL] SQL Injection em Query Builder Dinâmico
**ID:** AP-01  
**File:** `models.py`  
**Lines:** 275–285  
**Description:** `buscar_produtos()` constrói query dinamicamente concatenando strings do usuário: `query += " AND nome LIKE '%" + termo + "%'"` e `query += " AND categoria = '" + categoria + "'"`. O parâmetro `?q=` do endpoint `/produtos/busca` passa diretamente para a query.  
**Impact:** Exfiltração ou corrupção de dados via parâmetros do endpoint de busca.  
**Fix:** PT-01  
**Recommendation:** Usar `LIKE ?` com `params.append(f"%{termo}%")` e tupla no `cursor.execute(query, params)`.

---

### [HIGH] Secret Key e Debug Expostos no Health Check
**ID:** AP-06  
**File:** `controllers.py`  
**Lines:** 114–128  
**Description:** O endpoint `/health` retorna no JSON: `"secret_key": "minha-chave-super-secreta-123"`, `"debug": True` e `"db_path": "loja.db"`, expondo configuração interna a qualquer chamador.  
**Impact:** Atacante descobre a chave de assinatura, habilitando forja de sessões.  
**Fix:** PT-11  
**Recommendation:** Remover `secret_key`, `debug` e `db_path` do response do health check.

---

### [HIGH] Conexão de Banco Global e Mutável
**ID:** AP-07  
**File:** `database.py`  
**Lines:** 4–5, 8–10  
**Description:** `db_connection = None` é estado global mutável do módulo. A função `get_db()` usa `global db_connection` para inicializar uma única conexão compartilhada por todas as threads. SQLite com uma única conexão global não é thread-safe sob carga concorrente.  
**Impact:** Race conditions e corrupção de dados sob requisições concorrentes em produção.  
**Fix:** PT-05  
**Recommendation:** Substituir por conexão por requisição usando `flask.g` com `teardown_appcontext`.

---

### [HIGH] Side Effects de Notificação Dentro do Controller
**ID:** AP-08  
**File:** `controllers.py`  
**Lines:** 83–90, 107–112  
**Description:** `criar_pedido()` (linha 83) contém `print("ENVIANDO EMAIL/SMS/PUSH")` diretamente no controller após criar o pedido. `atualizar_status_pedido()` (linha 107) também tem prints de notificação. Essa lógica de notificação está misturada ao fluxo HTTP.  
**Impact:** Notificações não podem ser testadas, trocadas ou desabilitadas de forma independente.  
**Fix:** PT-08  
**Recommendation:** Extrair chamadas de notificação para `services/notification_service.py`.

---

### [MEDIUM] N+1 Queries nas Listagens de Pedidos
**ID:** AP-10  
**File:** `models.py`  
**Lines:** 175–205 (`get_pedidos_usuario`), 215–245 (`get_todos_pedidos`)  
**Description:** Ambas as funções executam `cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))` dentro de um loop por pedido, e depois `cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))` dentro de um loop por item. Para 10 pedidos com 3 itens: 1 + 10 + 30 = 41 queries.  
**Impact:** Tempo de resposta escala linearmente com dados; degradação severa em produção.  
**Fix:** PT-06  
**Recommendation:** Substituir loops aninhados por uma única query com `LEFT JOIN` em `pedidos`, `itens_pedido` e `produtos`.

---

### [MEDIUM] Código Duplicado entre get_pedidos_usuario e get_todos_pedidos
**ID:** AP-11  
**File:** `models.py`  
**Lines:** 175–245  
**Description:** `get_pedidos_usuario()` e `get_todos_pedidos()` compartilham ~35 linhas idênticas de lógica de loop e montagem do objeto pedido. A única diferença é a cláusula `WHERE usuario_id = ?`. Qualquer correção de bug deve ser aplicada nos dois lugares.  
**Impact:** Manutenção dobrada; funções vão divergir e criar comportamento inconsistente.  
**Fix:** PT-07  
**Recommendation:** Extrair função helper `_execute_pedidos_query(query, params)` compartilhada por ambas.

---

### [LOW] print() como Logging Operacional
**ID:** AP-13  
**File:** `controllers.py`, `app.py`, `models.py` (implícito)  
**Lines:** `controllers.py:14, 25, 75, 95, 107, 119`; `app.py:52, 59`  
**Description:** `print()` é usado em todo o código para eventos operacionais como "Produto criado", "Login bem-sucedido", "ERRO: ". Não há filtro por nível de log, sem output estruturado, sem integração com agregadores de log.  
**Impact:** Logs de produção são ruidosos e não filtráveis; impossível controlar verbosidade.  
**Fix:** PT-10  
**Recommendation:** Substituir todos os `print()` por `import logging; logger = logging.getLogger(__name__)`.

---

### [LOW] Magic Numbers na Lógica de Desconto
**ID:** AP-14  
**File:** `models.py`  
**Lines:** 257–263  
**Description:** `relatorio_vendas()` usa: `if faturamento > 10000`, `elif faturamento > 5000`, `elif faturamento > 1000` com multiplicadores `0.1`, `0.05`, `0.02` como literais sem nomes. Regras de negócio invisíveis no código.  
**Impact:** Regras não podem ser entendidas nem alteradas sem ler e modificar o código-fonte.  
**Fix:** PT-12  
**Recommendation:** Extrair `DISCOUNT_TIERS` para `config/settings.py` como constantes nomeadas.

---

### [LOW] Validação Inconsistente entre Criar e Atualizar Produto
**ID:** AP-12  
**File:** `controllers.py`  
**Lines:** `criar_produto: 53–65`, `atualizar_produto: 77–95`  
**Description:** `criar_produto()` valida `categoria` contra `categorias_validas` e valida comprimento do `nome`. `atualizar_produto()` não valida `categoria`, permitindo categorias inválidas na atualização.  
**Impact:** Integridade de dados inconsistente — criação válida, atualização pode corromper.  
**Fix:** Extrair `_validate_produto_input()` como helper compartilhado.  
**Recommendation:** Criar função de validação reutilizável chamada por ambos os endpoints.

---

```
================================
Phase 2 complete.
Total findings: 13 (5C / 3H / 2M / 3L)

Proceed with Phase 3 — Refactoring? [y/n]
> y
================================
```
