# Catálogo de Anti-Patterns (Fase 2)

Cada entrada traz: **severidade padrão**, **sinais de detecção** (textuais/grep e estruturais), **por que importa** e o **padrão do playbook** que corrige. Os sinais valem para qualquer linguagem; exemplos de grep cobrem Python e JavaScript.

## Escala de severidade

- **CRITICAL** — falha grave de segurança ou arquitetura: expõe dados sensíveis, permite execução arbitrária, ou viola totalmente a separação de responsabilidades (God Class).
- **HIGH** — forte violação de MVC/SOLID que dificulta manutenção e testes: regra de negócio em controller/rota, acoplamento sem DI, estado global mutável, autenticação falsa.
- **MEDIUM** — padronização, duplicação, performance moderada: N+1, validação ausente/duplicada, tratamento de erro inadequado, APIs deprecated.
- **LOW** — legibilidade: nomes ruins, magic numbers, imports não usados, logs com `print`.

> Regra de ajuste: rebaixe/eleve **no máximo um nível** quando o contexto justificar (ex.: credencial de *exemplo* em script de seed local → HIGH em vez de CRITICAL) e explique no finding.

## Índice

| ID | Anti-pattern | Severidade |
|---|---|---|
| AP-01 | SQL Injection (query por concatenação/interpolação) | CRITICAL |
| AP-02 | Credenciais / segredos hardcoded | CRITICAL |
| AP-03 | God Class / God File | CRITICAL |
| AP-04 | Exposição de dados sensíveis (senhas, segredos, cartão) | CRITICAL |
| AP-05 | Endpoint administrativo/destrutivo sem autenticação | CRITICAL |
| AP-06 | Armazenamento inseguro de senha (texto puro, MD5, hash caseiro) | CRITICAL |
| AP-07 | Regra de negócio em Controller/Rota (Fat Controller) | HIGH |
| AP-08 | Estado global mutável | HIGH |
| AP-09 | Acoplamento forte / ausência de Injeção de Dependência | HIGH |
| AP-10 | Operação multi-etapa sem transação / Callback Hell | HIGH |
| AP-11 | Autenticação falsa / token previsível | HIGH |
| AP-12 | Debug ativo / configuração de produção insegura | HIGH |
| AP-13 | Queries N+1 | MEDIUM |
| AP-14 | Validação de entrada ausente ou duplicada | MEDIUM |
| AP-15 | Tratamento de erros inadequado (bare except, vazamento de `str(e)`, sem handler central) | MEDIUM |
| AP-16 | Código duplicado (DRY) | MEDIUM |
| AP-17 | Integridade referencial ausente (registros órfãos) | MEDIUM |
| AP-18 | Uso de APIs deprecated | MEDIUM |
| AP-19 | Magic numbers / strings | LOW |
| AP-20 | Nomenclatura ruim | LOW |
| AP-21 | Imports não usados / código morto | LOW |
| AP-22 | Logging via `print`/`console.log` | LOW |

---

## CRITICAL

### AP-01 — SQL Injection
**Sinais de detecção**
- Query montada com `+`, f-string, `%`, `.format()` ou template literal contendo variáveis:
  - Python: `grep -nE "execute\(\s*(f[\"']|[\"'].*[\"']\s*\+)" ` ; `"... WHERE id = " + str(id)`; `f"SELECT ... {x}"`
  - JS: `` grep -nE "(run|get|all|query|exec)\(\s*(`[^`]*\$\{|[\"'][^\"']*[\"']\s*\+)" ``
- Cláusulas `LIKE '%" + termo + "%'` montadas com string.
- Endpoint que executa SQL vindo do request (`cursor.execute(dados["sql"])`) — também AP-05.

**Por que importa**: permite ler/alterar/apagar qualquer dado, bypass de login (`' OR '1'='1`).
**Correção**: Playbook **PB-01** (queries parametrizadas).

### AP-02 — Credenciais / segredos hardcoded
**Sinais de detecção**
- `SECRET_KEY = "..."`, `app.config["SECRET_KEY"] = "..."`, `password = '...'`, `dbPass`, `apiKey`, `pk_live_`, `sk_live_`, `smtp` + senha literal.
- `grep -niE "(secret|passw|pwd|pass|api[_-]?key|token|gateway).{0,20}[=:]\s*[\"'][^\"']{3,}" `
- Objeto/dicionário `config` com literais de credenciais; credenciais em classes de serviço (`self.email_password = 'senha123'`).

