"""Smoke test de contrato — pós-refatoração (Fase 3/4).

Exercita o comportamento observável das rotas inventariadas na Fase 1
(`reports/analysis-code-smells-project.md`) contra o código refatorado.

Diferenças deliberadas já documentadas em `reports/refactor-code-smells-project.md`:
  * `POST /admin/query` foi REMOVIDA (executava SQL arbitrário) → espera 404.
  * `POST /admin/reset-db` agora exige `Authorization: Bearer <ADMIN_TOKEN>`
    (401 sem token, 403 se `ADMIN_TOKEN` não configurado).
  * `POST /login` emite `token` de sessão assinado; as rotas de escrita exigem
    `Authorization: Bearer <token>`.
  * Produtos (`POST`/`PUT`/`DELETE`) exigem nível `admin`; pedidos exigem nível
    `cliente` no cadastro e `admin` na mudança de status (401 sem token, 403
    com nível insuficiente). Cliente só cria pedido para si mesmo.
  * `GET /health` não devolve mais `secret_key`, `db_path`, `debug`.
  * `GET /usuarios` não devolve mais o campo `senha`.
  * Senhas passam a ser hash com salt (login continua aceitando o seed legado).
  * `POST /produtos/busca` com injeção NÃO vaza mais a tabela (parametrizado).
  * Payload malformado → 400 (antes podia virar 500).

Uso:
    python tests/smoke_contract.py
"""

import os
import sys
import tempfile
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("SECRET_KEY", "smoke-test-secret")
os.environ.setdefault("DATABASE_PATH", str(Path(tempfile.mkdtemp(prefix="smoke-new-")) / "loja.db"))
os.environ.setdefault("ADMIN_TOKEN", "smoke-admin-token")

import app as app_module  # noqa: E402

results = []


def check(name, condition, detail=""):
    results.append((name, bool(condition), detail))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def login_token(client, email, senha):
    resposta = client.post("/login", json={"email": email, "senha": senha})
    return resposta.get_json().get("token")


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def main():
    app_module.app.config["TESTING"] = True
    client = app_module.app.test_client()

    try:
        run_checks(client)
    except Exception:
        traceback.print_exc()
        return 2

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n{passed}/{total} checks passaram")
    return 0 if passed == total else 1


