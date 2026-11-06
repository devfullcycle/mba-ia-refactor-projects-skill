# Refactor Playbook — Fase 3 (Refatoração)

Padrões de refatoração **agnósticos de linguagem**. Todos os exemplos usam pseudocódigo; aplique com os idiomas da stack detectada na Fase 1, usando as tabelas de tradução ao final de cada padrão. As tabelas por stack são referências de tradução — as regras e os testes de cada padrão valem para qualquer tecnologia.

## Padrão 1 — Extrair Repository (queries parametrizadas)

**Quando:** SQL espalhado em controllers/handlers e models, queries montadas por concatenação ou interpolação de string.

**Antes:**
```
function getProduto(id):
    cursor.execute("SELECT * FROM produtos WHERE id = " + id)
    return cursor.fetchOne()
```

**Depois:**
```
class ProdutoRepository:
    function getById(id):
        return db.execute("SELECT * FROM produtos WHERE id = ?", [id])
```

**Placeholders por stack:**

| Stack | Placeholder | Exemplo de chamada |
|---|---|---|
| Python (sqlite3) | `?` | `execute("... WHERE id = ?", (id,))` |
| Python (psycopg2) | `%s` / `%(nome)s` | `execute("... WHERE id = %s", (id,))` |
| Node (mysql2) | `?` | `query("... WHERE id = ?", [id])` |
| Node (pg) | `$1, $2...` | `query("... WHERE id = $1", [id])` |
| Java (JDBC) | `?` em `PreparedStatement` | `prepareStatement("... WHERE id = ?")` |
| Ruby (ActiveRecord) | `?` | `where("id = ?", id)` |
| PHP (PDO) | `?` / `:nome` | `prepare("... WHERE id = :id")` |
| Go (database/sql) | `?` ou `$1` (conforme driver) | `Query("... WHERE id = $1", id)` |
| C# (ADO.NET) | `@nome` | `new SqlParameter("@id", id)` |

**Regras:**
- O repository nunca importa nada da camada HTTP (request, response, framework web).
- Um repository por entidade agregada.
- Métodos padrão: `getById`, `getAll`, `create`, `update`, `delete`, `findBy<Campo>`.

## Padrão 2 — Extrair Service

**Quando:** Handler contém regras de negócio, cálculos, validações complexas ou orquestração entre entidades.

**Antes:**
```
function criarPedido(request):
    dados = request.body
    // cálculo de total, verificação de estoque, inserts...
    // 50+ linhas de lógica misturadas com HTTP
    return response(201, {"pedido_id": id})
```

**Depois:**
```
// service — sem imports de HTTP
class PedidoService:
    function criar(usuarioId, itens):
        total = calcularTotal(itens)
        verificarEstoque(itens)   // lança EstoqueInsuficienteError
        return pedidoRepo.create(usuarioId, total, itens)

// controller — só orquestra
function criarPedido(request):
    dados = request.body
    validarSchemaBasico(dados)    // 400 se inválido
    resultado = pedidoService.criar(dados.usuarioId, dados.itens)
    return response(201, {"dados": resultado})
```

**Regras:**
- Service não conhece o protocolo de transporte (não importa request/response do framework).
- Erros de negócio são exceções/resultados de domínio (`EstoqueInsuficienteError`, `NotFoundError`) — o error handler centralizado (Padrão 4) os traduz para status HTTP.
- Agrupe services por domínio, não por verbo HTTP.

## Padrão 3 — Configuração externalizada

**Antes:**
```
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
dbPath = "loja.db"
port = 5000
```

**Depois:**
```
class Config:
    SECRET_KEY = env("SECRET_KEY", default=geradoEmBoot())
    DB_PATH    = env("DB_PATH", default="loja.db")
    PORT       = env("PORT", default=5000)
```

**Mecanismo por stack:**

| Stack | Mecanismo |
|---|---|
| Python | `os.environ` / `os.getenv` + python-dotenv |
| Node | `process.env` + dotenv |
| Java | `System.getenv` / `application.yml` |
| Ruby | `ENV` / Rails credentials |
| PHP | `getenv()` / `$_ENV` + `.env` |
| Go | `os.Getenv` / viper |
| C# | `appsettings.json` + `IConfiguration` |

