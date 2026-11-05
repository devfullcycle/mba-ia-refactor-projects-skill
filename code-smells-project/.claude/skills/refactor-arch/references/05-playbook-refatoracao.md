# 05 — Playbook de refatoração

Use na **Fase 3**, depois do baseline. Cada padrão `P-xx` resolve anti-patterns do catálogo (`02-catalogo-antipatterns.md`). Os exemplos são **ilustrativos** (Python, JavaScript e, em alguns, Java/Go): traduza a ideia para a stack real do projeto, preservando suas convenções.

## 0. Regras gerais

1. **Preserve o contrato público** (rotas, métodos, chaves e formato das respostas, status). Padrões que mudam contrato estão marcados **[contrato]** e só se aplicam com `CT-xx` aprovado ou na variante compatível.
2. **Ordem canônica de aplicação** (cada passo seguido de verificação rápida de sintaxe/import — classe B):
   `P-01 config` → `P-18 dependências` (se aprovado) → `P-08 models/dados` (+ `P-02`, `P-17`, `P-10`) → `P-09 services` → `P-07 validação` → `P-04 serialização` → `P-05 auth/admin` → `P-06 erros` → `P-15 logs` → `P-12 async` / `P-11 N+1` → `P-13 DI/composition root` → `P-19 proteções HTTP` → `P-14 deprecated` → `P-16 limpeza`.
3. Dependências entre padrões: P-09 exige P-08; P-13 vem depois de P-08/P-09; P-04 antes de P-05; P-06 antes de remover `str(e)` dos controllers.
4. **Testes** seguem a política de `06-protocolo-validacao.md`, seção 8: adaptar com sentido (T1 mecânica, T2 contrato) é permitido; enfraquecer, remover ou pular teste para fazê-lo passar é **proibido** (T3); testes novos só na Opção 2 (T4).
5. Um padrão por vez; se a validação rápida falhar, corrija ou reverta aquele padrão antes de seguir.
6. Em todo padrão: depois de aplicar, **rebusque** o sinal do anti-pattern no código para confirmar que sumiu.
7. **Opção de contrato (P3 da rodada de perguntas).** Aplique cada padrão conforme a opção escolhida pelo usuário:

| Padrão | Opção 1 — manter o contrato | Opção 2 — atualizar |
|---|---|---|
| P-01, P-02, P-03, P-07, P-08 a P-10, P-12 a P-16, P-18 | aplica | aplica |
| P-06 (erros) | aplica; mantém status e formato do corpo; só deixa de vazar detalhe interno (contrato de erro, listado) | aplica |
| P-04 (campos sensíveis) | **mantém a chave e neutraliza o valor** (ex.: `"senha": null`) | omite o campo + teste de ausência |
| P-05 (auth/admin) | **não aplica**: o finding fica **residual** com a recomendação "reexecutar com a Opção 2" | aplica + testes (sem credencial ⇒ 401/403; com credencial ⇒ sucesso) |
| P-19 (CORS restritivo) | só rate limit e cabeçalhos aditivos; CORS padrão inalterado (residual) | restringe + prova |
| P-11 (paginação), P-17 (tipo numérico) | só se retrocompatível (parâmetro opcional, mesmo formato numérico) | pode mudar contrato + prova |

   Na Opção 2, **cada** mudança de contrato aplicada precisa de prova gerada pela refatoração (`06`, seção 8.9) e de justificativa no anexo (`03`, "Contratos — resultado"). Na Opção 1, nada muda no contrato: o que não puder ser corrigido sem mudá-lo vira residual declarado.

---

## P-01 · Extrair configuração e remover segredos hardcoded
**Resolve:** SEC-02, SEC-05 · **Contrato:** não