**Por que importa**: vazam em repositório, logs e backups; impossível rotacionar por ambiente.
**Correção**: **PB-02** (config via variáveis de ambiente + `.env.example`).

### AP-03 — God Class / God File
**Sinais de detecção**
- Um arquivo/classe que contém **3+ responsabilidades**: conexão/schema do banco, SQL, regra de negócio, rotas/HTTP, formatação.
- Classe com métodos como `initDb()` + `setupRoutes()` (ex.: `AppManager`).
- Módulo `models` único servindo vários domínios (produtos + usuários + pedidos + relatórios) com SQL e regras misturados.
- Entry point (`app.py`) definindo rotas com SQL inline.
- Arquivos > ~300 linhas ou funções > ~50 linhas com múltiplos níveis de callback/condicionais.

**Por que importa**: impossível testar em isolamento; qualquer mudança afeta tudo (viola SRP).
**Correção**: **PB-03** (separar por camada e domínio) + estrutura de `mvc-guidelines.md`.

### AP-04 — Exposição de dados sensíveis
**Sinais de detecção**
- Serialização que inclui senha/hash: `"senha": row["senha"]`, `'password': self.password` em `to_dict()`/JSON de resposta.
- Endpoint de health/info retornando `secret_key`, `debug`, caminho do banco, variáveis de ambiente.
- Log de dados de cartão/token/segredo: `console.log(\`... ${cc} ... ${config.paymentGatewayKey}\`)`.
- `SELECT *` retornado direto ao cliente para tabelas com colunas sensíveis.

**Por que importa**: vazamento direto de credenciais/PCI; viola LGPD.
**Correção**: **PB-04** (serialização explícita sem campos sensíveis + mascaramento em logs).

### AP-05 — Endpoint administrativo/destrutivo sem autenticação
**Sinais de detecção**
- Rotas `/admin/*`, `reset`, `query`, `delete-all`, `financial-report` sem verificação de identidade/papel.
- Handler que executa SQL arbitrário recebido no body.
- `DELETE FROM <tabela>` sem `WHERE` acionável por HTTP.

**Por que importa**: qualquer pessoa na rede pode destruir/extrair a base.
**Correção**: **PB-05** (guard/middleware de admin com token de config; desabilitado por padrão).

### AP-06 — Armazenamento inseguro de senha
**Sinais de detecção**
- Senha gravada como recebida (`INSERT ... senha ... VALUES (..., senha)`), comparação `WHERE senha = '...'`.
- `hashlib.md5(`, `hashlib.sha1(`, `sha256` sem salt para senha.
- "Hash" caseiro: base64, loops de concatenação (`badCrypto`), `substring` do resultado.
- Senha padrão atribuída silenciosamente (`p || "123456"`).

**Por que importa**: vazamento da base expõe todas as senhas (rainbow tables, reversível).
**Correção**: **PB-06** (`werkzeug.security` / `bcrypt` / `crypto.scrypt` com salt; migração de hashes legados).

---

## HIGH

### AP-07 — Regra de negócio em Controller/Rota (Fat Controller)
**Sinais de detecção**
- Handler HTTP com > ~30 linhas contendo cálculos, regras de status, estatísticas, montagem manual de dicionários por campo.
- Cálculos de domínio (descontos por faixa, "atrasado", taxas de conclusão) dentro de rotas.
- Rotas que chamam `db.session`/SQL diretamente + validam + formatam + notificam.
- Side-effects (e-mail/SMS/push) disparados no meio do handler.

**Correção**: **PB-07** (extrair para Controller + Model/Service).

### AP-08 — Estado global mutável
**Sinais de detecção**
- Python: `global <var>` dentro de funções; conexão de banco em variável de módulo (`db_connection = None` reatribuída); listas/dicts de módulo mutados.
- JS: `let cache = {}` / `let total = 0` em módulo e exportado; objetos mutados por vários módulos.
- `sqlite3.connect(..., check_same_thread=False)` compartilhado entre threads.

**Correção**: **PB-08** (conexão por request/escopo + objetos injetados).

### AP-09 — Acoplamento forte / sem Injeção de Dependência
**Sinais de detecção**
- Controllers importando e instanciando banco/serviços concretos diretamente (`from database import get_db` em controller; `new sqlite3.Database()` dentro da classe de negócio; `NotificationService()` criado dentro de rotas).
- Nenhum ponto de composição (composition root) — dependências são resolvidas por imports globais.
- Serviços instanciados mas nunca usados (camada morta).

