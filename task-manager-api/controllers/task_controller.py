"""Casos de uso de tasks: valida entrada, aplica regras e orquestra os models."""
import logging

from config.constants import (
    DEFAULT_PRIORITY,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
)
from controllers.common import get_or_404, persistence_errors
from models.category import Category
from models.task import Task
from models.user import User
from utils import validators
from utils.helpers import calculate_percentage, utc_now

logger = logging.getLogger(__name__)

TASK_NOT_FOUND = 'Task não encontrada'
USER_NOT_FOUND = 'Usuário não encontrado'
CATEGORY_NOT_FOUND = 'Categoria não encontrada'


def list_tasks():
    now = utc_now()
    result = []
    for task in Task.list_with_relations():
        data = task.to_dict()
        data['overdue'] = task.is_overdue(now)
        data['user_name'] = task.user.name if task.user else None
        data['category_name'] = task.category.name if task.category else None
        result.append(data)
    return result


def get_task(task_id):
    return get_or_404(Task, task_id, TASK_NOT_FOUND).to_dict_with_overdue()


def create_task(data):
    validators.require_json_object(data)

    title = validators.validate_title(data.get('title'), required_message='Título é obrigatório')
    description = data.get('description', '')
    status = validators.validate_status(data.get('status', STATUS_PENDING))
    priority = validators.validate_priority(data.get('priority', DEFAULT_PRIORITY))
    user_id = data.get('user_id')
    category_id = data.get('category_id')
    due_date = data.get('due_date')
    tags = data.get('tags')

    if user_id:
        get_or_404(User, user_id, USER_NOT_FOUND)
    if category_id:
        get_or_404(Category, category_id, CATEGORY_NOT_FOUND)

    task = Task(
        title=title,
        description=description,
        status=status,
        priority=priority,
        user_id=user_id,
        category_id=category_id,
    )
    if due_date:
        task.due_date = validators.parse_due_date(due_date, 'Formato de data inválido. Use YYYY-MM-DD')
    if tags:
        task.tags = validators.normalize_tags(tags)

    with persistence_errors('Erro ao criar task'):
        task.save()
    logger.info('Task criada: %s - %s', task.id, task.title)
    return task.to_dict()


def update_task(task_id, data):
    task = get_or_404(Task, task_id, TASK_NOT_FOUND)
    validators.require_json_object(data)

    changes = {}
    if 'title' in data:
        changes['title'] = validators.validate_title(data['title'])
    if 'description' in data:
        changes['description'] = data['description']
    if 'status' in data:
        changes['status'] = validators.validate_status(data['status'])
    if 'priority' in data:
        changes['priority'] = validators.validate_priority(data['priority'])
    if 'user_id' in data:
        if data['user_id']:
            get_or_404(User, data['user_id'], USER_NOT_FOUND)
        changes['user_id'] = data['user_id']
    if 'category_id' in data:
        if data['category_id']:
            get_or_404(Category, data['category_id'], CATEGORY_NOT_FOUND)
        changes['category_id'] = data['category_id']
    if 'due_date' in data:
        changes['due_date'] = (
            validators.parse_due_date(data['due_date'], 'Formato de data inválido')
            if data['due_date'] else None
        )
    if 'tags' in data:
        changes['tags'] = validators.normalize_tags(data['tags'])

    for field, value in changes.items():
        setattr(task, field, value)
    task.updated_at = utc_now()

    with persistence_errors('Erro ao atualizar'):
        task.save()
    logger.info('Task atualizada: %s', task.id)
    return task.to_dict()


def delete_task(task_id):
    task = get_or_404(Task, task_id, TASK_NOT_FOUND)
    with persistence_errors('Erro ao deletar'):
        task.delete()
    logger.info('Task deletada: %s', task_id)
    return {'message': 'Task deletada com sucesso'}


def search_tasks(args):
    text = args.get('q', '')
    status = args.get('status', '')
    priority = args.get('priority', '')
    user_id = args.get('user_id', '')

    tasks = Task.search(
        text=text,
        status=status,
        priority=validators.parse_int_param(priority, 'Prioridade inválida') if priority else None,
        user_id=validators.parse_int_param(user_id, 'user_id inválido') if user_id else None,
    )
    return [task.to_dict() for task in tasks]


def task_stats():
    total = Task.count_all()
    by_status = Task.count_by_status()
    done = by_status.get(STATUS_DONE, 0)
    return {
        'total': total,
        'pending': by_status.get(STATUS_PENDING, 0),
        'in_progress': by_status.get(STATUS_IN_PROGRESS, 0),
        'done': done,
        'cancelled': by_status.get(STATUS_CANCELLED, 0),
        'overdue': Task.count_overdue(),
        'completion_rate': calculate_percentage(done, total),
    }
