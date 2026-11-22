"""Casos de uso de usuários e login."""
import logging

from config.constants import ROLE_USER
from controllers.common import get_or_404, persistence_errors
from models.task import Task
from models.user import User
from services import auth_service
from utils import validators
from utils.errors import AppError

logger = logging.getLogger(__name__)

USER_NOT_FOUND = 'Usuário não encontrado'
EMAIL_TAKEN = 'Email já cadastrado'


def _require_text(data, field, message):
    value = data.get(field)
    if not value or not isinstance(value, str):
        raise AppError(message, 400)
    return value


def list_users():
    counts = Task.totals_by_user()
    result = []
    for user in User.list_all():
        data = user.to_dict()
        data['task_count'] = counts.get(user.id, (0, 0))[0]
        result.append(data)
    return result


def get_user(user_id):
    user = get_or_404(User, user_id, USER_NOT_FOUND)
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in Task.find_by_user(user.id)]
    return data


def create_user(data, actor=None):
    """`actor` é o usuário autenticado (se houver); só um admin pode criar contas privilegiadas."""
    validators.require_json_object(data)

    name = _require_text(data, 'name', 'Nome é obrigatório')
    email = _require_text(data, 'email', 'Email é obrigatório')
    password = _require_text(data, 'password', 'Senha é obrigatória')
    role = data.get('role', ROLE_USER)

    validators.validate_email(email)
    validators.validate_password(password, 'Senha deve ter no mínimo 4 caracteres')

    if User.find_by_email(email):
        raise AppError(EMAIL_TAKEN, 409)

    validators.validate_role(role)
    if role != ROLE_USER:
        if actor is None:
            raise AppError('Autenticação necessária', 401)
        if not actor.is_admin():
            raise AppError('Permissão de administrador necessária', 403)

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    with persistence_errors('Erro ao criar usuário'):
        user.save()
    logger.info('Usuário criado: %s - %s', user.id, user.name)
    return user.to_dict()


def update_user(user_id, data, actor):
    """Só o próprio usuário ou um admin altera a conta; role/active exigem admin."""
    if not (actor.is_admin() or actor.id == user_id):
        raise AppError('Permissão negada', 403)

    user = get_or_404(User, user_id, USER_NOT_FOUND)
    validators.require_json_object(data)

    if ('role' in data or 'active' in data) and not actor.is_admin():
        raise AppError('Permissão de administrador necessária', 403)

    if 'name' in data:
        if not data['name'] or not isinstance(data['name'], str):
            raise AppError('Nome inválido', 400)
        user.name = data['name']

    if 'email' in data:
        validators.validate_email(data['email'])
        existing = User.find_by_email(data['email'])
        if existing and existing.id != user.id:
            raise AppError(EMAIL_TAKEN, 409)
        user.email = data['email']

    if 'password' in data:
        validators.validate_password(data['password'], 'Senha muito curta')
        user.set_password(data['password'])

    if 'role' in data:
        user.role = validators.validate_role(data['role'])

    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise AppError('Campo active inválido', 400)
        user.active = data['active']

    with persistence_errors('Erro ao atualizar'):
        user.save()
    return user.to_dict()


def delete_user(user_id):
    user = get_or_404(User, user_id, USER_NOT_FOUND)
    with persistence_errors('Erro ao deletar'):
        user.delete()  # as tasks do usuário são removidas em cascata
    logger.info('Usuário deletado: %s', user_id)
    return {'message': 'Usuário deletado com sucesso'}


def get_user_tasks(user_id):
    user = get_or_404(User, user_id, USER_NOT_FOUND)
    return [task.to_brief_dict() for task in Task.find_by_user(user.id)]


def login(data):
    validators.require_json_object(data)

    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise AppError('Email e senha são obrigatórios', 400)

    user = User.find_by_email(email) if isinstance(email, str) else None
    if user is None or not isinstance(password, str) or not user.check_password(password):
        raise AppError('Credenciais inválidas', 401)
    if not user.active:
        raise AppError('Usuário inativo', 403)

    if user.uses_legacy_hash():
        # Migra hashes MD5 antigos para o algoritmo atual no primeiro login válido.
        user.set_password(password)
        try:
            with persistence_errors('Erro ao migrar hash de senha'):
                user.save()
        except AppError:
            logger.warning('Falha ao migrar hash de senha do usuário %s', user.id)

    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': auth_service.issue_token(user),
    }
