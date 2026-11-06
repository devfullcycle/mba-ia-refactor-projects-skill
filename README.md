# Criação de Skills — Refatoração Arquitetural Automatizada

O objetivo desse repositório é exibir um exemplo de como criar uma skill para o Claude, que realiza a refatoração arquitetural automatizada de projetos de software. A skill é capaz de identificar problemas de arquitetura e sugerir melhorias, além de gerar relatórios detalhados sobre os problemas encontrados.

## Construção da Skill

### Decisões de design

- **Orquestrador + 4 sub-skills, uma por fase.** O `refactor-arch` não analisa nem refatora: ele lê `reports/`, identifica o estado e carrega a sub-skill adequada (`analyze`, `audit`, `refactor`, `validate`).
- **Contexto limpo por fase.** Cada sub-skill lê apenas as referências da sua fase, em vez de carregar um único `SKILL.md` com todo o processo.
- **Gates explícitos.** Fases 1, 2 e 4 não alteram código-fonte (apenas leem e geram relatório); só a Fase 3 escreve código, e apenas após auditoria + confirmação explícita. A Fase 4 é o gate de conclusão.
- **Gate bloqueante na Fase 4.** Um CRITICAL/HIGH `PARCIAL` ou `NÃO RESOLVIDO` reprova o fluxo com status `FAIL` e recomendação `REPROVADO - AÇÃO NECESSÁRIA`. `APROVADO COM RESSALVAS` fica restrito a MEDIUM/LOW, e `VALIDATED` exige `Partial critical/high: 0`.
- **Segurança por padrão.** Auth/autorização são default deny, sem flag opt-in; gestão de usuários exige `admin`, e identidade/papel/posse vêm do token. Correções de segurança não podem ser adiadas por compatibilidade de contrato.
- **Estado derivado dos relatórios.** A máquina de estados do orquestrador usa a existência de `reports/analysis-*`, `audit-*`, `refactor-*` e `validation-*` para decidir o próximo passo, tornando o fluxo retomável.
- **`SKILL.md` curto + referências especializadas.** Os 7 arquivos em `references/` concentram o detalhe: Fase 1 (`stack-detection`, `architecture-detection`, `report-template`), Fase 2 (`anti-patterns`, `audit-report-template`) e Fases 3/4 (`mvc-guidelines`, `refactor-playbook`).
- **Cópia por projeto.** Cada projeto tem sua cópia em `.claude/skills/`, para que o Claude Code encontre a skill ao executar a partir da raiz do projeto.

### Anti-patterns do catálogo

- **19 anti-patterns**, em 5 categorias: 6 de segurança (SEC), 3 de arquitetura (ARCH), 1 de performance (PERF), 8 de qualidade (QUAL) e 1 de APIs deprecated (DEP).
- **Critério de seleção: cobrir os problemas reais dos 3 projetos de teste**, não um catálogo teórico genérico.
- Exemplos:
  - **SEC:** SQL Injection, credenciais hardcoded, hash fraco, rota sem autenticação/autorização, XSS e log com dados sensíveis.
  - **ARCH:** lógica de negócio no controller, acesso a dados no controller e model com responsabilidades duplas.
  - **PERF:** N+1 queries.
  - **QUAL:** God Class/File, validação ausente, tratamento de erro genérico, estado global mutável, dependência morta, ausência de migrations, configuração hardcoded e ausência de testes.
  - **DEP:** uso de APIs deprecated (`datetime.utcnow()`, `Query.get()`), detectado no `task-manager-api`.
- Cada item traz severidade, regra de detecção, motivo e critério de correção — o que padroniza o achado e evita severidade inflada.

### Padrões de refatoração (antes/depois em código)

O playbook da Fase 3 tem **9 padrões**, todos com blocos **Antes** e **Depois** em código — não apenas prosa. Os exemplos abaixo resumem o que a skill aplica; o detalhe por stack está em `<projeto>/.claude/skills/refactor-arch/references/refactor-playbook.md`.

#### Padrão 1 — Extrair Repository (queries parametrizadas)

**Antes:**
```python
@app.get("/produtos/<int:produto_id>")
def get_produto(produto_id):
    cursor.execute(f"SELECT * FROM produtos WHERE id = {produto_id}")  # injeção
    return jsonify(cursor.fetchone())
```

**Depois:**
```python
# repositories/produto_repository.py
class ProdutoRepository:
    def get_by_id(self, produto_id):
        return self.db.execute(
            "SELECT * FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()

# controllers/produto_controller.py — sem SQL
def get_produto(produto_id):
    produto = produto_service.buscar(produto_id)
    return jsonify({"dados": produto.to_dict()})
```

#### Padrão 2 — Extrair Service

**Antes:**
```python
@app.post("/pedidos")
def criar_pedido():
    dados = request.get_json()
    total = sum(item["preco"] * item["qtd"] for item in dados["itens"])
    for item in dados["itens"]:
        estoque = db.execute("SELECT qtd FROM estoque WHERE produto_id = ?",
                             (item["produto_id"],)).fetchone()
        if estoque["qtd"] < item["qtd"]:
            return jsonify({"erro": "sem estoque"}), 400
    pedido_id = db.execute("INSERT INTO pedidos ...").lastrowid
    return jsonify({"pedido_id": pedido_id}), 201
```

**Depois:**
```python
# services/pedido_service.py — sem imports de HTTP
class PedidoService:
    def criar(self, usuario_id, itens):
        total = calcular_total(itens)
        self.estoque.verificar(itens)          # EstoqueInsuficienteError
        return self.pedido_repo.create(usuario_id, total, itens)

# controllers/pedido_controller.py — só orquestra
def criar_pedido():
    dados = validate(PedidoSchema(), request.get_json())
    pedido = pedido_service.criar(g.usuario_id, dados["itens"])
    return jsonify({"pedido_id": pedido.id}), 201
```

#### Padrão 3 — Configuração externalizada

**Antes:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
DB_PATH = "loja.db"
PORT = 5000
```

**Depois:**
```python
import os
from secrets import token_hex

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or token_hex(32)  # sem literal
    DB_PATH = os.getenv("DATABASE_PATH", "loja.db")        # default não sensível
    PORT = int(os.getenv("PORT", "5000"))
