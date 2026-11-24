"""Cálculos dos relatórios, todos agregados no banco. A forma do JSON fica em views/report_view.py."""
from collections import Counter
from datetime import timedelta

from sqlalchemy import func, select

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from services import user_service
from utils.clock import utc_now
from utils.constants import HIGH_PRIORITY_MAX, RECENT_DAYS, STATUS_DONE


def _count(model, *conditions):
    return db.session.scalar(select(func.count()).select_from(model).where(*conditions))


def _group_counts(column, *conditions):
    return dict(db.session.execute(
        select(column, func.count()).where(*conditions).group_by(column)).all())


def summary():
    now = utc_now()
    since = now - timedelta(days=RECENT_DAYS)

    per_user = Counter()
    per_user_done = Counter()
    for user_id, status, count in db.session.execute(
            select(Task.user_id, Task.status, func.count())
            .where(Task.user_id.is_not(None))
            .group_by(Task.user_id, Task.status)):
        per_user[user_id] += count
        if status == STATUS_DONE:
            per_user_done[user_id] += count

    return {
        'now': now,
        'totals': {'tasks': _count(Task), 'users': _count(User), 'categories': _count(Category)},
        'by_status': _group_counts(Task.status),
        'by_priority': _group_counts(Task.priority),
        'overdue_tasks': db.session.scalars(
            select(Task).where(Task.overdue_clause(now)).order_by(Task.id)).all(),
        'recent_created': _count(Task, Task.created_at >= since),
        'recent_done': _count(Task, Task.status == STATUS_DONE, Task.updated_at >= since),
        'users': db.session.scalars(select(User).order_by(User.id)).all(),
        'per_user': per_user,
        'per_user_done': per_user_done,
    }


def user_report(user_id):
    user = user_service.get(user_id)
    of_user = Task.user_id == user_id
    return {
        'user': user,
        'by_status': Counter(_group_counts(Task.status, of_user)),
        'total': _count(Task, of_user),
        'overdue': _count(Task, of_user, Task.overdue_clause()),
        'high_priority': _count(Task, of_user, Task.priority <= HIGH_PRIORITY_MAX),
    }
