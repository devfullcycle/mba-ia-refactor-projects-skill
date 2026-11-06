# Audit Report — code-smells-project

> Gerado pela skill `refactor-arch` (Fase 2 — Auditoria).
> Data: 2026-11-05 | Raiz: `/home/eric-ogata/codes/full_cycle/mba_engenharia_ia/desafios/desafio3/mba-ia-refactor-projects-skill/code-smells-project` | Baseado na análise de: `reports/analysis-code-smells-project.md`
> Reexecução da Etapa 6: os achados abaixo são os da auditoria original e servem de critério de aceite para a validação. Os critérios objetivos de fechamento de CRITICAL/HIGH foram adicionados na seção 2.1.

## 1. Resumo

| Métrica | Valor |
|---|---|
| Arquivos auditados | 4 arquivos, 780 LOC |
| Total de achados | 16 |
| CRITICAL | 3 |
| HIGH | 4 |
| MEDIUM | 5 |
| LOW | 4 |

## 2. Achados detalhados

---

### [CRITICAL] SEC-01 — SQL Injection

**Onde:**
- `models.py:28`, `models.py:47-50`, `models.py:57-61`, `models.py:68`
- `models.py:92`, `models.py:109-111`, `models.py:126-129`
- `models.py:140`, `models.py:148-151`, `models.py:158-161`, `models.py:163-166`
- `models.py:174`, `models.py:188`, `models.py:192`, `models.py:220`, `models.py:224`
- `models.py:279-281`, `models.py:289-299`
- `app.py:69` (com `app.py:62`)

**Evidência:**
```python
# models.py:47-50
cursor.execute(
    "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES ('" +
    nome + "', '" + descricao + "', " + str(preco) + ", " + str(estoque) + ", '" + categoria + "')"
)

# models.py:109-111 (login: email e senha do usuário)
cursor.execute(
    "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
)

# models.py:289-299 (filtros de busca vindos da query string)
query = "SELECT * FROM produtos WHERE 1=1"
if termo:
    query += " AND (nome LIKE '%" + termo + "%' OR descricao LIKE '%" + termo + "%')"
if categoria:
    query += " AND categoria = '" + categoria + "'"
...
cursor.execute(query)

# app.py:62-69 (executa o que vier no body)
query = dados.get("sql", "")
...
cursor.execute(query)
```

**Impacto:** Toda entrada de usuário (body, query string, path) é concatenada diretamente na query. Um cliente pode enviar `' OR '1'='1`, `'; DROP TABLE produtos; --` ou fazer login com `" OR "1"="1` e contornar a autenticação. O endpoint `/admin/query` (`app.py:59-78`) transforma isso em execução de SQL arbitrário completo — equivalente a comprometimento total do banco.

**Recomendação:** Parametrizar todas as queries com placeholders `?`:
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha_hash))

query = "SELECT * FROM produtos WHERE 1=1"
params = []
if termo:
    query += " AND (nome LIKE ? OR descricao LIKE ?)"
    params += [f"%{termo}%", f"%{termo}%"]
if categoria:
    query += " AND categoria = ?"
    params.append(categoria)
cursor.execute(query, params)
```
E remover o endpoint `/admin/query` — nenhuma aplicação deve aceitar SQL do cliente.

**Referência:** `references/anti-patterns.md` → SEC-01

---

### [CRITICAL] SEC-02 — Credenciais hardcoded e vazadas em resposta HTTP

**Onde:** `app.py:7`, `controllers.py:289`

**Evidência:**
```python
# app.py:7
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"

# controllers.py:288-289 (dentro da resposta de /health)
"debug": True,
"secret_key": "minha-chave-super-secreta-123"
```

**Impacto:** O segredo da aplicação está no código-fonte (e no histórico do git) e, além disso, é devolvido publicamente pela rota `GET /health`, que não exige autenticação. Qualquer cliente anônimo obtém a chave usada para assinar sessões/cookies, permitindo forjar estado autenticado.

**Recomendação:** Ler de ambiente, nunca retornar segredos na API:
```python
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
```
Remover as chaves `secret_key`, `db_path` e `debug` da resposta de `/health`.

**Referência:** `references/anti-patterns.md` → SEC-02

---

### [CRITICAL] SEC-03 — Senhas em texto plano (sem hashing)

**Onde:** `database.py:76-78`, `database.py:81`, `models.py:109-111`, `models.py:126-129`, `models.py:79-86`, `models.py:95-102`

**Evidência:**
```python
# database.py:75-82 — seed com senhas literais
usuarios = [
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
]
cursor.executemany(
    "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
    usuarios
)