**Antes (Python/Flask)**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
app.run(host="0.0.0.0", port=5000, debug=True)
```
**Depois**
```python
# config/settings.py
import os

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY")          # obrigatório em produção
    DEBUG = os.environ.get("APP_DEBUG", "false").lower() == "true"
    HOST = os.environ.get("APP_HOST", "127.0.0.1")
    PORT = int(os.environ.get("APP_PORT", "5000"))

    @classmethod
    def validate(cls):
        if not cls.DEBUG and not cls.SECRET_KEY:
            raise RuntimeError("SECRET_KEY não definida")
```
```python
# app.py
from config.settings import Settings
Settings.validate()
app.config["SECRET_KEY"] = Settings.SECRET_KEY or "dev-only-nao-usar-em-producao"
app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
```
**Antes (Node)**
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_1234567890abcdef", port: 3000 };
```
**Depois**
```js
// config/settings.js
module.exports = {
  port: Number(process.env.PORT || 3000),
  dbPass: process.env.DB_PASS,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
};
```
**Passos:** (1) criar módulo de config; (2) substituir cada literal por leitura de ambiente; (3) adicionar `.env.example` com **nomes** e valores fictícios; (4) garantir que `.env` real esteja no `.gitignore`; (5) falhar de forma clara se um segredo obrigatório faltar fora de dev; (6) manter o comportamento atual do boot (valores de dev padrão) para o projeto continuar subindo.
**Riscos:** o projeto passa a depender de variáveis; deixe o padrão de desenvolvimento funcionando para não quebrar o boot. **O segredo antigo continua no histórico do git — recomende rotacioná-lo** (registre no relatório, não execute nada).
**Validar:** busca por literais de segredo/debug fixo não retorna nada; boot ok.

### Credenciais de seed e dados de demonstração (SEC-02)
Senha de usuário de exemplo/administrador gravada em texto no fonte do seed **é** finding. Não a mantenha só para os testes passarem: adapte a fixture do teste (T1, `06` seção 8).

**Antes (Python)**
```python
db.execute("INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
           ("Admin", "admin@exemplo.com", "admin123", "admin"))
```
**Depois**
```python
# config/settings.py
SEED_ADMIN_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD")        # sem valor padrão no código

# database/schema.py
if Settings.SEED_ADMIN_PASSWORD:                                    # só em dev/teste, e só se definida
    db.execute("INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
               ("Admin", "admin@exemplo.com", hash_password(Settings.SEED_ADMIN_PASSWORD), "admin"))
else:
    logger.warning("seed de usuários ignorado: SEED_ADMIN_PASSWORD não definida")   # nunca imprimir segredo
```
```python
# tests/conftest.py (ajuste T1: só o setup; asserções inalteradas)
os.environ["SEED_ADMIN_PASSWORD"] = "senha-de-teste"
```
**Passos:** (1) mover o literal para variável de ambiente lida pela config; (2) gravar com hash (P-03); (3) seed de usuários só em dev/teste e só se a variável existir; (4) a fixture/setup dos testes define a variável; (5) documentar a variável no `.env.example`.
**Contrato:** se o conjunto de usuários de seed observável por clientes mudar (ex.: listagem sem o admin de exemplo), registre em "Correções que exigem mudança de contrato"; na Opção 1, mantenha o mesmo conjunto de dados quando a variável estiver definida.
**Validar:** busca por senha literal no seed = vazio; a suíte passa com a variável definida pela fixture.

## P-02 · Parametrizar consultas
**Resolve:** SEC-01 · **Contrato:** não

**Antes (Python/sqlite3)**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("INSERT INTO produtos (nome, preco) VALUES ('" + nome + "', " + str(preco) + ")")
```
**Depois**
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute("INSERT INTO produtos (nome, preco) VALUES (?, ?)", (nome, preco))
```
**Antes (Node)** `db.all("SELECT * FROM users WHERE name = '" + name + "'")`
**Depois** `db.all("SELECT * FROM users WHERE name = ?", [name])`
**Java:** `PreparedStatement ps = c.prepareStatement("SELECT * FROM t WHERE id = ?"); ps.setLong(1, id);`
**Cláusulas dinâmicas** (filtros opcionais, `LIKE`): monte a lista de condições com placeholders e uma lista de valores; `LIKE ?` com `f"%{termo}%"` como valor. Nomes de coluna/tabela/ordenação dinâmicos vão por **lista branca**, nunca por parâmetro.
**Passos:** (1) listar todos os pontos do SEC-01; (2) converter um a um; (3) reaplicar a busca do sinal.
**Riscos:** o marcador de placeholder varia por driver (`?`, `%s`, `$1`, `:nome`); use o do driver em uso.
**Validar:** testes/rotas que usam as consultas; busca por concatenação em chamadas de execução = vazio.

