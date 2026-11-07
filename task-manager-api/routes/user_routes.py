import logging

from flask import Blueprint, request, jsonify

from database import db
from models.user import User
from models.task import Task
from utils.helpers import validate_email, VALID_ROLES, MIN_PASSWORD_LENGTH

user_bp = Blueprint('users', __name__)
logger = logging.getLogger(__name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    result = []
    for u in users:
        data = u.to_dict()
        data['task_count'] = len(u.tasks)
        result.append(data)
    return jsonify(result), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
    return jsonify(data), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    if not name:
        return jsonify({'error': 'Nome é obrigatório'}), 400
    if not email:
        return jsonify({'error': 'Email é obrigatório'}), 400
    if not password:
        return jsonify({'error': 'Senha é obrigatória'}), 400
    if not validate_email(email):
        return jsonify({'error': 'Email inválido'}), 400
    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({'error': 'Senha deve ter no mínimo 4 caracteres'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email já cadastrado'}), 409
    if role not in VALID_ROLES:
        return jsonify({'error': 'Role inválido'}), 400

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role
    db.session.add(user)
    db.session.commit()
    logger.info("Usuário criado: %s - %s", user.id, user.name)
    return jsonify(user.to_dict()), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        if not validate_email(data['email']):
            return jsonify({'error': 'Email inválido'}), 400
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            return jsonify({'error': 'Email já cadastrado'}), 409
        user.email = data['email']
    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            return jsonify({'error': 'Senha muito curta'}), 400
        user.set_password(data['password'])
    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            return jsonify({'error': 'Role inválido'}), 400
        user.role = data['role']
    if 'active' in data:
        user.active = data['active']

    db.session.commit()
    return jsonify(user.to_dict()), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    # Deleção em cascata das tasks do usuário (evita órfãos).
    for t in Task.query.filter_by(user_id=user_id).all():
        db.session.delete(t)
    db.session.delete(user)
    db.session.commit()
    logger.info("Usuário deletado: %s", user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    result = []
    for t in Task.query.filter_by(user_id=user_id).all():
        result.append({
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'status': t.status,
            'priority': t.priority,
            'created_at': str(t.created_at),
            'due_date': str(t.due_date) if t.due_date else None,
            'overdue': t.is_overdue(),
        })
    return jsonify(result), 200


@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Credenciais inválidas'}), 401
    if not user.active:
        return jsonify({'error': 'Usuário inativo'}), 403

    # NOTA: token stub — substituir por JWT real em produção.
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': 'fake-jwt-token-' + str(user.id),
    }), 200