# models.py:105-111 — comparação direta da senha em claro
def login_usuario(email, senha):
    cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
```

**Impacto:** As senhas são persistidas e comparadas em texto puro. Um vazamento do arquivo `loja.db` expõe todas as credenciais; o seed ainda publica senhas de exemplo conhecidas. As funções `get_todos_usuarios` (`models.py:72-87`) e `get_usuario_por_id` (`models.py:89-103`) devolvem o campo `senha` nas respostas HTTP.

**Recomendação:** Aplicar hashing com salt antes de persistir e comparar hashes:
```python
from werkzeug.security import generate_password_hash, check_password_hash

# criar_usuario
senha_hash = generate_password_hash(senha)
cursor.execute("INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
               (nome, email, senha_hash, tipo))

# login_usuario
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
row = cursor.fetchone()
if row and check_password_hash(row["senha"], senha):
    ...
```
E nunca incluir `senha` nos dicts de resposta.

**Referência:** `references/anti-patterns.md` → SEC-03 (e SEC-06 para exposição em log/resposta)

---

### [HIGH] SEC-04 — Rotas sem autenticação/autorização

**Onde:** `app.py:47-57`, `app.py:59-78`, `app.py:14-16`, `app.py:23-26`

**Evidência:**
```python
# app.py:47-57 — apaga todas as tabelas, sem auth
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
    db.commit()

# app.py:14-16 — escrita em produtos sem auth
app.add_url_rule("/produtos", "criar_produto", controllers.criar_produto, methods=["POST"])
app.add_url_rule("/produtos/<int:id>", "atualizar_produto", controllers.atualizar_produto, methods=["PUT"])
app.add_url_rule("/produtos/<int:id>", "deletar_produto", controllers.deletar_produto, methods=["DELETE"])
```

**Impacto:** Operações destrutivas e de escrita estão expostas a qualquer cliente anônimo. `POST /admin/reset-db` apaga catálogo, usuários e pedidos; `PUT/DELETE /produtos/<id>` permite alterar ou remover itens; `POST /pedidos` e `PUT /pedidos/<id>/status` mudam estado sem qualquer verificação de identidade. O `POST /login` (`controllers.py:167-186`) autentica mas não emite token nem cria sessão — depois do login não existe credencial para proteger as demais rotas.

**Recomendação:** Emitir token no login (JWT/sessão assinada) e adicionar guarda nas rotas sensíveis:
```python
@app.route("/admin/reset-db", methods=["POST"])
@require_admin           # decorator que valida token + tipo == "admin"
def reset_database():
    ...