## P-03 · Hash de senha com KDF adequado
**Resolve:** SEC-06 · **Contrato:** não (mas formato armazenado muda)

**Antes** `self.password = hashlib.md5(pwd.encode()).hexdigest()` / `senha = dados["senha"]` gravada em texto.
**Depois (Python)**
```python
from werkzeug.security import generate_password_hash, check_password_hash   # ou bcrypt/argon2
def set_password(self, pwd): self.password = generate_password_hash(pwd)
def check_password(self, pwd): return check_password_hash(self.password, pwd)
```
**Depois (Node)** `const hash = await bcrypt.hash(pwd, 12); const ok = await bcrypt.compare(pwd, hash);` (use `argon2`/`scrypt` nativo se não quiser nova dependência: `crypto.scryptSync`).
**Migração sem quebrar logins:** na verificação, se o valor armazenado estiver no formato antigo (texto puro, MD5 de 32 hex, etc.), compare no formato antigo **uma vez** e, se bater, regrave com o novo hash. Dados já gravados **não** são convertidos em lote (isso exigiria a senha).
**Passos:** (1) escolher a biblioteca já disponível na stack/projeto (evite nova dependência sem necessidade; se precisar, é P-18/classe C); (2) trocar gravação e comparação; (3) implementar rehash no login; (4) nunca devolver o hash (P-04); (5) não gerar senha padrão fraca.
**Validar:** criar usuário e logar (testes existentes ou rota do projeto); registrar que usuários antigos migram no próximo login.

## P-04 · Serialização de saída sem campos sensíveis (DTO)
**Resolve:** SEC-07 · **Contrato:** depende da opção (matriz da seção 0, regra 7): **Opção 1** neutraliza o valor e mantém a chave; **Opção 2** omite o campo **[contrato]**

**Antes**
```python
def to_dict(self): return {"id": self.id, "email": self.email, "password": self.password}
return jsonify({"secret_key": app.config["SECRET_KEY"], "debug": True, "db_path": "app.db"})
```
**Depois**
```python
PUBLIC_FIELDS = ("id", "nome", "email", "role")
def user_to_public(u): return {k: getattr(u, k) for k in PUBLIC_FIELDS}
# health: apenas {"status": "ok", "database": "connected", "counts": {...}}
```
**Node:** `const toPublic = ({ id, name, email }) => ({ id, name, email });`
**Passos:** (1) criar função/serializador de saída por entidade com **lista branca** de campos; (2) usar em todas as rotas que devolvem a entidade; (3) remover configuração interna do endpoint de saúde; (4) listar no relatório os campos removidos como mudança de contrato.
**Opção 1 (manter contrato):** o serializador devolve **as mesmas chaves**, com valor neutralizado nos campos sensíveis: `{"id": 1, "email": "a@b.c", "senha": None}`; em saúde/diagnóstico, `"secret_key": None`, `"db_path": None`, `"debug": False`. O formato não muda; o vazamento some. Registre o ajuste em "Mudanças aplicadas".
**Opção 2 (atualizar):** omite o campo (lista branca acima) e **prova** com teste: `assert "senha" not in resposta.json()[0]` (T4), verde no código refatorado e vermelho no checkpoint (`06`, seção 8.9). Preencha a justificativa e a prova no anexo.
**Validar:** Opção 1: rota igual (mesmas chaves) e nenhum valor sensível na resposta; Opção 2: rota igual exceto campos removidos (`ALTERADO (aprovado)`) com `E-nn`.

