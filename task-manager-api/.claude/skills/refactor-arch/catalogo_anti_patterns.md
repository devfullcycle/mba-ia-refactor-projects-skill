# 🚨 Catálogo de Anti-Patterns e APIs Obsoletas

Catálogo contendo 9 anti-patterns de código e arquitetura, classificados por severidade, com seus respectivos sinais de detecção.

| # | Anti-Pattern | Severidade | Sinais de Detecção no Código |
|---|---|---|---|
| 1 | **Hardcoded Secrets** | `CRITICAL` | Chaves de API, senhas de banco, `SECRET_KEY` ou tokens declarados diretamente em strings no código. |
| 2 | **SQL Injection Vulnerability** | `CRITICAL` | Concatenação direta de variáveis em queries SQL (`"SELECT * FROM users WHERE id = '" + id + "'"`). |
| 3 | **God File / God Class** | `CRITICAL` | Um único arquivo/classe (ex: `AppManager.js`, `models.py`) controlando banco, rotas, regras de negócio e HTML. |
| 4 | **Bypass de Camadas / Regras em Rotas** | `HIGH` | Handlers HTTP/routes executando queries SQL diretas, regras de cálculo complexas ou lógica de domínio. |
| 5 | **Callback Hell Assíncrono** | `HIGH` | Aninhamento profundo de callbacks (3+ níveis) em Node.js/JavaScript sem o uso de `async/await` ou `Promises`. |
| 6 | **Queries N+1 no Banco** | `MEDIUM` | Consultas SQL executadas dentro de laços de repetição (`for`/`forEach`) para buscar dados relacionados. |
| 7 | **Tratamento Inseguro de Exceções** | `MEDIUM` | Blocos `try/except` genéricos retornando mensagens brutas do sistema/stacktrace para a resposta HTTP (`res.status(500).send(err)`). |
| 8 | **APIs Deprecated / Obsoletas** | `MEDIUM` | Uso de funções descontinuadas pelos frameworks (veja a subseção abaixo). |
| 9 | **Logs e Print Statements Dispersos** | `LOW` | Uso excessivo de `print()` ou `console.log()` para depuração/rastreamento sem padronização ou logger oficial. |
| 10 | **Magic Numbers soltos pelo código** | `LOW` | Numeros mágicos (magic numbers) soltos pelo código. |
| 11 | **Nomenclatura ruins de variáveis** | `LOW` | Nomenclatura de variáveis ruins. |
| 12 | **Duplicação de código** | `MEDIUM` | Código duplicado. |

---

### ⚠️ Detecção de APIs Deprecated / Obsoletas

#### Python / Flask:
- ❌ `@app.before_first_request` (Removido no Flask 2.3+) → ✅ Utilizar `with app.app_context():` na inicialização.
- ❌ `json.loads(request.data)` → ✅ Utilizar `request.get_json()`.

#### Node.js / Express:
- ❌ `body-parser` (pacote legado separado) → ✅ Utilizar os middlewares nativos `express.json()` e `express.urlencoded()`.
- ❌ `res.sendfile()` → ✅ Utilizar o método moderno `res.sendFile()`.