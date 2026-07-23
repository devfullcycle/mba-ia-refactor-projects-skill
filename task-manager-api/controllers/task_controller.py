from datetime import datetime, timezone
from sqlalchemy import select
from flask import request
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from core.constants import VALID_STATUSES, PRIORITY_MIN, PRIORITY_MAX
from core.errors import NotFoundError, ValidationError
from utils.helpers import parse_date


def _task_with_names(t):
    data = t.to_dict()
    data["overdue"] = t.is_overdue()
    data["user_name"] = t.user.name if t.user else None
    data["category_name"] = t.category.name if t.category else None
    return data


def list_tasks():
    stmt = (
        select(Task)
        .options(
            db.joinedload(Task.user),
            db.joinedload(Task.category),
        )
    )
    tasks = db.session.execute(stmt).unique().scalars().all()
    return [_task_with_names(t) for t in tasks], 200


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError("Task nao encontrada")
    data = task.to_dict()
    data["overdue"] = task.is_overdue()
    return data, 200


def _validate_task_payload(data, partial=False):
    if not data:
        raise ValidationError("Dados invalidos")

    title = data.get("title")
    if not partial and not title:
        raise ValidationError("Titulo e obrigatorio")
    if title is not None:
        if len(title) < 3 or len(title) > 200:
            raise ValidationError("Titulo deve ter entre 3 e 200 caracteres")

    status = data.get("status", "pending")
    if status not in VALID_STATUSES:
        raise ValidationError("Status invalido")

    priority = data.get("priority", 3)
    if not (PRIORITY_MIN <= priority <= PRIORITY_MAX):
        raise ValidationError(f"Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}")


def create_task():
    data = request.get_json() or {}
    _validate_task_payload(data)

    user_id = data.get("user_id")
    if user_id and not db.session.get(User, user_id):
        raise NotFoundError("Usuario nao encontrado")
    category_id = data.get("category_id")
    if category_id and not db.session.get(Category, category_id):
        raise NotFoundError("Categoria nao encontrada")

    task = Task()
    task.title = data["title"]
    task.description = data.get("description", "")
    task.status = data.get("status", "pending")
    task.priority = data.get("priority", 3)
    task.user_id = user_id
    task.category_id = category_id

    due_date = data.get("due_date")
    if due_date:
        parsed = parse_date(due_date)
        if not parsed:
            raise ValidationError("Formato de data invalido. Use YYYY-MM-DD")
        task.due_date = parsed

    tags = data.get("tags")
    if tags:
        task.tags = ",".join(tags) if isinstance(tags, list) else tags

    db.session.add(task)
    db.session.commit()
    return task.to_dict(), 201


def update_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError("Task nao encontrada")

    data = request.get_json() or {}
    _validate_task_payload(data, partial=True)

    if "title" in data:
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "status" in data:
        task.status = data["status"]
    if "priority" in data:
        task.priority = data["priority"]
    if "user_id" in data:
        if data["user_id"] and not db.session.get(User, data["user_id"]):
            raise NotFoundError("Usuario nao encontrado")
        task.user_id = data["user_id"]
    if "category_id" in data:
        if data["category_id"] and not db.session.get(Category, data["category_id"]):
            raise NotFoundError("Categoria nao encontrada")
        task.category_id = data["category_id"]
    if "due_date" in data:
        if data["due_date"]:
            parsed = parse_date(data["due_date"])
            if not parsed:
                raise ValidationError("Formato de data invalido")
            task.due_date = parsed
        else:
            task.due_date = None
    if "tags" in data:
        task.tags = (
            ",".join(data["tags"]) if isinstance(data["tags"], list) else data["tags"]
        )

    db.session.commit()
    return task.to_dict(), 200


def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError("Task nao encontrada")
    db.session.delete(task)
    db.session.commit()
    return {"message": "Task deletada com sucesso"}, 200


def search_tasks():
    query_text = request.args.get("q", "")
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")
    user_id = request.args.get("user_id", "")

    stmt = select(Task)
    if query_text:
        like = f"%{query_text}%"
        stmt = stmt.where(db.or_(Task.title.like(like), Task.description.like(like)))
    if status:
        stmt = stmt.where(Task.status == status)
    if priority:
        try:
            stmt = stmt.where(Task.priority == int(priority))
        except ValueError:
            raise ValidationError("priority deve ser inteiro")
    if user_id:
        try:
            stmt = stmt.where(Task.user_id == int(user_id))
        except ValueError:
            raise ValidationError("user_id deve ser inteiro")

    tasks = db.session.execute(stmt).scalars().all()
    return [t.to_dict() for t in tasks], 200


def task_stats():
    session = db.session
    total = session.scalar(select(Task).with_only_columns(db.func.count(Task.id)))

    def _count_status(s):
        return session.scalar(
            select(db.func.count(Task.id)).where(Task.status == s)
        )

    pending = _count_status("pending")
    in_progress = _count_status("in_progress")
    done = _count_status("done")
    cancelled = _count_status("cancelled")

    now = datetime.now(timezone.utc)
    overdue_count = session.scalar(
        select(db.func.count(Task.id)).where(
            Task.due_date.is_not(None),
            Task.due_date < now,
            Task.status.in_(("pending", "in_progress")),
        )
    )

    return (
        {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "done": done,
            "cancelled": cancelled,
            "overdue": overdue_count,
            "completion_rate": round((done / total) * 100, 2) if total else 0,
        },
        200,
    )