## P-05 · Autenticação/autorização e proteção de rotas administrativas
**Resolve:** SEC-03, SEC-04, SEC-09, SEC-10, SEC-11 · **Contrato:** **[contrato]** — **só na Opção 2** (rotas passam a exigir credencial ou são removidas). Na Opção 1 este padrão **não é aplicado**: os findings ficam residuais com a recomendação "reexecutar com a Opção 2".

**Variantes:**
- **Remover** (padrão para execução de SQL/comando arbitrário vindo do cliente — SEC-04): apagar a rota e o handler. `CT-xx` obrigatório.
- **Proteger** (reset, relatórios, exclusão): exigir autenticação + perfil e, para ações destrutivas, flag explícita de ambiente.
- **Autorização de propriedade** (SEC-11): comparar o dono do recurso com a identidade autenticada.
- **Privilégio** (SEC-10): descartar `role`/`active` do corpo salvo se o chamador for admin.

**Depois (Python — decorador)**
```python
def require_role(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            user = authenticate(request)               # valida token/sessão de verdade
            if not user: return jsonify({"erro": "não autenticado"}), 401
            if roles and user.role not in roles: return jsonify({"erro": "sem permissão"}), 403
            g.user = user
            return fn(*a, **kw)
        return wrapper
    return deco

@app.post("/admin/reset-db")
@require_role("admin")
def reset_db():
    if not Settings.ALLOW_DESTRUCTIVE: return jsonify({"erro": "desabilitado"}), 403
```
**Depois (Node)**
```js
const requireRole = (...roles) => (req, res, next) => {
  const user = authenticate(req);
  if (!user) return res.status(401).json({ erro: "não autenticado" });
  if (roles.length && !roles.includes(user.role)) return res.status(403).json({ erro: "sem permissão" });
  req.user = user; next();
};
router.delete("/api/users/:id", requireRole("admin"), usersController.remove);
```
**Passos:** (1) se o projeto **não tem** mecanismo de identidade, introduza o mínimo compatível com a stack já usada (token assinado com chave da config, p. ex. JWT) **ou** proteja as rotas críticas por chave de administração vinda do ambiente e pergunte ao usuário qual caminho prefere (decisão de design, não presuma); (2) um único middleware/decorador; (3) aplicar nas rotas listadas como administrativas/destrutivas e em todas que expõem dados de usuários; (4) corrigir o login para emitir credencial verificável; (5) registrar mudanças de contrato (clientes passam a enviar credencial).
**Riscos:** quebra clientes existentes — por isso é `CT-xx` e só se aplica com a Opção 2.
**Provas exigidas (Opção 2, `06` seção 8.9)** — exemplo de testes no framework existente (T4/T2):
```python
def test_relatorio_exige_token(client):
    assert client.get("/relatorios/vendas").status_code == 401            # sem credencial
    assert client.get("/relatorios/vendas", headers={"Authorization": "Bearer invalido"}).status_code == 401

def test_relatorio_com_token_admin(client, admin_token):
    r = client.get("/relatorios/vendas", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200                                              # asserção original mantida
```
Cada teste: verde no código refatorado e, quando viável, **vermelho** no checkpoint do código original (prova de sensibilidade). Rota removida: `assert client.post("/admin/query", json={...}).status_code in (404, 405)`.
**Validar:** rota sem credencial ⇒ 401/403; com credencial ⇒ comportamento original; evidências `E-nn` no anexo (nada destrutivo em sondagem ad hoc).

## P-06 · Tratamento de erros centralizado
**Resolve:** SEC-13, ARC-09 · **Contrato:** pode alterar o corpo de erros 500 (formato/mensagem)

