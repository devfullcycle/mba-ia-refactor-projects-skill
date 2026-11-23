from sqlalchemy import select

from database import assign, commit_or_fail, db, paginate
from models.category import Category
from models.task import Task
from utils.errors import NotFoundError


def list_with_task_counts(page=None):
    categories = db.session.scalars(paginate(select(Category).order_by(Category.id), page)).all()
    counts = Task.counts_by(Task.category_id)
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
    assign(category, fields)
    commit_or_fail('Erro ao atualizar')
    return category


def delete(category):
    # O relacionamento Category.tasks (sem cascade de delete) faz o ORM zerar
    # category_id das tasks na mesma transação: elas ficam sem categoria, não órfãs.
    db.session.delete(category)
    commit_or_fail('Erro ao deletar')