**Regras:**
- Defaults só para valores **não-sensíveis** (porta, host). Segredos sem default seguro: gere em boot ou falhe explicitamente.
- Nunca commitar `.env` real — forneça `.env.example`.

## Padrão 4 — Error handling centralizado

**Quando:** cada handler tem seu próprio bloco de captura genérica (`try/except`, `try/catch`) e monta a resposta de erro de um jeito diferente.

**Antes:**
```
function criarProduto(request):
    try:
        dados = request.body
        se vazio(dados["nome"]):
            return response(400, {"erro": "nome obrigatório"})
        produto = produtoRepo.create(dados)
        return response(201, {"dados": produto})
    catch Exception as e:
        return response(500, {"erro": texto(e)})     // vaza detalhe interno

function buscarProduto(request, id):
    try:
        produto = produtoRepo.getById(id)
        se produto == nulo:
            return response(404, {"erro": "não encontrado"})
        return response(200, {"dados": produto})
    catch Exception as e:
        return response(500, {"erro": "falha"})       // formato diferente do anterior
```

**Depois:**
```
// domínio — exceções explícitas, sem conhecer HTTP
class ValidationError   extends Erro
class UnauthorizedError extends Erro
class ForbiddenError    extends Erro
class NotFoundError     extends Erro
class ConflictError     extends Erro

// controller — só orquestra; exceções propagam
function criarProduto(request):
    dados = validar(ProdutoSchema, request.body)
    return response(201, produtoService.criar(dados))

function buscarProduto(request, id):
    return response(200, produtoService.buscar(id))

// um único ponto de tradução para HTTP
registrarErrorHandler(ValidationError, function(err):
    return response(400, {"erro": err.mensagem}))

registrarErrorHandler(UnauthorizedError, function(err):
    return response(401, {"erro": err.mensagem}))

registrarErrorHandler(ForbiddenError, function(err):
    return response(403, {"erro": err.mensagem}))

registrarErrorHandler(NotFoundError, function(err):
    return response(404, {"erro": err.mensagem}))

registrarErrorHandler(ConflictError, function(err):
    return response(409, {"erro": err.mensagem}))

registrarErrorHandler(Exception, function(err):
    log.error(err)
    return response(500, {"erro": "erro interno"}))   // sem stack trace na resposta
```

**Mapeamento mínimo:**

| Exceção de domínio | HTTP |
|---|---|
| `ValidationError` | 400 |
| `UnauthorizedError` | 401 |
| `ForbiddenError` | 403 |
| `NotFoundError` | 404 |
| `ConflictError` | 409 |
| qualquer outra | 500 (mensagem genérica, sem stack trace em produção) |

**Mecanismo por stack:**

| Stack | Mecanismo |
|---|---|
| Flask | `@app.errorhandler(status)` |
| Django | middleware / `handler500` |
| Express | middleware de 4 parâmetros `(err, req, res, next)` |
| Spring | `@ControllerAdvice` + `@ExceptionHandler` |
| Rails | `rescue_from` |
| Laravel | `app/Exceptions/Handler.php` |
| Gin/Echo | middleware de recovery |

## Padrão 5 — Validação de entrada

**Quando:** o handler usa `request.body`/`req.body` cru e repete `se`s de formato, misturando validação de schema com regra de negócio.

**Antes:**
```
function criarProduto(request):
    dados = request.body                              // body cru
    se vazio(dados["nome"]):
        return response(400, {"erro": "nome obrigatório"})
    se dados["preco"] == nulo:
        return response(400, {"erro": "preço obrigatório"})
    se dados["preco"] < 0:
        return response(400, {"erro": "preço não pode ser negativo"})
    se dados["categoria"] notIn CATEGORIAS:
        return response(400, {"erro": "categoria inválida"})
    se produtoRepo.buscarPorNome(dados["nome"]) != nulo:
        return response(409, {"erro": "produto duplicado"})   // regra de negócio no controller
    return response(201, produtoRepo.create(dados))
```