**Antes**
```python
except Exception as e:
    return jsonify({"erro": str(e)}), 500
```
**Depois (Python/Flask)**
```python
class AppError(Exception):
    def __init__(self, message, status=400): self.message, self.status = message, status

@app.errorhandler(AppError)
def handle_app_error(e): return jsonify({"erro": e.message, "sucesso": False}), e.status

@app.errorhandler(Exception)
def handle_unexpected(e):
    logger.exception("erro não tratado")             # detalhe só no log
    return jsonify({"erro": "Erro interno", "sucesso": False}), 500
```
**Depois (Express)**
```js
class AppError extends Error { constructor(msg, status = 400) { super(msg); this.status = status; } }
app.use((err, req, res, next) => {
  if (err instanceof AppError) return res.status(err.status).json({ erro: err.message });
  logger.error(err);
  res.status(500).json({ erro: "Erro interno" });
});
```
**Passos:** (1) criar a classe de erro de domínio e o handler global; (2) substituir `try/except` repetidos por `raise AppError`/`next(err)` nos controllers; (3) trocar `except:` nu por captura específica; (4) em callbacks, sempre tratar `err`; (5) manter códigos de status e chaves do envelope existente.
**Validar:** rota com entrada inválida devolve o mesmo status de antes; erro interno não vaza detalhe.

## P-07 · Validação de entrada na borda
**Resolve:** SEC-12, SEC-10, SEC-14 · **Contrato:** pode transformar 500 em 400 (melhoria)

**Antes** `preco = dados["preco"]; estoque = dados["estoque"]  # sem checar tipo/faixa`
**Depois (Python)**
```python
def parse_produto(dados):
    if not isinstance(dados, dict): raise AppError("JSON inválido")
    nome = (dados.get("nome") or "").strip()
    if not 1 <= len(nome) <= 200: raise AppError("nome inválido")
    try: preco = Decimal(str(dados["preco"]))
    except (KeyError, InvalidOperation): raise AppError("preco inválido")
    if preco <= 0: raise AppError("preco deve ser positivo")
    quantidade = dados.get("quantidade")
    if not isinstance(quantidade, int) or quantidade <= 0: raise AppError("quantidade deve ser inteiro positivo")
    return {"nome": nome, "preco": preco}
```
**Depois (Node)**
```js
const { z } = require("zod");               // ou validação manual se não quiser dependência
const schema = z.object({ email: z.string().email(), c_id: z.number().int().positive() });
```
**Passos:** (1) listar entradas por rota (Superfície de ataque); (2) criar funções/esquemas de validação por entidade; (3) chamar no controller antes de qualquer efeito; (4) lista branca de campos aceitos (mass assignment); (5) preço/total sempre calculados no servidor.
**Riscos:** não endureça além do comportamento aceito hoje sem aprovação (ex.: não rejeite campos que clientes legítimos enviam); registre regras novas.
**Validar:** entradas válidas continuam passando; inválidas dão 4xx.

## P-08 · Extrair Models/Repositórios do God File/Class
**Resolve:** ARC-01, ARC-04, ARC-06 · **Contrato:** não

**Antes (Node)** — classe única que cria banco, schema, seed, rotas e regras (ex.: uma classe `*Manager`).
**Depois**
```
src/
├── config/settings.js
├── database/connection.js         # cria e exporta a conexão (composition root injeta)
├── database/schema.js             # DDL + seed (somente dev)
├── models/userModel.js            # queries parametrizadas
├── models/courseModel.js
├── services/checkoutService.js
├── controllers/checkoutController.js
├── routes/index.js
├── middlewares/errorHandler.js
└── app.js                         # composition root
```
**Antes (Python)** — `models.py` com 4 domínios + `database.py` com schema e seed.
**Depois** `models/produto_model.py`, `models/usuario_model.py`, `models/pedido_model.py`; `database/connection.py`; `database/schema.py`.
**Passos:** (1) mapear funções/classes por domínio; (2) mover **sem alterar comportamento**; (3) mantém assinaturas; (4) ajustar imports; (5) manter um módulo de compatibilidade só se necessário para não quebrar testes existentes (re-export), e removê-lo se nada depender dele; (6) registrar o mapa antigo→novo.
**Validar:** imports compilam; testes/rotas iguais.