def run_checks(client):
    # --- health: contadores preservados, segredos removidos -----------------
    r = client.get("/health")
    body = r.get_json()
    check("GET /health → 200", r.status_code == 200, f"status={r.status_code}")
    check(
        "GET /health conta produtos/usuarios/pedidos",
        body.get("counts") == {"produtos": 10, "usuarios": 3, "pedidos": 0},
        f"counts={body.get('counts')}",
    )
    check(
        "GET /health NÃO vaza secret_key/db_path/debug (SEC-02)",
        not ({"secret_key", "db_path", "debug"} & set(body)),
        f"campos={sorted(body)}",
    )

    # --- index --------------------------------------------------------------
    r = client.get("/")
    check("GET / → 200", r.status_code == 200, f"status={r.status_code}")
    check(
        "GET / lista os 6 recursos",
        set(r.get_json().get("endpoints", {})) == {"produtos", "usuarios", "pedidos", "login", "relatorios", "health"},
        f"endpoints={sorted(r.get_json().get('endpoints', {}))}",
    )

    # --- produtos: leitura --------------------------------------------------
    r = client.get("/produtos")
    body = r.get_json()
    check("GET /produtos → 200 com 10 itens", r.status_code == 200 and len(body["dados"]) == 10, f"status={r.status_code} n={len(body.get('dados', []))}")
    first = body["dados"][0]
    check(
        "GET /produtos item[0] = produto 1 (Notebook Gamer, 5999.99)",
        first["nome"] == "Notebook Gamer" and first["preco"] == 5999.99,
        f"nome={first['nome']} preco={first['preco']}",
    )

    r = client.get("/produtos/1")
    check("GET /produtos/1 → 200", r.status_code == 200 and r.get_json()["dados"]["nome"] == "Notebook Gamer", f"status={r.status_code}")
    r = client.get("/produtos/9999")
    check("GET /produtos/9999 → 404", r.status_code == 404, f"status={r.status_code}")

    # --- produtos: busca ----------------------------------------------------
    r = client.get("/produtos/busca?q=Mouse")
    check("GET /produtos/busca?q=Mouse → 1 item", r.status_code == 200 and r.get_json()["total"] == 1, f"status={r.status_code} total={r.get_json().get('total')}")
    r = client.get("/produtos/busca?categoria=vestuario")
    check("GET /produtos/busca?categoria=vestuario → 1 item", r.status_code == 200 and r.get_json()["total"] == 1, f"status={r.status_code}")
    r = client.get("/produtos/busca?preco_min=1000&preco_max=2000")
    check("GET /produtos/busca faixa de preço → 2 itens", r.status_code == 200 and r.get_json()["total"] == 2, f"status={r.status_code} total={r.get_json().get('total')}")

    # --- SQL injection neutralizada (SEC-01) --------------------------------
    r = client.get("/produtos/busca?q=' OR '1'='1")
    check(
        "GET /produtos/busca com ' OR '1'='1 NÃO vaza a tabela (SEC-01 corrigido)",
        r.status_code == 200 and r.get_json()["total"] == 0,
        f"status={r.status_code} total={r.get_json().get('total')}",
    )

    # --- produtos: escrita (admin) ------------------------------------------
    admin_token = login_token(client, "admin@loja.com", "admin123")
    cliente_token = login_token(client, "joao@email.com", "123456")
    admin_headers = auth_header(admin_token)
    cliente_headers = auth_header(cliente_token)
    check("Login admin emite token", isinstance(admin_token, str) and bool(admin_token), f"token_presente={bool(admin_token)}")
    check("Login cliente emite token", isinstance(cliente_token, str) and bool(cliente_token), f"token_presente={bool(cliente_token)}")

    payload_produto = {"nome": "Cabo HDMI", "preco": 29.9, "estoque": 7, "categoria": "informatica"}
    r = client.post("/produtos", json=payload_produto)
    check("POST /produtos sem token → 401 (SEC-04)", r.status_code == 401, f"status={r.status_code}")
    r = client.post("/produtos", json=payload_produto, headers=cliente_headers)
    check("POST /produtos com token de cliente → 403 (SEC-04)", r.status_code == 403, f"status={r.status_code}")

    r = client.post("/produtos", json=payload_produto, headers=admin_headers)
    body = r.get_json()
    novo_id = body.get("dados", {}).get("id")
    check("POST /produtos válido com admin → 201 com id", r.status_code == 201 and isinstance(novo_id, int), f"status={r.status_code} body={body}")

    for nome, payload, esperado in (
        ("POST /produtos sem preço/estoque", {"nome": "X"}, 400),
        ("POST /produtos preço negativo", {"nome": "X", "preco": -1, "estoque": 1}, 400),
        ("POST /produtos categoria inválida", {"nome": "X", "preco": 1, "estoque": 1, "categoria": "inexistente"}, 400),
        ("POST /produtos preco textual", {"nome": "X", "preco": "abc", "estoque": 1}, 400),
        ("POST /produtos sem body JSON", None, 400),
    ):
        if payload is not None:
            r = client.post("/produtos", json=payload, headers=admin_headers)
        else:
            r = client.post("/produtos", data="nao-json", content_type="text/plain", headers=admin_headers)
        check(f"{nome} → {esperado}", r.status_code == esperado, f"status={r.status_code} body={r.get_json()}")

    r = client.put("/produtos/9999", json={"nome": "n", "preco": 1, "estoque": 1})
    check("PUT /produtos/<id> sem token → 401 (SEC-04)", r.status_code == 401, f"status={r.status_code}")
    r = client.put(f"/produtos/{novo_id}", json={"nome": "Cabo HDMI 2.1", "preco": 39.9, "estoque": 5, "categoria": "informatica"}, headers=admin_headers)
    check("PUT /produtos/<id> válido com admin → 200", r.status_code == 200, f"status={r.status_code}")
    r = client.get(f"/produtos/{novo_id}")
    check("PUT refletido na leitura", r.get_json()["dados"]["nome"] == "Cabo HDMI 2.1", f"nome={r.get_json()['dados']['nome']}")
    r = client.put("/produtos/9999", json={"nome": "n", "preco": 1, "estoque": 1}, headers=admin_headers)
    check("PUT /produtos/9999 → 404", r.status_code == 404, f"status={r.status_code}")
    r = client.delete(f"/produtos/{novo_id}")
    check("DELETE /produtos/<id> sem token → 401 (SEC-04)", r.status_code == 401, f"status={r.status_code}")

    # --- usuarios -----------------------------------------------------------
    r = client.get("/usuarios")
    usuarios = r.get_json()["dados"]
    check("GET /usuarios → 200 com 3 usuários", r.status_code == 200 and len(usuarios) == 3, f"status={r.status_code} n={len(usuarios)}")
    check(
        "GET /usuarios NÃO expõe senha (SEC-03)",
        all("senha" not in u for u in usuarios),
        f"campos={sorted(usuarios[0])}",
    )

    r = client.get("/usuarios/1")
    check("GET /usuarios/1 → 200 (admin)", r.status_code == 200 and r.get_json()["dados"]["email"] == "admin@loja.com", f"status={r.status_code}")
    r = client.get("/usuarios/9999")
    check("GET /usuarios/9999 → 404", r.status_code == 404, f"status={r.status_code}")

    r = client.post("/usuarios", json={"nome": "Novo Cliente", "email": "novo@email.com", "senha": "segredo123"})
    check("POST /usuarios válido → 201", r.status_code == 201 and isinstance(r.get_json()["dados"]["id"], int), f"status={r.status_code}")
    r = client.post("/usuarios", json={"nome": "Sem Email"})
    check("POST /usuarios sem email/senha → 400", r.status_code == 400, f"status={r.status_code}")

    # senha armazenada como hash
    import database as db_pkg
    from flask import g
    with app_module.app.app_context():
        conn = db_pkg.get_db()
        row = conn.execute("SELECT senha FROM usuarios WHERE email = ?", ("novo@email.com",)).fetchone()
        check(
            "Senha persistida como hash com salt (SEC-03)",
            row is not None and row["senha"] != "segredo123" and ":" in row["senha"],
            f"prefixo={row['senha'][:14] if row else None}",
        )

    # --- login --------------------------------------------------------------
    r = client.post("/login", json={"email": "admin@loja.com", "senha": "admin123"})
    body = r.get_json()
    check("POST /login válido (seed legado) → 200", r.status_code == 200 and body.get("sucesso") is True, f"status={r.status_code} body={body}")
    check(
        "POST /login devolve token de sessão e NÃO devolve campo senha",
        isinstance(body.get("token"), str) and bool(body["token"]) and "senha" not in body.get("dados", {}),
        f"token_presente={bool(body.get('token'))} dados={body.get('dados')}",
    )
    r = client.post("/login", json={"email": "novo@email.com", "senha": "segredo123"})
    check("POST /login usuário novo (hash) → 200", r.status_code == 200, f"status={r.status_code}")

    r = client.post("/login", json={"email": "admin@loja.com", "senha": "errada"})
    check("POST /login senha errada → 401", r.status_code == 401, f"status={r.status_code}")
    r = client.post("/login", json={"email": "admin@loja.com"})
    check("POST /login sem senha → 400", r.status_code == 400, f"status={r.status_code}")
    r = client.post("/login", json={"email": "' OR '1'='1", "senha": "' OR '1'='1"})
    check("POST /login com injeção → 401 (SEC-01 corrigido)", r.status_code == 401, f"status={r.status_code}")

    # --- pedidos (cliente) --------------------------------------------------
    payload_pedido = {"usuario_id": 2, "itens": [{"produto_id": 2, "quantidade": 2}, {"produto_id": 3, "quantidade": 1}]}
    r = client.post("/pedidos", json=payload_pedido)
    check("POST /pedidos sem token → 401 (SEC-04)", r.status_code == 401, f"status={r.status_code}")
    r = client.post("/pedidos", json=payload_pedido, headers=admin_headers)
    check("POST /pedidos com token de admin → 403 (SEC-04)", r.status_code == 403, f"status={r.status_code}")
    r = client.post(
        "/pedidos",
        json={"usuario_id": 3, "itens": [{"produto_id": 2, "quantidade": 1}]},
        headers=cliente_headers,
    )
    check("POST /pedidos para outro usuário → 403 (SEC-04)", r.status_code == 403, f"status={r.status_code}")

    r = client.post("/pedidos", json=payload_pedido, headers=cliente_headers)
    body = r.get_json()
    pedido_id = body.get("dados", {}).get("pedido_id")
    total = body.get("dados", {}).get("total")
    esperado = round(89.90 * 2 + 299.90, 2)
    check("POST /pedidos válido com cliente → 201", r.status_code == 201 and isinstance(pedido_id, int), f"status={r.status_code} body={body}")
    check(f"POST /pedidos calcula total={esperado}", total == esperado, f"total={total}")

    r = client.get("/produtos/2")
    check("POST /pedidos baixa estoque do produto 2 (50 → 48)", r.get_json()["dados"]["estoque"] == 48, f"estoque={r.get_json()['dados']['estoque']}")

    r = client.post("/pedidos", json={"usuario_id": 2, "itens": [{"produto_id": 2, "quantidade": 99999}]}, headers=cliente_headers)
    check("POST /pedidos estoque insuficiente → 400", r.status_code == 400, f"status={r.status_code} body={r.get_json()}")
    r = client.get("/produtos/2")
    check("Estoque NÃO foi debitado no pedido rejeitado (rollback)", r.get_json()["dados"]["estoque"] == 48, f"estoque={r.get_json()['dados']['estoque']}")

    r = client.post("/pedidos", json={"usuario_id": 2, "itens": [{"produto_id": 9999, "quantidade": 1}]}, headers=cliente_headers)
    check("POST /pedidos produto inexistente → 400", r.status_code == 400, f"status={r.status_code}")
    r = client.post("/pedidos", json={"usuario_id": 2, "itens": []}, headers=cliente_headers)
    check("POST /pedidos sem itens → 400", r.status_code == 400, f"status={r.status_code}")
    r = client.post("/pedidos", json={"usuario_id": 9999, "itens": [{"produto_id": 1, "quantidade": 1}]}, headers=cliente_headers)
    check(
        "POST /pedidos para usuário inexistente → 403 (não permite enumerar usuários)",
        r.status_code == 403,
        f"status={r.status_code} body={r.get_json()}",
    )

    r = client.get("/pedidos/usuario/2")
    body = r.get_json()
    check("GET /pedidos/usuario/2 → 200 com 1 pedido", r.status_code == 200 and len(body["dados"]) == 1, f"status={r.status_code} n={len(body.get('dados', []))}")
    pedido = body["dados"][0]
    check(
        "GET /pedidos/usuario/2 traz itens com produto_nome",
        len(pedido["itens"]) == 2 and pedido["itens"][0]["produto_nome"] == "Mouse Wireless",
        f"itens={pedido['itens']}",
    )

    r = client.get("/pedidos")
    check("GET /pedidos → 200 com 1 pedido", r.status_code == 200 and len(r.get_json()["dados"]) == 1, f"status={r.status_code}")

    r = client.put(f"/pedidos/{pedido_id}/status", json={"status": "aprovado"})
    check("PUT /pedidos/<id>/status sem token → 401 (SEC-04)", r.status_code == 401, f"status={r.status_code}")
    r = client.put(f"/pedidos/{pedido_id}/status", json={"status": "aprovado"}, headers=admin_headers)
    check("PUT /pedidos/<id>/status com admin → 200", r.status_code == 200, f"status={r.status_code}")
    r = client.put(f"/pedidos/{pedido_id}/status", json={"status": "invalido"}, headers=admin_headers)
    check("PUT /pedidos/<id>/status inválido → 400", r.status_code == 400, f"status={r.status_code}")
    r = client.put("/pedidos/9999/status", json={"status": "aprovado"}, headers=admin_headers)
    check("PUT /pedidos/9999/status → 404", r.status_code == 404, f"status={r.status_code}")

    # --- relatorio ----------------------------------------------------------
    r = client.get("/relatorios/vendas")
    body = r.get_json()["dados"]
    check("GET /relatorios/vendas → 200", r.status_code == 200, f"status={r.status_code}")
    check(
        "GET /relatorios/vendas agrega faturamento e status",
        body["total_pedidos"] == 1 and body["faturamento_bruto"] == esperado and body["pedidos_aprovados"] == 1,
        f"body={body}",
    )
    check(
        "GET /relatorios/vendas faturamento abaixo de 1000 → desconto 0",
        body["desconto_aplicavel"] == 0 and body["faturamento_liquido"] == esperado,
        f"desconto={body['desconto_aplicavel']} liquido={body['faturamento_liquido']}",
    )

    # --- admin --------------------------------------------------------------
    r = client.post("/admin/query", json={"sql": "SELECT 1"})
    check("POST /admin/query REMOVIDA → 404", r.status_code == 404, f"status={r.status_code}")

    r = client.post("/admin/reset-db")
    check("POST /admin/reset-db sem token → 401 (SEC-04)", r.status_code == 401, f"status={r.status_code} body={r.get_json()}")
    r = client.post("/admin/reset-db", headers={"Authorization": "Bearer errado"})
    check("POST /admin/reset-db token inválido → 401", r.status_code == 401, f"status={r.status_code}")
    r = client.post("/admin/reset-db", headers={"Authorization": "Bearer smoke-admin-token"})
    check("POST /admin/reset-db com token → 200", r.status_code == 200, f"status={r.status_code} body={r.get_json()}")

    r = client.get("/produtos")
    check("Após reset-db a base fica vazia e o schema segue válido", r.status_code == 200 and r.get_json()["dados"] == [], f"status={r.status_code} n={len(r.get_json()['dados'])}")

    # --- 404 de rota desconhecida -------------------------------------------
    r = client.get("/nao-existe")
    check("GET /nao-existe → 404 JSON", r.status_code == 404, f"status={r.status_code}")


if __name__ == "__main__":
    sys.exit(main())
