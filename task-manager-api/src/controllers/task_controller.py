import logging

from src.models import category as category_model
from src.models import task as task_model
from src.models import user as user_model
from src.services import notification_service
from src.utils import validators
from src.utils.dates import utc_now
from src.utils.errors import ForbiddenError, NotFoundError
from src.utils.pagination import apply_page

logger = logging.getLogger(__name__)


def _get_or_404(task_id):
    task = task_model.find_by_id(task_id)
    if task is None:
        raise NotFoundError("Task não encontrada")
    return task


def _ensure_can_modify(task, actor):
    if not actor.is_staff() and task.user_id != actor.id:
        raise ForbiddenError("Você só pode alterar suas próprias tasks")


def _resolve_assignee(user_id, actor):
    user_id = validators.optional_id(user_id, "user_id")
    if user_id is None:
        return None
    if not actor.is_staff() and user_id != actor.id:
        raise ForbiddenError("Apenas admin/manager podem atribuir tasks a outros usuários")
    user = user_model.find_by_id(user_id)
    if user is None:
        raise NotFoundError("Usuário não encontrado")
    return user


def _resolve_category_id(category_id):
    category_id = validators.optional_id(category_id, "category_id")
    if category_id is not None and category_model.find_by_id(category_id) is None:
        raise NotFoundError("Categoria não encontrada")
    return category_id


def _validate_title(value):
    title = validators.required_string(value, "Título é obrigatório")
    return validators.string_length(
        title, task_model.TITLE_MIN_LENGTH, task_model.TITLE_MAX_LENGTH, "Título muito curto", "Título muito longo"
    )


def _validate_status(value):
    return validators.choice(value, task_model.VALID_STATUSES, "Status inválido")


def _validate_priority(value):
    message = f"Prioridade deve ser entre {task_model.PRIORITY_MIN} e {task_model.PRIORITY_MAX}"
    return validators.int_in_range(value, task_model.PRIORITY_MIN, task_model.PRIORITY_MAX, message, message)


def _validate_due_date(value):
    return validators.date(value) if value else None


def _notify_assignment(user, task):
    if user is not None:
        notification_service.notify_task_assigned(user, task)


def list_tasks(page=None):
    query = task_model.list_with_relations()
    total = task_model.count() if page else None
    return [task.to_list_item() for task in apply_page(query, page).all()], total


def get_task(task_id):
    return _get_or_404(task_id).to_dict_with_overdue()


def create_task(data, actor):
    data = validators.require_json_object(data)

    assignee = _resolve_assignee(data.get("user_id"), actor)
    fields = {
        "title": _validate_title(data.get("title")),
        "description": validators.optional_string(data.get("description", ""), "Descrição"),
        "status": _validate_status(data.get("status", task_model.STATUS_PENDING)),
        "priority": _validate_priority(data.get("priority", task_model.DEFAULT_PRIORITY)),
        "user_id": assignee.id if assignee else None,
        "category_id": _resolve_category_id(data.get("category_id")),
        "due_date": _validate_due_date(data.get("due_date")),
        "tags": validators.tags(data.get("tags")),
    }

    task = task_model.create(**fields)
    logger.info("Task criada: %s - %s", task.id, task.title)
    _notify_assignment(assignee, task)
    return task.to_dict()


def update_task(task_id, data, actor):
    task = _get_or_404(task_id)
    _ensure_can_modify(task, actor)
    data = validators.require_json_object(data)

    new_assignee = None
    if "title" in data:
        task.title = _validate_title(data["title"])
    if "description" in data:
        task.description = validators.optional_string(data["description"], "Descrição")
    if "status" in data:
        task.status = _validate_status(data["status"])
    if "priority" in data:
        task.priority = _validate_priority(data["priority"])
    if "user_id" in data:
        assignee = _resolve_assignee(data["user_id"], actor)
        new_user_id = assignee.id if assignee else None
        if new_user_id != task.user_id:
            new_assignee = assignee
        task.user_id = new_user_id
    if "category_id" in data:
        task.category_id = _resolve_category_id(data["category_id"])
    if "due_date" in data:
        task.due_date = _validate_due_date(data["due_date"])
    if "tags" in data:
        task.tags = validators.tags(data["tags"])

    task.updated_at = utc_now()
    task_model.save()
    logger.info("Task atualizada: %s", task.id)
    _notify_assignment(new_assignee, task)
    return task.to_dict()


def delete_task(task_id, actor):
    task = _get_or_404(task_id)
    _ensure_can_modify(task, actor)
    task_model.delete(task)
    logger.info("Task deletada: %s", task_id)
    return {"message": "Task deletada com sucesso"}


def search_tasks(args, page=None):
    priority = args.get("priority", "")
    user_id = args.get("user_id", "")
    query = task_model.search(
        text=args.get("q", ""),
        status=args.get("status", ""),
        priority=validators.query_int(priority, "priority") if priority else None,
        user_id=validators.query_int(user_id, "user_id") if user_id else None,
    )
    total = query.count() if page else None
    return [task.to_dict() for task in apply_page(query, page).all()], total


def task_stats():
    by_status = task_model.count_by_status()
    total = task_model.count()
    done = by_status[task_model.STATUS_DONE]
    return {
        "total": total,
        "pending": by_status[task_model.STATUS_PENDING],
        "in_progress": by_status[task_model.STATUS_IN_PROGRESS],
        "done": done,
        "cancelled": by_status[task_model.STATUS_CANCELLED],
        "overdue": task_model.count_overdue(utc_now()),
        "completion_rate": completion_rate(done, total),
    }


def completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0