**Correção**: **PB-09** (composition root + construtores recebendo dependências).

### AP-10 — Operação multi-etapa sem transação / Callback Hell
**Sinais de detecção**
- Sequência de `INSERT/UPDATE` relacionados (pedido + itens + estoque; matrícula + pagamento) sem `BEGIN/COMMIT/ROLLBACK` ou com `return` no meio.
- Callbacks aninhados 3+ níveis (`db.get(..., () => { db.run(..., () => { db.run(...` ).
- Contadores manuais para sincronizar callbacks (`pending--; if (pending === 0) res.json(...)`).

**Correção**: **PB-10** (async/await + transação atômica).

### AP-11 — Autenticação falsa / token previsível
**Sinais de detecção**
- `'fake-jwt-token-' + str(user.id)`, tokens derivados apenas do id, sem assinatura/expiração.
- Login que retorna dados do usuário sem emitir credencial verificável.

**Correção**: **PB-11** (token assinado com expiração usando a chave da config).

### AP-12 — Debug ativo / configuração de produção insegura
**Sinais de detecção**
- `debug=True`, `app.config["DEBUG"] = True`, `app.run(host="0.0.0.0", debug=True)`.
- `sqlite3.verbose()` em produção, CORS liberado para `*` sem config.

**Por que importa**: o debugger do Werkzeug permite execução remota de código.
**Correção**: **PB-02** (flags vindas da config/ambiente, padrão seguro).

---

## MEDIUM

### AP-13 — Queries N+1
**Sinais de detecção**
- Query dentro de `for`/`forEach` que itera resultados de outra query:
  - `for row in rows: cursor.execute("SELECT ... WHERE id = " + row[...])`
  - `for t in tasks: User.query.get(t.user_id)`
  - `courses.forEach(c => db.all("SELECT ... WHERE course_id = ?"...))`
- `.count()` por item em loop; várias `COUNT(*)` separadas que poderiam ser um `GROUP BY`.
- Acesso a relacionamento lazy em loop (`len(u.tasks)`).

**Correção**: **PB-12** (JOIN / `GROUP BY` / eager loading).

### AP-14 — Validação de entrada ausente ou duplicada
**Sinais de detecção**
- `request.get_json()` usado sem checar `None` (`dados.get` em `None` → 500).
- Tipos não validados (`preco < 0` com string → `TypeError` → 500; `int(request.args[...])` sem try).
- Mesmas regras de validação repetidas em create/update; listas de valores válidos repetidas.
- Funções de validação existentes em `utils` mas não usadas.

**Correção**: **PB-13** (validators centralizados por entidade, erros 400 consistentes).

### AP-15 — Tratamento de erros inadequado
**Sinais de detecção**
- `except:` (bare) ou `except Exception` engolindo erro; `catch` vazio; `(err) => { res.send(...) }` ignorando `err`.
- `return jsonify({"erro": str(e)}), 500` — vaza detalhes internos.
- `try/except` idêntico copiado em todos os handlers (sem error handler central).

**Correção**: **PB-14** (exceções de domínio + middleware de erro central).

### AP-16 — Código duplicado
**Sinais de detecção**
- Blocos idênticos de mapeamento `row → dict` repetidos; mesma lógica (ex.: "está atrasada?") reimplementada em vários arquivos; funções `get_todos_pedidos` e `get_pedidos_usuario` quase iguais.

**Correção**: **PB-15** (extrair função/método único no Model).

### AP-17 — Integridade referencial ausente
**Sinais de detecção**
- `DELETE` de entidade-pai sem tratar filhos (matrículas/pagamentos/tasks órfãos); mensagens como "ficaram sujos no banco".
- Tabelas sem `FOREIGN KEY`/`ON DELETE`; `PRAGMA foreign_keys` desligado.

**Correção**: **PB-16** (deleção em cascata dentro de transação / constraints).

### AP-18 — Uso de APIs deprecated
**Sinais de detecção (verifique sempre)**