**Depois:**
```
// schema — formato e tipos
schema ProdutoSchema:
    nome:      texto, obrigatório, mínimo 1
    preco:     número, obrigatório, mínimo 0
    categoria: texto, obrigatório, in CATEGORIAS

// controller — valida no início e devolve 400 com a lista completa
function criarProduto(request):
    dados, erros = validar(ProdutoSchema, request.body)
    se erros não vazio:
        return response(400, {"erros": erros})
    return response(201, produtoService.criar(dados))

// service — regra de negócio, não formato
class ProdutoService:
    function criar(dados):
        se produtoRepo.buscarPorNome(dados["nome"]) != nulo:
            lançar ConflictError("produto duplicado")
        return produtoRepo.create(dados)
```

```
// validador — retorna todos os erros de uma vez
function validarProduto(dados) -> lista de erros:
    erros = []
    se vazio(dados["nome"]):            erros.add("nome é obrigatório")
    se dados["preco"] < 0:              erros.add("preço não pode ser negativo")
    se dados["categoria"] notIn LISTA:  erros.add("categoria inválida")
    return erros
```

**Bibliotecas por stack (opcional):** Python: pydantic, marshmallow. Node: zod, joi, class-validator. Java: Bean Validation (`jakarta.validation`). Ruby: ActiveModel validations. PHP: Form Requests (Laravel). Go: go-playground/validator.

**Regra:** validação de *schema/formato* fica no controller (ou validador chamado por ele); validação de *regra de negócio* (ex.: estoque suficiente) fica no service.

## Padrão 6 — Hash de senhas

**Quando:** senha em texto puro ou hash fraco (MD5/SHA1) é persistida, comparada no login ou devolvida em responses — inclusive em seeds e bases legadas.

**Antes:**
```
// cadastro — senha em texto puro no banco e na response
function criarUsuario(request):
    dados = request.body
    usuario = usuarioRepo.create({
        "nome":  dados["nome"],
        "senha": dados["senha"]                 // texto puro persistido
    })
    return response(201, {"id": usuario["id"], "senha": usuario["senha"]})

// login — comparação em texto puro
function login(request):
    usuario = usuarioRepo.buscarPorEmail(request.body["email"])
    se usuario != nulo e usuario["senha"] == request.body["senha"]:
        return response(200, {"token": gerarToken(usuario)})
    return response(401, {"erro": "credenciais inválidas"})

// variante igualmente incorreta: hash fraco sem salt
function criarUsuarioComMd5(request):
    usuario = usuarioRepo.create({
        "nome":  request.body["nome"],
        "senha": md5(request.body["senha"])      // MD5 sem salt
    })
    return response(201, {"id": usuario["id"], "senha": usuario["senha"]})
```

**Depois:**
```
// cadastro — hash com salt antes de persistir
function criarUsuario(request):
    dados = validar(UsuarioCreateSchema, request.body)
    usuario = usuarioRepo.create({
        "nome":      dados["nome"],
        "senhaHash": hashSenha(dados["senha"])   // bcrypt/argon2/PBKDF2 + salt
    })
    return response(201, serializarPublico(usuario))

// login — somente verificação de hash, sem fallback em texto puro
function login(request):
    usuario = usuarioRepo.buscarPorEmail(request.body["email"])
    se usuario == nulo ou não verificarSenha(usuario["senhaHash"], request.body["senha"]):
        lançar UnauthorizedError("credenciais inválidas")
    return response(200, {"token": gerarToken(usuario)})

// serialização — o campo de senha nunca sai na response
function serializarPublico(usuario):
    return {"id": usuario["id"], "nome": usuario["nome"], "email": usuario["email"]}
```

**Seed e legado — também precisam estar hasheados:**
```
// seed — hash antes do INSERT (nunca o valor literal)
usuarioRepo.create({
    "email":     "admin@exemplo.com",
    "senhaHash": hashSenha(ADMIN_PASSWORD)
})

// migração única — converte senhas legadas sem prefixo de hash
para cada usuario em usuarioRepo.listarTodos():
    se não pareceHash(usuario["senha"]):          // sem scrypt:/pbkdf2:/$2
        usuarioRepo.atualizarSenha(
            usuario["id"],
            hashSenha(usuario["senha"])
        )
```