## P-09 · Extrair Service da lógica de negócio do controller
**Resolve:** ARC-02, SEC-14 · **Contrato:** não

**Antes**
```python
def criar_pedido():
    dados = request.get_json()
    total = 0
    for item in dados["itens"]:
        produto = models.get_produto_por_id(item["produto_id"])
        if produto["estoque"] < item["quantidade"]: return jsonify({"erro": "sem estoque"}), 400
        total += produto["preco"] * item["quantidade"]
    ...
```
**Depois**
```python
# services/pedido_service.py
def criar_pedido(usuario_id, itens, produtos_repo, pedidos_repo):
    total = Decimal(0)
    for item in itens:
        produto = produtos_repo.obter(item["produto_id"])
        if produto is None: raise AppError("produto não encontrado", 404)
        if produto["estoque"] < item["quantidade"]: raise AppError("sem estoque", 400)
        total += produto["preco"] * item["quantidade"]
    return pedidos_repo.criar(usuario_id, itens, total)

# controllers/pedido_controller.py
def criar():
    dados = parse_pedido(request.get_json())
    pedido_id = pedido_service.criar_pedido(dados["usuario_id"], dados["itens"], produtos_repo, pedidos_repo)
    return jsonify({"dados": {"pedido_id": pedido_id}, "sucesso": True}), 201
```
**Passos:** (1) identificar regra no handler; (2) mover para função/classe de service que recebe dependências; (3) controller só valida e traduz; (4) preço/total e aprovação de pagamento calculados/decididos no servidor — em fluxo de pagamento simulado, isole o gateway atrás de uma interface (`PaymentGateway`) e mantenha o comportamento de teste atual, **sinalizando** no relatório que a integração real é necessária.
**Validar:** mesmas respostas; regra testável sem HTTP.

## P-10 · Transações, atomicidade e integridade referencial
**Resolve:** SEC-15, ARC-10 · **Contrato:** não (schema: ver riscos)

**Antes** loop que verifica estoque e outro que grava, sem transação.
**Depois (Python/sqlite3)**
```python
def criar_pedido(db, usuario_id, itens):
    try:
        db.execute("BEGIN")
        total = 0
        for it in itens:
            cur = db.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                             (it["quantidade"], it["produto_id"], it["quantidade"]))
            if cur.rowcount == 0: raise AppError("sem estoque", 400)   # check-and-set atômico
            ...
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK"); raise
```
**Node (callbacks→promises):** agrupe `INSERT`s em `BEGIN … COMMIT` com `ROLLBACK` no erro; não ignore `err`.
**Integridade:** acrescente `UNIQUE`, `NOT NULL` e FK no DDL **de criação** do schema; para bancos já existentes, mudar schema é migração (**classe D**, pergunta individual) — nesse caso apenas registre a recomendação.
**Validar:** fluxo feliz igual; simular falha no meio não deixa estado parcial (apenas com testes existentes ou banco descartável).

## P-11 · Eliminar N+1, paginação e `SELECT *`
**Resolve:** ARC-07, ARC-11 · **Contrato:** paginação só se for opcional/retrocompatível

**Antes**
```python
for pedido in pedidos:
    itens = db.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (pedido["id"],)).fetchall()
    for it in itens:
        it["produto"] = db.execute("SELECT nome FROM produtos WHERE id = ?", (it["produto_id"],)).fetchone()
```
**Depois**
```python
rows = db.execute("""SELECT p.id AS pedido_id, i.quantidade, i.preco_unitario, pr.nome
                     FROM pedidos p JOIN itens_pedido i ON i.pedido_id = p.id
                     JOIN produtos pr ON pr.id = i.produto_id
                     WHERE p.usuario_id = ?""", (usuario_id,)).fetchall()
# agrupar por pedido_id em memória
```
**SQLAlchemy:** `joinedload`/`selectinload`; contagens com `func.count()` em vez de `.all()` + `len`. **Node:** um `JOIN` + `GROUP BY` em vez de callbacks aninhados por linha.
**Cuidado:** preserve ordem e formato do resultado (ordene explicitamente quando a ordem anterior era implícita).
**Validar:** resposta idêntica (mesmas chaves e valores) à do baseline.