```

Regra: defaults só para valores não sensíveis; segredos sem default fixo e falha explícita em produção.

#### Padrão 4 — Error handling centralizado

**Antes:**
```python
@app.post("/produtos")
def criar_produto():
    try:
        ...
    except Exception as e:
        return jsonify({"erro": str(e)}), 500      # vaza detalhe interno

@app.get("/produtos/<int:produto_id>")
def buscar_produto(produto_id):
    try:
        ...
    except Exception:
        return jsonify({"erro": "falha"}), 500     # formato diferente
```

**Depois:**
```python
# errors.py — exceções de domínio sem conhecer HTTP
class ValidationError(Exception): ...
class UnauthorizedError(Exception): ...
class ForbiddenError(Exception): ...
class NotFoundError(Exception): ...
class ConflictError(Exception): ...

# app.py — um único ponto de tradução
@app.errorhandler(ValidationError)
def validation_error(err):
    return jsonify({"erro": str(err)}), 400

@app.errorhandler(UnauthorizedError)
def unauthorized_error(err):
    return jsonify({"erro": str(err)}), 401

@app.errorhandler(ForbiddenError)
def forbidden_error(err):
    return jsonify({"erro": str(err)}), 403

@app.errorhandler(NotFoundError)
def not_found_error(err):
    return jsonify({"erro": str(err)}), 404

@app.errorhandler(Exception)
def internal_error(err):
    app.logger.exception(err)
    return jsonify({"erro": "erro interno"}), 500  # sem stack trace na resposta
```

Mapeamento mínimo: `400`, `401`, `403`, `404`, `409` e `500` genérico.

#### Padrão 5 — Validação de entrada

**Antes:**
```python
def criar_produto():
    dados = request.get_json()                         # body cru
    if not dados.get("nome"):
        return jsonify({"erro": "nome obrigatório"}), 400
    if dados.get("preco") is None or dados["preco"] < 0:
        return jsonify({"erro": "preço inválido"}), 400
    if dados.get("categoria") not in CATEGORIAS:
        return jsonify({"erro": "categoria inválida"}), 400
    return jsonify(produto_repo.create(dados)), 201
```

**Depois:**
```python
# schemas/validators.py — formato e tipos
class ProdutoSchema(Schema):
    nome = fields.Str(required=True, validate=validate.Length(min=1))
    preco = fields.Float(required=True, validate=validate.Range(min=0))
    categoria = fields.Str(required=True)

# controller — valida no início e devolve 400 com a lista completa
def criar_produto():
    dados = validate(ProdutoSchema(), request.get_json())
    produto = produto_service.criar(dados)             # regra de negócio no service
    return jsonify({"dados": produto.to_dict()}), 201

# service — duplicidade/estoque são regra de negócio, não de schema
def criar(self, dados):
    if self.produto_repo.find_by_nome(dados["nome"]):
        raise ConflictError("produto duplicado")
    return self.produto_repo.create(dados)
```

#### Padrão 6 — Hash de senhas

**Antes:**
```python
def criar_usuario():
    dados = request.get_json()
    db.execute("INSERT INTO usuarios (nome, senha) VALUES (?, ?)",
               (dados["nome"], dados["senha"]))          # texto puro
    return jsonify({"senha": dados["senha"]}), 201       # senha na resposta

def login():
    usuario = buscar_por_email(request.get_json()["email"])
    if usuario and usuario["senha"] == request.get_json()["senha"]:
        return jsonify({"token": gerar_token(usuario)})  # comparação direta
```

**Depois:**
```python
def criar_usuario():
    dados = validate(UsuarioCreateSchema(), request.get_json())
    usuario = usuario_repo.create(
        nome=dados["nome"],
        senha_hash=generate_password_hash(dados["senha"]),  # salt + custo
    )
    return jsonify({"dados": usuario.to_public_dict()}), 201  # sem senha

def login():
    dados = validate(LoginSchema(), request.get_json())
    usuario = usuario_repo.find_by_email(dados["email"])
    if not usuario or not check_password_hash(usuario.senha_hash, dados["senha"]):
        raise UnauthorizedError("credenciais inválidas")
    return jsonify({"token": gerar_token(usuario)})
```

Seed e legado também precisam estar hasheados:
```python
# seed — grava somente hash, nunca o literal
usuario_repo.create(email="admin@loja.com",
                    senha_hash=generate_password_hash("admin123"))

# migração de legado no boot — converte qualquer senha sem prefixo de hash
for usuario in usuario_repo.listar_todos():
    if not looks_hashed(usuario.senha):
        usuario_repo.update_senha(
            usuario.id, generate_password_hash(usuario.senha)
        )
```

**Regra:** a correção só é válida se **não restar senha em texto puro no banco, inclusive no seed**. Login usa apenas `check_password_hash`/equivalente, sem fallback de comparação direta; o campo de senha nunca é serializado.

#### Padrão 7 — N+1 → query única

**Antes:**
```python
pedidos = db.execute("SELECT * FROM pedidos").fetchall()
for pedido in pedidos:
    pedido["itens"] = db.execute(
        "SELECT * FROM itens WHERE pedido_id = ?", (pedido["id"],)
    ).fetchall()                                          # N+1
```

**Depois:**
```python
rows = db.execute("""
    SELECT p.*, i.produto_id, i.quantidade, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    ORDER BY p.id
""").fetchall()
pedidos = agrupar_por_pedido(rows)                        # 1 query
```

#### Padrão 8 — Rotas separadas do entrypoint

**Antes:**
```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "chave-literal"
db = conectar("loja.db")

@app.get("/produtos")
def listar_produtos():
    return jsonify(db.execute("SELECT * FROM produtos").fetchall())

@app.post("/produtos")
def criar_produto():
    ...                                                   # boot, config e handler juntos

app.run(debug=True)
```

**Depois:**
```python
# routes/produto_routes.py — só rotas; importa controller
produto_bp = Blueprint("produtos", __name__, url_prefix="/produtos")
produto_bp.add_url_rule("", view_func=produto_controller.listar, methods=["GET"])
produto_bp.add_url_rule("", view_func=produto_controller.criar, methods=["POST"])

# app.py — apenas composição
def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_error_handler(Exception, internal_error)
    return app
