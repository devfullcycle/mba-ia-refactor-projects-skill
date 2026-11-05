"""Testes de fumaça/caracterização da API de Task Manager (task-manager-api).

Cobrem o contrato HTTP atual (rotas, status e campos principais) para detectar
regressões após refatorações. O servidor é iniciado com dados do `seed.py`
(3 usuários, 4 categorias, 10 tasks). Os testes compartilham o servidor; cada
um cria os próprios dados e usa asserções que toleram dados de outros testes.
"""
import uuid


def _sufixo():
    return uuid.uuid4().hex[:8]


def _criar_usuario(api, **extra):
    payload = {"name": "Usuario " + _sufixo(), "email": f"u{_sufixo()}@teste.com",
               "password": "segredo"}
    payload.update(extra)
    r = api.post("/users", payload)
    assert r.status_code == 201, r.text
    return r.json()


def _criar_task(api, **extra):
    payload = {"title": "Task " + _sufixo()}
    payload.update(extra)
    r = api.post("/tasks", payload)
    assert r.status_code == 201, r.text
    return r.json()


# ---------- raiz / health ----------

def test_raiz(api):
    r = api.get("/")
    assert r.status_code == 200
    assert r.json()["message"] == "Task Manager API"


def test_health(api):
    r = api.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---------- login ----------

