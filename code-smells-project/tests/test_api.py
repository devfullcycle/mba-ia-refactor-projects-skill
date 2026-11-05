"""Testes de fumaça/caracterização da API de E-commerce (code-smells-project).

Cobrem o contrato HTTP atual (rotas, status e campos principais) para detectar
regressões após refatorações. Os testes compartilham um servidor; cada um cria
os próprios dados e usa asserções que toleram dados criados por outros testes.
"""
import uuid


def _sufixo():
    return uuid.uuid4().hex[:8]


def _criar_produto(api, preco=10.0, estoque=5, categoria="geral"):
    r = api.post("/produtos", {
        "nome": "Produto" + _sufixo(), "descricao": "teste",
        "preco": preco, "estoque": estoque, "categoria": categoria,
    })
    assert r.status_code == 201, r.text
    return r.json()["dados"]["id"]


def _criar_usuario(api):
    r = api.post("/usuarios", {
        "nome": "Usuario" + _sufixo(), "email": f"u{_sufixo()}@teste.com", "senha": "segredo1",
    })
    assert r.status_code == 201, r.text
    return r.json()["dados"]["id"]


# ---------- raiz / health ----------

def test_raiz(api):
    r = api.get("/")
    assert r.status_code == 200
    corpo = r.json()
    assert "endpoints" in corpo
    assert corpo["endpoints"]["produtos"] == "/produtos"


def test_health(api):
    r = api.get("/health")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["status"] == "ok"
    assert corpo["database"] == "connected"
    assert corpo["counts"]["produtos"] >= 10
    assert corpo["counts"]["usuarios"] >= 3


# ---------- produtos ----------

def test_listar_produtos_seed(api):
    r = api.get("/produtos")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["sucesso"] is True
    assert len(corpo["dados"]) >= 10
    for chave in ("id", "nome", "preco", "estoque", "categoria"):
        assert chave in corpo["dados"][0]


def test_buscar_produto_por_id(api):
    r = api.get("/produtos/1")
    assert r.status_code == 200
    assert r.json()["dados"]["nome"] == "Notebook Gamer"


def test_buscar_produto_inexistente(api):
    r = api.get("/produtos/999999")
    assert r.status_code == 404
    assert r.json()["sucesso"] is False