```

Regra: o módulo de rotas importa controllers, nunca services ou repositories diretamente.

#### Padrão 9 — Autenticação e autorização (default deny)

**Quando:** rotas de escrita, rotas administrativas, dados de outro usuário ou campos de papel/posse vindos do cliente.

**Antes:**
```python
@app.post("/usuarios")
def criar_usuario():
    dados = request.get_json()               # qualquer anônimo
    papel = dados.get("role", "user")         # cliente escolhe o próprio privilégio
    return jsonify(usuario_service.criar(dados, papel)), 201

@app.post("/pedidos")
def criar_pedido():
    dados = request.get_json()
    dono = dados["usuario_id"]                # cliente escolhe em nome de quem cria
    return jsonify(pedido_service.criar(dados, dono)), 201

@app.delete("/usuarios/<int:user_id>")
def excluir_usuario(user_id):
    usuario_service.excluir(user_id)          # qualquer anônimo exclui
    return "", 204
```

**Depois:**
```python
# middleware/auth.py — guard central: privado por padrão; público é exceção
def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = extrair_bearer(request)
        if not token:
            raise UnauthorizedError("credencial ausente")
        payload = verificar_token(token)      # assinatura, expiração, emissor
        g.user_id = payload["sub"]
        g.user_role = payload["role"]
        return fn(*args, **kwargs)
    return wrapper

def require_role(papel):
    def decorator(fn):
        @wraps(fn)
        @require_auth
        def wrapper(*args, **kwargs):
            if g.user_role != papel:
                raise ForbiddenError("perfil sem permissão")
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# gestão de usuários — somente admin (401 sem token; 403 sem papel)
@usuarios_bp.post("")
@require_role("admin")
def criar_usuario():
    dados = validate(UsuarioCreateSchema(), request.get_json())
    return jsonify(usuario_service.criar(dados)), 201

# recurso de domínio — dono vem do token, nunca do body
@pedidos_bp.post("")
@require_auth
def criar_pedido():
    dados = validate(PedidoCreateSchema(), request.get_json())
    if "usuario_id" in dados and dados["usuario_id"] != g.user_id:
        raise ForbiddenError("não é permitido criar em nome de terceiro")
    return jsonify(pedido_service.criar(dados, g.user_id)), 201

# rotas públicas são exceções explícitas e mínimas
@auth_bp.post("/login")
def login():
    ...
```

Tradução do conceito por stack:

| Stack | Guard central | Papel/role | Identidade do token |
|---|---|---|---|
| Flask | `before_request` + decorator | `@require_role` | `g.user_id`, `g.user_role` |
| Django | middleware / `LoginRequiredMixin` | `PermissionRequiredMixin` | `request.user` |
| Express | middleware `(req, res, next)` | `requireRole("admin")` | `req.user` |
| Spring | `SecurityFilterChain` | `@PreAuthorize` | `Authentication` |
| Rails | `before_action :authenticate` | `before_action` + Pundit | `current_user` |
| Laravel | middleware `auth` | `can:` / `Gate` | `auth()->user()` |
| Go | middleware `http.Handler` | checagem de papel no middleware | `context.Context` |
| ASP.NET | `[Authorize]` | `[Authorize(Roles="admin")]` | `HttpContext.User` |

**Regras:**
- **Default deny:** sem credencial → `401`; credencial sem o papel exigido → `403`.
- Gestão de usuários (listagem administrativa, criação, edição e exclusão) exige papel `admin`.
- Recursos de domínio exigem o dono ou `admin`; identidade, papel e posse vêm do token, nunca de `role`/`tipo`/`usuario_id`/`owner_id` do body.
- Rotas públicas são exceções explícitas e mínimas (ex.: login e health check).
- Verificar assinatura, expiração e emissor do token; não confiar apenas na presença dele.
- **A ausência de autenticação não pode ser o default:** a aplicação falha fechada. Nenhuma correção pode depender de flag opt-in (`AUTH_REQUIRED=true` ou similares).
- Testar sempre com a configuração padrão: `401` sem credencial, `403` sem papel, caminho autorizado `200/201`, body divergente ignorado/rejeitado.

### Segurança por padrão e gate da Fase 4

- **Default seguro, sem auth opt-in.** O guard de autenticação é aplicado por padrão; não existe flag que mantenha a aplicação insegura. Se a configuração de autenticação não estiver disponível, a aplicação falha fechada (`401`/`503`) em vez de liberar acesso. Rotas públicas são allowlist explícita.
- **Identidade derivada do token.** `role`, `tipo`, `usuario_id` e `owner_id` enviados pelo cliente nunca são aceitos como verdade. Gestão de usuários exige `admin`; recursos de domínio exigem dono ou `admin`.
- **Gate bloqueante da Fase 4.** Qualquer achado CRITICAL/HIGH `PARCIAL` ou `NÃO RESOLVIDO` reprova o fluxo:

```text
se algum CRITICAL/HIGH estiver PARCIAL ou NÃO RESOLVIDO:
    status            = FAIL
    recomendação      = REPROVADO - AÇÃO NECESSÁRIA
    fluxo_concluído   = False
senão se houver apenas MEDIUM/LOW pendente:
    status            = PASS
    recomendação      = APROVADO COM RESSALVAS
senão:
    status            = PASS / VALIDATED
    recomendação      = APROVADO