**Regras:**
- Hash com algoritmo com salt: **bcrypt**, **argon2** ou **PBKDF2** (alto fator de iteração).
- Nunca retornar o campo senha em responses — excluir na serialização ou na query (`SELECT` sem a coluna).
- Senhas legadas exigem **migração de dados**: re-hash no próximo login ou reset forçado. Documente a estratégia no relatório da Fase 3.
- **A correção só é válida se não restar senha em texto puro no banco, inclusive no seed.** Ter `generate_password_hash`/equivalente em um endpoint não basta se o seed ou o fallback de login continuarem em texto puro.

**Bibliotecas por stack:** Python: bcrypt, argon2-cffi, `hashlib.pbkdf2_hmac`, Flask/Werkzeug (`generate_password_hash`/`check_password_hash`). Node: bcrypt, argon2. Java: `BCryptPasswordEncoder`. Ruby: bcrypt (`has_secure_password`). PHP: `password_hash()`. Go: `golang.org/x/crypto/bcrypt`.

## Padrão 7 — N+1 → query única

**Antes:**
```
for pedido in pedidos:                        // 1 query
    itens = query("SELECT * FROM itens WHERE pedido_id = " + pedido.id)   // N queries
    for item in itens:
        produto = query("SELECT nome FROM produtos WHERE id = " + item.produtoId)  // N*M queries
```

**Depois (opção A — JOIN + agregação em memória):**
```
rows = query("""
    SELECT p.*, i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr   ON pr.id = i.produto_id
    WHERE p.usuario_id = ?
    ORDER BY p.id
""", [usuarioId])
pedidos = agrupar(rows)   // agrupa linhas do JOIN em objetos aninhados
```

**Depois (opção B — eager loading do ORM):**

| ORM | Mecanismo |
|---|---|
| SQLAlchemy | `joinedload` / `selectinload` |
| Django | `select_related` / `prefetch_related` |
| Sequelize | `include` |
| Rails | `includes` / `preload` |
| Laravel | `with()` |
| Hibernate | `JOIN FETCH` |

## Padrão 8 — Rotas separadas do entrypoint

**Quando:** o entrypoint registra rotas diretamente (`@app.route`, `app.add_url_rule`, `app.get`, etc.) e mistura boot, configuração e handlers no mesmo arquivo.

**Antes:**
```
// entrypoint — boot, config, rotas e handlers no mesmo arquivo
app = criarAplicacao()
app.config["SECRET_KEY"] = "chave-literal"          // segredo literal
banco = conectar("loja.db")

app.route("GET", "/produtos", function():
    return response(200, banco.query("SELECT * FROM produtos"))
)

app.route("POST", "/produtos", function(request):
    return response(201, banco.query("INSERT INTO produtos ...", request.body))
)

app.route("GET", "/usuarios", function():
    return response(200, banco.query("SELECT * FROM usuarios"))
)

app.iniciar(porta=5000)
```

**Depois:**
```
// routes/produtos — só registro de rotas
moduloProdutos = novoModuloRotas("/produtos")

moduloProdutos.get("",        produtoController.listar)
moduloProdutos.get("/:id",    produtoController.buscar)
moduloProdutos.post("",       produtoController.criar)
moduloProdutos.put("/:id",    produtoController.atualizar)
moduloProdutos.delete("/:id", produtoController.deletar)

// routes/usuarios — idem, um módulo por recurso
moduloUsuarios = novoModuloRotas("/usuarios")
moduloUsuarios.get("",     usuarioController.listar)
moduloUsuarios.post("",    usuarioController.criar)

// entrypoint — apenas compõe a aplicação
function criarAplicacao(config):
    app = novaAplicacao(config)
    app.registrar(moduloProdutos, moduloUsuarios)
    app.registrarErrorHandlers()
    return app
```

**Tradução:** `app.registrar(...)` equivale a `register_blueprints(app)` no Flask ou `app.use('/produtos', produtoRoutes)` no Express. O nome do arquivo de rotas segue a stack (`routes/produtos.py`, `routes/produtos.js`, etc.).

**Regra:** o módulo de rotas importa controllers, nunca services ou repositories diretamente.

## Padrão 9 — Autenticação e autorização (default deny)

