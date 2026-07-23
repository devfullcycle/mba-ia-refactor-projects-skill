from __future__ import annotations

import unittest

from store.domain.errors import AuthenticationError
from store.infrastructure.security import PasswordHasher, TokenService


class SecurityTests(unittest.TestCase):
    def test_password_is_salted_hashed_and_verified(self) -> None:
        hasher = PasswordHasher()
        first = hasher.hash("a-strong-password")
        second = hasher.hash("a-strong-password")
        self.assertNotEqual("a-strong-password", first)
        self.assertNotEqual(first, second)
        self.assertTrue(hasher.verify(first, "a-strong-password"))
        self.assertFalse(hasher.verify(first, "wrong-password"))

    def test_signed_token_rejects_tampering(self) -> None:
        service = TokenService("token-test-secret-with-at-least-32-characters", 60)
        token = service.issue({"id": 7, "email": "a@example.test", "tipo": "cliente"})
        actor = service.verify(token)
        self.assertEqual(7, actor.user_id)
        with self.assertRaises(AuthenticationError):
            service.verify(token + "tampered")