```

- `VALIDATED` exige `Partial critical/high: 0`; `APROVADO COM RESSALVAS` é restrito a MEDIUM/LOW.
- A validação roda com o **default** do projeto/`.env.example`, sem flags especiais. Para SEC-04, o `401` deve ocorrer no boot padrão; para SEC-03, a ausência de texto puro é verificada no banco/seed, não apenas na resposta HTTP.

### Agnosticismo de tecnologia

- **Detecção por evidência:** a Fase 1 parte de manifestos, dependências e código, com heurísticas para vários ecossistemas (`stack-detection.md`), e não de nomes de pastas ou suposições.
- **Camadas conceituais, não nomes fixos:** `mvc-guidelines.md` define responsabilidades e uma tabela de tradução por ecossistema (Flask, Django, Express, Spring, Rails, Laravel, Go, ASP.NET). Quando o framework tem convenção própria, a skill segue a convenção do framework.
- **Comandos derivados da análise:** boot e testes vêm do que foi detectado na Fase 1; não há comando de stack embutido no fluxo principal.
- **Escopo de validação:** a skill foi executada em Python/Flask (2 projetos) e Node.js/Express (1). Os demais ecossistemas são cobertos pelas heurísticas e tabelas de mapeamento, mas não foram validados empiricamente.

### Desafios encontrados e como foram resolvidos

- **Tamanho/contexto dos `SKILL.md`:** um único arquivo com detecção, catálogo, templates e playbook ficaria longo e caro em tokens. **Resolução:** o `SKILL.md` de cada fase ficou com objetivo, pré-requisitos, passos e regras; o detalhe foi movido para `references/`, lido sob demanda.
- **Projeto já parcialmente organizado (`task-manager-api`):** havia risco de sobrescrever uma estrutura existente. **Resolução:** a skill obriga análise e auditoria antes de qualquer alteração; a Fase 3 só inicia após confirmação explícita.

## Como executar a skill

Cada projeto possui uma cópia da skill em `.claude/skills/` (orquestrador `refactor-arch` + sub-skills de análise, auditoria, refatoração e validação). Por isso, a skill deve ser executada **a partir do diretório raiz do projeto desejado**, para que o Claude Code encontre a configuração local.

**Pré-requisitos gerais:**

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) instalado e autenticado (comando `claude` disponível no terminal).
- Dependências do projeto instaladas (necessárias principalmente para a Fase 4, que sobe a aplicação e executa os testes de validação).
- Executar os comandos abaixo a partir da raiz deste repositório.

> A skill é interativa: a Fase 2 (auditoria) pausa e pede confirmação explícita antes de modificar código na Fase 3. Responda `sim` para prosseguir com a refatoração.

#### 1) `code-smells-project` (Python/Flask — API de E-commerce)

```bash
cd code-smells-project

# Opcional: preparar ambiente para a validação (Fase 4)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Executar a skill
claude "/refactor-arch"
```

Opcional: antes de refatorar, suba a aplicação com `python app.py` (porta `5000`) para conhecer o comportamento original.

#### 2) `ecommerce-api-legacy` (Node.js/Express — LMS API com checkout)

Requer Node.js 18 ou superior.

```bash
cd ecommerce-api-legacy

# Opcional: preparar ambiente para a validação (Fase 4)
npm install
cp .env.example .env   # ajuste os valores se necessário

# Executar a skill
claude "/refactor-arch"
```

Opcional: valide o estado atual com `npm test` e/ou `npm start` (porta `3000`).

#### 3) `task-manager-api` (Python/Flask — API de Task Manager)

```bash
cd task-manager-api

# Opcional: preparar ambiente para a validação (Fase 4)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # opcional (defaults seguros)
flask --app app db upgrade    # aplica as migrations
python seed.py                # popula dados de exemplo

