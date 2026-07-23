from sqlalchemy import event, select

from database import db
from models.user import User
from tests.support import DatabaseTestCase


class SeedTransactionTests(DatabaseTestCase):
    def test_failure_rolls_back_the_entire_seed(self):
        before = {
            user.email: user.password
            for user in db.session.scalars(select(User)).all()
        }

        def fail_after_categories(stage):
            if stage == "categories":
                raise RuntimeError("falha injetada")

        with self.assertRaisesRegex(RuntimeError, "falha injetada"):
            self.app.extensions["controllers"]["seed"].seed(
                {
                    "admin": "new-admin-password",
                    "user": "new-user-password",
                    "manager": "new-manager-password",
                },
                after_stage=fail_after_categories,
            )

        after = {
            user.email: user.password
            for user in db.session.scalars(select(User)).all()
        }
        self.assertEqual(before, after)
        self.assertEqual(
            {"users": 3, "categories": 4, "tasks": 10},
            self.app.extensions["controllers"]["seed"].repository.counts(),
        )

    def test_missing_seed_credentials_do_not_delete_data(self):
        with self.assertRaisesRegex(ValueError, "Credenciais de seed ausentes"):
            self.app.extensions["controllers"]["seed"].seed({})
        self.assertEqual(
            {"users": 3, "categories": 4, "tasks": 10},
            self.app.extensions["controllers"]["seed"].repository.counts(),
        )


class QueryCountTests(DatabaseTestCase):
    def count_queries(self, callback):
        statements = []

        def record(_connection, _cursor, statement, _parameters, _context, _many):
            statements.append(statement)

        event.listen(db.engine, "before_cursor_execute", record)
        try:
            response = callback()
        finally:
            event.remove(db.engine, "before_cursor_execute", record)
        self.assertEqual(200, response.status_code, response.get_data(as_text=True))
        return len(statements)

    def test_collection_queries_are_constant(self):
        headers = self.auth_headers("admin")
        self.assertLessEqual(
            self.count_queries(lambda: self.client.get("/tasks", headers=headers)), 2
        )
        self.assertLessEqual(
            self.count_queries(lambda: self.client.get("/users", headers=headers)), 2
        )
        self.assertLessEqual(
            self.count_queries(lambda: self.client.get("/categories", headers=headers)),
            2,
        )
        self.assertLessEqual(
            self.count_queries(
                lambda: self.client.get("/reports/summary", headers=headers)
            ),
            9,
        )
