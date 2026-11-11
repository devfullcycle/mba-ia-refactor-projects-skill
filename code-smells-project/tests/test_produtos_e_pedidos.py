from tests.conftest import ADMIN_TOKEN

PRODUTO = {"nome": "Livro Clean Code", "descricao": "Livro", "preco": 100.0, "estoque": 5, "categoria": "livros"}


def _estoque(client, produto_id):
    return client.get(f"/produtos/{produto_id}").get_json()["dados"]["estoque"]


def _criar_pedido(client, headers, produto_id, quantidade):
    resposta = client.post("/pedidos", headers=headers, json={"itens": [{"produto_id": produto_id, "quantidade": quantidade}]})
    assert resposta.status_code == 201, resposta.get_json()
    return resposta.get_json()["dados"]


def test_crud_produto_admin(client, admin):
    headers, _ = admin
    resposta = client.post("/produtos", headers=headers, json=PRODUTO)
    assert resposta.status_code == 201
    produto_id = resposta.get_json()["dados"]["id"]

    assert client.put(f"/produtos/{produto_id}", headers=headers, json={**PRODUTO, "preco": 90}).status_code == 200
    assert client.get(f"/produtos/{produto_id}").get_json()["dados"]["preco"] == 90

    assert client.post("/produtos", headers=headers, json={**PRODUTO, "preco": -1}).status_code == 400
    assert client.post("/produtos", headers=headers, json={**PRODUTO, "categoria": "x"}).status_code == 400

    assert client.delete(f"/produtos/{produto_id}", headers=headers).status_code == 200
    assert client.get(f"/produtos/{produto_id}").status_code == 404
    assert all(p["id"] != produto_id for p in client.get("/produtos").get_json()["dados"])


def test_pedido_usa_usuario_do_token(client, joao, maria):
    headers, usuario = joao
    _, outra = maria
    estoque_antes = _estoque(client, 2)

    dados = _criar_pedido(client, headers, 2, 2)
    assert dados["usuario_id"] == usuario["id"] and dados["total"] == 179.8
    assert _estoque(client, 2) == estoque_antes - 2

    pedidos = client.get(f"/pedidos/usuario/{usuario['id']}", headers=headers).get_json()["dados"]
    assert len(pedidos) == 1 and pedidos[0]["itens"][0]["produto_nome"] == "Mouse Wireless"

    em_nome_de_outro = {"usuario_id": outra["id"], "itens": [{"produto_id": 2, "quantidade": 1}]}
    assert client.post("/pedidos", headers=headers, json=em_nome_de_outro).status_code == 403


def test_pedido_validacoes(client, joao, admin):
    headers, _ = joao
    item = [{"produto_id": 1, "quantidade": 1}]
    assert client.post("/pedidos", headers=headers, json={"itens": []}).status_code == 400
    assert client.post("/pedidos", headers=headers, json={"itens": [{"produto_id": 999, "quantidade": 1}]}).status_code == 400
    assert client.post("/pedidos", headers=headers, json={"itens": [{"produto_id": 1, "quantidade": 999}]}).status_code == 400
    assert client.post("/pedidos", headers=headers, json={"usuario_id": "abc", "itens": item}).status_code == 400

    admin_headers, _ = admin
    assert client.post("/pedidos", headers=admin_headers, json={"usuario_id": 999, "itens": item}).status_code == 400


def test_ciclo_de_status_e_devolucao_de_estoque(client, joao, admin):
    headers, _ = joao
    admin_headers, _ = admin
    estoque_inicial = _estoque(client, 3)
    pedido_id = _criar_pedido(client, headers, 3, 3)["pedido_id"]
    assert _estoque(client, 3) == estoque_inicial - 3

    url = f"/pedidos/{pedido_id}/status"
    assert client.put(url, headers=admin_headers, json={"status": "xyz"}).status_code == 400
    assert client.put(url, headers=admin_headers, json={"status": "entregue"}).status_code == 409
    assert client.put(url, headers=admin_headers, json={"status": "aprovado"}).status_code == 200
    assert client.put(url, headers=admin_headers, json={"status": "cancelado"}).status_code == 200
    assert _estoque(client, 3) == estoque_inicial
    assert client.put(url, headers=admin_headers, json={"status": "aprovado"}).status_code == 409
    assert client.put("/pedidos/999/status", headers=admin_headers, json={"status": "aprovado"}).status_code == 404


def test_relatorio_ignora_cancelados(client, joao, admin):
    headers, _ = joao
    admin_headers, _ = admin
    _criar_pedido(client, headers, 10, 1)
    cancelado = _criar_pedido(client, headers, 10, 2)["pedido_id"]
    client.put(f"/pedidos/{cancelado}/status", headers=admin_headers, json={"status": "cancelado"})

    relatorio = client.get("/relatorios/vendas", headers=admin_headers).get_json()["dados"]
    assert relatorio["total_pedidos"] == 2
    assert relatorio["pedidos_cancelados"] == 1
    assert relatorio["faturamento_bruto"] == 59.9
    assert relatorio["ticket_medio"] == 59.9


def test_consulta_admin_bloqueia_hash_de_senha_e_escrita(client):
    headers = {"X-Admin-Token": ADMIN_TOKEN}
    ok = client.post("/admin/query", headers=headers, json={"sql": "SELECT id, email FROM usuarios"})
    assert ok.status_code == 200 and len(ok.get_json()["dados"]) == 3

    for sql in (
        "SELECT senha FROM usuarios",
        "SELECT * FROM usuarios",
        "DELETE FROM produtos",
        "SELECT 1; DELETE FROM produtos",
    ):
        assert client.post("/admin/query", headers=headers, json={"sql": sql}).status_code == 400, sql

    assert client.post("/admin/reset-db", headers=headers).status_code == 200
    assert client.get("/health").get_json()["counts"] == {"produtos": 0, "usuarios": 0, "pedidos": 0}
