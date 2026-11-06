"""Testes das mudanças de contrato aprovadas (refactor-arch, Opção 2, Run id 20261105-175512).

Cada teste referencia o CT/finding do relatório reports/audit-project-1.md. O teste de
/admin/reset-db fica por último porque, no código original, a rota apaga o banco.
"""
import uuid

PRODUTO_INEXISTENTE = 999999
PEDIDO_INEXISTENTE = 999999


def _sufixo():
    return uuid.uuid4().hex[:8]


def _cliente_com_token(api_anonimo, token):
    return type(api_anonimo)(api_anonimo.base, token)


def _novo_cliente(api_anonimo):
    """Cadastra um cliente pela rota pública e devolve (id, cliente autenticado)."""
    email = f"c{_sufixo()}@teste.com"
    r = api_anonimo.post("/usuarios", {"nome": "Cliente" + _sufixo(), "email": email, "senha": "segredo1"})
    assert r.status_code == 201, r.text
    usuario_id = r.json()["dados"]["id"]
    login = api_anonimo.post("/login", {"email": email, "senha": "segredo1"})
    assert login.status_code == 200, login.text
    return usuario_id, _cliente_com_token(api_anonimo, login.json()["dados"].get("token"))


def _novo_produto(api):
    r = api.post("/produtos", {"nome": "Produto" + _sufixo(), "preco": 10.0, "estoque": 5, "categoria": "geral"})
    assert r.status_code == 201, r.text
    return r.json()["dados"]["id"]


# ---------- CT-01 (F-005, F-004): POST /admin/query removida ----------

def test_ct01_admin_query_removida(api, api_anonimo):
    assert api_anonimo.post("/admin/query", {"sql": "SELECT 1"}).status_code == 404
    assert api.post("/admin/query", {"sql": "SELECT 1"}).status_code == 404


# ---------- CT-03 (F-004): relatório financeiro só para admin ----------

def test_ct03_relatorio_exige_admin(api, api_anonimo):
    assert api_anonimo.get("/relatorios/vendas").status_code == 401
    assert _cliente_com_token(api_anonimo, "invalido").get("/relatorios/vendas").status_code == 401
    _, cliente = _novo_cliente(api_anonimo)
    assert cliente.get("/relatorios/vendas").status_code == 403
    assert api.get("/relatorios/vendas").status_code == 200


# ---------- CT-04 (F-003): autenticação por token ----------

def test_ct04_login_emite_token(api_anonimo):
    r = api_anonimo.post("/login", {"email": "admin@loja.com", "senha": "admin123"})
    assert r.status_code == 200
    token = r.json()["dados"].get("token")
    assert isinstance(token, str) and token


def test_ct04_rotas_de_dados_exigem_token(api_anonimo):
    chamadas = [
        ("GET", "/usuarios", None),
        ("GET", "/usuarios/1", None),
        ("POST", "/produtos", {"nome": "Sem Token", "preco": 1, "estoque": 1}),
        ("PUT", f"/produtos/{PRODUTO_INEXISTENTE}", {"nome": "Sem Token", "preco": 1, "estoque": 1}),
        ("DELETE", f"/produtos/{PRODUTO_INEXISTENTE}", None),
        ("POST", "/pedidos", {"usuario_id": 1, "itens": [{"produto_id": 1, "quantidade": 1}]}),
        ("GET", "/pedidos", None),
        ("GET", "/pedidos/usuario/1", None),
        ("PUT", f"/pedidos/{PEDIDO_INEXISTENTE}/status", {"status": "aprovado"}),
    ]
    for metodo, caminho, corpo in chamadas:
        r = api_anonimo._req(metodo, caminho, json=corpo)
        assert r.status_code == 401, f"{metodo} {caminho}"
        assert r.json()["sucesso"] is False, f"{metodo} {caminho}"


def test_ct04_cliente_sem_perfil_admin(api_anonimo):
    _, cliente = _novo_cliente(api_anonimo)
    assert cliente.post("/produtos", {"nome": "Cliente", "preco": 1, "estoque": 1}).status_code == 403
    assert cliente.get("/usuarios").status_code == 403
    assert cliente.get("/pedidos").status_code == 403
    assert cliente.put(f"/pedidos/{PEDIDO_INEXISTENTE}/status", {"status": "aprovado"}).status_code == 403


def test_ct04_cliente_acessa_apenas_os_proprios_dados(api, api_anonimo):
    usuario_id, cliente = _novo_cliente(api_anonimo)
    outro_id, _ = _novo_cliente(api_anonimo)
    produto_id = _novo_produto(api)

    assert cliente.get(f"/usuarios/{outro_id}").status_code == 403
    assert cliente.get(f"/pedidos/usuario/{outro_id}").status_code == 403
    item = [{"produto_id": produto_id, "quantidade": 1}]
    assert cliente.post("/pedidos", {"usuario_id": outro_id, "itens": item}).status_code == 403

    assert cliente.get(f"/usuarios/{usuario_id}").status_code == 200
    r = cliente.post("/pedidos", {"usuario_id": usuario_id, "itens": item})
    assert r.status_code == 201
    pedido_id = r.json()["dados"]["pedido_id"]
    pedidos = cliente.get(f"/pedidos/usuario/{usuario_id}").json()["dados"]
    assert any(p["id"] == pedido_id for p in pedidos)


def test_ct04_rotas_publicas_continuam_abertas(api_anonimo):
    # Guarda de regressão do limite do CT-04: estas rotas seguem sem credencial.
    for caminho in ("/", "/health", "/produtos", "/produtos/busca?q=Mouse", "/produtos/1"):
        assert api_anonimo.get(caminho).status_code == 200, caminho


# ---------- CT-05 / CT-06 (F-006): campos sensíveis omitidos ----------

def test_ct05_usuarios_sem_senha(api):
    usuarios = api.get("/usuarios").json()["dados"]
    assert usuarios
    assert all("senha" not in u for u in usuarios)
    assert "senha" not in api.get("/usuarios/1").json()["dados"]


def test_ct06_health_sem_configuracao_interna(api_anonimo):
    corpo = api_anonimo.get("/health").json()
    for campo in ("secret_key", "db_path", "debug"):
        assert campo not in corpo, campo


# ---------- CT-08 (F-003, F-016): CORS restrito ----------

def test_ct08_cors_nao_libera_origem_desconhecida(api_anonimo):
    r = api_anonimo.get("/produtos", headers={"Origin": "http://origem-nao-permitida.example"})
    assert r.status_code == 200
    assert "Access-Control-Allow-Origin" not in r.headers


# ---------- CT-09 (F-010): status de pedido inexistente ----------

def test_ct09_status_de_pedido_inexistente_404(api):
    r = api.put(f"/pedidos/{PEDIDO_INEXISTENTE}/status", {"status": "aprovado"})
    assert r.status_code == 404
    assert r.json()["sucesso"] is False


# ---------- CT-02 (F-004): reset exige admin e flag de ambiente (manter por último) ----------

def test_ct02_reset_db_exige_admin(api, api_anonimo):
    _, cliente = _novo_cliente(api_anonimo)
    assert api_anonimo.post("/admin/reset-db").status_code == 401
    assert _cliente_com_token(api_anonimo, "invalido").post("/admin/reset-db").status_code == 401
    assert cliente.post("/admin/reset-db").status_code == 403
    # Mesmo como admin, sem ALLOW_DESTRUCTIVE=true a operação é recusada (o banco é preservado).
    assert api.post("/admin/reset-db").status_code == 403
    assert api.get("/health").json()["counts"]["produtos"] >= 10
