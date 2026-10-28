# Catálogo de Anti-patterns — Fase 2 (Auditoria)

Cada anti-pattern tem: **ID**, **severidade**, **regra de detecção** (com o que grep/ler), **por que é problema**, e **critério de correção**.

## Severidades

| Severidade | Critério |
|---|---|
| **CRITICAL** | Vulnerabilidade de segurança explorável (SQLi, credenciais expostas, crypto fraca). |
| **HIGH** | Violação arquitetural grave que impede testabilidade/mudança (lógica de negócio no Controller, ausência de validação em rotas sensíveis). |
| **MEDIUM** | Degradação de qualidade/performace que já impacta (N+1, God Class, estado global mutável). |
| **LOW** | Risco futuro, falta de separação de preocupações, dívida técnica (SQL inline sem migration, dependência morta). |

## Anti-patterns

### SEC-01 — SQL Injection
- **Severidade:** CRITICAL
- **Detecção:** Concatenação/f-string/`%` em query SQL dentro de handler, controller ou model. grep por `execute(`, `cursor.execute(`, `query(` com f-string, `.format(`, `%s` não-parametrizado.
- **Por que:** Entrada de usuário interpolada diretamente na query → execução de SQL arbitrário.
- **Critério de correção:** Usar parâmetros posicionais ou nomeados (`execute("SELECT ... WHERE id = ?", (id,))` ou `execute("SELECT ... WHERE id = :id", {"id": id})`).

### SEC-02 — Credenciais hardcoded
- **Severidade:** CRITICAL
- **Detecção:** Strings literais com `password`, `secret`, `api_key`, `token`, `connection_string` contendo valores não-vazios; URLs de conexão com `user:pass@`.
- **Por que:** Credenciais expostas no código-fonte; vazamento em repositório é inevitável.
- **Critério de correção:** Ler de variáveis de ambiente (`os.environ`, `os.getenv`, `process.env`) ou arquivo `.env` via `python-dotenv`/`dotenv`.

### SEC-03 — Criptografia fraca / hash inseguro
- **Severidade:** CRITICAL
- **Detecção:** Uso de `hashlib.md5`, `hashlib.sha1`, `bcrypt` sem salt, `DES`, `RC4`, `md5()` em MySQL/Postgres.
- **Por que:** Algoritmos quebrados; não resistem a brute-force moderno.
- **Critério de correção:** Usar `bcrypt`, `argon2`, ou `hashlib.pbkdf2_hmac` com salt para senhas; SHA-256+ para checksums.

### SEC-04 — Rota sem autenticação/autorização
- **Severidade:** HIGH
- **Detecção:** Rotas com verbos `POST`, `PUT`, `DELETE`, `PATCH` que não verificam token/session antes de operar em dados sensíveis. grep por `@app.route` / `router.post` sem `@login_required` / `@jwt_required` / middleware de auth correspondente.
- **Por que:** Acesso não-autorizado a dados sensíveis ou operações destrutivas.
- **Critério de correção:** Adicionar middleware/guard de auth em rotas sensíveis.

### SEC-05 — XSS — output sem escaping
- **Severidade:** HIGH
- **Detecção:** Templates com `{{ ... }}` usando `|safe` (Jinja), `dangerouslySetInnerHTML` (React), ou `render_template_string` com input não-sanitizado; respostas HTML montadas com f-string.
- **Por que:** Injeção de script executável no navegador do usuário.
- **Critério de correção:** Auto-escaping habilitado; usar `render_template` (não `render_template_string`); nunca montar HTML com string concatenada.

### SEC-06 — Log com dados sensíveis
- **Severidade:** HIGH
- **Detecção:** `logger.info/error/debug` com `password`, `token`, `secret`, `body` completo de request contendo credenciais.
- **Por que:** Logs são frequentemente acessíveis e retidos; dados sensíveis expostos em texto puro.
- **Critério de correção:** Sanitizar antes de logar; nunca logar senhas, tokens, ou bodies completos de autenticação.

### ARCH-01 — Lógica de negócio no Controller
- **Severidade:** HIGH
- **Detecção:** Handler/rota contém: cálculos, validações complexas (não só schema), montagem de respostas com transformação de dados, loops sobre entidades, regras de estado (se X então Y). grep por `if`/`for`/`while` dentro de funções de rota com mais de 10 linhas.
- **Por que:** Acopla transporte (HTTP) a regra de domínio; impede testabilidade e reuso.
- **Critério de correção:** Extrair para service/use-case; controller só orquestra (recebe request, chama service, devolve resposta).

### ARCH-02 — Acesso a dados no Controller
- **Severidade:** HIGH
- **Detecção:** `db.execute`, `cursor.execute`, `Model.query`, `session.query`, `db.session.add/delete` dentro de função de rota.
- **Por que:** Mesmo problema que ARCH-01, mas na camada de dados; sem repository/model dedicado, não há ponto único para mudar persistência.
- **Critério de correção:** Mover para Model method ou Repository; controller chama `service.do()` ou `repository.find()`.

