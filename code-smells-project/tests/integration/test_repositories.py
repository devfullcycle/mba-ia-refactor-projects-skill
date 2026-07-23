from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest

from store.domain.errors import ConflictError, ValidationError
from store.domain.models import OrderItem
from store.infrastructure.repositories import OrderRepository, UserRepository
from store.infrastructure.security import PasswordHasher
from store.infrastructure.sqlite import SQLiteDatabase


class CountingDatabase(SQLiteDatabase):
    def __init__(self, path: str) -> None:
        super().__init__(path)
        self.statements: list[str] = []

    def _connect(self) -> sqlite3.Connection:
        connection = super()._connect()
        connection.set_trace_callback(self.statements.append)
        return connection


class RepositoryIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory(prefix="store-repository-test-")
        self.database = CountingDatabase(os.path.join(self._temporary_directory.name, "test.db"))
        self.hasher = PasswordHasher()
        self.database.initialize(
            self.hasher,
            "admin@example.test",
            "strong-admin-password",
        )
        self.users = UserRepository(self.database)
        self.orders = OrderRepository(self.database)
        self.user_id = self.users.create(
            "Cliente",
            "client@example.test",
            self.hasher.hash("strong-client-password"),
        )

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def test_order_requires_existing_user_and_positive_quantity(self) -> None:
        with self.assertRaises(ValidationError):
            self.orders.create(99999, [OrderItem(1, 1)])
        with self.assertRaises(sqlite3.IntegrityError):
            with self.database.transaction() as connection:
                connection.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (1, 1, -1, 1)"
                )

    def test_failure_in_second_item_rolls_back_order_items_and_stock(self) -> None:
        with self.database.transaction() as connection:
            connection.executescript(
                """
                CREATE TRIGGER abort_second_test_item
                BEFORE INSERT ON itens_pedido
                WHEN NEW.produto_id = 2
                BEGIN SELECT RAISE(ABORT, 'injected failure'); END;
                """
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.orders.create(self.user_id, [OrderItem(1, 1), OrderItem(2, 1)])
        with self.database.connection() as connection:
            self.assertEqual(0, connection.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0])
            self.assertEqual(0, connection.execute("SELECT COUNT(*) FROM itens_pedido").fetchone()[0])
            self.assertEqual(10, connection.execute("SELECT estoque FROM produtos WHERE id = 1").fetchone()[0])

    def test_cancellation_restores_stock_once_and_is_terminal(self) -> None:
        result = self.orders.create(self.user_id, [OrderItem(1, 2)])
        self.orders.update_status(result["pedido_id"], "cancelado")
        self.orders.update_status(result["pedido_id"], "cancelado")
        with self.database.connection() as connection:
            stock = connection.execute("SELECT estoque FROM produtos WHERE id = 1").fetchone()[0]
        self.assertEqual(10, stock)
        with self.assertRaises(ConflictError):
            self.orders.update_status(result["pedido_id"], "aprovado")

    def test_order_graph_uses_one_select_instead_of_n_plus_one(self) -> None:
        self.orders.create(self.user_id, [OrderItem(1, 1), OrderItem(2, 1)])
        self.database.statements.clear()
        result = self.orders.list_all()
        selects = [statement for statement in self.database.statements if statement.lstrip().upper().startswith("SELECT")]
        self.assertEqual(1, len(selects), selects)
        self.assertEqual(2, len(result[0]["itens"]))