def test_busca_produtos_por_termo(api):
    r = api.get("/produtos/busca", params={"q": "Mouse"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["total"] >= 1
    assert all("Mouse" in p["nome"] for p in corpo["dados"])


def test_busca_produtos_por_categoria_e_preco(api):
    r = api.get("/produtos/busca", params={"categoria": "moveis", "preco_max": "5000"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["total"] == len(corpo["dados"])
    assert all(p["categoria"] == "moveis" and p["preco"] <= 5000 for p in corpo["dados"])


def test_crud_produto(api):
    pid = _criar_produto(api, preco=25.5, estoque=3, categoria="livros")

    r = api.get(f"/produtos/{pid}")
    assert r.status_code == 200
    assert r.json()["dados"]["preco"] == 25.5

    r = api.put(f"/produtos/{pid}", {
        "nome": "Produto Atualizado", "descricao": "novo", "preco": 30, "estoque": 7,
        "categoria": "livros",
    })
    assert r.status_code == 200
    dados = api.get(f"/produtos/{pid}").json()["dados"]
    assert dados["nome"] == "Produto Atualizado"
    assert dados["estoque"] == 7

    assert api.delete(f"/produtos/{pid}").status_code == 200
    assert api.get(f"/produtos/{pid}").status_code == 404


def test_atualizar_e_deletar_produto_inexistente(api):
    corpo = {"nome": "Algum", "preco": 1, "estoque": 1}
    assert api.put("/produtos/999999", corpo).status_code == 404
    assert api.delete("/produtos/999999").status_code == 404


def test_criar_produto_validacoes(api):
    base = {"nome": "Valido", "preco": 10, "estoque": 1, "categoria": "geral"}
    casos = [
        ({k: v for k, v in base.items() if k != "nome"}, "nome ausente"),
        ({k: v for k, v in base.items() if k != "preco"}, "preço ausente"),
        ({k: v for k, v in base.items() if k != "estoque"}, "estoque ausente"),
        ({**base, "preco": -1}, "preço negativo"),
        ({**base, "estoque": -1}, "estoque negativo"),
        ({**base, "nome": "A"}, "nome curto"),
        ({**base, "categoria": "inexistente"}, "categoria inválida"),
    ]
    for payload, descricao in casos:
        r = api.post("/produtos", payload)
        assert r.status_code == 400, descricao
        assert "erro" in r.json(), descricao


# ---------- usuários / login ----------

def test_listar_usuarios_seed(api):
    r = api.get("/usuarios")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["sucesso"] is True
    emails = [u["email"] for u in corpo["dados"]]
    assert "admin@loja.com" in emails


def test_buscar_usuario(api):
    r = api.get("/usuarios/1")
    assert r.status_code == 200
    assert r.json()["dados"]["email"] == "admin@loja.com"
    assert api.get("/usuarios/999999").status_code == 404


def test_criar_usuario(api):
    uid = _criar_usuario(api)
    r = api.get(f"/usuarios/{uid}")
    assert r.status_code == 200
    assert r.json()["dados"]["id"] == uid


def test_criar_usuario_campos_obrigatorios(api):
    r = api.post("/usuarios", {"nome": "Sem Senha", "email": "x@x.com"})
    assert r.status_code == 400


def test_login_sucesso(api):
    r = api.post("/login", {"email": "admin@loja.com", "senha": "admin123"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["sucesso"] is True
    assert corpo["dados"]["email"] == "admin@loja.com"


def test_login_credenciais_invalidas(api):
    r = api.post("/login", {"email": "admin@loja.com", "senha": "errada"})
    assert r.status_code == 401
    assert r.json()["sucesso"] is False


def test_login_campos_obrigatorios(api):
    assert api.post("/login", {"email": "admin@loja.com"}).status_code == 400


# ---------- pedidos ----------

def test_criar_pedido_calcula_total_e_baixa_estoque(api):
    pid = _criar_produto(api, preco=10.0, estoque=5)
    uid = _criar_usuario(api)

    r = api.post("/pedidos", {"usuario_id": uid, "itens": [{"produto_id": pid, "quantidade": 2}]})
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["sucesso"] is True
    assert corpo["dados"]["total"] == 20.0
    pedido_id = corpo["dados"]["pedido_id"]

    assert api.get(f"/produtos/{pid}").json()["dados"]["estoque"] == 3

    pedidos_usuario = api.get(f"/pedidos/usuario/{uid}").json()["dados"]
    assert any(p["id"] == pedido_id for p in pedidos_usuario)

    todos = api.get("/pedidos").json()["dados"]
    assert any(p["id"] == pedido_id for p in todos)


def test_criar_pedido_estoque_insuficiente(api):
    pid = _criar_produto(api, estoque=1)
    uid = _criar_usuario(api)
    r = api.post("/pedidos", {"usuario_id": uid, "itens": [{"produto_id": pid, "quantidade": 5}]})
    assert r.status_code == 400
    assert r.json()["sucesso"] is False
    assert api.get(f"/produtos/{pid}").json()["dados"]["estoque"] == 1


def test_criar_pedido_produto_inexistente(api):
    uid = _criar_usuario(api)
    r = api.post("/pedidos", {"usuario_id": uid, "itens": [{"produto_id": 999999, "quantidade": 1}]})
    assert r.status_code == 400


def test_criar_pedido_validacoes(api):
    assert api.post("/pedidos", {"itens": [{"produto_id": 1, "quantidade": 1}]}).status_code == 400
    assert api.post("/pedidos", {"usuario_id": 1, "itens": []}).status_code == 400


def test_atualizar_status_pedido(api):
    pid = _criar_produto(api, estoque=5)
    uid = _criar_usuario(api)
    pedido_id = api.post("/pedidos", {
        "usuario_id": uid, "itens": [{"produto_id": pid, "quantidade": 1}],
    }).json()["dados"]["pedido_id"]

    assert api.put(f"/pedidos/{pedido_id}/status", {"status": "aprovado"}).status_code == 200
    pedidos = api.get(f"/pedidos/usuario/{uid}").json()["dados"]
    assert next(p for p in pedidos if p["id"] == pedido_id)["status"] == "aprovado"

    assert api.put(f"/pedidos/{pedido_id}/status", {"status": "invalido"}).status_code == 400


# ---------- relatório ----------

def test_relatorio_vendas(api):
    r = api.get("/relatorios/vendas")
    assert r.status_code == 200
    dados = r.json()["dados"]
    for chave in ("total_pedidos", "faturamento_bruto", "desconto_aplicavel",
                  "faturamento_liquido", "pedidos_pendentes", "pedidos_aprovados",
                  "pedidos_cancelados", "ticket_medio"):
        assert chave in dados
