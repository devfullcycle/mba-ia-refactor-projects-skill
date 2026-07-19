from flask import request, jsonify
from marshmallow import ValidationError

from models.user import User
from models.task import Task
from schemas import first_error
from schemas.user_schema import UserCreateSchema, UserUpdateSchema
from services import user_service
from middlewares.error_handler import ApiError

_create_schema = UserCreateSchema()
_update_schema = UserUpdateSchema()


def list_users():
    return jsonify([u.to_summary_dict() for u in User.all()]), 200


def get_user(user_id):
    user = User.get(user_id)
    if not user:
        raise ApiError('Usuário não encontrado', 404)
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.for_user(user_id)]
    return jsonify(data), 200


def create_user():
    payload = request.get_json(silent=True)
    if not payload:
        raise ApiError('Dados inválidos', 400)
    try:
        data = _create_schema.load(payload)
    except ValidationError as err:
        raise ApiError(first_error(err), 400)

    if User.get_by_email(data['email']):
        raise ApiError('Email já cadastrado', 409)

    user = User()
    user.name = data['name']
    user.email = data['email']
    user.set_password(data['password'])
    user.role = data['role']
    user.save()
    return jsonify(user.to_dict()), 201


def update_user(user_id):
    user = User.get(user_id)
    if not user:
        raise ApiError('Usuário não encontrado', 404)

    payload = request.get_json(silent=True)
    if not payload:
        raise ApiError('Dados inválidos', 400)
    try:
        data = _update_schema.load(payload)
    except ValidationError as err:
        raise ApiError(first_error(err), 400)

    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        existing = User.get_by_email(data['email'])
        if existing and existing.id != user_id:
            raise ApiError('Email já cadastrado', 409)
        user.email = data['email']
    if 'password' in data:
        user.set_password(data['password'])
    if 'role' in data:
        user.role = data['role']
    if 'active' in data:
        user.active = data['active']

    user.save()
    return jsonify(user.to_dict()), 200


def delete_user(user_id):
    user = User.get(user_id)
    if not user:
        raise ApiError('Usuário não encontrado', 404)
    user_service.delete_user_cascade(user)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    user = User.get(user_id)
    if not user:
        raise ApiError('Usuário não encontrado', 404)
    return jsonify([t.to_summary_dict() for t in Task.for_user(user_id)]), 200
