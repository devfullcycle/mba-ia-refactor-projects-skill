from datetime import datetime

from sqlalchemy.orm import joinedload

from database import db
from models.category import Category
from models.task import Task
from models.user import User


def _serialize_task(t, now=None):
    now = now or datetime.utcnow()
    task_data = t.to_dict()
    if t.due_date:
        if t.due_date < now:
            if t.status != "done" and t.status != "cancelled":
                task_data["overdue"] = True
            else:
                task_data["overdue"] = False
        else:
            task_data["overdue"] = False
    else:
        task_data["overdue"] = False

    if t.user_id and t.user:
        task_data["user_name"] = t.user.name
    else:
        task_data["user_name"] = None

    if t.category_id and t.category:
        task_data["category_name"] = t.category.name
    else:
        task_data["category_name"] = None
    return task_data


def list_tasks():
    tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
    now = datetime.utcnow()
    return [_serialize_task(t, now) for t in tasks], 200


def get_task(task_id):
    task = Task.query.options(joinedload(Task.user), joinedload(Task.category)).get(task_id)
    if not task:
        return {"error": "Task não encontrada"}, 404
    now = datetime.utcnow()
    data = _serialize_task(task, now)
    return data, 200


def create_task(data):
    if not data:
        return {"error": "Dados inválidos"}, 400
    title = data.get("title")
    if not title:
        return {"error": "Título é obrigatório"}, 400
    if len(title) < 3:
        return {"error": "Título muito curto"}, 400
    if len(title) > 200:
        return {"error": "Título muito longo"}, 400

    description = data.get("description", "")
    status = data.get("status", "pending")
    try:
        priority = int(data.get("priority", 3))
    except (TypeError, ValueError):
        return {"error": "Prioridade deve ser um inteiro entre 1 e 5"}, 400
    user_id = data.get("user_id")
    category_id = data.get("category_id")
    due_date = data.get("due_date")
    tags = data.get("tags")

    if status not in ["pending", "in_progress", "done", "cancelled"]:
        return {"error": "Status inválido"}, 400
    if priority < 1 or priority > 5:
        return {"error": "Prioridade deve ser entre 1 e 5"}, 400

    if user_id:
        if not User.query.get(user_id):
            return {"error": "Usuário não encontrado"}, 404
    if category_id:
        if not Category.query.get(category_id):
            return {"error": "Categoria não encontrada"}, 404

    task = Task()
    task.title = title
    task.description = description
    task.status = status
    task.priority = priority
    task.user_id = user_id
    task.category_id = category_id

    if due_date:
        try:
            task.due_date = datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            return {"error": "Formato de data inválido. Use YYYY-MM-DD"}, 400

    if tags:
        task.tags = ",".join(tags) if isinstance(tags, list) else tags

    try:
        db.session.add(task)
        db.session.commit()
        return task.to_dict(), 201
    except Exception:
        db.session.rollback()
        return {"error": "Erro ao criar task"}, 500


def update_task(task_id, data):
    task = Task.query.get(task_id)
    if not task:
        return {"error": "Task não encontrada"}, 404
    if not data:
        return {"error": "Dados inválidos"}, 400

    if "title" in data:
        if len(data["title"]) < 3:
            return {"error": "Título muito curto"}, 400
        if len(data["title"]) > 200:
            return {"error": "Título muito longo"}, 400
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "status" in data:
        if data["status"] not in ["pending", "in_progress", "done", "cancelled"]:
            return {"error": "Status inválido"}, 400
        task.status = data["status"]
    if "priority" in data:
        try:
            prio = int(data["priority"])
        except (TypeError, ValueError):
            return {"error": "Prioridade deve ser um inteiro entre 1 e 5"}, 400
        if prio < 1 or prio > 5:
            return {"error": "Prioridade deve ser entre 1 e 5"}, 400
        task.priority = prio
    if "user_id" in data:
        uid = data["user_id"]
        if uid and not User.query.get(uid):
            return {"error": "Usuário não encontrado"}, 404
        task.user_id = uid
    if "category_id" in data:
        cid = data["category_id"]
        if cid and not Category.query.get(cid):
            return {"error": "Categoria não encontrada"}, 404
        task.category_id = cid
    if "due_date" in data:
        if data["due_date"]:
            try:
                task.due_date = datetime.strptime(data["due_date"], "%Y-%m-%d")
            except ValueError:
                return {"error": "Formato de data inválido"}, 400
        else:
            task.due_date = None
    if "tags" in data:
        tags = data["tags"]
        task.tags = ",".join(tags) if isinstance(tags, list) else tags

    task.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        return task.to_dict(), 200
    except Exception:
        db.session.rollback()
        return {"error": "Erro ao atualizar"}, 500


def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return {"error": "Task não encontrada"}, 404
    try:
        db.session.delete(task)
        db.session.commit()
        return {"message": "Task deletada com sucesso"}, 200
    except Exception:
        db.session.rollback()
        return {"error": "Erro ao deletar"}, 500


def search_tasks(query, status, priority, user_id):
    q = Task.query
    if query:
        q = q.filter(
            db.or_(
                Task.title.like(f"%{query}%"),
                Task.description.like(f"%{query}%"),
            )
        )
    if status:
        q = q.filter(Task.status == status)
    if priority:
        q = q.filter(Task.priority == int(priority))
    if user_id:
        q = q.filter(Task.user_id == int(user_id))
    results = q.all()
    return [t.to_dict() for t in results], 200


def task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status="pending").count()
    in_progress = Task.query.filter_by(status="in_progress").count()
    done = Task.query.filter_by(status="done").count()
    cancelled = Task.query.filter_by(status="cancelled").count()

    now = datetime.utcnow()
    overdue_count = 0
    for t in Task.query.all():
        if t.due_date and t.due_date < now and t.status not in ("done", "cancelled"):
            overdue_count += 1

    stats = {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "done": done,
        "cancelled": cancelled,
        "overdue": overdue_count,
        "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
    }
    return stats, 200
