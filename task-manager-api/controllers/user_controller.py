from flask import jsonify, request

from middlewares.auth import current_user, issue_token, require_admin_user
from services import access_policy, user_service
from utils.request_utils import get_json_body
from validators import common, user_validator
from views import task_view, user_view


def list_users():
    pairs = user_service.list_with_task_counts(common.pagination(request.args))
    return jsonify([user_view.render_list_item(u, count) for u, count in pairs]), 200


def get_user(user_id):
    user = user_service.get(user_id)
    tasks = user_service.tasks_of(user_id)
    return jsonify(user_view.render_detail(user, tasks)), 200


def create_user():
    """Registro público; role privilegiado ou `active` exigem token de admin (401/403)."""
    fields = user_validator.validate_create(get_json_body())
    if access_policy.registration_requires_admin(fields):
        require_admin_user()
    user = user_service.create(fields)
    return jsonify(user_view.render(user)), 201


def update_user(user_id):
    user = user_service.get(user_id)
    access_policy.ensure_can_update_user(current_user(), user.id)
    fields = user_validator.validate_update(get_json_body())
    access_policy.ensure_can_set_user_fields(current_user(), fields)
    user = user_service.update(user, fields)
    return jsonify(user_view.render(user)), 200


def delete_user(user_id):
    user_service.delete(user_service.get(user_id))
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    user_service.get(user_id)
    tasks = user_service.tasks_of(user_id, common.pagination(request.args))
    return jsonify([task_view.render_summary(t) for t in tasks]), 200


def login():
    email, password = user_validator.validate_login(get_json_body())
    user = user_service.authenticate(email, password)
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user_view.render(user),
        'token': issue_token(user),
    }), 200
