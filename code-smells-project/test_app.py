# -*- coding: utf-8 -*-
"""Testes de validacao - code-smells-project (Python/Flask E-commerce)"""
import os
import sys
os.environ.setdefault("SECRET_KEY", "test-secret")
sys.stdout.reconfigure(encoding="utf-8")

from app import create_app

app = create_app()


def run_tests():
    # O seed e aplicado automaticamente pelo get_db() em database/connection.py
    client = app.test_client()
    passed = 0
    failed = 0

    def check(label, response, expected_status, **assertions):
        nonlocal passed, failed
        ok = response.status_code == expected_status
        data = response.get_json() or {}
        for key, expected in assertions.items():
            actual = data.get(key)
            if callable(expected):
                ok = ok and expected(actual)
            else:
                ok = ok and (actual == expected)
        mark = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
            print(f"  [{mark}] {label}  (got {response.status_code}, data={data})")
            return
        print(f"  [{mark}] {label}")

    print("\n=== Projeto 1 - code-smells-project ===\n")

    print("--- Raiz e Health ---")
    check("GET /", client.get("/"), 200, versao="2.0.0")
    r = client.get("/health")
    check("GET /health - status ok", r, 200, status="ok")
    d2 = r.get_json() or {}
    if "secret_key" not in d2:
        passed += 1
        print("  [PASS] GET /health - secret_key NAO exposta")
    else:
        failed += 1
        print("  [FAIL] GET /health - secret_key EXPOSTA (bug de seguranca)")

    print("\n--- Produtos ---")
    check("GET /produtos - lista produtos (minimo 10)",
          client.get("/produtos"), 200,
          dados=lambda v: isinstance(v, list) and len(v) >= 10)
    check("GET /produtos/busca?q=Notebook - encontra 1",
          client.get("/produtos/busca?q=Notebook"), 200, total=1)
    check("GET /produtos/1 - produto existe",
          client.get("/produtos/1"), 200, sucesso=True)
    check("GET /produtos/9999 - 404",
          client.get("/produtos/9999"), 404)
    check("POST /produtos - cria produto",
          client.post("/produtos", json={
              "nome": "Produto Teste", "preco": 99.9,
              "estoque": 5, "categoria": "geral"
          }), 201, sucesso=True)
    check("POST /produtos - categoria invalida -> 400",
          client.post("/produtos", json={
              "nome": "X", "preco": 1, "estoque": 1, "categoria": "invalida"
          }), 400)

    print("\n--- Usuarios ---")
    check("GET /usuarios - lista usuarios",
          client.get("/usuarios"), 200, sucesso=True)
    check("GET /usuarios/1 - usuario existe",
          client.get("/usuarios/1"), 200, sucesso=True)

    print("\n--- Login ---")
    check("POST /login - senha correta -> 200",
          client.post("/login", json={
              "email": "admin@loja.com", "senha": "admin123"
          }), 200, sucesso=True)
    check("POST /login - senha errada -> 401",
          client.post("/login", json={
              "email": "admin@loja.com", "senha": "errada"
          }), 401, sucesso=False)
    check("POST /login - campos ausentes -> 400",
          client.post("/login", json={}), 400)

    print("\n--- Pedidos ---")
    r_pedido = client.post("/pedidos", json={
        "usuario_id": 2,
        "itens": [{"produto_id": 1, "quantidade": 1}]
    })
    check("POST /pedidos - cria pedido",  r_pedido, 201, sucesso=True)
    check("GET /pedidos - lista pedidos", client.get("/pedidos"), 200, sucesso=True)
    check("GET /pedidos/usuario/2",       client.get("/pedidos/usuario/2"), 200, sucesso=True)
    check("PUT /pedidos/1/status - aprovado",
          client.put("/pedidos/1/status", json={"status": "aprovado"}), 200, sucesso=True)
    check("PUT /pedidos/1/status - status invalido -> 400",
          client.put("/pedidos/1/status", json={"status": "invalido"}), 400)

    print("\n--- Relatorio ---")
    check("GET /relatorios/vendas",
          client.get("/relatorios/vendas"), 200, sucesso=True)

    print(f"\n{'='*40}")
    print(f"Resultado: {passed} PASS / {failed} FAIL")
    print(f"{'='*40}\n")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