## P-12 · Callbacks → async/await
**Resolve:** ARC-05 · **Contrato:** não

**Antes** `db.get(q1, [a], (err, x) => { db.get(q2, [x.id], (err, y) => { ... }) })`
**Depois**
```js
const get = (sql, params) => new Promise((res, rej) => db.get(sql, params, (e, r) => e ? rej(e) : res(r)));
const run = (sql, params) => new Promise((res, rej) => db.run(sql, params, function (e) { e ? rej(e) : res(this); }));

router.post("/api/checkout", asyncHandler(async (req, res) => {
  const course = await get("SELECT * FROM courses WHERE id = ? AND active = 1", [cid]);
  if (!course) throw new AppError("Curso não encontrado", 404);
  ...
}));
```
`asyncHandler = fn => (req, res, next) => fn(req, res, next).catch(next)` (encaminha ao handler global — P-06). **Python:** `async`/`await` só se o framework/driver já forem assíncronos; não troque o modelo de concorrência de uma app síncrona.
**Cuidado:** relatórios que montavam resposta por contadores devem manter ordem determinística (ordene).
**Validar:** mesma resposta para a mesma entrada.

## P-13 · Injeção de dependência e composition root
**Resolve:** ARC-03, ARC-04 · **Contrato:** não

**Antes** `from database import get_db` em cada módulo; `globalCache = {}` mutado em qualquer lugar; `new sqlite3.Database(':memory:')` dentro de uma classe.
**Depois (Node)**
```js
// app.js
const db = createConnection(settings);
const userModel = createUserModel(db);
const checkoutService = createCheckoutService({ userModel, courseModel, paymentGateway });
const app = buildApp({ checkoutService, settings });
```
**Depois (Python)**
```python
def create_app(settings=None):
    app = Flask(__name__)
    db = create_connection(settings or Settings)          # uma conexão por requisição/contexto, não global compartilhada
    app.extensions["produto_repo"] = ProdutoRepo(db)
    register_routes(app); register_error_handlers(app)
    return app
```
**Passos:** (1) criar `create_app`/`buildApp`; (2) instanciar infraestrutura só ali; (3) passar dependências por parâmetro/construtor; (4) substituir estado global por objeto com ciclo de vida definido (cache com limite ou removido se nunca lido); (5) manter o comando de execução original funcionando (`python app.py` / `npm start`).
**Validar:** boot idêntico; testes existentes continuam importando o que precisam.

## P-14 · Substituir APIs deprecated
**Resolve:** DEP-01…DEP-05 · **Contrato:** não

| Antes | Depois |
|---|---|
| `datetime.utcnow()` | `datetime.now(timezone.utc)` (atenção: devolve datetime *aware*; se o código compara com valores *naive*, converta a referência também) |
| `Model.query.get(id)` | `db.session.get(Model, id)` |
| `@app.before_first_request` | inicialização dentro de `create_app()` |
| `new Buffer(x)` | `Buffer.from(x)` / `Buffer.alloc(n)` |
| `url.parse(u)` | `new URL(u)` |
| `crypto.createCipher` | `crypto.createCipheriv` com IV aleatório |
| `body-parser` standalone | `express.json()` / `express.urlencoded()` |
**Passos:** (1) substituir ocorrência a ocorrência; (2) atenção a diferenças de tipo/retorno (ex.: `session.get` devolve `None`, não lança); (3) confirme a versão suportada antes de trocar.
**Validar:** testes/rotas; ausência de warnings de deprecation no boot (registre a saída).

## P-15 · Logging estruturado com mascaramento
**Resolve:** SEC-08, QLT-04 · **Contrato:** não