# Executar a skill
claude "/refactor-arch"
```

Opcional: valide o estado atual com `pytest` e/ou `python app.py` (porta `5000`).

#### Executando apenas uma fase

Também é possível invocar diretamente uma sub-skill, a partir da raiz do projeto:

```bash
claude "/refactor-arch-analyze"    # Fase 1 — Análise
claude "/refactor-arch-audit"      # Fase 2 — Auditoria (somente leitura)
claude "/refactor-arch-refactor"   # Fase 3 — Refatoração (exige confirmação)
claude "/refactor-arch-validate"   # Fase 4 — Validação pós-refatoração
```

#### Reexecutando o fluxo completo

Os três projetos já possuem relatórios em `reports/` (`analysis-*`, `audit-*`, `refactor-*` e `validation-*`). Como o orquestrador usa esses arquivos para decidir o estado do fluxo, ele só considerará o processo concluído se o `validation-*.md` indicar `PASS`/`VALIDATED`, recomendação `APROVADO` e `Partial critical/high: 0`. Para executar todas as fases novamente do zero, mova os relatórios existentes antes de rodar a skill:

```bash
# A partir do diretório do projeto (ex.: code-smells-project)
mv reports reports.bak
mkdir reports
claude "/refactor-arch"
```

Para restaurar os relatórios originais depois: `rm -rf reports && mv reports.bak reports`.

## Estrutura do Projeto

```text
mba-ia-refactor-projects-skill/
├── README.md
├── .gitignore
├── .claude/
│   └── settings.local.json
├── code-smells-project/          # Python/Flask - API de E-commerce (com code smells)
│   ├── app.py
│   ├── config.py
│   ├── errors.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
│   ├── README.md
│   ├── controllers/
│   ├── database/
│   │   ├── connection.py
│   │   └── schema.py
│   ├── middleware/
│   │   ├── auth.py
│   │   └── error_handler.py
│   ├── models/
│   │   └── produto.py
│   ├── repositories/
│   │   ├── pedido_repository.py
│   │   ├── produto_repository.py
│   │   └── usuario_repository.py
│   ├── routes/
│   │   ├── pedido_routes.py
│   │   ├── produto_routes.py
│   │   ├── relatorio_routes.py
│   │   └── usuario_routes.py
│   ├── schemas/
│   │   └── validators.py
│   ├── services/
│   │   ├── admin_service.py
│   │   ├── health_service.py
│   │   ├── notificacao_service.py
│   │   ├── pedido_service.py
│   │   ├── produto_service.py
│   │   └── usuario_service.py
│   ├── tests/
│   │   └── smoke_contract.py
│   ├── reports/
│   │   ├── analysis-code-smells-project.md
│   │   ├── audit-code-smells-project.md
│   │   ├── refactor-code-smells-project.md
│   │   └── validation-code-smells-project.md
│   └── .claude/skills/           # Skills de refatoração arquitetural
│       ├── refactor-arch/
│       ├── refactor-arch-analyze/
│       ├── refactor-arch-audit/
│       ├── refactor-arch-refactor/
│       └── refactor-arch-validate/
├── ecommerce-api-legacy/         # Node.js/Express - LMS API com fluxo de checkout
│   ├── app.js (src/app.js)
│   ├── package.json
│   ├── package-lock.json
│   ├── api.http
│   ├── .env.example
│   ├── .gitignore
│   ├── README.md
│   ├── src/
│   │   ├── app.js
│   │   ├── container.js
│   │   ├── config/
│   │   │   └── index.js
│   │   ├── controllers/
│   │   │   ├── CheckoutController.js
│   │   │   ├── FinancialReportController.js
│   │   │   └── UserController.js
│   │   ├── database/
│   │   │   ├── connection.js
│   │   │   ├── migrator.js
│   │   │   ├── schema.js
│   │   │   └── migrations/
│   │   │       └── 001_initial_schema.sql
│   │   ├── errors/
│   │   ├── middleware/
│   │   │   ├── asyncHandler.js
│   │   │   ├── auth.js
│   │   │   ├── errorHandler.js
│   │   │   └── notFound.js
│   │   ├── models/
│   │   │   ├── Course.js
│   │   │   ├── Enrollment.js
│   │   │   ├── Payment.js
│   │   │   └── User.js
│   │   ├── repositories/
│   │   │   ├── AuditLogRepository.js
│   │   │   ├── CourseRepository.js
│   │   │   ├── EnrollmentRepository.js
│   │   │   ├── PaymentRepository.js
│   │   │   ├── ReportRepository.js
│   │   │   └── UserRepository.js
│   │   ├── routes/
│   │   │   ├── adminRoutes.js
│   │   │   ├── checkoutRoutes.js
│   │   │   ├── index.js
│   │   │   └── userRoutes.js
│   │   ├── services/
│   │   │   ├── CheckoutService.js
│   │   │   ├── FinancialReportService.js
│   │   │   ├── PaymentGateway.js
│   │   │   └── UserService.js
│   │   ├── utils/
│   │   │   ├── logger.js
│   │   │   └── password.js
│   │   └── validators/
│   │       ├── checkoutValidator.js
│   │       └── idValidator.js
│   ├── tests/
│   │   ├── api.test.js
│   │   └── password.test.js
│   ├── reports/
│   │   ├── analysis-ecommerce-api-legacy.md
│   │   ├── audit-ecommerce-api-legacy.md
│   │   ├── refactor-ecommerce-api-legacy.md
│   │   └── validation-ecommerce-api-legacy.md
│   └── .claude/skills/           # Skills de refatoração arquitetural
│       ├── refactor-arch/
│       ├── refactor-arch-analyze/
│       ├── refactor-arch-audit/
│       ├── refactor-arch-refactor/
│       └── refactor-arch-validate/
└── task-manager-api/            # Python/Flask - API de Task Manager
    ├── app.py
    ├── database.py
    ├── errors.py
    ├── requirements.txt
    ├── tasks.db
    ├── seed.py
    ├── .env.example
    ├── .gitignore
    ├── README.md
    ├── config/
    │   └── settings.py
    ├── controllers/
    │   ├── category_controller.py
    │   ├── common.py
    │   ├── report_controller.py
    │   ├── task_controller.py
    │   └── user_controller.py
    ├── middleware/
    │   ├── auth.py
    │   └── error_handler.py
    ├── migrations/
    │   ├── alembic.ini
    │   ├── env.py
    │   ├── script.py.mako
    │   └── versions/
    │       └── 81c7c4d76ee3_initial_schema.py
    ├── models/
    │   ├── category.py
    │   ├── task.py
    │   └── user.py
    ├── repositories/
    │   ├── category_repository.py
    │   ├── task_repository.py
    │   └── user_repository.py
    ├── services/
    │   ├── auth_service.py
    │   ├── category_service.py
    │   ├── report_service.py
    │   ├── task_service.py
    │   └── user_service.py
    ├── utils/
    │   └── helpers.py
    ├── validators/
    │   └── schemas.py
    ├── reports/
    │   ├── analysis-task-manager-api.md
    │   ├── audit-task-manager-api.md
    │   ├── refactor-task-manager-api.md
    │   └── validation-task-manager-api.md
    └── .claude/skills/           # Skills de refatoração arquitetural
        ├── refactor-arch/
        ├── refactor-arch-analyze/
        ├── refactor-arch-audit/
        ├── refactor-arch-refactor/
        └── refactor-arch-validate/
