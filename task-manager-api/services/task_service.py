import logging

from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from database import commit_or_fail, db
from models.category import Category
from models.task import Task
from models.user import User
from utils.clock import utc_now
from utils.constants import TASK_STATUSES
from utils.errors import NotFoundError
from utils.stats import percentage

logger = logging.getLogger(__name__)


def list_all():
    """Todas as tasks com usuário e categoria carregados numa única query (sem N+1)."""
    stmt = (
        select(Task)
        .options(joinedload(Task.user), joinedload(Task.category))
        .order_by(Task.id)
    )
    return db.session.scalars(stmt).unique().all()


def get(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task


def _ensure_references(fields):
    if fields.get('user_id') and not db.session.get(User, fields['user_id']):
        raise NotFoundError('Usuário não encontrado')
    if fields.get('category_id') and not db.session.get(Category, fields['category_id']):
        raise NotFoundError('Categoria não encontrada')


def create(fields):
    _ensure_references(fields)
    task = Task(**fields)
    db.session.add(task)
    commit_or_fail('Erro ao criar task')
    logger.info('Task criada: %s - %s', task.id, task.title)
    return task


def update(task, fields):
    _ensure_references(fields)
    for name, value in fields.items():
        setattr(task, name, value)
    task.updated_at = utc_now()
    commit_or_fail('Erro ao atualizar')
    logger.info('Task atualizada: %s', task.id)
    return task


def delete(task):
    task_id = task.id
    db.session.delete(task)
    commit_or_fail('Erro ao deletar')
    logger.info('Task deletada: %s', task_id)


def search(filters):
    stmt = select(Task).order_by(Task.id)
    if filters['q']:
        pattern = f"%{filters['q']}%"
        stmt = stmt.where(or_(Task.title.like(pattern), Task.description.like(pattern)))
    if filters['status']:
        stmt = stmt.where(Task.status == filters['status'])
    if filters['priority'] is not None:
        stmt = stmt.where(Task.priority == filters['priority'])
    if filters['user_id'] is not None:
        stmt = stmt.where(Task.user_id == filters['user_id'])
    return db.session.scalars(stmt).all()


def stats():
    rows = db.session.execute(select(Task.status, func.count()).group_by(Task.status)).all()
    by_status = {status: count for status, count in rows}
    total = sum(by_status.values())
    overdue = db.session.scalar(
        select(func.count()).select_from(Task).where(Task.overdue_clause()))
    done = by_status.get('done', 0)
    result = {'total': total}
    result.update({status: by_status.get(status, 0) for status in TASK_STATUSES})
    result['overdue'] = overdue
    result['completion_rate'] = percentage(done, total)
    return result
