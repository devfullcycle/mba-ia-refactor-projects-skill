from flask import jsonify, request

from middlewares.auth import current_user
from services import access_policy, task_service
from utils.request_utils import get_json_body
from validators import common, task_validator
from views import task_view


def list_tasks():
    tasks = task_service.list_all(common.pagination(request.args))
    return jsonify([task_view.render_list_item(t) for t in tasks]), 200


def get_task(task_id):
    return jsonify(task_view.render_detail(task_service.get(task_id))), 200


def create_task():
    fields = task_validator.validate_create(get_json_body())
    fields = access_policy.resolve_task_owner(current_user(), fields, creating=True)
    task = task_service.create(fields)
    return jsonify(task_view.render(task)), 201


def update_task(task_id):
    task = task_service.get(task_id)
    access_policy.ensure_can_manage_task(current_user(), task)
    fields = task_validator.validate_update(get_json_body())
    fields = access_policy.resolve_task_owner(current_user(), fields, creating=False)
    task = task_service.update(task, fields)
    return jsonify(task_view.render(task)), 200


def delete_task(task_id):
    task = task_service.get(task_id)
    access_policy.ensure_can_manage_task(current_user(), task)
    task_service.delete(task)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    filters = task_validator.parse_search_filters(request.args)
    tasks = task_service.search(filters, common.pagination(request.args))
    return jsonify([task_view.render(t) for t in tasks]), 200


def task_stats():
    return jsonify(task_service.stats()), 200