### ARCH-03 — Modelo com responsabilidades duplas
- **Severidade:** MEDIUM
- **Detecção:** Arquivo de "model" que contém: queries SQL + regras de negócio + funções utilitárias. grep por múltiplas responsabilidades no mesmo arquivo.
- **Por que:** Viola SRP; difícil testar isoladamente.
- **Critério de correção:** Separar em Model (entidade + validação), Repository (acesso a dados), Service (regras).

### PERF-01 — N+1 queries
- **Severidade:** MEDIUM
- **Detecção:** Loop sobre resultados de query com query interna (ex: `for item in items: item.related = db.query(...)`). Grep por `for` + `execute`/`query`/`get`/`filter` no mesmo escopo.
- **Por que:** N+1 chamadas ao banco → latência exponencial.
- **Critério de correção:** Usar JOIN, `IN` clause, ou ORM eager loading (`joinedload`, `selectinload`, `.include()`).

### QUAL-01 — God Class / God File
- **Severidade:** MEDIUM
- **Detecção:** Arquivo com >300 LOC (Python) ou >400 LOC (JS/TS) que lida com >2 domínios/recursos distintos. grep por imports de múltiplos domínios.
- **Por que:** Arquivo central que everyone touches → merge conflicts, medo de mudar, bugs.
- **Critério de correção:** Dividir por domínio/responsabilidade; máximo ~150-200 LOC por arquivo de regra de negócio.

### QUAL-02 — Validação de entrada ausente
- **Severidade:** MEDIUM
- **Detecção:** Controller/handler acessa `request.json`, `request.body`, `req.body`, `request.form` diretamente sem checagem de schema, tipo, ou obrigatoriedade de campos.
- **Por que:** Dados malformados causam 500 internos, bugs silenciosos, ou comportamentos inesperados.
- **Critério de correção:** Validar com schema (marshmallow, pydantic, zod, joi, Joi, etc.) ou validação manual explícita com retorno 400.

### QUAL-03 — Tratamento de erro genérico
- **Severidade:** MEDIUM
- **Detecção:** `except Exception:`, `except:`, `catch (e) { }`, `except BaseException`, `try/except` vazio que engole erro sem logar ou relançar.
- **Por que:** Esconde bugs; dificulta diagnóstico em produção; erro inesperado tratado como esperado.
- **Critério de correção:** Capturar exceções específicas; logar; relançar ou retornar 500 com mensagem genérica.

### QUAL-04 — Estado global mutável
- **Severidade:** MEDIUM
- **Detecção:** Variável de módulo (`USERS = []`, `cache = {}`, `DB = None`) mutada por múltiplas funções; singleton sem thread-safety.
- **Por que:** Não-testável; race conditions; estado entre requests em produção.
- **Critério de correção:** Passar estado como parâmetro, usar DI, ou encapsular em classe com escopo de request.

### QUAL-05 — Dependência declarada mas não usada (dead dependency)
- **Severidade:** LOW
- **Detecção:** Dependência no manifesto (`requirements.txt`, `package.json`) sem import/require em nenhum arquivo de código.
- **Por que:** Aumenta superfície de ataque, tempo de build, e confusão.
- **Critério de correção:** Remover do manifesto se realmente não usada; ou documentar por que está presente.

### QUAL-06 — Schema sem versionamento (no migrations)
- **Severidade:** LOW
- **Detecção:** SQL `CREATE TABLE` inline no código ou no entrypoint; ausência de pasta `migrations/`, `alembic/`, `prisma/`, `db/migrate/`.
- **Por que:** Schema não versionado = impossível replicar ambiente; deploy quebra sem histórico.
- **Critério de correção:** Adicionar sistema de migrations (Alembic, Prisma Migrate, knex migrations, Django migrations).

### QUAL-07 — Configuração hardcoded
- **Severidade:** LOW
- **Detecção:** Portas, hosts, debug flags, paths literais no código em vez de `os.environ`/`os.getenv`/`process.env`/`.env`.
- **Por que:** Diferente envs (dev/staging/prod) requerem mudanças no código.
- **Critério de correção:** Mover para variáveis de ambiente com fallback sensível.

### QUAL-08 — Sem testes automatizados
- **Severidade:** LOW
- **Detecção:** Ausência de `tests/`, `__tests__/`, `spec/`, `*_test.py`, `*.test.js`.
- **Por que:** Refatoração sem segurança de regressão → bugs em produção.
- **Critério de correção:** Adicionar suite de testes mínima (unit + integration para rotas críticas).

## Regras de aplicação

1. **Todo achado aponta para arquivo:linha exato.** Sem linha, não é achado — é nota.
2. **Severidade não se infla.** Um "if" simples dentro de uma rota não é ARCH-01; procure *regra de negócio* (cálculos, condições compostas, manipulação de estado).
3. **Contexto importa.** Um `except Exception` num health-check endpoint é aceitável; num endpoint de pagamento não é.
4. **Não duplique achados.** Se o mesmo anti-pattern aparece no mesmo arquivo 3x, é **uma ocorrência** com múltiplos locais (liste os 3 locais sob o mesmo achado).
5. **Pausar antes de alterar.** A Fase 2 só **reporta**. A confirmação do usuário é necessária antes de iniciar a Fase 3 (refatoração).
