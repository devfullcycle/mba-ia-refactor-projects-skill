"""Serviço de relatórios e categorias — agregações sem N+1."""

from datetime import datetime, timedelta

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from config import settings
from middlewares.error_handler import ApiError


class ReportServiceError(ApiError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def summary_report():
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    by_status = {s: Task.query.filter_by(status=s).count() for s in settings.VALID_STATUSES}
    by_priority = {p: Task.query.filter_by(priority=p).count() for p in range(1, 6)}

    all_tasks = Task.query.all()
    overdue_tasks = [t for t in all_tasks if t.is_overdue()]

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == "done", Task.updated_at >= seven_days_ago
    ).count()

    # Agregação por usuário sem N+1 (busca tasks uma única vez).
    user_stats = _user_stats()

    return {
        "generated_at": str(datetime.utcnow()),
        "overview": {
            "total_tasks": total_tasks,
            "total_users": total_users,
            "total_categories": total_categories,
        },
        "tasks_by_status": by_status,
        "tasks_by_priority": {
            "critical": by_priority[1],
            "high": by_priority[2],
            "medium": by_priority[3],
            "low": by_priority[4],
            "minimal": by_priority[5],
        },
        "overdue": {
            "count": len(overdue_tasks),
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "due_date": str(t.due_date),
                    "days_overdue": t.days_overdue(),
                }
                for t in overdue_tasks
            ],
        },
        "recent_activity": {
            "tasks_created_last_7_days": recent_tasks,
            "tasks_completed_last_7_days": recent_done,
        },
        "user_productivity": user_stats,
    }


def user_report(user_id):
    user = User.query.get(user_id)
    if not user:
        raise ReportServiceError("Usuário não encontrado", 404)
    tasks = Task.query.filter_by(user_id=user_id).all()

    total = len(tasks)
    by_status = {s: 0 for s in settings.VALID_STATUSES}
    overdue = 0
    high_priority = 0
    done = 0

    for t in tasks:
        by_status[t.status] = by_status.get(t.status, 0) + 1
        if t.status == "done":
            done += 1
        if t.priority <= 2:
            high_priority += 1
        if t.is_overdue():
            overdue += 1

    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "statistics": {
            "total_tasks": total,
            "done": by_status["done"],
            "pending": by_status["pending"],
            "in_progress": by_status["in_progress"],
            "cancelled": by_status["cancelled"],
            "overdue": overdue,
            "high_priority": high_priority,
            "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
        },
    }


def _user_stats():
    """Produtividade por usuário com N+1 reduzido (busca tasks uma vez)."""
    users = User.query.all()
    all_tasks = Task.query.all()
    by_user = {}
    for t in all_tasks:
        by_user.setdefault(t.user_id, []).append(t)

    result = []
    for u in users:
        tasks = by_user.get(u.id, [])
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == "done")
        result.append(
            {
                "user_id": u.id,
                "user_name": u.name,
                "total_tasks": total,
                "completed_tasks": completed,
                "completion_rate": round((completed / total) * 100, 2) if total > 0 else 0,
            }
        )
    return result


# --- Categorias (regras + CRUD) ---

def list_categories():
    result = []
    for c in Category.query.all():
        data = c.to_dict()
        data["task_count"] = Task.query.filter_by(category_id=c.id).count()
        result.append(data)
    return result


def create_category(data):
    if not data:
        raise ReportServiceError("Dados inválidos", 400)
    name = data.get("name")
    if not name:
        raise ReportServiceError("Nome é obrigatório", 400)
    color = data.get("color", settings.DEFAULT_COLOR)
    if not _valid_color(color):
        raise ReportServiceError("Cor inválida", 400)

    category = Category()
    category.name = name
    category.description = data.get("description", "")
    category.color = color
    db.session.add(category)
    db.session.commit()
    return category.to_dict()


def update_category(cat_id, data):
    cat = Category.query.get(cat_id)
    if not cat:
        raise ReportServiceError("Categoria não encontrada", 404)
    if "name" in data:
        if not data["name"]:
            raise ReportServiceError("Nome é obrigatório", 400)
        cat.name = data["name"]
    if "description" in data:
        cat.description = data["description"]
    if "color" in data:
        if not _valid_color(data["color"]):
            raise ReportServiceError("Cor inválida", 400)
        cat.color = data["color"]
    db.session.commit()
    return cat.to_dict()


def delete_category(cat_id):
    cat = Category.query.get(cat_id)
    if not cat:
        raise ReportServiceError("Categoria não encontrada", 404)
    db.session.delete(cat)
    db.session.commit()


def _valid_color(color):
    return bool(color) and len(color) == 7 and color.startswith("#")