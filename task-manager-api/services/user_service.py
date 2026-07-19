"""Orquestração de operações de usuário que exigem atomicidade."""
from database import db
from models.task import Task


def delete_user_cascade(user):
    """Remove o usuário e suas tasks numa única transação (sem deixar órfãos)."""
    for task in Task.for_user(user.id):
        db.session.delete(task)
    db.session.delete(user)
    db.session.commit()
