from __future__ import annotations

import os
import tempfile
import unittest

os.environ.setdefault("APP_SECRET", "module-test-secret-with-at-least-32-characters")

from app import create_app
from config import Settings


class ApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory(prefix="store-api-test-")
        self.database_path = os.path.join(self._temporary_directory.name, "test.db")
        self.settings = Settings(
            database_path=self.database_path,
            secret_key="application-test-secret-with-at-least-32-characters",
            environment="test",
            bootstrap_admin_email="admin@example.test",
            bootstrap_admin_password="strong-admin-password",
        )
        self.application = create_app(self.settings)
        self.application.config.update(TESTING=True)
        self.client = self.application.test_client()

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    @staticmethod
    def bearer(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def login(self, email: str, password: str) -> str:
        response = self.client.post("/login", json={"email": email, "senha": password})
        self.assertEqual(200, response.status_code, response.get_json())
        return response.get_json()["token"]

    def admin_headers(self) -> dict[str, str]:
        return self.bearer(self.login("admin@example.test", "strong-admin-password"))

    def create_client(self, email: str = "client@example.test") -> tuple[int, dict[str, str]]:
        response = self.client.post(
            "/usuarios",
            json={"nome": "Cliente", "email": email, "senha": "strong-client-password"},
        )
        self.assertEqual(201, response.status_code, response.get_json())
        user_id = response.get_json()["dados"]["id"]
        return user_id, self.bearer(self.login(email, "strong-client-password"))
