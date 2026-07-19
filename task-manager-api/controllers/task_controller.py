from datetime import datetime

from flask import request, jsonify
from marshmallow import ValidationError

from models.task import Task
from models.user import User
from models.category import Category
from schemas import first_error
from schemas.task_schema import TaskCreateSchema, TaskUpdateSchema
from services import report_service
from middlewares.error_handler import ApiError
from utils.constants import DATE_FORMAT

_create_schema = TaskCreateSchema()
_update_schema = TaskUpdateSchema()


def _parse_due_date(value, message):
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (ValueError, TypeError):
        raise ApiError(message, 400)


def _normalize_tags(tags):
    if isinstance(tags, list):
        return ','.join(tags)
    return tags


def _require_related(model, entity_id, not_found_message):
    if entity_id and not model.get(entity_id):
        raise ApiError(not_found_message, 404)


def list_tasks():
    return jsonify([t.to_dict_full() for t in Task.all()]), 200


def get_task(task_id):
    task = Task.get(task_id)
    if not task:
        raise ApiError('Task não encontrada', 404)
    return jsonify(task.to_dict_with_overdue()), 200


def create_task():
    payload = request.get_json(silent=True)
    if not payload:
        raise ApiError('Dados inválidos', 400)
    try:
        data = _create_schema.load(payload)
    except ValidationError as err:
        raise ApiError(first_error(err), 400)

    _require_related(User, data['user_id'], 'Usuário não encontrado')
    _require_related(Category, data['category_id'], 'Categoria não encontrada')

    task = Task()
    task.title = data['title']
    task.description = data['description']
    task.status = data['status']
    task.priority = data['priority']
    task.user_id = data['user_id']
    task.category_id = data['category_id']
    if data['due_date']:
        task.due_date = _parse_due_date(data['due_date'], 'Formato de data inválido. Use YYYY-MM-DD')
    if data['tags']:
        task.tags = _normalize_tags(data['tags'])

    task.save()
    return jsonify(task.to_dict()), 201


def update_task(task_id):
    task = Task.get(task_id)
    if not task:
        raise ApiError('Task não encontrada', 404)

    payload = request.get_json(silent=True)
    if not payload:
        raise ApiError('Dados inválidos', 400)
    try:
        data = _update_schema.load(payload)
    except ValidationError as err:
        raise ApiError(first_error(err), 400)

    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        task.status = data['status']
    if 'priority' in data:
        task.priority = data['priority']
    if 'user_id' in data:
        _require_related(User, data['user_id'], 'Usuário não encontrado')
        task.user_id = data['user_id']
    if 'category_id' in data:
        _require_related(Category, data['category_id'], 'Categoria não encontrada')
        task.category_id = data['category_id']
    if 'due_date' in data:
        task.due_date = _parse_due_date(data['due_date'], 'Formato de data inválido') if data['due_date'] else None
    if 'tags' in data:
        task.tags = _normalize_tags(data['tags'])

    task.touch()
    task.save()
    return jsonify(task.to_dict()), 200


def delete_task(task_id):
    task = Task.get(task_id)
    if not task:
        raise ApiError('Task não encontrada', 404)
    task.delete()
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def _optional_int(value, message):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        raise ApiError(message, 400)


def search_tasks():
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    priority = _optional_int(request.args.get('priority', ''), 'Prioridade inválida')
    user_id = _optional_int(request.args.get('user_id', ''), 'user_id inválido')

    tasks = Task.search(query=query, status=status, priority=priority, user_id=user_id)
    return jsonify([t.to_dict() for t in tasks]), 200


def stats():
    return jsonify(report_service.task_stats()), 200
