"""Orquestração de operações de categoria com integridade referencial."""
from database import db
from models.task import Task


def delete_category_safely(category):
    """Remove a categoria após desvincular as tasks (category_id -> NULL),
    evitando referências órfãs. Tudo numa única transação."""
    for task in Task.for_category(category.id):
        task.category_id = None
    db.session.delete(category)
    db.session.commit()