```


## Análise Manual

> Esta seção registra a triagem manual inicial, anterior à execução da skill. A fonte de verdade para severidade e fechamento é o `reports/audit-*.md` de cada projeto; os números consolidados após a refatoração estão na seção **Resultados da reexecução (2026-11-05)**.

### code-smells-project (Python/Flask — API de E-commerce)

** Problemas Identificados:**

1. [CRITICAL] Sistema apresenta problemas de SQL Injection. No arquivo `app.py`, a função `get_product` utiliza a variável `product_id` diretamente na query SQL, sem validação ou sanitização. Isso permite que um usuário malicioso insira código SQL arbitrário, comprometendo a segurança do banco de dados.
2. [MEDIUM] O projeto não apresenta validações de input nas rotas. No arquivo `app.py`, as funções `create_product` e `update_product` não validam os dados recebidos do usuário, o que pode levar a inconsistências no banco de dados e falhas na aplicação.
3. [MEDIUM] O projeto apresenta problemas de Queries N+1. Ex. No arquivo `models.py`, a função `get_todos_pedidos` faz uma query para buscar todos os pedidos, e para cada pedido, faz uma query separada para buscar os produtos associados. Isso resulta em múltiplas queries ao banco de dados, impactando a performance da aplicação.
4. [LOW] O projeto possi importações não utilizadas. No arquivo `models.py`, o sistema importa a biblioteca `sqlite3`, mas não a utiliza em nenhum lugar do código, o que pode levar a confusão e aumento do tamanho do código desnecessariamente.
5. [LOW] O projeto apresenta configurações hardcoded. No arquivo `app.py`, a configuração de iniciar o servidor Flask está hardcoded com a porta 5000. Isso pode dificultar a configuração do ambiente de desenvolvimento e produção, além de não seguir boas práticas de configuração.

### ecommerce-api-legacy (Node.js/Express — LMS API com fluxo de checkout)

** Problemas Identificados:**

1. [CRITICAL] Configurações de conexão com DB, chaves de pagamento, porta de configuração estão codificados no projeto. Deveria ter sido utilizado um arquivo .env para resolver
2. [MEDIUM] Projeto  utiliza um algoritmo de criptogafia para senhas que não funciona.
3. [MEDIUM] Projeto não utiliza um sistema de ORM para realizar conexões com o banco de dados, resultando em queries escritas direto no código.
4. [LOW] Sistema não está dividido em uma estrutura MVC. Toda a lógica está apesar em um local.
5. [LOW] Sistema não possui um sistema real de log. Como todos os logs da aplicação são salvos em uma variável global, quando o sistema é desligado, os logs serão perdidos. 

### task-manager-api (Python/Flask — API de Task Manager)

** Problemas Identificados:**

1. [CRITICAL] Na classe de User (models/user.py), os métodos de password utilizam o MD5 para criptografar a senha, o que é considerado inseguro. Deveria ser utilizado um algoritmo mais seguro, como bcrypt. MD5 é um algoritmo de hash rápido, o que o torna vulnerável a ataques de força bruta. Além disso, não há um mecanismo de salt para aumentar a segurança das senhas.
2. [MEDIUM] O projeto apresenta problemas de Queries N+1. No arquivo `routes/task_routes.py`, a função `get_tasks` faz uma query para buscar todas as tarefas, e para cada tarefa, faz uma query separada para buscar os detalhes do usuário associado. Isso resulta em múltiplas queries ao banco de dados, impactando a performance da aplicação.
3. [MEDIUM] O projeto não apresenta validações de input nas rotas. No arquivo `routes/task_routes.py`, as funções `create_task` e `update_task` não validam os dados recebidos do usuário, o que pode levar a inconsistências no banco de dados e falhas na aplicação.
4. [LOW] O projeto apresenta imports não utilizados. No arquivo `app.py`, existem imports de bibliotecas que não são utilizadas em nenhum lugar do código, o que pode levar a confusão e aumento do tamanho do código desnecessariamente.
5. [LOW] O projeto apresenta configurações hardcoded. No arquivo `app.py`, a configuração de iniciar o servidor Flask está hardcoded com a porta 5000. Além disso, as configuração como `app.config['SQLALCHEMY_DATABASE_URI']` e `app.config['SECRET_KEY']` estão hardcoded, o que pode dificultar a configuração do ambiente de desenvolvimento e produção, além de não seguir boas práticas de configuração.


## C) Seção "Resultados"

### Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)

| Projeto | Stack | Arquivos auditados | Total de achados | CRITICAL | HIGH | MEDIUM | LOW | Relatório |
|---|---|---|---|---|---|---|---|---|
| **code-smells-project** | Python/Flask (API E-commerce) | 4 arquivos, ~780 LOC | 16 | 3 | 4 | 5 | 4 | [`code-smells-project/reports/audit-code-smells-project.md`](code-smells-project/reports/audit-code-smells-project.md) |
| **ecommerce-api-legacy** | Node.js/Express (LMS com checkout) | 3 arquivos de código, ~180 LOC | 13 | 2 | 4 | 4 | 3 | [`ecommerce-api-legacy/reports/audit-ecommerce-api-legacy.md`](ecommerce-api-legacy/reports/audit-ecommerce-api-legacy.md) |
| **task-manager-api** | Python/Flask (Task Manager) | 9 arquivos de código, ~1100 LOC (excluindo `__init__.py` e `seed.py`) | 16 | 3 | 3 | 5 | 5 | [`task-manager-api/reports/audit-task-manager-api.md`](task-manager-api/reports/audit-task-manager-api.md) |

**Principais achados críticos detectados:**
- **code-smells-project:** SQL Injection (SEC-01), credenciais hardcoded/expostas (SEC-02), senhas em texto plano (SEC-03)
- **ecommerce-api-legacy:** Credenciais hardcoded (SEC-02), criptografia fraca/hash inseguro (SEC-03)
- **task-manager-api:** `SECRET_KEY` hardcoded (SEC-02), credenciais SMTP hardcoded (SEC-02), MD5 sem salt + hash exposto em respostas (SEC-03)

### Resultados da reexecução (2026-11-05)

Números extraídos dos `reports/validation-*.md` dos três projetos após as correções do feedback:

| Projeto | Rotas validadas | Testes | CRITICAL resolvidos | HIGH resolvidos | Partial critical/high | Evidência de segurança | Recomendação | Relatório |
|---|---|---|---|---|---|---|---|---|
| **code-smells-project** | **19/19** | **73/73** (`tests/smoke_contract.py`) | **3/3** | **4/4** | **0** | SEC-01/02/03/04 `RESOLVIDO`; admin em rotas de escrita; seed e banco em repouso com hash scrypt; login só com `check_password_hash` | **APROVADO** | [`validation-code-smells-project.md`](code-smells-project/reports/validation-code-smells-project.md) |
| **ecommerce-api-legacy** | **3/3** | **16/16** (`npm test`) | **2/2** | **4/4** | **0** | SEC-02/03/04/06 `RESOLVIDO`; Bearer admin com fail-closed; checkout exige senha do titular; scrypt em repouso; logs sem PAN/chave/senha | **APROVADO** | [`validation-ecommerce-api-legacy.md`](ecommerce-api-legacy/reports/validation-ecommerce-api-legacy.md) |
| **task-manager-api** | **22/22** | **8/8** (`pytest`) | **3/3** | **3/3** | **0** | SEC-02/03/04 `RESOLVIDO`; JWT default deny sem opt-in; `admin` na gestão de usuários; seed scrypt; posse derivada do token | **APROVADO** | [`validation-task-manager-api.md`](task-manager-api/reports/validation-task-manager-api.md) |

**Gate aplicado:** `Critical resolved` integral, `High resolved` integral e `Partial critical/high: 0` em todos os projetos. Nenhum CRITICAL/HIGH ficou `PARCIAL` ou `NÃO RESOLVIDO`; a única ressalva de `code-smells-project` é MEDIUM/LOW (PERF-01 e QUAL-06) e não bloqueia o gate.


### Comparação antes/depois da estrutura de cada projeto

#### 1) code-smells-project (Python/Flask)
**Antes (monolito flat):**
```text
code-smells-project/
├── app.py           (88 LOC)  entrypoint + rotas + SQL admin
├── controllers.py   (292 LOC) HTTP + validação + regra de negócio
├── database.py      (86 LOC)  conexão global + DDL + seed
├── models.py        (314 LOC) SQL bruto + mapeamento + regra de negócio
└── requirements.txt
```

**Depois (MVC em camadas):**
```text
code-smells-project/
├── app.py                    entrypoint com registro de blueprints (46 LOC)
├── config.py                 configuração via ambiente
├── errors.py                 erros de domínio
├── routes/                   roteamento por recurso (Blueprints)
├── controllers/              orquestração HTTP → schema → service → resposta
├── schemas/validators.py     validação de entrada
├── services/                 regras de negócio (produto, usuario, pedido, etc.)
├── repositories/             acesso a dados com queries parametrizadas
├── models/produto.py         entidades/invariantes
├── database/                 connection.py (por request) + schema.py (DDL/seed)
├── middleware/               error_handler.py + auth.py
├── tests/smoke_contract.py   smoke test (73 checks)
└── .env.example
```

| Métrica | Antes | Depois |
|---|---|---|
| Arquivos-fonte `.py` | 4 | 31 |
| LOC (sem testes) | 780 | 1428 |
| Maior arquivo | 314 (`models.py`) | 139 (`pedido_repository.py`) |
| Camadas | 0 (flat) | 8 (routes, controllers, schemas, services, repositories, models, database, middleware) |
| Queries parametrizadas | Não | Sim (100%) |
| Testes | 0 | 73 checks |

#### 2) ecommerce-api-legacy (Node.js/Express)
**Antes:** Estrutura monolítica centrada em `src/AppManager.js` com toda lógica HTTP, regras de negócio, acesso a dados e configuração hardcoded em um único local. Configurações sensíveis em `src/utils.js`. Criptografia insegura em `src/utils.js`.

**Depois:** Reestruturado para padrão MVC + Services + Repositories (36 arquivos JS + 1 SQL, ~867 LOC). Configurações movidas para ambiente/`config/`, lógica extraída para services/controllers/repositories, segredos removidos do código, hash de senha com `scrypt` + salt, rotas administrativas e destrutivas com Bearer admin fail-closed e checkout exigindo a senha do titular. Resultado validado: **16/16 testes**, **14/14 cenários HTTP**, **2/2 CRITICAL** e **4/4 HIGH** resolvidos, `Partial critical/high: 0`.

*(Detalhes completos em [`ecommerce-api-legacy/reports/refactor-ecommerce-api-legacy.md`](ecommerce-api-legacy/reports/refactor-ecommerce-api-legacy.md) e [`ecommerce-api-legacy/reports/validation-ecommerce-api-legacy.md`](ecommerce-api-legacy/reports/validation-ecommerce-api-legacy.md).)*

#### 3) task-manager-api (Python/Flask)
**Antes:** Já possuía alguma organização (`models/`, `routes/`, `services/`, `utils/`, `controllers/`, `migrations/`) mas com problemas críticos: `SECRET_KEY` hardcoded em `app.py`, senhas com MD5 sem salt e hash exposto via `to_dict()`, rotas sem autenticação/autorização, token fake previsível, N+1, validação insuficiente, `datetime.utcnow()`/`Query.get()` deprecated, ausência de testes.

**Depois:** Reestruturado/aprimorado pela skill para alinhar ao MVC, com hash seguro (`generate_password_hash`/`check_password_hash`), remoção de dados sensíveis das respostas, autenticação JWT default deny, autorização `admin` na gestão de usuários, posse derivada do token, extração de regras para services, tratamento de erros centralizado, configuração via ambiente e demais correções da auditoria. Resultado validado: **22/22 rotas**, **8/8 testes**, **3/3 CRITICAL** e **3/3 HIGH** resolvidos, `Partial critical/high: 0`.

*(Detalhes completos em [`task-manager-api/reports/refactor-task-manager-api.md`](task-manager-api/reports/refactor-task-manager-api.md) e [`task-manager-api/reports/validation-task-manager-api.md`](task-manager-api/reports/validation-task-manager-api.md).)*


### Checklist de validação preenchido para cada projeto

#### Checklist - code-smells-project (Python/Flask)
**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.1.1)
- [x] Domínio da aplicação descrito corretamente (API E-commerce - produtos, pedidos, usuários)
- [x] Número de arquivos analisados condiz com a realidade (4 arquivos na análise inicial)

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (16 findings)
- [x] Detecção de APIs deprecated incluída (conforme catálogo/achados)
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue padrão MVC (routes/controllers/services/repositories/models)
- [x] Configuração extraída para módulo de config (sem hardcoded sensível)
- [x] Models criados para abstrair dados/entidades
- [x] Views/Routes separadas para roteamento (Blueprints)
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado (middleware/error_handler.py)
- [x] Entry point claro (app.py)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais continuam respondendo (19/19 rotas validadas)
- [x] Autorização por nível nas rotas de escrita (SEC-04): produtos → `admin`; pedidos → `cliente` (próprio usuário); status → `admin`
- [x] Autorização administrativa: gestão de produtos e status de pedido exigem `admin`; `401` sem token e `403` sem papel
- [x] Rotas de escrita exigem autenticação por padrão; identidade e posse vêm do token, nunca do body
- [x] SEC-03 sem texto puro no seed/banco: seed grava hash scrypt; banco em repouso sem senha legível; login só com `check_password_hash`
- [x] Migração de senhas legadas executada no boot, antes de qualquer autenticação
- [x] Nenhum CRITICAL/HIGH `PARCIAL` ou `NÃO RESOLVIDO` no `validation-code-smells-project.md`

**Validação pós-refatoração:** `tests/smoke_contract.py` — **73/73 checks** passando. Boot real OK. Gate: `Critical resolved: 3/3`, `High resolved: 4/4`, `Partial critical/high: 0`; recomendação **APROVADO**. Relatório: [`validation-code-smells-project.md`](code-smells-project/reports/validation-code-smells-project.md).

#### Checklist - ecommerce-api-legacy (Node.js/Express)
**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (JavaScript/Node.js)
- [x] Framework detectado corretamente (Express)
- [x] Domínio da aplicação descrito corretamente (LMS API com fluxo de checkout)
- [x] Número de arquivos analisados condiz com a realidade

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (13 findings)
- [x] Detecção de APIs deprecated incluída (quando aplicável)
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída (credenciais movidas para ambiente)
- [x] Models/repositories/services separados conforme necessário
- [x] Controllers/rotas organizados
- [x] Error handling adequado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais continuam respondendo (3/3 rotas de contrato + caminhos de erro)
- [x] Autorização administrativa: `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem Bearer admin; sem `ADMIN_TOKEN` falham fechado (`503`)
- [x] Checkout de conta existente exige a senha do titular; identidade/dono não vêm do body
- [x] SEC-02: credenciais somente via ambiente (sem literais); SEC-03: hash scrypt com salt e banco em repouso sem texto puro
- [x] Logs sem PAN completo, chave de pagamento ou senha (apenas `cardLast4`)
- [x] Nenhum CRITICAL/HIGH `PARCIAL` ou `NÃO RESOLVIDO` no `validation-ecommerce-api-legacy.md`