**Quando:** rotas de escrita, rotas administrativas, dados de outro usuário ou campos de papel/posse vindos do cliente.

**Antes:**
```
function criarUsuario(request):
    dados = request.body                       // qualquer anônimo
    papel = dados["role"] ?? "user"            // cliente escolhe o próprio privilégio
    usuario = usuarioService.criar(dados, papel)
    return response(201, usuario)

function criarTarefa(request):
    dados = request.body
    dono = dados["usuarioId"]                  // cliente escolhe em nome de quem cria
    return response(201, tarefaService.criar(dados, dono))

function atualizarUsuario(request, id):
    return response(200, usuarioService.atualizar(id, request.body))  // qualquer anônimo edita

function excluirUsuario(request, id):
    usuarioService.excluir(id)                                       // qualquer anônimo exclui
    return response(204)
```

**Depois:**
```
// guard central — toda rota é privada por padrão; pública é exceção declarada
function guard(request):
    token = extrairToken(request)              // Authorization: Bearer ...
    se ausente(token):
        lançar UnauthorizedError("credencial ausente")
    contexto = verificarToken(token)           // assinatura, expiração, emissor
    request.usuario = {
        "id":    contexto["sub"],
        "papel": contexto["role"]
    }
    próximo(request)

// registrado uma vez; em stacks sem middleware global, use decorator/wrapper em todas as rotas
registrarGuardGlobal(guard)

function exigirPapel(request, papelEsperado):
    se request.usuario["papel"] != papelEsperado:
        lançar ForbiddenError("papel insuficiente")

// gestão de usuários — somente admin
function criarUsuario(request):
    exigirPapel(request, "admin")              // 401 já garantido pelo guard global
    dados = validar(UsuarioCreateSchema, request.body)
    return response(201, usuarioService.criar(dados))

// recurso de domínio — dono vem do token, nunca do body
function criarTarefa(request):
    dados = validar(TarefaCreateSchema, request.body)
    se dados["usuarioId"] existe e dados["usuarioId"] != request.usuario["id"]:
        lançar ForbiddenError("não é permitido criar em nome de terceiro")
    dados["usuarioId"] = request.usuario["id"] // valor do token prevalece
    return response(201, tarefaService.criar(dados))

// leitura/edição de recurso existente — dono ou admin
function buscarTarefa(request, id):
    tarefa = tarefaService.buscar(id)
    se tarefa["usuarioId"] != request.usuario["id"]
       e request.usuario["papel"] != "admin":
        lançar ForbiddenError("acesso negado")
    return response(200, tarefa)

// rotas públicas são exceções explícitas e mínimas
registrarRotaPublica("POST", "/login", login)
```

**Regras:**
- **Default deny:** sem credencial → `401`; credencial sem o papel exigido → `403`.
- Em stacks sem middleware global, aplique o guard como decorator/wrapper em todas as rotas e mantenha uma allowlist explícita para as públicas.
- Gestão de usuários (`POST`/`PUT`/`DELETE` e listagem administrativa) exige papel `admin`.
- Rotas de domínio exigem o dono do recurso ou `admin`; criação em nome de terceiro só com posse derivada do token.
- **Nunca** confiar em `role`, `tipo`, `usuario_id` ou `owner_id` enviados pelo cliente.
- **A ausência de autenticação não pode ser o default:** a aplicação deve falhar fechada. Nenhuma correção pode depender de flag opt-in (`AUTH_REQUIRED=true` e similares).
- Rotas públicas são exceções explícitas e mínimas (ex.: login, health check).
- Verificar assinatura, expiração e emissor do token; não confiar apenas na presença dele.
- Respostas de autenticação/autorização não devem revelar se o recurso existe; use `401`/`403` de forma consistente.

**Tabela por stack (tradução do conceito):**

