from tests.conftest import SENHA_CLIENTE


def test_index_e_health_publicos(client):
    assert client.get("/").status_code == 200
    health = client.get("/health").get_json()
    assert health["status"] == "ok"
    assert health["counts"] == {"produtos": 10, "usuarios": 3, "pedidos": 0}
    assert "secret_key" not in health and "db_path" not in health


def test_catalogo_publico(client):
    corpo = client.get("/produtos").get_json()
    assert corpo["sucesso"] is True and len(corpo["dados"]) == 10
    assert client.get("/produtos/1").status_code == 200
    assert client.get("/produtos/999").status_code == 404


def test_busca_escapa_curingas(client):
    assert client.get("/produtos/busca?q=%25").get_json()["total"] == 0
    assert client.get("/produtos/busca?q=mouse").get_json()["total"] == 1
    assert client.get("/produtos/busca?preco_min=abc").status_code == 400


def test_login_emite_token_e_nao_expoe_senha(client):
    resposta = client.post("/login", json={"email": "JOAO@email.com", "senha": SENHA_CLIENTE})
    corpo = resposta.get_json()
    assert resposta.status_code == 200
    assert corpo["token"] and "senha" not in corpo["dados"]


def test_login_invalido(client):
    assert client.post("/login", json={"email": "joao@email.com", "senha": "errada"}).status_code == 401
    assert client.post("/login", json={}).status_code == 400


def test_rotas_protegidas_exigem_token(client):
    assert client.get("/usuarios").status_code == 401
    assert client.get("/pedidos").status_code == 401
    assert client.get("/relatorios/vendas").status_code == 401
    assert client.post("/produtos", json={}).status_code == 401
    assert client.post("/pedidos", json={}).status_code == 401
    assert client.get("/usuarios", headers={"Authorization": "Bearer adulterado"}).status_code == 401


def test_cliente_nao_acessa_rotas_admin(client, joao):
    headers, _ = joao
    assert client.get("/usuarios", headers=headers).status_code == 403
    assert client.get("/pedidos", headers=headers).status_code == 403
    assert client.get("/relatorios/vendas", headers=headers).status_code == 403
    assert client.delete("/produtos/1", headers=headers).status_code == 403
    assert client.put("/pedidos/1/status", headers=headers, json={"status": "aprovado"}).status_code == 403


def test_cliente_so_ve_os_proprios_dados(client, joao, maria):
    headers, usuario = joao
    _, outra = maria
    assert client.get(f"/usuarios/{usuario['id']}", headers=headers).status_code == 200
    assert client.get(f"/usuarios/{outra['id']}", headers=headers).status_code == 403
    assert client.get(f"/pedidos/usuario/{outra['id']}", headers=headers).status_code == 403


def test_cadastro_com_email_duplicado(client):
    novo = {"nome": "Ana", "email": "ana@email.com", "senha": "segredo"}
    assert client.post("/usuarios", json=novo).status_code == 201
    assert client.post("/usuarios", json={**novo, "email": "ANA@email.com"}).status_code == 409
    assert client.post("/usuarios", json={"nome": "x", "email": "sem-arroba", "senha": "y"}).status_code == 400


def test_admin_token_de_manutencao(client):
    assert client.post("/admin/reset-db").status_code == 401
    assert client.post("/admin/reset-db", headers={"X-Admin-Token": "errado"}).status_code == 401