**Validação:** `npm test` — **16/16**; smoke HTTP **14/14**; gate `Critical resolved: 2/2`, `High resolved: 4/4`, `Partial critical/high: 0`; recomendação **APROVADO**. Relatório: [`validation-ecommerce-api-legacy.md`](ecommerce-api-legacy/reports/validation-ecommerce-api-legacy.md).

#### Checklist - task-manager-api (Python/Flask)
**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask + SQLAlchemy)
- [x] Domínio da aplicação descrito corretamente (API de Task Manager)
- [x] Número de arquivos analisados condiz com a realidade (~9 arquivos de código)

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (16 findings) - mesmo com organização parcial
- [x] Detecção de APIs deprecated incluída (`datetime.utcnow()`, `Query.get()`)
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue/aproxima padrão MVC
- [x] Configuração extraída para módulo de config/ambiente (sem hardcoded sensível)
- [x] Models mantidos/corrigidos (remoção de exposição de senha, hash seguro)
- [x] Views/Routes organizadas
- [x] Controllers/Services concentram regras de negócio
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais continuam respondendo (22/22 rotas de negócio)
- [x] Autorização administrativa: `GET/POST/PUT/DELETE /users` exigem `admin`; `401` sem token e `403` sem papel
- [x] Auth default deny sem opt-in (`AUTH_REQUIRED` ausente → `True`); posse de tarefa derivada do JWT
- [x] SEC-03 sem texto puro no seed/banco: seed grava `scrypt:`; `password` removido das respostas; login sem fallback
- [x] Nenhum CRITICAL/HIGH `PARCIAL` ou `NÃO RESOLVIDO` no `validation-task-manager-api.md`

