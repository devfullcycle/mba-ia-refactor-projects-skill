from tests.support import DatabaseTestCase


class PublicContractTests(DatabaseTestCase):
    def call(self, method, path, expected_status, **kwargs):
        if path not in ("/", "/health", "/login") and "headers" not in kwargs:
            kwargs["headers"] = self.auth_headers("admin")
        response = self.client.open(path, method=method, **kwargs)
        self.assertEqual(
            expected_status,
            response.status_code,
            (method, path, response.get_data(as_text=True)),
        )
        return response.get_json()

    def test_all_22_http_operations_keep_their_shapes_and_statuses(self):
        self.assertEqual(
            {"message": "Task Manager API", "version": "1.0"},
            self.call("GET", "/", 200),
        )
        self.assertEqual("ok", self.call("GET", "/health", 200)["status"])

        tasks = self.call("GET", "/tasks", 200)
        self.assertEqual(10, len(tasks))
        self.assertTrue(
            {"overdue", "user_name", "category_name"}.issubset(tasks[0])
        )
        self.assertEqual(1, self.call("GET", "/tasks/1", 200)["id"])
        task = self.call(
            "POST",
            "/tasks",
            201,
            json={"title": "Nova task", "priority": 2, "tags": ["x", "y"]},
        )
        updated_task = self.call(
            "PUT", f"/tasks/{task['id']}", 200, json={"status": "done"}
        )
        self.assertEqual("done", updated_task["status"])
        self.assertEqual(
            {"message": "Task deletada com sucesso"},
            self.call("DELETE", f"/tasks/{task['id']}", 200),
        )
        self.assertEqual(
            1,
            len(self.call("GET", "/tasks/search?q=autentica%C3%A7%C3%A3o", 200)),
        )
        self.assertEqual(10, self.call("GET", "/tasks/stats", 200)["total"])

        users = self.call("GET", "/users", 200)
        self.assertEqual(3, len(users))
        self.assertIn("task_count", users[0])
        detail = self.call("GET", "/users/1", 200)
        self.assertEqual(4, len(detail["tasks"]))
        self.assertNotIn("password", detail)
        user = self.call(
            "POST",
            "/users",
            201,
            json={
                "name": "Novo",
                "email": "novo@example.com",
                "password": "safe-password",
            },
        )
        self.assertNotIn("password", user)
        updated_user = self.call(
            "PUT",
            f"/users/{user['id']}",
            200,
            json={"name": "Atualizado", "active": False},
        )
        self.assertFalse(updated_user["active"])
        self.assertEqual(
            {"message": "Usuário deletado com sucesso"},
            self.call("DELETE", f"/users/{user['id']}", 200),
        )
        self.assertEqual(4, len(self.call("GET", "/users/1/tasks", 200)))
        login = self.call(
            "POST",
            "/login",
            200,
            json={"email": "joao@email.com", "password": self.passwords["admin"]},
        )
        self.assertNotIn("password", login["user"])
        self.assertEqual(
            login["user"]["id"],
            self.app.extensions["auth_service"].verify_token(login["token"]),
        )

        summary = self.call("GET", "/reports/summary", 200)
        self.assertEqual(
            {"total_tasks": 10, "total_users": 3, "total_categories": 4},
            summary["overview"],
        )
        self.assertEqual(
            4,
            self.call("GET", "/reports/user/1", 200)["statistics"]["total_tasks"],
        )

        categories = self.call("GET", "/categories", 200)
        self.assertEqual(4, len(categories))
        self.assertIn("task_count", categories[0])
        category = self.call(
            "POST", "/categories", 201, json={"name": "Documentação"}
        )
        updated_category = self.call(
            "PUT",
            f"/categories/{category['id']}",
            200,
            json={"color": "#ffffff"},
        )
        self.assertEqual("#ffffff", updated_category["color"])
        self.assertEqual(
            {"message": "Categoria deletada"},
            self.call("DELETE", f"/categories/{category['id']}", 200),
        )

    def test_invalid_types_are_400_instead_of_500(self):
        headers = self.auth_headers("admin")
        cases = [
            ("POST", "/tasks", {"title": "Task válida", "priority": "x"}),
            ("PUT", "/tasks/1", {"title": 42}),
            ("GET", "/tasks/search?priority=x", None),
            ("PUT", "/users/1", {"active": "yes"}),
        ]
        for method, path, payload in cases:
            with self.subTest(method=method, path=path):
                response = self.client.open(
                    path,
                    method=method,
                    json=payload,
                    headers=headers,
                )
                self.assertEqual(400, response.status_code)
                self.assertEqual({"error"}, set(response.get_json()))

    def test_not_found_and_conflict_envelopes_are_preserved(self):
        self.assertEqual(
            {"error": "Task não encontrada"},
            self.call("GET", "/tasks/999", 404),
        )
        self.assertEqual(
            {"error": "Email já cadastrado"},
            self.call(
                "POST",
                "/users",
                409,
                json={
                    "name": "Duplicado",
                    "email": "joao@email.com",
                    "password": "safe-password",
                },
            ),
        )

    def test_authentication_and_role_matrix(self):
        all_roles = {"user", "manager", "admin"}
        managers = {"manager", "admin"}
        admins = {"admin"}
        operations = (
            ("GET", "/tasks", None, all_roles),
            ("GET", "/tasks/1", None, all_roles),
            ("POST", "/tasks", {"title": "Autorização"}, managers),
            ("PUT", "/tasks/999", {"status": "done"}, managers),
            ("DELETE", "/tasks/999", None, managers),
            ("GET", "/tasks/search?q=login", None, all_roles),
            ("GET", "/tasks/stats", None, all_roles),
            ("GET", "/users", None, admins),
            ("GET", "/users/1", None, admins),
            (
                "POST",
                "/users",
                {
                    "name": "Matriz",
                    "email": "matrix@example.com",
                    "password": "matrix-password",
                },
                admins,
            ),
            ("PUT", "/users/999", {"name": "Matriz"}, admins),
            ("DELETE", "/users/999", None, admins),
            ("GET", "/users/1/tasks", None, admins),
            ("GET", "/reports/summary", None, managers),
            ("GET", "/reports/user/1", None, managers),
            ("GET", "/categories", None, all_roles),
            ("POST", "/categories", {"name": "Matriz"}, managers),
            ("PUT", "/categories/999", {"name": "Matriz"}, managers),
            ("DELETE", "/categories/999", None, managers),
        )

        for method, path, payload, _allowed_roles in operations:
            with self.subTest(method=method, path=path, role="anonymous"):
                response = self.client.open(path, method=method, json=payload)
                self.assertEqual(401, response.status_code)
                self.assertEqual(
                    {"error": "Autenticação obrigatória"},
                    response.get_json(),
                )

        for role in ("user", "manager", "admin"):
            headers = self.auth_headers(role)
            for method, path, payload, allowed_roles in operations:
                with self.subTest(method=method, path=path, role=role):
                    response = self.client.open(
                        path,
                        method=method,
                        json=payload,
                        headers=headers,
                    )
                    if role in allowed_roles:
                        self.assertNotIn(
                            response.status_code,
                            (401, 403),
                            response.get_data(as_text=True),
                        )
                    else:
                        self.assertEqual(403, response.status_code)
                        self.assertEqual(
                            {"error": "Permissão insuficiente"},
                            response.get_json(),
                        )

        for method, path, payload in (
            ("GET", "/", None),
            ("GET", "/health", None),
            (
                "POST",
                "/login",
                {
                    "email": "joao@email.com",
                    "password": self.passwords["admin"],
                },
            ),
        ):
            with self.subTest(method=method, path=path, role="public"):
                response = self.client.open(
                    path,
                    method=method,
                    json=payload,
                )
                self.assertEqual(200, response.status_code)

    def test_invalid_and_tampered_bearer_tokens_are_401(self):
        for authorization in ("Basic abc", "Bearer", "Bearer invalid-token"):
            with self.subTest(authorization=authorization):
                response = self.client.get(
                    "/tasks",
                    headers={"Authorization": authorization},
                )
                self.assertEqual(401, response.status_code)