```
No mínimo, restringir `/admin/*` a administradores e exigir sessão válida nos verbos de escrita.

**Referência:** `references/anti-patterns.md` → SEC-04

---

### [HIGH] ARCH-01 — Lógica de negócio no Controller

**Onde:** `controllers.py:24-62`, `controllers.py:64-96`, `controllers.py:188-220`, `controllers.py:237-255`

**Evidência:**
```python
# controllers.py:43-54 — regras de domínio (preço, estoque, tamanho, categorias válidas)
if preco < 0:
    return jsonify({"erro": "Preço não pode ser negativo"}), 400
if estoque < 0:
    return jsonify({"erro": "Estoque não pode ser negativo"}), 400
if len(nome) < 2:
    return jsonify({"erro": "Nome muito curto"}), 400
if len(nome) > 200:
    return jsonify({"erro": "Nome muito longo"}), 400
categorias_validas = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
if categoria not in categorias_validas:
    return jsonify({"erro": "Categoria inválida. Válidas: " + str(categorias_validas)}), 400

# controllers.py:205-210 — decisão de negócio + notificações no handler
if "erro" in resultado:
    return jsonify({"erro": resultado["erro"], "sucesso": False}), 400
print("ENVIANDO EMAIL: Pedido " + str(resultado["pedido_id"]) + " criado para usuario " + str(usuario_id))
print("ENVIANDO SMS: Seu pedido foi recebido!")
print("ENVIANDO PUSH: Novo pedido recebido pelo sistema")

# controllers.py:247-250 — transição de estado com efeitos colaterais
if novo_status == "aprovado":
    print("NOTIFICAÇÃO: Pedido " + str(pedido_id) + " foi aprovado! Preparar envio.")
if novo_status == "cancelado":
    print("NOTIFICAÇÃO: Pedido " + str(pedido_id) + " cancelado. Devolver estoque.")
```

**Impacto:** Os handlers acumulam regras de domínio (faixas válidas de categoria, limites de nome, transições de status), efeitos colaterais (notificações) e orquestração de persistência. A mesma validação é duplicada em `criar_produto` e `atualizar_produto`. Não há como testar as regras sem subir o Flask e um banco real.

**Recomendação:** Extrair casos de uso para uma camada de serviço; o controller só traduz HTTP ↔ domínio:
```python
def criar_produto():
    resultado = ProdutoService.criar(request.get_json())
    return jsonify(resultado.body), resultado.status
```
Centralizar validação em um schema (marshmallow/pydantic) e as notificações em um `NotificationService`.

**Referência:** `references/anti-patterns.md` → ARCH-01

---

### [HIGH] ARCH-02 — Acesso a dados no Controller (e no entrypoint)

**Onde:** `controllers.py:266-274` (`health_check`), `app.py:49-55` (`reset_database`), `app.py:66-76` (`executar_query`)

**Evidência:**
```python
# controllers.py:266-274
db = get_db()
cursor = db.cursor()
cursor.execute("SELECT 1")
cursor.execute("SELECT COUNT(*) FROM produtos")
produtos = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM usuarios")
usuarios = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM pedidos")
pedidos = cursor.fetchone()[0]

# app.py:49-55
db = get_db()
cursor = db.cursor()
cursor.execute("DELETE FROM itens_pedido")
cursor.execute("DELETE FROM pedidos")
```

**Impacto:** SQL bruto aparece em três camadas de arquivos diferentes (`app.py`, `controllers.py`, `models.py`), sem repositório único. Mudar a engine ou o schema obriga a alterar handlers HTTP.

**Recomendação:** Mover toda query para repositórios/`models`; o controller chama `HealthService.carregar_contadores()` e o admin chama `DatabaseAdminService.reset()`.

**Referência:** `references/anti-patterns.md` → ARCH-02

---

### [HIGH] QUAL-02 — Validação de entrada ausente ou frágil

**Onde:** `controllers.py:30-54`, `controllers.py:74-90`, `controllers.py:153-158`, `controllers.py:169-170`, `controllers.py:190-201`, `controllers.py:239-242`, `app.py:61-64`

**Evidência:**
```python
# controllers.py:167-174 — get_json() pode ser None → AttributeError → 500
def login():
    dados = request.get_json()
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

# controllers.py:237-243 — mesmo padrão
def atualizar_status_pedido(pedido_id):
    dados = request.get_json()
    novo_status = dados.get("status", "")
    if novo_status not in ["pendente", "aprovado", "enviado", "entregue", "cancelado"]:
        return jsonify({"erro": "Status inválido"}), 400

# controllers.py:43-46 — sem checagem de tipo; string causa TypeError → 500
if preco < 0:
    return jsonify({"erro": "Preço não pode ser negativo"}), 400
```

**Impacto:** Sem JSON no body (ou com `Content-Type` errado), `dados` é `None` e o handler estoura `AttributeError`, devolvendo 500 em vez de 400. Campos como `preco`, `estoque`, `quantidade` e `usuario_id` não têm validação de tipo: `{"preco": "abc"}` gera `TypeError` na comparação. Nenhum campo é validado no `criar_pedido` além de presença.

**Recomendação:** Validar com schema antes de qualquer lógica:
```python
from pydantic import BaseModel, ValidationError, Field

class LoginInput(BaseModel):
    email: str
    senha: str

try:
    payload = LoginInput(**request.get_json(silent=True) or {})
except ValidationError as e:
    return jsonify({"erro": e.errors()}), 400
```

**Referência:** `references/anti-patterns.md` → QUAL-02

---

### [MEDIUM] ARCH-03 — Model com responsabilidades duplas

**Onde:** `models.py` (arquivo inteiro; representativo em `models.py:133-169` e `models.py:235-273`)

**Evidência:**
```python
# models.py:133-169 — "model" que faz query, regra de negócio e transação
def criar_pedido(usuario_id, itens):
    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = " + str(item["produto_id"]))
        produto = cursor.fetchone()
        if produto is None:
            return {"erro": "Produto " + str(item["produto_id"]) + " não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": "Estoque insuficiente para " + produto["nome"]}
        total = total + (produto["preco"] * item["quantidade"])
    ...

# models.py:256-262 — regra de desconto dentro de relatorio_vendas
desconto = 0
if faturamento > 10000:
    desconto = faturamento * 0.1
elif faturamento > 5000:
    desconto = faturamento * 0.05
elif faturamento > 1000:
    desconto = faturamento * 0.02
```

**Impacto:** `models.py` mistura três papéis: SQL/persistência, mapeamento linha→dict (repetido ~7 vezes) e regras de negócio (cálculo de total, verificação de estoque, faixas de desconto). Viola SRP e impede testar a regra de desconto sem banco.

**Recomendação:** Separar em `repositories/` (acesso a dados), `models/` (entidades e invariantes) e `services/` (total, estoque, desconto), com um helper de mapeamento único.

**Referência:** `references/anti-patterns.md` → ARCH-03

---

### [MEDIUM] QUAL-01 — God File

**Onde:** `models.py` (314 LOC), `controllers.py` (292 LOC)

**Evidência:**
```
314 models.py        # produtos + usuarios + autenticacao + pedidos + relatorios
292 controllers.py   # handlers de 4 dominios distintos
```
```python
# models.py:1-2
from database import get_db
import sqlite3
# seguido de: get_todos_produtos, get_produto_por_id, criar_produto, atualizar_produto,
# deletar_produto, get_todos_usuarios, get_usuario_por_id, login_usuario, criar_usuario,
# criar_pedido, get_pedidos_usuario, get_todos_pedidos, relatorio_vendas,
# atualizar_status_pedido, buscar_produtos
```

**Impacto:** `models.py` (314 LOC) está acima do limiar de 300 LOC e cobre 4 domínios (catálogo, usuários/auth, pedidos, relatórios). `controllers.py` (292 LOC) está no limite e também cobre 4 domínios. Qualquer mudança em pedidos força editar os mesmos arquivos que catálogo e autenticação, aumentando conflitos e risco de regressão.

**Recomendação:** Dividir por domínio — `repositories/produto_repository.py`, `usuario_repository.py`, `pedido_repository.py` — e espelhar nos controllers, mantendo ~150-200 LOC por arquivo.

**Referência:** `references/anti-patterns.md` → QUAL-01

---

### [MEDIUM] PERF-01 — N+1 queries

**Onde:** `models.py:171-201` (`get_pedidos_usuario`), `models.py:203-233` (`get_todos_pedidos`), `models.py:139-166` (`criar_pedido`)

**Evidência:**
```python
# models.py:176-199
for row in rows:
    ...
    cursor2 = db.cursor()
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    itens = cursor2.fetchall()
    for item in itens:
        cursor3 = db.cursor()
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
        prod = cursor3.fetchone()

# models.py:154-160 — segunda passada sobre os itens após a validação
for item in itens:
    cursor.execute("SELECT preco FROM produtos WHERE id = " + str(item["produto_id"]))
    produto = cursor.fetchone()
```

**Impacto:** Para N pedidos com M itens, `get_todos_pedidos` executa 1 + N + (N×M) queries. `criar_pedido` consulta cada produto duas vezes (validação e inserção). O custo cresce de forma multiplicativa com o volume.

**Recomendação:** Carregar em lote com `IN`/JOIN:
```python
cursor.execute(
    """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    """
)
```
Em `criar_pedido`, reaproveitar os produtos já lidos na validação em vez de reconsultar.

**Referência:** `references/anti-patterns.md` → PERF-01

---

### [MEDIUM] QUAL-03 — Tratamento de erro genérico com vazamento de detalhes

**Onde:** `controllers.py:10-12`, `21-22`, `60-62`, `95-96`, `108-109`, `125-126`, `133-134`, `143-144`, `164-165`, `185-186`, `218-220`, `226-227`, `234-235`, `254-255`, `261-262`, `291-292`; `app.py:77-78`

**Evidência:**
```python
# controllers.py:10-12 e repetido em quase todos os handlers
except Exception as e:
    print("ERRO: " + str(e))
    return jsonify({"erro": str(e)}), 500

# controllers.py:291-292
except Exception as e:
    return jsonify({"status": "erro", "detalhes": str(e)}), 500

# app.py:77-78
except Exception as e:
    return jsonify({"erro": str(e)}), 500
```

**Impacto:** Todo erro interno é capturado como `Exception` e devolvido ao cliente com `str(e)`. Isso mistura 400 acionáveis com falhas reais de servidor (agora indistinguíveis) e vaza nomes de tabelas, colunas e caminhos internos — insumo direto para exploração (combina com SEC-01). Um `except Exception` em `/health` é aceitável; em `criar_pedido` e `login` esconde bugs reais.

**Recomendação:** Capturar exceções específicas e centralizar o tratamento:
```python
@app.errorhandler(Exception)
def handle_unexpected(e):
    logger.exception("erro inesperado")
    return jsonify({"erro": "Erro interno do servidor"}), 500
```
Devolver mensagem genérica ao cliente e o detalhe apenas no log.

**Referência:** `references/anti-patterns.md` → QUAL-03

---

### [MEDIUM] QUAL-04 — Estado global mutável e conexão não thread-safe

**Onde:** `database.py:4-10`

**Evidência:**
```python
# database.py:4-10
db_connection = None
db_path = "loja.db"

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
```

**Impacto:** Uma única conexão global é compartilhada entre todos os requests, sem lock nem escopo de request, com `check_same_thread=False` desativando a proteção do `sqlite3`. Transações concorrentes se intercalam sobre o mesmo cursor global: dois pedidos simultâneos podem validar estoque com o mesmo valor e gravar estoque negativo (`models.py:139-166`). Também torna os testes não isolados — o estado persiste entre casos.

**Recomendação:** Conexão por request (ou pool) com gestão de contexto e transação explícita:
```python
def get_db():
    return sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()
```
Alternativamente, migrar para SQLAlchemy com `scoped_session`.

**Referência:** `references/anti-patterns.md` → QUAL-04

---

### [MEDIUM] QUAL-02b — Transação não atômica em criação de pedido

**Onde:** `models.py:137-168`

**Evidência:**
```python
# models.py:139-146 — valida estoque em uma passada...
for item in itens:
    cursor.execute("SELECT * FROM produtos WHERE id = " + str(item["produto_id"]))
    produto = cursor.fetchone()
    ...
    if produto["estoque"] < item["quantidade"]:
        return {"erro": "Estoque insuficiente para " + produto["nome"]}
    total = total + (produto["preco"] * item["quantidade"])

# models.py:148-168 — ...e só depois insere e baixa estoque
cursor.execute("INSERT INTO pedidos ...")
pedido_id = cursor.lastrowid
for item in itens:
    ...
    cursor.execute("UPDATE produtos SET estoque = estoque - " + str(item["quantidade"]) + " WHERE id = " + str(item["produto_id"]))
db.commit()
```

**Impacto:** A checagem de estoque e o `UPDATE` estão separados por múltiplas operações e só há um `commit` no final, sem `BEGIN IMMEDIATE` nem verificação no update. Entre a validação e a baixa, outro request pode consumir o estoque (TOCTOU); com a conexão global compartilhada (QUAL-04), o risco é real. Pedido parcialmente aplicado não é revertido se algo falhar no meio do loop.

**Recomendação:** Fazer o débito condicional dentro da própria instrução e validar as linhas afetadas:
```python
cursor.execute(
    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
    (item["quantidade"], item["produto_id"], item["quantidade"]),
)
if cursor.rowcount == 0:
    db.rollback()
    raise EstoqueInsuficiente(item["produto_id"])
```
Envolver todo o caso de uso em uma transação única com rollback em erro.

**Referência:** `references/anti-patterns.md` → QUAL-04 / ARCH-03 (integridade transacional)

---

### [LOW] SEC-06 — Dados sensíveis e PII em log

**Onde:** `controllers.py:179`, `controllers.py:182`, `controllers.py:161`

**Evidência:**
```python
# controllers.py:179,182
print("Login bem-sucedido: " + email)
...
print("Login falhou: " + email)

# controllers.py:161
print("Usuário criado: " + email)
```

**Impacto:** E-mails de usuários (PII) são escritos em stdout em texto plano, junto com tentativas de login falhas — que também servem de sinal para ataques. `str(e)` em `controllers.py:11` pode ainda incluir a senha em mensagens de erro do banco.

**Recomendação:** Usar `logging` com nível apropriado e mascarar o identificador; nunca logar credenciais nem `str(e)` cru.

**Referência:** `references/anti-patterns.md` → SEC-06

---

### [LOW] QUAL-05 — Dependência e imports mortos

**Onde:** `database.py:2`, `models.py:2`, `app.py:7`

**Evidência:**
```python
# database.py:1-2 — 'os' importado e nunca usado
import sqlite3
import os

# models.py:1-2 — 'sqlite3' importado e nunca usado (usa via get_db)
from database import get_db
import sqlite3

# app.py:7 — SECRET_KEY definida e nunca usada (sem sessão/token)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```

**Impacto:** Imports sem uso poluem o módulo e mascaram dependências reais; `SECRET_KEY` sem uso sugere intenção de autenticação que não foi implementada (reforça SEC-04). Das dependências do manifesto, `flask` e `flask-cors` são usadas — não há dependência de manifesto morta.

**Recomendação:** Remover `import os` (`database.py:2`) e `import sqlite3` (`models.py:2`); ao implementar autenticação de verdade, usar a `SECRET_KEY` ou removê-la se não houver sessão.

**Referência:** `references/anti-patterns.md` → QUAL-05

---

### [LOW] QUAL-06 — Schema sem versionamento

**Onde:** `database.py:14-53`

**Evidência:**
```python
# database.py:14-53
cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        ...
    )
""")
# ... usuarios (linha 30: email TEXT, sem UNIQUE)
# ... pedidos (linha 39: usuario_id INTEGER, sem FOREIGN KEY)
# ... itens_pedido (linhas 48-50: pedido_id/produto_id sem FOREIGN KEY)
```

**Impacto:** O schema é criado em runtime por DDL inline, sem migrations nem histórico. Não há como evoluir colunas com segurança, reproduzir ambientes ou revisar mudanças. Além disso, não há `UNIQUE` em `usuarios.email` (aceita contas duplicadas) nem `CHECK` em `preco`/`estoque` (aceita valores negativos por fora da API), e nenhuma constraint de integridade referencial.

**Recomendação:** Introduzir Alembic (ou Flask-Migrate) e mover o DDL para migrations versionadas; adicionar `UNIQUE(email)`, `CHECK(preco >= 0)`, `CHECK(estoque >= 0)` e `FOREIGN KEY` com `PRAGMA foreign_keys = ON`.

**Referência:** `references/anti-patterns.md` → QUAL-06

---

### [LOW] QUAL-07 — Configuração hardcoded

**Onde:** `app.py:7-8`, `app.py:88`, `database.py:5`, `controllers.py:285-289`

**Evidência:**
```python
# app.py:7-8
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True

# app.py:88
app.run(host="0.0.0.0", port=5000, debug=True)

# database.py:5
db_path = "loja.db"

# controllers.py:285-289
"versao": "1.0.0",
"ambiente": "producao",
"db_path": "loja.db",
"debug": True,
```

**Impacto:** Segredo, flag de debug, host, porta e caminho do banco estão fixos no código, e o `/health` afirma `"ambiente": "producao"` enquanto `debug=True` está ligado — o Werkzeug debugger permitiria execução de código no host. Não há `.env` nem leitura de ambiente.

**Recomendação:** Centralizar em um `config.py` lendo o ambiente:
```python
DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
DATABASE_PATH = os.getenv("DATABASE_PATH", "loja.db")
SECRET_KEY = os.environ["SECRET_KEY"]
```
Garantir `debug=False` fora de desenvolvimento.

**Referência:** `references/anti-patterns.md` → QUAL-07

---

### [LOW] QUAL-08 — Sem testes automatizados

**Onde:** projeto inteiro (ausência estrutural)

**Evidência:**
```
$ find . -type d -name 'tests' -o -name '__tests__' -o -name 'spec'
(nenhum resultado)
$ cat requirements.txt
flask==3.1.1
flask-cors==5.0.1
```
Não há `tests/`, `conftest.py`, `pytest.ini` nem dependência de teste (`pytest`, `unittest` não declarados).

**Impacto:** Não existe rede de segurança para a refatoração. Fluxos críticos — cálculo de total do pedido, baixa de estoque, faixas de desconto do relatório, login — não têm cobertura, então qualquer mudança estrutural é feita às cegas.

**Recomendação:** Adicionar `pytest` e uma suíte mínima cobrindo: criação de pedido (estoque suficiente/insuficiente), cálculo de total, login válido/inválido, filtros de busca e contrato de status HTTP das rotas. Testes de regressão antes de mover código para services.

**Referência:** `references/anti-patterns.md` → QUAL-08

---

### 2.1 Critérios objetivos de fechamento (CRITICAL/HIGH)

Um achado só é considerado **RESOLVIDO** na Fase 4 quando todos os critérios
abaixo são comprovados por código e por execução (smoke/HTTP real). Qualquer
critério pendente rebaixa a classificação para pendente e bloqueia o gate.

| ID | Severidade | Critério de fechamento |
|---|---|---|
| **SEC-01** | CRITICAL | (a) nenhuma query interpola entrada de usuário — todos os valores usam `?`; (b) `POST /admin/query` removida (404); (c) payload de injeção (`' OR '1'='1`) não altera resultado de busca nem autentica no login. |
| **SEC-02** | CRITICAL | (a) nenhum segredo literal no código; `SECRET_KEY` obrigatória via ambiente; (b) `GET /health` não devolve `secret_key`, `db_path` nem `debug`; (c) grep de segredos sem ocorrências. |
| **SEC-03** | CRITICAL | (a) seed e cadastro persistem apenas hash com sal (`scrypt:`/`pbkdf2:`/`argon2`); (b) nenhuma senha do seed em texto puro no banco; (c) login usa exclusivamente `check_password_hash`; (d) registros legados em texto puro são re-hasheados no boot e continuam autenticando; (e) `GET /usuarios` e `GET /usuarios/<id>` não expõem `senha`; (f) não existe caminho de comparação `stored == senha_informada`. |
| **SEC-04** | HIGH | (a) rotas de escrita exigem token de sessão; (b) nível `admin`/`cliente` verificado no servidor, nunca no body; (c) `401` sem token, `403` com nível insuficiente ou posse indevida; (d) `/admin/reset-db` falha fechado sem `ADMIN_TOKEN`. |
| **ARCH-01** | HIGH | controllers apenas orquestram (request → validação → service → resposta), sem regra de negócio, cálculo ou efeito colateral. |
| **ARCH-02** | HIGH | nenhum SQL em `controllers/` ou `app.py`; acesso a dados concentrado em `repositories/` (e services administrativos dedicados). |
| **QUAL-02** | HIGH | validação de presença/tipo centralizada; body ausente ou campo com tipo inválido devolve `400` (nunca `500`). |

## 3. Mapa de calor por arquivo

| Arquivo | CRIT | HIGH | MED | LOW | Total |
|---|---|---|---|---|---|
| `models.py` | 2 | 0 | 3 | 1 | 6 |
| `app.py` | 1 | 3 | 0 | 2 | 6 |
| `controllers.py` | 2 | 3 | 2 | 2 | 9 |
| `database.py` | 1 | 0 | 1 | 2 | 4 |
| projeto (ausência estrutural) | 0 | 0 | 0 | 1 | 1 |

> Os achados são compartilhados entre arquivos quando o padrão se repete (ex.: SEC-01 ocorre em `models.py` e `app.py`); a tabela conta cada ocorrência no arquivo onde há evidência de linha.

## 4. Achados por categoria

### Segurança
- **SEC-01** (CRITICAL) — SQL Injection em 18 blocos de `models.py` e no endpoint `/admin/query`.
- **SEC-02** (CRITICAL) — segredo hardcoded em `app.py:7` e exposto em `controllers.py:289`.
- **SEC-03** (CRITICAL) — senhas em texto plano no seed, no login e nas respostas de API.
- **SEC-04** (HIGH) — rotas de escrita e administrativas sem autenticação/autorização.
- **SEC-06** (LOW) — PII (e-mails) e erros internos em `print`.

### Arquitetura
- **ARCH-01** (HIGH) — regras de negócio e notificações nos handlers HTTP.
- **ARCH-02** (HIGH) — SQL bruto em `controllers.py` e `app.py`, fora da camada de dados.
- **ARCH-03** (MEDIUM) — `models.py` com persistência + mapeamento + regra de negócio.

### Performance
- **PERF-01** (MEDIUM) — N+1 na listagem de pedidos e dupla consulta de produto em `criar_pedido`.

### Qualidade
- **QUAL-01** (MEDIUM) — `models.py` (314 LOC) e `controllers.py` (292 LOC) cobrindo 4 domínios cada.
- **QUAL-02 / QUAL-02b** (HIGH/MEDIUM) — validação ausente/frágil e transação não atômica com TOCTOU de estoque.
- **QUAL-03** (MEDIUM) — `except Exception` genérico em 17 locais, devolvendo `str(e)` ao cliente.
- **QUAL-04** (MEDIUM) — conexão SQLite global compartilhada com `check_same_thread=False`.
- **QUAL-05** (LOW) — imports e configuração mortos.
- **QUAL-06** (LOW) — DDL inline sem migrations e sem constraints de integridade.
- **QUAL-07** (LOW) — segredo, debug, host, porta e caminho do banco hardcoded.
- **QUAL-08** (LOW) — nenhuma cobertura de testes.

## 5. Recomendações prioritárias

Ordem sugerida de correção (do mais crítico ao menos crítico):

1. **[CRITICAL] SEC-01** — Parametrizar todas as queries em `models.py` e remover `POST /admin/query` (`app.py:59-78`).
2. **[CRITICAL] SEC-02** — Mover `SECRET_KEY` para env (`app.py:7`) e retirar `secret_key`/`db_path`/`debug` de `/health` (`controllers.py:285-289`).
3. **[CRITICAL] SEC-03** — Aplicar `generate_password_hash`/`check_password_hash` e remover `senha` das respostas (`models.py:79-131`).
4. **[HIGH] SEC-04** — Proteger `/admin/*` e os verbos de escrita com token/sessão emitido no login (`app.py:14-26,47-78`).
5. **[HIGH] ARCH-01 + ARCH-02** — Extrair services e repositórios; controllers apenas traduzem HTTP (`controllers.py:` handlers; `app.py:47-78`).
6. **[HIGH] QUAL-02** — Introduzir schemas de validação com retorno 400 (marshmallow/pydantic) e checagem de tipo.
7. **[MEDIUM] QUAL-04 + QUAL-02b** — Conexão por request e débito de estoque atômico com `rowcount`/transação.
8. **[MEDIUM] PERF-01** — Substituir N+1 por JOIN/`IN` nas listagens de pedidos.
9. **[MEDIUM] QUAL-03** — Centralizar tratamento de erro e devolver mensagem genérica.
10. **[MEDIUM] ARCH-03 + QUAL-01** — Dividir `models.py` e `controllers.py` por domínio.
11. **[LOW] QUAL-05, QUAL-06, QUAL-07, QUAL-08, SEC-06** — Limpeza de imports, migrations com constraints, config por env, suíte de testes e logging adequado.

## 6. Notas e limitações

- **Natureza estática da auditoria:** nenhum boot, teste de integração ou chamada HTTP foi executado. Os achados vêm de leitura de código com linha exata; comportamentos de runtime (ex.: resposta exata de `sqlite3` a cada injeção) não foram reproduzidos.
- **Versões:** `flask==3.1.1` e `flask-cors==5.0.1` conforme manifesto; não foram importadas para confirmar a versão instalada.
- **`QUAL-05` (dependência morta) parcialmente aplicável:** as duas dependências do manifesto **são usadas**; o achado foi mantido como LOW por causa dos imports mortos (`os`, `sqlite3`) e da `SECRET_KEY` sem uso — que não são dependências de manifesto.
- **`QUAL-02b`** foi classificado separadamente por ser um defeito de integridade transacional, não apenas de validação de entrada; se preferir aderência estrita ao catálogo, pode ser absorvido por **QUAL-04** (concorrência sobre estado compartilhado).
- **Falsos positivos descartados:** o `try/except` de `health_check` (`controllers.py:265-292`) é aceitável em contexto de health-check, mas foi agrupado em QUAL-03 apenas por devolver `str(e)`; `@app.route("/")` (`app.py:32-45`) e o CORS não foram tratados como achados.
- **Fora do escopo do catálogo:** ausência de paginação (`models.py:4-22`, `203-233`) e falta de filtro por `ativo` foram observadas na Fase 1 mas não têm ID correspondente no catálogo — não foram emitidas como achados.
- **Git:** `reports/analysis-code-smells-project.md` aparece como deletado no working tree; este relatório foi criado do zero e não sobrescreveu arquivo existente.
