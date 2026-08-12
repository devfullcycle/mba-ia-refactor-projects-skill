"""Serviço de tasks — regras de negócio extraídas das rotas.

Rotas ficam finas (validação + chamada do service); a lógica de domínio
(overdue, validação, CRUD) vive aqui.
"""

from datetime import datetime

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from config import settings
from middlewares.error_handler import ApiError


class TaskServiceError(ApiError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def list_tasks():
    tasks = Task.query.all()
    result = []
    for t in tasks:
        data = t.serializable()
        data["user_name"] = t.user.name if t.user else None
        data["category_name"] = t.category.name if t.category else None
        result.append(data)
    return result


def get_task(task_id):
    t = Task.query.get(task_id)
    if not t:
        raise TaskServiceError("Task não encontrada", 404)
    return t.serializable()


def create_task(data):
    _validate_task_payload(data)  # valida não-nulos e tipos
    task = Task()
    _apply_task_data(task, data)
    _validate_user_refs(task.user_id, task.category_id)
    db.session.add(task)
    _commit()
    return task.serializable()


def update_task(task_id, data):
    task = Task.query.get(task_id)
    if not task:
        raise TaskServiceError("Task não encontrada", 404)
    if data.get("title") is not None:
        _validate_title(data["title"])
    if "status" in data and data["status"] not in settings.VALID_STATUSES:
        raise TaskServiceError("Status inválido", 400)
    if "priority" in data and not (1 <= data["priority"] <= 5):
        raise TaskServiceError("Prioridade deve ser entre 1 e 5", 400)
    _apply_task_data(task, data)
    _validate_user_refs(task.user_id, task.category_id)
    task.updated_at = datetime.utcnow()
    db.session.commit()
    return task.serializable()


def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        raise TaskServiceError("Task não encontrada", 404)
    db.session.delete(task)
    db.session.commit()


def search_tasks(query=None, status=None, priority=None, user_id=None):
    q = Task.query
    if query:
        like = f"%{query}%"
        q = q.filter(
            db.or_(Task.title.like(like), Task.description.like(like))
        )
    if status:
        q = q.filter(Task.status == status)
    if priority:
        q = q.filter(Task.priority == int(priority))
    if user_id:
        q = q.filter(Task.user_id == int(user_id))
    return [t.serializable() for t in q.all()]


def task_stats():
    total = Task.query.count()
    by_status = {s: Task.query.filter_by(status=s).count() for s in settings.VALID_STATUSES}
    all_tasks = Task.query.all()
    overdue_count = sum(1 for t in all_tasks if t.is_overdue())
    done = by_status["done"]
    return {
        "total": total,
        "pending": by_status["pending"],
        "in_progress": by_status["in_progress"],
        "done": done,
        "cancelled": by_status["cancelled"],
        "overdue": overdue_count,
        "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
    }


# --- helpers privados ---

def _validate_task_payload(data):
    if not data:
        raise TaskServiceError("Dados inválidos", 400)
    if data.get("title") is None:
        raise TaskServiceError("Título é obrigatório", 400)
    _validate_title(data["title"])
    if "status" in data and data["status"] not in settings.VALID_STATUSES:
        raise TaskServiceError("Status inválido", 400)
    if "priority" in data and not (1 <= data["priority"] <= 5):
        raise TaskServiceError("Prioridade deve ser entre 1 e 5", 400)


def _validate_title(title):
    if len(title) < settings.MIN_TITLE_LENGTH:
        raise TaskServiceError("Título muito curto", 400)
    if len(title) > settings.MAX_TITLE_LENGTH:
        raise TaskServiceError("Título muito longo", 400)


def _apply_task_data(task, data):
    task.title = data.get("title", task.title)
    task.description = data.get("description", task.description)
    task.status = data.get("status", task.status)
    task.priority = data.get("priority", task.priority)
    task.user_id = data.get("user_id", task.user_id)
    task.category_id = data.get("category_id", task.category_id)
    if "due_date" in data:
        task.due_date = _parse_due_date(data.get("due_date"))
    if "tags" in data:
        tags = data["tags"]
        task.tags = ",".join(tags) if isinstance(tags, list) else tags


def _commit():
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise TaskServiceError("Erro ao salvar", 500)


def _parse_due_date(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise TaskServiceError("Formato de data inválido. Use YYYY-MM-DD", 400)


def _validate_user_refs(user_id, category_id):
    if user_id and not User.query.get(user_id):
        raise TaskServiceError("Usuário não encontrado", 404)
    if category_id and not Category.query.get(category_id):
        raise TaskServiceError("Categoria não encontrada", 404)