**Antes** `print("Login bem-sucedido: " + email)` · `console.log(\`Processando cartão ${cc} na chave ${key}\`)`
**Depois**
```python
import logging
logger = logging.getLogger("app")
def mask(v, keep=4): return (v[:keep] + "***") if v else v
logger.info("login ok user_id=%s", user.id)             # identificador, não e-mail/senha/cartão
logger.info("pagamento processado last4=%s", cc[-4:])
```
```js
logger.info({ msg: "pagamento processado", last4: cc.slice(-4) });   // nunca o número completo nem a chave
```
**Passos:** (1) usar o logger da stack (`logging`, `pino`/`winston`, `slf4j`); (2) nunca logar cartão, senha, token, chave; (3) níveis corretos; (4) configuração em um ponto (config).
**Validar:** busca por logs com variáveis sensíveis = vazio.

## P-16 · Constantes, duplicação e código morto
**Resolve:** QLT-01, QLT-02, QLT-03, QLT-05, ARC-08 · **Contrato:** não

**Antes** `if total > 10000: desconto = 0.1 elif total > 5000: desconto = 0.05` · `def f(id, u, cc): ...` · import sem uso.
**Depois**
```python
DESCONTOS = ((10000, Decimal("0.10")), (5000, Decimal("0.05")), (1000, Decimal("0.02")))   # constants.py
def calcular_desconto(total): return next((d for limite, d in DESCONTOS if total > limite), Decimal(0))
```
**Passos:** (1) extrair constantes nomeadas/enums; (2) função única para blocos repetidos ≥ 3×; (3) renomear identificadores ruins **somente internamente** (nunca chaves de payload/API sem aprovação); (4) remover imports/funções mortos **depois de buscar usos em todo o projeto** (incluindo testes); (5) serviço nunca usado: ou conecte-o ao fluxo (se for claramente a intenção) ou remova e registre.
**Validar:** testes/rotas inalterados.

## P-17 · Dinheiro em tipo exato
**Resolve:** ARC-12 · **Contrato:** pode mudar tipo numérico na resposta (cuide do formato)

**Antes** `preco REAL` / `float`. **Depois** inteiro em centavos ou `Decimal`/`NUMERIC`; converta na borda (entrada/saída) mantendo o **mesmo formato numérico** das respostas atuais (ex.: valor com 2 casas).
**Cuidado:** mudar o tipo da coluna é migração (classe D); sem aprovação, mantenha a coluna e converta em código com `Decimal` + arredondamento explícito (`ROUND_HALF_UP`).
**Validar:** totais iguais aos do baseline para os mesmos dados.

## P-18 · Dependências: atualizar, fixar e remover não usadas
**Resolve:** SEC-16 · **Contrato:** não

Remova do manifesto pacotes declarados e nunca importados (confirme por busca); fixe versões onde estavam soltas; **não atualize majors** sem aprovação (classe C + risco). Sugira `pip-audit`/`npm audit` no relatório como passo manual ou, se o usuário permitir, execute (classe C, usa rede).
**Validar:** instalar (se permitido) e rodar a validação; sem imports quebrados.

## P-19 · Proteções HTTP básicas
**Resolve:** SEC-17, SEC-09 (CORS) · **Contrato:** cabeçalhos de segurança e rate limit são aditivos (Opção 1 e 2); **restringir o CORS padrão afeta clientes de outras origens** e só se aplica na Opção 2 (com prova)

```js
app.use(helmet());
app.use(rateLimit({ windowMs: 60_000, max: 100 }));
app.use(cors({ origin: settings.corsOrigins }));        // lista vinda da config
```
```python
CORS(app, origins=Settings.CORS_ORIGINS)                 # lista branca; padrão = origem do próprio front, não "*"
```
Use as bibliotecas já presentes ou equivalentes simples; se exigir nova dependência, é P-18/classe C.
**Cuidado:** limites de taxa muito baixos quebram clientes; use padrões conservadores e configuráveis.
**Validar:** rotas continuam respondendo; cabeçalhos presentes (inspecione uma resposta).
