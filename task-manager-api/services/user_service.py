import logging

from sqlalchemy import func, select

from database import commit_or_fail, db
from models.task import Task
from models.user import User
from utils.errors import AuthenticationError, ConflictError, ForbiddenError, NotFoundError

logger = logging.getLogger(__name__)


def list_with_task_counts():
    """Usuários com a contagem de tasks calculada em uma única agregação."""
    users = db.session.scalars(select(User).order_by(User.id)).all()
    counts = dict(db.session.execute(
        select(Task.user_id, func.count()).where(Task.user_id.isnot(None)).group_by(Task.user_id)
    ).all())
    return [(user, counts.get(user.id, 0)) for user in users]


def get(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return user


def tasks_of(user_id):
    return db.session.scalars(
        select(Task).where(Task.user_id == user_id).order_by(Task.id)).all()


def _ensure_email_free(email, ignore_user_id=None):
    existing = db.session.scalar(select(User).where(User.email == email))
    if existing and existing.id != ignore_user_id:
        raise ConflictError('Email já cadastrado')


def create(fields):
    _ensure_email_free(fields['email'])
    user = User(name=fields['name'], email=fields['email'], role=fields['role'])
    user.set_password(fields['password'])
    db.session.add(user)
    commit_or_fail('Erro ao criar usuário')
    logger.info('Usuário criado: %s - %s', user.id, user.name)
    return user


def update(user, fields):
    if 'email' in fields:
        _ensure_email_free(fields['email'], ignore_user_id=user.id)
    for name, value in fields.items():
        if name == 'password':
            user.set_password(value)
        else:
            setattr(user, name, value)
    commit_or_fail('Erro ao atualizar')
    return user


def delete(user):
    user_id = user.id
    for task in tasks_of(user_id):
        db.session.delete(task)
    db.session.delete(user)
    commit_or_fail('Erro ao deletar')
    logger.info('Usuário deletado: %s', user_id)


def authenticate(email, password):
    user = db.session.scalar(select(User).where(User.email == email))
    if not user or not user.check_password(password):
        raise AuthenticationError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')
    if user.uses_legacy_hash():
        user.set_password(password)  # migra hash MD5 antigo para o formato seguro
        commit_or_fail('Erro ao atualizar')
    return user
