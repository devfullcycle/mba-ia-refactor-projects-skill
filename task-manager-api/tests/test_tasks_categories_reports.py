TASK_FIELDS = {"id", "title", "description", "status", "priority", "user_id", "category_id",
               "created_at", "updated_at", "due_date", "tags"}


def test_task_list_and_detail_contract(client, regular):
    headers, _ = regular
    tasks = client.get("/tasks", headers=headers).get_json()
    assert len(tasks) == 10
    assert set(tasks[0]) == TASK_FIELDS | {"overdue", "user_name", "category_name"}
    assert tasks[0]["user_name"] == "João Silva" and tasks[0]["overdue"] is True

    detail = client.get("/tasks/1", headers=headers).get_json()
    assert set(detail) == TASK_FIELDS | {"overdue"}
    assert client.get("/tasks/999", headers=headers).get_json() == {"error": "Task não encontrada"}

    page = client.get("/tasks?page=2&per_page=4", headers=headers)
    assert [t["id"] for t in page.get_json()] == [5, 6, 7, 8] and page.headers["X-Total-Count"] == "10"


def test_task_crud_and_validation(client, regular):
    headers, me = regular
    payload = {"title": "Nova task", "priority": 2, "category_id": 1, "due_date": "2030-01-31", "tags": ["a", "b"]}
    created = client.post("/tasks", headers=headers, json={**payload, "user_id": me["id"]})
    assert created.status_code == 201
    task = created.get_json()
    assert set(task) == TASK_FIELDS and task["tags"] == ["a", "b"] and task["status"] == "pending"

    invalid_payloads = (
        {"title": "ab"}, {"title": "x" * 201}, {"title": 123}, {"title": "Válido", "priority": "alta"},
        {"title": "Válido", "priority": 9}, {"title": "Válido", "status": "x"},
        {"title": "Válido", "due_date": "31/01/2030"}, {},
    )
    for bad in invalid_payloads:
        assert client.post("/tasks", headers=headers, json=bad).status_code == 400, bad
    assert client.post("/tasks", headers=headers, json={"title": "Válido", "category_id": 999}).status_code == 404

    updated = client.put(f"/tasks/{task['id']}", headers=headers, json={"status": "done", "due_date": None})
    body = updated.get_json()
    assert updated.status_code == 200 and body["status"] == "done" and body["due_date"] is None
    deleted = client.delete(f"/tasks/{task['id']}", headers=headers)
    assert deleted.get_json() == {"message": "Task deletada com sucesso"}


def test_regular_user_cannot_touch_others_tasks(client, regular, manager):
    headers, _ = regular
    # Task 1 pertence ao admin.
    assert client.put("/tasks/1", headers=headers, json={"title": "Invadida"}).status_code == 403
    assert client.delete("/tasks/1", headers=headers).status_code == 403
    assert client.post("/tasks", headers=headers, json={"title": "Para outro", "user_id": 1}).status_code == 403

    manager_headers, _ = manager
    assert client.put("/tasks/1", headers=manager_headers, json={"priority": 5}).status_code == 200


def test_search_and_stats(client, regular):
    headers, _ = regular
    found = client.get("/tasks/search?q=bug", headers=headers).get_json()
    assert [t["id"] for t in found] == [4] and set(found[0]) == TASK_FIELDS
    assert len(client.get("/tasks/search?status=pending&priority=1", headers=headers).get_json()) == 2
    assert client.get("/tasks/search?priority=abc", headers=headers).status_code == 400

    assert client.get("/tasks/stats", headers=headers).get_json() == {
        "total": 10, "pending": 6, "in_progress": 2, "done": 1, "cancelled": 1, "overdue": 2, "completion_rate": 10.0,
    }


def test_categories(client, regular, manager):
    headers, _ = regular
    categories = client.get("/categories", headers=headers).get_json()
    assert set(categories[0]) == {"id", "name", "description", "color", "created_at", "task_count"}
    assert categories[0]["task_count"] == 6
    assert client.post("/categories", headers=headers, json={"name": "X"}).status_code == 403

    staff, _ = manager
    created = client.post("/categories", headers=staff, json={"name": "QA"})
    assert created.status_code == 201 and created.get_json()["color"] == "#000000"
    assert client.post("/categories", headers=staff, json={"name": "QA", "color": "azul"}).status_code == 400
    assert client.put(f"/categories/{created.get_json()['id']}", headers=staff).status_code == 400
    assert client.put("/categories/4", headers=staff, json={"color": "#ffffff"}).get_json()["color"] == "#ffffff"

    assert client.delete("/categories/4", headers=staff).get_json() == {"message": "Categoria deletada"}
    # Task 4 era da categoria removida: fica desvinculada, sem FK órfã.
    assert client.get("/tasks/4", headers=staff).get_json()["category_id"] is None


def test_reports(client, regular, admin):
    headers, me = regular
    assert client.get("/reports/summary", headers=headers).status_code == 403
    assert client.get("/reports/user/1", headers=headers).status_code == 403
    own = client.get(f"/reports/user/{me['id']}", headers=headers).get_json()
    assert own["statistics"] == {
        "total_tasks": 3, "done": 0, "pending": 1, "in_progress": 2, "cancelled": 0,
        "overdue": 0, "high_priority": 2, "completion_rate": 0,
    }

    admin_headers, _ = admin
    summary = client.get("/reports/summary", headers=admin_headers).get_json()
    assert list(summary) == ["generated_at", "overview", "tasks_by_status", "tasks_by_priority", "overdue",
                             "recent_activity", "user_productivity"]
    assert summary["overview"] == {"total_tasks": 10, "total_users": 3, "total_categories": 4}
    assert summary["tasks_by_priority"] == {"critical": 2, "high": 3, "medium": 3, "low": 2, "minimal": 0}
    assert summary["overdue"]["count"] == 2
    assert summary["recent_activity"]["tasks_created_last_7_days"] == 10
    assert summary["user_productivity"][2]["completion_rate"] == 33.33
    assert client.get("/reports/user/999", headers=admin_headers).status_code == 404


def test_unknown_route_returns_json(client):
    response = client.get("/nao-existe")
    assert response.status_code == 404 and "error" in response.get_json()
