# -*- coding: utf-8 -*-
"""Testes de validacao - task-manager-api (Python/Flask + SQLAlchemy)"""
import os
import sys
os.environ.setdefault("SECRET_KEY", "test-secret")
sys.stdout.reconfigure(encoding="utf-8")

from app import app, db
from seed import seed_data


def run_tests():
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed_data()

    client = app.test_client()
    passed = 0
    failed = 0

    def check(label, response, expected_status, **assertions):
        nonlocal passed, failed
        ok = response.status_code == expected_status
        data = response.get_json()
        if data is None:
            data = {}
        for key, expected in assertions.items():
            actual = data.get(key) if isinstance(data, dict) else None
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

    def manual_pass(label):
        nonlocal passed
        passed += 1
        print(f"  [PASS] {label}")

    def manual_fail(label, detail=""):
        nonlocal failed
        failed += 1
        print(f"  [FAIL] {label}  {detail}")

    print("\n=== Projeto 3 - task-manager-api ===\n")

    print("--- Raiz e Health ---")
    check("GET /",       client.get("/"),       200, version="2.0.0")
    check("GET /health", client.get("/health"), 200, status="ok")

    print("\n--- Tasks ---")
    r_tasks = client.get("/tasks")
    tasks = r_tasks.get_json()
    if isinstance(tasks, list) and len(tasks) >= 10:
        manual_pass(f"GET /tasks - {len(tasks)} tasks retornadas")
    else:
        manual_fail("GET /tasks", f"esperava lista com >=10 items, got {tasks}")

    check("GET /tasks/1",      client.get("/tasks/1"), 200)
    check("GET /tasks/9999 - 404", client.get("/tasks/9999"), 404)
    check("POST /tasks - cria task",
          client.post("/tasks", json={
              "title": "Nova Task de Teste",
              "status": "pending",
              "priority": 3,
              "user_id": 1,
          }), 201)
    check("POST /tasks - status invalido -> 400",
          client.post("/tasks", json={"title": "X", "status": "invalido"}), 400)

    print("\n--- Usuarios (password NAO deve aparecer) ---")
    r_users = client.get("/users")
    check("GET /users - retorna 200", r_users, 200)
    users = r_users.get_json()
    if isinstance(users, list) and users:
        if "password" not in users[0]:
            manual_pass("GET /users - campo 'password' NAO exposto")
        else:
            manual_fail("GET /users - campo 'password' EXPOSTO (bug de seguranca)")

    check("GET /users/1",          client.get("/users/1"), 200)
    check("GET /users/9999 - 404", client.get("/users/9999"), 404)

    print("\n--- Login (senha com werkzeug, nao MD5) ---")
    r_login = client.post("/login", json={"email": "joao@email.com", "password": "1234"})
    check("POST /login - senha correta -> 200", r_login, 200)

    r_fail = client.post("/login", json={"email": "joao@email.com", "password": "errada"})
    check("POST /login - senha errada -> 401", r_fail, 401)

    check("POST /login - campos ausentes -> 400",
          client.post("/login", json={}), 400)

    print("\n--- Relatorios ---")
    r_sum = client.get("/reports/summary")
    check("GET /reports/summary - retorna 200", r_sum, 200)
    summary = r_sum.get_json() or {}
    total = summary.get("overview", {}).get("total_tasks", 0)
    if total >= 10:
        manual_pass(f"GET /reports/summary - total_tasks={total}")
    else:
        manual_fail("GET /reports/summary", f"total_tasks={total}")

    check("GET /reports/user/1",      client.get("/reports/user/1"), 200)
    check("GET /reports/user/9999 - 404", client.get("/reports/user/9999"), 404)

    print("\n--- Categorias ---")
    check("GET /categories",
          client.get("/categories"), 200)
    check("POST /categories - cria categoria",
          client.post("/categories", json={"name": "Teste", "color": "#ff0000"}), 201)

    print(f"\n{'='*40}")
    print(f"Resultado: {passed} PASS / {failed} FAIL")
    print(f"{'='*40}\n")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
