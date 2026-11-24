# Catálogo de Anti-Patterns

Cada entrada: **sinais de detecção** (agnósticos de stack), **severidade**, **impacto** e **playbook** correspondente (`refactoring-playbook.md`).

## Critérios de severidade

| Nível | Critério |
|---|---|
| **CRITICAL** | Falha de segurança explorável ou risco de perda/corrupção de dados. Corrigir primeiro. |
| **HIGH** | Violação arquitetural grave que impede manutenção/teste ou causa bugs em produção. |
| **MEDIUM** | Degrada qualidade, performance ou legibilidade; risco moderado. |
| **LOW** | Estilo, convenção, melhoria menor. |

Se um achado cabe em dois níveis, escolha o mais alto quando houver exposição de dados ou execução de entrada do usuário.

---

## CRITICAL

### AP-01 — SQL Injection (queries por concatenação)
- **Sinais**: SQL montado com concatenação/f-string/template literal/`format`/`%` incluindo variáveis vindas de request (`"... WHERE id = " + id`, `` `SELECT ... ${req.params.id}` ``, `f"... '{nome}'"`); ausência de placeholders (`?`, `$1`, `%s` com parâmetros, `:name`).
- **Impacto**: leitura/alteração/destruição arbitrária de dados.
- **Playbook**: P1.

### AP-02 — Credenciais e segredos hardcoded
- **Sinais**: senhas, tokens, `SECRET_KEY`, chaves de API, strings de conexão com usuário/senha literais no código; `DEBUG = True` fixo; arquivo `.env` versionado.
- **Impacto**: vazamento de acesso via repositório.
- **Playbook**: P2.

### AP-03 — Exposição de dados sensíveis / autenticação fraca
- **Sinais**: senhas em texto puro ou hash fraco (MD5/SHA1 sem salt) no banco; respostas que devolvem senha/token/hash; endpoints administrativos ou destrutivos (reset de banco, execução de SQL/comando arbitrário, dump) sem autenticação; comparação de senha em texto.
- **Impacto**: comprometimento de contas e de todo o sistema.
- **Playbook**: P2, P8, P12 (proteger **todas** as mutações, não só as citadas).

## HIGH

### AP-04 — God Class / God File
- **Sinais**: arquivo ou classe com > ~300 linhas ou com 3+ responsabilidades (rotas + SQL + regra de negócio + config); um único módulo que importa tudo e define tudo.
- **Impacto**: impossível testar/evoluir isoladamente.
- **Playbook**: P3, P4.

### AP-05 — Lógica de negócio e acesso a dados no controller/rota
- **Sinais**: handlers de rota que executam queries, calculam totais/descontos, validam regras e formatam resposta no mesmo bloco; rotas importam driver de banco ou ORM diretamente.
- **Impacto**: viola MVC; regra duplicada; sem reuso.
- **Playbook**: P3, P4, P5.

### AP-06 — Estado global mutável e conexão global
- **Sinais**: variáveis de módulo mutáveis compartilhadas entre requests (conexão única global, caches em dict/array solto, contadores); `global`/singletons implícitos sem controle de ciclo de vida; conexão compartilhada entre threads sem cuidado.
- **Impacto**: race conditions, vazamento de estado, testes frágeis.
- **Playbook**: P6.

### AP-07 — Tratamento de erros ausente ou inadequado
- **Sinais**: `except:`/`catch` vazio ou que engole a exceção; retorno de stack trace ao cliente; ausência de try/catch em I/O; erros devolvidos com status 200; mensagens de erro inconsistentes entre rotas.
- **Impacto**: falhas silenciosas, vazamento de internals.
- **Playbook**: P7.

## MEDIUM

### AP-08 — Problema N+1 / queries ineficientes
- **Sinais**: query dentro de loop (para cada item buscar relacionado); `SELECT *` desnecessário; listagens sem paginação; carregar tabela inteira para filtrar em memória.
- **Impacto**: latência cresce com o volume.
- **Playbook**: P9.

### AP-09 — Validação de entrada ausente ou duplicada
- **Sinais**: uso direto de `request.json[...]`/`req.body` sem checar presença, tipo ou formato; mesma validação copiada em várias rotas; conversões sem tratamento (`int(x)` sem try).
- **Impacto**: bugs, dados inválidos, base para injeções.
- **Playbook**: P5.

