import hashlib

from src.config.database import db
from src.models import User
from tests.conftest import USER_PASSWORD, login

PROTECTED_GETS = ["/tasks", "/tasks/1", "/tasks/search", "/tasks/stats", "/users", "/users/1",
                  "/users/1/tasks", "/categories", "/reports/summary", "/reports/user/1"]


def test_public_endpoints(client):
    assert client.get("/").get_json() == {"message": "Task Manager API", "version": "1.0"}
    health = client.get("/health")
    assert health.status_code == 200 and health.get_json()["status"] == "ok"


def test_protected_endpoints_require_token(client):
    for path in PROTECTED_GETS:
        assert client.get(path).status_code == 401, path
    assert client.get("/tasks", headers={"Authorization": "Bearer fake-jwt-token-1"}).status_code == 401


def test_login_contract_and_no_password_leak(client):
    response = client.post("/login", json={"email": "maria@email.com", "password": USER_PASSWORD})
    body = response.get_json()
    assert response.status_code == 200
    assert body["message"] == "Login realizado com sucesso"
    assert "password" not in body["user"] and not body["token"].startswith("fake-jwt-token")

    assert client.post("/login", json={"email": "maria@email.com", "password": "errada"}).status_code == 401
    assert client.post("/login", json={"email": "x@y.com"}).status_code == 400
    assert client.post("/login", data="nao-json").status_code == 400


def test_public_signup_cannot_escalate_privilege(client, admin):
    new_user = {"name": "Ana", "email": "ana@email.com", "password": "senha-forte-1"}
    assert client.post("/users", json={**new_user, "role": "admin"}).status_code == 403

    created = client.post("/users", json=new_user)
    assert created.status_code == 201
    body = created.get_json()
    assert body["role"] == "user" and "password" not in body
    assert client.post("/users", json=new_user).status_code == 409
    assert client.post("/users", json={**new_user, "email": "invalido"}).status_code == 400
    assert client.post("/users", json={**new_user, "email": "b@email.com", "password": "123"}).status_code == 400

    headers, _ = admin
    manager = client.post("/users", headers=headers, json={**new_user, "email": "m@email.com", "role": "manager"})
    assert manager.status_code == 201 and manager.get_json()["role"] == "manager"


def test_user_update_permissions(client, regular, admin):
    headers, me = regular
    renamed = client.put(f"/users/{me['id']}", headers=headers, json={"name": "Maria S."})
    assert renamed.get_json()["name"] == "Maria S."
    assert client.put(f"/users/{me['id']}", headers=headers, json={"role": "admin"}).status_code == 403
    assert client.put("/users/1", headers=headers, json={"name": "Hacker"}).status_code == 403
    assert client.delete("/users/1", headers=headers).status_code == 403

    admin_headers, _ = admin
    assert client.put(f"/users/{me['id']}", headers=admin_headers, json={"active": "não"}).status_code == 400
    assert client.put(f"/users/{me['id']}", headers=admin_headers, json={"active": False}).status_code == 200
    # Usuário desativado perde o acesso imediatamente, mesmo com token ainda válido.
    assert client.get("/tasks", headers=headers).status_code == 401


def test_delete_user_removes_tasks(client, admin):
    headers, _ = admin
    assert len(client.get("/users/2/tasks", headers=headers).get_json()) == 3
    assert client.delete("/users/2", headers=headers).get_json() == {"message": "Usuário deletado com sucesso"}
    assert client.get("/users/2", headers=headers).status_code == 404
    assert all(task["user_id"] != 2 for task in client.get("/tasks", headers=headers).get_json())


def test_user_list_and_detail_contract(client, admin):
    headers, _ = admin
    users = client.get("/users", headers=headers).get_json()
    assert set(users[0]) == {"id", "name", "email", "role", "active", "created_at", "task_count"}
    detail = client.get("/users/1", headers=headers).get_json()
    assert "password" not in detail and isinstance(detail["tasks"], list)

    page = client.get("/users?page=1&per_page=2", headers=headers)
    assert len(page.get_json()) == 2 and page.headers["X-Total-Count"] == "3"


def test_legacy_md5_password_is_migrated_on_login(app, client):
    with app.app_context():
        user = db.session.get(User, 2)
        user.password = hashlib.md5(b"senha-legada").hexdigest()
        db.session.commit()

    login(client, "maria@email.com", "senha-legada")
    with app.app_context():
        assert not db.session.get(User, 2).has_legacy_password()
    login(client, "maria@email.com", "senha-legada")
