import hashlib
import os
import tempfile
from pathlib import Path
from unittest import TestCase, mock

from app import create_app
from config import ConfigurationError, Settings
from database import db
from models.user import User
from services.auth_service import AuthService, ExpiredAuthToken, InvalidAuthToken
from services.notification_service import NotificationDeliveryError, NotificationService
from tests.support import DatabaseTestCase


class ConfigurationTests(TestCase):
    def test_secret_is_required(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ConfigurationError, "SECRET_KEY"):
                Settings.load()

    def test_factory_has_no_schema_side_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "factory.db"
            app = create_app(
                {
                    "SECRET_KEY": "factory-test-secret",
                    "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
                    "TESTING": True,
                }
            )
            self.assertFalse(database_path.exists())
            with app.app_context():
                db.create_all()
            self.assertTrue(database_path.exists())

    def test_debug_is_false_by_default(self):
        settings = Settings.load({"SECRET_KEY": "test-secret"})
        self.assertFalse(settings.debug)


class AuthenticationTests(DatabaseTestCase):
    def test_hashes_are_adaptive_salted_and_never_presented(self):
        first = User(name="A", email="a@example.com")
        second = User(name="B", email="b@example.com")
        first.set_password("same-password")
        second.set_password("same-password")
        self.assertNotEqual(first.password, second.password)
        self.assertGreater(len(first.password), 32)
        self.assertTrue(first.check_password("same-password"))
        self.assertFalse(first.check_password("wrong-password"))

        responses = [
            self.client.get("/users/1", headers=self.auth_headers("admin")),
            self.client.post(
                "/login",
                json={
                    "email": "joao@email.com",
                    "password": self.passwords["admin"],
                },
            ),
        ]
        for response in responses:
            self.assertNotIn("password", response.get_data(as_text=True).lower())

    def test_legacy_md5_is_rehashed_after_successful_login(self):
        user = User(name="Legado", email="legacy@example.com", role="user")
        user.password = hashlib.md5(b"legacy-password").hexdigest()
        db.session.add(user)
        db.session.commit()
        old_hash = user.password

        response = self.client.post(
            "/login",
            json={"email": user.email, "password": "legacy-password"},
        )
        self.assertEqual(200, response.status_code)
        db.session.refresh(user)
        self.assertNotEqual(old_hash, user.password)
        self.assertGreater(len(user.password), 32)

    def test_tokens_reject_tampering_and_expiration(self):
        service = AuthService("token-test-secret", ttl_seconds=60)
        token = service.issue_token(123)
        self.assertEqual(123, service.verify_token(token))
        with self.assertRaises(InvalidAuthToken):
            service.verify_token(token + "tampered")

        expired_service = AuthService("token-test-secret", ttl_seconds=-1)
        with self.assertRaises(ExpiredAuthToken):
            expired_service.verify_token(expired_service.issue_token(123))


class NotificationAdapterTests(TestCase):
    def test_smtp_uses_timeout_and_context_manager(self):
        service = NotificationService(
            "smtp.example.com",
            587,
            "sender@example.com",
            "smtp-password",
            timeout_seconds=7,
        )
        connection = mock.MagicMock()
        smtp_context = mock.MagicMock()
        smtp_context.__enter__.return_value = connection
        with mock.patch(
            "services.notification_service.smtplib.SMTP",
            return_value=smtp_context,
        ) as smtp:
            self.assertTrue(service.send_email("to@example.com", "Assunto", "Corpo"))

        smtp.assert_called_once_with("smtp.example.com", 587, timeout=7)
        connection.starttls.assert_called_once_with()
        connection.login.assert_called_once_with("sender@example.com", "smtp-password")
        smtp_context.__exit__.assert_called_once()

    def test_smtp_failure_is_typed_and_does_not_report_success(self):
        service = NotificationService(
            "smtp.example.com",
            587,
            "sender@example.com",
            "smtp-password",
        )
        with mock.patch(
            "services.notification_service.smtplib.SMTP",
            side_effect=OSError("network unavailable"),
        ):
            with self.assertRaises(NotificationDeliveryError):
                service.send_email("to@example.com", "Assunto", "Corpo")
