# Catálogo de anti-patterns (≥8) + severidade

Use esta lista para **cruzar** o código na Fase 2. Cada item: **nome**, **severidade típica**, **sinais de detecção**.

---

## AP-01 — SQL injection por concatenação de strings

- **Severidade:** CRITICAL  
- **Sinais:** `.execute("... " + var)`, f-strings ou `%` em SQL dinâmico em Python; template strings JS montando SQL com `${input}` sem binding.  
- **Stacks:** SQLite raw, `mysql`, drivers sem parâmetros.

## AP-02 — Backdoor / SQL arbitrário via HTTP

- **Severidade:** CRITICAL  
- **Sinais:** endpoint que aceita `sql`, `query` no body e executa no banco; “admin query” sem autenticação forte.

## AP-03 — Segredos hardcoded

- **Severidade:** CRITICAL  
- **Sinais:** `SECRET_KEY = "..."`, `pk_live_`, `smtp` password literal, API keys em `config` objeto exportado, comentários “senha prod”.

## AP-04 — God Class / God Module

- **Severidade:** HIGH  
- **Sinais:** um arquivo/classe com DB init, SQL, rotas HTTP, regras de negócio e logging; centenas de linhas sem separação.

## AP-05 — Senhas fracas ou home-made crypto

- **Severidade:** HIGH  
- **Sinais:** MD5/SHA1 direto para senha; função “hash” custom com loops e `base64`; senhas em texto plano no banco.

## AP-06 — Vazamento de dados sensíveis em respostas

- **Severidade:** HIGH  
- **Sinais:** `to_dict()` inclui `password` ou hash; `/health` retorna `secret_key`; listagem de usuários com credenciais.

## AP-07 — Estado global mutável para negócio

- **Severidade:** HIGH  
- **Sinais:** `globalCache = {}` exportado e mutado; contadores globais de receita sem isolamento; singletons com estado inconsistente em testes.

## AP-08 — N+1 queries

- **Severidade:** MEDIUM  
- **Sinais:** loop `for x in items:` com query dentro; `forEach` disparando `db.get` por elemento sem JOIN/agregação.

## AP-09 — Callback pyramid / async aninhado excessivo

- **Severidade:** MEDIUM  
- **Sinais:** 4+ níveis de `})` em Node; falta de `async/await` ou Promise chain clara.

## AP-10 — Validação só na borda ou duplicada

- **Severidade:** MEDIUM  
- **Sinais:** mesma regra de categoria/status copy-paste em vários handlers; ausência de validação de tipos em JSON crítico.

## AP-11 — Exceções genéricas / `except:`

- **Severidade:** LOW a MEDIUM  
- **Sinais:** `except:` sem tipo; `except Exception` engole erro sem log estruturado.

## AP-12 — Magic numbers e debug em “produção”

- **Severidade:** LOW  
- **Sinais:** `if faturamento > 10000` sem constante nomeada; `print` de PII; `DEBUG=True` default.

---

## APIs deprecated (obrigatório verificar)

Procure evidências **concretas** no repo. Exemplos de busca:

| Stack | Padrão / grep | Se encontrado |
|--------|----------------|---------------|
| Node | `require('util').isArray` (legado), `new Buffer(` | Preferir `Array.isArray`, `Buffer.from` |
| Express | `req.param()` (removido/depreciado em favor de `req.params`/`req.query`) | Reportar MEDIUM |
| Python | `datetime.utcnow()` (Flask/SQLAlchemy — comportamento “naive” UTC) | Sugerir `datetime.now(timezone.utc)` onde aplicável |
| Python | `hashlib.md5` para senhas | Tratar como AP-05 (HIGH), não só deprecated |

Se **nenhuma** API deprecada for encontrada após busca razoável, adicione um finding:

- **[MEDIUM ou LOW] Deprecated APIs — N/A**  
  Description: “Nenhum uso confirmado de APIs marcadas como deprecated nas fontes consultadas; verificação: …”

---

## Distribuição esperada no relatório

- Pelo menos **1 CRITICAL ou HIGH** por projeto realista legado.  
- Mínimo **5 findings** no total (podem incluir N/A de deprecated se necessário, preferir achados reais).
