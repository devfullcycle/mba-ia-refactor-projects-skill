from sqlalchemy import func, select

from database import commit_or_fail, db
from models.category import Category
from models.task import Task
from utils.errors import NotFoundError


def list_with_task_counts():
    categories = db.session.scalars(select(Category).order_by(Category.id)).all()
    counts = dict(db.session.execute(
        select(Task.category_id, func.count())
        .where(Task.category_id.isnot(None))
        .group_by(Task.category_id)
    ).all())
    return [(category, counts.get(category.id, 0)) for category in categories]


def get(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')
    return category


def create(fields):
    category = Category(**fields)
    db.session.add(category)
    commit_or_fail('Erro ao criar categoria')
    return category


def update(category, fields):
    for name, value in fields.items():
        setattr(category, name, value)
    commit_or_fail('Erro ao atualizar')
    return category


def delete(category):
    db.session.delete(category)
    commit_or_fail('Erro ao deletar')