def test_login_sucesso(api):
    r = api.post("/login", {"email": "joao@email.com", "password": "1234"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["user"]["email"] == "joao@email.com"
    assert corpo["token"] == "fake-jwt-token-" + str(corpo["user"]["id"])


def test_login_credenciais_invalidas(api):
    assert api.post("/login", {"email": "joao@email.com", "password": "errada"}).status_code == 401
    assert api.post("/login", {"email": "naoexiste@email.com", "password": "1234"}).status_code == 401


def test_login_campos_obrigatorios(api):
    assert api.post("/login", {"email": "joao@email.com"}).status_code == 400


def test_login_usuario_inativo(api):
    usuario = _criar_usuario(api, password="abcd")
    assert api.put(f"/users/{usuario['id']}", {"active": False}).status_code == 200
    r = api.post("/login", {"email": usuario["email"], "password": "abcd"})
    assert r.status_code == 403


# ---------- usuários ----------

def test_listar_usuarios_seed(api):
    r = api.get("/users")
    assert r.status_code == 200
    usuarios = r.json()
    assert len(usuarios) >= 3
    for chave in ("id", "name", "email", "role", "active", "task_count"):
        assert chave in usuarios[0]


def test_buscar_usuario_com_tasks(api):
    r = api.get("/users/1")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["email"] == "joao@email.com"
    assert isinstance(corpo["tasks"], list)
    assert api.get("/users/999999").status_code == 404


def test_crud_usuario(api):
    usuario = _criar_usuario(api, role="manager")
    uid = usuario["id"]
    assert usuario["role"] == "manager"

    r = api.put(f"/users/{uid}", {"name": "Nome Novo"})
    assert r.status_code == 200
    assert r.json()["name"] == "Nome Novo"

    assert api.delete(f"/users/{uid}").status_code == 200
    assert api.get(f"/users/{uid}").status_code == 404


def test_criar_usuario_validacoes(api):
    existente = _criar_usuario(api)
    base = {"name": "Fulano", "email": f"f{_sufixo()}@teste.com", "password": "abcd"}
    casos = [
        ({k: v for k, v in base.items() if k != "name"}, 400),
        ({k: v for k, v in base.items() if k != "email"}, 400),
        ({k: v for k, v in base.items() if k != "password"}, 400),
        ({**base, "email": "invalido"}, 400),
        ({**base, "password": "123"}, 400),
        ({**base, "role": "superuser"}, 400),
        ({**base, "email": existente["email"]}, 409),
    ]
    for payload, esperado in casos:
        assert api.post("/users", payload).status_code == esperado, payload


def test_tasks_do_usuario(api):
    usuario = _criar_usuario(api)
    task = _criar_task(api, user_id=usuario["id"])
    r = api.get(f"/users/{usuario['id']}/tasks")
    assert r.status_code == 200
    assert [t["id"] for t in r.json()] == [task["id"]]
    assert api.get("/users/999999/tasks").status_code == 404


def test_deletar_usuario_remove_suas_tasks(api):
    usuario = _criar_usuario(api)
    task = _criar_task(api, user_id=usuario["id"])
    assert api.delete(f"/users/{usuario['id']}").status_code == 200
    assert api.get(f"/tasks/{task['id']}").status_code == 404


# ---------- tasks ----------

def test_listar_tasks_seed(api):
    r = api.get("/tasks")
    assert r.status_code == 200
    tasks = r.json()
    assert len(tasks) >= 10
    for chave in ("id", "title", "status", "priority", "tags", "overdue",
                  "user_name", "category_name"):
        assert chave in tasks[0]


def test_buscar_task(api):
    r = api.get("/tasks/1")
    assert r.status_code == 200
    assert "overdue" in r.json()
    assert api.get("/tasks/999999").status_code == 404


def test_crud_task(api):
    task = _criar_task(api, description="desc", priority=2, tags=["a", "b"],
                       due_date="2030-01-31")
    tid = task["id"]
    assert task["status"] == "pending"
    assert task["priority"] == 2
    assert task["tags"] == ["a", "b"]
    assert task["due_date"].startswith("2030-01-31")

    r = api.put(f"/tasks/{tid}", {"status": "done", "priority": 5})
    assert r.status_code == 200
    assert r.json()["status"] == "done"
    assert api.get(f"/tasks/{tid}").json()["priority"] == 5

    assert api.delete(f"/tasks/{tid}").status_code == 200
    assert api.get(f"/tasks/{tid}").status_code == 404


def test_task_vencida_marcada_como_overdue(api):
    task = _criar_task(api, due_date="2000-01-01")
    assert api.get(f"/tasks/{task['id']}").json()["overdue"] is True
    api.put(f"/tasks/{task['id']}", {"status": "done"})
    assert api.get(f"/tasks/{task['id']}").json()["overdue"] is False


def test_criar_task_validacoes(api):
    usuario = _criar_usuario(api)
    base = {"title": "Titulo valido"}
    casos = [
        ({}, 400),
        ({"title": "ab"}, 400),
        ({"title": "x" * 201}, 400),
        ({**base, "status": "invalido"}, 400),
        ({**base, "priority": 9}, 400),
        ({**base, "due_date": "31/01/2030"}, 400),
        ({**base, "user_id": 999999}, 404),
        ({**base, "category_id": 999999}, 404),
    ]
    for payload, esperado in casos:
        assert api.post("/tasks", payload).status_code == esperado, payload
    assert api.post("/tasks", {**base, "user_id": usuario["id"]}).status_code == 201


def test_atualizar_task_validacoes(api):
    task = _criar_task(api)
    tid = task["id"]
    assert api.put("/tasks/999999", {"title": "Qualquer"}).status_code == 404
    assert api.put(f"/tasks/{tid}", {"title": "ab"}).status_code == 400
    assert api.put(f"/tasks/{tid}", {"status": "invalido"}).status_code == 400
    assert api.put(f"/tasks/{tid}", {"priority": 0}).status_code == 400
    assert api.put(f"/tasks/{tid}", {"user_id": 999999}).status_code == 404
    assert api.delete("/tasks/999999").status_code == 404


def test_busca_de_tasks(api):
    marcador = "marcador" + _sufixo()
    task = _criar_task(api, title="Busca " + marcador, priority=4)

    r = api.get("/tasks/search", params={"q": marcador})
    assert r.status_code == 200
    assert [t["id"] for t in r.json()] == [task["id"]]

    r = api.get("/tasks/search", params={"q": marcador, "status": "done"})
    assert r.json() == []

    r = api.get("/tasks/search", params={"priority": 4})
    assert task["id"] in [t["id"] for t in r.json()]
    assert all(t["priority"] == 4 for t in r.json())


def test_stats_de_tasks(api):
    r = api.get("/tasks/stats")
    assert r.status_code == 200
    s = r.json()
    for chave in ("total", "pending", "in_progress", "done", "cancelled",
                  "overdue", "completion_rate"):
        assert chave in s
    assert s["total"] == s["pending"] + s["in_progress"] + s["done"] + s["cancelled"]


# ---------- categorias ----------

def test_listar_categorias_seed(api):
    r = api.get("/categories")
    assert r.status_code == 200
    categorias = r.json()
    assert len(categorias) >= 4
    assert "task_count" in categorias[0]


def test_crud_categoria(api):
    r = api.post("/categories", {"name": "Cat " + _sufixo(), "color": "#ff0000"})
    assert r.status_code == 201
    cid = r.json()["id"]

    r = api.put(f"/categories/{cid}", {"description": "nova descricao"})
    assert r.status_code == 200
    assert r.json()["description"] == "nova descricao"

    assert api.delete(f"/categories/{cid}").status_code == 200
    assert api.delete(f"/categories/{cid}").status_code == 404


def test_categoria_validacoes(api):
    assert api.post("/categories", {"description": "sem nome"}).status_code == 400
    assert api.put("/categories/999999", {"name": "X"}).status_code == 404


# ---------- relatórios ----------

def test_relatorio_resumo(api):
    r = api.get("/reports/summary")
    assert r.status_code == 200
    corpo = r.json()
    for chave in ("overview", "tasks_by_status", "tasks_by_priority", "overdue",
                  "recent_activity", "user_productivity"):
        assert chave in corpo
    assert corpo["overview"]["total_users"] >= 3
    assert corpo["overview"]["total_tasks"] >= 10


def test_relatorio_por_usuario(api):
    r = api.get("/reports/user/1")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["user"]["id"] == 1
    assert "statistics" in corpo
    assert api.get("/reports/user/999999").status_code == 404