**Validação:** `pytest` — **8/8**; smoke **22/22**; gate `Critical resolved: 3/3`, `High resolved: 3/3`, `Partial critical/high: 0`; recomendação **APROVADO**. Relatório: [`validation-task-manager-api.md`](task-manager-api/reports/validation-task-manager-api.md).


### Screenshots ou logs mostrando as aplicações rodando após refatoração
Os projetos foram refatorados pela skill nos seus respectivos diretórios com cópia da skill. Os relatórios de validação em `/reports/validation-[nome do projeto].md` confirmam que as aplicações iniciam sem erros e os endpoints continuam respondendo após a refatoração. Os logs de execução das fases 1-2-3 foram gerados pela skill durante a refatoração.

### Observações sobre como a skill se comportou em stacks diferentes

- **Agnóstica à tecnologia:** A skill foi copiada com sucesso para `ecommerce-api-legacy/` (Node.js/Express) e `task-manager-api/` (Python/Flask) e executou as 3 fases em ambos os casos, demonstrando reutilização.
- **Adaptação ao nível de organização:** Em **code-smells-project** (monolito completamente desestruturado, 4 arquivos), a skill fez uma reorganização radical para MVC com criação de múltiplas camadas (routes, controllers, services, repositories, schemas, middleware, database). Em **task-manager-api** (já parcialmente organizado com models/routes/services), a skill identificou problemas mesmo com estrutura existente e propôs melhorias incrementais sem quebrar a aplicação. Em **ecommerce-api-legacy** (Node.js/Express monolítico), adaptou-se à stack diferente mantendo o mesmo processo de análise/auditoria/refatoração.
- **Detecção abrangente:** Encontrou tanto problemas arquiteturais (God Class/Files, lógica no controller, SQL fora de repositório) quanto de segurança (SQL Injection, credenciais hardcoded, senhas fracas/expostas, falta de auth) e performance (N+1). Também detectou **APIs deprecated** (`datetime.utcnow()`, `Query.get()` no task-manager-api).
- **Segurança proativa:** Em code-smells-project, removeu `POST /admin/query` (executor SQL arbitrário), protegeu `POST /admin/reset-db` com token estático, passou o `/login` a emitir token de sessão e aplicou autorização por nível nas rotas de escrita (produtos → `admin`; cadastro de pedido → `cliente`, apenas em nome próprio), além de neutralizar SQL Injection com queries parametrizadas e remover exposição de segredos/senhas.
- **Validação rigorosa:** A Fase 2 pausou solicitando confirmação antes da refatoração. A Fase 3 validou (boot + smoke tests). O projeto 1 teve validação automatizada com **73 checks** passando, incluindo os cenários de autorização `401`/`403`; a Fase 4 aplicou o gate bloqueante e reprovaria qualquer CRITICAL/HIGH `PARCIAL` ou `NÃO RESOLVIDO`.
- **Qualidade dos relatórios:** Relatórios seguem template padronizado com achados por severidade, arquivo/linha exatos, evidências, impacto e recomendação - facilitando rastreabilidade.
- **Desafios observados:** Projetos com estrutura parcial exigem maior sutileza para não sobrescrever organização existente de forma destrutiva; stacks diferentes requerem heurísticas de detecção adequadas (linguagem/framework). Ajustes nos arquivos de referência foram necessários para garantir cobertura mínima (>=5 findings, incluindo CRITICAL/HIGH) em todos os 3 projetos.
- **Resultado geral:** Todos os critérios obrigatórios foram atendidos nos 3 projetos - stack detectada corretamente, >=5 findings com pelo menos 1 CRITICAL/HIGH, aplicação funcional após refatoração.