| Stack | Guard central | Papel/role | Identidade do token |
|---|---|---|---|
| Flask | `before_request` + decorator | decorator `@require_role` | `g.usuario_id`, `g.papel` |
| Django | middleware / `LoginRequiredMixin` | `PermissionRequiredMixin` / `@permission_required` | `request.user` |
| Express | middleware `(req, res, next)` | middleware `requireRole("admin")` | `req.user` |
| Spring | `SecurityFilterChain` | `@PreAuthorize("hasRole('ADMIN')")` | `Authentication` / `Principal` |
| Rails | `before_action :authenticate` | `before_action` + Pundit (`authorize`) | `current_user` |
| Laravel | middleware `auth` | middleware `can:` / `Gate` | `auth()->user()` |
| Go | middleware `http.Handler` | checagem de papel no middleware | `context.Context` |
| ASP.NET | `[Authorize]` | `[Authorize(Roles="admin")]` | `HttpContext.User` |

**Testes obrigatórios — sempre com a configuração padrão:**
- [ ] Escrita sem credencial → `401`.
- [ ] Credencial válida sem o papel exigido → `403`.
- [ ] Credencial com o papel correto → `200`/`201`.
- [ ] Gestão de usuários: não-admin → `403`; admin → sucesso.
- [ ] Body com `role`/`usuario_id`/`owner_id` divergente do token → valor do body ignorado (ou `403`), nunca aceito.
- [ ] Token expirado ou com assinatura inválida → `401`.
- [ ] Dono acessando o próprio recurso → sucesso; outro usuário → `403`.
- [ ] Rotas públicas continuam acessíveis e apenas elas.
- [ ] Suite executada com o default do `.env.example`/config, sem flag especial que ligue a correção.

## Checklist por entidade refatorada

- [ ] Repository criado; todas as queries parametrizadas
- [ ] Service criado; regras de negócio extraídas do controller
- [ ] Controller reduzido a orquestração pura
- [ ] Rotas do recurso registradas em módulo separado
- [ ] Nenhum bloco de captura genérica no caminho do recurso
- [ ] Nenhum segredo/config literal introduzido
- [ ] Responses do recurso não expõem campos sensíveis
- [ ] Rotas de escrita exigem autenticação por padrão (`401` sem credencial)
- [ ] Rotas administrativas exigem papel `admin` (`403` sem papel)
- [ ] Identidade, papel e posse vêm do token, nunca do body
- [ ] Nenhuma senha em texto puro no banco, inclusive no seed/legado
- [ ] Endpoints do recurso exercitados manualmente após a movimentação
- [ ] Código antigo removido (sem duplicata entre camadas)

## Como a refatoração resolve cada anti-pattern

Resolvidos **naturalmente** ao mover código para as camadas:

| Anti-pattern | Resolução |
|---|---|
| SEC-01 SQL Injection | Queries parametrizadas no Repository (Padrão 1) |
| SEC-02 Credenciais hardcoded | Config externalizada (Padrão 3) |
| ARCH-01 Lógica no Controller | Extração para Service (Padrão 2) |
| ARCH-02 Dados no Controller | Extração para Repository (Padrão 1) |
| ARCH-03 Model com responsabilidades duplas | Split Model/Repository/Service (Padrões 1-2) |
| QUAL-01 God Class | Divisão por domínio nas camadas |
| QUAL-02 Validação ausente | Validadores por recurso (Padrão 5) |
| QUAL-03 Erro genérico | Error handler centralizado (Padrão 4) |
| QUAL-04 Estado global mutável | Conexão/serviços encapsulados, sem singleton mutável |
| QUAL-07 Config hardcoded | Config externalizada (Padrão 3) |

Exigem **passo dedicado** (não se resolvem só movendo código):

| Anti-pattern | Resolução |
|---|---|
| SEC-03 Crypto fraca | Substituir hash + migrar dados legados (Padrão 6); seed e banco em repouso também precisam estar hasheados |
| SEC-04 Rota sem auth | Autenticação e autorização default deny (Padrão 9), com papel `admin` para gestão de usuários e posse derivada do token |
| SEC-05 XSS | Revisar serialização/templates que emitem HTML |
| SEC-06 Log sensível | Revisar logs; sanitizar antes de registrar |
| PERF-01 N+1 | Reescrever query com JOIN/eager loading (Padrão 7) |
| QUAL-05 Dead dependency | Remover do manifesto após confirmar ausência de uso |
| QUAL-06 Sem migrations | Adotar ferramenta de migration da stack |
| QUAL-08 Sem testes | Criar suite mínima de testes |
