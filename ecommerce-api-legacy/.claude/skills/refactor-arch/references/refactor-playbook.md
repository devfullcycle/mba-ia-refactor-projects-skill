# Refactor Playbook — Fase 3 (Refatoração)

Padrões de refatoração **agnósticos de linguagem**. Os exemplos usam pseudocódigo; aplique com os idiomas da stack detectada na Fase 1, usando as tabelas de tradução ao final de cada padrão.

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

**Antes:** bloco de captura genérica em cada handler (`try/except Exception`, `catch (e)`), cada um formatando resposta de erro à sua maneira.

**Depois:** registrar o mecanismo global do framework; handlers deixam exceções propagarem.

| Stack | Mecanismo |
|---|---|
| Flask | `@app.errorhandler(status)` |
| Django | middleware / `handler500` |
| Express | middleware de 4 parâmetros `(err, req, res, next)` |
| Spring | `@ControllerAdvice` + `@ExceptionHandler` |
| Rails | `rescue_from` |
| Laravel | `app/Exceptions/Handler.php` |
| Gin/Echo | middleware de recovery |

**Mapeamento mínimo:** erro de validação → 400; recurso não encontrado → 404; não autorizado → 401/403; demais → 500 com mensagem genérica (sem vazar stack trace em produção).

## Padrão 5 — Validação de entrada

**Antes:** checks manuais espalhados e inconsistentes por handler; body usado cru.

**Depois:** validador por recurso, invocado no início do handler; retorno 400 com lista de erros.

```
function validarProduto(dados) -> lista de erros:
    erros = []
    se vazio(dados["nome"]):          erros.add("nome é obrigatório")
    se dados["preco"] < 0:            erros.add("preço não pode ser negativo")
    se dados["categoria"] notIn LISTA: erros.add("categoria inválida")
    return erros
```

**Bibliotecas por stack (opcional):** Python: pydantic, marshmallow. Node: zod, joi, class-validator. Java: Bean Validation (`jakarta.validation`). Ruby: ActiveModel validations. PHP: Form Requests (Laravel). Go: go-playground/validator.

**Regra:** validação de *schema/formato* fica no controller (ou validador chamado por ele); validação de *regra de negócio* (ex.: estoque suficiente) fica no service.

## Padrão 6 — Hash de senhas

**Antes:** senha em texto puro ou hash fraco (MD5/SHA1) persistida e retornada em responses.

**Depois:**
- Hash com algoritmo com salt: **bcrypt**, **argon2** ou **PBKDF2** (alto fator de iteração).
- Nunca retornar o campo senha em responses — excluir na serialização ou na query (`SELECT` sem a coluna).
- Senhas legadas exigem **migração de dados**: re-hash no próximo login ou reset forçado. Documente a estratégia no relatório da Fase 3.

**Bibliotecas por stack:** Python: bcrypt, argon2-cffi, `hashlib.pbkdf2_hmac`. Node: bcrypt, argon2. Java: `BCryptPasswordEncoder`. Ruby: bcrypt (`has_secure_password`). PHP: `password_hash()`. Go: `golang.org/x/crypto/bcrypt`.

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

**Antes:** entrypoint com dezenas de registros de rota misturados a boot, config e handlers inline.

**Depois:** um módulo de rotas por recurso; o entrypoint só compõe a aplicação.

```
// routes/produtos — só registro
grupo = router.group("/produtos")
grupo.get("",        produtoCtrl.listar)
grupo.get("/:id",    produtoCtrl.buscar)
grupo.post("",       produtoCtrl.criar)
grupo.put("/:id",    produtoCtrl.atualizar)
grupo.delete("/:id", produtoCtrl.deletar)

// entrypoint
app.register(routes.produtos, routes.usuarios, routes.pedidos)
```

**Regra:** o módulo de rotas importa controllers, nunca services ou repositories diretamente.

## Checklist por entidade refatorada

- [ ] Repository criado; todas as queries parametrizadas
- [ ] Service criado; regras de negócio extraídas do controller
- [ ] Controller reduzido a orquestração pura
- [ ] Rotas do recurso registradas em módulo separado
- [ ] Nenhum bloco de captura genérica no caminho do recurso
- [ ] Nenhum segredo/config literal introduzido
- [ ] Responses do recurso não expõem campos sensíveis
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
| SEC-03 Crypto fraca | Substituir hash + migrar dados legados (Padrão 6) |
| SEC-04 Rota sem auth | Criar middleware de auth e aplicar nas rotas sensíveis |
| SEC-05 XSS | Revisar serialização/templates que emitem HTML |
| SEC-06 Log sensível | Revisar logs; sanitizar antes de registrar |
| PERF-01 N+1 | Reescrever query com JOIN/eager loading (Padrão 7) |
| QUAL-05 Dead dependency | Remover do manifesto após confirmar ausência de uso |
| QUAL-06 Sem migrations | Adotar ferramenta de migration da stack |
| QUAL-08 Sem testes | Criar suite mínima de testes |