### AP-10 — Duplicação de código (DRY)
- **Sinais**: blocos idênticos/similares de serialização, validação ou query repetidos; conversão linha→dict copiada em vários lugares.
- **Impacto**: correções precisam ser replicadas.
- **Playbook**: P4, P5.

## LOW

### AP-11 — Magic numbers e strings
- **Sinais**: literais com significado de negócio espalhados (`0.1` desconto, `"pendente"`, limites `100`, códigos de status como strings repetidas).
- **Playbook**: P10.

### AP-12 — Nomenclatura e convenções inconsistentes
- **Sinais**: mistura de `snake_case`/`camelCase`, nomes de uma letra (`x`, `d`, `r`), nomes enganosos, idiomas misturados; código comentado morto; `print`/`console.log` de debug em vez de logger.
- **Playbook**: P10.

---

## APIs deprecated (detecção obrigatória)

Compare o que o código usa com a versão detectada na Fase 1. Classifique: **MEDIUM** por padrão; **HIGH** se já foi **removida** na versão instalada ou se tem implicação de segurança; **LOW** se apenas desencorajada. Registre como `AP-13 — API deprecated` (um achado por API/ocorrência agrupada), citando a API obsoleta e o equivalente moderno. Playbook: P8 (e P11).

Lista de exemplos (não exaustiva — o princípio vale para qualquer stack; confirme na documentação oficial da versão em uso):

| Stack | Obsoleto | Moderno |
|---|---|---|
| Node.js | `new Buffer()` | `Buffer.from()` / `Buffer.alloc()` |
| Node.js | `fs.exists()` | `fs.existsSync()` / `fs.promises.access()` |
| Node.js | `url.parse()` | `new URL()` |
| Node.js | `crypto.createCipher` | `crypto.createCipheriv` |
| Node.js | `body-parser` separado (Express ≥4.16) | `express.json()` / `express.urlencoded()` |
| Node.js | callbacks aninhados / `request` lib | `async/await` / `fetch` / `axios` |
| Express | `res.send(status)` numérico, `req.param()` | `res.sendStatus()`, `req.params/query/body` |
| Express | `app.del()` | `app.delete()` |
| Mongoose | `.remove()`, `useNewUrlParser` opts | `deleteOne()/deleteMany()` |
| Python | `datetime.utcnow()` / `utcfromtimestamp()` | `datetime.now(timezone.utc)` |
| Python | `imp`, `distutils`, `asyncio.get_event_loop()` solto | `importlib`, `setuptools`, `asyncio.run()` |
| Python | `%`-format / `.format` para SQL | consultas parametrizadas |
| Flask | `@app.before_first_request`, `flask.json.JSONEncoder` | inicialização no factory / `app.json` provider |
| Flask | `flask.ext.*`, `request.is_xhr` | imports diretos / checar headers |
| SQLAlchemy | `Query.get()`, `declarative_base` legado, `engine.execute()` | `Session.get()`, `DeclarativeBase`, `connection.execute(text())` |
| Django | `url()`, `ugettext`, `render_to_response` | `path()/re_path()`, `gettext`, `render()` |
| Java | `new Date()`/`Calendar`, `Thread.stop`, `finalize()` | `java.time`, `interrupt`, `Cleaner`/try-with-resources |
| Spring | `WebSecurityConfigurerAdapter` | bean `SecurityFilterChain` |
| PHP | `mysql_*`, `ereg`, `each()` | PDO/mysqli, `preg_*`, `foreach` |
| JS geral | `var`, `==` | `const/let`, `===` |
| Crypto | MD5/SHA1 para senha | bcrypt/argon2/scrypt |

**Como detectar**: busque pelos nomes acima; leia warnings de deprecation ao subir a app (`-W error::DeprecationWarning`, `node --trace-deprecation`); consulte changelog/docs da versão (ex.: Context7 MCP). Para qualquer API não listada, aplique o mesmo raciocínio: se a documentação da versão instalada a marca como deprecated/removida, é um achado.

---

## Ordem de verificação sugerida

1. Segredos e SQL (varredura textual por `SELECT|INSERT|UPDATE|DELETE`, `password|secret|key|token`).
2. Estrutura (tamanho de arquivos, camadas misturadas).
3. Estado global e erros.
4. Performance e validação.
5. Deprecated.
6. Estilo.

Reporte no mínimo o que for evidenciado; não force achados em categorias sem sinal no código.
