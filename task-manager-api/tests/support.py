import tempfile
import unittest
from pathlib import Path

from app import create_app
from database import db


class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "test.db"
        self.app = create_app(
            {
                "SECRET_KEY": "tests-only-secret-key",
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
                "TESTING": True,
            }
        )
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.passwords = {
            "admin": "admin-test-password",
            "user": "user-test-password",
            "manager": "manager-test-password",
        }
        self.app.extensions["controllers"]["seed"].seed(self.passwords)
        self.client = self.app.test_client()

    def auth_headers(self, role="admin"):
        emails = {
            "admin": "joao@email.com",
            "user": "maria@email.com",
            "manager": "pedro@email.com",
        }
        response = self.client.post(
            "/login",
            json={"email": emails[role], "password": self.passwords[role]},
        )
        self.assertEqual(200, response.status_code, response.get_data(as_text=True))
        return {"Authorization": f"Bearer {response.get_json()['token']}"}

    def tearDown(self):
        db.session.remove()
        self.context.pop()
        self.temporary_directory.cleanup()
