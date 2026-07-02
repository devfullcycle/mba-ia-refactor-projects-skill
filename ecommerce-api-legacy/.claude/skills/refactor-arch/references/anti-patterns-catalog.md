# Catálogo de Anti-Patterns (Fase 2)

Cada entrada tem: sinais de detecção acionáveis, severidade e o que recomendar. A severidade segue a rubrica fixa do desafio (ver final do arquivo). Um mesmo trecho pode disparar mais de um anti-pattern.

---

## CRITICAL

### AP-01 — SQL Injection / Query por concatenação de string
**Sinais:** query montada com `+`, f-string, template string ou interpolação contendo entrada do usuário (`"... WHERE id = " + str(id)`, `` `SELECT ... ${x}` ``, `f"... '{email}'"`). Ausência de placeholders parametrizados (`?`, `%s`, `:param`) quando há valores dinâmicos.
**Recomendação:** usar queries parametrizadas / prepared statements ou o query builder do ORM. Nunca concatenar entrada na query.

### AP-02 — Credenciais / segredos hardcoded
**Sinais:** `SECRET_KEY`, `password`, `api_key`, `token`, chaves de gateway (`pk_live_`, `sk_`), credenciais de banco ou SMTP com valor literal no código. Segredo devolvido em resposta HTTP.
**Recomendação:** mover para variáveis de ambiente (`os.environ`/`process.env`) com defaults seguros só para dev; nunca serializar segredos em respostas.

### AP-03 — Senha em texto plano ou hash inseguro
**Sinais:** senha salva sem hash; hash com MD5/SHA1; função de hash "caseira"; campo de senha retornado por endpoint (`to_dict()` incluindo `password`/`senha`).
**Recomendação:** usar hash forte com salt (`bcrypt`, `argon2`, `werkzeug.security.generate_password_hash`); nunca serializar o campo de senha.

### AP-04 — Endpoint perigoso sem autenticação
**Sinais:** rota que executa SQL/comando arbitrário vindo do request; rota destrutiva (reset/drop/delete em massa) sem auth, allowlist ou confirmação.
**Recomendação:** remover o endpoint ou protegê-lo com autenticação + autorização; jamais executar SQL bruto vindo do cliente.

### AP-05 — God Class / God File
**Sinais:** um único arquivo/classe concentra conexão de banco, criação de schema/seed, roteamento e regras de negócio; centenas de linhas com múltiplas responsabilidades.
**Recomendação:** separar em camadas MVC (config, models, controllers, views/routes) por domínio.

---

## HIGH

### AP-06 — Lógica de negócio na camada errada (rota/controller "gordo")
**Sinais:** cálculos, regras de domínio, montagem de agregados ou queries diretas dentro de handlers de rota/controllers; controller acessando o banco sem passar por model/service.
**Recomendação:** extrair regras para models/services; o controller apenas orquestra (recebe request → chama service → devolve response).

### AP-07 — Estado global mutável
**Sinais:** variáveis de módulo mutáveis compartilhadas entre requisições (`globalCache = {}`, `totalRevenue = 0`, conexão de banco como singleton global mutável).
**Recomendação:** encapsular estado; usar escopo por requisição, injeção de dependência ou store apropriado.

### AP-08 — Ausência de autenticação/autorização nas rotas
**Sinais:** existe login mas nenhuma rota valida o token; rotas que leem/alteram dados de qualquer usuário sem checagem de identidade; token previsível/forjável (`"fake-token-" + id`).
**Recomendação:** middleware de autenticação; tokens assinados com expiração (JWT real); checagem de autorização por recurso.

### AP-09 — Callback hell / tratamento de erro incompleto
**Sinais:** callbacks aninhados em 3+ níveis; parâmetros `err` ignorados; ausência de `try/catch` em fluxo assíncrono; falta de `await`/Promises onde caberia.
**Recomendação:** achatar com `async/await` + Promises; tratar todos os erros; centralizar via middleware de erro.

### AP-10 — Acoplamento forte / ausência de injeção de dependência
**Sinais:** módulos instanciando diretamente suas dependências concretas (banco, serviços) em vez de recebê-las; impossível testar em isolamento (sem como injetar mock).
**Recomendação:** injetar dependências via construtor/parâmetros; depender de abstrações.

---

## MEDIUM

