import os
import tempfile
import unittest

from app import create_app


class AppTests(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(dir=os.getcwd(), suffix=".db")
        os.close(self.db_fd)
        self.addCleanup(self._cleanup_db)
        self.app = create_app(
            {
                "TESTING": True,
                "DATABASE": self.db_path,
                "ADMIN_API_TOKEN": "admin-token",
                "SECRET_KEY": "test-secret",
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self._cleanup_db()

    def _cleanup_db(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_health_does_not_expose_secret_key_or_debug_flag(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "ok")
        self.assertNotIn("secret_key", payload)
        self.assertNotIn("debug", payload)
        self.assertIn("counts", payload)

    def test_user_listing_and_login_hide_passwords(self):
        users_response = self.client.get("/usuarios")
        self.assertEqual(users_response.status_code, 200)
        users_payload = users_response.get_json()
        self.assertGreaterEqual(len(users_payload["dados"]), 1)
        self.assertNotIn("senha", users_payload["dados"][0])

        login_response = self.client.post(
            "/login",
            json={"email": "admin@loja.com", "senha": "admin123"},
        )
        self.assertEqual(login_response.status_code, 200)
        login_payload = login_response.get_json()
        self.assertEqual(login_payload["dados"]["email"], "admin@loja.com")
        self.assertNotIn("senha", login_payload["dados"]) 

    def test_admin_routes_require_token_and_query_is_read_only(self):
        unauthorized_reset = self.client.post("/admin/reset-db")
        self.assertEqual(unauthorized_reset.status_code, 403)

        authorized_reset = self.client.post("/admin/reset-db", headers={"X-Admin-Token": "admin-token"})
        self.assertEqual(authorized_reset.status_code, 200)

        query_response = self.client.post(
            "/admin/query",
            headers={"X-Admin-Token": "admin-token"},
            json={"sql": "SELECT COUNT(*) AS total FROM produtos"},
        )
        self.assertEqual(query_response.status_code, 200)
        self.assertEqual(query_response.get_json()["dados"][0]["total"], 0)

        blocked_write = self.client.post(
            "/admin/query",
            headers={"X-Admin-Token": "admin-token"},
            json={"sql": "DELETE FROM produtos"},
        )
        self.assertEqual(blocked_write.status_code, 400)

    def test_create_product_and_failed_order_use_safe_boundaries(self):
        create_response = self.client.post(
            "/produtos",
            json={
                "nome": "Mesa d'agua",
                "descricao": "Produto com aspas simples",
                "preco": 12.5,
                "estoque": 4,
                "categoria": "geral",
            },
        )
        self.assertEqual(create_response.status_code, 201)

        search_response = self.client.get("/produtos/busca", query_string={"q": "Mesa d'agua"})
        self.assertEqual(search_response.status_code, 200)
        search_payload = search_response.get_json()
        self.assertTrue(any(item["nome"] == "Mesa d'agua" for item in search_payload["dados"]))

        before_orders = self.client.get("/pedidos").get_json()["dados"]
        before_products = self.client.get("/produtos").get_json()["dados"]
        before_stock = next(item["estoque"] for item in before_products if item["id"] == 1)

        failed_order = self.client.post(
            "/pedidos",
            json={
                "usuario_id": 1,
                "itens": [
                    {"produto_id": 1, "quantidade": 1},
                    {"produto_id": 9999, "quantidade": 1},
                ],
            },
        )
        self.assertEqual(failed_order.status_code, 404)

        after_orders = self.client.get("/pedidos").get_json()["dados"]
        after_products = self.client.get("/produtos").get_json()["dados"]
        after_stock = next(item["estoque"] for item in after_products if item["id"] == 1)

        self.assertEqual(len(after_orders), len(before_orders))
        self.assertEqual(after_stock, before_stock)


if __name__ == "__main__":
    unittest.main()