| Stack | API deprecated (sinal) | Equivalente moderno |
|---|---|---|
| Python ≥3.12 | `datetime.utcnow()`, `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)` (use helper que remove tz se a coluna for *naive*) |
| SQLAlchemy 2.x / Flask-SQLAlchemy 3.x | `Model.query.get(id)` (legacy `Query.get`) | `db.session.get(Model, id)` |
| SQLAlchemy 2.x | `session.query(X).filter(...)` em código novo | `db.session.execute(db.select(X).where(...))` |
| Flask ≥2.3 | `@app.before_first_request`, `flask.json.JSONEncoder`, `app.json_encoder` | inicialização no factory; `app.json` provider |
| Flask ≥2.2 | `send_file(attachment_filename=...)` | `download_name=` |
| Python | `hashlib.md5` para senha, `cgi`, `imp`, `distutils`, `asyncio.get_event_loop()` sem loop | `werkzeug.security`/`hashlib.scrypt`, `email`, `importlib`, `setuptools`, `asyncio.run` |
| Node.js | `new Buffer()` / `Buffer()` | `Buffer.from()` / `Buffer.alloc()` |
| Node.js | `url.parse()`, `querystring` | `new URL()`, `URLSearchParams` |
| Node.js | `crypto.createCipher()` | `crypto.createCipheriv()` |
| Node.js | `fs.exists()`, `util.isArray()`… | `fs.existsSync`/`fs.promises.access`, `Array.isArray()` |
| Express 4→5 | `body-parser` separado, `req.param()`, `res.send(status)`, `res.json(obj, status)`, `app.del()` | `express.json()`, `req.params/query/body`, `res.status(s).send()`, `app.delete()` |
| JS | `String.prototype.substr` | `slice` / `substring` |
| Geral | Callback API quando a lib oferece Promise/async | `async/await` (legacy pattern — classifique como LOW se não for deprecated de fato) |

Use `grep -rnE "utcnow\(|\.query\.get\(|before_first_request|new Buffer\(|url\.parse\(|\.substr\(|createCipher\(|req\.param\(" .` como ponto de partida e confirme as versões no manifesto.

**Correção**: **PB-17** (substituição pela API moderna).

---

## LOW

### AP-19 — Magic numbers / strings
**Sinais**: literais de regra de negócio soltos (`0.1`, `10000`, `5000`, `<= 2`, `len(x) < 3`, `['pending', 'done', ...]` repetidas, `'#000000'`, porta `5000`), constantes definidas mas não usadas.
**Correção**: **PB-18** (constantes/enums nomeados no módulo de domínio).

### AP-20 — Nomenclatura ruim
**Sinais**: variáveis de 1–2 letras fora de loops curtos (`u`, `e`, `p`, `cc`, `cid`, `d`, `c2`), nomes de payload crípticos (`usr`, `eml`, `pwd`, `c_id`), nomes enganosos (`badCrypto`, `AppManager`, `logAndCache`), `cursor2`/`cursor3`.
**Correção**: **PB-19** (renomear internamente; manter nomes do contrato HTTP).

### AP-21 — Imports não usados / código morto
**Sinais**: `import os, sys, json, time` sem uso; funções utilitárias nunca chamadas (`grep -rn "nome_funcao" .` só encontra a definição); variáveis exportadas não usadas (`totalRevenue`).
**Correção**: **PB-19** (remover).

### AP-22 — Logging via print/console.log
**Sinais**: `print(` / `console.log(` para eventos de negócio, erros e "notificações" simuladas.
**Correção**: **PB-20** (logger estruturado do stdlib/framework com níveis).

---

## Checklist rápido de varredura

```bash
# segurança
grep -rnE "execute\(.*(\+|%|\.format|f\")" --include=*.py .
grep -rniE "(secret|passw|senha|api_?key|token|gateway).{0,15}[=:] *[\"']" --include=*.py --include=*.js . | grep -v node_modules
grep -rnE "md5|sha1\(|badCrypto|base64" --include=*.py --include=*.js . | grep -v node_modules
grep -rnE "debug *= *True|DEBUG\"\] *= *True" --include=*.py .
# arquitetura
grep -rnE "^\s*global " --include=*.py .
grep -rnE "^(let|var) [a-zA-Z]+ *= *(\{|\[|0)" --include=*.js src
# performance
grep -rnB3 "execute\(\|\.query\.\|db\.\(get\|all\|run\)(" . | grep -E "for |forEach"
# qualidade
grep -rnE "except:|except Exception" --include=*.py .
grep -rnE "print\(|console\.log\(" --include=*.py --include=*.js . | grep -v node_modules
```