### AP-11 — Query N+1
**Sinais:** query dentro de loop (`for` percorrendo registros e executando uma query por item); montagem de agregados abrindo cursor/consulta por linha em vez de JOIN/agregação.
**Recomendação:** usar JOIN, `IN (...)`, eager loading do ORM ou agregação única.

### AP-12 — Validação ausente ou duplicada
**Sinais:** rota sem validação de entrada; **ou** o mesmo bloco de validação copiado entre create/update; regras de validação espalhadas.
**Recomendação:** centralizar validação (schema/validator dedicado, ex.: marshmallow/pydantic/Joi) e reutilizar.

### AP-13 — Código duplicado (lógica repetida)
**Sinais:** o mesmo cálculo/transformação copiado em vários pontos (ex.: cálculo de "overdue", montagem de dict de resposta) ignorando método/helper já existente.
**Recomendação:** extrair para função/método único e reutilizar (DRY); usar o método do model quando já existe.

### AP-14 — Uso inadequado de middleware / configuração
**Sinais:** CORS liberado sem restrição em produção; `debug=True` fixo; middlewares mal posicionados; parsing/erros tratados ad hoc em cada rota.
**Recomendação:** configurar CORS por ambiente; `debug` via env; middlewares de parsing e erro centralizados.

---

## LOW

### AP-15 — Logging por print/console
**Sinais:** `print(...)` / `console.log(...)` usados para log de aplicação, erros e auditoria, sem nível nem timestamp estruturado.
**Recomendação:** usar biblioteca de logging (`logging` do Python, logger do Node) com níveis.

### AP-16 — Magic numbers e valores hardcoded
**Sinais:** números/strings soltos com significado de negócio (limites, faixas de desconto, listas de status/categorias válidas repetidas inline).
**Recomendação:** extrair para constantes nomeadas / config.

### AP-17 — Nomenclatura ruim
**Sinais:** variáveis de uma letra ou abreviações opacas (`u, e, p, cid, cc`), nomes que não revelam intenção.
**Recomendação:** renomear para nomes descritivos.

### AP-18 — Imports não utilizados / dead code
**Sinais:** imports declarados e nunca usados; funções/variáveis mortas.
**Recomendação:** remover.

### AP-19 — Tratamento de exceção genérico
**Sinais:** `except:` / `except Exception` sem log detalhado; `catch` que engole o erro.
**Recomendação:** capturar exceções específicas, logar contexto, propagar/traduzir adequadamente.

---

## APIs deprecated / obsoletas (verificação obrigatória)

Sinalize uso de APIs obsoletas e recomende o equivalente moderno. A severidade depende do risco (segurança → CRITICAL/HIGH; apenas manutenção → MEDIUM/LOW).

| API / prática obsoleta | Equivalente moderno | Severidade típica |
|---|---|---|
| `hashlib.md5`/`sha1` para senha | `werkzeug.security.generate_password_hash`, `bcrypt`, `argon2` | CRITICAL |
| `datetime.utcnow()` (deprecated no Python 3.12+) | `datetime.now(datetime.UTC)` | LOW/MEDIUM |
| `sqlite3.connect(check_same_thread=False)` como singleton global | pool/conexão por requisição ou ORM | HIGH |
| Callbacks de `sqlite3` (Node) em vez de Promises | `sqlite`/`better-sqlite3` com async/await, ou wrapper `promisify` | MEDIUM |
| Express body-parser externo | `express.json()` nativo (Express 4.16+) | LOW |
| `var` em JS | `const`/`let` | LOW |
| `request` (lib npm) | `fetch` nativo / `axios` | LOW |
| Flask `@app.route` acumulando lógica em vez de Blueprints | Blueprints + camadas | MEDIUM |
| CORS liberado com `*` em produção | origens explícitas por ambiente | MEDIUM |

Ao encontrar, cite a API atual, a linha e o substituto recomendado.

---

## Rubrica de severidade (fixa)

- **CRITICAL:** falhas graves de arquitetura/segurança que quebram o funcionamento correto, expõem dados sensíveis (credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (God Class com banco + lógica + roteamento juntos).
- **HIGH:** fortes violações de MVC/SOLID que dificultam muito manutenção e testes (lógica de negócio presa em controllers, acoplamento sem injeção de dependência, estado global mutável).
- **MEDIUM:** problemas de padronização, duplicação de código ou performance moderada (queries N+1, uso inadequado de middleware, validações ausentes nas rotas).
- **LOW:** melhorias de legibilidade, nomenclatura ruim, magic numbers soltos.
