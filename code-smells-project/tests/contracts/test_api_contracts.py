from __future__ import annotations

import os
import sqlite3

from tests.helpers import ApiTestCase


class PublicContractTests(ApiTestCase):
    def test_all_nineteen_routes_keep_identity_and_safe_success_shapes(self) -> None:
        root = self.client.get("/")
        self.assertEqual(200, root.status_code)
        self.assertEqual({"mensagem", "versao", "endpoints"}, set(root.get_json()))
        self.assertFalse(os.path.exists(self.database_path), "GET / não deve inicializar persistência")

        health = self.client.get("/health")
        self.assertEqual(200, health.status_code)
        self.assertEqual(
            {"status", "database", "counts", "versao", "ambiente"}, set(health.get_json())
        )
        self.assertNotIn("secret_key", health.get_json())
        self.assertNotIn("db_path", health.get_json())

        admin_headers = self.admin_headers()

        products = self.client.get("/produtos")
        self.assertEqual(200, products.status_code)
        self.assertEqual({"dados", "sucesso"}, set(products.get_json()))
        self.assertEqual(10, len(products.get_json()["dados"]))

        search = self.client.get(
            "/produtos/busca?q=Mouse&categoria=informatica&preco_min=1&preco_max=100"
        )
        self.assertEqual(200, search.status_code)
        self.assertEqual({"dados", "total", "sucesso"}, set(search.get_json()))

        product = self.client.get("/produtos/1")
        self.assertEqual(200, product.status_code)
        self.assertEqual({"dados", "sucesso"}, set(product.get_json()))

        created_product = self.client.post(
            "/produtos",
            headers=admin_headers,
            json={
                "nome": "Produto de Teste",
                "descricao": "temporário",
                "preco": 10.5,
                "estoque": 3,
                "categoria": "geral",
            },
        )
        self.assertEqual(201, created_product.status_code)
        product_id = created_product.get_json()["dados"]["id"]

        updated_product = self.client.put(
            f"/produtos/{product_id}",
            headers=admin_headers,
            json={
                "nome": "Produto Atualizado",
                "descricao": "temporário",
                "preco": 11.5,
                "estoque": 2,
                "categoria": "geral",
            },
        )
        self.assertEqual(200, updated_product.status_code)
        self.assertEqual({"mensagem", "sucesso"}, set(updated_product.get_json()))

        deleted_product = self.client.delete(f"/produtos/{product_id}", headers=admin_headers)
        self.assertEqual(200, deleted_product.status_code)

        user_id, user_headers = self.create_client()

        users = self.client.get("/usuarios", headers=admin_headers)
        self.assertEqual(200, users.status_code)
        self.assertTrue(all("senha" not in user for user in users.get_json()["dados"]))

        user = self.client.get(f"/usuarios/{user_id}", headers=user_headers)
        self.assertEqual(200, user.status_code)
        self.assertNotIn("senha", user.get_json()["dados"])

        login = self.client.post(
            "/login",
            json={"email": "client@example.test", "senha": "strong-client-password"},
        )
        self.assertEqual(200, login.status_code)
        self.assertEqual({"dados", "token", "sucesso", "mensagem"}, set(login.get_json()))

        order = self.client.post(
            "/pedidos",
            headers=user_headers,
            json={"usuario_id": user_id, "itens": [{"produto_id": 1, "quantidade": 1}]},
        )
        self.assertEqual(201, order.status_code)
        order_id = order.get_json()["dados"]["pedido_id"]

        all_orders = self.client.get("/pedidos", headers=admin_headers)
        self.assertEqual(200, all_orders.status_code)
        self.assertEqual({"dados", "sucesso"}, set(all_orders.get_json()))

        user_orders = self.client.get(f"/pedidos/usuario/{user_id}", headers=user_headers)
        self.assertEqual(200, user_orders.status_code)
        self.assertEqual(1, len(user_orders.get_json()["dados"]))

        updated_order = self.client.put(
            f"/pedidos/{order_id}/status",
            headers=admin_headers,
            json={"status": "aprovado"},
        )
        self.assertEqual(200, updated_order.status_code)

        report = self.client.get("/relatorios/vendas", headers=admin_headers)
        self.assertEqual(200, report.status_code)
        self.assertEqual({"dados", "sucesso"}, set(report.get_json()))

        arbitrary_query = self.client.post(
            "/admin/query", headers=admin_headers, json={"sql": "DROP TABLE produtos"}
        )
        self.assertEqual(410, arbitrary_query.status_code)
        self.assertEqual(10, len(self.client.get("/produtos").get_json()["dados"]))

        reset = self.client.post("/admin/reset-db", headers=admin_headers)
        self.assertEqual(200, reset.status_code)
        self.assertEqual({"mensagem", "sucesso"}, set(reset.get_json()))

    def test_authorization_matrix_returns_401_and_403(self) -> None:
        payload = {"nome": "Produto", "preco": 1, "estoque": 1, "categoria": "geral"}
        self.assertEqual(401, self.client.post("/produtos", json=payload).status_code)
        user_id, user_headers = self.create_client("limited@example.test")
        self.assertEqual(
            403,
            self.client.post("/produtos", headers=user_headers, json=payload).status_code,
        )
        self.assertEqual(403, self.client.get("/usuarios", headers=user_headers).status_code)
        self.assertEqual(
            403,
            self.client.post(
                "/pedidos",
                headers=user_headers,
                json={"usuario_id": user_id + 1, "itens": [{"produto_id": 1, "quantidade": 1}]},
            ).status_code,
        )

    def test_injection_payloads_are_data_and_password_never_leaks(self) -> None:
        admin_headers = self.admin_headers()
        malicious_name = "Produto'); DROP TABLE usuarios; --"
        created = self.client.post(
            "/produtos",
            headers=admin_headers,
            json={
                "nome": malicious_name,
                "descricao": "x' OR 1=1 --",
                "preco": 1,
                "estoque": 1,
                "categoria": "geral",
            },
        )
        self.assertEqual(201, created.status_code, created.get_json())
        self.assertEqual(
            401,
            self.client.post(
                "/login", json={"email": "' OR 1=1 --", "senha": "anything"}
            ).status_code,
        )
        user_id, _ = self.create_client("hash@example.test")
        with sqlite3.connect(self.database_path) as connection:
            stored = connection.execute("SELECT senha FROM usuarios WHERE id = ?", (user_id,)).fetchone()[0]
        self.assertNotEqual("strong-client-password", stored)
        self.assertTrue(stored.startswith("scrypt:"))

    def test_errors_are_consistent_and_sanitized(self) -> None:
        response = self.client.get("/produtos/busca?preco_min=not-a-number")
        self.assertEqual(400, response.status_code)
        self.assertEqual({"erro", "sucesso"}, set(response.get_json()))
        missing = self.client.get("/produtos/99999")
        self.assertEqual(404, missing.status_code)
        self.assertEqual({"erro", "sucesso"}, set(missing.get_json()))
